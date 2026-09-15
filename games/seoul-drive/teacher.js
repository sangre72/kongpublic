/* ===== 교사 주행 API (u_4926) =====
   게임 내부 좌표로 '정확한 주행'을 수행한다. 이건 학습자료를 만드는 도구일 뿐,
   최종 주행 모델에는 들어가지 않는다(로직주행 금지 원칙 유지).

   제공 동작: 전진(차로중앙 유지) / 후진 / 좌회전 / 우회전
   파이썬은 window.__teach 로 호출하고, 화면 픽셀 ↔ 그때의 조작값을 쌍으로 수집한다. */
(function(){
  const T = {mode:'fwd', log:[], on:false};

  /* ★보행자 제동 파라미터(a_5057). 횡방향 4m 는 gap() 의 LW*0.62=2.02m 보다 넓다 —
     차로 가장자리로 뛰어드는(무단횡단 JAY_P) 보행자를 그 게이트가 놓쳤다. */
  const PED_SLOW_M = 25;    // 이 거리 안이면 감속
  const PED_STOP_M = 12;    // 이 거리 안이면 정지
  const PED_LAT_M  = 4;     // 횡방향 허용 폭(m)
  T.PED = {slow:PED_SLOW_M, stop:PED_STOP_M, lat:PED_LAT_M};

  /* ★차로 추종 재작성 (u_5001).
     이전 구조의 결함: nearestSeg 는 '차에서 가장 가까운 중심선 위 점'을 준다.
     차가 옆으로 움직이면 그 점도 같이 옆으로 따라온다. 목표점과 cross-track
     기준이 둘 다 그 점에 매달려 있어서, '지금 있는 자리'가 늘 기준이 됐다.
     그래서 다른 차로로 옮기려 해도 수렴할 고정 기준선이 없었고, 조향만
     포화됐다(3회 시도 3회 실패, u_4992~4996).

     여기서는 기준을 바꾼다:
       1) 세그먼트의 t(진행률)만 nearestSeg 에서 받고,
       2) 목표 차로의 '중심선'을 세그먼트 기하로 직접 계산한다(차 위치와 무관).
       3) lookahead 는 그 차로 중심선 위에서 전방으로 잡는다.
     이러면 차가 옆에 있든 없든 목표선이 고정돼 수렴한다. */
  function laneTarget(){
    const n = nearestSeg(me.x, me.y);
    if(!n) return null;
    const sg = n.s;
    let d = ((me.ang - sg.ang + Math.PI*3) % (Math.PI*2)) - Math.PI;
    const dir = Math.abs(d) < Math.PI/2 ? 1 : -1;

    // 이 방향으로 쓸 수 있는 차로 수 → 목표 차로를 실제 범위로 clamp
    const nl = sg.o ? sg.l : Math.max(1, Math.floor(sg.l/2));
    T.laneMax = nl;
    /* ★내비 경로가 있으면 '경로가 있는 차로'를 목표로 삼는다(u_5025 실측).
       예전엔 교사가 경로와 무관하게 자기 차로(T.lane, 기본 0차로)를 목표로 잡았다.
       경로는 가장 오른쪽 차로에 그려지는데 교사는 다른 차로를 원해서, 둘이 서로
       다른 곳을 가리켰다 — 화면 실측 ct=6.5m(약 2개 차로). 그 결과 차가 차로
       경계로 계속 밀려 '차로이탈'만 9회 났다(추돌·보행자 0회).
       주행 중에는 경로가 정답이다. 교사는 그 차로를 따른다. */
    let want = Math.max(0, Math.min(nl-1, (T.lane|0)));
    if(typeof auto!=='undefined' && auto.on && auto.wp && auto.wp.length){
      const w = auto.wp[Math.min(auto.i, auto.wp.length-1)];
      if(w){
        // 경로점이 중심선에서 얼마나 떨어져 있나 → 차로 인덱스로 환산
        const lat = (-(n.px-w.x)*Math.sin(sg.ang) + (n.py-w.y)*Math.cos(sg.ang)) / S * dir;
        const gi  = sg.o ? (lat + (sg.roadW/2)/S)/(LW/S) - 0.5
                         : Math.abs(lat)/(LW/S) - 0.5;
        want = Math.max(0, Math.min(nl-1, Math.round(gi)));
      }
    }
    /* ★첫 프레임의 laneF 는 '목표'가 아니라 '차가 지금 실제로 있는 차로'여야 한다
       (u_5001 실사고). 목표로 초기화하면, 차가 다른 차로에 있을 때 시작부터
       큰 횡오차가 생겨 조향이 곧바로 포화된다(steer 0.98 고정, 표준편차 0.000). */
    if(T.laneF === undefined){
      const lat0 = (-(n.px-me.x)*Math.sin(sg.ang) + (n.py-me.y)*Math.cos(sg.ang)) / S * dir;
      // lat0: 중심선 기준 부호거리(m) → 차로 인덱스로 환산
      const guess = sg.o ? (lat0 + (sg.roadW/2)/S)/(LW/S) - 0.5
                         : Math.abs(lat0)/(LW/S) - 0.5;
      T.laneF = Math.max(0, Math.min(nl-1, Math.round(guess)));
      /* ★목표(T.lane)는 아직 지정된 적 없을 때만 현재 차로로 맞춘다.
         무조건 덮어쓰면 밖에서 setLane 으로 지시한 목표가 지워진다(u_5001). */
      if(T.lane === undefined || T.laneSet !== true) T.lane = T.laneF;
    }
    /* ★차로 수가 다른 도로로 넘어갈 때도 '한 번에' 옮기지 않는다(u_5001 실사고).
       예전엔 여기서 laneF 를 곧바로 nl-1 로 잘랐다. 4차로에서 2차로 구간으로
       들어가는 순간 laneF 3 → 1 로 점프하고, 목표선이 6m 옆으로 튀어
       조향이 포화됐다. clamp 도 한 프레임에 step 만큼만 적용한다. */
    const step = 0.02;
    const hi = nl - 1;
    if(T.laneF > hi) T.laneF = Math.max(hi, T.laneF - step);
    if(T.laneF < 0)  T.laneF = Math.min(0,  T.laneF + step);
    // 실제 차선변경도 2~3초에 걸쳐 한다(0.02/프레임 ≈ 한 차로에 2.5초@30fps)
    if(T.laneF < want)      T.laneF = Math.min(want, T.laneF + step);
    else if(T.laneF > want) T.laneF = Math.max(want, T.laneF - step);
    T.laneMoving = Math.abs(T.laneF - want) > 0.005 || T.laneF > hi;

    const off = laneOffset(sg, dir, T.laneF);     // 목표 차로 오프셋(고정)
    const ang = sg.ang + (dir<0 ? Math.PI : 0);   // 내 진행방향

    /* ★목표 차로 중심선 — 차 위치가 아니라 세그먼트에서 계산한다.
       nearestSeg 의 t 를 그대로 써서 '도로를 따라 얼마나 왔는가'만 가져온다. */
    const A = nodes[sg.a], B = nodes[sg.b];
    const baseX = A.x + (B.x-A.x)*n.t - Math.sin(sg.ang)*off;
    const baseY = A.y + (B.y-A.y)*n.t + Math.cos(sg.ang)*off;

    /* 차로변경 중에는 멀리 본다. 가까이 보면 같은 횡이동에 큰 각도가 필요해
       조향이 포화된다(실측). 변경이 끝나면 다시 가깝게 본다. */
    const LA = (T.laneMoving ? 30 : 14) * S;
    const px = baseX + Math.cos(ang)*LA;
    const py = baseY + Math.sin(ang)*LA;

    /* cross-track 도 같은 고정 기준선으로 잰다(부호: 왼쪽 -, 오른쪽 +) */
    const cross = (-(baseX-me.x)*Math.sin(sg.ang) + (baseY-me.y)*Math.cos(sg.ang)) / S * dir;

    return {x:px, y:py, ang, seg:sg, off, dirSign:dir, cross};
  }

  function obstacleAhead(){
    // 전방 장애물까지 거리(m). 게임 내부 정보 사용(교사 전용)
    return gap(me, 40*S) / S;
  }

  /* ★보행자 전방거리(a_5057). 왜 별도 함수인가:
     gap() 은 peds 를 '보기는 한다'(rebuildHash 가 peds 를 hgrid 에 넣는다).
     하지만 횡방향 게이트가 LW*0.62 = 2.02m 라, 차로 가장자리로 뛰어드는 보행자가
     그 밖에 있으면 gap 이 아예 못 본다. 게다가 gap 은 '가장 가까운 물체 하나'의
     거리만 돌려주므로, 앞차가 25m 에 있으면 12m 의 보행자가 그 값에 가려진다.
     → 보행자만 따로, 더 넓은 횡방향(4m)으로 훑는다.
     이미 지나친 보행자(f<=0)는 제외 — 뒤에서 걷는 사람 때문에 서면 안 된다. */
  function pedAhead(){
    if(typeof peds==='undefined' || !peds || !peds.length) return 1e9;
    const ca=Math.cos(me.ang), sa=Math.sin(me.ang);
    let best=1e9;
    for(const p of peds){
      const dx=p.x-me.x, dy=p.y-me.y;
      const f=(dx*ca+dy*sa)/S;                 // 전방거리(m). 음수면 이미 지나쳤다
      if(f<=0 || f>=PED_SLOW_M) continue;
      const l=Math.abs(-dx*sa+dy*ca)/S;        // 횡방향 거리(m)
      if(l>PED_LAT_M) continue;
      if(f<best) best=f;
    }
    return best;
  }

  /* 교사 조작값 산출 — 조향 -1~1, 스로틀 0~1, 브레이크 0~1 */
  T.compute = function(){
    const lt = laneTarget();
    if(!lt) return {steer:0, thr:0, brake:1, ok:false};
    let diff = ((Math.atan2(lt.y-me.y, lt.x-me.x) - me.ang + Math.PI*3) % (Math.PI*2)) - Math.PI;
    if(T.mode==='rev'){
      // 후진: 뒤로 가되 차로를 벗어나지 않게
      const back = ((lt.ang + Math.PI - me.ang + Math.PI*3)%(Math.PI*2))-Math.PI;
      return {steer: Math.max(-1,Math.min(1, -back*1.2)), thr:0, brake:1, rev:1, ok:true};
    }
    /* 좌/우 회전 모드: 교차로에서 해당 방향 도로를 목표로 삼는다 */
    if(T.mode==='left'||T.mode==='right'){
      const want = T.mode==='left' ? -1 : 1;
      const nd = nearestNode(me.x,me.y);
      const N = nodes[nd];
      if(N && Math.hypot(N.x-me.x,N.y-me.y) < 30*S && N.e.length>2){
        let best=null,bestScore=-9;
        for(const si of N.e){
          const sg2=segs[si];
          const a2=(sg2.a===nd)?sg2.ang:sg2.ang+Math.PI;
          let rel=((a2-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
          const sc = want*rel;                    // 원하는 방향일수록 큼
          if(Math.abs(rel)>0.35 && sc>bestScore){bestScore=sc;best=a2}
        }
        if(best!==null) diff = ((best-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
      }
    }
    const d = obstacleAhead();
    let brake = 0, thr = 1;
    if(d < 9){ brake = 1; thr = 0; }            // 앞 막힘 → 정지
    else if(d < 18){ brake = 0.4; thr = 0.15; } // 접근 → 감속
    /* ★보행자 제동(a_5057). 사고 연쇄의 시작점이 보행자 충돌이었다.
       25m 안이면 감속, 12m 안이면 정지. 차량 제동보다 항상 우선(Math.max)한다 —
       앞차 기준으로 이미 계산된 brake 를 덮어쓰지 않고 더 강한 쪽을 쓴다. */
    const pd = pedAhead();
    if(pd < PED_STOP_M){ brake = 1; thr = 0; }
    else if(pd < PED_SLOW_M){
      brake = Math.max(brake, 0.5);
      thr = Math.min(thr, 0.12);
    }
    /* ★적신호 정지(u_4978). 신호등은 91개가 깔려 있었지만 교사가 아예 보지
       않아서, 데이터에 '빨간불에 선다'가 한 프레임도 없었다.
       내 진행방향과 같은 방향을 바라보는 신호만 대상으로 한다(맞은편 신호 무시).
       ★정지선을 넘었으면(뒤에 있으면) 그냥 통과한다 — 교차로 한가운데 서면 더 위험하다. */
    if(typeof signals!=='undefined' && signals.length){
      const now=performance.now();
      const fx=Math.cos(me.ang), fy=Math.sin(me.ang);
      let sd=1e9;
      for(const sg of signals){
        const dx=sg.x-me.x, dy=sg.y-me.y;
        const f=(dx*fx+dy*fy)/S;                       // 전방거리(m)
        if(f<1.5 || f>38) continue;                    // 이미 지났거나 너무 멂
        if(Math.abs(-dx*Math.sin(me.ang)+dy*Math.cos(me.ang))/S > 7) continue;  // 옆 도로
        let rel=((sg.ang-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
        if(Math.abs(rel)>0.9) continue;                // 내 방향 신호가 아님
        if(sigRed(sg, now) && f<sd) sd=f;
      }
      if(sd<1e9){
        if(sd<10){ brake=1; thr=0; }                   // 정지선 앞 → 정지
        else if(sd<22){ brake=Math.max(brake,0.5); thr=Math.min(thr,0.1); }
      }
    }
    // 커브에서 감속
    const bend = Math.min(1, Math.abs(diff)/0.7);
    thr *= (1 - 0.6*bend);
    /* ★목표 속도 추종(u_4975). 오너: "내가 원하는 주행 속도를 설정하면
       그 속도에 맞게 끼어들기나 추월을 할 수도 있으니까".
       기존 교사는 thr=1 고정이라 '늘 최고속'이었고, 그 데이터로 배운 모델은
       속도 개념 자체가 없었다. 목표속도(km/h)를 빌드로 주고 교사가 거기에 맞춘다.
       ★앞이 막히거나(d<18) 커브면 위 로직이 우선이다 — 목표속도가 안전보다
         앞서면 안 된다("뭐 바뀌면 당연히 천천히 가야 되겠지만"). */
    /* ★목표속도는 '정상상태 속도'로 환산해서 맞춘다(u_4975 수정).
       처음엔 err 에 비례해 thr 을 깎았는데, 그러면 목표에 가까워질수록
       thr 이 같이 줄어 훨씬 아래에서 눌러앉는다(droop).
       실측: 목표 50 → 실제 37km/h 에서 정체(thr 0.79).
       여기서는 '이 thr 이면 결국 몇 m/s 가 되는가'가 cap*thr 이라는 점을 이용해
       필요한 thr 을 역산하고, 커브·전방 감속분(thr0)을 상한으로 씌운다. */
    const TGT = (window.__TARGET_KMH || 45) / 3.6;       // m/s
    if(brake === 0){
      const cap = TGT * 1.12;                            // thr=1 일 때 도달 속도
      const need = Math.max(0, Math.min(1, TGT / cap));  // 목표 유지에 필요한 thr(≈0.89)
      // 아직 목표보다 느리면 잠깐 더 밟아 가속을 붙인다
      const boost = me.v < TGT - 0.5 ? 1 : need;
      thr = Math.min(thr, boost);
      if(me.v > TGT + 2.0) { thr = 0; brake = Math.min(0.4, (me.v - TGT - 2.0) * 0.15); }
    }
    /* ★2026-09-14 실브라우저 실측 수정: 기존 조향은 heading-error(diff)만 썼다.
       그래서 차로와 나란히 달리되 옆으로 6m 벗어난 상태에서는 diff≈0 →
       조향 0 → 이탈을 영원히 못 고쳤다(측정: ln 2.4→6.6m 단조 증가).
       Stanley 방식으로 횡방향 오차(cross-track) 항을 더한다. */
    /* cross-track 은 laneTarget 이 '목표 차로 중심선' 기준으로 이미 계산했다.
       예전엔 여기서 lane=0 으로 다시 계산해, 목표는 3차로인데 보정은 1차로로
       끌어당기는 모순이 생겼다(u_4992 실사고). 한 곳에서만 정한다. */
    const ns = nearestSeg(me.x,me.y);
    const cross = lt.cross || 0;
    const spd = Math.max(3, me.v);
    const xt = Math.atan2(0.9*cross, spd);               // 속도가 빠를수록 완만하게
    /* ★차선변경 중에는 cross-track 을 약하게 건다(u_5001 실측).
       이 항은 '차로 중심으로 되돌리는' 힘이라, 3.2m 를 통째로 옮기는 동작에는
       과하게 작용해 제어기가 스스로와 싸운다(실측: 폭 0.7m 에 그치고 속도가
       45→14→1km/h 로 주저앉았다). 변경 중에는 목표점 추종(diff)에 맡기고,
       끝나면 원래 세기로 돌아와 차로 중심을 잡는다. */
    /* ★cross-track 이 크면 그 자체로 조향을 포화시킨다(P1 재진단, u_5020).
       실측: ct=9.7m 인 상태에서 xt항 1.54 + diff항 1.09 → 합 2.6 → ±1 로 잘림.
       포화되면 '얼마나 꺾을지'가 사라지고 항상 최대조향이 되어, 학습 라벨이
       상수가 된다(조향 포화 97%).
       원인은 목표 차로와 실제 위치가 멀리 벌어진 채 유지되는 것 —
       laneF 가 목표에 도달해 laneMoving=false 가 되면 감쇠도 풀려 더 세게 당긴다.
       → 오차가 한 차로(3.25m)를 넘으면 '지금 있는 차로'로 목표를 재설정한다.
         사람도 3차로를 목표로 잡았다가 못 가면 지금 차로에서 다시 판단한다. */
    if(Math.abs(cross) > 3.25 && !T.laneMoving){
      const nl2 = lt.seg.o ? lt.seg.l : Math.max(1, Math.floor(lt.seg.l/2));
      const cur = Math.max(0, Math.min(nl2-1, Math.round(Math.abs(lt.off)/(LW/S) - 0.5)));
      T.lane = cur; T.laneF = cur;      // 현재 차로에서 다시 시작
    }
    /* 큰 횡오차에서 xt 항이 단독으로 포화시키지 않게 상한을 둔다.
       조향의 주도권은 목표점 추종(diff)이 갖고, xt 는 보정 역할로 제한한다. */
    const xtK = T.laneMoving ? 0.5 : 1.6;
    const xtTerm = Math.max(-0.6, Math.min(0.6, xt*xtK));
    const steer = Math.max(-1, Math.min(1, diff*1.8 + xtTerm));
    // 진단(u_5020): 어느 항이 포화를 만드는지 화면으로 본다
    T.dbg = {d: diff*1.8, x: xt*xtK, cross: cross};
    return {steer, thr, brake, rev:0, ok:true,
            lane_off: (ns?ns.d:0)/S, obst:d};
  };

  /* 교사가 직접 차를 몬다(키 입력 없이 물리에 직접 반영) */
  T.drive = function(dt){
    const a = T.compute();
    if(!a.ok) return a;
    /* ★내비 경로가 있으면 교사는 조향하지 않는다(u_5036/5037 실사고).
       오너: "왜 자꾸 좌회전을 하는거야", "경로는 직진으로 되있잖아".
       화면 실측이 정확히 그랬다 —
         AUTO(경로주행) st=-0.00 df=-0.00 d=0.7m  ← 경로는 직진, 오차 0
         KB(교사)       st=1.00                   ← 교사는 좌회전 최대
       경로주행이 맞게 계산해도 교사가 me.steer 를 덮어써서 차가 좌회전했다.
       경로가 살아 있는 동안 조향 주도권은 경로에 있다. */
    if(typeof auto!=='undefined' && auto.on && auto.wp && auto.wp.length>1){
      return a;                       // 라벨은 그대로 내보내되 차는 건드리지 않는다
    }
    me.steer = a.steer;
    if(a.rev){ me.v += (-3.0 - me.v)*Math.min(1, dt*2.2); }
    else if(a.brake > 0.5){ me.v -= 9.0*dt; if(me.v<0) me.v=0; }
    /* ★thr=1 일 때의 상한을 목표속도에 맞춘다(u_4975).
       예전엔 14m/s(=50km/h) 고정이라, 커브 감속(thr*0.4~1)이 겹치면
       목표를 50으로 줘도 실제로는 36km/h 언저리에서 더 못 올라갔다. */
    else { const cap = (window.__TARGET_KMH || 45)/3.6 * 1.12;
           me.v += (a.thr*cap - me.v)*Math.min(1, dt*1.8); }
    return a;
  };

  T.setMode = m => { T.mode = m; return T.mode; };
  /* 차로 지정 — 0 = 중앙선쪽 1차로, 커질수록 바깥(우측). 화면 readout 에 표시된다 */
  T.lane = 0;
  T.setLane = k => { T.lane = Math.max(0, k|0); T.laneSet = true; return T.lane; };

  /* ★자율 수집 모드 — AppleScript 없이 페이지 안에서 스스로 돈다(u_4926).
     Chrome이 기본으로 AppleScript JS 실행을 막아두기 때문에 외부 호출 대신
     게임 루프가 직접 교사를 굴리고, 조작값을 화면 하단에 '색 막대'로 표시한다.
     파이썬은 화면만 캡처해서 [픽셀 ↔ 조작] 쌍을 만든다(로직 전달 없음). */
  T.auto = false;
  T.dagger = false;          // 교사=정답만 계산(주행은 모델이). build.py --dagger 로 켠다
  /* ★교사 순회(2026-09-14 데이터 검사 결과 대응).
     교사를 그냥 두면 같은 길만 왕복해서 데이터가 한쪽으로 쏠린다
     (실측: 29,121프레임에 신호등 0개, 브레이크 9개, 조향 좌78%/우2%).
     일정 시간마다 강제로 다른 도로에 재배치해 골고루 돌게 한다. */
  /* 교사 순회는 제거했다 — 12초마다 리셋하니 주행이 계속 끊겼다.
     데이터 편중의 원인은 신호등 데이터 누락이었지 교사 경로가 아니었다. */
  T.last = {steer:0, thr:0, brake:0, rev:0};
  window.__teachAuto = function(on, mode){
    T.auto = !!on; if(mode) T.mode = mode;
    return T.auto;
  };
  /* 조작값을 화면에 그린다 — 파이썬이 눈으로 읽는 라벨 */
  T.drawLabel = function(){
    if(!T.auto) return;
    const a=T.last, x=6, y=H-16, w=18, h=10;
    const bar=(i,v,col)=>{           // v: -1~1 → 막대 길이
      g.fillStyle='rgba(0,0,0,.55)'; g.fillRect(x+i*(w+3), y, w, h);
      g.fillStyle=col;
      const t=Math.max(0,Math.min(1,(v+1)/2));
      g.fillRect(x+i*(w+3), y, w*t, h);
    };
    bar(0, a.steer,        '#4da3ff');   // 조향 -1~1
    bar(1, a.thr*2-1,      '#2fe06a');   // 스로틀 0~1
    bar(2, a.brake*2-1,    '#ff4d4d');   // 브레이크 0~1
    bar(3, a.rev*2-1,      '#ffd23f');   // 후진 0/1
    /* ★2026-09-14: 라벨 막대는 픽셀로 되읽기가 불안정했다(브라우저 UI와 색 충돌).
       DevTools 콘솔은 top 프레임에서 돌아 __teach 를 못 본다(샌드박스 iframe).
       → 상태를 캔버스에 숫자로 직접 찍어서 스크린샷으로 정확히 읽는다. */
    /* ★기계 판독용 코드픽셀(2026-09-14): OCR·막대길이 추정은 불안정했다.
       조작값을 8비트 색으로 직접 찍는다 → 파이썬이 픽셀 하나만 읽으면 정확한 값.
       좌상단 (0,0)~(5,0): [마커, steer, thr, brake, rev, speed] */
    const enc=(v)=>Math.max(0,Math.min(255,Math.round(v*255)));
    const CY=y-30, CX=6;   // 라벨 막대 바로 위(가시영역 확인됨)
    const put=(i,r,gg,b)=>{ g.fillStyle='rgb('+r+','+gg+','+b+')'; g.fillRect(CX+i*6,CY,6,6); };
    put(0, 0xA5, 0x5A, 0xC3);                                  // 고정 마커
    put(1, enc((a.steer+1)/2), enc(a.thr), enc(a.brake));      // 조향·스로틀·브레이크
    put(2, enc(a.rev), enc(Math.min(1,me.v/40)), enc(Math.min(1,(a.lane_off||0)/12)));
    put(3, me.crashes&255, crashHold?255:0, enc(Math.min(1,(a.obst||99)/40)));

    g.font='11px ui-monospace,Menlo,monospace';
    g.fillStyle='#000'; g.fillRect(x, y-16, 210, 13);
    g.fillStyle='#7CFF9E';
    const kmh=(me.v*3.6)|0, lane=((nearestSeg(me.x,me.y)||{d:0}).d/S).toFixed(1);
    const logged = (window.__log ? window.__log.n : -1);   // -1 = db 미연결
    g.fillText('KB v='+kmh+' st='+a.steer.toFixed(2)+' th='+a.thr.toFixed(2)
               +' br='+(a.brake||0).toFixed(2)
               +' ln'+(T.lane+1)+'->'+(T.laneF!==undefined?(T.laneF+1).toFixed(2):'-')
               +'/'+(T.laneMax||'?')
               +' D='+(window.__laneDemo||'-')
               +' GO='+(window.__goHit||0)+'/'+(window.__planFail||0)
               +' | diff='+(T.dbg?T.dbg.d.toFixed(2):'-')
               +' xt='+(T.dbg?T.dbg.x.toFixed(2):'-')
               +' ct='+(T.dbg?T.dbg.cross.toFixed(1):'-')
               +' br='+(a.brake||0).toFixed(2)
               +' cr='+me.crashes+' ln='+lane+' LOG='+logged, x+2, y-6);
  };
  T.state = () => ({mode:T.mode, v:me.v, crashes:me.crashes, crashHold:crashHold,
                    onRoad:onRoad(me.x,me.y).ok, laneOff:(nearestSeg(me.x,me.y)||{d:0}).d/S});
  window.__teach = T;
  /* URL로 바로 켠다: ?teach=fwd | rev | left | right  (외부 호출 불필요) */
  /* ★아티팩트는 샌드박스 iframe 안에서 돈다 → iframe의 location.search에는
     주소창에 친 ?teach=... 가 없다(실측: 새 탭·캐시무력화 모두 실패).
     그래서 상위 프레임 URL까지 훑고, 그마저 막히면 그냥 켠다. */
  /* ★2026-09-14: 샌드박스 iframe은 주소창 ?teach= 를 절대 못 본다(콘솔 실측).
     → URL 게이트 폐기. localStorage 로 모드를 받고, 없으면 fwd 로 기본 가동.
     외부에서 모드 변경: window.__teach.set('left') 또는 localStorage.kb_teach='left' 후 리로드. */
  let mode='fwd';
  try{ const v=localStorage.getItem('kb_teach'); if(v && /^(fwd|rev|left|right|off)$/.test(v)) mode=v; }catch(e){}
  T.set = (v)=>{ try{localStorage.setItem('kb_teach',v)}catch(e){}; T.mode=v; T.auto=(v!=='off'); };
  /* ★키보드 토글(2026-09-14): 모델 검증 때 교사를 꺼야 하는데,
     샌드박스 iframe이라 밖에서 JS를 못 넣는다(콘솔·AppleScript 둘 다 차단).
     그래서 페이지가 직접 키를 받는다 — T = 교사 on/off.
     끄면 차는 키보드 입력(파이썬이 넣는 방향키)만 따른다. */
  /* 키 이벤트는 iframe 포커스에 따라 안 들어올 수 있다(실측: T 눌러도 교사가 안 꺼짐).
     그래서 (1) 캔버스·window·document 전부에 리스너를 달고
            (2) localStorage 를 주기적으로 다시 읽어 외부에서도 끌 수 있게 한다. */
  const onKey=(e)=>{
    if(e.key==='t' || e.key==='T'){
      T.auto = !T.auto;
      try{ localStorage.setItem('kb_teach', T.auto ? (T.mode||'fwd') : 'off'); }catch(_){}
    }
  };
  for(const t of [window, document, document.querySelector('canvas')]){
    if(t) t.addEventListener('keydown', onKey, true);
  }
  setInterval(()=>{
    try{
      const v=localStorage.getItem('kb_teach');
      if(v==='off' && T.auto) T.auto=false;
      else if(v && v!=='off' && !T.auto){ T.auto=true; T.mode=v; }
    }catch(_){}
  }, 300);
  const m = (mode==='off') ? null : [null, mode];
  if(m){
    T.auto=true; T.mode=m[1];
    /* ★교사는 자기 출발 위치를 스스로 잡는다(2026-09-14 실제 브라우저 검증).
       게임의 hardReset()이 차를 주차칸(도로 밖 13m)에 세워둬서,
       교사를 켜도 화면에서는 차가 그대로 서 있었다 —
       시뮬레이터에서는 통과했지만 실제로는 전진이 시작되지 않았다. */
    let bs=null,bl=0;
    for(const q of segs){ if(q.len>bl){bl=q.len;bs=q} }
    if(bs){
      const A=nodes[bs.a],B=nodes[bs.b], off=laneOffset(bs,1,0), t0=0.12;
      me.x=A.x+(B.x-A.x)*t0-Math.sin(bs.ang)*off;
      me.y=A.y+(B.y-A.y)*t0+Math.cos(bs.ang)*off;
      me.ang=bs.ang; me.v=0; me.crashes=0; me.dmg=0;
      streamWorld(true);
    }
  }
})();

/* ===== 학습데이터 업로드 (2026-09-14) =====================================
   왜 필요했나: 교사 조작값을 밖으로 빼내는 데 아래가 전부 실패했다.
     1) URL ?teach= → 샌드박스 iframe은 주소창 파라미터를 못 본다.
     2) DevTools 콘솔 → 콘솔은 top 프레임에서 돌아 __teach 가 안 보인다.
     3) AppleScript JS 실행 → Chrome이 기본 차단.
     4) 캔버스 색상 코드픽셀 → 프레임 합성으로 색이 뭉개져(A55AC3 → 5862 93) 판독 불가.
   → 페이지가 스스로 db에 기록하고, 오케가 read_db로 정확한 값을 회수한다.
   화면 픽셀은 파이썬이 따로 캡처해 같은 타임스탬프로 맞춘다.                     */
(async function(){
  /* ★2026-09-14 u_4969: db 기록 중단.
     라벨은 화면 코드픽셀(game.js draw() 말미)로 전달한다 — 용량 제약이 없고
     픽셀과 라벨이 같은 프레임이라 시간 어긋남도 없다.
     db 는 run 66개(≈20만 프레임)가 쌓여 'Storage full' 배너가 캔버스 상단을
     덮었고, 그 배너가 바로 코드픽셀 자리를 가려 디코딩이 전부 실패했다.
     되살리려면 이 return 을 지우기 전에 기존 runs/* 를 먼저 비울 것. */
  return;
  if(!window.claude || !claude.use) return;
  const db = await claude.use('db').catch(()=>null);
  if(!db) return;
  let VIS = false;
  try{
    const c = document.querySelector('canvas');
    if(c) new IntersectionObserver((es)=>{ VIS = es.some(e=>e.isIntersecting && e.intersectionRatio>0.3); },
                                   {threshold:[0,0.3,0.6]}).observe(c);
  }catch(e){ VIS = true; }
  const RUN = 'run_' + Date.now();
  /* 상위에 인덱스 문서를 남긴다 — 서브컬렉션만 쓰면 runs 목록이 비어 보여
     오케가 run id를 찾을 수 없다(실측: list runs → 0건). */
  try{ await db.doc('index/'+RUN).set({run:RUN, started:Date.now()}); }catch(e){}
  let buf = [], n = 0;
  window.__log = {run:RUN, get n(){return n}, buf};
  setInterval(async ()=>{
    /* ★배경 프레임 제외(2026-09-14 실측): 아티팩트는 프레임이 여러 개 뜨고,
       보이지 않는 인스턴스는 교통·환경이 없어 steer=0/thr=1 만 찍힌다.
       그 데이터로 학습하면 '무조건 직진'만 배운다. 보이는 프레임만 기록. */
    /* ★보이는 프레임만 기록(2026-09-14 실측).
       아티팩트는 같은 페이지를 여러 프레임에 띄우는데, 화면 밖 인스턴스는
       visibilityState 가 'visible' 이고 캔버스 크기도 정상이라 그것만으로는 못 거른다.
       실제로 그 스트림은 v=12.67·steer=0·obst=40(아무것도 안 보임)에 고정돼 있었고,
       눈에 보이는 차는 v=45로 조향하며 달리고 있었다 — 즉 전혀 다른 인스턴스다.
       IntersectionObserver 로 '진짜 화면에 들어와 있는지'를 직접 확인한다. */
    if(!VIS) return;
    const T=window.__teach; if(!T) return;
    /* ★DAgger(2026-09-14 강화학습 단계): 교사가 '주행'은 안 하고 '정답'만 계산해도 기록한다.
       모델이 운전하는 동안 교사에게 "너라면 여기서 뭐 했겠냐"를 물어 같이 저장하면,
       모델이 실제로 겪는 상황(이탈 직전·사고 직전)만 골라 배울 수 있다.
       교사가 혼자 달린 데이터는 교사가 잘 가는 길만 담겨 있어서 그게 안 된다. */
    if(!T.auto && !T.dagger) return;
    if(T.dagger && !T.auto){ try{ T.last = T.compute(); }catch(_){} }
    const a = T.last || {};
    const st = (T.state?T.state():{}) || {};
    buf.push({t:Date.now(), steer:+(a.steer||0).toFixed(4), thr:+(a.thr||0).toFixed(4),
              brake:+(a.brake||0).toFixed(4), rev:a.rev||0, v:+(st.v||0).toFixed(2),
              lane:+((a.lane_off||0)).toFixed(2), obst:+((a.obst===undefined?99:a.obst)).toFixed(1),
              cr:st.crashes||0, hold:st.crashHold?1:0, mode:st.mode});
    if(buf.length >= 50){
      const chunk = buf.splice(0, buf.length);
      n += chunk.length;
      try{
        await db.doc('runs/'+RUN+'/frames/f'+String(n).padStart(6,'0')).set({rows:chunk});
        await db.doc('index/'+RUN).update({frames:n, updated:Date.now()});
      }catch(e){}
    }
  }, 50);   // 20Hz
})();

/* ===== 교사 주행 API (u_4926) =====
   게임 내부 좌표로 '정확한 주행'을 수행한다. 이건 학습자료를 만드는 도구일 뿐,
   최종 주행 모델에는 들어가지 않는다(로직주행 금지 원칙 유지).

   제공 동작: 전진(차로중앙 유지) / 후진 / 좌회전 / 우회전
   파이썬은 window.__teach 로 호출하고, 화면 픽셀 ↔ 그때의 조작값을 쌍으로 수집한다. */
(function(){
  const T = {mode:'fwd', log:[], on:false};

  /* ★보행자 제동 파라미터 — game.js 의 공용 상수를 그대로 쓴다.
     예전엔 여기서 횡 4m 를 따로 들고 있었다. driveAuto 는 2.2m + 차도 점유를
     봤기 때문에, 내비 주행 중(driveAuto 가 조향·교사는 제동 거부권만) 둘이 매
     프레임 다르게 판단했다. 상수까지 공용으로 둬야 그 갈라짐이 안 돌아온다. */
  T.PED = {slow:PED_SLOW_M, stop:PED_STOP_M, lat:PED_CROSS_LAT_M};

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
  /* 앞차 정보(거리 m, 속도). gap() 과 같은 규칙. */
  function leadCar(){
    let best=null, bd=40;
    const ca=Math.cos(me.ang), sa=Math.sin(me.ang);
    for(const o of (typeof cars!=='undefined'?cars:[])){
      const dx=o.x-me.x, dy=o.y-me.y;
      const f=(dx*ca+dy*sa)/S;
      if(f<=0||f>=bd) continue;
      if(Math.abs((-dx*sa+dy*ca)/S) < LW/S*0.62){ bd=f; best={gap:f, v:o.v}; }
    }
    return best;
  }
  function leadGap(){ const l=leadCar(); return l?l.gap:99; }
  /* 목표 차로가 비었는지 — 앞 45m, 뒤 18m */
  function laneFree(laneIdx, dir, sg, nl){
    const off = laneOffset(sg, dir, laneIdx);
    const px = me.x - Math.sin(sg.ang)*off, py = me.y + Math.cos(sg.ang)*off;
    const ca=Math.cos(me.ang), sa=Math.sin(me.ang);
    for(const o of (typeof cars!=='undefined'?cars:[])){
      const dx=o.x-px, dy=o.y-py;
      const f=(dx*ca+dy*sa)/S, l=(-dx*sa+dy*ca)/S;
      if(Math.abs(l) > LW/S*0.70) continue;
      if(f < 18 && f > -45) return false;
    }
    return onRoad(px,py).ok;
  }
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

    /* ★추월 판단은 교사가 한다(u_5123 오너 지시).
       처음에 driveAuto(기하 제어기)에만 넣었는데, 그건 모델이 배우지 못한다.
       교사가 시연해야 라벨로 남고, 그 라벨로 학습해야 모델이 스스로 추월한다.
       "추월도 모댈로 학습되야한다고" — 맞는 지적이다.

       사람이 판단하는 순서 그대로:
         1) 앞차가 22m 안이고 나보다 느린가(0.85배 미만)
         2) 옆 차로가 비었나 — 앞 45m / 뒤 18m (뒤를 봐야 추월해오는 차 앞에 안 낀다)
         3) 추월차로는 왼쪽(차로 인덱스가 작은 쪽)이 원칙
         4) 편도 1차로면 추월 불가(법규)
       앞이 트이면 원래 차로로 돌아온다. */
    if(nl >= 2){
      const lead = leadCar();
      if(!T.ot) T.ot = {on:0, from:0, t:0};
      if(T.ot.on){
        T.ot.t += 1/60;
        const g = leadGap();
        if((T.ot.t > 1.2 && g > 30) || T.ot.t > 9.0){ T.ot.on = 0; }   // 복귀
        else want = T.ot.lane;
      }else if(lead && lead.gap < 22 && lead.v < me.v*0.85){
        /* ★왼쪽이 막혔으면 오른쪽으로 비켜간다(u_5151 오너 지시).
           "왼쪽 차선이 비었을경우 추월해야하고, 왼쪽이 막혀있고 오른쪽이 비었다면
            오른쪽차선으로 변경해서 직진해야지"
           기존엔 왼쪽만 보고, 막히면 그냥 뒤에 서 있었다 — 그게 지금 정체의 원인이다.
           우선순위: 왼쪽(추월차로가 원칙) → 안 되면 오른쪽(진로 변경). */
        const cands = [want - 1, want + 1];          // 왼쪽 먼저, 그 다음 오른쪽
        for(const c of cands){
          if(c < 0 || c > nl-1 || c === want) continue;
          if(!laneFree(c, dir, sg, nl)) continue;
          T.ot = {on:1, from:want, lane:c, t:0, side:(c<want?'L':'R')};
          window.__otN = (window.__otN||0) + 1;      // 추월/진로변경 횟수 계측
          want = c;
          break;
        }
      }
    }
    /* ★u_5182 차로 선택 규칙(도로교통법 기준).
         · 기본은 주행차로 = 가장 오른쪽(인덱스 nl-1)이 아니라 1차로쪽부터.
           이 게임의 인덱스는 0 이 중앙선쪽이므로, 우측통행 기준 주행차로는
           인덱스가 큰 쪽이다. 다만 경로점이 지정한 차로가 우선한다.
         · 좌회전이 임박하면 가장 왼쪽(0), 우회전이면 가장 오른쪽(nl-1).
         · 차로가 줄면 남는 차로 안으로, 늘면 지금 차로를 유지한다.
       회전 판단은 aheadTurn/aheadDist 로 앞을 미리 본다(위에서 계산). */
    /* ★u_5182 오너 지시: 차선 판단에 필요한 정보를 갖춘다.
       "현재 도로 몇차선 / 내가 몇차선 / 회전하려면 몇차선 / 차로 증감시 어디로".
       지금은 현재 차로수(nl)와 내 차로(laneF)뿐이라 앞을 못 본다.
       경로 앞쪽 웨이포인트로 다음 구간의 도로를 찾아 미리 읽는다. */
    let aheadNl = null, aheadTurn = null, aheadDist = null;
    try{
      if(typeof auto!=='undefined' && auto.wp && auto.wp.length){
        const i0 = Math.min(auto.i, auto.wp.length-1);
        for(let k=i0+1; k<auto.wp.length; k++){
          const w = auto.wp[k];
          const dm = Math.hypot(w.x-me.x, w.y-me.y)/S;
          if(dm > 200) break;                   // ★200m 넘으면 경로 인덱스가 뒤처진 것
                                                //   (실측 8280m 이 나왔다 — 뒤쪽 점을 잡음)
          if(dm < 12) continue;                 // 너무 가까운 점은 현재 구간
          const n2 = nearestSeg(w.x, w.y);
          if(!n2 || !n2.s) break;
          if(n2.s === sg) continue;             // 아직 같은 도로
          const nl2 = n2.s.o ? (n2.s.l||1) : Math.max(1, Math.floor((n2.s.l||2)/2));
          aheadNl = nl2; aheadDist = +dm.toFixed(0);
          /* 회전 방향: 다음 도로 방향과 현재 도로 방향의 차이.
             좌회전이면 왼쪽 차로(인덱스 작은 쪽), 우회전이면 오른쪽 끝 차로. */
          let rel = ((n2.s.ang - sg.ang + Math.PI*3) % (Math.PI*2)) - Math.PI;
          aheadTurn = Math.abs(rel) < 0.35 ? 'S' : (rel < 0 ? 'L' : 'R');
          break;
        }
      }
    }catch(e){ T._aErr = String(e).slice(0,80); }
    /* ★이 블록은 laneTarget() 본문이라 예외가 나면 함수가 통째로 죽고
       g2 가 통째로 사라진다(실측: 전 필드 None). 반드시 감싼다. */
    let ruleWant = null;
    try{
      if(aheadTurn && aheadDist !== null && aheadDist < 80){
        if(aheadTurn === 'L') ruleWant = 0;
        else if(aheadTurn === 'R') ruleWant = nl - 1;
      }
      if(aheadNl !== null && aheadNl < nl){
        // 차로가 줄어든다 → 사라질 차로에 있으면 미리 남는 쪽으로
        ruleWant = Math.min(ruleWant === null ? (T.laneF|0) : ruleWant, aheadNl - 1);
      }
    }catch(e){ ruleWant = null; T._rErr = String(e).slice(0,60); }
    if(typeof auto!=='undefined' && auto.on && auto.wp && auto.wp.length){
      const w = auto.wp[Math.min(auto.i, auto.wp.length-1)];
      if(w){
        // 경로점이 중심선에서 얼마나 떨어져 있나 → 차로 인덱스로 환산
        const lat = (-(n.px-w.x)*Math.sin(sg.ang) + (n.py-w.y)*Math.cos(sg.ang)) / S * dir;
        /* ★u_5180: laneOffset 의 원점을 도로 좌측 가장자리로 고쳤으므로
           (game.js: -(roadW/2) + (lane+0.5)*LW), 역산도 같은 원점을 써야 한다.
           u_5176 에서 lat/LW-0.5 로 바꿨던 건 laneOffset 이 중심선 기준이던
           시절의 임시방편이었다 — 지금은 틀렸다. 이게 안 맞으면 want 가
           매 프레임 다른 값을 내고, laneF 가 7.0→0.7 처럼 도로를 훑는다
           (실측: 8차로에서 목표가 한쪽 끝에서 반대쪽 끝까지 흘렀다). */
        const gi  = sg.o ? ((lat + (sg.roadW/2)/S)/(LW/S) - 0.5)
                         : (Math.abs(lat)/(LW/S) - 0.5);
        want = Math.max(0, Math.min(nl-1, Math.round(gi)));
        // 회전·차로감소 규칙이 있으면 그쪽이 우선한다(경로점은 직진 기준이다)
        if(ruleWant !== null) want = Math.max(0, Math.min(nl-1, ruleWant));
        T._want = want;   // dbg2 로 넘기기 위한 전달용(스코프가 다르다)
      }
    }
    /* ★첫 프레임의 laneF 는 '목표'가 아니라 '차가 지금 실제로 있는 차로'여야 한다
       (u_5001 실사고). 목표로 초기화하면, 차가 다른 차로에 있을 때 시작부터
       큰 횡오차가 생겨 조향이 곧바로 포화된다(steer 0.98 고정, 표준편차 0.000). */
    if(T.laneF === undefined){
      const lat0 = (-(n.px-me.x)*Math.sin(sg.ang) + (n.py-me.y)*Math.cos(sg.ang)) / S * dir;
      // lat0: 중심선 기준 부호거리(m) → 차로 인덱스로 환산
      const guess = sg.o ? ((lat0 + (sg.roadW/2)/S)/(LW/S) - 0.5)
                         : (Math.abs(lat0)/(LW/S) - 0.5);   // laneOffset 역함수(위와 동일)
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
    /* ★u_5171 실측으로 이 완만한 clamp 가 원인임이 드러났다.
       분해 결과: 차는 도로 중심선에서 0.72m 떨어져 정상 주행 중인데,
       목표 차로 오프셋이 7.88m 였다(도로폭 9.6m). 즉 목표점이 도로 밖이다.

       원인 — 3차로에서 1차로 도로로 들어가면 laneF 2 → 0 으로 가야 하는데
       step 0.02 로는 100프레임(3.3초)이 걸린다. 그동안 목표는 계속 도로
       밖을 가리키고, cross 8m, 조향 포화가 유지된다.
       '한 번에 옮기지 않는다'는 원래 의도는 옳지만, 그건 같은 도로 안에서
       차선을 바꿀 때 얘기다. 도로가 아예 좁아져 그 차로가 존재하지 않으면
       천천히 갈 이유가 없다 — 없는 차로에 머무는 것이 곧 도로 이탈이다.
       ⇒ 도로 밖으로 나가는 방향의 clamp 는 즉시 적용한다. */
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
    /* ★u_5171 진단: cross 7.3m 의 출처를 분해한다.
       nd  = 차에서 세그먼트 중심선까지의 순수 거리(투영 오차)
       off = 목표 차로 오프셋(차로 인덱스가 틀리면 여기가 크다)
       둘 중 어느 쪽이 cross 를 만드는지 봐야 고칠 곳이 정해진다. */
    /* ★u_5180: nd 는 부호 없는 거리라 좌/우 구분이 안 돼 차로 판정이 불가능하다.
       cross(목표 차로 기준 부호거리)와 off(목표 차로 오프셋)로 역산하면
       중심선 기준 부호거리 = cross + off 가 된다. 새 변수를 만들지 않는다 —
       ns 를 참조했다가 예외가 나 g2 블록이 통째로 사라졌다(같은 실수 2회). */
    T.dbg2 = {err: (T._aErr||T._rErr)||null, aNl: aheadNl, aTurn: aheadTurn, aD: aheadDist, want: (T._want===undefined?null:T._want),
              lat: +((cross + off/S)).toFixed(2), sw: sg.w || null, nl: nl,
              laneF: +(+(T.laneF||0)).toFixed(2),
              off: +(off/S).toFixed(2), nd: +(n.d/S).toFixed(2),
              roadW: +((sg.roadW||0)/S).toFixed(2), o: sg.o?1:0};

    return {x:px, y:py, ang, seg:sg, off, dirSign:dir, cross};
  }

  function obstacleAhead(){
    // 전방 장애물까지 거리(m). 게임 내부 정보 사용(교사 전용)
    return gap(me, 40*S) / S;
  }

  /* ★보행자 전방거리. 왜 gap() 으로 안 되나:
     gap() 은 peds 를 '보기는 한다'(rebuildHash 가 peds 를 hgrid 에 넣는다).
     하지만 '가장 가까운 물체 하나'의 거리만 돌려주므로, 앞차가 25m 에 있으면
     12m 의 보행자가 그 값에 가려진다. → 보행자만 따로 훑어야 한다.
     그 판정은 game.js 의 pedBrakeDist() 하나뿐이다(driveAuto 와 공용). */
  function pedAhead(){ return pedBrakeDist(); }

  /* 교사 조작값 산출 — 조향 -1~1, 스로틀 0~1, 브레이크 0~1 */
  T.compute = function(){
    const lt = laneTarget();
    if(!lt) return {steer:0, thr:0, brake:1, ok:false};
    /* ★u_5173 오너 정의: "정면으로 진행하는게 직진".
       기존 diff 는 '차 위치 → 목표점' 각도였다. 그러면 직선 도로인데도
       차가 옆으로 벗어난 만큼 각도가 생긴다 — 실측 환산: 이탈 4m 면 15.9도,
       8m 면 29.7도. 도로는 곧은데 "돌아라"는 신호가 나오는 것이고,
       거기에 게인 1.8 이 곱해져 조향이 포화하고 차가 커브를 그렸다.
       ⇒ 직진의 기준은 '도로 방향과 내 방향을 맞추는 것'이다.
         차로 복귀는 그 다음이며, 이미 xtTerm 이 담당한다(±0.6 제한).
         이렇게 나누면 직선 도로에서 방향오차는 0 이 된다. */
    let diff = ((lt.ang - me.ang + Math.PI*3) % (Math.PI*2)) - Math.PI;
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
    /* ★u_5181 실측: 추종오차가 2~3.6m 인데 허용 여유는 0.72m((3.25-1.8)/2).
       3~5배 초과인데도 복귀력(xt항)은 0.23~0.33 으로 상한 0.6 의 절반만 쓴다.
       원인은 이 식의 분모가 속도라는 것 — Stanley 의 고속 안정화 항이지만,
       v=10 이면 2m 이탈에도 0.18 밖에 안 나온다(게인 1.6 곱해도 0.29).
       도로별 실측이 이를 뒷받침한다: 8차로 3% / 4차로 26% / 3차로 62% /
       1차로 69% — 넓은 도로는 오차를 흡수하고 좁은 도로만 무너진다.
       즉 '차선 개념'이 없는 게 아니라 정밀도가 여유를 못 맞추는 것이다.
       ⇒ 차로 여유를 넘긴 만큼은 속도 감쇠를 걷어낸다. 차로 안에서는
         기존대로 완만하게(잔떨림·고속 진동 방지). */
    const MARGIN = (LANE_M - 1.8) / 2;                  // 차로 여유 0.72m
    const excess = Math.max(0, Math.abs(cross) - MARGIN);
    const spdEff = excess > 0 ? Math.max(3, spd - excess * 2.2) : spd;
    const xt = Math.atan2(0.9*cross, spdEff);
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
    /* ★u_5176 오너 지적 "차선을 물고 달리는 상황이 있음".
       실측(루틴 주행 157샘플): 차로중심 이탈 평균 3.41m, 최대 12.45m,
       차로 안(±1.62m) 유지가 32% 뿐. 차로폭이 3.25m 이므로 '평균적으로
       차로 하나를 통째로 넘어간' 상태다. 68% 의 시간이 점선 위나 옆 차로다.

       원인: 차로 복귀항(xtTerm)이 ±0.6 으로 묶여 있었다. 그 상한은 예전
       diff 가 '목표점 각도'라 이미 포화 직전이던 시절, 둘이 합쳐 넘치지
       않게 하려고 둔 것이다. 이제 diff 는 도로 방향 기준(u_5173)이라
       직선에서 0 이 되므로 그 여유를 복귀에 쓸 수 있다.

       ⇒ 이탈이 차로 반폭(1.62m)을 넘으면 강하게 되돌린다.
         차로 안에서는 약하게(잔떨림 방지), 밖에서는 세게(법규 위반이므로). */
    const xtK = T.laneMoving ? 0.5 : 1.6;
    const xtTerm = Math.max(-0.6, Math.min(0.6, xt*xtK));
    let steerRaw = Math.max(-1, Math.min(1, diff*1.8 + xtTerm));
    /* ★u_5171 실측: 교사 조향이 떨고 있었다(chattering).
       포화 60%를 보고 '핸들을 끝까지 꺾은 채 유지한다'고 해석했는데 틀렸다.
       실제 포화 연속구간은 평균 3.3프레임(0.2초)뿐이고,
       프레임의 29%에서 부호가 반전하며 24%가 한 프레임에 1.0 이상 급변한다.
       +1.0 → -1.0 을 50ms 만에 오간다.

       그 떨림이 그대로 라벨이 되므로, 직진 구간에서도 라벨이 ±1 로 진동한다.
       오드가 직진을 못 배우는 진짜 이유가 이것이다(직진 라벨 3~6%).

       실제 차는 조향을 순간이동시킬 수 없다. 물리적 한계를 건다 —
       사람이 핸들을 돌리는 속도는 대략 2회전/초, 조향비를 감안하면
       정규화 조향 기준 초당 4.0 정도가 상한이다(프레임당 0.2). */
    /* ★상태는 T.last 가 아니라 전용 변수에 둔다.
       T.last 는 `T.dagger && !T.auto` 일 때만 갱신되므로(525행), 그걸 기준으로
       쓰면 값이 얼어붙고 rate limit 이 모든 출력을 그 고정값 쪽으로 붙잡는다.
       실측: 포화가 4% 예상이었는데 96% 가 나왔다(핸들이 한쪽에 고정). */
    /* ★u_5171 2차 수정: 제한을 넣었는데 실측 반전율이 27% 그대로였다.
       시뮬레이션상 4.0/s 면 4% 가 나와야 했다. 원인은 T.compute() 가
       한 프레임에 여러 곳에서 불린다는 것(호출지점 5곳: teacher 373/563,
       game 3180/3194/3228). 매 호출마다 steerPrev 가 갱신되니 제한이
       호출 횟수만큼 느슨해진다 — 3번 불리면 실질 12/s 다.
       ⇒ 프레임 단위로 한 번만 적용하고, 같은 프레임의 재호출은 그 값을 쓴다. */
    const MAXRATE = 4.0 / 60;
    const _now = (typeof performance !== 'undefined') ? performance.now() : Date.now();
    let steer;
    if(T._srFrame !== undefined && (_now - T._srFrame) < 8){
      steer = T.steerPrev;                          // 같은 프레임 재호출
    }else{
      if(typeof T.steerPrev !== 'number') T.steerPrev = steerRaw;
      steer = Math.max(T.steerPrev - MAXRATE,
                       Math.min(T.steerPrev + MAXRATE, steerRaw));
      T.steerPrev = steer;
      T._srFrame = _now;
    }
    // 진단(u_5020): 어느 항이 포화를 만드는지 화면으로 본다
    /* ★u_5171: 예전엔 상한 적용 '전' 값(xt*xtK)을 보고해서 x=1.06 처럼
       불가능한 수치가 찍혔다(실제 xtTerm 은 ±0.6 으로 잘린다). 실제 값을 쓴다. */
    T.dbg = {d: diff*1.8, x: xtTerm, cross: cross, raw: steerRaw};
    /* ★lane_off 는 '차로 중심'까지의 거리여야 한다(u_5148/5149/5150 오너 지적).
       기존엔 ns.d = **도로 중심선**까지의 거리를 넣고 있었다. 그래서 오드는
       '도로 안에만 있으면 된다'로 배웠고, 차선을 물고 달려도 라벨상 정상이었다.
       실측: xt=0.85m — 편도2차로(차로중심 1.75m)에서 중앙선 쪽으로 붙어 있다.
       도로교통법상 차선을 걸치고 달리는 건 위반이다. 학습 신호부터 고친다.
       aux 헤드(bc_train2)가 이 값을 쓰므로, 여기가 바뀌면 오드가 차로를 배운다. */
    let laneOff = (ns?ns.d:0)/S;
    if(ns && ns.s){
      const sg=ns.s, nl = sg.o ? (sg.l||1) : Math.max(1, Math.floor((sg.l||2)/2));
      const li = Math.max(0, Math.min(nl-1, Math.round(T.laneF!==undefined?T.laneF:0)));
      const want = Math.abs(laneOffset(sg, 1, li))/S;     // 내 차로 중심의 중앙선 거리
      laneOff = Math.abs(laneOff - want);                  // 차로 중심에서 벗어난 양
    }
    /* ★u_5171 v14 실패의 교훈: lane_off 는 '얼마나 벗어났나' 스칼라 1개라
       방향이 없다(좌 3m 와 우 3m 가 같은 값). 그래서 오드는 '벗어났다'는
       알아도 '어디로 피하나'를 모른 채 그 신호에 끌려다녔고, 건물 충돌이
       41건(v5) → 96건(v14) 으로 늘었다. 거리도 2948m → 1370m 로 반토막.
       net.py 의 원설계대로 좌/우 여유를 따로 준다 — 이게 있어야
       '오른쪽이 좁다 → 왼쪽으로' 같은 판단을 배울 수 있다.
       ns.d = 도로 중심선까지 거리, cross 부호로 어느 쪽인지 안다. */
    let freeL = 99, freeR = 99;
    if(ns && ns.s){
      const halfW = (ns.s.roadW || 0) * 0.5 / S;      // 도로 반폭(m)
      const lat = cross;                              // 부호: 왼쪽 -, 오른쪽 +
      freeL = Math.max(0, halfW + lat);               // 왼쪽 가장자리까지
      freeR = Math.max(0, halfW - lat);               // 오른쪽 가장자리까지
    }
    return {steer, thr, brake, rev:0, ok:true,
            lane_off: laneOff, free_l: freeL, free_r: freeR, obst:d};
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
  /* ★교사 순회는 없다(제거됨). 교사는 차를 옮기지 않고 몰기만 한다.
     한때 일정 시간마다 다른 도로로 강제 재배치해 데이터 편중을 풀려 했다
     (근거였던 실측: 29,121프레임에 신호등 0개, 브레이크 9개, 조향 좌78%/우2%).
     하지만 12초마다 리셋하니 주행이 계속 끊겼고, 편중의 진짜 원인은 경로가
     아니라 신호등 데이터 누락이었다. 배치는 game.js(placeCarNear)가 전담한다. */
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
    /* ★a_5112 P1: 교사의 중복 코드픽셀을 제거했다(라벨 오염의 원인).
       game.js:2300 이 이미 같은 마커(0xA5,0x5A,0xC3)로 16px 블록을 (0,0)에 찍는데,
       여기서 6px 블록을 (6, y-30)에 또 찍었다. 스케일도 달랐다 — game.js 는 v/20,
       교사는 v/40. decode.py 는 (0,0)에서 16px 블록을 읽으므로 보통은 game.js 가
       이기지만, 교사 막대가 판독영역에 걸치면 값이 섞인다.
       실측 증거(data/final/Y.npy 85768행): rev 는 항상 0 이어야 하는데
         corr(rev, speed) = 0.9996,  median(rev/v) = 0.0251 ≈ 1/40
       = 교사의 v/40 슬롯이 rev 자리로 새어 들어왔다. Y[:,3](aux)는 무의미하다.
       ⇒ 기록자는 game.js 하나로 통일한다. 교사는 사람이 읽는 텍스트만 그린다. */

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
    /* ★교사가 차를 옮기지 않는다(u_5076/5077 실사고, 2026-09-15).
       예전엔 여기서 '가장 긴 구간'(q.len>bl)을 골라 차를 그리로 순간이동시켰다.
       거리 조건이 없어서 그 일대 최장 간선 = 경부고속도로가 뽑혔다.
       실측 추적: hardReset 은 강남역(14,-7)에서 정상 종료하는데, 그 직후
       이 코드가 (-711,-291) 로 783m 옮겼다. 오너가 "왜 자꾸 경부고속도로로
       넘어가냐"고 다섯 번 지적한 그 현상이 전부 이것이다.
       당시 주석의 전제("hardReset 이 차를 주차칸에 세워둬서")는 이미 무효다 —
       지금 hardReset 은 강남역 최근접 시가지 도로에 정상 배치한다.
       ⇒ 출발 위치는 게임(hardReset·출발지 설정 UI)이 정한다. 교사는 몰기만 한다. */
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

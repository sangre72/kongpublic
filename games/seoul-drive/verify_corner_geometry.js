/* 코너 기하 검증 스크립트 (u_5057)
   실행: node games/seoul-drive/verify_corner_geometry.js
   ★game.js 의 경로생성 블록을 '그대로 추출'해 돌린다(재구현 드리프트 방지).
     game.js 를 고치면 아래 AUTO-EXTRACTED 블록도 다시 붙여넣어야 한다.
   검사: 90도 좌/우회전에서 (1) 모든 웨이포인트가 중앙선을 넘지 않는지,
        (2) 점 간격이 리샘플 간격(5m)의 1.2배를 넘지 않는지, (3) 직선 무회귀.
   ★중앙선 판정은 게임과 같은 규칙: nearestSeg 는 선분까지 거리(t 클램프),
     그리고 nearJunction(roadW*1.5) 안은 하드 구속 면제(game.js:1771). */
const S=6.0, LANE_M=3.25, LW=LANE_M*S;
const laneOff=(l,o)=>o?0.5*LW-(l*LW)/2:0.5*LW;
function buildNEW(p,NS){const edgeOf=()=>null;
    const RS = 5*S;                                   // 중심선 리샘플 간격 5m
    const wp=[];
    {
      const NP=p.length;
      const nodeAt=i=>NS[p[i]];
      const segAng=i=>{const a=nodeAt(i),b=nodeAt(i+1);return Math.atan2(b.y-a.y,b.x-a.x)};
      const segLen=i=>{const a=nodeAt(i),b=nodeAt(i+1);return Math.hypot(b.x-a.x,b.y-a.y)};
      // 1) 구간별 차로 오프셋(간선 속성)
      const offs=[];
      for(let i=0;i<NP-1;i++){
        const sg=edgeOf(p[i],p[i+1]);
        offs.push(sg ? laneOff(sg.l||2, sg.o) : LW*.5);
      }
      /* 2) 내부 노드마다 코너 원을 미리 구한다.
         ★호는 '중심선 코너원(반경 Rc) + 차로 반경(Rl)' 으로 만든다. 중심선에
         호를 그린 뒤 오프셋을 다시 더하는 방식은 좌회전에서 부호가 뒤집혀
         반대 차도로 들어갔고(실측: 호 중앙 y=+1.66m → -1.21m), 두 차로선에
         직접 접하는 원을 쓰는 방식은 좌/우 구분이 없어 좌회전이 안쪽으로
         파고들었다(실측 minLat: 좌90 -0.13m, 좌120 -1.37m, 좌150 -2.82m).
         동심원 방식은 두 방식 모두를 고친다(검증: verify_corner_geometry.js). */
      const RMIN=8*S;                                   // 중심선 기준 코너 반경 8m
      const corner=[];
      for(let i=0;i<NP;i++) corner.push(null);
      for(let i=1;i<NP-1;i++){
        const a1=segAng(i-1), a2=segAng(i);
        let d=((a2-a1+Math.PI*3)%(Math.PI*2))-Math.PI;   // 좌회전<0, 우회전>0
        if(Math.abs(d)<0.12) continue;                   // 거의 직진 = 호 불필요
        const half=d/2, t=Math.abs(Math.tan(half));
        const o1=offs[i-1], o2=offs[i], o=(o1+o2)/2;
        const V=nodeAt(i);
        /* ★코너는 '중심선 원 하나 + 차로 반경'으로 잡는다(최종형, 실측 도출).
           중심선에 반경 Rc 로 접하는 원을 그리고, 차로 주행선은 그 원과 동심이되
           반경만 바꾼다:
              우회전(Δ>0) : 차로가 회전 '안쪽'  → Rl = Rc - off
              좌회전(Δ<0) : 차로가 회전 '바깥쪽' → Rl = Rc + off
           두 차로선에 직접 접하는 원을 쓰던 이전 식은 이 방향 구분이 없어서,
           좌회전에서 주행선이 안쪽으로 파고들었다(실측 minLat: 좌90 -0.13m,
           좌120 -1.37m, 좌150 -2.82m — 각도가 급할수록 악화).
           중심 O 는 이등분선 위 |OV| = Rc/sin(내각/2) 지점(내각 = π-|Δ|). */
        const interior=Math.PI-Math.abs(d);
        const sh=Math.sin(interior/2); const shs=Math.abs(sh)<0.05?0.05:sh;
        /* ★접선길이 상한 = min(다리 45%, 교차로 면제반경).
           중앙선 하드 구속은 nearJunction(반경 roadW*1.5) 안을 면제하므로
           (game.js:1771), 호가 그 밖으로 나가면 다시 구속 대상이 된다.
           급한 각(150도)에서 Rc=6m 면 접선길이가 22.39m 나 돼 면제반경 9.75m 를
           한참 넘겼다 → 좌150 에서 minLat=-3.15m. 반경을 줄여 호를 교차로 안에
           가둔다(급한 각일수록 작게 도는 게 실제 주행과도 맞다). */
        const JR=(LW*2)*1.5;                            // nearJunction 면제 반경
        const Tcap=Math.min(segLen(i-1)*0.45, segLen(i)*0.45, JR*0.9);
        let Rc=Math.max(RMIN, LW/(t<0.05?0.05:t));
        if(Rc*t>Tcap) Rc=Tcap/(t<0.05?0.05:t);
        const sgnD=d>=0?1:-1;
        /* ★우회전은 차로 반경이 Rc-off 라 Rc 가 작아지면 0 으로 붕괴한다.
           바닥(LW*0.3)에 걸리면 호 끝점이 다리와 어긋나 이음매에서 튄다
           (실측 우150: Rl 이 0.97m 바닥에 걸려 표본당 99.4도). 바닥에 걸리지
           않도록 Rc 쪽을 먼저 키운다 — 차로 반경이 최소 LW*0.5 는 되게. */
        const RLMIN=LW*0.5;
        if(sgnD>0 && Rc-Math.abs(o)<RLMIN) Rc=RLMIN+Math.abs(o);
        const Rl=Rc - sgnD*Math.abs(o);                     // 차로 반경
        const bis=a1+half;                                   // 이등분 방향
        const nx=-Math.sin(bis)*sgnD, ny=Math.cos(bis)*sgnD; // 회전 안쪽 법선
        const Cox=V.x+nx*(Rc/shs), Coy=V.y+ny*(Rc/shs);
        // 차로 호의 시작/끝 각도 = 중심선 접점 각도와 동일(동심원)
        const Tc=Rc*t;                                       // 중심선 접점까지 거리
        const P0x=V.x-Math.cos(a1)*Tc, P0y=V.y-Math.sin(a1)*Tc;
        const P2x=V.x+Math.cos(a2)*Tc, P2y=V.y+Math.sin(a2)*Tc;
        const A0=Math.atan2(P0y-Coy,P0x-Cox), A2=Math.atan2(P2y-Coy,P2x-Cox);
        // 다리에서 잘라낼 길이 = 중심선 접점까지 거리(차로 호도 같은 지점에서 이어진다)
        const geom={Cox,Coy,R:Rl,A0,A2,T0:Tc,T2:Tc};
        corner[i]={a1,a2,d,half,T:Math.max(0,geom.T0),T2:Math.max(0,geom.T2),g:geom};
      }
      /* ★'뒤로 가는' 점은 버린다.
         코너가 안 생기는 완만한 각(Δ<0.12rad)에서는 두 다리가 각자 꼭짓점 점을
         내는데, 오프셋 방향이 미세하게 달라 두 번째 점이 진행방향 반대로
         0.1~0.2m 물러난다. 거리로만 걸러내면(0.05m) 통과해 버리고, 헤딩이
         한 표본에서 180도 뒤집힌다(실측 5도 코너: 표본당 177.5도 → 곡률 폭발).
         직전 진행방향과 내적이 음수면 그 점은 경로가 아니라 잡음이다. */
      const push=(x,y)=>{
        const q=wp[wp.length-1];
        if(!q){ wp.push({x,y}); return; }
        const dx=x-q.x, dy=y-q.y;
        if(Math.hypot(dx,dy) <= 0.05*S) return;          // 같은 자리
        if(wp.length>=2){
          const r=wp[wp.length-2];
          const px=q.x-r.x, py=q.y-r.y;
          if(px*dx+py*dy < 0) return;                    // 역주행 점
        }
        wp.push({x,y});
      };
      // 3) 구간을 리샘플해 오프셋하되, 코너의 접선구간(T) 안쪽 점은 호가 대신한다.
      for(let i=0;i<NP-1;i++){
        const A=nodeAt(i), B=nodeAt(i+1), a=segAng(i), L=segLen(i), off=offs[i];
        const t0 = corner[i]   ? corner[i].T2  : 0;      // 시작쪽(앞 코너의 진출접점)에서 자를 길이
        const t1 = corner[i+1] ? corner[i+1].T : 0;      // 끝쪽(다음 코너의 진입접점)에서 자를 길이
        const s0=t0, s1=L-t1;
        if(s1>s0){
          const n=Math.max(1,Math.round((s1-s0)/RS));
          for(let k=0;k<=n;k++){
            const s=s0+(s1-s0)*k/n, u=s/L;
            push(A.x+(B.x-A.x)*u - Math.sin(a)*off, A.y+(B.y-A.y)*u + Math.cos(a)*off);
          }
        }
        // 4) 이 구간의 끝이 코너면 이등분선 호를 붙인다.
        const c=corner[i+1];
        if(c){
          /* ★코너는 위에서 미리 구한 원(중심 g.Cox,g.Coy · 반경 g.R)의 접점
             F0→F2 구간 호를 그대로 4등분해 낸다. 접점이 다리 리샘플의 끝점과
             같으므로 이음매에서 끊김이 없다. */
          const g=c.g;
          let dA=((g.A2-g.A0+Math.PI*3)%(Math.PI*2))-Math.PI;
          const A0=g.A0;
          /* ★호 분할 수는 각도에 비례시킨다. 4등분 고정이면 급한 각에서 표본당
             회전이 커져(실측 우150: 108.8도/표본) 곡률 스캔이 다시 폭발한다.
             20도/표본 이하가 되게 나눈다(최소 4, 최대 10). */
          const N=Math.max(4, Math.min(10, Math.ceil(Math.abs(dA)/(20*Math.PI/180))));
          for(let k=0;k<=N;k++){
            const ang=A0+dA*(k/N);
            push(g.Cox+Math.cos(ang)*g.R, g.Coy+Math.sin(ang)*g.R);
          }
        }
      }
      if(!wp.length) push(nodeAt(0).x, nodeAt(0).y);
    }

  return wp;}

// ===== OLD 구현(비교용) =====
function buildOLD(p,NS){
  const wp=[];
  for(let i=0;i<p.length;i++){const n=NS[p[i]];
    if(i<p.length-1){const m=NS[p[i+1]],a=Math.atan2(m.y-n.y,m.x-n.x);const off=LW*.5;
      wp.push({x:n.x-Math.sin(a)*off,y:n.y+Math.cos(a)*off});}
    else wp.push({x:n.x,y:n.y});}
  const out=[wp[0]];
  for(let i=1;i<wp.length;i++){const a=out[out.length-1],b=wp[i];
    const L=Math.hypot(b.x-a.x,b.y-a.y),n=Math.floor(L/(25*S));
    for(let k=1;k<=n;k++){const u=k/(n+1);out.push({x:a.x+(b.x-a.x)*u,y:a.y+(b.y-a.y)*u});}
    out.push(b);}
  return out;
}
// lat = 진행방향 오른쪽이 +. 각 점을 '자기 다리' 중 가장 유리한 쪽으로 판정.
function lat(q,A,ang){return (-(q.x-A.x)*Math.sin(ang)+(q.y-A.y)*Math.cos(ang))/S;}
// ★게임의 하드 구속과 같은 방식으로 잰다: nearestSeg 는 t 를 [0,1] 로 클램프해
// '선분'까지의 거리를 쓴다(game.js:568). 따라서 꼭짓점 부근의 점은 두 선분 중
// 실제로 가장 가까운 쪽 기준으로 판정된다. 무한직선으로 재면 코너 인수인계
// 지점이 허위로 음수가 나온다(실측: 좌90 점9 가 -0.13m 로 잘못 잡혔다).
function nearestLeg(q,nd){
  let bd=Infinity,bi=-1;
  for(let k=0;k<nd.length-1;k++){
    const A=nd[k],B=nd[k+1];
    const vx=B.x-A.x,vy=B.y-A.y,L=vx*vx+vy*vy;
    let t=L?((q.x-A.x)*vx+(q.y-A.y)*vy)/L:0;t=Math.max(0,Math.min(1,t));
    const d=(A.x+vx*t-q.x)**2+(A.y+vy*t-q.y)**2;
    if(d<bd){bd=d;bi=k;}
  }
  return bi;
}
// ★게임의 하드 구속은 nearJunction() 으로 교차로 반경(roadW*1.5) 안을 아예
// 면제한다(game.js:1771). 코너 호는 정의상 그 안에 있으므로, 그 구역을 뺀
// '실제로 구속이 걸리는 점들'만 대상으로 최소 lat 을 잰다.
const ROADW=LW*2;                     // 왕복2차로 전체폭
function inJunction(q,nd){
  const R=ROADW*1.5;
  for(let k=1;k<nd.length-1;k++){
    if(Math.hypot(q.x-nd[k].x,q.y-nd[k].y)<=R) return true;
  }
  return false;
}
function minLat(wps,nd){
  let worst=Infinity,wi=-1;
  for(let i=0;i<wps.length;i++){
    if(inJunction(wps[i],nd)) continue;       // 구속 면제 구역
    const k=nearestLeg(wps[i],nd);
    const A=nd[k],B=nd[k+1];
    const v=lat(wps[i],A,Math.atan2(B.y-A.y,B.x-A.x));
    if(v<worst){worst=v;wi=i;}
  }
  return {v:worst,i:wi};
}
function spacing(w){let m=0;for(let i=1;i<w.length;i++)m=Math.max(m,Math.hypot(w[i].x-w[i-1].x,w[i].y-w[i-1].y)/S);return m;}
function maxTurn(w){let m=0;for(let i=2;i<w.length;i++){
  const a1=Math.atan2(w[i-1].y-w[i-2].y,w[i-1].x-w[i-2].x);
  const a2=Math.atan2(w[i].y-w[i-1].y,w[i].x-w[i-1].x);
  m=Math.max(m,Math.abs(((a2-a1+Math.PI*3)%(Math.PI*2))-Math.PI));}
  return m*180/Math.PI;}

const RS_M=5;
let fail=0;
function run(label, C){
  const nd=[{x:0,y:0},{x:40*S,y:0},C];
  const NS=nd, p=[0,1,2];
  const o=buildOLD(p,NS), n=buildNEW(p,NS);
  const lo=minLat(o,nd), ln=minLat(n,nd);
  console.log(`${label}`);
  console.log(`  OLD: pts=${o.length} minLat=${lo.v.toFixed(2)}m maxSpacing=${spacing(o).toFixed(2)}m maxTurn/sample=${maxTurn(o).toFixed(1)}deg ${lo.v<0?'CROSSES':'ok'}`);
  console.log(`  NEW: pts=${n.length} minLat=${ln.v.toFixed(2)}m maxSpacing=${spacing(n).toFixed(2)}m maxTurn/sample=${maxTurn(n).toFixed(1)}deg ${ln.v<0?'CROSSES':'ok'}`);
  if(ln.v<0){console.log('  !! ASSERT FAIL: NEW crosses centreline at idx',ln.i, n[ln.i].x/S, n[ln.i].y/S);fail++;}
  if(spacing(n)>1.2*RS_M){console.log(`  !! ASSERT FAIL: NEW spacing ${spacing(n).toFixed(2)}m > 1.2*${RS_M}m`);fail++;}
  return {o,n};
}
console.log('lane offset (2-lane two-way) =', (LW*.5/S).toFixed(2),'m\n');
run('90deg RIGHT turn', {x:40*S,y:40*S});
run('90deg LEFT  turn', {x:40*S,y:-40*S});

// 직선 회귀
{
  const nd=[{x:0,y:0},{x:100*S,y:0},{x:200*S,y:0}];
  const o=buildOLD([0,1,2],nd), n=buildNEW([0,1,2],nd);
  const dev=w=>{let m=0;for(const q of w)m=Math.max(m,Math.abs(q.y/S-LW*.5/S));return m;};
  console.log('\nSTRAIGHT (회귀 검사)');
  console.log(`  OLD: pts=${o.length} maxDevFromLaneCentre=${dev(o).toFixed(4)}m maxSpacing=${spacing(o).toFixed(2)}m`);
  console.log(`  NEW: pts=${n.length} maxDevFromLaneCentre=${dev(n).toFixed(4)}m maxSpacing=${spacing(n).toFixed(2)}m`);
  if(dev(n)>1e-6){console.log('  !! ASSERT FAIL: straight regressed');fail++;}
}
// 다양한 각도 스윕
console.log('\n각도 스윕(좌/우 30~150도) — 중앙선 침범·간격 검사');
for(const deg of [30,45,60,90,120,150]){
  for(const sgn of [1,-1]){
    const th=sgn*deg*Math.PI/180;
    const nd=[{x:0,y:0},{x:40*S,y:0},{x:40*S+Math.cos(th)*40*S, y:Math.sin(th)*40*S}];
    const n=buildNEW([0,1,2],nd);
    const ln=minLat(n,nd), sp=spacing(n), mt=maxTurn(n);
    const bad=(ln.v<0)||(sp>1.2*RS_M);
    if(bad)fail++;
    console.log(`  ${sgn>0?'R':'L'}${deg}: minLat=${ln.v.toFixed(2)}m spacing=${sp.toFixed(2)}m turn/sample=${mt.toFixed(1)}deg ${bad?'FAIL':'ok'}`);
  }
}
console.log(fail? `\n${fail} ASSERTION(S) FAILED` : '\nALL ASSERTIONS PASSED');

// ===== 곡률 스캔 영향(game.js:1221 과 같은 방식) =====
function kappaMax(w){
  // 5m 스텝으로 헤딩 변화 / 거리 -> rad/m, vmaxCurve 계산
  let mk=0;
  for(let i=2;i<w.length;i++){
    const a1=Math.atan2(w[i-1].y-w[i-2].y,w[i-1].x-w[i-2].x);
    const a2=Math.atan2(w[i].y-w[i-1].y,w[i].x-w[i-1].x);
    const dth=Math.abs(((a2-a1+Math.PI*3)%(Math.PI*2))-Math.PI);
    const ds=Math.hypot(w[i].x-w[i-1].x,w[i].y-w[i-1].y)/S;
    if(ds>0.1) mk=Math.max(mk, dth/ds);
  }
  return mk;
}
const vmax=k=>k>1e-4?Math.max(3.5,Math.min(14,Math.sqrt(2.4/k))):14;
console.log('\n===== 코너 통과 속도(곡률 스캔) =====');
for(const [lbl,C] of [['R90',{x:40*S,y:40*S}],['L90',{x:40*S,y:-40*S}]]){
  const nd=[{x:0,y:0},{x:40*S,y:0},C];
  const o=buildOLD([0,1,2],nd), n=buildNEW([0,1,2],nd);
  const ko=kappaMax(o), kn=kappaMax(n);
  console.log(`  ${lbl} OLD kappa=${ko.toFixed(3)}/m vmaxCurve=${vmax(ko).toFixed(2)}m/s (${(vmax(ko)*3.6).toFixed(0)}km/h)`);
  console.log(`  ${lbl} NEW kappa=${kn.toFixed(3)}/m vmaxCurve=${vmax(kn).toFixed(2)}m/s (${(vmax(kn)*3.6).toFixed(0)}km/h)`);
}
// ===== 연속 코너 / 짧은 다리 =====
console.log('\n===== 연속 코너·짧은 다리 =====');
{
  // 15m 다리로 좌-우 연속
  const nd=[{x:0,y:0},{x:30*S,y:0},{x:30*S,y:-15*S},{x:60*S,y:-15*S},{x:60*S,y:20*S}];
  const n=buildNEW([0,1,2,3,4],nd);
  console.log(`  4-corner short-leg: pts=${n.length} minLat=${minLat(n,nd).v.toFixed(2)}m spacing=${spacing(n).toFixed(2)}m turn/sample=${maxTurn(n).toFixed(1)}deg`);
}
{
  // 거의 직선(5도) — 호가 안 생겨야 정상
  const th=5*Math.PI/180;
  const nd=[{x:0,y:0},{x:50*S,y:0},{x:50*S+Math.cos(th)*50*S,y:Math.sin(th)*50*S}];
  const n=buildNEW([0,1,2],nd);
  console.log(`  near-straight 5deg: pts=${n.length} minLat=${minLat(n,nd).v.toFixed(2)}m spacing=${spacing(n).toFixed(2)}m turn/sample=${maxTurn(n).toFixed(1)}deg`);
}

console.log('\n--- 5deg dump ---');
{const th=5*Math.PI/180;
 const nd=[{x:0,y:0},{x:50*S,y:0},{x:50*S+Math.cos(th)*50*S,y:Math.sin(th)*50*S}];
 const n=buildNEW([0,1,2],nd);
 for(let i=0;i<n.length;i++)console.log(i,(n[i].x/S).toFixed(2),(n[i].y/S).toFixed(2));}

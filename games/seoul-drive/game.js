/* ====== 강남 드라이브 — 실측 스케일 물리/렌더 ======
   ★스케일 규약: S = px per metre. 모든 치수는 '미터'로 쓰고 S를 곱해 그린다.
     (이전 버그: 차 5.8m×12.3m > 차로폭 3.5m → 차가 도로를 벗어남) */
const S = 6.0;                 // px/m
const LANE_M = 3.25;           // 차로폭(m) — 한국 도시부 기준
const LW = LANE_M * S;         // 19.5px
const SIDEWALK_M = 3.0;        // 인도폭(m)

const cv=document.getElementById('cv'),g=cv.getContext('2d');
let W,H,DPR=Math.min(devicePixelRatio||1,2);
function fit(){W=innerWidth;H=innerHeight;cv.width=W*DPR;cv.height=H*DPR;g.setTransform(DPR,0,0,DPR,0,0)}
addEventListener('resize',fit);fit();
/* ★u_4923 '지도가 너무 어둡다'.
   원인: CSS 변수를 밝게 덮어써도 소용없었다(실측: 도로 픽셀 변화 0).
   아티팩트 뷰어가 iframe 위에 어두운 레이어를 덧씌우기 때문에 페이지 CSS로는 못 이긴다.
   → 게임이 칠하는 색 자체를 밝은 값으로 고정한다. 합성 후에도 남는다.
   사람 눈에도, CNN 입력 픽셀에도 같이 효과가 있다. */
/* ★u_4923/u_4924 '지도가 어둡다 / 잘 안 보인다'.
   아티팩트 뷰어가 캔버스를 약 27% 밝기로 눌러버린다(실측: 도로 #b9bfc8 → [51,52,54]).
   CSS 필터로 되돌리려다 화면이 전부 회색으로 뭉개져 실패했었다(전역 곱이라 명암이 같이 죽음).
   → 색을 '밝게'가 아니라 '대비를 키운 채' 다시 고른다.
     도로는 거의 흰색까지 올리고, 차선·글자는 완전한 흰/검으로 양 끝에 붙인다.
     눌린 뒤에도 도로-차선 차이가 남도록 하는 게 핵심(CNN 입력에도 동일하게 유효). */
/* ★대비 강화(u_4945). 차선·오브젝트가 흰 도로에 묻혀 안 보였다.
   도로는 약간 회색으로 내리고, 차선은 완전한 검정, 보도는 확실히 구분되는 톤으로. */
/* ★실제 도로교통 기준 색(2026-09-14 u_4955).
   기존에는 도로를 밝게(#e4e8ee) 하고 차선을 검정으로 칠했다 — 실제와 정반대다.
   한국 도로표지 기준으로 맞춘다:
     차도   = 아스팔트 진회색   (배경·인도와 명확히 구분)
     차선   = 흰색 점선         (같은 방향 차로 구분)
     중앙선 = 노란색 실선       (반대방향 분리)
     인도   = 밝은 회색
   차도만 어둡게 하면 차선(흰색)이 그 위에서 가장 밝아 대비가 최대가 된다.
   사람 눈에도 CNN 입력에도 이 배치가 맞다. */
/* ★실제 도로교통 기준 색(2026-09-14 u_4955).
   차도=아스팔트 진회색 / 차선=흰색 / 중앙선=노란색 / 인도=밝은 회색.
   차도만 어둡게 하면 흰 차선이 그 위에서 가장 밝아 대비가 최대가 된다.
   대비 실측(도로 기준): 차선 175, 중앙선 134, 인도 123, 배경 166.

   ※'화면이 파랗다'고 판단했던 건 오진이었다(u_4957 오너 지적).
     뷰어 오버레이가 아니라 페이지 텍스트가 전체선택(Cmd+A)된 상태의
     선택 하이라이트였다. 캔버스 빈 곳을 클릭해 선택을 풀면
     색편향(B-R)이 +47 → +2 로 사실상 중립이 된다.
     ⇒ 캡처 전에는 항상 선택을 해제할 것. 색 보정은 필요 없다. */
const PAL={'--bg':'#f5f6f8','--bld':'#d6dbe3','--bldEdge':'#8b95a3','--bldInk':'#1a1f28',
           '--road':'#4a4f57','--walk':'#c3cad3','--line':'#ffffff','--center':'#ffd400',
           '--roadInk':'#ffffff','--halo':'rgba(0,0,0,.55)','--lamp':'#2a2f36',
           '--green':'#00b050','--ink':'#1a1f28'};
const C=v=>PAL[v] || getComputedStyle(document.documentElement).getPropertyValue(v).trim();

/* ---------- 지도 청크 로딩 (서울·경기 전역, u_4877/4878) ----------
   전체 9.8MB를 한 번에 올리면 브라우저가 죽는다 → 1km 격자로 쪼개
   차 주변 3x3만 메모리에 올린다. 중앙값 15KB/청크. */
const CHUNK=1000;                                   // m
var curChunk='';
var navErr='';
var crashLit=0;
var lastDraw=0; var DRAW_MS=1000/30;   /* 렌더 30fps 제한(u_4941).
  ※60fps 로 올려도 비전 새화면은 92→94fps 로 거의 안 늘고(캡처 API 고정비용이 상한),
    WindowServer 는 10.8%→21.5% 로 2배가 된다. 30fps 가 최적점.(u_4942 실측) */
var crashHold=0, crashHoldT=0, bldStuck=0, blockT=0;   // 사고 정지 상태(화면 빨강 고정)   // ★hardReset()가 먼저 호출되므로 var로 호이스팅(TDZ 방지)
const CH=(typeof CHUNKS!=='undefined')?CHUNKS:null;
function chunkKey(x,y){return Math.floor(x/CHUNK)+','+Math.floor(y/CHUNK)}
let loadedKeys=new Set();
function collectRoads(cx,cy){
  // cx,cy = 미터 기준 차 위치
  if(!CH) return ROADS;
  const out=[];const keys=[];
  const i0=Math.floor(cx/CHUNK),j0=Math.floor(cy/CHUNK);
  for(let i=i0-1;i<=i0+1;i++)for(let j=j0-1;j<=j0+1;j++){
    const k=i+','+j;keys.push(k);
    const c=CH[k];if(c)out.push(...c.r);
  }
  loadedKeys=new Set(keys);
  return out;
}
function collectBlds(cx,cy){
  if(!CH) return BLDS;
  const out=[];
  const i0=Math.floor(cx/CHUNK),j0=Math.floor(cy/CHUNK);
  for(let i=i0-1;i<=i0+1;i++)for(let j=j0-1;j<=j0+1;j++){
    const c=CH[i+','+j];if(c)out.push(...c.b);
  }
  return out;
}
let ROADS_ACTIVE=collectRoads(0,0);
let BLDS_ACTIVE =collectBlds(0,0);
let BLDS_ALL=[];   /* 전 청크 건물(전역 그래프 stitch 검사용) */

/* ---------- 그래프 (청크가 바뀌면 다시 짓는다) ---------- */
const nodes=[],segs=[];let nmap=new Map();
const key=p=>p[0].toFixed(0)+'_'+p[1].toFixed(0);
function nid(p){const k=key(p);if(nmap.has(k))return nmap.get(k);
  const i=nodes.length;nodes.push({x:p[0]*S,y:p[1]*S,e:[]});nmap.set(k,i);return i}
function buildGraph(roads){
  nodes.length=0;segs.length=0;nmap=new Map();
  for(const w of roads)for(let i=0;i<w.p.length-1;i++){
    const a=nid(w.p[i]),b=nid(w.p[i+1]);if(a===b)continue;
    const si=segs.length;
    const len=Math.hypot(nodes[b].x-nodes[a].x,nodes[b].y-nodes[a].y);
    const ang=Math.atan2(nodes[b].y-nodes[a].y,nodes[b].x-nodes[a].x);
    segs.push({a,b,l:w.l,o:w.o,n:w.n,len,ang,roadW:w.l*LW});
    nodes[a].e.push(si);nodes[b].e.push(si);
  }
}
buildGraph(ROADS_ACTIVE);
const other=(s,n)=>s.a===n?s.b:s.a;
function nearestSegRaw(x,y){
  let b=null,bd=1e18;
  for(const s of segs){
    const A=nodes[s.a],B=nodes[s.b];
    const vx=B.x-A.x,vy=B.y-A.y,L=vx*vx+vy*vy;
    let t=L?((x-A.x)*vx+(y-A.y)*vy)/L:0;t=Math.max(0,Math.min(1,t));
    const d=(A.x+vx*t-x)**2+(A.y+vy*t-y)**2;
    if(d<bd){bd=d;b=s}
  }
  return b;
}
let XR=nodes.map(n=>n.e.length>=3);
function recalcXR(){XR=nodes.map(n=>n.e.length>=3)}

/* 건물 폴리곤(px) */
let blds=[];
/* ★지하구조물은 충돌 대상이 아니다(u_5077 실사고).
   강남역지하쇼핑센터는 144x174m 로 강남대로 위를 덮고 있다. 지상 도로를 달리는 차가
   지하상가와 충돌할 수는 없다. 이것 때문에 강남역에서 출발하면 즉시 '건물 충돌'이 났다. */
const UNDERGROUND_RE=/지하상가|지하쇼핑|지하도|지하차도|지하주차/;
function isUnderground(b){ return UNDERGROUND_RE.test(b.n||''); }
function mkBlds(src){return src.filter(b=>!isUnderground(b)).map(b=>{
  const p=b.p.map(q=>[q[0]*S,q[1]*S]);
  let cx=0,cy=0;for(const q of p){cx+=q[0];cy+=q[1]}
  cx/=p.length;cy/=p.length;
  let minx=1e9,maxx=-1e9,miny=1e9,maxy=-1e9;
  for(const q of p){minx=Math.min(minx,q[0]);maxx=Math.max(maxx,q[0]);
    miny=Math.min(miny,q[1]);maxy=Math.max(maxy,q[1])}
  return{n:b.n,h:b.h||3,p,cx,cy,minx,maxx,miny,maxy,
    area:(maxx-minx)*(maxy-miny)};
})}
blds=mkBlds(BLDS_ACTIVE);

/* 건물 충돌 인덱스 — 격자 버킷(빠른 조회) */
const GRID=40*S;
let bgrid=new Map();
const gkey=(i,j)=>i+'|'+j;
function buildBldGrid(){
  bgrid=new Map();
  for(let bi=0;bi<blds.length;bi++){
    const b=blds[bi];
    for(let i=Math.floor(b.minx/GRID);i<=Math.floor(b.maxx/GRID);i++)
      for(let j=Math.floor(b.miny/GRID);j<=Math.floor(b.maxy/GRID);j++){
        const k=gkey(i,j);if(!bgrid.has(k))bgrid.set(k,[]);bgrid.get(k).push(bi);
      }
  }
}
buildBldGrid();
function pointInPoly(x,y,p){
  let c=false;
  for(let i=0,j=p.length-1;i<p.length;j=i++){
    const xi=p[i][0],yi=p[i][1],xj=p[j][0],yj=p[j][1];
    if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)c=!c;
  }
  return c;
}
/* 점이 건물 안인가 → 건물 인덱스 반환(없으면 -1) */
function bldAt(x,y){
  const arr=bgrid.get(gkey(Math.floor(x/GRID),Math.floor(y/GRID)));
  if(!arr)return -1;
  for(const bi of arr){
    const b=blds[bi];
    if(x<b.minx||x>b.maxx||y<b.miny||y>b.maxy)continue;
    if(pointInPoly(x,y,b.p))return bi;
  }
  return -1;
}
/* 차 앞범퍼/모서리 4점으로 벽 충돌 검사 */
function bldHit(c){
  const ca=Math.cos(c.ang),sa=Math.sin(c.ang);
  const hx=c.h*.5,wx=c.w*.5;
  const pts=[[hx,0],[hx,wx*.8],[hx,-wx*.8],[-hx,0]];
  for(const[f,l]of pts){
    const x=c.x+ca*f-sa*l, y=c.y+sa*f+ca*l;
    const bi=bldAt(x,y);
    if(bi>=0)return bi;
  }
  return -1;
}

/* 횡단보도 — ★실제 OSM crossing 노드(ar_4872). 합성 아님 */
let cross=[];
function buildCross(){cross=(typeof XWALK!=='undefined'?XWALK:[]).map(c=>{
  const x=c.x*S,y=c.y*S;
  const n=nearestSegRaw(x,y);
  return{x,y,ang:n?n.ang:0,w:n?n.roadW:3*LW};
})}
buildCross();
/* ★신호등 — 교차로 진입부 정지선마다 배치(u_4875).
   실제 도로처럼: 한 교차로의 신호는 하나의 주기를 공유하고,
   교차하는 방향끼리는 서로 반대 위상(직교 현시)이다.
   ※단, 차량 AI에는 이 정보를 주지 않는다 — 화면의 '색'으로만 존재한다. */
let signals=[];
function buildSignals(){
 signals=[];
  // OSM 신호등이 있는 교차로만 신호교차로로 취급(실제 상황 반영)
  const sigPts=(typeof SIGNALS!=='undefined'?SIGNALS:[]).map(c=>({x:c.x*S,y:c.y*S}));
  const isSignalised=n=>sigPts.some(p=>Math.hypot(p.x-n.x,p.y-n.y)<38*S);
  for(let ni=0;ni<nodes.length;ni++){
    if(!XR[ni])continue;
    const N=nodes[ni];
    if(!isSignalised(N))continue;
    const t0=Math.random()*20, period=16+Math.random()*6;
    for(const si of N.e){
      const sg=segs[si];
      const toward=(sg.a===ni)?sg.ang+Math.PI:sg.ang;   // 교차로를 향하는 진행방향
      const d=sg.roadW*.5+SIDEWALK_M*S+1.6*S;           // 정지선 위치
      // 접근 차로(우측) 쪽으로 치우쳐 배치
      const lat=sg.roadW*.28;
      signals.push({
        x:N.x+Math.cos(toward+Math.PI)*d-Math.sin(toward)*lat,
        y:N.y+Math.sin(toward+Math.PI)*d+Math.cos(toward)*lat,
        ang:toward, node:ni, t0, period,
        // 직교 현시: 도로 방향(가로/세로)에 따라 위상 반전
        phase: (Math.abs(Math.cos(sg.ang))>0.5)?0:1
      });
    }
  }
}
buildSignals();
function sigRed(sg,now){
  const ph=((now/1000)+sg.t0)%sg.period;
  const green = sg.phase===0 ? (ph<sg.period*0.45)
                             : (ph>=sg.period*0.5 && ph<sg.period*0.95);
  return !green;
}
/* ★표지판 — 도로 내용에 맞게 자동 생성(u_4875)
   실제 도로 속성(차로수·일방통행·교차로)에서 유도한다. 임의 배치 아님.
   ※차량 AI는 이걸 표지판으로 인식하지 않는다 — 화면의 색 덩어리일 뿐. */
let signs=[];
function buildSigns(){
 signs=[];
  for(const s of segs){
    if(s.len<45*S)continue;
    const A=nodes[s.a],B=nodes[s.b];
    const put=(t,frac,txt,col)=>{
      const h=s.roadW*.5+SIDEWALK_M*S*.7;
      signs.push({x:A.x+(B.x-A.x)*frac-Math.sin(s.ang)*h,
                  y:A.y+(B.y-A.y)*frac+Math.cos(s.ang)*h,
                  t,txt,col});
    };
    // 일방통행 → 진입금지/일방통행 표지
    if(s.o) put('one',0.5,'⇧','#2f6fd0');
    // 넓은 도로(4차로+) → 제한속도 60, 좁으면 30
    if(s.l>=3||Math.random()<.35) put('spd',0.28, s.l>=4?'60':'30', '#c0392b');
    // 교차로 직전 → 신호/양보
    if(XR[s.b]) put('yld',0.86,'▽','#c0392b');
  }
}
buildSigns();

/* 가로등 */
let lamps=[];
function buildLamps(){
 lamps=[];
 for(const s of segs){
  const h=s.roadW*.5+SIDEWALK_M*S*.55;
  for(let d=8*S;d<s.len-8*S;d+=25*S)
    for(const sg of[-1,1]){
      const t=d/s.len,A=nodes[s.a],B=nodes[s.b];
      lamps.push({x:A.x+(B.x-A.x)*t-Math.sin(s.ang)*h*sg,
                  y:A.y+(B.y-A.y)*t+Math.cos(s.ang)*h*sg});
    }
 }
}
buildLamps();

/* ---------- 차량 제원(실제 m) ---------- */
const TY={
  /* ★차량색 진하게(2026-09-14 u_4945 '하나도 안 보인다').
     도로를 거의 흰색으로 만든 뒤로 #eef2f7(거의 흰색) 같은 차량이 배경에 묻혔다.
     흰 바닥에서 확실히 구분되는 진한 원색만 쓴다 — 사람 눈과 CNN 입력 양쪽에 유효. */
  /* ★차량색(u_4955 후속): 도로를 실제 아스팔트(#4a4f57)로 바꿨으므로
     어두운 차량은 바닥에 묻힌다. 밝고 채도 높은 색으로 간다.
     실제 도로에서도 차는 배경보다 밝거나 채도가 높아 눈에 띈다. */
  car  :{wm:1.8,hm:4.6,vmax:13,n:'승용차',cs:['#ffffff','#e8e8e8','#d81b1b','#1565ff','#00a862','#ffb300','#9c27b0']},
  truck:{wm:2.5,hm:8.5,vmax:9 ,n:'트럭'  ,cs:['#f0f0f0','#7fb3d5','#e67e22']},
  moto :{wm:0.8,hm:2.1,vmax:15,n:'오토바이',cs:['#ff4081','#ffea00']},
  bike :{wm:0.6,hm:1.8,vmax:5 ,n:'자전거',cs:['#26d07c','#40c4ff']}
};
const rnd=(a,b)=>a+Math.random()*(b-a),pick=a=>a[(Math.random()*a.length)|0];

/* 차로 중심 오프셋: dir=+1 → 진행방향 기준 오른쪽 차로 */
function laneOffset(s,dir,lane){
  /* lane 은 실수도 받는다(차선변경 보간용, u_4972) — 정수로 깎지 않는다 */
  /* ★일방통행은 '전 차로 사용'이지만 중심선을 걸치면 안 된다(a_5092).
     (lane+.5)*LW - roadW/2 는 차로를 중심선 양쪽으로 펼치므로, 4차로 일방통행이면
     lane0/1 이 -4.88m/-1.62m = 진행방향 기준 **왼쪽**(맞은편 차로)에 놓인다.
     올림픽대로·강변북로·경부고속도로처럼 방향별로 분리된 차도(divided carriageway)는
     그 자체가 한쪽 차도이므로, 중심선 왼쪽에 그리면 역주행으로 보인다.
     실측: 일방통행 296253 케이스 중 165126(55.7%)이 왼쪽에 놓였다.
     → 진행방향 오른쪽으로 전 차로를 몰아서 배치한다. */
  /* ★u_5180 오너 지적 "지금도 3차로 차선 중앙으로 달림".
     실측으로 확인: 4차로 도로(폭 13m)에서 laneF=0(1차로) 인데 차가
     도로 좌측 기준 8.13m = 3차로 한복판에 있었다.
     원인은 이 식이 '중심선 기준' 오프셋을 돌려준다는 것. 주석의 의도는
     '중심선 오른쪽으로 전 차로를 몰아서 배치' 인데, 그러려면 원점이
     도로 왼쪽 가장자리여야 한다. (lane+0.5)*LW 만 쓰면 중심선에서
     그만큼 더 오른쪽으로 밀린다.
     실측 환산 — 현재식이 가리키는 실제 차로:
       8차로→5차로, 5차로→4차로, 4차로→3차로, 1차로→도로 밖(3.25m).
     ⇒ 도로 왼쪽 가장자리(-roadW/2)를 원점으로 잡는다. */
  if(s.o){ return -(s.roadW*0.5) + (lane+0.5)*LW; }  // 일방통행: 좌측 가장자리부터 차로 배치
  const halfLanes=Math.max(1,Math.floor(s.l/2));
  const k=Math.max(0,Math.min(lane,halfLanes-1));
  return dir>0 ? (k+0.5)*LW : -((k+0.5)*LW);
}
const cars=[],peds=[];
function seed(){
  cars.length=0;peds.length=0;
  for(let i=0;i<segs.length;i++){
    const s=segs[i];
    if(s.len<12*S)continue;
    const n=s.l>=4?3:s.l>=3?2:1;
    for(let k=0;k<n;k++){
      const t=Math.random()<.14?'truck':Math.random()<.18?'moto':Math.random()<.12?'bike':'car';
      const T=TY[t];
      const dir=s.o?1:(Math.random()<.5?1:-1);
      const lane=(Math.random()*Math.max(1,s.o?s.l:Math.floor(s.l/2)))|0;
      cars.push({t,...T,c:pick(T.cs),w:T.wm*S,h:T.hm*S,
        si:i,dir,lane,tp:Math.random(),
        v:T.vmax*rnd(.55,.85),x:0,y:0,ang:0,alive:1});
    }
    if(Math.random()<.45){
      const sg=Math.random()<.5?-1:1;
      peds.push({si:i,tp:Math.random(),sg,v:rnd(1.1,1.6),dir:Math.random()<.5?1:-1,
        x:0,y:0,c:pick(['#d94a3d','#3b7dd8','#2fa360','#e8a317','#111827','#8b5cf6'])});
    }
  }
  cars.forEach(c=>placeCar(c));peds.forEach(p=>placePed(p));
}
function placeCar(c){
  const s=segs[c.si],A=nodes[s.a],B=nodes[s.b];
  /* ★차선변경 중에는 실수 차로(laneF)로 위치를 잡는다(u_4972).
     정수 lane 으로만 그리면 차가 옆 차선으로 순간이동해 보이고,
     학습 입력으로도 '끼어드는 과정'이 사라져 버린다. */
  const off=laneOffset(s,c.dir,(c.laneF!==undefined?c.laneF:c.lane));
  const a=s.ang+(c.dir<0?Math.PI:0);
  c.x=A.x+(B.x-A.x)*c.tp-Math.sin(s.ang)*off;
  c.y=A.y+(B.y-A.y)*c.tp+Math.cos(s.ang)*off;
  c.ang=a;
}
function placePed(p){
  const s=segs[p.si],A=nodes[s.a],B=nodes[s.b];
  const h=s.roadW*.5+SIDEWALK_M*S*.5;
  p.x=A.x+(B.x-A.x)*p.tp-Math.sin(s.ang)*h*p.sg;
  p.y=A.y+(B.y-A.y)*p.tp+Math.cos(s.ang)*h*p.sg;
}
seed();

/* ---------- 주차장 (시작 위치) ----------
   오너 지시: "시작할때 난 주차 영역에 있어야함" — 도로 위 스폰 = 즉시 사고. */
const PARK={bays:[],cx:0,cy:0,ang:0};
(function(){
  // 지도 중심에서 가장 가까운 '긴 도로' 옆 빈 땅에 주차장을 만든다
  let bs=null,bd=1e18;
  for(const s of segs){
    if(s.len<28*S)continue;
    const mx=(nodes[s.a].x+nodes[s.b].x)/2,my=(nodes[s.a].y+nodes[s.b].y)/2;
    const d=mx*mx+my*my;if(d<bd){bd=d;bs=s}
  }
  if(!bs)return;
  const A=nodes[bs.a],B=nodes[bs.b];
  const mx=(A.x+B.x)/2,my=(A.y+B.y)/2;
  // 도로 옆(인도 바깥)으로 물러난 지점, 건물이 없는 쪽 선택
  const off=bs.roadW*.5+SIDEWALK_M*S+7*S;
  let best=null;
  for(const sg of[1,-1]){
    const px=mx-Math.sin(bs.ang)*off*sg, py=my+Math.cos(bs.ang)*off*sg;
    if(bldAt(px,py)<0){best={px,py,sg};break}
  }
  if(!best)best={px:mx-Math.sin(bs.ang)*off,py:my+Math.cos(bs.ang)*off,sg:1};
  PARK.cx=best.px;PARK.cy=best.py;PARK.ang=bs.ang;
  const BW=2.5*S,BH=5.2*S;                 // 주차칸 2.5m x 5.2m
  for(let i=0;i<6;i++){
    const t=(i-2.5)*BW*1.06;
    PARK.bays.push({x:best.px+Math.cos(bs.ang)*t, y:best.py+Math.sin(bs.ang)*t,
                    w:BW,h:BH,ang:bs.ang+Math.PI/2});
  }
  PARK.exit={x:mx-Math.sin(bs.ang)*(bs.roadW*.25)*best.sg,
             y:my+Math.cos(bs.ang)*(bs.roadW*.25)*best.sg};
})();

/* ---------- 목적지 POI ---------- */
/* ★POI는 '건물 위치'이지 '도로 위 지점'이 아니다(u_4896 오너 지적).
   실측: 60곳 중 55곳이 도로에서 20m 이상 떨어져 있고 중앙값 539m.
   내비 목적지는 반드시 **도로 위 진입점(entrance)** 이어야 한다.
   이건 학습 문제가 아니라 목적지를 잡는 방식의 문제다. */
const POIS=(typeof POI!=='undefined'?POI:[]).map(p=>({n:p.n,k:p.k,x:p.x*S,y:p.y*S,ex:null,ey:null}));
function poiEntrance(p){
  if(p.ex!==null)return p;
  const n=nearestSeg(p.x,p.y);
  if(n){p.ex=n.px;p.ey=n.py;p.edist=n.d/S}
  else {p.ex=p.x;p.ey=p.y;p.edist=1e9}
  return p;
}
let poiIdx=0;
function hasChunk(xm,ym){
  if(!CH)return true;
  return !!CH[Math.floor(xm/CHUNK)+','+Math.floor(ym/CHUNK)];
}
function nextPOI(){
  if(!POIS.length)return null;
  /* ★목적지는 '지금 로딩된 도로망 안'에 있어야 한다(u_4895).
     이전엔 청크 존재만 봤는데, 청크가 있어도 활성 그래프(3x3)에 없으면
     경로가 지도 가장자리에서 끊긴다 — 실측: 한국분재박물관은 가장 가까운
     도로노드까지 2625m, 즉 도달 불가인데 목적지로 잡히고 있었다.
     → 실제 도로 노드에서 120m 이내인 POI만 후보로 삼는다. */
  const near=[];
  for(const p of POIS){
    const n=nearestSegRaw(p.x,p.y);
    if(!n)continue;
    const A=nodes[n.a],B=nodes[n.b];
    const vx=B.x-A.x,vy=B.y-A.y,L=vx*vx+vy*vy;
    let t=L?((p.x-A.x)*vx+(p.y-A.y)*vy)/L:0;t=Math.max(0,Math.min(1,t));
    const d=Math.hypot(A.x+vx*t-p.x,A.y+vy*t-p.y);
    if(d<120*S)near.push({p,d});
  }
  if(!near.length)return null;
  near.sort((a,b)=>Math.hypot(a.p.x-me.x,a.p.y-me.y)-Math.hypot(b.p.x-me.x,b.p.y-me.y));
  const raw=near[poiIdx++%near.length].p;
  const e=poiEntrance(raw);
  // 목적지 = 도로 위 진입점. 이름은 POI 이름을 그대로 쓴다.
  return {n:raw.n,k:raw.k,x:e.ex,y:e.ey,poiX:raw.x,poiY:raw.y};
}

/* ---------- 내 차 ---------- */
var mt;
function flash(t){const m=document.getElementById('msg');if(!m)return;m.textContent=t;
  m.classList.add('show');clearTimeout(mt);mt=setTimeout(()=>m.classList.remove('show'),1200)}
const auto={on:0,goal:null,wp:[],i:0,act:'대기'};
const me={x:0,y:0,ang:0,v:0,steer:0,wm:1.8,hm:4.6,w:1.8*S,h:4.6*S,
  dmg:0,crashes:0,cool:0,offroad:0};
/* ★출발지 = 강남역 (u_5073 오너 지시).
   이전엔 지도원점(0,0)에 가장 가까운 '긴 도로'를 골랐다. 그런데 20m 이상이라는
   조건만 두니 원점 근처를 지나는 경부고속도로가 뽑혔다 — 고속도로에서 출발하면
   좌/우회전을 볼 수 없고 진출로까지 묶인다.
   지도는 이미 강남역 중심이다(강남역지하쇼핑센터 = (11.4,-9.9) ≈ 원점).
   그래서 원점 근처를 쓰되, 고속도로/자동차전용도로를 빼고 '일반 시가지 도로'만
   후보로 삼는다. 판정축 = 이름(고속도로·고속화·나들목·분기점)과 차로수. */
const HWY_RE=/고속도로|고속화|나들목|분기점|램프|JC|IC/;
function isCityRoad(s){
  if(HWY_RE.test(s.n||''))return false;
  /* ★차로수로 거르지 않는다(u_5076). 강남대로가 8차로다 — 넓다고 고속도로가 아니다.
     이 조건 때문에 강남역 본선이 후보에서 빠졌다. 판정은 이름(고속도로/램프)만 쓴다. */
  return true;
}
/* ★start 는 '지금의 segs 기준'으로 매번 다시 구한다.
   이전엔 로드 직후 한 번만 계산해 인덱스를 들고 있었다. 그런데 청크가 바뀔 때마다
   buildGraph() 가 segs 를 통째로 다시 만든다(2120행) — 인덱스가 재배열되므로
   같은 번호가 전혀 다른 도로를 가리킨다. 그게 강남대로를 골랐는데도 경부고속도로에서
   출발하던 원인이다(u_5073/u_5074). 실측: 원점 최근접 = 강남대로 16.8m,
   경부고속도로는 상위 20위 안에도 없다. */
/* ★출발 기준점 = 강남역 실좌표 (u_5073/5074/5075 오너 지시, 3회 지적).
   '원점 최근접'은 기준이 아니다 — 원점이 강남역이라는 보장이 없고, 실제로
   출발 도로가 강남역과 무관하게 잡혔다. 강남역 좌표를 직접 찍는다.
   출처: 청크의 s(역) 항목, 그리고 검색인덱스 '강남역지하쇼핑센터'(11.4,-9.9). */
let GANGNAM=null;
function gangnamXY(){
  if(GANGNAM)return GANGNAM;
  /* ★'강남역' 접두 검색은 틀린다(u_5077 실사고).
     SEARCH 에서 '강남역'으로 시작하는 첫 항목 = 강남역리가스퀘어오피스텔(-286,-370.9),
     실제 역에서 460m 떨어진 오피스텔이고 바로 옆이 경부고속도로다.
     그래서 계속 경부고속도로에서 출발했다. 정확한 항목 하나를 지정한다.
     기준점 = 강남역지하쇼핑센터(11.4,-9.9) = 강남역 그 자체. */
  if(typeof SEARCH!=='undefined'){
    for(const r of SEARCH) if(r.n==='강남역지하쇼핑센터'){ GANGNAM={x:r.x,y:r.y}; return GANGNAM; }
    for(const r of SEARCH) if(r.n==='강남역'){ GANGNAM={x:r.x,y:r.y}; return GANGNAM; }
  }
  GANGNAM={x:11.4,y:-9.9};        // 실측 상수(위 항목이 없을 때만)
  return GANGNAM;
}
/* ★출발 배치 정책 = 이 함수 하나 (2026-09-15).
   왜 합쳤나: 같은 정책(강남역/지정 좌표 최근접 시가지 도로 → 2패스 → 건물 없는 t)이
   pickStart·hardReset·setStart 세 곳에 손으로 복제돼 있었다. 한 곳을 고쳐도 나머지
   두 곳은 옛 규칙 그대로 남는다 — teacher.js 가 스폰 로직 사본을 들고 game.js 를
   덮어써 버린 사고(u_5077)와 정확히 같은 구조다. 지금은 셋이 우연히 일치할 뿐이었다.
   ⇒ 앞으로 배치 규칙을 고칠 곳은 여기 한 군데다.

   인자: (x,y) = 기준 좌표(월드 단위, m 아님).
     opt.metric  'mid'  = 세그먼트 중점까지의 거리로 고른다(강남역 기준 배치)
                 'proj' = 세그먼트 위 수직투영 거리로 고른다(내 위치 스냅)
     opt.ts      건물 회피로 훑을 t 후보(없으면 metric 별 기본값)
     opt.place   true 면 me.x/me.y/me.ang 까지 직접 세팅한다
     opt.any     true 면 길이 20m 하한을 풀어 아무 구간이나 받는다(최후수단)
   반환: {seg, si, t, x, y, ang, d2, free} / 후보가 없으면 null.
   ★주의: 좌표 스트리밍(streamWorld)은 호출자 책임이다 — segs 에 올라와 있지 않은
     도로는 애초에 후보가 될 수 없다(u_5077: 먼저 옮기고 스트리밍해야 한다). */
function placeCarNear(x,y,opt){
  opt=opt||{};
  const metric = opt.metric || 'mid';
  if(!segs.length) return null;
  /* 2패스: 1차는 시가지 도로만, 그래도 없으면 2차에서 고속도로까지 받는다.
     (고속도로에서 출발하면 좌/우회전을 못 배운다 — isCityRoad 주석 참고) */
  let bs=null, bsi=-1, bd=1e18, bt=0;
  for(let pass=0;pass<2;pass++){
    for(let i=0;i<segs.length;i++){
      const s=segs[i];
      if(!opt.any && s.len<20*S) continue;
      if(pass===0 && !isCityRoad(s)) continue;
      const A=nodes[s.a], B=nodes[s.b];
      let d2, t=0;
      if(metric==='proj'){
        const vx=B.x-A.x, vy=B.y-A.y, L=vx*vx+vy*vy;
        t = L?((x-A.x)*vx+(y-A.y)*vy)/L:0; t=Math.max(0,Math.min(1,t));
        const px=A.x+vx*t-x, py=A.y+vy*t-y;
        d2 = px*px+py*py;
      }else{
        const mx=(A.x+B.x)/2-x, my=(A.y+B.y)/2-y;
        d2 = mx*mx+my*my;
      }
      if(d2<bd){ bd=d2; bs=s; bsi=i; bt=t; }
    }
    if(bs) break;
  }
  if(!bs) return null;
  const A=nodes[bs.a], B=nodes[bs.b];
  const off=laneOffset(bs,1,0);
  const at=t=>({x:A.x+(B.x-A.x)*t-Math.sin(bs.ang)*off,
                y:A.y+(B.y-A.y)*t+Math.cos(bs.ang)*off});
  /* ★건물 안에서 출발하면 뜨자마자 충돌이다(u_5077 실측: 강남역지하쇼핑센터 충돌).
     구간을 따라 여러 지점을 훑어 건물에 안 걸리는 곳을 고른다. */
  const ts = opt.ts || (metric==='proj'
             ? [bt,bt+0.1,bt-0.1,bt+0.2,bt-0.2,0.5,0.25,0.75]
             : [0.15,0.3,0.45,0.6,0.75,0.9,0.05]);
  let t0 = (metric==='proj') ? bt : 0.15, free=false;
  for(const t of ts){
    const tc=Math.max(0,Math.min(1,t));
    const q=at(tc);
    if(bldAt(q.x,q.y)<0){ t0=tc; free=true; break; }
  }
  const q=at(t0);
  if(opt.place){ me.x=q.x; me.y=q.y; me.ang=bs.ang; }
  return {seg:bs, si:bsi, t:t0, x:q.x, y:q.y, ang:bs.ang, d2:bd, free:free};
}
function pickStart(){
  /* 세그먼트 '선택'만 필요하다 — 차는 reset() 이 옮긴다. 배치 계산은 버린다. */
  const g=gangnamXY();
  const r=placeCarNear(g.x*S, g.y*S, {metric:'mid'});
  return r ? r.si : 0;
}
let start=pickStart();
function reset(){
  start=pickStart();                 // ★청크 재구축으로 인덱스가 밀렸을 수 있다
  const s=segs[start],A=nodes[s.a],B=nodes[s.b];
  /* 출발 도로 이름을 남긴다 — 화면만 보고 '경부고속도로 같다'고 추정하지 않기 위해(u_5074) */
  const _g=gangnamXY();
  window.__startRoad = (s.n||'(이름없음)')+' '+(s.l||'?')+'차로 강남역에서 '
                     + Math.round(Math.hypot((A.x+B.x)/2-_g.x*S,(A.y+B.y)/2-_g.y*S)/S)+'m';
  /* ★걸음마 단계에서는 도로 위에서 시작한다(u_4917 실측 근거).
     주차칸 시작은 도로에서 13.3m 떨어져 있어, 직진하면 도로에 닿지 못하고
     5.5초 만에 '도로이탈' 사고가 난다 — 25판 중 19판이 1.6~2.1초에 죽은 원인.
     주차는 별도 단계(4~5)에서 다룬다. */
  /* ★주차칸 출발은 학습·수집에 해롭다(2026-09-14 u_4950 지적으로 발견).
     PARK.bays[2] 는 도로 밖 13.25m 지점이다. 수집 빌드는 LEARN 이 아니라
     이쪽으로 빠져서, 교사가 도로를 벗어난 채 계속 달렸다.
     실측: 학습 데이터 29,121프레임 중 51%가 차로중심 10m 초과(중앙값 13.25m).
     그 상태로 모은 데이터가 '좌측통행/차로무시'처럼 보인 원인이다.
     ⇒ LEARN 이든 아니든 도로 위에서 출발한다. 주차는 별도 단계에서 다룬다. */
  if(segs.length && segs[start]){
    const sg=segs[start],A2=nodes[sg.a],B2=nodes[sg.b];
    const off2=laneOffset(sg,1,0);
    me.x=(A2.x+B2.x)/2-Math.sin(sg.ang)*off2;
    me.y=(A2.y+B2.y)/2+Math.cos(sg.ang)*off2;
    me.ang=sg.ang;
  }else{
    const off=laneOffset(s,1,0);
    me.x=(A.x+B.x)/2-Math.sin(s.ang)*off;
    me.y=(A.y+B.y)/2+Math.cos(s.ang)*off;
    me.ang=s.ang;
  }
  me.v=0;me.dmg=0;me.crashes=0;me.offroad=0;
  resetTeacherLane();
  _autoOff('reset'); auto.on=0;auto.goal=null;auto.wp=[];seed();sync();flash('리셋');
}

/* ---------- 도로 판정(인도 침범 감지) ---------- */
function nearestSeg(x,y){
  let best=null;
  for(const s of segs){
    const A=nodes[s.a],B=nodes[s.b];
    const vx=B.x-A.x,vy=B.y-A.y,L=vx*vx+vy*vy;
    let t=L?((x-A.x)*vx+(y-A.y)*vy)/L:0;t=Math.max(0,Math.min(1,t));
    const px=A.x+vx*t,py=A.y+vy*t,d=Math.hypot(px-x,py-y);
    if(!best||d<best.d)best={d,s,t,px,py};
  }
  return best;
}
/* ★차선변경 중에는 '방금까지 달리던 도로'로 판정한다(u_5146 실사고).
   onRoad 는 nearestSeg — 가장 가까운 중심선 — 으로 판정한다. 그런데 차선을
   바꾸는 동안 차는 두 차로에 걸치고, 그 순간 옆 도로가 더 가까워진다.
   그러면 게임이 '남의 도로' 기준으로 이탈을 계산한다.
   실측: xt=1.70m 인데 margin=6.50m — 도로 한복판인데 '도로 이탈' 로 찍혔다.
   차선변경·회피·추월이 정확히 이 상황이라, 그 동작을 할 때마다 게임이 끊겼다.
   ⇒ 직전 프레임의 도로를 기억해두고, 그 도로 위에 있으면 그걸로 판정한다. */
let _lastSeg=null, _lastSegT=0;
function onRoad(x,y){
  const n=nearestSeg(x,y);
  if(!n)return{ok:false,d:1e9,s:null};
  /* 직전 도로가 아직 유효하면(1.5초 이내) 그 도로 기준도 같이 본다 */
  if(_lastSeg && _lastSeg!==n.s && (performance.now()-_lastSegT)<1500){
    const A=nodes[_lastSeg.a], B=nodes[_lastSeg.b];
    /* ★청크 스트리밍으로 nodes 가 재구성되면 캐시된 _lastSeg 의 인덱스가 죽는다.
       실측: loop 에서 "Cannot read properties of undefined (reading 'x')" 51회. */
    if(!A||!B){ _lastSeg=null; }else{
    const vx=B.x-A.x, vy=B.y-A.y, L=vx*vx+vy*vy;
    let t=L?((x-A.x)*vx+(y-A.y)*vy)/L:0; t=Math.max(0,Math.min(1,t));
    const d0=Math.hypot(A.x+vx*t-x, A.y+vy*t-y);
    if(d0<=_lastSeg.roadW*.5){            // 원래 도로 위에 있으면 그게 정답이다
      return{ok:true, d:d0, s:_lastSeg, edge:d0-_lastSeg.roadW*.5};
    }
    }
  }
  const ok=n.d<=n.s.roadW*.5;
  if(ok){ _lastSeg=n.s; _lastSegT=performance.now(); }
  return{ok,d:n.d,s:n.s,edge:n.d-n.s.roadW*.5};
}
/* ★교차로 근접 판정(2026-09-15).
   교차로에서는 좌/우회전으로 중앙선을 넘는 것이 합법이고, 그 지점에서
   nearestSeg 는 교차하는 쪽 도로를 집기 쉽다. XR[n]=간선 3개 이상=교차로.
   구간 sg 의 양 끝 노드 중 교차로인 것에서 roadW*1.5 안쪽이면 참. */
function nearJunction(x,y,sg){
  const R=sg.roadW*1.5, R2=R*R;
  for(const ni of [sg.a, sg.b]){
    if(!XR[ni]) continue;
    const n=nodes[ni];
    if((n.x-x)**2+(n.y-y)**2 <= R2) return true;
  }
  return false;
}

/* ★보행자 제동 판정 — 교사(teacher.js)와 내비주행(driveAuto)이 '같은 하나'를 쓴다.
   WHY(u_5056 후속): 예전엔 이 규칙이 두 군데 손으로 복사돼 있었고, 서로 달랐다.
   내비 주행에서는 driveAuto 가 핸들을 쥐고 교사는 제동 거부권만 내므로, 둘이
   매 프레임 '설지 말지'를 다르게 판단했다. 실측된 두 갈래:
     · 교사: 횡 4m 고정 + 인도 필터 없음 → 건너편 인도에 서 있는 사람에게도 섰다
       (u_5056 과브레이크 사고의 원인. 교차로엔 항상 누가 있어 영원히 안 풀린다).
     · driveAuto: 횡 2.2m + `!p.cross && !onRoad()` → p.cross 가 켜졌다는 이유만으로
       아직 인도에 서 있는 무단횡단 보행자를 차도에 있는 것으로 쳤다.
   PED_CROSS_LAT_M 을 왜 안 넓히나: 2.2m 는 u_5056 의 과브레이크 수정값 그 자체다.
   넓히면 그 사고가 그대로 돌아온다. 그래서 '넓히기'가 아니라 '차도 점유 여부'로 푼다.

   판정 = 차도에 실제로 서 있는가(onRoad). p.cross 플래그는 쓰지 않는다.
   측정으로 확인한 이유(4차로 roadW=13m, h=8m 기준):
     · 무단횡단 시작 순간(cross=1, cx2=0) off=8.0m → 아직 인도다. 플래그를 믿으면
       인도 위 사람에게 제동한다.
     · 횡단 완료로 cross=0 되는 순간(|cx2|=cmax) off=-8.0m → 이미 건너편 인도다.
       즉 플래그가 꺼질 때 사람은 차도 밖이므로, 플래그를 버려도 놓치는 구간이 없다.
   결국 onRoad 하나가 두 경우를 모두 정확히 가른다. */
const PED_SLOW_M      = 25;    // 이 거리 안이면 감속
const PED_STOP_M      = 12;    // 이 거리 안이면 정지
const PED_CROSS_LAT_M = 2.2;   // 차도 위 보행자: 내 차로 폭만(u_5056 과브레이크 수정값)
function pedBrakeDist(){
  if(typeof peds==='undefined' || !peds || !peds.length) return 1e9;
  const ca=Math.cos(me.ang), sa=Math.sin(me.ang);
  let best=1e9;
  for(const p of peds){
    const dx=p.x-me.x, dy=p.y-me.y;
    const f=(dx*ca+dy*sa)/S;                 // 전방거리(m). 0 이하면 이미 지나쳤다
    if(f<=0 || f>=PED_SLOW_M) continue;      // 뒤에서 걷는 사람 때문에 서면 안 된다
    const l=Math.abs(-dx*sa+dy*ca)/S;        // 횡방향 거리(m)
    if(l>PED_CROSS_LAT_M) continue;
    if(!onRoad(p.x,p.y).ok) continue;        // 인도 위 사람은 무시(차도 점유만 본다)
    if(f<best) best=f;
  }
  return best;
}

/* ---------- A* ---------- */
function nearestNode(x,y){let b=0,d=1e18;
  for(let i=0;i<nodes.length;i++){const t=(nodes[i].x-x)**2+(nodes[i].y-y)**2;
    if(t<d){d=t;b=i}}return b}
/* ★도로교통법을 지키는 경로탐색 (u_5022 오너 지적).
   문제: 기존 A* 는 방향 없는 그래프였다. other(seg,c) 로 모든 간선을 양방향 통행했다.
     → 반대편 차선을 목적지로 찍으면 '그 자리에서 즉시 유턴'이 최단경로로 나온다.
     → 일방통행도 역주행한다. 이건 운전이 아니다.
   해결: 상태를 '노드'가 아니라 **(노드, 들어온 간선)** 으로 둔다.
     · 일방통행(o=true)은 a→b 방향으로만 통행
     · 같은 간선으로 되돌아가기(=제자리 유턴)는 금지
     · 교차로가 아닌 곳(간선 2개)에서의 방향전환도 금지 — 유턴은 교차로에서만
   비용은 거리 그대로. '돌아가더라도 합법인 길'이 유일한 해가 된다. */
function segAllows(si, from){
  const sg = segs[si];
  if(!sg.o) return true;              // 양방향 도로
  return sg.a === from;               // 일방통행은 a→b 만
}
function isJunction(n){ return (nodes[n].e || []).length >= 3; }

function astar(s,t){
  /* 상태키 = "노드|들어온간선". 시작은 들어온 간선이 없다(-1). */
  const key=(n,si)=>n+'|'+si;
  const G={}, F={}, came={}, seen=new Set();
  const h=(a,b)=>Math.hypot(nodes[a].x-nodes[b].x,nodes[a].y-nodes[b].y);
  const st0=key(s,-1);
  G[st0]=0; F[st0]=h(s,t);
  const open=[{n:s, si:-1, k:st0}];
  let guard=0;
  while(open.length && guard++ < 200000){
    open.sort((a,b)=>F[a.k]-F[b.k]);
    const cur=open.shift();
    if(cur.n===t){
      const p=[cur.n]; let k=cur.k;
      while(came[k]!==undefined){ const pv=came[k]; p.unshift(pv.n); k=pv.k; }
      return p;
    }
    if(seen.has(cur.k)) continue;
    seen.add(cur.k);
    for(const si of nodes[cur.n].e){
      if(si===cur.si) continue;                       // 왔던 길로 되돌아가기 = 제자리 유턴 금지
      if(!segAllows(si, cur.n)) continue;             // 일방통행 역주행 금지
      /* 교차로가 아닌 지점에서 방향을 바꾸는 것도 유턴이다.
         간선이 2개뿐인 중간노드에서는 계속 진행만 허용된다(위 si!==cur.si 로 이미 보장). */
      const nb=other(segs[si],cur.n);
      const nk=key(nb,si);
      const ng=(G[cur.k]||0)+segs[si].len;
      if(G[nk]===undefined||ng<G[nk]){
        G[nk]=ng; F[nk]=ng+h(nb,t); came[nk]={n:cur.n,k:cur.k};
        if(!seen.has(nk)) open.push({n:nb, si:si, k:nk});
      }
    }
  }
  return null;
}
/* ★장거리 경로용 전역 그래프(2026-09-14 u_4947).
   streamWorld 는 3x3 청크(±1.5km)만 nodes/segs 에 올린다. 그래서 4km 떨어진
   종합운동장으로 planTo 하면 목적지 노드가 아예 없어 A* 가 항상 null 을 냈다
   (실측: dm=17 회 시도, wp=0). 경로 탐색만은 전체 도로로 해야 한다. */
let GNODES=null, GSEGS=null, GIDX=null;
function buildGlobalGraph(){
  if(GNODES||!CH) return;
  const all=[];
  BLDS_ALL=[];
  for(const k in CH){ const c=CH[k]; if(!c) continue;
    if(c.r) all.push(...c.r);
    if(c.b) BLDS_ALL.push(...c.b);            // 가상간선이 건물을 뚫는지 검사용
  }
  const map=new Map(); GNODES=[]; GSEGS=[];
  const key=(x,y)=>Math.round(x*10)+','+Math.round(y*10);
  const nid=(x,y)=>{ const k=key(x,y); let i=map.get(k);
    if(i===undefined){ i=GNODES.length; map.set(k,i); GNODES.push({x:x*S,y:y*S,e:[]}); }
    return i; };
  for(const r of all){
    const p=r.p; if(!p||p.length<2) continue;
    for(let i=0;i+1<p.length;i++){
      const a=nid(p[i][0],p[i][1]), b=nid(p[i+1][0],p[i+1][1]);
      if(a===b) continue;
      const A=GNODES[a],B=GNODES[b];
      const len=Math.hypot(B.x-A.x,B.y-A.y);
      /* ★차로수·일방통행을 간선에 싣는다(u_5025).
         이게 없으면 경로를 중심선에서 무조건 1.75m 로만 띄우게 되는데,
         일방통행 도로에서는 그 위치가 반대쪽 끝(실측 오차 5.25~7.0m)이라
         주행선이 도로 밖·역주행 위치에 놓인다. */
      /* ★w(way id)·nd(끝점 OSM 노드 id)를 간선에 싣는다(a_5053).
         회전제한 키가 "<from_way>|<via_node>|<to_way>" 라 이 둘이 없으면 조회가 안 된다.
         way 는 여러 간선으로 쪼개지므로 끝점 id 는 '맨 앞/맨 뒤 간선'에만 유효하다:
         n0 = 이 간선의 a 가 way 시작점일 때만, n1 = b 가 way 끝점일 때만 채운다.
         교차로 = 두 way 가 끝점 노드를 공유하는 지점이므로 이걸로 via 판정이 된다. */
      const nd=r.nd;
      const si=GSEGS.length;
      GSEGS.push({a,b,len,l:(r.l||2),o:!!r.o,
                  w:(r.w||0),
                  n0:(nd&&i===0)?nd[0]:0,
                  n1:(nd&&i+2===p.length)?nd[1]:0});
      A.e.push(si); B.e.push(si);
    }
  }
  stitchGraph();
  // 회전금지 테이블 적재(a_5053). data6.js 의 TURNS 전역. 없으면 제한 없이 동작.
  if(!RESTRICT) loadRestrict(typeof TURNS!=='undefined'?TURNS:{});
}

/* ★끊긴 도로망 잇기 (u_5005 실사고).
   OSM 도로는 교차해도 정확히 같은 좌표를 공유하지 않는 경우가 많다. 좌표 일치
   (0.1 정밀도)로만 노드를 합치면 그래프가 섬으로 쪼개진다.
   실측: 노드 17,649 / 연결요소 96개. 최대 요소가 86%, 나머지 14%가 고립.
   차와 목적지가 다른 섬에 있으면 A* 가 반드시 실패한다 — '테헤란로 검색이 안 된다'의
   진짜 원인이 이것이었다(검색은 정상, 경로탐색이 실패). 실측 GO=1/1 로 확인.
   → 25m 이내로 가까운 섬끼리 가상 간선으로 잇는다(실측: 95개 중 53개가 연결 가능). */
function stitchGraph(){
  const N=GNODES.length; if(!N) return;
  const comp=new Int32Array(N).fill(-1);
  let nc=0;
  for(let i=0;i<N;i++){
    if(comp[i]>=0) continue;
    const q=[i]; comp[i]=nc;
    while(q.length){
      const u=q.pop();
      for(const si of GNODES[u].e){
        const sg=GSEGS[si], v=(sg.a===u)?sg.b:sg.a;
        if(comp[v]<0){ comp[v]=nc; q.push(v); }
      }
    }
    nc++;
  }
  if(nc<2) return;
  // 요소 크기 → 가장 큰 것이 본토
  const size=new Int32Array(nc);
  for(let i=0;i<N;i++) size[comp[i]]++;
  let main=0; for(let c=1;c<nc;c++) if(size[c]>size[main]) main=c;
  // 본토 노드를 격자에 담는다(전수비교는 O(n^2) 라 못 쓴다)
  const R=25*S, g=new Map();
  const gk=(x,y)=>((x/R)|0)+','+((y/R)|0);
  for(let i=0;i<N;i++){
    if(comp[i]!==main) continue;
    const k=gk(GNODES[i].x,GNODES[i].y);
    let a=g.get(k); if(!a){a=[];g.set(k,a);} a.push(i);
  }
  let joined=0, rejected=0;
  for(let c=0;c<nc;c++){
    if(c===main) continue;
    let bi=-1,bj=-1,bd=R*R;
    for(let i=0;i<N;i++){
      if(comp[i]!==c) continue;
      const x=GNODES[i].x,y=GNODES[i].y,gx=(x/R)|0,gy=(y/R)|0;
      for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++){
        const arr=g.get((gx+dx)+','+(gy+dy)); if(!arr) continue;
        for(const j of arr){
          const d=(GNODES[j].x-x)**2+(GNODES[j].y-y)**2;
          if(d<bd){ bd=d; bi=i; bj=j; }
        }
      }
    }
    if(bi>=0){
      /* ★중간점이 실제 도로 위가 아니면 잇지 않는다(u_5024).
         무조건 이으면 건물·강·철로를 가로지르는 '없는 길'이 생긴다.
         실측(강남 3x3): 이렇게 만든 6개 간선의 중간점이 6/6 모두 도로 밖
         (median 7.2m·max 12.3m) — 이것이 '길 없는 곳으로 간다'의 원인이었다. */
      /* ★전역 그래프 기준으로 판정해야 한다. onRoad()/nearestSeg() 는 적재된 청크
         (차 주변)만 보기 때문에, 멀리 있는 섬은 무조건 '도로 아님'이 되어
         전부 기각된다 → 경로탐색 자체가 실패한다(실측: wp=0, 화면 '도로 이탈'). */
      if(gapOK(GNODES[bi].x,GNODES[bi].y,GNODES[bj].x,GNODES[bj].y)){
        const len=Math.hypot(GNODES[bj].x-GNODES[bi].x, GNODES[bj].y-GNODES[bi].y);
        const si=GSEGS.length; GSEGS.push({a:bi,b:bj,len,v:1});   /* v=가상간선 */
        GNODES[bi].e.push(si); GNODES[bj].e.push(si);
        joined++;
      }else rejected++;
    }
  }
  window.__stitch = nc+'->'+(nc-joined)+' (기각 '+rejected+')';
}
/* 전역 그래프의 실제 도로 간선 중 (x,y) 에 가장 가까운 지점. 가상간선은 제외한다. */
/* 두 점을 잇는 가상 간선이 통행 가능한가.
   ★'중간점이 도로 위인가'로 물으면 안 된다 — 섬 사이 간격은 정의상 도로가 없는
   곳이라 정상적인 연결까지 전부 기각된다(실제로 그렇게 짰다가 경로탐색이 통째로
   실패했다: wp=0·화면 '도로 이탈').
   실제로 막아야 하는 건 '건물을 관통하는 연결'이다. */
function gapOK(ax,ay,bx,by){
  for(const g of BLDS_ALL){
    const p=g.p; if(!p||p.length<3) continue;
    for(let i=0;i<p.length;i++){
      const q=p[i], r=p[(i+1)%p.length];
      if(segInt(ax,ay,bx,by, q[0]*S,q[1]*S, r[0]*S,r[1]*S)) return false;
    }
  }
  return true;
}
function segInt(x1,y1,x2,y2,x3,y3,x4,y4){
  const d=(x2-x1)*(y4-y3)-(y2-y1)*(x4-x3);
  if(Math.abs(d)<1e-9) return false;
  const t=((x3-x1)*(y4-y3)-(y3-y1)*(x4-x3))/d;
  const u=((x3-x1)*(y2-y1)-(y3-y1)*(x2-x1))/d;
  return t>0&&t<1&&u>0&&u<1;
}
function gNearestOnRoad(x,y){
  if(!GSEGS) return null;
  let best=null;
  for(const sg of GSEGS){
    if(sg.v) continue;                       // 가상간선 = 실제 도로 아님
    const A=GNODES[sg.a],B=GNODES[sg.b];
    const vx=B.x-A.x,vy=B.y-A.y,L=vx*vx+vy*vy;
    let t=L?((x-A.x)*vx+(y-A.y)*vy)/L:0; t=Math.max(0,Math.min(1,t));
    const px=A.x+vx*t,py=A.y+vy*t,d=(px-x)**2+(py-y)**2;
    if(!best||d<best.d2) best={d2:d,px,py};
  }
  return best;
}
function gNearest(x,y){
  let bi=0,bd=1e18;
  for(let i=0;i<GNODES.length;i++){
    const d=(GNODES[i].x-x)**2+(GNODES[i].y-y)**2;
    if(d<bd){bd=d;bi=i}
  }
  return bi;
}
/* ★출발점은 '차가 실제로 달리고 있는 도로'에서 잡는다(u_5032).
   오너 실사고: "지금 주행중인 차는 경부선인데 그 옆길로 경로를 찾아주냐".
   gNearest 는 거리만 본다. 고속도로 옆에는 램프·側道가 바로 붙어 있어서
   (실측: 고속도로 표본 8곳 중 4곳이 20m 이내, 2곳은 0.0m) 옆 도로 노드가
   최근접으로 잡힌다. 그러면 경로가 '옆길에서 출발'하는 것으로 만들어지고,
   차는 고속도로 위에서 그 옆길로 가려고 그 자리에서 튼다.
   해결: 진행방향이 맞는 간선만 후보로 본다 — 그래야 고속도로를 계속 타고
   가다 '진짜 진출로'에서 빠지는 경로가 나온다. */
function gStartNode(x,y,ang){
  if(!GSEGS||!GSEGS.length) return gNearest(x,y);
  const fx=Math.cos(ang), fy=Math.sin(ang);
  /* ★a_5051 실측으로 원인을 특정했다(추정 아님). 오프라인 300표본×무작위 heading:
       - 간선 선택은 이미 정확하다: '차→선택간선 투영점' 거리 p95=0.4m, max=3.5m.
       - 그런데 반환값이 '끝점'이라 실제 출발점 거리 p95=48.7m, max=100.7m 로 튄다.
       - 먼 사례의 간선 길이 중앙값 34.9m(전체 20.2m), 투영 t 중앙값 0.43 = 간선 한복판.
     즉 xt=31.6m 은 '엉뚱한 도로를 골라서'가 아니라 '맞는 도로의 먼 끝점을 줘서' 생긴다.
     반경(26m)·점수식은 주범이 아니었다. → 투영점에 노드를 만들어 그 자리에서 출발한다. */
  let bsi=-1, bem=-1, bt=0, bal=0;
  for(let si=0;si<GSEGS.length;si++){
    const sg=GSEGS[si]; if(sg.v) continue;
    const A=GNODES[sg.a], B=GNODES[sg.b];
    const vx=B.x-A.x, vy=B.y-A.y, L=Math.hypot(vx,vy); if(L<1) continue;
    const L2=vx*vx+vy*vy;
    let t=((x-A.x)*vx+(y-A.y)*vy)/L2; t=Math.max(0,Math.min(1,t));
    const d=Math.hypot(A.x+vx*t-x, A.y+vy*t-y);
    if(d>50*S) continue;                       // Valhalla search_radius 기본 50m
    const dot=(vx*fx+vy*fy)/L;
    const align = sg.o ? dot : Math.abs(dot);
    /* fmm calc_ep(ar_5034 Q1) = exp(-0.5*(d/σ)²). 우리는 GPS가 아니라 '진짜 heading'을
       알기 때문에 cos(Δθ)² 을 곱한다. 하드컷 없음(GraphHopper 원칙) — 후보가 0이 되는
       일이 없고, 방향이 반대인 간선은 cos<0 → 0 으로 자연히 탈락한다. */
    const c = Math.max(0, align);
    const em = Math.exp(-0.5*Math.pow(d/(8*S),2)) * c*c;
    if(em>bem){ bem=em; bsi=si; bt=t; bal=align; }
  }
  if(bsi<0) return gNearest(x,y);              // hard-fail 금지
  const sg=GSEGS[bsi], A=GNODES[sg.a], B=GNODES[sg.b];
  const vx=B.x-A.x, vy=B.y-A.y;
  const px=A.x+vx*bt, py=A.y+vy*bt;
  /* 진행방향 '앞' 끝점이 이미 충분히 가까우면(8m) 그걸 쓴다 — 매번 노드를 만들면
     그래프가 계속 커진다(실측 300표본 중 129건이 이 경우). */
  const fa=(A.x-x)*fx+(A.y-y)*fy, fb=(B.x-x)*fx+(B.y-y)*fy;
  const fwd = sg.o ? sg.b : (fa>fb ? sg.a : sg.b);
  const F=GNODES[fwd];
  const fd=Math.hypot(F.x-x,F.y-y);
  if(fd<=8*S && ((F.x-x)*fx+(F.y-y)*fy)>0) return fwd;
  /* ★투영점을 그래프에 끼워넣는다. 간선을 A-P-B 로 쪼개고 원래 간선은 막는다(v=1).
     이렇게 해야 A* 가 '차가 서 있는 그 지점'에서 출발한다. 끝점을 주면 차는 최대
     100m 떨어진 데서 시작하는 경로를 받고, 거기로 가려다 길 아닌 데로 튼다(s=0 고정). */
  const pi=GNODES.length;
  GNODES.push({x:px,y:py,e:[]});
  const la=Math.hypot(px-A.x,py-A.y), lb=Math.hypot(B.x-px,B.y-py);
  /* ★w/n0/n1 을 새 간선에 승계한다(ar_5053 지적).
     간선을 쪼갤 때 way id 를 안 넘기면, 그 간선에 걸린 회전금지가 조회되지 않아
     출발 직후 첫 교차로에서만 제한이 빠진다. */
  const s1=GSEGS.length; GSEGS.push({a:sg.a,b:pi,len:la,l:sg.l,o:sg.o,w:sg.w,n0:sg.n0,n1:sg.n1});
  const s2=GSEGS.length; GSEGS.push({a:pi,b:sg.b,len:lb,l:sg.l,o:sg.o,w:sg.w,n0:sg.n0,n1:sg.n1});
  GNODES[sg.a].e.push(s1); GNODES[pi].e.push(s1);
  GNODES[pi].e.push(s2);  GNODES[sg.b].e.push(s2);
  sg.v=1;                                      // 원본 간선은 이제 쓰지 않는다
  (window.__gSplit=window.__gSplit||[]).push(bsi);   // 복구용 기록(planTo 가 되돌린다)
  return pi;
}
/* ★실제로 쓰이는 경로탐색은 이 gAstar 다(astar 는 전역그래프 실패시 대체).
   u_5022 에서 도로교통법을 astar 에만 넣었더니 실제 경로에는 하나도 적용되지
   않았다 — 오너 실사고: "경부선에서 코엑스 가는데 그자리에서 우회전을 해버린다".
   고속도로는 데이터상 o:true(일방)인데 양방향으로 훑고 있었고, 아무 노드에서나
   빠져나갈 수 있었다. 상태를 (노드, 들어온 간선) 으로 바꿔 두 가지를 막는다:
     · 일방통행 역주행
     · 왔던 간선으로 되돌아가기(제자리 유턴)
   ★간선 방향 판정: GSEGS 의 a→b 가 진행 가능 방향이다(일방일 때). */
function gSegAllows(sg, from){
  if(!sg.o) return true;          // 양방향 도로
  return sg.a === from;           // 일방통행은 a→b 만
}
/* ★회전금지(a_5053). RESTRICT = data/seoul/restrictions.json 의 turn_costs,
   키 "<from_way>|<via_node>|<to_way>" → 값 no_left_turn / only_straight_on 등.
   오너 실사고 u_5042: "우회전 안해야 할 곳에서 우회전".

   ★only_* 는 no_* 의 반대다(ar_5046 이 '흔한 버그'로 지목한 지점).
     no_left_turn      : 그 (from,via,to) 전이 '하나만' 금지.
     only_straight_on  : 그 via 에서 '지정된 to 를 제외한 나머지 전부' 금지.
   only_* 를 단순 금지로 짜면 합법 회전까지 막힌다 — 아래 onlyTo 분기가 그 처리다. */
let RESTRICT=null, RONLY=null;
function loadRestrict(tbl){
  RESTRICT=tbl||{}; RONLY={};
  for(const k in RESTRICT){
    if(RESTRICT[k].slice(0,5)!=='only_') continue;
    const p=k.split('|');                 // from|via|to
    (RONLY[p[0]+'|'+p[1]] ||= []).push(p[2]);
  }
}
window.loadRestrict=loadRestrict;
/* 간선이 via 노드에서 갖는 OSM way id. way 는 여러 간선으로 쪼개지므로
   끝점 간선에만 n0/n1 이 실려 있다. via 와 맞닿은 쪽 id 를 돌려준다. */
function segWayAt(sg, viaOsmId){
  if(!sg || !sg.w) return 0;
  if(sg.n0===viaOsmId || sg.n1===viaOsmId) return sg.w;
  return 0;
}
function gTurnBlocked(prevSi, viaNode, nextSi){
  if(!RESTRICT || prevSi<0) return false;
  const A=GSEGS[prevSi], B=GSEGS[nextSi];
  if(!A||!B||!A.w||!B.w) return false;         // way id 없으면 판정 불가 → 통과
  const N=GNODES[viaNode];
  const via = (A.n0&&(A.a===viaNode))?A.n0 : (A.n1&&(A.b===viaNode))?A.n1 : 0;
  if(!via) return false;                        // 이 노드는 way 끝점이 아니다(교차로 아님)
  const fw=A.w, tw=B.w;
  if(fw===tw) { /* 같은 way 계속 진행 — u턴 제한만 의미 있다 */ }
  /* ★순서 주의(오프라인 검증에서 실제로 걸린 버그): only_* 키도 같은 테이블에 들어있다.
     only_* 키가 가리키는 전이는 '금지'가 아니라 '의무'다. 먼저 RESTRICT 를 조회해
     무조건 막아버리면 합법(의무) 회전까지 막힌다 — 실측 0/20 통과였다.
     그래서 ① only_* 지정 전이면 즉시 허용 ② no_* 만 금지 ③ 나머지 only_* 역적용. */
  const only=RONLY[fw+'|'+via];
  if(only && only.indexOf(String(tw))>=0) return false;   // ① 의무 회전 = 항상 허용
  const v=RESTRICT[fw+'|'+via+'|'+tw];
  if(v && v.slice(0,3)==='no_') return true;              // ② no_* 만 단일 금지
  if(only && only.length && fw!==tw) return true;         // ③ only_* : 나머지 전부 금지
  return false;
}
function gAstar(s,t,startAng){
  const key=(n,si)=>n+'|'+si;
  const st={n:s,si:-1};
  const G={[key(s,-1)]:0}, came={}, open=[st], seen=new Set();
  const h=(a)=>Math.hypot(GNODES[a].x-GNODES[t].x,GNODES[a].y-GNODES[t].y);
  const F={[key(s,-1)]:h(s)};
  let guard=0;
  while(open.length && guard++<400000){
    open.sort((a,b)=>F[key(a.n,a.si)]-F[key(b.n,b.si)]);
    const cur=open.shift(), ck=key(cur.n,cur.si);
    if(cur.n===t){
      const p=[cur.n]; let k=ck;
      while(came[k]!==undefined){ const pv=came[k]; p.unshift(pv.n); k=key(pv.n,pv.si); }
      return p;
    }
    if(seen.has(ck)) continue;
    seen.add(ck);
    for(const si of GNODES[cur.n].e){
      if(si===cur.si) continue;                     // 제자리 유턴 금지
      const sg=GSEGS[si];
      if(!gSegAllows(sg, cur.n)) continue;          // 일방통행 역주행 금지
      if(gTurnBlocked(cur.si, cur.n, si)) continue; // ★회전금지(a_5053)
      const nb=(sg.a===cur.n)?sg.b:sg.a;
      /* ★첫 구간은 차가 지금 향한 방향으로만 나간다(u_5048).
         오너: "건너편으로 차가 가려고 이동하는데. 가운데는 분리선이고
         건너편은 역주행이라 가면 안 되는 곳".
         왕복도로는 양방향 통행이 합법이라, A* 가 출발하자마자 같은 도로를
         반대 방향으로 되짚는 경로를 만들 수 있다. 그러면 웨이포인트가 맞은편
         차도에 놓이고, 차는 중앙선을 넘어야만 그 경로에 올라탈 수 있다.
         출발 순간만 방향을 강제하면 이 경로 자체가 안 만들어진다. */
      if(cur.si===-1 && startAng!==undefined){
        const A=GNODES[cur.n], B=GNODES[nb];
        const ea=Math.atan2(B.y-A.y, B.x-A.x);
        let dd=((ea-startAng+Math.PI*3)%(Math.PI*2))-Math.PI;
        if(Math.abs(dd) > Math.PI/2) continue;      // 뒤로 나가는 첫 구간 금지
      }
      /* 가상간선(stitch)은 실제 도로가 아니다 — 비용 40배로 최후수단화(u_5024). */
      /* ★좁은 도로는 비용을 올려 우회시킨다(u_5117 실측).
         실측: 사고 9건 중 9건이 전부 같은 1차로 도로(폭 3.25m)에서 났다.
           rOff=0 — 경로선은 중심선 위로 완벽하다. 더 개선할 여지가 없다.
           그런데 허용 반경 1.63m 에 차폭이 1.8m 라 실질 여유가 0.72m 뿐이고,
           실제 이탈거리는 2.30m 였다(여유의 3배).
         제어기를 아무리 조여도 0.72m 안에서 코너를 도는 건 무리다.
         사람도 골목을 피해 큰길로 가듯, 경로 단계에서 좁은 길을 피한다.
         금지가 아니라 가중치다 — 좁은 길밖에 없으면 여전히 쓴다. */
      const narrow = (sg.l||2) <= 1 ? 12 : ((sg.l||2) <= 2 ? 2.5 : 1);
      const ng=G[ck]+sg.len*(sg.v?40:1)*narrow;
      const nk=key(nb,si);
      if(G[nk]===undefined||ng<G[nk]){
        came[nk]={n:cur.n,si:cur.si}; G[nk]=ng; F[nk]=ng+h(nb);
        if(!seen.has(nk)) open.push({n:nb,si});
      }
    }
  }
  return null;
}
/* ★갓길 주차(u_5041 오너 지시). 지금 있는 도로의 가장 바깥 차로 바깥쪽으로
   붙여 세운다. 주행을 완전히 멈추고(교사 포함) 경로도 해제한다. */
function parkCar(){
  _autoOff('parkCar'); auto.on=0; auto.wp=[]; auto.i=0; auto.goal=null;
  const T=window.__teach; if(T) T.auto=false;     // 교사도 정지
  /* ★parkCar 는 '지금 위치의 도로'로만 붙어야 한다(u_5079 실사고).
     hardReset 이 테헤란로@13m 로 올려놨는데 parkCar 가 그 뒤에 돌면서
     경부고속도로로 옮겼다 — 실측 'pick:테헤란로@13m ... START: 경부고속도로 783m'.
     원인은 nearestSeg 가 차 주변 청크만 보는데 그 청크가 아직 안 바뀌어 있어서다.
     스냅 전에 월드를 현재 위치 기준으로 다시 스트리밍한다. */
  try{ if(typeof streamWorld==='function') streamWorld(true); }catch(e){}
  const n=nearestSeg(me.x,me.y);
  /* 스냅 대상이 터무니없이 멀면(청크 미로딩 등) 차라리 움직이지 않는다. */
  if(n && n.d > 60*S){
    me.v=0; me.steer=0; me.offroad=0; me.cool=1.0; window.__parked=1; flash('갓길 주차'); sync(); return;
  }
  if(n){
    const sg=n.s;
    // 진행방향 유지
    let d=((me.ang - sg.ang + Math.PI*3)%(Math.PI*2))-Math.PI;
    const dir = sg.o ? 1 : (Math.abs(d)<Math.PI/2 ? 1 : -1);
    const ang = sg.ang + (dir<0 ? Math.PI : 0);
    // 가장 바깥 차로 중앙 = 갓길 쪽
    const lanes = sg.o ? sg.l : Math.max(1, Math.floor(sg.l/2));
    const off = Math.abs(laneOffset(sg, dir, lanes-1));
    me.x = n.px - Math.sin(ang)*off;
    me.y = n.py + Math.cos(ang)*off;
    me.ang = ang;
  }
  me.v=0; me.steer=0; me.offroad=0; me.cool=1.0;
  window.__parked=1;
  flash('갓길 주차');
  sync();
}
window.parkCar=parkCar;
function planTo(x,y){
  window.__ptCnt=(window.__ptCnt||0)+1;
  buildGlobalGraph();
  /* ★이전 경로에서 gStartNode 가 주입한 노드/간선을 되돌린다(ar_5051 경고).
     gStartNode 는 차 투영점을 실제 노드로 끼워넣어 매칭 정확도를 확보한다
     (실측 p95 131m→7.7m). 대신 호출의 57%가 그래프를 키운다. 경로를 여러 번
     잡으면 GNODES/GSEGS 가 무한히 자란다. 매 plan 시작 시 원래 크기로 자른다. */
  if(GNODES && window.__gBase){
    const b=window.__gBase;
    if(GNODES.length>b.n){
      for(let si=b.s; si<GSEGS.length; si++){       // 주입 간선을 노드 인접목록에서 제거
        const sg=GSEGS[si];
        for(const nd of [sg.a,sg.b]){
          if(nd<b.n && GNODES[nd]){
            const e=GNODES[nd].e, k=e.indexOf(si);
            if(k>=0) e.splice(k,1);
          }
        }
      }
      GNODES.length=b.n; GSEGS.length=b.s;
      for(const sp of (window.__gSplit||[])) if(GSEGS[sp]) GSEGS[sp].v=0;  // 분할표시 복구
      window.__gSplit=[];
    }
  }
  if(GNODES && !window.__gBase) window.__gBase={n:GNODES.length, s:GSEGS.length};
  let p=null, NS=nodes;
  if(GNODES){                                  // 장거리: 전역 그래프로
    /* ★출발점 후보를 여러 개 시도한다(u_5036).
       gStartNode 하나만 믿으면, 그 노드가 막다른 곳이거나(일방통행 진행방향
       끝점의 3.1%가 그렇다) 목적지 방향으로 나가는 길이 없을 때 경로탐색이
       통째로 실패한다 — 화면에서 auto=0, wp=0 으로 확인했다.
       방향 맞는 점 → 그냥 최근접 점 순으로 시도해서 첫 성공을 쓴다. */
    const tgt=gNearest(x,y);
    const cands=[gStartNode(me.x,me.y,me.ang), gNearest(me.x,me.y)];
    for(const sN of cands){
      if(sN===undefined||sN<0) continue;
      const gp=gAstar(sN, tgt, me.ang);
      if(!gp) continue;
      /* ★경로는 '내 차가 있는 도로'에서 시작해야 한다(u_5038 오너 지시).
         출발노드가 차에서 60m 넘게 떨어져 있으면 그건 옆 도로다 — 그런 경로는
         차가 따라갈 수 없고, 따라가려 하면 길 아닌 데를 가로지른다. 버린다. */
      const s0=GNODES[gp[0]];
      if(Math.hypot(s0.x-me.x, s0.y-me.y) > 60*S) continue;
      /* ★경로는 '도로'로 정의한다(u_5035 오너 지시).
         후보 경로의 앞부분이 실제 도로 위인지 검사해서, 아니면 그 경로를 쓰지
         않는다. 도로가 아닌 곳을 지나는 경로는 애초에 경로가 아니다. */
      {
        let ok=0,n=0;
        for(let k=0;k<gp.length && n<25;k++){
          const nd=GNODES[gp[k]];
          if(Math.hypot(nd.x-me.x,nd.y-me.y) > 1200*S) break;  // 미적재 청크는 판정 불가
          if(onRoad(nd.x,nd.y).ok) ok++;
          n++;
        }
        if(n>=3 && ok/n < 0.8) continue;      // 5개 중 1개꼴로 도로 밖이면 버린다
      }
      /* ★u_5185 진단: 경로가 312m 에서 끝난다(목적지까지 8.6km).
         gAstar 가 반환한 노드 수와 실제 끝점이 목적지 근처인지 본다. */
      try{
        const e=GNODES[gp[gp.length-1]], t2=GNODES[tgt];
        window.__planDbg = {nodes:gp.length,
          endToTgt:+(Math.hypot(e.x-t2.x,e.y-t2.y)/S).toFixed(0),
          tgtToMe:+(Math.hypot(t2.x-me.x,t2.y-me.y)/S).toFixed(0)};
      }catch(err){}
      p=gp; NS=GNODES; break;
    }
  }
  if(!p){ p=astar(nearestNode(me.x,me.y),nearestNode(x,y)); NS=nodes; }
  if(!p){ flash('경로 없음'); window.__planFail=(window.__planFail||0)+1; return; }
  /* ★주행선을 '실제 차로 중앙'에 놓는다(u_5025).
     예전엔 중심선에서 무조건 LW*.5(=1.75m)만 띄웠다. 왕복도로는 우연히 맞지만
     일방통행은 전 차로를 쓰기 때문에 기준이 달라서, 올바른 위치가 -3.5m~-5.25m 인데
     +1.75m 로 찍혔다(실측 오차 5.25~7.0m). 그 결과 주행선이 도로 반대쪽 끝이나
     도로 밖에 놓였고, 차는 그 선을 충실히 따라가며 인도로 올라갔다.
     laneOffset() 과 같은 규칙으로 계산한다. */
  /* ★차로 오프셋 부호(u_5030). 적용식이 wp = n - sin(a)*off 라 부호가 뒤집힌다:
     off<0 이면 진행방향 '오른쪽'에 놓인다. 실측으로 확인했다(언주로 일방4차로,
     반폭 7.0m):
        off=-5.25 -> 중심선 +5.25m = 오른쪽 차로(정상)
        off=+1.75 -> 중심선 -1.75m = 왼쪽 반대차로(틀림)
     laneOffset() 의 일방통행 식이 맞다. 부호를 '고치려다' 오히려 반대차로로
     보낼 뻔했다 — 계산해보고 되돌렸다. */
  /* ★a_5111: 일방통행 식을 laneOffset()(game.js:291)과 일치시킨다.
     a_5092 에서 laneOffset 의 일방 분기를 (lane+.5)*LW 로 고쳤는데(중심선 '오른쪽'),
     주행선 계산은 이 복사본이라 옛 식 0.5*LW-(lanes*LW)/2(중심선 '왼쪽')을 그대로 썼다.
     => NPC 는 오른쪽, 주행선은 왼쪽. 규칙이 정반대가 됐다.
     실측(테헤란로 일방3차로, roadW 9.75m): 주행선 -3.25m → 차가 맞은편 차도 쪽으로
     붙고, onRoad() 의 nearestSeg 가 '맞은편 간선'을 집어 차로이탈이 발생했다.
     기록: {n:테헤란로,l:3,o:1,roadW:9.75,xt:3.25,margin:4.88,rOff:-3.25} — xt<margin
     인데도(자기 차도 안인데도) 사고가 났다 = 다른 간선 기준으로 판정된 것. */
  /* ★u_5177 오너 지적 "경로선 자체가 차선 위에 그려짐". 맞다.
     이 함수가 차로수와 무관하게 항상 0.5*LW(=1.62m)를 돌려주고 있었고,
     그러면 경로선은 늘 '1차로 중심' 자리에 놓인다. 그런데 게임의 차로
     기하(laneOffset)는 일방통행을 (lane+0.5)*LW 로 배치한다 — 규약이 서로
     다르다. 실측: 4차로 도로(폭 13m)에서 교사 목표는 8.90m 인데 경로선은
     1.62m 였고, 도로 중심선 6.50m 는 정확히 2/3차로 경계 점선 위다.
     점선 위치 3.25/6.5/9.75, 차로 중심 1.62/4.88/8.12/11.38 —
     경로선이 차로 중심 중 어디에도 안 맞으면 그 선을 따르는 순간 차선을 문다.
     ⇒ laneOffset 과 같은 규약으로 통일한다(주행차로 = 가장 오른쪽 차로 기준
       1차로. 차로 인덱스는 교사가 T.lane 으로 따로 관리한다). */
  /* ★u_5181 오너 지적 "스크린샷만 봐도 안내선과 차선이 겹쳐진게 보인다".
     화면으로 확인했고 사실이었다. 내가 숫자로 '경로점 1.62m = 차로 정중앙'
     이라고 검증했던 건 이 함수의 반환값을 계산한 것이지, 화면에 그려진
     선이 아니었다. 스크린샷 한 장이면 끝날 걸 붙들고 있었다.

     원인: 이 함수가 일방통행·왕복 구분 없이 항상 0.5*LW(1.62m)를 돌려준다.
     nl 을 계산해놓고 쓰지도 않는다. 그런데 게임의 차로 기하(laneOffset)는
     일방통행을 -(roadW/2)+(lane+0.5)*LW 로 배치한다 — 원점이 다르다.
     넓은 일방통행 도로일수록 경로선이 차로 중심에서 멀어지고,
     결국 점선 위에 얹힌다.
     ⇒ laneOffset 과 같은 식을 쓴다. roadW 가 필요하므로 간선을 통째로 받는다. */
  /* ★u_5191 오너 지적 "직진 도로에서 4개 차로 거의 유턴 후 복귀. 경로 설정 개판".
     실측으로 원인이 잡혔다 — 경로선이 0.88~7.50차로를 오가고 1차로 넘게 튀는
     곳이 9번이었다. 차는 그 선을 0.26m 오차로 충실히 따라가므로, 차가 아니라
     경로선이 유턴을 하고 있었다.

     원인: 같은 테헤란로인데 구간마다 차로수가 3→4→3→5 로 다르다.
     '좌측 가장자리에서 1차로'로 잡으면 도로폭이 바뀔 때마다 기준점이 움직인다.
       3차로(9.75m) off -3.25 / 4차로(13m) -4.88 / 5차로(16.25m) -6.50
     3→5차로 전환에서 정확히 3.25m(한 차로)가 점프한다.

     ⇒ 주행차로(가장 오른쪽)를 기준으로 잡는다. 도로가 넓어지든 좁아지든
       오른쪽 끝에서 반 차로 안쪽이라 위치가 연속이다. 한국 도로교통법의
       주행차로 원칙과도 맞는다(추월·좌회전이 아니면 오른쪽). */
  const laneOff=(sg)=>{
    if(!sg) return 0.5*LW;
    const rw = sg.roadW || (Math.max(1, sg.l||2) * LW);
    return sg.o ? (rw*0.5 - 0.5*LW)             // 일방: 오른쪽 끝에서 반 차로 안
                : (rw*0.5 - 0.5*LW);            // 왕복: 진행방향 차도의 오른쪽 끝
  };
  const edgeOf=(i,j)=>{                         // 두 노드를 잇는 간선 찾기
    if(NS!==GNODES) return null;
    for(const si of GNODES[i].e){
      const sg=GSEGS[si];
      if((sg.a===i&&sg.b===j)||(sg.a===j&&sg.b===i)) return sg;
    }
    return null;
  };
  /* ★코너 기하 재작성(u_5057 실측).
     순서를 바꿨다: [리샘플(중심선) → 점마다 자기 국소방향으로 오프셋 → 교차로는 이등분선 호].
     예전엔 각 노드를 '그 노드를 떠나는 간선' 방향으로만 오프셋했다. 직선에서는
     이웃 오프셋이 같아 문제가 없었지만(직진 주행은 지금도 완벽), 교차로에서는
     진입점은 a1, 꼭짓점은 a2 로 오프셋돼 꼭짓점에서 횡방향이 툭 끊겼다.
     실측(왕복2차로 off=+1.75m, 90도):
       좌회전 - 꼭짓점 오프셋이 반대 차도(lat=-1.75m)로 들어간다 → 중앙선 하드
                구속이 위치를 되돌리고 0.9초 뒤 crash('중앙선 침범'). 좌회전마다
                결정적으로 발생했다(간헐 아님).
       올바른 차로중앙은 이등분선 위의 off/cos(Δ/2)=2.47m.
     또 리샘플이 '오프셋 뒤'에 있어서, 교차로 인접 간선은 짧아(L<25m) n=floor(L/25)=0
     → 가장 급한 코너가 가장 성긴 채로 남았다. 5m 한 칸에 90도 → kap≈0.31 →
     vmaxCurve 가 하한 3.5m/s 로 눌려, 실재하지도 않는 코너에서 기어갔다. */
  const RS = 5*S;                                   // 중심선 리샘플 간격 5m
  const wp=[];
  {
    const NP=p.length;
    const nodeAt=i=>NS[p[i]];
    const segAng=i=>{const a=nodeAt(i),b=nodeAt(i+1);return Math.atan2(b.y-a.y,b.x-a.x)};
    const segLen=i=>{const a=nodeAt(i),b=nodeAt(i+1);return Math.hypot(b.x-a.x,b.y-a.y)};
    // 1) 구간별 차로 오프셋(간선 속성)
    const offs=[];
    let _edgeMiss=0;
    for(let i=0;i<NP-1;i++){
      const sg=edgeOf(p[i],p[i+1]);
      if(!sg) _edgeMiss++;
      offs.push(sg ? laneOff(sg) : LW*.5);
    }
    /* ★u_5185 진단: gAstar 는 291노드로 목적지까지 도달하는데(endToTgt=0)
       웨이포인트는 64점 312m 뿐이다. 이 리샘플 단계에서 잘린다.
       NP 와 edgeOf 실패 수를 본다 — edgeOf 가 NS!==GNODES 면 무조건 null 이라
       간선을 못 찾으면 구간 길이도 못 구한다. */
    try{ window.__npDbg = {NP:NP, edgeMiss:_edgeMiss, nsIsG:(NS===GNODES)}; }catch(e){}
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
    let _dropSame=0, _dropBack=0;
    const push=(x,y)=>{
      const q=wp[wp.length-1];
      if(!q){ wp.push({x,y}); return; }
      const dx=x-q.x, dy=y-q.y;
      if(Math.hypot(dx,dy) <= 0.05*S){ _dropSame++; return; }   // 같은 자리
      /* ★u_5185 실사고: 이 '역주행 점' 판정이 2,726점을 버리고 66점만 남겼다.
         291노드·8,195m 경로가 64점·312m 로 잘린 원인이 이것이다.
         원래 의도는 코너 꼭짓점에서 생기는 0.1~0.2m 짜리 잡음 점 제거인데,
         내적 부호만 보면 코너 호가 안쪽으로 꺾일 때 정상 점도 전부 역내적이
         되고, 한 번 걸리면 이후 점이 연쇄로 날아간다.
         ⇒ '짧고 뒤로 가는' 점만 버린다. 정상 간격(5m 리샘플)이면 코너에서
           방향이 꺾여도 경로다. */
      if(wp.length>=2 && Math.hypot(dx,dy) < 1.5*S){
        const r=wp[wp.length-2];
        const px=q.x-r.x, py=q.y-r.y;
        if(px*dx+py*dy < 0){ _dropBack++; return; }              // 짧은 역주행 잡음
      }
      wp.push({x,y});
    };
    /* ★u_5185: 291노드가 64점이 되는 원인을 센다. '역주행 점' 판정이
       코너 호와 다리 리샘플 사이에서 과하게 걸리면 경로 뒷부분이 통째로
       날아간다 — 한 번 걸리기 시작하면 이후 점이 계속 직전 방향과 역내적이 된다. */
    window.__pushDbg = ()=>({same:_dropSame, back:_dropBack, kept:wp.length});
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
      const c=window.__NOARC?null:corner[i+1];
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
  /* ★마지막 지점은 반드시 '도로 위'로 스냅한다(u_4896).
     POI 원점은 건물 안/뒤라서 그대로 두면 경로 마지막 구간이 길이 아닌 곳을 가로지른다. */
  /* ★목적지 스냅은 전역 그래프(GSEGS) 기준으로 한다(u_5024).
     nearestSeg 는 로컬 segs(적재된 청크)만 본다 → 먼 목적지는 '차 근처 도로'로
     스냅돼 마지막 구간이 아무것도 없는 곳을 직선으로 가로질렀다. */
  /* ★u_5185/5187 실사고: 여기서 목적지를 '무조건' 붙인다.
     경로 탐색이 실패해 중간이 비어도 마지막 점만 목적지로 꽂히므로,
     경로가 64점(약 320m)에서 끊긴 채 8,286m 를 순간이동하는 선이 된다.
     실측: 점 65개, 중앙간격 5.1m 인데 마지막 한 칸만 8286m —
     (300,-112) → (-4309,-6998). 차는 그 점을 향해 급선회하고,
     그게 화면에서 '제자리 피턴'으로 보인다. 닿는 순간 진행률도 1.0 으로 튄다.
     ⇒ 직전 점과 정상 간격(리샘플 5m 의 20배=100m) 안일 때만 붙인다.
       멀면 경로 탐색이 실패한 것이므로 붙이지 않고 그대로 둔다 —
       짧아도 '이어진 경로'가 끊긴 경로보다 낫다. */
  const nn=gNearestOnRoad(x,y) || nearestSeg(x,y);
  {
    const dst = nn ? {x:nn.px, y:nn.py} : {x, y};
    const last = wp[wp.length-1];
    const gap = last ? Math.hypot(dst.x-last.x, dst.y-last.y)/S : 0;
    if(!last || gap <= 100){
      wp.push(dst);
    }else{
      window.__wpTrunc = {gap:+gap.toFixed(0), n:wp.length};
    }
  }
  /* ★차 뒤에 있는 웨이포인트는 버린다(u_5033).
     경로 첫 점이 뒤에 있으면 차가 그 자리에서 유턴한다 — 불법이고, 사람이
     운전하는 방식도 아니다. 진행방향 기준으로 이미 지난 점은 건너뛰고
     '앞에 있는 첫 점'부터 따라간다. */
  auto.wp=wp;
  /* ★차 뒤의 '첫 몇 점'만 건너뛴다(u_5033, u_5035 수정).
     목적지가 뒤에 있으면 모든 점이 뒤로 판정돼 st 가 끝까지 가버렸다 →
     경로가 마지막 한 점만 남아 차가 아무것도 안 했다(오너: "목적지 설정하면
     아무것도 안 되"). 유턴을 막으려다 경로를 통째로 없앤 것이다.
     뒤에 있는 건 '출발 직후 몇 점'일 뿐이므로 상한을 둔다. 목적지 자체가
     뒤라면 그건 건너뛸 게 아니라 정상적으로 돌아서 가야 하는 경로다. */
  {
    const fx=Math.cos(me.ang), fy=Math.sin(me.ang);
    const CAP=Math.min(3, Math.max(0, wp.length-2));   // 최대 3점까지만
    let st=0;
    while(st<CAP && ((wp[st].x-me.x)*fx + (wp[st].y-me.y)*fy) < 0) st++;
    auto.i=st;
  }
  try{ if(window.__pushDbg) window.__npDbg2 = window.__pushDbg(); }catch(e){}
  /* ★u_5190 진단: 교사 목표(laneOffset)는 8.12m 로 맞는데 차는 12~15m 를 달린다.
     GEOM 이 쫓는 건 auto.wp 이므로, wp 가 실제로 어느 차로에 놓였는지 본다. */
  try{
    /* ★u_5190/5191: 경로선 여러 점의 차로 위치를 훑는다.
       차는 경로선을 0.26m 오차로 잘 따라가는데 목표 차로와는 5.85m 차이다 —
       경로선 자체가 차로를 넘나든다는 뜻("직진 도로에서 4개 차로 유턴"). */
    const lanes=[];
    for(let k=10;k<Math.min(400, wp.length);k+=10){
      const q=wp[k], n=nearestSeg(q.x, q.y);
      if(!n || !n.s) continue;
      const rw=n.s.roadW/S;
      const lat=(-(n.px-q.x)*Math.sin(n.s.ang) + (n.py-q.y)*Math.cos(n.s.ang))/S;
      lanes.push(+((rw/2+lat)/3.25).toFixed(2));
      // ★어느 도로로 판정됐는지도 같이 본다 — 경로점마다 다른 도로를 잡으면
      //   같은 직진 구간인데 차로 번호가 튄다.
      if(!window.__wpSeg) window.__wpSeg=[];
      if(window.__wpSeg.length<12) window.__wpSeg.push((n.s.n||'?')+'/'+(n.s.l||0)+'차로');
    }
    if(lanes.length){
      let jump=0;
      for(let k=1;k<lanes.length;k++) if(Math.abs(lanes[k]-lanes[k-1])>1.0) jump++;
      window.__wpLane = {n:lanes.length, min:Math.min(...lanes), max:Math.max(...lanes),
                         jumps:jump, head:lanes.slice(0,12)};
    }
  }catch(e){}
  /* ★같은 자리에 겹친 웨이포인트를 제거한다(u_5039 실사고).
     전역 그래프는 0.1m 정밀도로 노드를 용접하므로, 아주 짧은 간선이 그대로
     남아 경로에 '거의 같은 점'이 연달아 들어온다. 그러면 두 점으로 만드는
     진행방향 벡터의 길이가 0이 되어(L2<=1) 조향 목표가 정의되지 않는다.
     실측: path_dist 가 계산되지 못해 초기값 40m·172도로 고정되고, auto.i 는
     88에서 멈춘 채 차가 제자리에서 사고만 반복했다(오너: "제자리 사고만 남").
     1m 미만으로 붙은 점은 버린다. */
  {
    const out=[wp[0]];
    for(let i=1;i<wp.length;i++){
      const p=out[out.length-1], q=wp[i];
      if(Math.hypot(q.x-p.x, q.y-p.y) >= 1.0*S) out.push(q);
    }
    if(out.length>=2){
      if(out[out.length-1]!==wp[wp.length-1]) out.push(wp[wp.length-1]);
      wp.length=0; for(const q of out) wp.push(q);
      auto.i=Math.min(auto.i, wp.length-1);
    }
  }
  /* ★u_5185/5187 진단: wpLen=65 에 routeM=8598 → 점 간격 132m.
     정상은 5m(RS) 라 2439점이어야 한다. 132m 간격이면 코너를 표현할 수 없어
     좌회전이 제자리 피턴처럼 보인다. 리샘플이 실제로 도는지 계측한다. */
  try{
    let gaps=[], mx=0;
    for(let i=1;i<wp.length;i++){
      const g=Math.hypot(wp[i].x-wp[i-1].x, wp[i].y-wp[i-1].y)/S;
      gaps.push(g); if(g>mx) mx=g;
    }
    gaps.sort((a,b)=>a-b);
    let bi=-1, bg=0;
    for(let i=1;i<wp.length;i++){
      const g=Math.hypot(wp[i].x-wp[i-1].x, wp[i].y-wp[i-1].y)/S;
      if(g>bg){ bg=g; bi=i; }
    }
    window.__wpDbg = {n:wp.length, med:+(gaps[gaps.length>>1]||0).toFixed(1),
                      max:+mx.toFixed(1), over50:gaps.filter(g=>g>50).length,
                      at:bi, of:wp.length,
                      // 끊긴 지점 앞뒤 좌표(m). 경로가 어디서 튀는지 본다.
                      p0: bi>0?[+(wp[bi-1].x/S).toFixed(0),+(wp[bi-1].y/S).toFixed(0)]:null,
                      p1: bi>0?[+(wp[bi].x/S).toFixed(0),+(wp[bi].y/S).toFixed(0)]:null};
  }catch(e){}
  /* ★경로 설정과 출발을 분리한다(u_5041 오너 지시).
     예전엔 경로를 만들자마자 auto.on=1 로 바로 달렸다. 이제 경로는 화면에
     표시만 하고, '목적지 가기'를 눌러야 출발한다. */
  /* ★25m 후처리 리샘플 제거(u_5057). 오프셋 '뒤'에 돌던 리샘플이라 직선에만
     점을 늘리고 코너(짧은 간선, L<25m → floor(L/25)=0)에는 한 점도 못 더했다.
     이제 위에서 중심선을 5m 간격으로 '먼저' 리샘플한다. */
  auto.goal=wp[wp.length-1];
  auto.cum=null; auto.s=0; auto.k=1;      // 호길이 진행 리셋
  auto.on = !!window.__autoStart;          // 기본 false = 표시만
  sync();
}
/* ★공간 해시 — 전수 비교(O(n^2), 2628대에서 182ms)를 근처만 비교(O(n))로 바꾼다 */
const HG=30*S;                       // 격자 한 칸 30m
let hgrid=new Map();
function hkey(x,y){return ((x/HG)|0)+'|'+((y/HG)|0)}
function rebuildHash(){
  hgrid=new Map();
  for(const o of cars){if(!o.alive)continue;
    const k=hkey(o.x,o.y);let a=hgrid.get(k);if(!a){a=[];hgrid.set(k,a)}a.push(o)}
  for(const o of peds){
    const k=hkey(o.x,o.y);let a=hgrid.get(k);if(!a){a=[];hgrid.set(k,a)}a.push(o)}
  /* ★내 차를 공간해시에 넣는다(u_4924 실측 결함).
     빠져 있어서 다른 차·오토바이·자전거 눈에 내 차가 '존재하지 않았다'.
     내가 가만히 서 있어도 그대로 통과·충돌 → 피할 방법이 없는 사고였다. */
  {const k=hkey(me.x,me.y);let a=hgrid.get(k);if(!a){a=[];hgrid.set(k,a)}a.push(me)}
}
function gap(c,range){
  range=range||40*S;let b=range;
  const ca=Math.cos(c.ang),sa=Math.sin(c.ang);
  const i0=(c.x/HG)|0,j0=(c.y/HG)|0;
  const r=Math.ceil(range/HG);
  for(let i=i0-r;i<=i0+r;i++)for(let j=j0-r;j<=j0+r;j++){
    const arr=hgrid.get(i+'|'+j);if(!arr)continue;
    for(const o of arr){
      if(o===c)continue;
      const dx=o.x-c.x,dy=o.y-c.y;
      const f=dx*ca+dy*sa;
      if(f<=0||f>=b)continue;
      const l=-dx*sa+dy*ca;
      if(Math.abs(l)<LW*.62)b=f;
    }
  }
  return b;
}
/* ═══════════ 추월 (u_5121 오너 지시) ═══════════════════════════════
   오너: "다른 차량 추월은 아직 못하나. 방해하는차도 피해가야하는데."
   기존 driveAuto 는 앞차가 있으면 gp<11m 에서 vmax=0 으로 **서기만** 했다.
   비켜갈 생각 자체가 없어서, 느린 차 뒤에 붙으면 영원히 못 간다.

   판단은 사람이 하는 순서 그대로:
     1) 앞차가 가깝고(22m 이내) 나보다 느린가(0.85배 미만)
     2) 옆 차로가 비었나 — 앞 45m, 뒤 18m 를 본다(뒤를 봐야 추월해오는 차 앞에 안 낀다)
     3) 그 차로가 도로 안인가
   셋 다 맞으면 횡방향 목표를 한 차로 옮긴다. 조향은 Pure Pursuit 가 그대로 한다.
   추월이 끝나면(앞차를 지나치면) 원래 차로로 돌아온다. */
function laneClear(side){
  /* side=+1 오른쪽, -1 왼쪽. 내 진행방향 기준 한 차로 옆을 훑는다. */
  const ca=Math.cos(me.ang), sa=Math.sin(me.ang);
  const ox=-Math.sin(me.ang)*LW*side, oy=Math.cos(me.ang)*LW*side;   // 옆 차로 중심
  const px=me.x+ox, py=me.y+oy;
  const i0=(px/HG)|0, j0=(py/HG)|0, r=Math.ceil((45*S)/HG);
  for(let i=i0-r;i<=i0+r;i++)for(let j=j0-r;j<=j0+r;j++){
    const arr=hgrid.get(i+'|'+j); if(!arr) continue;
    for(const o of arr){
      if(o===me) continue;
      const dx=o.x-px, dy=o.y-py;
      const f=dx*ca+dy*sa;            // 전후 거리
      const l=-dx*sa+dy*ca;           // 횡 거리
      if(Math.abs(l) > LW*0.70) continue;
      if(f < 18*S && f > -45*S) return false;   // 뒤 18m ~ 앞 45m 안에 차가 있으면 불가
    }
  }
  return onRoad(px,py).ok;            // 옆 차로가 도로 안이어야 한다
}
const OT={on:0, side:0, t:0};
function overtakeOffset(dt, gp){
  /* 반환값 = 경로선에서 옆으로 밀 거리(m*S). 0 이면 추월 안 함. */
  if(OT.on){
    OT.t+=dt;
    // 앞이 트이고 충분히 지났으면 복귀
    if(OT.t>1.2 && gap(me) > 30*S) { OT.on=0; OT.side=0; OT.t=0; return 0; }
    if(OT.t>9.0) { OT.on=0; OT.side=0; OT.t=0; return 0; }   // 안전장치
    return -Math.sin(0)*0 + LW*OT.side;
  }
  if(gp > 22*S) return 0;                       // 앞차가 멀면 추월 불필요
  const lead=gapCar(me);
  if(!lead || lead.v >= me.v*0.85) return 0;    // 나보다 느리지 않으면 추월 안 함
  const sg=(nearestSeg(me.x,me.y)||{}).s;
  const lanes = sg ? (sg.o ? (sg.l||1) : Math.max(1,Math.floor((sg.l||2)/2))) : 1;
  if(lanes < 2) return 0;                       // 편도 1차로면 추월 불가(법규)
  for(const side of [-1, 1]){                   // 좌측 우선(추월차로)
    if(laneClear(side)){ OT.on=1; OT.side=side; OT.t=0; return LW*side; }
  }
  return 0;
}
function gapCar(c,range){
  /* gap() 과 같은 규칙으로 '앞차 객체'를 돌려준다(속도 비교용) */
  range=range||40*S; let b=range, best=null;
  const ca=Math.cos(c.ang),sa=Math.sin(c.ang);
  const i0=(c.x/HG)|0,j0=(c.y/HG)|0,r=Math.ceil(range/HG);
  for(let i=i0-r;i<=i0+r;i++)for(let j=j0-r;j<=j0+r;j++){
    const arr=hgrid.get(i+'|'+j);if(!arr)continue;
    for(const o of arr){
      if(o===c)continue;
      const dx=o.x-c.x,dy=o.y-c.y, f=dx*ca+dy*sa;
      if(f<=0||f>=b)continue;
      if(Math.abs(-dx*sa+dy*ca)<LW*.62){ b=f; best=o; }
    }
  }
  return best;
}
const KMH=v=>Math.round(v*3.6);
/* ═══════════ 모델 주행 (a_5085) ═══════════════════════════════════════
   학습된 CNN(bc_final.pt)이 실제로 차를 몬다.

   ★왜 이게 필요했나: 모델 10개와 32GB 학습데이터가 있는데 게임 어디에서도
     모델을 부르지 않았다. 차를 모는 건 기하(driveAuto=Pure Pursuit) 아니면
     규칙(teacher.js)뿐이었다. 모델은 만들어놓고 한 번도 핸들을 잡은 적이 없다.

   ★왜 키보드 주입이 아닌가(drive_infer.py 방식 기각):
     game.js step() 의 키 처리는 `if(!auto.on)` 안에만 있다(실측 game.js:1645).
     즉 경로가 살아있으면 화살표키가 통째로 무시된다 — 정작 보고 싶은
     '경로를 따라 모델이 모는' 경우가 안 된다. 게다가 키는 이산값이라
     steer 가 항상 ±0.85 로 뭉개져 모델의 연속출력을 버린다.

   ★대신 로컬 서버의 /ctl 을 폴링해서 me.steer / me.v 에 직접 넣는다.
     아티팩트(샌드박스)였다면 못 했겠지만 지금은 로컬 페이지라 fetch 가 된다.

   ON/OFF: 화면의 [모델] 버튼, 또는 키보드 M.
   기하 제어(driveAuto)·교사(teacher.js) 는 그대로 살아있다 — 끄면 즉시 복귀. */
/* ★?nomodel=1 이면 모델 주행을 처음부터 잠근다(측정용, 2026-09-15).
   WHY: /ctl 이 on=1 을 보내면 mdlPoll 이 MDL.on 을 켜 버린다. 기하(GEOM) 주행을
     측정하려는 자동 하네스 입장에서는, 추론루프가 떠 있기만 해도 측정이 오염된다
     — 실제로 모델이 steer=0 thr=0 만 내보내 8598m 경로에서 313m 만에 멈췄고,
     사람이 [모델] 버튼을 눌러 끄기 전까지 v=0 이었다(HUD DRV=MODEL 로 확정).
     userOff=true 로 시작하면 mdlPoll 의 `if(d.on && !MDL.userOff)` 가 막아준다.
   사람이 쓰는 기본 동작은 그대로다(파라미터 없으면 종전과 동일). */
addEventListener('error',e=>{window.__jsErr=(e.message||'')+' @'+(e.filename||'').slice(-24)+':'+e.lineno;},true);
addEventListener('unhandledrejection',e=>{window.__jsErr='promise:'+String(e.reason&&e.reason.message||e.reason);},true);
function _autoOff(tag){ (window.__autoOffLog=window.__autoOffLog||[]).push(tag+'@'+Math.round(performance.now())); if(window.__autoOffLog.length>16) window.__autoOffLog.shift(); }
function runBtnEl(){return document.getElementById('qrun')}
const MDL = {on:false, steer:0, thr:0, brake:0, t:0, seq:-1, err:0, rx:0, ms:0,
             userOff: /[?&]nomodel=1/.test(location.search)};
function mdlPoll(dt){
  MDL.t += dt;
  if(MDL.t < 0.05) return;            // 20Hz — 추론루프(≈30~60Hz)보다 촘촘할 필요 없다
  MDL.t = 0;
  /* ★진단 텔레메트리를 같은 폴링에 실어 보낸다(사고 종류별 카운터).
     HUD 글자를 스크린샷에서 읽는 건 금지(오독 사고)라 값 자체를 올려 보낸다.
     새 연결/타이머를 만들지 않으므로 주행 부하에 영향이 없다. */
  let _tq='';
  try{
    _tq='?tel='+encodeURIComponent(JSON.stringify({
      crk: window.__crk||{}, cr: me.crashes|0,
      lde: (window.__lde||[]).slice(-12),      // a_5111 T1: 차로이탈 기하 기록
      /* ★GO_NOT_ENGAGED 추적(u_5126). 버튼은 auto.wp.length 로 막히는데
         디코더는 wp_len=234 를 보여준다 — 둘이 다르면 경로가 지워진 것이다. */
      wpLen: auto.wp.length, autoOn: auto.on|0, parked: window.__parked|0,
      /* 경로 총길이(m)와 지금까지 간 거리 — 진행률만으로는 '얼마나 먼 길인가'를 모른다 */
      routeM: (auto.cum&&auto.cum.length)? Math.round(auto.cum[auto.cum.length-1]/S) : 0,
      doneM: Math.round((auto.s||0)/S),
      /* ★누가 모는지를 계측으로 노출한다(u_5129). 화면 글자를 눈으로 읽지 않는다. */
      mdlOn: MDL.on?1:0, mdlUserOff: MDL.userOff?1:0, drv: (MDL.on?'MODEL':(auto.on&&auto.wp.length?'GEOM':'TEACH')),
      /* ★DAgger 라벨원(u_5139). 모델이 모는 동안 교사가 계산한 '정답'을 그대로 노출한다.
         모델이 실제로 가는 상황(차선 벗어남·사고 직전)의 정답이 있어야 DAgger 가 성립한다.
         기존 dagger_run.py 는 라벨을 아예 저장하지 않아 쓸모없는 프레임만 쌓았다. */
      tch: (function(){ const T=window.__teach, a=T&&T.last;
        const g=T&&T.dbg;
        return a ? {st:+(+a.steer).toFixed(4), th:+(+a.thr).toFixed(4),
                    br:+(+(a.brake||0)).toFixed(4), ok:1,
                    // ★u_5171: 조향 89% 포화. 어느 항이 범인인지 보려면 항별로 봐야 한다.
                    d:g?+(+g.d).toFixed(3):null, x:g?+(+g.x).toFixed(3):null,
                    ct:g?+(+g.cross).toFixed(2):null,
                    // ★u_5171: onroad=1 인데 cross 가 25m 나온다(왕복8차로보다 넓다).
                    //   기준 세그먼트가 프레임마다 바뀌는지 본다 — 교차로에서 목표가
                    //   튀면 cross 는 '다른 도로 기준' 거리가 되어 의미가 없어진다.
                    g2:(window.__teach&&window.__teach.dbg2)||null,
                    // ★u_5171: 사고의 77%가 도로 경계 이탈(건물27%·인도25%·도로12%·차로13%).
                    //   교사는 lane_off(차로 중심에서 벗어난 양)를 이미 계산하는데
                    //   저장이 안 돼 학습에 한 번도 쓰인 적이 없다. 보조목표로 쓴다.
                    lo:(a.lane_off===undefined?null:+(+a.lane_off).toFixed(3)),
                    // ★u_5171: 좌/우 여유(m). 방향 없는 lane_off 만으로는
                    //   '어디로 피하나'를 배울 수 없었다(v14 건물충돌 96건).
                    fl:(a.free_l===undefined?null:+(+a.free_l).toFixed(2)),
                    fr:(a.free_r===undefined?null:+(+a.free_r).toFixed(2))} : {ok:0}; })(),
      car: {v:+me.v.toFixed(3), x:+(me.x/S).toFixed(2), y:+(me.y/S).toFixed(2),
            ang:+me.ang.toFixed(4), onroad: onRoad(me.x,me.y).ok?1:0},
      bldDbg: window.__bldDbg||null,
      wpDbg: window.__wpDbg||null,
      wpLane: window.__wpLane||null,
      wpSeg: window.__wpSeg||null,
      ppXt: (window.__ppXt===undefined?null:window.__ppXt),
      planDbg: window.__planDbg||null,
      npDbg: window.__npDbg||null,
      npDbg2: window.__npDbg2||null,
      wpTrunc: window.__wpTrunc||null,
      offDbg: window.__offDbg||null,
      qrunRect: (function(){var b=runBtnEl();if(!b)return null;var r=b.getBoundingClientRect();
        return {l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height),
                cx:Math.round(r.left+r.width/2),cy:Math.round(r.top+r.height/2),
                sy:Math.round(r.top+r.height/2)+(window.screenY||0)+(outerHeight-innerHeight)};})(),
      scrY: window.screenY, outH: outerHeight, innH: innerHeight,
      jsErr: window.__jsErr||'', loopErrN: window.__loopErrN|0,
      now: Math.round(performance.now()), daCnt: window.__daCnt|0,
      runHit: window.__runHit|0, runRet: window.__runRet||'', mdlOn: MDL.on?1:0,
      /* ★추월 상태를 계측에 노출한다(u_5123). 교사가 실제로 추월을 시연하는지
         화면 추측이 아니라 숫자로 확인해야 한다. ot.on=1 인 구간이 곧 학습 라벨이다. */
      ot: (window.__teach && window.__teach.ot) || null,
      otN: window.__otN || 0,                  // 누적 추월 횟수
      v: +me.v.toFixed(2), prog: +((auto.cum&&auto.cum.length? (auto.s||0)/(auto.cum[auto.cum.length-1]||1) : 0)).toFixed(4),
      drv: MDL.on?'MODEL':(auto.on&&auto.wp.length?'GEOM':'TEACH'),
      st:+MDL.steer.toFixed(3), thr:+MDL.thr.toFixed(3), brk:+MDL.brake.toFixed(3),
      onroad: (typeof onRoad==='function'? (onRoad(me.x,me.y).ok?1:0) : -1),
      camz: +(cam.z||0).toFixed(4), S: (typeof S!=='undefined'? S : -1)
    }));
  }catch(e){ _tq='?tel='+encodeURIComponent(JSON.stringify({err:String(e&&e.message||e)})); }
  fetch('/ctl'+_tq, {cache:'no-store'}).then(r=>r.json()).then(d=>{
    if(d.seq !== MDL.seq){ MDL.seq = d.seq; MDL.rx++;
      MDL.rxT = performance.now(); }   // ★u_5172: 명령 수신 시각(만료 판정용)
    MDL.steer = +d.steer||0; MDL.thr = +d.thr||0; MDL.brake = +d.brake||0;
    /* on 은 페이지 버튼이 주도권을 갖는다. 파이썬이 on=1 을 보내면 켜지지만,
       사람이 화면에서 끄면 그게 이긴다(안전: 폭주하면 손으로 끌 수 있어야 한다). */
    /* ★force=1 이면 사람이 꺼둔 것도 무시하고 켠다(u_5133).
       userOff 는 '폭주하면 손으로 끌 수 있어야 한다'는 안전장치인데,
       자동 학습 루프에서는 그게 한 번 켜지면 모델이 영영 안 돌아온다.
       실측: userOff=1 로 굳어서 /ctl on=1 을 보내도 drv=GEOM 유지.
       학습 하네스가 명시적으로 force 를 보낼 때만 해제한다. */
    if(d.force){ MDL.userOff = false; }
    /* ★교사 모드를 원격으로 바꾼다(u_5144 커리큘럼 수집).
       좌회전·정지·추월 라벨은 교사에게 '그 상황을 하라'고 시켜야 생긴다.
       그냥 달리면 실측상 좌회전 108 / 우회전 10,142 로 94배 쏠린다. */
    if(d.teach && window.__teach && window.__teach.setMode){
      try{ if(window.__teach.mode!==d.teach) window.__teach.setMode(d.teach); }catch(e){}
    }
    if(d.on && !MDL.userOff) MDL.on = true;
    /* ★하네스가 명시적으로 놓아줄 수 있어야 한다(a_5170).
       끄는 건 사람만' 규칙은 폭주 방지용인데, 그 탓에 GEOM 기준선을 재려고
       on=0 을 보내도 drv=MODEL 로 굳어 3 에피소드가 통째로 무효가 됐다.
       release=1 은 학습 하네스만 보내는 명시적 해제 신호다(사람 버튼과 무관). */
    if(d.release){ MDL.on = false; MDL.userOff = false; }
    /* ★force 는 '켜기'에만 쓴다(u_5133 실사고).
       model_drive.py 가 매 프레임 force:1 을 보내는데, 여기서 on 이 falsy 한
       프레임 하나만 섞여도 모델이 꺼져버렸다 — 실측: 출발 누르면 drv=TEACH 로 추락.
       끄는 건 사람(버튼·M키)만 한다. 자동 루프가 자기 모드를 끄면 학습이 끊긴다. */
    /* ★rst 카운터가 바뀌면 소프트리셋 1회(u_5126). 리로드 없이 에피소드만 새로 시작. */
    if(typeof d.rst==='number'){
      if(MDL.rst===undefined) MDL.rst = d.rst;              // 첫 폴링은 기준만 잡는다
      else if(d.rst !== MDL.rst){ MDL.rst = d.rst;
        try{ window.__softReset && window.__softReset(); }catch(e){} }
    }
  }).catch(e=>{ MDL.err++; });
}
/* 모델 출력 → 차. teacher.js T.drive 와 같은 물리 규약을 쓴다(일관성). */
function driveModel(dt){
  /* ★u_5172 오너 질문 "지금 뭐로 운행중이지 / 왜 이동하는거야" 에서 드러난 결함.
     추론 프로세스가 죽어도 MDL.thr 이 그대로 남아 차가 계속 달렸다.
     실측: 조향/스로틀/제동이 6초간 +0.010/0.614/0.149 로 고정인 채
     981m → 1011m 이동. 아무도 운전하지 않는데 가속이 유지된다.
     실차라면 치명적이고, 측정도 오염된다(모델 평가인 줄 알았던 주행이
     사실은 굳은 명령의 관성일 수 있다).
     ⇒ 0.5초 이상 새 명령이 없으면 입력을 버리고 서서히 멈춘다. */
  const _age = MDL.rxT ? (performance.now() - MDL.rxT) : 1e9;
  if(_age > 500){
    me.v -= 3.0*dt; if(me.v < 0) me.v = 0;     // 타력주행으로 감속
    me.steer = 0;                               // 조향도 중립으로
    window.__mdl = {st:0, thr:0, brk:0, rx:MDL.rx, err:MDL.err, stale:1};
    return;
  }
  me.steer = Math.max(-0.9, Math.min(0.9, MDL.steer));
  /* ★브레이크는 '절대 임계'가 아니라 '스로틀과의 비교'로 판단한다(u_5101 실사고).
     실측: 모델이 thr=0.96 과 brk=0.84 를 동시에 냈고, brk>0.5 하드 게이트가
     이겨서 차가 영원히 서 있었다(화면 DRV=MODEL v=0).
     학습 라벨에서는 thr>0.5 와 brk>0.5 가 동시에 나오는 경우가 **0.00%** 다
     (brk>0.5 자체가 0.49%). 즉 둘이 같이 큰 건 모델이 학습 분포 밖에서
     두 헤드를 동시에 밀어올린 것이지, '세워라'라는 뜻이 아니다.
     → 더 강하게 요구하는 쪽을 따른다. 진짜 정지 의도(brk 우세)는 그대로 선다. */
  if(MDL.brake > 0.5 && MDL.brake > MDL.thr + 0.1){ me.v -= 9.0*dt; if(me.v < 0) me.v = 0; }
  else { const cap = (window.__TARGET_KMH || 45)/3.6 * 1.12;
         me.v += (Math.max(0,MDL.thr)*cap - me.v)*Math.min(1, dt*1.8); }
  window.__mdl = {st:me.steer, thr:MDL.thr, brk:MDL.brake, rx:MDL.rx, err:MDL.err, stale:0};
}
function setModel(on){
  MDL.on = !!on; MDL.userOff = !on;
  if(!MDL.on) window.__brkT = 0;
  const b = document.getElementById('mdlBtn');
  if(b){ b.classList.toggle('on', MDL.on); b.textContent = MDL.on ? '모델 ON' : '모델'; }
  /* ★모델 주행 중에는 경로 패널을 숨긴다(ar_5106 실측 근거).
     #nav 패널은 학습 프레임에 단 한 장도 없는데 실시간 화면에서는 상단을 덮는다.
     패널 영역 밝기: 학습 평균 0.546(0.85 초과 0%) vs 실시간 0.916(100%).
     실시간 최솟값 0.870 > 학습 최댓값 — 분포가 겹치지 않는다(완전한 OOD).
     그래서 실시간 조향 상관이 0.011(잡음)까지 떨어졌다.
     ★자르는 건 해법이 아니다: 전처리에서 상단을 크롭하면 학습 프레임의 기하까지
       바뀌어 스로틀이 0.808 -> 0.381~0.470 으로 무너진다.
       실시간 화면을 학습 때와 같게 만드는 것이 맞다 — 패널을 없앤다.
     실측: 패널만 가리면 조향 -0.066 -> +0.298 로 학습값에 붙는다. */
  const nav = document.getElementById('nav');
  if(nav) nav.style.visibility = MDL.on ? 'hidden' : '';
  if(typeof flash==='function') flash(MDL.on ? '모델 주행 ON' : '모델 주행 OFF');
  return MDL.on;
}
window.__setModel = setModel;
addEventListener('keydown', e=>{ if(e.key==='m'||e.key==='M') setModel(!MDL.on); });

/* ★진행률 추적을 주행제어에서 분리한다(a_5170 실사고).
   기존엔 호길이 테이블(auto.cum) 생성과 s 갱신이 driveAuto() 안에만 있었다.
   그런데 모델이 몰면 driveAuto 는 호출되지 않는다 — 그래서 auto.cum 이 영원히
   null 이고 /tel 의 prog 가 항상 정확히 0 이었다. 실측: 모델 주행 60초 2회에서
   prog 0.0000 고정(차는 실제로 움직였고 사고도 났다).
   ⇒ '얼마나 갔는가'는 '누가 모는가'와 무관한 측정이므로 밖으로 뺀다. */
function trackProgress(){
  const W=auto.wp, N=W.length;
  if(N<2) return;
  if(!auto.cum || auto.cum.length!==N){
    auto.cum=new Float64Array(N); auto.cum[0]=0;
    for(let k=1;k<N;k++) auto.cum[k]=auto.cum[k-1]+Math.hypot(W[k].x-W[k-1].x,W[k].y-W[k-1].y);
    auto.s=0; auto.k=1;
  }
  let bs=auto.s, bd=1e18, bk=auto.k||1;
  const lo=auto.s-20*S, hi=auto.s+250*S;
  for(let k=1;k<N;k++){
    if(auto.cum[k]<lo) continue;
    if(auto.cum[k-1]>hi) break;
    const a=W[k-1], b=W[k];
    const vx=b.x-a.x, vy=b.y-a.y, L2=vx*vx+vy*vy;
    const u=L2>1e-6 ? Math.max(0,Math.min(1,((me.x-a.x)*vx+(me.y-a.y)*vy)/L2)) : 0;
    const px=a.x+vx*u, py=a.y+vy*u;
    let ph=((Math.atan2(vy,vx) - me.ang + Math.PI*3)%(Math.PI*2))-Math.PI;
    if(L2>1e-6 && Math.abs(ph) > 75*Math.PI/180) continue;
    const dd=(px-me.x)**2+(py-me.y)**2;
    if(dd<bd){ bd=dd; bs=auto.cum[k-1]+Math.sqrt(L2)*u; bk=k; }
  }
  if(bs > auto.s-3*S) auto.s=Math.max(auto.s, Math.min(bs, auto.s+60*S));
  auto.k=bk; auto.i=Math.min(N-1,bk); auto.xt=Math.sqrt(bd)/S;
}
function driveAuto(dt){
  window.__daCnt=(window.__daCnt||0)+1;
  if(auto.on) window.__parked=0;   // 주행 중엔 주차 플래그가 남아있으면 안 된다
  if(!auto.wp.length){auto.act='대기';return}
  /* ★★ 호길이 기반 Pure Pursuit (u_5049, fable 재설계).
     docs/driving_unsolved.md 의 실패 6건은 전부 '어느 웨이포인트를 목표로 삼나'를
     고르는 문제였다 — 가까우면/지나치면/최근접/순서대로. 코너에서는 어떤 규칙도
     틀린다: 모퉁이 너머 점이 더 가깝고, 7m 안에는 못 들어오고, 세그먼트 방향은
     90도씩 점프해서 조향이 포화·진동한다(실측 307→14→67→29→62→32도).
     여기서는 웨이포인트 인덱스를 아예 고르지 않는다.
       · 진행 = 경로 위 호길이 s(스칼라). 뒤로 갈 수 없다(단조증가).
       · 목표 = s 에서 Ld 만큼 앞의 '경로 위 보간점'. 연속적으로 움직인다.
       · 조향 = pure pursuit: δ = atan(2·L·sinα / Ld). 세그먼트 점프가 없다.
       · 속도 = 앞 25m 의 곡률로 미리 감속. 코너를 직선 속도로 들어가지 않는다. */
  const W=auto.wp, N=W.length;
  trackProgress();                               // 호길이 테이블 생성도 여기서 한다
  const total=auto.cum[N-1];
  const posAt=(sv)=>{                              // 호길이 → 경로 위 점 + 방향
    sv=Math.max(0,Math.min(total,sv));
    let k=Math.max(1, auto.k||1);
    while(k<N-1 && auto.cum[k]<sv) k++;
    while(k>1 && auto.cum[k-1]>sv) k--;
    const a=W[k-1], b=W[k], L=auto.cum[k]-auto.cum[k-1];
    const u=L>1e-6 ? (sv-auto.cum[k-1])/L : 0;
    return {x:a.x+(b.x-a.x)*u, y:a.y+(b.y-a.y)*u, ang:Math.atan2(b.y-a.y,b.x-a.x), k};
  };
  // 2) 도착
  {
    const g=W[N-1], dg=Math.hypot(g.x-me.x,g.y-me.y);
    if(auto.s>=total-10*S && dg<8*S){
      me.v*=.82;auto.act='도착';
      if(me.v<.3){_autoOff('arrive');me.v=0;auto.on=0;flash('목적지 도착');sync()}
      return;
    }
  }
  // 3) 전방 곡률 → 코너 속도
  let vmaxCurve=14;
  {
    const look=25*S, step=5*S;
    let maxK=0;
    for(let sv=auto.s; sv<Math.min(total,auto.s+look); sv+=step){
      const p0=posAt(sv), p1=posAt(sv+step);
      let dth=((p1.ang-p0.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
      const kap=Math.abs(dth)/(step/S);            // rad/m
      if(kap>maxK) maxK=kap;
    }
    if(maxK>1e-4){
      const aLat=2.4;                              // m/s² 허용 횡가속
      vmaxCurve=Math.max(3.5, Math.min(14, Math.sqrt(aLat/maxK)));
    }
    auto.curv=maxK;
  }
  // 4) 전방주시점 + pure pursuit 조향
  const wb=me.hm*0.6;                              // m
  /* ★경로에서 밀려났으면 '복귀 모드'로 전환한다(u_5052).
     실측: s=1130m 지점에서 xt=19.8m 로 밀린 뒤 df=0.93(53도)로 옆을 겨냥한 채
     v=0 정지. Pure Pursuit 는 경로 위에 있을 때를 전제하므로, 크게 벗어나면
     전방주시점이 옆으로 가버려 복귀하지 못한다.
     벗어남이 크면 Ld 를 짧게 잡아 '경로로 곧장 붙는' 각도를 만든다. */
  const off = auto.xt||0;                          // m
  const Ld = off > 6
    ? Math.max(4, Math.min(8, 4 + 0.3*me.v))       // 복귀: 짧게 → 급히 붙는다
    : Math.max(6, Math.min(16, 0.9*me.v));         // 정상: 속도비례
  /* ★gp/otOff 는 여기서 계산한다(u_5126 실사고 수정).
     추월 오프셋을 쓰는 조향 코드가 선언보다 42줄 위에 삽입돼 있어서
     `const otOff` 의 TDZ(temporal dead zone)에 걸렸다 — driveAuto 가 매 프레임
     "Cannot access 'otOff' before initialization" 을 던졌고, loop() 이 그대로
     터져 requestAnimationFrame 재등록이 안 돼 게임이 통째로 멈췄다
     (실측: [목적지 가기] 직후 performance.now() 6197ms 고정, daCnt=0, v=0).
     그래서 autoOn=1 인데 차가 1cm 도 못 움직였다. */
  const gp=gap(me);
  /* ★추월은 driveAuto 에 두지 않는다(u_5138 오너 지적).
     driveAuto 는 '수식 주행'이고, 여기에 기능을 넣으면 모델이 아니라 루틴이 잘 가게 된다.
     추월 판단은 teacher.js 에만 있다 — 교사가 시연하고, 그게 라벨이 되고, 모델이 배운다.
     (모델 주행 중에는 driveAuto 자체가 호출되지 않으므로 여기 코드는 학습과 무관하다.) */
  const otOff = 0;
  const P=posAt(auto.s + Ld*S);
  if(otOff){                                   // 추월 중이면 목표를 옆 차로로 민다
    P.x += -Math.sin(me.ang)*otOff;
    P.y +=  Math.cos(me.ang)*otOff;
  }
  let alpha=((Math.atan2(P.y-me.y,P.x-me.x)-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
  const Lreal=Math.max(3, Math.hypot(P.x-me.x,P.y-me.y)/S);
  let delta=Math.atan2(2*wb*Math.sin(alpha), Lreal);   // rad
  /* ★u_5190 실사고: 경로선은 3차로 중앙(8.13m)에 정확히 놓였고 교사도 그걸
     목표로 잡는데(7.28m), 차는 12.17m 를 달렸다 — 4.89m 밖.
     원인은 이 Pure Pursuit 가 목표점을 auto.s(경로 진행도) 기준으로만 잡는다는 것.
     차가 옆으로 밀려도 '경로를 따라 얼마나 왔나'만 보므로 횡오차가 조향에
     들어가지 않는다. 그래서 한 번 밀리면 나란히 달릴 뿐 복귀하지 않는다
     (실측: 교사는 복귀력 0.372 를 계산하는데 실제 조향은 0.010).
     ⇒ Stanley 의 횡오차 항을 더한다. 경로선 기준 부호거리를 재서
       속도로 나눈다(고속에서 과민해지지 않게). */
  /* ★posAt(auto.s) 는 '경로를 따라 s 만큼 온 점'이라 차 위치와 같게 나온다
     (실측 xt=0). 경로선 대비 실제 횡오차는 웨이포인트 선분에 직접 투영해야 한다. */
  try{
    let bi=-1, bd=1e18, bx=0, by=0, ba=0;
    const i0=Math.max(0, auto.i-3), i1=Math.min(auto.wp.length-1, auto.i+6);
    for(let i=i0;i<i1;i++){
      const A=auto.wp[i], B=auto.wp[i+1];
      const vx=B.x-A.x, vy=B.y-A.y, L2=vx*vx+vy*vy;
      if(L2<1e-6) continue;
      let t=((me.x-A.x)*vx+(me.y-A.y)*vy)/L2; t=Math.max(0,Math.min(1,t));
      const cx=A.x+vx*t, cy=A.y+vy*t;
      const d2=(cx-me.x)**2+(cy-me.y)**2;
      if(d2<bd){ bd=d2; bi=i; bx=cx; by=cy; ba=Math.atan2(vy,vx); }
    }
    if(bi>=0){
      const xt=(-(bx-me.x)*Math.sin(ba) + (by-me.y)*Math.cos(ba))/S;   // m, 부호
      const k=1.2, spd=Math.max(3, me.v);
      delta += Math.max(-0.35, Math.min(0.35, Math.atan2(k*xt, spd)));
      window.__ppXt = +xt.toFixed(2);
    }
  }catch(e){}
  const maxSteer=.62;
  me.steer=Math.max(-.9,Math.min(.9, delta/maxSteer));
  // 5) 속도
  /* ★보행자 제동을 경로주행에도 넣는다(ar_5057 지적).
     워커가 teacher.js 에 넣었지만, 내비 주행 중 실제로 모는 건 driveAuto 다.
     보행자 사고가 crashHold 연쇄의 시작점이었으므로 여기서 막는 게 근본이다.
     ★규칙은 pedBrakeDist() 하나로 통일했다(교사와 공용) — 예전엔 여기에 손으로
     복사한 사본이 있었고 교사본과 달라서, 내비 주행 중 두 제어기가 매 프레임
     다른 판단을 냈다. 사본을 없애야 그 갈라짐이 다시 안 생긴다. */
  const pedD=pedBrakeDist();
  let vmax=vmaxCurve;
  if(pedD<PED_STOP_M) vmax=0;
  else if(pedD<PED_SLOW_M) vmax=Math.min(vmax, 3.5);
  if(off>6) vmax=Math.max(vmax, 4.5);              // 복귀 중엔 최소한의 추진력 유지
  if(Math.abs(alpha)>0.6) vmax=Math.min(vmax,5);   // 크게 틀어야 하면 감속
  /* ★정차 교착 해제(u_5050).
     gap() 은 거리만 본다. 앞차가 '서 있으면' gap<11m 이 영원히 유지돼 vmax=0 으로
     굳는다. 그 앞차도 막혀 있어서 안 비킨다 — 실측: 경로·조향 정상인데 v=0.1 로
     70초 내내 제자리(사고 3회 후 NPC 줄에 갇힘).
     사람은 이럴 때 아주 천천히 비집고 나간다. 5초 넘게 못 움직이면 서행을 허용한다. */
  /* ★교착 판정은 '앞이 막혔나'가 아니라 '실제로 못 가고 있나'로 한다(u_5052).
     gap<28m 조건을 달았더니, 옆·뒤에 끼여 갇힌 경우 gap 은 비어 보여서 타이머가
     안 돌았다 — 실측: 1.1km 지점에서 추돌 2회 후 v=0 으로 140초 정지.
     경로가 남아 있는데 못 가면 그건 이유가 무엇이든 교착이다. */
  /* ★앞차가 있으면 교착으로 치지 않는다(u_5059 실사고).
     예전엔 '못 가고 있으면 무조건 교착'이라 앞차 뒤에 정상적으로 줄 서 있는
     상황에서도 서행이 발동해, 앞차를 그대로 들이받았다 — 강남→시청 촬영에서
     램프 합류 대기 중 gp=7m 인데 creep 이 2.2m/s 를 강제해 추돌.
     줄 서서 기다리는 건 교착이 아니라 정상 주행이다. */
  const queued = gp < 14*S;                        // 앞차 대기 중
  auto.stall = (auto.on && me.v < 0.8 && !queued && auto.s < total-20*S)
                 ? (auto.stall||0)+dt : 0;
  const creep = auto.stall > 3;
  /* ★추월 판단이 먼저다(u_5121). 비켜갈 수 있으면 서지 않는다.
     otOff/gp 는 조향(4번)에서 이미 쓰므로 그 위에서 계산해 둔다. */
  if(otOff){
    /* 추월 중에는 앞차 정지 규칙을 완화한다 — 옆 차로로 나가는 중이므로
       앞차가 가까워도 멈추면 안 된다. 대신 옆 차로 안전은 laneClear 가 이미 봤다. */
    if(gp<7*S) vmax = Math.min(vmax, 3.0);
  }else{
    if(gp<28*S)vmax=Math.min(vmax,14*(gp-9*S)/(19*S));
    if(gp<11*S)vmax = 0;                             // ★앞차 앞에서는 무조건 정지
  }
  if(creep && !queued){
    vmax=Math.max(vmax,2.2);
    /* 10초 넘게 갇혀 있으면 주변 NPC 를 비켜준다 — 시뮬레이터가 스스로 못 푸는
       교착(사방이 정지차)은 사람이 경적 울리고 기다리는 상황과 다르다. */
    if(auto.stall > 10){
      for(const c of cars){
        if(!c.alive) continue;
        const dx=c.x-me.x, dy=c.y-me.y;
        if(dx*dx+dy*dy < (14*S)*(14*S) && Math.abs(c.v)<0.5) c.alive=false;
      }
      auto.stall=3;                                // 한 번 비운 뒤 다시 지켜본다
    }
  }
  if(auto.s>=total-25*S)vmax=Math.min(vmax,4);
  me.v+=(vmax-me.v)*Math.min(1,dt*2.0);
  auto.act=gp<11*S?'정지 — 전방 장애물':gp<28*S?'감속 — 차간유지'
    :auto.curv>0.05?'선회 중':(auto.s>=total-25*S)?'목적지 접근':'주행 중';
  window.__da={st:me.steer, df:alpha, i:auto.i, n:N,
               d:Lreal, xt:auto.xt||0, s:auto.s/S, tot:total/S, vc:vmaxCurve,
               gp:gp/S, vmax:vmax, stall:auto.stall||0, brk:window.__brkT||0, ped:pedD,
               blk:blockT||0, bst:bldStuck||0, cool:me.cool||0, hold:crashHold||0};
}

/* ---------- 충돌 ---------- */
function obb(a,b){          // 회전 사각형 근사(반지름 + 축투영)
  const dx=b.x-a.x,dy=b.y-a.y;
  const dist=Math.hypot(dx,dy);
  if(dist>(a.h+b.h))return false;
  const c=Math.cos(a.ang),s=Math.sin(a.ang);
  const f=Math.abs(dx*c+dy*s),l=Math.abs(-dx*s+dy*c);
  return f<(a.h+b.h)*.46 && l<(a.w+b.w)*.5;
}
/* ★순간이동 뒤에는 교사 차로 상태를 반드시 버린다 (2026-09-15).
   T.laneF(현재 차로 실수값)와 T.laneSet(목표 차로 지정 여부)은 한 번 정해지면
   다시 지워지지 않았다. 그래서 차가 4차로 도로에서 2차로 도로로 순간이동하면
   옛 laneF(예: 3)가 그대로 남고, teacher.js 의 clamp 가 그걸 0.02/프레임으로
   되돌린다 — 한 차로를 넘기는 데 2.5초다. 그 2.5초 동안
     laneMoving = true  → lookahead 14m → 30m,
                          cross-track 이득 1.6 → 0.5
   즉 '차선변경 중 이득'으로 달린다. 차선변경은 하지도 않는데.
   스폰 직후·사고 복귀 직후가 정확히 그 구간이었다.
   지우면 laneTarget() 의 첫 프레임 로직이 '차가 지금 실제로 있는 차로'로
   다시 추정한다(teacher.js 56~68행) — 그게 옳은 초기값이다.
   ★teacher.js 보다 먼저 도는 경로(hardReset 등)가 있으므로 __teach 부재는 무시한다. */
function resetTeacherLane(){
  const T=window.__teach; if(!T) return;
  T.laneF=undefined;        // 현재 차로 추정을 다음 프레임에 새로 한다
  T.laneSet=false;          // 옛 도로에서 지시된 목표 차로를 버린다
  T.laneMoving=false;       // 변경중 이득(lookahead 30m / xt 0.5)을 끈다
}
function respawnOnRoad(){
  /* ★사고 후 도로 복귀. 단순히 제자리에 세우면 같은 건물로 다시 직진해
     무한 충돌한다(실측: 같은 건물에 34회). 그래서:
       - 차로 중앙에 세우고
       - 진행방향을 '도로를 따라' 맞추되
       - 방금 박은 쪽 반대로 조금 물러나 재출발시킨다. */
  const n=nearestSeg(me.x,me.y);
  if(!n)return;
  const sg=n.s;
  /* ★복귀 방향은 '가던 방향'을 유지한다(u_5037 실사고).
     예전엔 me.ang=sg.ang 로 세그먼트의 저장 방향을 그대로 썼다. 양방향 도로에서
     저장 방향은 임의라, 절반의 확률로 차가 뒤를 보고 되살아난다. 그러면 목적지
     반대로 달리다 즉시 차로를 벗어나고, 또 사고나고, 또 복귀한다 —
     실측(20초): 속도가 12.6→0.1→12.6→0.2 로 반복되고 진행률이 0.034 를
     한 번도 못 넘겼다(5/15회 뒤로 감). 오너가 본 '경로가 자꾸 바뀌고 차와
     연동이 안 된다'가 이것이다.
     일방통행이면 통행 방향이 정답이고, 양방향이면 내 진행방향에 가까운 쪽이다. */
  let dir=1;
  {
    const d=((me.ang - sg.ang + Math.PI*3) % (Math.PI*2)) - Math.PI;
    dir = Math.abs(d) < Math.PI/2 ? 1 : -1;
    if(sg.o) dir = 1;                       // 일방통행은 a→b 만
  }
  const off=laneOffset(sg,dir,0);
  // 세그먼트를 따라(진행방향 기준) 조금 뒤로 물린 지점
  const back=Math.min(0.35,(8*S)/Math.max(1,sg.len));
  const t2=Math.max(0,Math.min(1, dir>0 ? n.t-back : n.t+back));
  const A=nodes[sg.a],B=nodes[sg.b];
  const px=A.x+(B.x-A.x)*t2, py=A.y+(B.y-A.y)*t2;
  const ang = sg.ang + (dir<0 ? Math.PI : 0);
  me.x=px-Math.sin(ang)*Math.abs(off);
  me.y=py+Math.cos(ang)*Math.abs(off);
  me.ang=ang;me.v=0;me.offroad=0;me.cool=1.0;
  resetTeacherLane();      // 다른 차로수의 도로로 옮겨갔을 수 있다(PART B)
}
function crash(label,heavy){
  if(me.cool>0)return;
  me.cool=.8;me.crashes++;
  /* ★무엇에 부딪히는지 종류별로 센다(u_5025 진단용).
     'cr=8' 만 봐서는 원인을 모른다 — 추돌인지 보행자인지 차로이탈인지에 따라
     고칠 곳이 완전히 다르다. */
  { const k=label.indexOf('추돌')>=0?'추돌'
          : label.indexOf('보행자')>=0?'보행자'
          : label.indexOf('중앙선')>=0?'중앙선'      // ★F2 분리 측정(u_5061)
          : label.indexOf('차로')>=0?'차로이탈'
          : label.indexOf('충돌')>=0?'건물'
          /* ★'도로 이탈'·'인도 침범'(game.js:1948)이 어느 갈래에도 안 걸려
             전부 '기타'로 뭉쳤다(실측: 사고 12건 전부 기타). 원인을 못 가린다. */
          /* ★셋을 갈라서 센다(u_5169 오너 지적).
             오너: "차로 이탈은 중앙선과 인도로 넘어가지 않는 차선변경이겠지" — 맞다.
             그런데 지금 코드는 성격이 다른 셋을 '차로이탈' 하나로 뭉쳐 세고 있었다:
               인도 침범 = 차도 벗어나 인도 쪽 (경계 초과 <= 인도폭 2.5m)
               도로 이탈 = 그보다 더 멀리 (인도까지 넘어감)
               중앙선   = 반대 차로 (이미 별도 항목)
             법규상 무게도 다르고 고칠 지점도 다르다. 분리해야 원인이 보인다. */
          : label.indexOf('인도')>=0?'인도침범'
          : label.indexOf('도로')>=0?'도로이탈':'기타';
    window.__crk=window.__crk||{}; window.__crk[k]=(window.__crk[k]||0)+1;
    /* ★a_5111 T1: 차로이탈이 '어떤 도로에서' 나는지 기하를 통째로 남긴다.
       roadW/차로수/일방여부/실제 횡오차/주행선 오프셋을 같이 찍어야
       좁은길·일방오독·게인 중 무엇인지 구분된다. 추정 금지, 측정. */
    try{
      const ns=nearestSeg(me.x,me.y);
      if(ns&&ns.s){
        const sg=ns.s, lanes=sg.l||2;
        /* ★여기에 planTo laneOff 의 '옛날 식'이 복사돼 남아 있었다(u_5137).
           본체는 이미 일방=0.5*LW 로 고쳤는데 이 계측 코드만 구식이라,
           rOff 가 -3.25/-6.50 으로 찍혀 '경로가 반대차로를 노린다'고 오독했다.
           오늘만 네 번째 '한쪽만 고친 복사본' 이다. 같은 식을 쓴다. */
        const rOff=0.5*LW;                                  // planTo laneOff 와 동일식
        (window.__lde=window.__lde||[]).push({
          k:k, n:sg.n||'', l:lanes, o:sg.o?1:0,
          roadW:+(sg.roadW/S).toFixed(2),
          xt:+(ns.d/S).toFixed(2),                 // 실제 중심선 횡거리
          margin:+((sg.roadW*.5)/S).toFixed(2),    // 이탈 임계
          rOff:+(rOff/S).toFixed(2),               // 주행선이 노린 오프셋
          v:+me.v.toFixed(2), i:(auto.i|0)});
      }
    }catch(e){}
  }
  me.dmg=Math.min(100,me.dmg+(heavy?22:14));
  me.v*=-.25;
  const el=document.getElementById('crash');
  /* ★사고 = 화면 전체를 붉게 '정지'시킨다(u_4918 오너 지시).
     140ms 번쩍임은 판별이 어려웠다 → 깜빡임 없이 꽉 찬 빨강으로 고정.
     학습모드면 그 상태로 잠깐 멈췄다가 처음부터 다시 시작한다. */
  if(el){el.style.opacity=.92;}
  crashLit=1.2;
  crashHold=1;
  if(LEARN){
    me.v=0;
    setTimeout(()=>{
      if(el)el.style.opacity=0;
      crashHold=0; crashLit=0;
      hardReset(); epStart();
    }, 600);
  }else{
    /* ★2026-09-14 검증 중 발견: 학습모드가 아니면 사고 후 리셋이 없어서,
       모델 검증 때 한 번 박으면 차가 그 자리에 영원히 멈춰 있었다
       (실측: 26초간 화면 diff 0.0, 화면에 차도 안 보임).
       검증에서도 사고가 나면 처음부터 다시 시작해야 계속 볼 수 있다. */
    setTimeout(()=>{
      if(el)el.style.opacity=0;
      crashHold=0; crashLit=0;
      /* ★목적지 안내 중이면 처음으로 되돌리지 않는다(u_5024 P2).
         hardReset() 은 차를 출발지로 순간이동시키고 auto.wp 까지 비운다.
         내비게이션 중에 그러면 사고 한 번에 경로가 사라진다 — 사람이 쓰는
         내비는 그렇게 동작하지 않는다. 학습 에피소드일 때만 전체 리셋한다. */
      if(auto.on && auto.wp.length){ respawnOnRoad(); me.v=0; }
      else hardReset();
    }, 600);
  }
  flash('💥 '+label);
  (window.__trace=window.__trace||[]).push('CRASH:'+label+'@'
    +Math.round(Math.hypot(me.x-gangnamXY().x*S,me.y-gangnamXY().y*S)/S)+'m');
  /* ★사고가 나도 목적지는 유지한다(u_5024 P2).
     예전엔 여기서 auto.on=0 으로 경로를 버렸다. 그러면 초반에 한 번만 부딪혀도
     안내가 통째로 사라지고, 차는 길잡이 없이 표류한다 — 화면에서 wp=0·auto=0 으로
     확인했다. 사람도 접촉사고가 났다고 목적지를 잊지는 않는다.
     도로로 복귀시킨 뒤 남은 경로를 계속 따라가게 한다. */
  respawnOnRoad();          // 도로로 복귀시켜 다음 시도를 가능하게
  if(auto.on && auto.wp.length){
    /* ★복귀 시 재조준은 '가까운 앞쪽 몇 점'으로 제한한다(u_5038 실사고).
       예전엔 남은 경로 전체에서 최근접 점을 찾았다. 경로는 되돌아오는 구간이
       있어서(코엑스 경로는 출발지 근처를 다시 지난다), 한참 뒤쪽 점이
       '가장 가깝다'고 잡힌다. 사고 한 번에 인덱스가 88까지 순간이동하고,
       그 점은 반대 방향이라 차가 경로에서 40m·172도 벗어난 채 굳는다 —
       실측에서 매번 wp_idx=88, 방향차 172도로 고정됐다.
       앞으로 20점 안에서만, 그리고 30m 안에 있을 때만 재조준한다. */
    let bi=auto.i, bd=1e18;
    const END=Math.min(auto.wp.length, auto.i+20);
    for(let i=auto.i;i<END;i++){
      const d=(auto.wp[i].x-me.x)**2+(auto.wp[i].y-me.y)**2;
      if(d<bd){bd=d;bi=i}
    }
    if(bd < (30*S)*(30*S)){
      auto.i=bi;
      if(auto.cum && bi<auto.cum.length){ auto.s=auto.cum[bi]; auto.k=Math.max(1,bi); }  // 호길이 창도 함께 이동
    }
    sync();
  }
  sync();
}

/* ---------- 물리 ---------- */
const K={};
function step(dt){
  /* ★사고 정지가 영구히 latch 되지 않게 한다(u_5056).
     crashHold 는 600ms 뒤 setTimeout 이 푼다. 그런데 그 사이에 또 사고가 나면
     타이머가 겹쳐서, 먼저 걸린 타이머가 푼 뒤 나중 것이 다시 세운다. 그러면
     아무도 못 푸는 상태가 된다 — 실측: 보행자 사고 1회 뒤 vmax=14·gp=40·brk=0
     (아무도 제동을 안 거는데) v=0 으로 영구 정지, 진행률 0.161 에서 멈춤.
     2초 이상 지속되면 강제로 푼다. */
  if(crashHold){
    crashHoldT=(crashHoldT||0)+dt;
    if(crashHoldT>2){ crashHold=0; crashLit=0; crashHoldT=0;
      const _el=document.getElementById('crash'); if(_el)_el.style.opacity=0; }
    else { me.v=0; return; }
  } else crashHoldT=0;
  const AC=5.2,BR=9.0,VMAX=17;                    // m/s
  if(!auto.on){
    if(K.ArrowUp)me.v+=AC*dt;
    else if(K.ArrowDown)me.v-=BR*dt;
    else me.v-=Math.sign(me.v)*Math.min(Math.abs(me.v),2.4*dt);
    me.v=Math.max(-5,Math.min(VMAX,me.v));
    me.steer=((K.ArrowLeft?-1:0)+(K.ArrowRight?1:0))*.85;
  }
  const px0=me.x,py0=me.y,pa0=me.ang;   // 벽 충돌시 되돌릴 직전 위치
  // 자전거 모델: 조향각 → 곡률 (속도 낮으면 회전 못함)
  const wheelbase=me.hm*.6;
  const maxSteer=.62;                              // rad
  const sa=me.steer*maxSteer;
  me.ang += (me.v/wheelbase)*Math.tan(sa)*dt;
  me.x += Math.cos(me.ang)*me.v*S*dt;
  me.y += Math.sin(me.ang)*me.v*S*dt;
  if(me.cool>0)me.cool-=dt;

  // ★건물(벽) 충돌 — 통과 불가. 이전 위치로 되돌리고 정지
  const bi=bldHit(me);
  if(bi>=0){
    /* ★u_5182 진단: 도로 위인데 건물 충돌이 난다는 지적.
       실측 onroad=1, xt=1.63m, margin=3.25m — 여유 안인데 건물 28건.
       충돌 시점의 도로/건물 관계를 남겨서 폴리곤이 도로를 덮는지 본다. */
    try{
      const _r=onRoad(me.x,me.y), _b=blds[bi];
      window.__bldDbg = {onroad:_r&&_r.ok?1:0, d:_r?+(_r.d/S).toFixed(2):null,
        roadW:_r&&_r.s?+(_r.s.roadW/S).toFixed(2):null,
        bld:_b&&_b.n?_b.n:'?', n:(window.__bldDbg&&window.__bldDbg.n||0)+1};
    }catch(e){}
    me.x=px0;me.y=py0;me.ang=pa0;
    const nm=blds[bi].n?blds[bi].n:'건물';
    me.v=0;
    crash(nm+' 충돌',true);
    /* ★건물에 끼면 빠져나온다(u_5056 실측).
       매 프레임 driveAuto 가 속도를 주면 → 이동이 건물에 막혀 되돌려지고 v=0.
       무한 반복이라 차가 영원히 멈춘다. 화면상 제동 0·앞차 40m·보행자 없음·
       사고 카운트도 안 늘어(cool 타이머) 원인이 안 보인다 — 실측으로 이걸
       찾는 데 세 번 헛짚었다.
       경로 주행 중이면 경로 위 안전한 지점으로 되돌려 다시 출발시킨다. */
    bldStuck=(bldStuck||0)+dt;
    if(bldStuck>1.5 && auto.on && auto.wp.length>1){
      const j=Math.min(auto.wp.length-1, auto.i+3);   // 막힌 점을 건너뛴다
      const t=auto.wp[j], p=auto.wp[Math.max(0,j-1)];
      me.x=t.x; me.y=t.y;
      me.ang=Math.atan2(t.y-p.y, t.x-p.x);
      me.v=0; me.cool=1.2; bldStuck=0;
      auto.i=j;
      if(auto.cum && j<auto.cum.length){ auto.s=auto.cum[j]; auto.k=Math.max(1,j); }
      flash('건물 끼임 복구');
    }
  } else bldStuck=0;
  /* ★차로 밖으로는 '못 나간다' — 물리적 구속(u_5027).
     도로교통법은 절대적이다. 예전엔 인도 침범을 감속+사고기록으로만 처리해서,
     차가 실제로는 인도 위를 계속 굴러다녔다(실측 25초에 사고 8~23회).
     건물은 이미 하드 구속(위치 되돌림)인데 도로만 물렁했던 것이다.
     이제 도로 밖으로 나가는 이동 자체를 무효로 만든다 — 벽과 같은 취급.
     이렇게 하면 어떤 컨트롤러(경로주행·교사·학습모델)를 쓰든 물리적으로
     차로를 벗어날 수 없다. 규칙을 지키길 '기대'하는 대신 못 어기게 만든다. */
  /* ★중앙선을 넘는 이동은 막는다(u_5048).
     오너: "가운데는 분리선으로 사고고, 건너편길은 역주행이라 가면 안 되는 곳".
     도로 밖은 이미 하드 구속인데 중앙선은 자유라, 차가 반대 차도로 넘어갔다.
     왕복도로에서 진행방향 기준 중앙선 너머로 나가는 이동을 되돌린다. */
  /* ★단, nearestSeg 가 '내가 달리는 도로'라는 보장이 없다(2026-09-15 수정).
     nearestSeg() 는 폭·방향 조건 없이 전 구간을 훑어 '가장 가까운 중심선'만 준다.
     교차로 한복판·램프·나란한 이면도로 옆에서는 그게 교차하는 다른 도로다.
     그 낯선 구간의 ang 로 dir 을 정하고 lat 을 재면, 직각에 가까운 중심선까지의
     거리라 lat 이 임의로 음수가 된다 → 위치 되돌림 + me.v*=0.5 가 매 프레임 —
     교차로에서 합법적으로 좌회전하던 차가 '중앙선 침범'으로 사고 처리됐다.
     즉 이 구속은 '중앙선을 합법적으로 넘어야 하는 바로 그 지점'에서 제일 못 믿는다.
     세 가지 관문을 세운다:
       1) ns.d <= roadW*0.5 — 실제로 그 도로 위에 있을 때만
       2) |Δheading| < 60° — 그 구간을 따라 달리고 있을 때만
          (양방향 도로는 저장된 ang 방향이 임의라 180° 접은 값으로 본다)
       3) 교차로 노드에서 roadW*1.5 안쪽이면 검사 자체를 끈다 — 회전 구간 */
  {
    const ns=nearestSeg(me.x,me.y);
    if(ns && ns.s && !ns.s.o && ns.d <= ns.s.roadW*0.5 && !nearJunction(me.x,me.y,ns.s)){
      const sg=ns.s;
      let dd=((me.ang - sg.ang + Math.PI*3)%(Math.PI*2))-Math.PI;
      /* 양방향 구간은 a→b 방향이 임의로 저장돼 있다. 역방향으로 달리는 것이
         정상(반대 차선)이므로 헤딩 일치 판정은 180° 접어서 본다. */
      const align = Math.abs(dd) > Math.PI/2 ? Math.PI-Math.abs(dd) : Math.abs(dd);
      if(align >= Math.PI/3){ blockT=Math.max(0,(blockT||0)-dt*0.5); }
      else{
      const dir = Math.abs(dd) < Math.PI/2 ? 1 : -1;
      // 중심선 기준 부호거리(진행방향 오른쪽이 +)
      const lat = (-(ns.px-me.x)*Math.sin(sg.ang) + (ns.py-me.y)*Math.cos(sg.ang)) * dir;
      if(lat < -0.6*S){                       // 중앙선 너머(반대 차도)
        me.x=px0; me.y=py0; me.ang=pa0;
        me.v*=0.5;
        me.offroad+=dt;
        if(me.offroad>.9){ me.offroad=0; crash('중앙선 침범',false); }
        blockT=(blockT||0)+dt;                // 얼마나 계속 막히고 있나
      } else blockT=Math.max(0,(blockT||0)-dt*0.5);   // 깜빡여도 누적되게 천천히 감소
      }
    }
  }
  /* ★하드 구속(중앙선·차로밖)에 오래 갇히면 경로 위로 복귀한다(u_5056).
     두 구속 모두 '위치 되돌림 + me.v 감쇠'를 매 프레임 한다. 경로점이 임계선
     바로 너머에 있으면 차는 그쪽으로 갈 수 없는데 계속 가려고 해서, 속도가
     0.2 로 수렴한 채 영원히 멈춘다 — 사고도 안 나고 제동도 0이라 화면상
     원인이 안 보인다(세 번 헛짚은 이유).
     규칙을 푸는 게 아니라, 갇히면 합법인 경로 위로 되돌려 다시 출발시킨다. */
  /* ★u_5191 오너 지적 "건물에 걸려 못 빠져나감". 실측으로 확인 —
     좌표 (-678,-1973) 이 20초간 한 번도 안 변했다. 속도는 0.6~2.2 로 찍히는데
     이동이 매 프레임 되돌려져 실제로는 제자리다. 조향도 +0.01 고정으로
     탈출을 시도조차 안 한다.
     원인: blockT 는 '중앙선 침범(lat<-0.6)' 일 때만 누적된다. 건물·경계에
     막힌 경우는 그 조건에 안 걸려서 탈출 로직이 영영 발동하지 않는다.
     ⇒ '가속 명령이 있는데 실제로 안 움직이는' 상태를 따로 센다.
       이게 갇힘의 정의다 — 원인이 건물이든 경계든 상관없다. */
  {
    const moved = Math.hypot(me.x-(window.__lastX||me.x), me.y-(window.__lastY||me.y))/S;
    window.__lastX=me.x; window.__lastY=me.y;
    /* ★속도 조건(v>0.3)을 걸었더니 여전히 갇혔다 — 갇힌 상태의 v 가
       0.00~0.34 를 오가서 조건을 자주 못 넘긴다(실측 19/20 샘플 제자리).
       '주행 중인데 안 움직인다' 만으로 충분하다. 정상 주행이면 5m/s 로
       프레임당 0.08m 는 움직인다. */
    if(auto.on && moved < 0.02 && !window.__parked && me.cool<=0){
      window.__stuckT=(window.__stuckT||0)+dt;
      if(window.__stuckT > 1.2) blockT = Math.max(blockT||0, 1.1);   // 복귀 발동
    }else window.__stuckT=Math.max(0,(window.__stuckT||0)-dt*0.5);
  }
  if(blockT>1.0 && auto.on && auto.wp.length>1){
    /* ★막힌 그 점이 아니라 '몇 점 앞'으로 보낸다(u_5056).
       같은 점으로 되돌리면 도착하자마자 같은 구속에 다시 걸려 무한반복이다 —
       실측: wp45 는 통과했는데 wp64 에서 같은 v=0.2 증상이 재현됐다.
       구속을 못 넘는 지점은 건너뛰고 그 다음 합법 지점부터 이어간다. */
    const j=Math.min(auto.wp.length-1, auto.i+3);
    const t=auto.wp[j];
    const p=auto.wp[Math.max(0,j-1)];
    me.x=t.x; me.y=t.y; me.ang=Math.atan2(t.y-p.y,t.x-p.x);
    me.v=0; me.offroad=0; me.cool=1.2; blockT=0;
    auto.i=j;
    if(auto.cum && j<auto.cum.length){ auto.s=auto.cum[j]; auto.k=Math.max(1,j); }
    flash('경로 복귀');
  }
  const r=onRoad(me.x,me.y);
  const inPark=PARK.bays.length&&Math.hypot(me.x-PARK.cx,me.y-PARK.cy)<12*S;
  if(!r.ok&&!inPark){
    const r0=onRoad(px0,py0);
    if(r0.ok){
      /* 직전엔 도로 위였다 → 이번 이동이 도로를 벗어나게 했다. 무효화한다.
         진행방향 성분만 죽이고 도로를 따라 미끄러지게 해서 그 자리에 붙어버리지 않게. */
      /* ★수집 모드(__COLLECT_RECOVER)에서는 되돌리지 않는다(u_5115 승인).
         평소엔 도로 밖으로 나가려는 이동을 무효화한다 — 그래서 학습 데이터의
         on_road 가 85,768 프레임 전부 1.00 이었다. 수집 운이 나빴던 게 아니라
         차가 물리적으로 도로 밖에 나갈 수 없었다.
         모델은 '이탈했을 때 어떻게 돌아오는지'를 시연받은 적이 없고,
         그래서 한 번 벗어나면 복구를 못 한다(실측: 사고 100% 가 차로이탈).
         수집 모드에서만 이탈을 허용하고, 교사가 도로로 되돌아오는 과정을 녹화한다. */
      if(!window.__COLLECT_RECOVER){
        me.x=px0; me.y=py0;
        me.v*=0.55;
      }
      me.offroad+=dt;
      /* ★경계에 붙어 멈춘 차를 사고로 세지 않는다(u_5169 실측).
         되돌림이 차를 경계선에 정확히 고정시키고(xt≈margin), 속도가 0 으로
         죽으면 스스로 빠져나올 수 없다. 그 상태로 0.9초가 지나면 사고가 나고,
         복귀시켜도 같은 자리라 또 난다 — 실측: 사고 4건 중 3건이
         xt=1.62/margin=1.63, 6.50/6.50, 4.87/4.88 에 v≈0.1 이었다.
         '차를 못 몬 것'이 아니라 '끼인 것'이다. 둘은 다른 문제다.
         거의 정지 상태면 타이머를 세우고, 대신 도로 안쪽으로 조금 밀어 꺼내준다. */
      if(me.v < 0.5){
        me.offroad = Math.max(0, me.offroad - dt);       // 타이머 정지
        const rr = onRoad(me.x, me.y);
        if(rr.s){                                         // 도로 중심 쪽으로 살짝
          const sg = rr.s, A = nodes[sg.a], B = nodes[sg.b];
          const vx = B.x-A.x, vy = B.y-A.y, L2 = vx*vx+vy*vy;
          let t = L2 ? ((me.x-A.x)*vx + (me.y-A.y)*vy)/L2 : 0;
          t = Math.max(0, Math.min(1, t));
          const cx = A.x+vx*t, cy = A.y+vy*t;
          const d = Math.hypot(me.x-cx, me.y-cy) || 1;
          me.x += (cx-me.x)/d * 0.6*S*dt*10;
          me.y += (cy-me.y)/d * 0.6*S*dt*10;
        }
      }
      const lim = window.__COLLECT_RECOVER ? 6.0 : 0.9;   // 수집 중엔 복귀할 시간을 준다
      if(me.offroad>lim){ me.offroad=0; crash('차로 이탈 시도',false); }
      blockT=(blockT||0)+dt;
    }else{
      /* 이미 도로 밖(사고 직후 등) → 복귀 유도. 여기선 종전대로 감속·기록. */
      me.offroad+=dt;
      me.v*=(1-2.6*dt);
      if(me.offroad>.28){me.offroad=0;
        /* ★u_5182 진단: "도로인데 건물/인도 판정이 난다".
           사고는 순간이라 사후 조회로는 못 본다. 판정 시점의 값을 남긴다. */
        try{
          window.__offDbg = {edge:+(r.edge/S).toFixed(2),
            d:+(r.d/S).toFixed(2), roadW:r.s?+(r.s.roadW/S).toFixed(2):null,
            sw:SIDEWALK_M, kind:(r.edge>SIDEWALK_M*S?'도로이탈':'인도침범'),
            n:((window.__offDbg&&window.__offDbg.n)||0)+1};
        }catch(e){}
        crash(r.edge>SIDEWALK_M*S?'도로 이탈':'인도 침범',false)}
      /* ★이 가지도 교착 카운터를 올린다(a_5170 실사고).
         여기엔 blockT 증가가 없어서, 차가 도로 '밖'에 떨어지면 위의 경로복귀
         (blockT>1.0)가 영영 안 걸렸다. 실측: 교사(GEOM)가 doneM=65, wp13 에서
         xt=2.3 > margin=1.63 인 폭 3.25m 구간에 붙어 '인도침범'을 172회까지
         반복하며 10분 내내 한 발짝도 못 나갔다. 교사가 못 가면 DAgger 라벨도
         그 지점에서 통째로 오염된다 — 되돌림 가지와 같은 탈출구를 준다. */
      blockT=(blockT||0)+dt;
    }
  }else me.offroad=0;

  /* ★출발 대기 중에는 NPC 추돌을 사고로 세지 않는다(u_5041).
     경로만 설정하고 서 있는 동안 뒤차가 와서 박으면, 아직 출발도 안 한 주행이
     사고부터 기록된다(실측: v=0, auto=0 인데 '승용차 추돌').
     서 있는 건 운전자 과실이 아니므로 대기 상태에서는 제외한다. */
  const waiting = (!auto.on && auto.wp.length>1 && me.v<0.5)
              || (auto.stall > 5 && me.v < 3);        // 교착 탈출 서행 중(u_5050)
  for(const c of cars){if(!c.alive)continue;
    if(obb(me,c)){
      /* ★내가 들이받은 것만 내 사고다(u_5061 F1-2).
         정지해 있는데 뒤차가 와서 박는 건 내 과실이 아니다. 그런데 그것도
         사고로 집계돼 '사고=실패' 판정이 부당하게 실패 처리됐다.
         판정: 내 차가 상대보다 빠르고, 상대가 내 '앞'에 있을 때만 내 추돌. */
      const fx=Math.cos(me.ang), fy=Math.sin(me.ang);
      const ahead = ((c.x-me.x)*fx + (c.y-me.y)*fy) > 0;
      const iAmFaster = me.v > (c.v||0) + 0.5;
      if(!waiting && ahead && iAmFaster) crash(c.n+' 추돌',c.t==='truck');
      else if(!waiting){ me.v=Math.min(me.v, Math.max(0,(c.v||0))); }  // 밀리지만 사고 아님
    }}
  for(const p of peds){
    if(obb(me,{x:p.x,y:p.y,ang:me.ang,w:1.4*S,h:1.4*S}))crash('보행자 사고',true)}
}
function stepCar(c,dt){
  const s=segs[c.si];
  const gp=gap(c,26*S);
  // ★후진하는 차(주차 진입/출차 흉내) — 가끔 뒤로 뺀다
  if(c.rev===undefined&&Math.random()<0.00035){c.rev=1.2+Math.random()*1.4}
  if(c.rev>0){
    c.rev-=dt;c.v+=(-2.2-c.v)*Math.min(1,dt*2);
    if(c.rev<=0){c.rev=undefined}
  }else{
    const tv=gp<10*S?0:gp<20*S?c.vmax*.35:c.vmax*.8;
    c.v+=(tv-c.v)*Math.min(1,dt*1.6);
  }
  /* ★차선변경·끼어들기(u_4972).
     두 가지로 일어난다:
       (a) 앞이 막히면 옆 차선으로 피한다 — 실제 정체에서 나오는 자연스러운 끼어들기
       (b) 낮은 확률로 그냥 차선을 바꾼다 — 교통량 단계에 따라 빈도가 올라간다
     lane 은 정수라 튀면 순간이동처럼 보이므로 laneF(실수)를 두고 부드럽게 따라가게 한다.
     ★플레이어 앞으로 파고드는 것도 막지 않는다 — 그게 학습시키려는 상황이다. */
  const nl = s.o ? s.l : Math.floor(s.l/2);        // 이 방향으로 쓸 수 있는 차로 수
  if(c.laneF===undefined) c.laneF=c.lane;
  if(c.chg===undefined && nl>1){
    const blocked = gp < 14*S;                      // 앞차에 막힘
    const want = (blocked && Math.random()<0.02) || Math.random()<CUT_P;
    if(want){
      const dirs=[];
      if(c.lane>0) dirs.push(-1);
      if(c.lane<nl-1) dirs.push(1);
      if(dirs.length){ c.chg=pick(dirs); c.chgT=0; }
    }
  }
  if(c.chg!==undefined){
    c.chgT+=dt;
    const tgt=Math.max(0,Math.min(nl-1, c.lane+c.chg));
    c.laneF += (tgt-c.laneF)*Math.min(1,dt*1.8);
    if(Math.abs(tgt-c.laneF)<0.06 || c.chgT>3.0){
      c.lane=tgt; c.laneF=tgt; c.chg=undefined;
    }
  }else{
    c.laneF += (c.lane-c.laneF)*Math.min(1,dt*3);
  }
  c.tp+=c.dir*(c.v*S*dt)/s.len;
  if(c.tp>1||c.tp<0){
    const nd=c.tp>1?s.b:s.a;
    /* ★일방통행 역주행 금지(NPC가 좌측통행처럼 보이던 원인).
       후속 구간을 아무 간선에서나 고르면, 도착 노드가 그 구간의 b 인 일방통행
       구간을 뒤에서 거슬러 올라가게 된다(dir=-1). 그러면 진행방향 기준 차로
       오프셋이 통째로 반대편(맞은편 차로)으로 놓여 좌측주행으로 보인다.
       실측: 청크 60개 90945개 전이 중 2449개(2.7%)가 이 역주행이었다.
       → 진입 가능한 간선만 후보로 둔다. 후보가 없으면 U턴(else 가지). */
    let opts=nodes[nd].e.filter(i=>i!==c.si&&segAllows(i,nd));
    if(!opts.length)opts=nodes[nd].e.filter(i=>segAllows(i,nd));
    if(opts.length){
      const ni=pick(opts),ns=segs[ni];
      c.si=ni;c.dir=(ns.a===nd)?1:-1;c.tp=(ns.a===nd)?0.001:0.999;
      c.lane=Math.min(c.lane,Math.max(0,(ns.o?ns.l:Math.floor(ns.l/2))-1));
    }else{c.dir*=-1;c.tp=Math.max(0.001,Math.min(0.999,c.tp))}
  }
  placeCar(c);
}
function stepPed(p,dt){
  const s=segs[p.si];
  // ★건널목 횡단(u_4873): 가까운 횡단보도에 닿으면 길을 건넌다
  if(p.cross){
    p.cx2+=p.cdir*p.v*S*dt;
    if(Math.abs(p.cx2)>p.cmax){p.cross=0;p.sg=-p.sg}
    const h=s.roadW*.5+SIDEWALK_M*S*.5;
    const base=h*p.sg - p.cdir*0;                // 인도에서 차도로
    const off=p.sg>0? h-Math.abs(p.cx2)*2 : -h+Math.abs(p.cx2)*2;
    const A=nodes[s.a],B=nodes[s.b];
    p.x=A.x+(B.x-A.x)*p.tp-Math.sin(s.ang)*off;
    p.y=A.y+(B.y-A.y)*p.tp+Math.cos(s.ang)*off;
    return;
  }
  p.tp+=p.dir*(p.v*S*dt)/s.len;
  if(p.tp>1||p.tp<0){p.dir*=-1;p.tp=Math.max(0,Math.min(1,p.tp))}
  placePed(p);
  if(Math.random()<0.02){                          // 횡단 시작(실측 조정: 후보 보행자가 적어 확률 상향)
    for(const c of cross){
      if(Math.hypot(c.x-p.x,c.y-p.y)<14*S){
        p.cross=1;p.cx2=0;p.cdir=1;p.cmax=(s.roadW*.5+SIDEWALK_M*S*.5);break;
      }
    }
  }
  /* ★무단횡단 — 인도에서 갑자기 뛰어나온다(u_4981).
     WHY(오너): 실제 위험은 횡단보도가 아니라 '갑자기 튀어나오는 것'이다.
     기존 보행자는 횡단보도에서만 건너서, 급제동을 배울 상황이 안 만들어졌다.
     내 차 앞쪽 가까운 거리에서만 발동시킨다 — 멀리서 건너면 그냥 지나가서
     학습 표본이 안 된다. 뛰는 속도는 평소의 2배로 둬서 '돌발'이 되게 한다. */
  if(!p.cross && JAY_P>0 && Math.random()<JAY_P){
    const dx=p.x-me.x, dy=p.y-me.y;
    const fx=Math.cos(me.ang), fy=Math.sin(me.ang);
    const f=(dx*fx+dy*fy)/S;                        // 내 앞 거리(m)
    const lat=Math.abs(-dx*Math.sin(me.ang)+dy*Math.cos(me.ang))/S;
    if(f>8 && f<34 && lat<12){                      // 반응은 가능하되 급한 거리
      p.cross=1; p.cx2=0; p.cdir=1; p.jay=1;
      p.cmax=(s.roadW*.5+SIDEWALK_M*S*.5);
      p.v*=2.0;                                     // 뛰어나온다
    }
  }
}

/* ---------- 렌더 ---------- */
const cam={x:0,y:0,z:1};
var camA=0;   // 카메라 회전각(차 진행방향이 화면 위)
function draw(){
  g.fillStyle=C('--bg');g.fillRect(0,0,W,H);
  cam.x+=(me.x-cam.x)*.12;cam.y+=(me.y-cam.y)*.12;
  const zoom=cam.z;
  /* ★차 전방이 항상 화면 위쪽이 되도록 맵을 회전한다(u_4920).
     실제 내비·주행 시점과 같다. 이래야 '직진 = 화면에서 위로 뻗은 길'이 되어
     신경망이 배울 대상이 일관된다(회전 안 하면 같은 직진도 매번 다른 그림). */
  camA += ((me.ang + Math.PI/2) - camA) * 0.18;     // 부드럽게 따라감
  g.save();g.translate(W/2,H*0.62);g.scale(zoom,zoom);
  g.rotate(-camA);
  g.translate(-cam.x,-cam.y);
  const vw=W/zoom/2+60,vh=H/zoom/2+60;   // ★화면에 보이는 만큼만(u_4880)
  // 회전 후에는 축정렬 사각형이 안 맞는다 → 반경으로 판정
  const vr=Math.hypot(vw,vh);
  const inView=(x,y,m)=>((x-cam.x)**2+(y-cam.y)**2) < (vr+(m||0))**2;

  // 건물
  g.lineJoin='round';
  for(const b of blds){
    if(!inView(b.cx,b.cy,Math.max(b.maxx-b.minx,b.maxy-b.miny)))continue;
    g.beginPath();g.moveTo(b.p[0][0],b.p[0][1]);
    for(let i=1;i<b.p.length;i++)g.lineTo(b.p[i][0],b.p[i][1]);
    g.closePath();
    g.fillStyle=C('--bld');g.fill();
    g.strokeStyle=C('--bldEdge');g.lineWidth=1.2;g.stroke();
  }
  // ★미로딩 구역 표시 — 데이터가 없는 칸은 '갈 수 없는 곳'으로 칠한다.
  //   비어 있으면 비전이 '뻥 뚫린 도로'로 착각해 그리로 돌진한다(u_4888 실사고).
  if(CH){
    const i0=Math.floor((cam.x/S)/CHUNK),j0=Math.floor((cam.y/S)/CHUNK);
    for(let i=i0-2;i<=i0+2;i++)for(let j=j0-2;j<=j0+2;j++){
      if(CH[i+','+j])continue;
      const x=i*CHUNK*S,y=j*CHUNK*S,w=CHUNK*S;
      g.fillStyle=C('--void');g.fillRect(x,y,w,w);
    }
  }
  // 인도
  g.lineCap='round';
  for(const s of segs){
    const A=nodes[s.a],B=nodes[s.b];
    if(!inView((A.x+B.x)/2,(A.y+B.y)/2,s.len))continue;
    g.strokeStyle=C('--walk');g.lineWidth=s.roadW+SIDEWALK_M*2*S;
    g.beginPath();g.moveTo(A.x,A.y);g.lineTo(B.x,B.y);g.stroke();
  }
  // 차도
  for(const s of segs){
    const A=nodes[s.a],B=nodes[s.b];
    if(!inView((A.x+B.x)/2,(A.y+B.y)/2,s.len))continue;
    g.strokeStyle=C('--road');g.lineWidth=s.roadW;
    g.beginPath();g.moveTo(A.x,A.y);g.lineTo(B.x,B.y);g.stroke();
  }
  // 차선
  for(const s of segs){
    if(s.l<2)continue;
    const A=nodes[s.a],B=nodes[s.b];
    if(!inView((A.x+B.x)/2,(A.y+B.y)/2,s.len))continue;
    /* ★중앙선 버그 수정(2026-09-14 u_4950 '중앙선이 없다').
       기존 조건 i===s.l/2 는 차로수가 홀수면 절대 참이 안 된다
       (i 는 정수, s.l/2 는 x.5). 실측: 3/5/9차로 등 전체 도로의 18%(847개)가
       중앙선 없이 그려지고 있었다.
       양방향 도로는 항상 중앙에 선이 있어야 하므로 반올림해서 판정한다. */
    const midIdx = Math.round(s.l/2);
    for(let i=1;i<s.l;i++){
      const off=(i-s.l/2)*LW,ox=-Math.sin(s.ang)*off,oy=Math.cos(s.ang)*off;
      const mid=!s.o&&i===midIdx;
      g.strokeStyle=mid?C('--center'):C('--line');
      g.lineWidth=mid?2.6:1.8;g.setLineDash(mid?[]:[3*S,3*S]);
      g.beginPath();g.moveTo(A.x+ox,A.y+oy);g.lineTo(B.x+ox,B.y+oy);g.stroke();
    }
    g.setLineDash([]);
  }
  // 주차장
  if(PARK.bays.length){
    g.save();
    for(const b of PARK.bays){
      g.save();g.translate(b.x,b.y);g.rotate(b.ang);
      g.fillStyle=C('--walk');g.fillRect(-b.h/2,-b.w/2,b.h,b.w);
      g.strokeStyle=C('--line');g.lineWidth=1.6;
      g.strokeRect(-b.h/2,-b.w/2,b.h,b.w);
      g.restore();
    }
    g.restore();
  }
  // 목적지 POI 마커
  for(const p of POIS){
    if(!inView(p.x,p.y,0))continue;
    const on=auto.goal&&Math.hypot(auto.goal.x-p.x,auto.goal.y-p.y)<6*S;
    g.fillStyle=on?C('--green'):'rgba(214,90,60,.85)';
    g.beginPath();g.arc(p.x,p.y,on?2.2*S:1.3*S,0,7);g.fill();
    g.strokeStyle='rgba(255,255,255,.85)';g.lineWidth=1.4;g.stroke();
  }
  // 횡단보도
  for(const c of cross){
    if(!inView(c.x,c.y,0))continue;
    g.save();g.translate(c.x,c.y);g.rotate(c.ang);
    g.fillStyle=C('--line');
    for(let i=-c.w/2+2;i<c.w/2-3;i+=.9*S)g.fillRect(-1.8*S,i,3.6*S,.45*S);
    g.restore();
  }
  // 표지판 — 실제 도로 속성에서 생성된 것
  for(const sg of signs){
    if(!inView(sg.x,sg.y,0))continue;
    g.save();g.translate(sg.x,sg.y);
    g.fillStyle='#7b8493';g.fillRect(-.12*S,0,.24*S,1.6*S);   // 기둥
    g.beginPath();
    if(sg.t==='spd'){g.arc(0,-.2*S,1.15*S,0,7);g.fillStyle='#fff';g.fill();
      g.lineWidth=.28*S;g.strokeStyle=sg.col;g.stroke();}
    else if(sg.t==='yld'){g.moveTo(0,.9*S);g.lineTo(-1.1*S,-1*S);g.lineTo(1.1*S,-1*S);
      g.closePath();g.fillStyle='#fff';g.fill();g.lineWidth=.26*S;g.strokeStyle=sg.col;g.stroke();}
    else{g.fillStyle=sg.col;g.fillRect(-1*S,-1.2*S,2*S,1.9*S);}
    if(sg.t==='spd'){g.fillStyle='#111';g.font='700 '+(1.1*S)+'px system-ui';
      g.textAlign='center';g.textBaseline='middle';g.fillText(sg.txt,0,-.2*S);}
    else if(sg.t==='one'){g.fillStyle='#fff';g.font='700 '+(1.2*S)+'px system-ui';
      g.textAlign='center';g.textBaseline='middle';g.fillText(sg.txt,0,-.25*S);}
    g.restore();
  }
  // 신호등 — 색만 그린다(차는 이 색을 '바닥과 다른 것'으로만 본다)
  {const now=performance.now();
   for(const sg of signals){
     if(!inView(sg.x,sg.y,0))continue;
     /* ★신호등 크기 상향(2026-09-14 u_4934/u_4935).
        기존 반경 .95*S(=5.7px)는 화면을 84x84로 줄이면 4~5픽셀만 남아
        빨강/초록 구분이 사실상 불가능했다(학습셋 실측: 빨간불 프레임당 평균 0.3px).
        실제 운전에서도 신호등은 멀리서 식별되게 돼 있으므로 과장이 아니다.
        반경을 2.2배로 키우고 흰 테두리를 둘러 축소 후에도 색이 살아남게 한다. */
     /* ★실물 4색 신호등(u_4996 오너 지적 "엉망으로 그려놨다", u_4999 진행).
        기존엔 색 원 하나였다 — 함체도 등도 없어서 '색 점'이었다.
        한국 차량 신호등 규격(위키/나무위키 확인):
          횡형 4색 = 왼쪽부터 적색 · 황색 · 녹색화살표(좌회전) · 녹색
        ★모양 자체가 특징이다. 검은 가로 함체에 등 4개가 박힌 실루엣을
          CNN 이 배울 수 있어야 한다. 색 점으로는 그 특징이 안 생긴다.
        도로 방향(sg.ang)에 맞춰 회전시켜, 마주 오는 방향에서 정면으로 보이게 한다. */
     const RED=sigRed(sg,now);
     const LW_=1.55*S, LH=1.55*S;            // 등 하나 크기
     const BW=LW_*4+0.9*S, BH=LH+0.7*S;      // 함체
     g.save();
     g.translate(sg.x,sg.y);
     g.rotate(sg.ang+Math.PI/2);             // 도로를 가로지르게
     // 지주(짧게) — 함체가 공중에 뜬 느낌을 준다
     g.fillStyle='#3a4048';
     g.fillRect(-0.35*S, BH*0.5, 0.7*S, 1.6*S);
     // 함체
     g.fillStyle='#15181d';
     rr(-BW/2,-BH/2,BW,BH,0.5*S); g.fill();
     g.strokeStyle='rgba(255,255,255,.25)'; g.lineWidth=1; g.stroke();
     // 등 4개 — 왼쪽부터 적 · 황 · 좌회전화살표 · 녹
     const cols = RED ? ['#ff2d18','#2a2118','#16301c','#16301c']
                      : ['#3a1512','#2a2118','#16301c','#19e05a'];
     for(let i=0;i<4;i++){
       const cx=-BW/2+0.45*S+LW_*(i+0.5);
       g.fillStyle=cols[i];
       g.beginPath(); g.arc(cx,0,LH*0.42,0,7); g.fill();
       if(i===2){                            // 좌회전 화살표 실루엣
         g.strokeStyle = cols[i]==='#16301c' ? 'rgba(120,200,140,.35)' : '#19e05a';
         g.lineWidth=1.6; g.beginPath();
         g.moveTo(cx+LH*0.22,0); g.lineTo(cx-LH*0.20,0);
         g.moveTo(cx-LH*0.20,0); g.lineTo(cx-LH*0.02,-LH*0.20);
         g.moveTo(cx-LH*0.20,0); g.lineTo(cx-LH*0.02, LH*0.20);
         g.stroke();
       }
     }
     // 점등된 등의 발광(멀리서도 색이 남게 — 축소돼도 살아남는 핵심)
     const li = RED?0:3;
     const gx=-BW/2+0.45*S+LW_*(li+0.5);
     g.globalAlpha=.45; g.fillStyle=RED?'#ff2d18':'#19e05a';
     g.beginPath(); g.arc(gx,0,LH*0.85,0,7); g.fill();
     g.globalAlpha=1;
     g.restore();
   }}
  // 경로
  if(auto.wp.length){                       // ★출발 전에도 경로를 보여준다(u_5041)
    g.strokeStyle=C('--green');g.globalAlpha=.6;g.lineWidth=5;g.setLineDash([4*S,3*S]);
    /* ★경로선은 '경로'만 그린다(u_5031).
       예전엔 nearestSeg(차 위치) 에서 시작해 다음 웨이포인트로 직선을 그었다.
       차가 차로에서 밀려 있으면 그 첫 획이 차로를 가로지르는 긴 대각선이 되어
       '경로가 차로를 무시한다'처럼 보였다 — 실제 경로는 멀쩡한데 그리기가 만든
       착시였다(경로선 13,715점 조밀 검사: 도로 밖 0개).
       이제 웨이포인트만 잇는다. */
    /* ★u_5172 오너 지적: "안내선이 차선 중앙이 아니고 차선에 그려진다".
       맞다 — auto.wp 는 도로 '중심선'이다. 양방향 도로에서 중심선은 곧
       중앙선이라, 그 선을 따라가면 차선을 물거나 반대차로로 넘어간다.
       교사는 이미 차로 오프셋(실측 7.92m)을 따로 잡고 있어서, 화면의
       안내선과 실제 주행 목표가 달랐다.
       ⇒ 그릴 때만 주행 차로 쪽으로 밀어준다. auto.wp 자체는 건드리지
         않는다 — 진행률 계산이 그 배열을 쓰므로 옮기면 진행률이 깨진다. */
    g.beginPath();
    /* ★u_5177: 여기서 교사 오프셋을 또 더하면 안 된다(내가 만든 버그).
       wp 는 이미 laneOff 로 차로 오프셋이 적용된 좌표다. 거기에 교사의
       off(4차로에서 8.90m)를 더하니 1.62+8.90=10.52m 가 되어 9.75m 점선
       바로 옆에 선이 그려졌다. wp 를 그대로 그린다. */
    const _ox = 0, _oy = 0;
    g.moveTo(auto.wp[auto.i].x+_ox, auto.wp[auto.i].y+_oy);
    for(let i=auto.i;i<auto.wp.length;i++)g.lineTo(auto.wp[i].x+_ox,auto.wp[i].y+_oy);
    g.stroke();g.setLineDash([]);g.globalAlpha=1;
    g.fillStyle=C('--green');g.beginPath();g.arc(auto.goal.x,auto.goal.y,1.6*S,0,7);g.fill();
  }
  // 가로등
  for(const l of lamps){
    if(!inView(l.x,l.y,0))continue;
    /* ★가로등도 진하게(u_4945) — 연한 노랑 후광이 흰 배경에 묻혔다 */
    /* ★후광을 2.4m -> 1.0m 로 줄인다(u_5118/5119 오너 지적).
       가로등은 충돌 대상이 아니다(충돌 코드 없음). 위치도 도로 밖이다 —
       1차로 도로 기준 중심선에서 3.00m, 도로 절반폭은 1.62m 이므로 인도 위다.
       그런데 후광 반지름이 2.4m 라 도로(1.62m) 위를 덮어서 '차가 가로등에
       부딪히는 것처럼' 보였다. 실제로는 통과한다 — 보이는 것과 판정이 달랐다.
       학습 입력이기도 하므로 노란 원이 도로를 가리면 모델 시야도 오염된다. */
    g.fillStyle='rgba(255,190,60,.35)';g.beginPath();g.arc(l.x,l.y,1.0*S,0,7);g.fill();
    g.fillStyle=C('--lamp');g.beginPath();g.arc(l.x,l.y,.55*S,0,7);g.fill();
  }
  // 보행자
  for(const p of peds){
    if(!inView(p.x,p.y,0))continue;
    g.fillStyle='rgba(0,0,0,.22)';g.beginPath();g.arc(p.x+1,p.y+1.5,.42*S,0,7);g.fill();
    g.fillStyle=p.c;g.beginPath();g.arc(p.x,p.y,.38*S,0,7);g.fill();
  }
  for(const c of cars){if(c.alive&&inView(c.x,c.y,10))veh(c)}
  veh(me,1);

  /* 도로명 · 건물명 라벨 (월드 좌표에 그리되 글자는 화면 기준 크기) */
  g.save();
  const inv=1/zoom;
  // 건물명
  g.textAlign='center';g.textBaseline='middle';
  for(const b of blds){
    if(!b.n)continue;
    if(!inView(b.cx,b.cy,0))continue;
    if(b.area<(10*S)*(10*S))continue;
    g.save();g.translate(b.cx,b.cy);g.scale(inv,inv);
    g.font='600 12px "Chakra Petch",system-ui,sans-serif';
    g.lineWidth=3;g.strokeStyle=C('--halo');g.strokeText(b.n,0,0);
    g.fillStyle=C('--bldInk');g.fillText(b.n,0,0);
    g.restore();
  }
  // POI 이름
  for(const p of POIS){
    if(!inView(p.x,p.y,0))continue;
    g.save();g.translate(p.x,p.y-2.4*S);g.scale(inv,inv);
    g.font='700 12px "Chakra Petch",system-ui,sans-serif';
    g.lineWidth=3.5;g.strokeStyle=C('--halo');g.strokeText(p.n,0,0);
    g.fillStyle='#c0392b';g.fillText(p.n,0,0);
    g.restore();
  }
  // 도로명 — 같은 이름은 화면당 한 번만
  const shown=new Set();
  for(const s of segs){
    if(!s.n||shown.has(s.n))continue;
    const A=nodes[s.a],B=nodes[s.b];
    const mx=(A.x+B.x)/2,my=(A.y+B.y)/2;
    if(!inView(mx,my,0))continue;
    if(s.len<16*S)continue;
    shown.add(s.n);
    let a=s.ang;if(a>Math.PI/2||a<-Math.PI/2)a+=Math.PI;
    g.save();g.translate(mx,my);g.rotate(a);g.scale(inv,inv);
    g.font='700 13px "Chakra Petch",system-ui,sans-serif';
    g.lineWidth=3.5;g.strokeStyle=C('--halo');g.strokeText(s.n,0,0);
    g.fillStyle=C('--roadInk');g.fillText(s.n,0,0);
    g.restore();
  }
  g.restore();
  g.restore();
  drawChip();
  if(window.__teach&&window.__teach.drawLabel)window.__teach.drawLabel();
  /* ★라벨 코드픽셀 — 화면에서 직접 읽는다(2026-09-14).
     아티팩트 db 로 라벨을 보내던 방식은 용량 초과로 1시간 동안 조용히 죽어 있었고
     (run 66개 누적, 'Storage full'), 그 사이 수집한 42,584프레임이 라벨 없이 버려졌다.
     화면에 찍으면 용량 제약이 없고, 픽셀과 라벨이 같은 프레임이라 시간 어긋남도 없다.
     16px 블록 4개: [마커, steer/thr/brake, rev/속도/차로거리, 사고/정지/장애물] */
  {
    const T=window.__teach, a=(T&&T.last)||{steer:0,thr:0,brake:0,rev:0};
    const ns=nearestSeg(me.x,me.y);
    const enc=v=>Math.max(0,Math.min(255,Math.round(v*255)));
    const B=16, X0=0, Y0=0;
    const put=(i,r,gg,b)=>{ g.fillStyle='rgb('+r+','+gg+','+b+')';
                            g.fillRect(X0+i*B, Y0, B, B); };
    put(0, 0xA5, 0x5A, 0xC3);                                    // 고정 마커
    put(1, enc((a.steer+1)/2), enc(a.thr), enc(a.brake));
    put(2, enc(a.rev), enc(Math.min(1,me.v/20)), enc(Math.min(1,(ns?ns.d/S:0)/16)));
    put(3, Math.min(255,me.crashes), crashHold?255:0, onRoad(me.x,me.y).ok?255:0);
    /* ★블록4 = 주행 평가용(u_5016). 오너: '실제 인간 세상처럼 좌/우회전·유턴으로
       목적지에 가는지'를 평가하려면 방향과 경로 진행률을 밖에서 읽을 수 있어야 한다.
         R = 차 진행방향(0~2pi 를 0~255)  ← 좌/우회전·유턴 판정의 근거
         G = 경로 진행률(i/wp)            ← 목적지로 실제로 다가가는지
         B = 자율주행 on/off              ← 경로주행 중인지 */
    {
      const hd = ((me.ang % (Math.PI*2)) + Math.PI*2) % (Math.PI*2);
      const prog = (auto.on && auto.wp.length) ? auto.i/auto.wp.length : 0;
      put(4, Math.round(hd/(Math.PI*2)*255), enc(prog), auto.on?255:0);
    }
    /* ★블록5 = 주행가능공간(u_5028). 오너: '다닐 수 있는 길과 없는 길이 구분이
       안 돼 있나'. 확인해보니 정확했다 — 라벨이 steer/thr/brake 3개뿐이라
       '도로 위에 있어야 한다'를 가르친 적이 한 번도 없었다. 8.5만 프레임 전부
       핸들 흉내만 배웠다.
       색으로는 구분이 된다(도로 vs 인도 색거리 80). 다만 인도 vs 건물은 16.8 이라
       '못 가는 곳'끼리는 안 뭉개진다 — 어차피 둘 다 못 가는 곳이라 상관없다.
       그래서 '얼마나 여유가 있나'를 좌/우로 나눠 명시적으로 준다.
         R = 왼쪽 여유(0~8m)   G = 오른쪽 여유(0~8m)   B = 지금 도로 위인가 */
    {
      const probe=(sgn)=>{                       // 옆으로 훑어서 도로 끝까지 거리
        const nx=-Math.sin(me.ang)*sgn, ny=Math.cos(me.ang)*sgn;
        let far=0;
        for(let m=0.5;m<=8;m+=0.5){
          if(onRoad(me.x+nx*m*S, me.y+ny*m*S).ok) far=m; else break;
        }
        return far;
      };
      put(5, enc(probe(-1)/8), enc(probe(1)/8), onRoad(me.x,me.y).ok?255:0);
      /* ★블록6 = 경로 자체가 도로 위인가(u_5036 진단).
         '길 없는 데로 경로를 잡는다'는 지적을 화면에서 직접 확인하기 위해,
         남은 웨이포인트를 훑어 도로 위 비율을 싣는다.
           R = 도로 위 웨이포인트 비율(0~255)
           G = 검사한 개수/255
           B = 첫 웨이포인트가 도로 위면 255 */
      {
        /* ★적재된 청크 안의 웨이포인트만 센다(u_5036).
           onRoad 는 로컬 segs(차 주변 3x3 청크)만 본다. 먼 웨이포인트는 그 도로가
           아직 안 올라와서 무조건 '도로밖'으로 나온다 — 그대로 세면 53% 같은
           가짜 수치가 나온다(같은 청크 안에서만 재면 실제로는 0.9%).
           그래서 차에서 1.2km 안쪽만 검사한다. */
        let ok=0,n=0,first=0;
        const LIM=1200*S;
        if(auto.wp&&auto.wp.length){
          for(let i=auto.i;i<auto.wp.length && n<60;i+=1){
            const w=auto.wp[i];
            if(Math.hypot(w.x-me.x,w.y-me.y)>LIM) break;
            const r=onRoad(w.x,w.y).ok;
            if(n===0) first=r?255:0;
            if(r) ok++; n++;
          }
        }
        put(6, n?Math.round(ok/n*255):0, Math.min(255,n), first);
        /* ★블록7 = 차가 경로를 실제로 따라가고 있나(u_5038 진단).
           R = 차에서 현재 경로선까지 거리(0~40m)
           G = 경로 진행방향과 차 진행방향의 차이(0~180도)
           B = auto.i 를 255 로 정규화(경로 소비 진척) */
        {
          let dist=40, angd=180;
          if(auto.wp && auto.wp.length>1){
            const i=Math.min(auto.i, auto.wp.length-1);
            const a=auto.wp[Math.max(0,i-1)], b=auto.wp[i];
            const vx=b.x-a.x, vy=b.y-a.y, L2=vx*vx+vy*vy;
            if(L2>1){
              const u=Math.max(0,Math.min(1,((me.x-a.x)*vx+(me.y-a.y)*vy)/L2));
              dist=Math.min(40, Math.hypot(a.x+vx*u-me.x, a.y+vy*u-me.y)/S);
              let dd=((Math.atan2(vy,vx)-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
              angd=Math.min(180, Math.abs(dd)*180/Math.PI);
            }
          }
          put(7, enc(dist/40), enc(angd/180), Math.min(255,auto.i));
          /* ★블록8 = driveAuto 가 도는가·경로 길이(u_5039 진단).
             R = driveAuto 호출 카운터(프레임마다 +1, 255로 wrap)
             G = auto.wp.length (255 clamp)
             B = auto.on */
          put(8, (window.__daCnt||0)&255, Math.min(255,auto.wp?auto.wp.length:0), auto.on?255:0);
        }
      }
    }
  }
  /* ★항상 켜지는 상태 표시(2026-09-14). 교사가 꺼진 검증 빌드에서는 교사 readout 이
     안 그려져서, 차가 왜 멈췄는지 화면에서 읽을 방법이 없었다.
     속도·사고횟수·도로위 여부·차로중심거리를 언제나 찍는다. */
  {
    const ns=nearestSeg(me.x,me.y);
    const on=onRoad(me.x,me.y);
    g.font='11px ui-monospace,Menlo,monospace';
    g.fillStyle='#000'; g.fillRect(6,H-14,360,13);
    g.fillStyle= on.ok ? '#7CFF9E' : '#ff6b6b';
    const _ck=window.__crk||{};
    const _cks=Object.keys(_ck).map(k=>k+':'+_ck[k]).join(' ')||'-';
    const _da=window.__da;
    if(_da){
      g.fillStyle='#ffd23f';
      g.fillText('AUTO st='+_da.st.toFixed(2)+' df='+_da.df.toFixed(2)
                 +' s='+(_da.s||0).toFixed(0)+'/'+(_da.tot||0).toFixed(0)+'m xt='+_da.xt.toFixed(1)
                 +' vc='+(_da.vc||0).toFixed(0)+' gp='+(_da.gp||0).toFixed(0)+' ped='+((_da.ped>900)?'-':(_da.ped||0).toFixed(0))
                 +' vmax='+(_da.vmax||0).toFixed(1)+' stl='+(_da.stall||0).toFixed(0)
                 +' brk='+(_da.brk||0).toFixed(0)+' tb='+((window.__tbrk===undefined)?'-':window.__tbrk.toFixed(2))+' blk='+(_da.blk||0).toFixed(1)+' bst='+(_da.bst||0).toFixed(1)+' cool='+(_da.cool||0).toFixed(1)+' hld='+(_da.hold||0)+' plan='+(window.__ptCnt||0),
                 12, H-52);
    }
    /* ★누가 모는지 화면에 띄운다(a_5085). 모델/기하 비교가 목적이므로
       '지금 핸들을 쥔 게 누구인가'가 안 보이면 측정 자체가 무의미하다. */
    {
      const _md = window.__mdl;
      g.fillStyle = MDL.on ? '#ff9f43' : '#7CFF9E';
      g.fillText('DRV=' + (MDL.on ? 'MODEL' : (auto.on && auto.wp.length ? 'GEOM' : 'TEACH'))
        + (MDL.on && _md ? ' st=' + _md.st.toFixed(2) + ' thr=' + _md.thr.toFixed(2)
             + ' brk=' + _md.brk.toFixed(2) + ' rx=' + _md.rx + ' err=' + _md.err : ''),
        12, H - 66);
    }
    g.fillStyle='#8bffb0';
    g.fillText('CAR v='+((me.v*3.6)|0)+' cr='+me.crashes+'['+_cks+']'
               +' road='+(on.ok?'Y':'N')
               +' d='+(ns?(ns.d/S).toFixed(1):'--')+'m'
               +' hold='+(crashHold?1:0)
               +' sig='+signals.length            /* 신호등 생성 개수 — 0 이면 데이터/필터 문제 */
               +' wp='+(auto.wp?auto.wp.length:0)  /* 경로 웨이포인트 수 — 0 이면 planTo 실패 */
               +' dm='+(window.__demoTry||0)+'/'+(window.__demoWhy||'-')  /* 데모 시도/실패사유 */
               +' auto='+(auto.on?1:0)          /* ★auto.on 이면 키 입력이 전부 무시된다(step) */
               +' K='+(K.ArrowUp?'U':'-')+(K.ArrowDown?'D':'-')
                     +(K.ArrowLeft?'L':'-')+(K.ArrowRight?'R':'-'), 9, H-4);
  }
  try{ drawNav(); }
  catch(e){ navErr=String(e&&e.message||e).slice(0,60);
    g.fillStyle='#ff3b30';g.font='700 12px system-ui';
    g.fillText('NAV ERR: '+navErr, 12, H-12); }
}
function veh(c,mine){
  g.save();g.translate(c.x,c.y);g.rotate(c.ang+Math.PI/2);
  const w=c.w,h=c.h,r=Math.min(w,h)*.22;
  g.fillStyle='rgba(0,0,0,.25)';rr(-w/2+1.5,-h/2+2,w,h,r);g.fill();
  g.fillStyle=mine?'#f1f4f9':c.c;rr(-w/2,-h/2,w,h,r);g.fill();
  /* ★차량 윤곽을 밝게(u_4955): 도로가 아스팔트 진회색이라 검은 테두리는 묻힌다.
     빨강·파랑 차량은 도로 대비가 58~85 로 낮은데, 밝은 테두리를 두르면
     어떤 차체색이든 형태가 살아난다(실제 야간 도로에서 차 윤곽이 보이는 것과 같다). */
  g.strokeStyle='rgba(255,255,255,.85)';g.lineWidth=1.2;rr(-w/2,-h/2,w,h,r);g.stroke();
  if(c.t!=='bike'&&c.t!=='moto'){
    g.fillStyle='rgba(18,24,32,.55)';
    rr(-w/2+w*.14,-h/2+h*.16,w*.72,h*.22,r*.5);g.fill();
    rr(-w/2+w*.14,h/2-h*.34,w*.72,h*.18,r*.5);g.fill();
  }
  if(mine){
    g.fillStyle='#ffe9a8';g.fillRect(-w/2+w*.1,-h/2-1.5,w*.22,2);
    g.fillRect(w/2-w*.32,-h/2-1.5,w*.22,2);
    if(me.v<-0.1||K.ArrowDown){g.fillStyle='#ff5a4d';
      g.fillRect(-w/2+w*.1,h/2-.5,w*.22,2);g.fillRect(w/2-w*.32,h/2-.5,w*.22,2)}
  }
  g.restore();
}
function rr(x,y,w,h,r){g.beginPath();g.moveTo(x+r,y);g.arcTo(x+w,y,x+w,y+h,r);
  g.arcTo(x+w,y+h,x,y+h,r);g.arcTo(x,y+h,x,y,r);g.arcTo(x,y,x+w,y,r);g.closePath()}

function roadName(){const n=nearestSeg(me.x,me.y);return n&&n.s.n?n.s.n:'이름없는 길'}

/* ---------- 입력/UI ---------- */
addEventListener('keydown',e=>{
  /* ★검색창에 포커스가 있으면 주행 조작으로 넘기지 않는다(u_5005 실사고).
     방향키로 검색 결과를 고르는 순간 '수동 전환'이 돌아 경로(auto.on)가 꺼졌다.
     실제로 이것 때문에 테헤란로 검색이 wp=0 으로 보였다 — 검색은 정상이었다. */
  const ae = document.activeElement;
  if(ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA')) return;
  if(e.key.startsWith('Arrow')){K[e.key]=1;e.preventDefault();
    if(auto.on){_autoOff('arrowkey');auto.on=0;sync();flash('수동 전환')}}
  if(e.key==='r'||e.key==='R')reset();
  if(e.key==='h'||e.key==='H')flash('🔊 빵!');
  if(e.key==='+'||e.key==='=')cam.z=Math.min(2.2,cam.z*1.18);
  if(e.key==='-'||e.key==='_')cam.z=Math.max(.45,cam.z/1.18);
});
addEventListener('keyup',e=>K[e.key]=0);
cv.addEventListener('pointerdown',e=>{
  /* ★지도 클릭으로 목적지를 잡는 건 '더블클릭'으로만 한다(u_5042/5043).
     캔버스가 화면 전체를 덮고 있어서, UI 버튼을 눌러도 그 클릭이 캔버스까지
     내려와 planTo 가 다시 불렸다. UI 사각형을 제외하는 방식으로 막아봤지만
     여전히 샜다 — 실측 plan=8(경로를 여덟 번 다시 짬), 그래서 차가 엉뚱한 데서
     우회전하고 길을 못 따라갔다.
     단발 클릭으로는 절대 경로를 바꾸지 않게 해서 원천 차단한다.
     지도에서 목적지를 찍고 싶으면 빈 도로를 더블클릭한다. */
  if(e.detail < 2) return;                 // 더블클릭만 허용
  if(e.target && e.target!==cv) return;
  for(const id of ['nav','tp','tl','hp','burger']){
    const el=document.getElementById(id);
    if(!el || el.hidden) continue;
    const b=el.getBoundingClientRect();
    if(e.clientX>=b.left && e.clientX<=b.right && e.clientY>=b.top && e.clientY<=b.bottom) return;
  }
  const r=cv.getBoundingClientRect();
  window.__autoStart=false;                // 지도 클릭도 '경로 설정'까지만
  planTo((e.clientX-r.left-W/2)/cam.z+cam.x,(e.clientY-r.top-H/2)/cam.z+cam.y);
  const rb=document.getElementById('qrun');
  if(rb && auto.wp.length>1){ rb.disabled=false; flash('경로 설정됨 — [목적지 가기]'); }
  flash('목적지 설정');
});
cv.addEventListener('wheel',e=>{e.preventDefault();
  cam.z=Math.max(.45,Math.min(2.2,cam.z*(e.deltaY<0?1.1:1/1.1)))},{passive:false});
document.getElementById('md').onclick=()=>{
  if(auto.on){_autoOff('mdclick');auto.on=0;flash('수동 전환')}
  else if(auto.goal){auto.on=1;flash('자율주행 재개')}
  else flash('지도를 클릭해 목적지를 정하세요');
  sync();
};
document.getElementById('rs').onclick=reset;
/* ★교통량 버튼(u_4997) — 빌드 없이 화면에서 바로 바꾼다 */
function syncTrafficUI(){
  document.querySelectorAll('button.tf').forEach(b=>{
    b.classList.toggle('on', b.dataset.lv===window.__TRAFFIC);
  });
}
document.querySelectorAll('button.tf').forEach(b=>{
  b.onclick=()=>{ window.setTraffic(b.dataset.lv);
                  flash('교통량: '+b.textContent+' (차 '+WANT_CARS+'대)'); };
});
syncTrafficUI();

/* ★계기판 토글(u_4874) — 주행 중엔 화면을 가리지 않는다 */
let hudOn=false;
function setHud(v){
  hudOn=v;
  for(const id of['hp','tp','tl']){const e=document.getElementById(id);if(e)e.hidden=!v}
  const b=document.getElementById('burger');
  if(b){b.classList.toggle('on',v);b.setAttribute('aria-expanded',v?'true':'false')}
}
const _bg=document.getElementById('burger');
if(_bg)_bg.onclick=e=>{e.stopPropagation();setHud(!hudOn)};
addEventListener('keydown',e=>{if(e.key==='i'||e.key==='I')setHud(!hudOn)});
setHud(false);
function sync(){
  const b=document.getElementById('md'),s=document.getElementById('st');
  if(b){b.textContent=auto.on?'수동으로':'자율주행';b.classList.toggle('on',!!auto.on)}
  if(s){s.textContent=auto.on?'AUTOPILOT':'수동';s.classList.toggle('live',!!auto.on)}
  const cc=document.getElementById('cc');if(cc)cc.textContent=me.crashes;
  const d=document.getElementById('dm');
  if(d){d.style.width=(100-me.dmg)+'%';
    d.style.background=me.dmg>66?C('--red'):me.dmg>33?C('--amber'):C('--green')}
}
// ★LEARN을 reset()보다 먼저 정한다 — reset()이 학습모드 여부로 시작위치를 고른다.
var LEARN=/[?&]learn=1/.test(location.search);
reset();sync();

/* ★동적 스트리밍(u_4879) — 차가 청크를 넘어가면 그 주변만 다시 짓는다.
   화면에 보이는 영역만 유지하므로 서울·경기 전역이어도 메모리가 일정하다. */
function streamWorld(force){
  if(!CH)return;
  const k=chunkKey(me.x/S,me.y/S);
  if(!force&&k===curChunk)return;
  curChunk=k;
  ROADS_ACTIVE=collectRoads(me.x/S,me.y/S);
  BLDS_ACTIVE =collectBlds(me.x/S,me.y/S);
  buildGraph(ROADS_ACTIVE);recalcXR();
  blds=mkBlds(BLDS_ACTIVE);buildBldGrid();
  buildCross();buildSignals();buildSigns();buildLamps();
  respawnTraffic();
}
/* 새 영역에 맞춰 교통 재배치(먼 곳 차량은 버린다) */
function respawnTraffic(){
  cars.length=0;peds.length=0;
  for(let i=0;i<segs.length;i++){
    const sg=segs[i];
    if(sg.len<12*S)continue;
    const A=nodes[sg.a],B=nodes[sg.b];
    const mx=(A.x+B.x)/2,my=(A.y+B.y)/2;
    if((mx-me.x)**2+(my-me.y)**2>(620)**2)continue;   // 초기 소수만(나머지는 동적 등장)
    if(Math.random()>0.25)continue;
    for(let k2=0;k2<1;k2++){
      const t=Math.random()<.14?'truck':Math.random()<.18?'moto':Math.random()<.12?'bike':'car';
      const T=TY[t];
      const dir=sg.o?1:(Math.random()<.5?1:-1);
      const lane=(Math.random()*Math.max(1,sg.o?sg.l:Math.floor(sg.l/2)))|0;
      const c={t,...T,c:pick(T.cs),w:T.wm*S,h:T.hm*S,si:i,dir,lane,tp:Math.random(),
        v:T.vmax*rnd(.55,.85),x:0,y:0,ang:0,alive:1};
      placeCar(c);cars.push(c);
    }
    if(Math.random()<.12){
      const sgn=Math.random()<.5?-1:1;
      const p2={si:i,tp:Math.random(),sg:sgn,v:rnd(1.1,1.6),dir:Math.random()<.5?1:-1,
        x:0,y:0,c:pick(['#d94a3d','#3b7dd8','#2fa360','#e8a317','#111827','#8b5cf6'])};
      placePed(p2);peds.push(p2);
    }
  }
}

/* ★오브젝트 동적 등장/퇴장(u_4881)
   전부 미리 깔지 않는다. 화면 가장자리 밖에서 조금씩 나타나고,
   멀어지면 사라진다. 매번 다른 상황이 만들어져 학습 표본이 다양해진다. */
/* ★교통량 3단계 + 끼어들기 (u_4972).
   WHY(오너): "실제 운전을 잘 하는지 확인"하려면 한산한 길만 달려선 알 수 없다.
   빈 도로에서 차선 지키는 것과, 옆차가 끼어드는 상황에서 안 박는 건 다른 능력이다.
   단계는 빌드 플래그(window.__TRAFFIC)로 고른다 — 아티팩트는 샌드박스라
   URL 파라미터가 안 들어오기 때문(cf RECIPE DEAD END #1). */
const TRAFFIC_LV = {
  light:  {cars:12, peds: 8, cut:0.00020},   // 적당히 — 차선유지 기본기
  medium: {cars:34, peds:16, cut:0.00060},   // 중간 (기존 기본값)
  heavy:  {cars:72, peds:30, cut:0.00150},   // 아주 많음 — 정체·끼어들기 빈발
};
/* ★런타임 전환(u_4997). 예전엔 빌드 플래그라 밀도를 바꾸려면 매번 다시 빌드하고
   아티팩트를 재배포해야 했다. 화면 버튼으로 즉시 바꿀 수 있게 let 으로 바꾼다. */
let _TL = TRAFFIC_LV[window.__TRAFFIC] || TRAFFIC_LV.medium;
let WANT_CARS=_TL.cars, WANT_PEDS=_TL.peds, CUT_P=_TL.cut;
/* 앞쪽 우선 스폰 비율 — 밀도가 높을수록 강하게(정체를 만들려면 앞에 있어야 한다) */
let FRONT_BIAS = {light:0.3, medium:0.6, heavy:0.85}[window.__TRAFFIC] ?? 0.6;
/* 무단횡단 발생확률(프레임당, 보행자 1명 기준) — 밀도가 높을수록 잦다 */
let JAY_P = {light:0.0004, medium:0.0010, heavy:0.0022}[window.__TRAFFIC] ?? 0.0010;

/* 교통량 전환 — 버튼/외부에서 호출. 즉시 반영되고, 줄일 때는 멀리 있는 차부터 지운다. */
window.setTraffic = function(lv){
  if(!TRAFFIC_LV[lv]) return null;
  window.__TRAFFIC = lv;
  _TL = TRAFFIC_LV[lv];
  WANT_CARS=_TL.cars; WANT_PEDS=_TL.peds; CUT_P=_TL.cut;
  FRONT_BIAS = {light:0.3, medium:0.6, heavy:0.85}[lv];
  JAY_P      = {light:0.0004, medium:0.0010, heavy:0.0022}[lv];
  // 초과분은 내게서 먼 것부터 정리한다(눈앞에서 사라지면 부자연스럽다)
  const far=(a,b)=>((b.x-me.x)**2+(b.y-me.y)**2)-((a.x-me.x)**2+(a.y-me.y)**2);
  if(cars.length>WANT_CARS){ cars.sort(far); cars.length=WANT_CARS; }
  if(peds.length>WANT_PEDS){ peds.sort(far); peds.length=WANT_PEDS; }
  try{ syncTrafficUI(); }catch(e){}
  return lv;
};
let spawnAcc=0;
function spawnDespawn(dt){
  const viewR=Math.max(W,H)/cam.z*0.62+140;      // 화면 반경
  const killR=viewR*1.9;
  // 멀어진 것 제거
  for(let i=cars.length-1;i>=0;i--){
    const c=cars[i];
    if((c.x-me.x)**2+(c.y-me.y)**2>killR*killR)cars.splice(i,1);
  }
  for(let i=peds.length-1;i>=0;i--){
    const p=peds[i];
    if((p.x-me.x)**2+(p.y-me.y)**2>killR*killR)peds.splice(i,1);
  }
  // 조금씩 등장(한 프레임에 몰아서 넣지 않는다)
  spawnAcc+=dt;
  if(spawnAcc<0.12)return;
  spawnAcc=0;
  const ring=[];                                   // 화면 밖 가장자리 도로
  for(let i=0;i<segs.length;i++){
    const sg=segs[i];if(sg.len<12*S)continue;
    const A=nodes[sg.a],B=nodes[sg.b];
    const mx=(A.x+B.x)/2,my=(A.y+B.y)/2;
    const d2=(mx-me.x)**2+(my-me.y)**2;
    if(d2>viewR*viewR*0.85&&d2<killR*killR*0.8)ring.push(i);
  }
  if(!ring.length)return;
  if(cars.length<WANT_CARS){
    /* ★내 앞에 차를 깔아준다(u_4975 후속).
       WHY: heavy 로 72대를 띄워도 9x9km 에 흩어지면 내 차선 앞은 거의 항상 비어 있다.
       실측: heavy 40초 주행에서 제동 0%, 앞차 없음(readout 에도 전방차 없음).
       제동·정체·끼어들기를 배우려면 '내가 가는 길 위'에 있어야 의미가 있다.
       그래서 후보 구간 중 내 진행방향 앞쪽(내적>0)인 것을 우선 고른다. */
    let i;
    if(FRONT_BIAS>0 && Math.random()<FRONT_BIAS){
      const fx=Math.cos(me.ang), fy=Math.sin(me.ang);
      const fwd=ring.filter(k=>{
        const A=nodes[segs[k].a],B=nodes[segs[k].b];
        const mx=(A.x+B.x)/2-me.x, my=(A.y+B.y)/2-me.y;
        return (mx*fx+my*fy)>0;                  // 내 앞쪽
      });
      i = fwd.length ? pick(fwd) : pick(ring);
    }else i = pick(ring);
    const sg=segs[i];
    const t=Math.random()<.14?'truck':Math.random()<.2?'moto':Math.random()<.13?'bike':'car';
    const T=TY[t];
    const dir=sg.o?1:(Math.random()<.5?1:-1);
    const nlane=Math.max(1,sg.o?sg.l:Math.floor(sg.l/2));
    /* ★내 차로(또는 바로 옆)에 놓는다(u_4975/4977 실측 후속).
       WHY: 강남대로는 편도 5차로다. 차로를 균등난수로 고르면 내 차로에 올 확률이
       1/5 이고, 그나마 앞/뒤·반대방향으로 또 갈린다. 실측에서 heavy 72대를 띄우고도
       40초 동안 앞차를 한 번도 못 만나 제동이 0% 였다(화면에도 먼 차로에만 차가 있었다).
       제동·정체를 배우게 하려면 '같은 차로 앞'에 있어야 한다. */
    let lane;
    if(FRONT_BIAS>0 && Math.random()<FRONT_BIAS){
      /* 내 차로 번호는 따로 안 들고 있으므로 가장 가까운 구간 기준 횡오프셋에서 역산한다 */
      let myl = 0;
      const ns0 = nearestSeg(me.x,me.y);
      if(ns0 && ns0.s === sg){
        const lat = (-(ns0.px-me.x)*Math.sin(sg.ang) + (ns0.py-me.y)*Math.cos(sg.ang));
        myl = Math.max(0, Math.min(nlane-1, Math.round(Math.abs(lat)/LW - 0.5)));
      }
      const jitter = Math.random()<0.6 ? 0 : (Math.random()<0.5?-1:1);
      lane = Math.max(0, Math.min(nlane-1, myl + jitter));
    }else lane=(Math.random()*nlane)|0;
    const c={t,...T,c:pick(T.cs),w:T.wm*S,h:T.hm*S,si:i,dir,lane,
      tp:Math.random(),v:T.vmax*rnd(.5,.9),x:0,y:0,ang:0,alive:1};
    placeCar(c);cars.push(c);
  }
  if(peds.length<WANT_PEDS){
    const i=pick(ring);
    const p2={si:i,tp:Math.random(),sg:Math.random()<.5?-1:1,v:rnd(1.0,1.7),
      dir:Math.random()<.5?1:-1,x:0,y:0,
      c:pick(['#d94a3d','#3b7dd8','#2fa360','#e8a317','#111827','#8b5cf6'])};
    placePed(p2);peds.push(p2);
  }
}

/* ===== 학습 에피소드 (u_4882/4883) =====
   판 시작 → POI 자동 지정 → 주행 → 도착/실패 → 자동 리셋 → 다음 판.
   ★상태는 화면 좌상단 4x4 픽셀 '상태칩'으로만 노출한다.
     게임 변수를 파이썬에 넘기지 않는다 = 비전이 눈으로 읽어야 한다(로직금지 준수). */
const EP={n:0,t:0,limit:75,goal:null,state:'run',clears:0,fails:0,startD:0,
          stuck:0,bestD:1e18};
function epStart(){
  EP.n++;EP.t=0;EP.state='run';EP.stuck=0;
  const p=nextPOI();
  if(p){EP.goal=p;auto.goal={x:p.x,y:p.y};}
  else EP.goal=null;
  EP.startD=EP.goal?Math.hypot(EP.goal.x-me.x,EP.goal.y-me.y):0;
  EP.bestD=EP.startD;
  /* ★제한시간 = 거리에 비례(u_4884).
     실측: POI까지 중앙값 2985m, 최대 5247m.
     실주행 ~10m/s에 우회 1.6배 → 필요시간 = 거리/10*1.6.
     여기에 2배 여유 + 최소 90초. 즉 '75초 안에 도착'이 아니라
     '그 거리면 이 정도는 줘야 한다'로 계산한다. */
  const need=(EP.startD/S)/10*1.6;
  EP.limit=Math.max(90,Math.min(900,need*2));
}
function epEnd(ok){
  EP.state=ok?'clear':'fail';
  if(ok)EP.clears++;else EP.fails++;
  setTimeout(()=>{hardReset();epStart()},700);
}
function hardReset(){
  /* ★항상 도로 위에서 재시작한다(u_4917/u_4953).
     지금 이 함수에 주차칸 분기는 없다 — PARK.bays 는 segs 가 통째로 비었을 때만
     쓰는 최후 수단이다(아래 else 절). 과거에 여기가 주차칸으로 고정돼 있어서
     reset() 만 고쳐도 매 판 주차칸(도로 밖 13.3m)으로 돌아갔고, 직진하면 도로에
     닿기 전에 이탈 사고가 났다 — 그 분기가 사라졌다는 사실이 이 주석의 요점이다. */
  /* ★검증(교사 OFF) 때도 도로 위에서 출발해야 한다. 주차칸 출발은 도로 밖 13m 지점이라
     모델이 아무리 전진해도 길을 못 찾는다(2026-09-14 검증 실패 원인 중 하나). */
  /* ★hardReset()은 teacher.js 보다 먼저 돈다 → window.__teach 로 판단하면 항상 false 라
     주차칸(도로 밖 13.3m)에서 출발해 버린다(실측: readout 'road=N d=13.3m').
     빌드 플래그(window.__SPAWN_ON_ROAD)로 판단한다. */
  /* ★2026-09-14 u_4953: 여기가 진짜 사고-리셋 경로다.
     앞서 reset()(410행) 만 고치고 이걸 놓쳐서, 사고가 나면 주차칸으로 돌아가
     그대로 갇혔다. 실측: 수집 421초 중 첫 10%만 도로위 93%, 사고 발생 후
     나머지 90%가 전부 lane=13.01m / 도로위 0.3% / 속도 12km/h 로 고정.
     LEARN·플래그와 무관하게 항상 도로 위에서 재시작한다. */
  /* ★먼저 강남역으로 순간이동한 뒤 그 일대를 스트리밍한다(u_5077).
     segs 는 '차 주변 3x3 청크'만 담는다. 차가 아직 경부고속도로 근처에 있으면
     강남역 도로가 아예 안 올라와 있어서, '강남역 최근접'을 구해도 후보 중에
     고속도로밖에 없다 — 실측 'START: 경부고속도로 / 강남역에서 783m'.
     좌표를 먼저 옮기고 streamWorld 를 돌려야 강남역 도로가 segs 에 들어온다. */
  {
    const g0=gangnamXY();
    me.x=g0.x*S; me.y=g0.y*S;
    try{ if(typeof streamWorld==='function') streamWorld(true); }catch(e){ }
  }
  if(segs.length){
    /* ★사고 지점 근처 청크로 스트리밍이 바뀌면 옛 start 인덱스는 무효다.
       배치 규칙은 placeCarNear() 한 곳에 있다(강남역 최근접 시가지 도로 → 건물 회피).
       ★'가장 긴 구간'이 아니라 '강남역에서 가장 가까운 시가지 도로'다(u_5073~5076).
       가장 긴 구간을 고르면 그 일대에서 제일 긴 간선대로가 뽑힌다 — 강남역과 무관하다.
       실측: 강남역(11.4,-9.9) 기준 최근접 = 테헤란로 12.7m. */
    const g=gangnamXY();
    const r=placeCarNear(g.x*S, g.y*S, {metric:'mid', place:true});
    /* r===null = 20m 이상인 구간이 하나도 없다(청크가 덜 올라왔을 때).
       그 땐 첫 구간에 같은 규칙(ts 후보 없이 t=0.15)으로라도 세운다. */
    const r2 = r || placeCarNear(nodes[segs[0].a].x, nodes[segs[0].a].y,
                                 {metric:'mid', place:true, any:true});
    const bs = r2 ? r2.seg : segs[0];
    if(!r2){ me.x=nodes[bs.a].x; me.y=nodes[bs.a].y; me.ang=bs.ang; }
    window.__startFree=(r2&&r2.free)?1:0;
    window.__startRoad=(bs.n||'(이름없음)')+' '+(bs.l||'?')+'차로 강남역에서 '
                      +Math.round(Math.sqrt(r2?r2.d2:0)/S)+'m';
    /* ★멀리 순간이동하면 그 구역 청크가 아직 없어 road=N 이 된다(실측 d=13.2m).
       스폰 직후 강제로 월드를 다시 스트리밍해 도로·신호등을 채운다. */
    try{ if(typeof streamWorld==='function') streamWorld(true); }catch(e){}
  }else if(PARK.bays.length){const b=PARK.bays[2];me.x=b.x;me.y=b.y;me.ang=PARK.ang}
  me.v=0;me.dmg=0;me.crashes=0;me.offroad=0;me.cool=0;
  resetTeacherLane();
  _autoOff('spawn'); auto.on=0;auto.wp=[];auto.i=0;
  streamWorld(true);
}
function epTick(dt){
  if(!LEARN||EP.state!=='run')return;
  /* ★사용자가 목적지를 찍고 주행 중이면 학습 에피소드는 관여하지 않는다(u_5035).
     이 빌드는 teacher=ON(=LEARN)이라 내비게이션 중에도 에피소드가 같이 돌았다.
     에피소드는 자기 목표(EP.goal)를 갖고 있어서, 45초간 그쪽으로 못 가까워지면
     실패 처리하고 hardReset() 을 부른다 — hardReset 은 auto.wp 를 비우고 차를
     에피소드 출발지로 순간이동시킨다.
     그래서 경로가 69점 멀쩡히 있는데도 차는 경로에서 40m·172도 떨어진 채
     굳어 있었다(라벨 블록이 auto.wp.length<=1 분기를 찍은 이유).
     내비 주행이 우선이다. 에피소드는 멈춰 둔다. */
  if(auto.on && auto.wp && auto.wp.length>1){ EP.stuck=0; EP.t=0; return; }
  EP.t+=dt;
  if(EP.goal){
    const d=Math.hypot(EP.goal.x-me.x,EP.goal.y-me.y);
    if(d<9*S){epEnd(true);return}          // ★클리어 = 목적지 도달
    /* 진전이 있으면 시간을 더 준다 — 오래 걸리는 게 죄는 아니다.
       '가까워지지 않는 것'만 실패로 본다. */
    if(d<EP.bestD-3*S){EP.bestD=d;EP.stuck=0}
    else{EP.stuck+=dt}
    if(EP.stuck>45){epEnd(false);return}   // 45초간 한 발짝도 못 가까워지면 포기
  }
  if(EP.t>EP.limit){epEnd(false);return}   // 거리 대비 총 제한시간
  if(me.dmg>=100){epEnd(false);return}     // 대파
}
/* 상태칩 — 화면 좌상단. 비전이 이 색을 보고 판정한다.
   초록=클리어 / 빨강=실패 / 파랑=주행중, 옆 막대=남은시간 */
/* ★네비 미니맵(u_4893) — 실제 내비처럼 '축약된 경로'를 화면에 그린다.
   비전은 이 그림을 눈으로 본다. 좌표를 넘겨받는 게 아니다(로직금지 유지).
   화면 우상단 고정 위치 = 눈이 항상 같은 자리를 보면 된다. */
function drawNav(){
  /* 목적지가 아직 없으면 가까운 POI를 잠정 목표로 삼아서라도 내비를 띄운다.
     (학습모드 진입 전에도 비전이 같은 자리에서 같은 그림을 보게 하려는 것) */
  let G=EP.goal||auto.goal;
  if(!G&&POIS.length){
    let b=null,bd=1e18;
    for(const p of POIS){const d=(p.x-me.x)**2+(p.y-me.y)**2;if(d<bd){bd=d;b=p}}
    G=b;
  }
  if(!G)return;
  /* ★위치: 화면 상단 중앙에서 약간 오른쪽. 우측 끝에 붙이면 창 경계에 걸려
     비전 캡처 밖으로 잘려 안 보였다(2026-09-14 실측). */
  /* ★우측으로 더(u_5035 오너 지시). 0.72 는 검색창과 겹쳤다.
     우측 끝에서 R+14 만큼만 띄워 캡처 안에는 남게 한다. */
  const R=54,cx=W-R-14,cy=R+12;
  // 배경 원
  g.save();
  g.beginPath();g.arc(cx,cy,R,0,7);
  g.fillStyle='rgba(12,16,22,.82)';g.fill();
  g.strokeStyle='rgba(255,255,255,.22)';g.lineWidth=1.5;g.stroke();
  g.clip();
  // 차 기준 회전(항상 위쪽이 진행방향) — 실제 내비와 같은 방식
  g.translate(cx,cy);g.rotate(-me.ang-Math.PI/2);
  const SC=R/(260*S);                    // 반경 260m를 원 안에 축약
  // 주변 도로를 가늘게
  g.strokeStyle='rgba(150,160,175,.55)';
  for(const sg of segs){
    const A=nodes[sg.a],B=nodes[sg.b];
    const ax=(A.x-me.x)*SC,ay=(A.y-me.y)*SC,bx=(B.x-me.x)*SC,by=(B.y-me.y)*SC;
    if(Math.abs(ax)>R&&Math.abs(bx)>R&&Math.abs(ay)>R&&Math.abs(by)>R)continue;
    g.lineWidth=Math.max(1,sg.l*0.6);
    g.beginPath();g.moveTo(ax,ay);g.lineTo(bx,by);g.stroke();
  }
  // ★목적지까지의 경로를 굵은 초록선으로(축약 경로)
  const path=navPath(G);
  if(path&&path.length>1){
    g.strokeStyle='#28e07a';g.lineWidth=3.2;g.lineCap='round';
    g.beginPath();
    for(let i=0;i<path.length;i++){
      const x=(path[i].x-me.x)*SC,y=(path[i].y-me.y)*SC;
      i?g.lineTo(x,y):g.moveTo(x,y);
    }
    g.stroke();
  }
  // 목적지 표시(원 밖이면 테두리에 붙임)
  let gx=(G.x-me.x)*SC, gy=(G.y-me.y)*SC;
  const gd=Math.hypot(gx,gy);
  if(gd>R-6){const k=(R-6)/gd;gx*=k;gy*=k}
  g.fillStyle='#ff3b30';g.beginPath();g.arc(gx,gy,4.5,0,7);g.fill();
  g.restore();
  // 내 차(항상 중앙, 위 방향)
  g.save();g.translate(cx,cy);
  g.fillStyle='#ffffff';g.beginPath();
  g.moveTo(0,-6);g.lineTo(4.5,5);g.lineTo(-4.5,5);g.closePath();g.fill();
  g.restore();
}
/* 경로 계산은 게임 쪽에서 한다(내비 화면을 그리기 위해).
   차에게 좌표로 알려주지 않는다 — 오직 위 그림으로만 전달된다. */
let navCache={t:0,path:null,goal:null};
function navPath(G){
  G=G||EP.goal;
  const now=performance.now();
  if(navCache.path&&navCache.goal===G&&now-navCache.t<1200)return navCache.path;
  let path=null;
  if(G){
    const a=astar(nearestNode(me.x,me.y),nearestNode(G.x,G.y));
    if(a)path=a.map(i=>({x:nodes[i].x,y:nodes[i].y}));
  }
  navCache={t:now,path,goal:G};
  return path;
}
function drawChip(){
  const x=6,y=6,w=54,h=10;
  // ★사고 표시등 — 칩 오른쪽. 사고 후 1.2초간 계속 켜져 있어 비전이 샘플링해도 보인다.
  g.fillStyle=crashLit>0?'#ff2d2d':'rgba(0,0,0,.25)';
  g.fillRect(x+w+4,y,h,h);
  g.fillStyle=EP.state==='clear'?'#00d26a':EP.state==='fail'?'#ff2d2d':'#2f7bff';
  g.fillRect(x,y,h,h);
  g.fillStyle='rgba(0,0,0,.25)';g.fillRect(x+h+3,y,w-h-3,h);
  const frac=EP.goal?Math.max(0,1-Math.hypot(EP.goal.x-me.x,EP.goal.y-me.y)/Math.max(1,EP.startD)):0;
  g.fillStyle='#ffd23f';g.fillRect(x+h+3,y,(w-h-3)*frac,h);   // 목적지 근접도
}

let last=performance.now(),nt=0;
function loop(t){
  streamWorld(false);
  const dt=Math.min(.05,(t-last)/1000);last=t;
  /* ★한 프레임에 한 컨트롤러만 차를 몬다(P1, u_5020).
     예전엔 교사와 자율주행이 매 프레임 둘 다 실행돼 me.steer/me.v 를 서로 덮어썼다.
     서로 다른 방향을 요구하면 조향이 ±1 로 튀어 포화됐다(실측 97~99%).
     경로가 있으면 자율주행이 몰고, 없으면 교사가 몬다.
     ★교사는 여전히 매 프레임 '정답'을 계산한다(T.compute) — 학습 라벨은 계속 나와야
       하므로, 모는 것만 멈추고 라벨 생산은 유지한다. */
  const T = window.__teach;
  mdlPoll(dt);                                      // 모델 제어채널 폴링(항상)
  if(MDL.on){
    /* ★모델이 핸들을 쥔다. driveAuto 는 호출하지 않는다 — 둘이 매 프레임
       me.steer 를 서로 덮어쓰면 누가 모는지 측정이 불가능해진다(u_5026 에서
       경로 vs 교사가 정확히 그렇게 싸워 사고가 8→23회로 늘었다).
       단 진행률·웨이포인트 추적은 계속 돌아야 평가가 되므로 auto 상태는 둔다. */
    driveModel(dt);
    /* 진행률은 모델이 몰 때도 반드시 갱신한다 — 이게 평가지표 그 자체다. */
    try{ if(auto.wp.length) trackProgress(); }catch(e){}
    /* ★모델이 몰 때는 교사가 '몰지 않아도' 정답은 계속 계산한다(u_5158 DAgger).
       T.last 는 T.auto 가 true 일 때만 갱신됐는데, parkCar() 가 T.auto=false 로
       꺼놓고 아무도 되돌리지 않는다. 그래서 수집이 '교사 라벨 없음'으로 중단됐다.
       DAgger 의 정의가 '모델이 몰고 교사는 정답만 말한다' 이므로,
       모는 것(T.auto)과 답하는 것(T.compute)을 분리한다. */
    try{ if(T) T.last = T.compute(); }catch(e){}   // 라벨은 항상 생산
  }else if(auto.on && auto.wp.length){
    /* ★내비 경로와 자율주행을 실제로 연결한다(u_5026).
       예전엔 경로가 있으면 driveAuto 가 전부 몰았다. 그런데 driveAuto 는
       '다음 점으로 핸들을 꺾는다'가 전부라, 신호등·앞차·보행자·목표속도를
       하나도 보지 않는다. 그래서 경로가 맞아도 사고가 났다(실측 25초에 8회).
       역할을 나눈다:
         · 어디로 갈지(조향)  = 경로       → driveAuto
         · 어떻게 안전하게    = 교사        → 적신호 정지·차간거리·커브감속·목표속도
       교사의 brake/thr 로 경로 주행의 속도를 덮어써서, 경로를 따라가되
       빨간불에 서고 앞차와 간격을 유지한다. */
    driveAuto(dt);                                  // 경로 = 조향(어디로)
    if(T && T.auto){
      try{
        const a = T.compute();                      // 교사 = 안전(어떻게)
        T.last = a;
        window.__tbrk = a ? a.brake : -1;           // 교사 제동값 자체를 화면에 노출
        /* ★교사의 '정지' 지시만 받는다(u_5026 실측 수정).
           처음엔 thr 까지 받아 속도를 통째로 덮어썼는데, 경로주행의 가감속과
           교사의 목표속도가 매 프레임 싸워서 오히려 사고가 늘었다
           (실측: 25초 사고 8회 → 30초 23회). 되돌리고 '멈춰야 할 때 멈춘다'만
           남긴다 — 빨간불·앞차·보행자가 여기에 해당한다. */
        /* ★교사 제동이 영구히 잡고 있지 못하게 한다(u_5052).
           실측: 교차로에서 st=0·xt=0·사고0 으로 완벽히 정렬된 채 v=0 이 120초
           지속. 경로·조향은 정상인데 교사 brake 가 매 프레임 v 를 0.4 로 눌렀다.
           신호는 주기적으로 바뀌므로 정상이라면 풀려야 한다 — 20초 넘게 계속
           제동이면 그건 오검출로 보고 무시한다(사람도 신호가 안 바뀌면 살펴본다). */
        if(a && a.ok!==false && a.brake>0.5){
          window.__brkT=(window.__brkT||0)+dt;
          if(window.__brkT < 20){
            me.v -= me.v*Math.min(1, dt*3.2*a.brake);
            if(a.brake>=1) me.v=Math.min(me.v, 0.4);
          }
        }else window.__brkT=0;
      }catch(e){}
    }
  }else if(T && T.auto && !(window.__parked && !auto.on)){
    T.last = T.drive(dt);                           // 경로 없음 = 교사가 조종
  }else if(window.__parked && !auto.on){
    /* ★주행 중(auto.on)이면 주차 상태로 빠지지 않는다(u_5056 실사고).
       parkCar() 가 __parked=1 을 세우는데, 사고 복귀 경로에서 이게 남으면
       경로 주행 중에도 이 분기로 들어와 매 프레임 me.v 를 0 으로 깎는다 —
       실측: vmax=14·gp=40·brk=0·cr=0·hold=0 으로 모든 지표가 '가라'인데 v=0. */
    /* ★주차 상태: 아무도 몰지 않는다(u_5041).
       예전엔 페이지를 열자마자 교사가 곧바로 차를 몰았다(T.auto=true 기본).
       오너: "시작하면 바로 차가 주행을 하는데". 이제 주차로 시작하고,
       [목적지 가기]를 눌러야 움직인다. */
    me.v *= (1 - Math.min(1, dt*4));
    if(T && T.auto){ try{ T.last=T.compute(); }catch(e){} }   // 라벨은 계속 생산
  }
  step(dt);
  epTick(dt);
  if(crashLit>0)crashLit-=dt;
  spawnDespawn(dt);
  rebuildHash();
  // 화면 밖 먼 차량은 계산하지 않는다(보이지도 않고 비전에도 안 잡힘)
  const R2=Math.pow(Math.max(W,H)/cam.z*0.75+220,2);  // 화면 크기에 맞춘 시뮬 반경
  for(const c of cars){if(!c.alive)continue;
    if((c.x-cam.x)**2+(c.y-cam.y)**2>R2)continue;
    stepCar(c,dt)}
  for(const p of peds){
    if((p.x-cam.x)**2+(p.y-cam.y)**2>R2)continue;
    stepPed(p,dt)}
  /* ★그리기 프레임 제한(2026-09-14 u_4941).
     WindowServer(화면 합성)가 CPU 47% 를 먹고 있었는데, 캡처를 전혀 안 해도
     동일했다 — 즉 캡처 탓이 아니라 게임이 60fps 로 캔버스를 계속 다시 그리는 탓이다.
     (Chrome 을 완전히 종료하면 WindowServer 가 상위에서 사라지는 것으로 확정)
     물리는 매 프레임 돌려 주행 품질을 유지하고, 그리기만 30fps 로 낮춘다.
     비전 모델도 58fps 로 읽으므로 30fps 렌더면 충분하다. */
  if(t - lastDraw >= DRAW_MS){ lastDraw = t; draw(); }
  const sp=document.getElementById('sp');if(sp)sp.textContent=KMH(Math.abs(me.v));
  const ac=document.getElementById('ac');if(ac)ac.textContent=auto.on?auto.act:'수동 주행';
  if(t-nt>350){nt=t;const rd=document.getElementById('rd');if(rd)rd.textContent=roadName()}
  window.__rafN=(window.__rafN|0)+1;
  requestAnimationFrame(_loopSafe);
}
/* ★loop 이 한 번이라도 던지면 rAF 재등록이 안 돼 게임이 영원히 멈춘다(u_5126 실측:
   [목적지 가기] 직후 performance.now() 가 6197ms 에 고정, daCnt=0).
   던져도 다음 프레임을 반드시 예약한다 — 한 프레임 손해가 정지보다 낫다. */
function _loopSafe(t){
  try{ loop(t); }
  catch(e){ window.__jsErr='loop:'+(e&&e.message||e)+' @'+((e&&e.stack||'').split('\n')[1]||'').trim();
            window.__loopErrN=(window.__loopErrN|0)+1;
            requestAnimationFrame(_loopSafe); }
}
requestAnimationFrame(_loopSafe);

/* ===== 학습 모드 초기화 — 모든 정의가 끝난 뒤 실행(TDZ 방지) ===== */
function setLearn(v){
  LEARN=v;
  if(LEARN){hardReset();epStart();flash('학습 모드 시작')}
  else{EP.state='idle';flash('학습 모드 종료')}
}
addEventListener('keydown',e=>{if(e.key==='l'||e.key==='L')setLearn(!LEARN)});
if(LEARN){hardReset();epStart()}
/* ★LEARN 여부와 무관하게 모든 빌드가 hardReset() 으로 도로 위에서 출발한다.
   이 else 가 그 보장이다 — 이제 빠지는 빌드가 없다.
   왜 생겼나(측정 기록): 예전엔 LEARN 빌드만 hardReset() 을 불렀고, 도로출발은
   --teacher-off 빌드에만 주입되는 __SPAWN_ON_ROAD 플래그에 매달려 있었다.
   그래서 교사(수집) 빌드는 초기 주차칸(도로 밖 13.3m)에 그대로 서 있었고
   — 실측 readout road=N d=13.3m, 디코더 lane=13.0m / on_road=0 —
   도로 밖에서 수집·검증이 돌았다. 플래그 분기는 제거됐다. */
else { hardReset(); }
/* ★시작은 '주차' 상태로(u_5041). 페이지를 열자마자 교사가 차를 몰기 시작하면
   사용자가 경로를 설정할 틈이 없다. 첫 프레임 전에 세워둔다. */
window.__parked=1;
setTimeout(()=>{ try{ parkCar(); }catch(e){} }, 400);
/* ★출발지를 화면에 박아서 추정을 끝낸다(u_5077). 어느 도로에서 시작했는지 눈으로 확인. */
setTimeout(()=>{
  try{
    const n=nearestSeg(me.x,me.y), g=gangnamXY();
    const nm=(n&&n.s.n)||'(이름없음)';
    const dist=Math.round(Math.hypot(me.x-g.x*S, me.y-g.y*S)/S);
    window.__startRoad = nm+' / 강남역에서 '+dist+'m';
    const el=document.createElement('div');
    el.style.cssText='position:fixed;left:8px;bottom:26px;z-index:99999;background:#000;color:#0f0;'
      +'font:12px monospace;padding:3px 6px;border:1px solid #0f0';
    el.textContent='START: '+window.__startRoad;
    document.body.appendChild(el);
  }catch(e){
    const el=document.createElement('div');
    el.style.cssText='position:fixed;left:8px;bottom:26px;z-index:99999;background:#000;color:#f44;font:12px monospace;padding:3px 6px';
    el.textContent='START ERR: '+e.message;
    document.body.appendChild(el);
  }
}, 1200);

/* ===== 목적지 검색 (u_5003) =====
   오너 요구(u_4984): "한글이든 영문이든 주소든 지명이든 상호든 다 가게".
   맵에 이미 도로명 1,507 + 건물명 1,900 이 들어 있어서 인덱스만 붙이면 된다.
   찾은 지점은 건물 안일 수 있으므로, 반드시 '도로 위 진입점'으로 바꿔 경로를 낸다
   (u_4896 오너 지적: POI는 건물 위치이지 도로 위 지점이 아니다). */
(function(){
  const box = document.getElementById('q');
  const res = document.getElementById('qr');
  const go  = document.getElementById('qgo');
  if(!box || !res) return;
  const IDX = (typeof SEARCH !== 'undefined') ? SEARCH : [];
  let hits = [], sel = 0;

  const norm = t => (t||'').toLowerCase().replace(/\s+/g,'');
  const KIND = {road:'도로', bld:'건물', poi:'명소'};

  function search(qq){
    const q = norm(qq);
    if(q.length < 1) return [];
    const starts = [], contains = [];
    for(const r of IDX){
      const n = norm(r.n);
      if(n === q || n.startsWith(q)) starts.push(r);
      else if(n.includes(q)) contains.push(r);
      if(starts.length > 40) break;
    }
    // 가까운 것 우선 — 지금 위치에서 먼 곳을 위에 띄우면 쓸모없다
    const d2 = r => (r.x*S-me.x)**2 + (r.y*S-me.y)**2;
    starts.sort((a,b)=>d2(a)-d2(b)); contains.sort((a,b)=>d2(a)-d2(b));
    return starts.concat(contains).slice(0, 8);
  }

  function render(){
    res.innerHTML = '';
    hits.forEach((r,i)=>{
      const km = Math.hypot(r.x*S-me.x, r.y*S-me.y)/S/1000;
      const d = document.createElement('div');
      d.className = 'it' + (i===sel?' sel':'');
      d.innerHTML = '<b></b><span></span>';
      d.querySelector('b').textContent = r.n;
      d.querySelector('span').textContent = KIND[r.k]+' · '+km.toFixed(1)+'km';
      d.onclick = ()=>{ sel=i; window.__autoStart=false; pick();
        const rb=document.getElementById('qrun');
        if(rb && auto.wp.length>1){ rb.disabled=false; flash('경로 설정됨 — [목적지 가기]를 누르세요'); } };
      res.appendChild(d);
    });
  }

  function pick(){
    const r = hits[sel]; if(!r) return;
    /* 건물 중심으로 바로 planTo 하면 '도로가 아닌 곳'을 목적지로 잡는다.
       가장 가까운 도로 위 지점으로 옮긴다. */
    /* ★목적지 스냅은 전역 그래프 기준이어야 한다(u_5035 실사고).
       nearestSeg 는 적재된 청크(차 주변 3x3)만 본다. 코엑스는 3.8km 밖이라
       그 도로가 안 올라와 있고, 그러면 목적지가 '차 근처 도로'로 스냅된다.
       결과: 경로가 차 주변을 한 바퀴 도는 짧은 고리가 되고, 차는 경로에서
       40m·172도 떨어진 채 굳는다(실측 wp_idx=88 고정).
       gNearestOnRoad 는 전역 도로 간선을 보므로 먼 목적지도 제대로 붙는다. */
    try{ buildGlobalGraph(); }catch(e){}     // 스냅 전에 전역 그래프가 있어야 한다
    const n = (typeof gNearestOnRoad==='function' ? gNearestOnRoad(r.x*S, r.y*S) : null)
              || nearestSeg(r.x*S, r.y*S);
    const gx = n ? n.px : r.x*S, gy = n ? n.py : r.y*S;
    planTo(gx, gy);
    flash(r.n + ' 로 안내 시작');
    res.innerHTML = ''; box.blur();
  }

  let t=null;
  box.oninput = ()=>{ clearTimeout(t); t=setTimeout(()=>{
    hits = search(box.value); sel = 0; render();
  }, 90); };
  box.onkeydown = e=>{
    if(e.key==='ArrowDown'){ sel=Math.min(hits.length-1,sel+1); render(); e.preventDefault(); }
    else if(e.key==='ArrowUp'){ sel=Math.max(0,sel-1); render(); e.preventDefault(); }
    else if(e.key==='Enter'){
      /* ★타이핑 직후 Enter 가 눌리면 oninput 디바운스(90ms)가 아직 안 돌아
         hits 가 비어 있다. 그 경우 여기서 즉시 검색해서 첫 결과로 간다.
         (자동 타이핑 테스트에서 발견 — 사람이 쳐도 빠르면 같은 일이 생긴다) */
      if(!hits.length){ hits = search(box.value); sel = 0; }
      window.__autoStart = false;            // 엔터도 '경로 설정'까지만(u_5041)
      pick(); e.preventDefault();
      const rb=document.getElementById('qrun');
      if(rb && auto.wp.length>1){ rb.disabled=false; flash('경로 설정됨 — [목적지 가기]를 누르세요'); }
    }
    else if(e.key==='Escape'){ res.innerHTML=''; box.blur(); }
    e.stopPropagation();          // 방향키가 주행 조작으로 새지 않게
  };
  /* ★[출발]은 드롭다운 상태에 기대지 않는다(u_5003 실측).
     자동 타이핑에서는 oninput 이 안 뜨는 경우가 있어 hits 가 빈 채로 남는다.
     누를 때마다 입력값으로 새로 검색해서 첫 결과로 간다 — 사람이 쳐도 같은 동작. */
  const runBtn = document.getElementById('qrun');
  if(go) go.onclick = ()=>{
    window.__goHit = (window.__goHit||0)+1;      // 버튼이 눌렸는지 화면으로 확인
    hits = search(box.value);
    if(!hits.length){ flash('검색 결과 없음: '+box.value); return; }
    window.__autoStart = false;                  // 경로만 만든다(출발 안 함)
    sel = 0; pick();
    if(auto.wp.length>1){
      if(runBtn) runBtn.disabled = false;
      flash('경로 설정됨 — [목적지 가기]를 누르세요');
    }
  };
  /* ===== 출발지 설정 (u_5080 오너 지시: "출발지와 목적지를 선택할 수 있게") =====
     목적지와 같은 검색 인덱스를 쓰고, 찾은 지점을 '도로 위'로 스냅해 차를 옮긴다.
     스냅 전에 그 일대를 스트리밍해야 한다 — 안 그러면 차 주변 청크만 보고
     엉뚱한 도로(경부고속도로)에 붙는다(u_5077~5079 실사고). */
  const setBtn = document.getElementById('qset');
  const sBox   = document.getElementById('qs');
  function setStart(name){
    const q=(name||'').trim();
    if(!q){ flash('출발지를 입력하세요'); return false; }
    const cand=search(q);
    if(!cand.length){ flash('출발지 없음: '+q); return false; }
    /* ★'강남역'을 치면 강남역리가스퀘어오피스텔이 먼저 잡힌다(u_5080 실측).
       역 이름을 넣었으면 역/지하상가를 우선한다: 정확일치 > 역-부속시설 > 나머지. */
    const nq=norm(q);
    const rank=r=>{
      const n=norm(r.n);
      if(n===nq) return 0;                                  // 정확히 그 이름
      if(r.k==='poi') return 1;                             // POI(역 등)
      if(nq.endsWith('역') && n.startsWith(nq)){
        return /지하상가|지하쇼핑|역사|출구/.test(n) ? 2 : 4;  // 역 부속시설 우선
      }
      return 3;
    };
    const r=cand.slice().sort((a,b)=>rank(a)-rank(b))[0];
    // 1) 먼저 그 좌표로 옮기고 월드를 그 일대로 스트리밍한다
    me.x=r.x*S; me.y=r.y*S;
    try{ streamWorld(true); }catch(e){}
    /* 2) 이제 로드된 도로 중에서 가장 가까운 '시가지 도로'에 붙인다.
       고르는 규칙·건물 회피는 placeCarNear() 한 곳에 있다(hardReset·pickStart 와 공용).
       여기만 기준이 '강남역'이 아니라 '방금 옮긴 내 위치'라서 metric='proj' 다. */
    const r2=placeCarNear(me.x, me.y, {metric:'proj', place:true});
    if(!r2){ flash('출발지 근처에 도로가 없습니다'); return false; }
    const bs=r2.seg;
    me.v=0; me.steer=0;
    me.crashes=0; me.dmg=0; me.offroad=0; me.cool=1.0;
    crashHold=0; crashHoldT=0; bldStuck=0; blockT=0;
    resetTeacherLane();
    _autoOff('setStart'); auto.on=0; auto.wp=[]; auto.i=0; auto.goal=null; window.__parked=1;
    const T=window.__teach; if(T) T.auto=false;
    try{ streamWorld(true); }catch(e){}
    const rb2=document.getElementById('qrun'); if(rb2) rb2.disabled=true;
    window.__startRoad=(bs.n||'(이름없음)')+' / '+r.n;
    flash('출발지: '+r.n+' ('+(bs.n||'도로')+')');
    sync();
    return true;
  }
  window.setStart=setStart;

  /* ★로딩하면 강남역→시청역이 자동으로 잡힌다(u_5109/5110 오너 지시).
     매 리로드마다 출발지·목적지를 손으로 넣는 게 시간 낭비였다.
     [목적지 가기]는 자동으로 누르지 않는다 — 출발 시점은 사람이 정한다.
     ?auto=0 으로 끌 수 있다. */
  if(!/[?&]auto=0/.test(location.search)) setTimeout(()=>{
    try{
      const sb=document.getElementById('qs'), db=document.getElementById('q');
      if(!sb||!db) return;
      if(!sb.value) sb.value='강남역';
      if(!db.value) db.value='시청역';
      if(!setStart(sb.value)) return;          // 출발지 배치 실패면 경로도 잡지 않는다
      hits=search(db.value); if(!hits.length){ flash('목적지 없음: '+db.value); return; }
      sel=0; window.__autoStart=false; pick();  // 경로만 만든다(출발은 사람이)
      const rb=document.getElementById('qrun');
      if(rb && auto.wp.length>1){ rb.disabled=false; flash('강남역→시청역 경로 준비됨 — [목적지 가기]'); }
      /* ★?go=1 이면 경로가 잡힌 직후 자동으로 출발한다(u_5126).
         RL 하네스는 OS 클릭에 의존하면 안 된다 — 손쉬운사용 권한이 한 번
         끊기면(TCC) 클릭·키가 통째로 무시되어 모든 에피소드가
         GO_NOT_ENGAGED 로 끝난다(실측: mousedown 은 #qrun 에 정확히 꽂히는데
         mouseup 이 안 와서 click 이 합성되지 않음 → runHit=0).
         사람이 쓰는 기본 동작은 그대로다(파라미터 없으면 종전과 동일). */
      if(/[?&]go=1/.test(location.search) && auto.wp.length>1){
        startDrive();
      }
    }catch(e){ console.warn('auto-route', e); }
  }, 1500);
  if(setBtn) setBtn.onclick = ()=>setStart(sBox?sBox.value:'');
  if(sBox) sBox.onkeydown = e=>{ if(e.key==='Enter'){ e.preventDefault(); setStart(sBox.value); } };

  const mdlBtn = document.getElementById('mdlBtn');
  if(mdlBtn) mdlBtn.onclick = ()=> setModel(!MDL.on);   // 모델 주행 ON/OFF (a_5085)
  const parkBtn = document.getElementById('qpark');
  if(parkBtn) parkBtn.onclick = ()=>{
    parkCar();
    if(runBtn) runBtn.disabled = true;      // 경로가 해제되므로 다시 설정해야 한다
  };
  /* ★'목적지 가기' = 실제 출발(u_5041). 경로가 있어야만 동작한다. */
  /* ★출발을 'click' 이벤트에만 의존하지 않는다(u_5126 실측 근거).
     자동 하네스(CGEvent)로 이 버튼을 누르면 mousedown 은 #qrun 에 정확히
     꽂히는데 mouseup 이 오지 않아 click 이 합성되지 않는다 — 실측 evLog:
       pointerdown:224,131>qrun  mousedown:224,131>qrun  (그 다음이 없다)
     같은 패널의 형제 버튼(#qpark)은 down/up/click 이 전부 온다. 즉 좌표도
     히트테스트도 정상이고(4모서리+중앙 전부 elementFromPoint=qrun),
     핸들러도 정상이다(b.click() 은 runHit=1·autoOn=1 로 즉시 성공).
     고장난 것은 이 한 요소의 mouseup 전달뿐이다.
     → click 을 기다리지 않고 pointerdown 에서도 출발시킨다. 사람 조작은
       종전과 똑같고(둘 다 와도 __runBusy 로 한 번만 실행), 자동 하네스는
       up 이 없어도 출발한다. */
  function startDrive(){
    if(window.__runBusy) return;             // click+pointerdown 중복 방지
    window.__runBusy = 1; setTimeout(()=>{ window.__runBusy = 0; }, 300);
    window.__runHit=(window.__runHit||0)+1;   // 핸들러 진입 카운터(u_5126 진단)
    if(runBtn && runBtn.disabled){ window.__runRet='disabled'; return; }
    if(!auto.wp.length){ window.__runRet='nowp'; flash('먼저 경로를 설정하세요'); return; }
    window.__parked=0;                       // 주차 해제
    /* ★차를 경로 위에 올리는 건 '출발하는 순간'이어야 한다(u_5050).
       예전엔 planTo(=경로 설정) 안에서 했다. 그런데 경로 설정과 출발 사이에
       차가 계속 굴러가므로, 출발할 때는 이미 경로에서 멀어져 있다 —
       실측 s=0/4115m, xt=99.9m, df=-155도(경로가 등 뒤). 그러면 아무리
       조향이 맞아도 도달할 수 없고 차는 좌우로 헌팅만 한다(방향 반전 18회).
       출발 버튼을 누른 그 프레임에 경로 시작점·방향으로 정렬한다. */
    if(auto.wp.length>1){
      const a=auto.wp[0], b=auto.wp[1];
      const ang=Math.atan2(b.y-a.y, b.x-a.x);
      me.x=a.x; me.y=a.y; me.ang=ang;
      me.v=0; me.steer=0; me.offroad=0; me.cool=0.8;
      auto.cum=null; auto.s=0; auto.k=1; auto.i=0; auto.stall=0;
      /* ★사고 상태도 같이 턴다(u_5126 소프트리셋).
         이게 남아 있으면 출발하자마자 crashHold 로 다시 굳는다. */
      me.crashes=0; me.dmg=0;
      crashHold=0; crashHoldT=0; crashLit=0; bldStuck=0; blockT=0;
      const _ce=document.getElementById('crash'); if(_ce) _ce.style.opacity=0;
      resetTeacherLane();
      window.__crk={}; window.__lde=[]; window.__otN=0;
    }
    /* ★출발 직후 월드를 차 위치 기준으로 다시 스트리밍한다(u_5111 실사고).
       위에서 차를 경로 시작점으로 순간이동시키는데, 그 지점이 다른 청크면
       다음 프레임의 streamWorld 가 그래프를 통째로 다시 만든다. 그때 경로가
       날아가서 [목적지 가기]를 누르는 순간 wp=0·auto=0 이 됐다
       (실측: 누르기 전 wp_len=59 -> 누른 뒤 wp=0, DRV 가 MODEL 에서 TEACH 로 떨어짐).
       여기서 먼저 스트리밍해 두면 프레임 루프가 다시 만들 일이 없다. */
    try{ if(typeof streamWorld==='function') streamWorld(true); }catch(e){}
    auto.on = 1; window.__runRet='ok'; window.__runOnAt=performance.now(); sync(); flash('목적지로 출발');
  }
  window.__startDrive = startDrive;          // 하네스가 직접 부를 수 있는 경로
  /* ★소프트 리셋(u_5126). 페이지를 다시 안 띄우고 에피소드만 새로 시작한다.
     리로드는 맵·검색인덱스(10MB)를 매번 다시 파싱해 ~50초가 든다 —
     130초 에피소드의 38%. 경로(auto.wp)는 그대로 두고 차만 출발점으로
     되돌리면 되므로, startDrive 가 이미 하는 일이 곧 리셋이다.
     반환값으로 하네스가 성공 여부를 바로 확인한다. */
  window.__softReset = function(){
    /* ★리셋은 '반드시 붙는다'로 만든다(u_5126). 연속 리셋에서 3번째가 실패했는데
       원인은 (a) __runBusy 300ms 창에 걸리거나 (b) 직전 에피소드가 도착 판정으로
       auto.on=0 이 된 직후라 startDrive 가 한 프레임 늦게 먹히는 것이었다.
       둘 다 '한 번 더 부르면 붙는' 성질이라 여기서 확인 후 재시도한다. */
    window.__runBusy = 0;                    // 직전 호출의 중복방지 창을 연다
    window.__runRet = '';
    if(!auto.wp.length) return {ok:0, why:'nowp', wp:0};
    startDrive();
    if(!auto.on){                            // 한 번 더(위 두 원인 모두 1회 재시도로 해소)
      window.__runBusy = 0;
      startDrive();
    }
    return {ok: auto.on?1:0, why: window.__runRet||'', wp: auto.wp.length,
            t: Math.round(performance.now())};
  };
  if(runBtn){
    runBtn.onclick = startDrive;
    runBtn.addEventListener('pointerdown', e=>{ if(e.button===0) startDrive(); });
  }
  /* 입력이 이벤트로 안 잡히는 환경(자동입력 등)을 위해 주기적으로도 확인한다 */
  let lastV = '';
  setInterval(()=>{
    if(document.activeElement !== box) return;
    if(box.value === lastV) return;
    lastV = box.value;
    hits = search(box.value); sel = 0; render();
  }, 300);
  window.__search = search;       // 검증용
  /* 화면에 검색 상태를 띄운다 — 샌드박스라 콘솔을 못 보니 이게 유일한 진단 수단(u_5005) */
  window.__sdbg = ()=>({v:box.value, hits:hits.length, sel:sel,
                        idx:IDX.length, auto:auto.on, wp:auto.wp.length});
})();

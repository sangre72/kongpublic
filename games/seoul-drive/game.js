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
var crashHold=0;   // 사고 정지 상태(화면 빨강 고정)   // ★hardReset()가 먼저 호출되므로 var로 호이스팅(TDZ 방지)
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
function mkBlds(src){return src.map(b=>{
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
  if(s.o){ return (lane+0.5)*LW - s.roadW/2; }      // 일방통행: 전 차로 사용
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
let start=0,_bd=1e18;
for(let i=0;i<segs.length;i++){
  const s=segs[i];if(s.len<20*S)continue;
  const mx=(nodes[s.a].x+nodes[s.b].x)/2,my=(nodes[s.a].y+nodes[s.b].y)/2;
  const d=mx*mx+my*my;if(d<_bd){_bd=d;start=i}
}
function reset(){
  const s=segs[start],A=nodes[s.a],B=nodes[s.b];
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
  }me.v=0;me.dmg=0;me.crashes=0;me.offroad=0;
  auto.on=0;auto.goal=null;auto.wp=[];seed();sync();flash('리셋');
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
function onRoad(x,y){
  const n=nearestSeg(x,y);
  if(!n)return{ok:false,d:1e9,s:null};
  return{ok:n.d<=n.s.roadW*.5,d:n.d,s:n.s,edge:n.d-n.s.roadW*.5};
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
      const si=GSEGS.length; GSEGS.push({a,b,len,l:(r.l||2),o:!!r.o});
      A.e.push(si); B.e.push(si);
    }
  }
  stitchGraph();
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
function gAstar(s,t){
  const G={[s]:0},F={[s]:0},came={},open=[s],seen=new Set();
  const h=(a,b)=>Math.hypot(GNODES[a].x-GNODES[b].x,GNODES[a].y-GNODES[b].y);
  let guard=0;
  while(open.length && guard++<400000){
    open.sort((a,b)=>F[a]-F[b]); const c=open.shift();
    if(c===t){const p=[c];let k=c;while(came[k]!==undefined){k=came[k];p.unshift(k)}return p}
    seen.add(c);
    for(const si of GNODES[c].e){
      /* ★가상간선(stitch)은 실제 도로가 아니다 — 통행비용 40배로 최후수단화(u_5024).
         없으면 '길 없는 곳을 가로지르는' 경로가 최단경로로 선택된다(실측: 6/6 중간점이
         도로에서 median 7.2m·max 12.3m 벗어남). */
      const sg=GSEGS[si], nb=(sg.a===c)?sg.b:sg.a,
            ng=G[c]+sg.len*(sg.v?40:1);
      if(G[nb]===undefined||ng<G[nb]){came[nb]=c;G[nb]=ng;F[nb]=ng+h(nb,t);
        if(!seen.has(nb))open.push(nb)}
    }
  }
  return null;
}
function planTo(x,y){
  buildGlobalGraph();
  let p=null, NS=nodes;
  if(GNODES){                                  // 장거리: 전역 그래프로
    const gp=gAstar(gNearest(me.x,me.y), gNearest(x,y));
    if(gp){ p=gp; NS=GNODES; }
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
  const laneOff=(lanes,oneway)=>{
    if(oneway) return 0.5*LW - (lanes*LW)/2;   // 일방: 가장 오른쪽 차로
    return 0.5*LW;                              // 왕복: 진행방향 1차로
  };
  const edgeOf=(i,j)=>{                         // 두 노드를 잇는 간선 찾기
    if(NS!==GNODES) return null;
    for(const si of GNODES[i].e){
      const sg=GSEGS[si];
      if((sg.a===i&&sg.b===j)||(sg.a===j&&sg.b===i)) return sg;
    }
    return null;
  };
  const wp=[];
  for(let i=0;i<p.length;i++){
    const n=NS[p[i]];
    if(i<p.length-1){
      const m=NS[p[i+1]],a=Math.atan2(m.y-n.y,m.x-n.x);
      const sg=edgeOf(p[i],p[i+1]);
      const off=sg ? laneOff(sg.l||2, sg.o) : LW*.5;
      wp.push({x:n.x-Math.sin(a)*off,y:n.y+Math.cos(a)*off});
    }else wp.push({x:n.x,y:n.y});
  }
  /* ★마지막 지점은 반드시 '도로 위'로 스냅한다(u_4896).
     POI 원점은 건물 안/뒤라서 그대로 두면 경로 마지막 구간이 길이 아닌 곳을 가로지른다. */
  /* ★목적지 스냅은 전역 그래프(GSEGS) 기준으로 한다(u_5024).
     nearestSeg 는 로컬 segs(적재된 청크)만 본다 → 먼 목적지는 '차 근처 도로'로
     스냅돼 마지막 구간이 아무것도 없는 곳을 직선으로 가로질렀다. */
  const nn=gNearestOnRoad(x,y) || nearestSeg(x,y);
  wp.push(nn?{x:nn.px,y:nn.py}:{x,y});
  auto.wp=wp;auto.i=0;auto.goal=wp[wp.length-1];auto.on=1;sync();
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
const KMH=v=>Math.round(v*3.6);
function driveAuto(dt){
  if(!auto.wp.length){auto.act='대기';return}
  const t=auto.wp[auto.i],d=Math.hypot(t.x-me.x,t.y-me.y);
  if(d<4*S){
    if(auto.i<auto.wp.length-1)auto.i++;
    else{me.v*=.82;auto.act='도착';
      if(me.v<.3){me.v=0;auto.on=0;flash('목적지 도착');sync()}return}
  }
  let df=((Math.atan2(t.y-me.y,t.x-me.x)-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
  /* ★경로'선'을 따라간다 — 다음 점만 보고 조향하면 코너를 가로질러 인도로 올라간다.
     실측 계산: 웨이포인트 간격 19m·코너 90°면 안쪽으로 9.5m 파고든다.
     편도2차로 도로 반폭이 약 7m 이므로 그대로 인도 침범이다(화면 확인: road=N).
     그래서 '이전 점→다음 점' 선분에 대한 횡오차(cross-track)를 같이 없앤다. */
  const pv=auto.wp[Math.max(0,auto.i-1)];
  let xt=0;
  {
    const vx=t.x-pv.x, vy=t.y-pv.y, L2=vx*vx+vy*vy;
    if(L2>1){
      const u=Math.max(0,Math.min(1,((me.x-pv.x)*vx+(me.y-pv.y)*vy)/L2));
      const px=pv.x+vx*u, py=pv.y+vy*u;
      // 부호 있는 횡오차: 경로 진행방향 기준 왼쪽(+)/오른쪽(-)
      xt=((me.x-px)*(-vy)+(me.y-py)*vx)/Math.sqrt(L2);
      const seg=((Math.atan2(vy,vx)-me.ang+Math.PI*3)%(Math.PI*2))-Math.PI;
      // 경로 방향 + 횡오차 보정(Stanley 식). 속도가 빠를수록 보정을 약하게.
      df = seg + Math.atan2(-xt*1.6, Math.max(3*S, me.v*S));
      df = ((df+Math.PI*3)%(Math.PI*2))-Math.PI;
    }
  }
  const gp=gap(me),curve=Math.min(1,Math.abs(df)/.8);
  let vmax=14*(1-.62*curve);                       // m/s (≈50km/h)
  if(gp<28*S)vmax=Math.min(vmax,14*(gp-9*S)/(19*S));
  if(gp<11*S)vmax=0;
  if(auto.i>=auto.wp.length-1&&d<22*S)vmax=Math.min(vmax,4);
  me.steer=Math.max(-.9,Math.min(.9,df*2.4));
  me.v+=(vmax-me.v)*Math.min(1,dt*2.0);
  auto.act=gp<11*S?'정지 — 전방 장애물':gp<28*S?'감속 — 차간유지'
    :curve>.4?'선회 중':(auto.i>=auto.wp.length-1&&d<22*S)?'목적지 접근':'주행 중';
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
function respawnOnRoad(){
  /* ★사고 후 도로 복귀. 단순히 제자리에 세우면 같은 건물로 다시 직진해
     무한 충돌한다(실측: 같은 건물에 34회). 그래서:
       - 차로 중앙에 세우고
       - 진행방향을 '도로를 따라' 맞추되
       - 방금 박은 쪽 반대로 조금 물러나 재출발시킨다. */
  const n=nearestSeg(me.x,me.y);
  if(!n)return;
  const sg=n.s;
  const off=laneOffset(sg,1,0);
  // 세그먼트를 따라 조금 뒤로 물린 지점
  const back=Math.min(0.35,(8*S)/Math.max(1,sg.len));
  const t2=Math.max(0,Math.min(1,n.t-back));
  const A=nodes[sg.a],B=nodes[sg.b];
  const px=A.x+(B.x-A.x)*t2, py=A.y+(B.y-A.y)*t2;
  me.x=px-Math.sin(sg.ang)*off;
  me.y=py+Math.cos(sg.ang)*off;
  me.ang=sg.ang;me.v=0;me.offroad=0;me.cool=1.0;
}
function crash(label,heavy){
  if(me.cool>0)return;
  me.cool=.8;me.crashes++;
  /* ★무엇에 부딪히는지 종류별로 센다(u_5025 진단용).
     'cr=8' 만 봐서는 원인을 모른다 — 추돌인지 보행자인지 차로이탈인지에 따라
     고칠 곳이 완전히 다르다. */
  { const k=label.indexOf('추돌')>=0?'추돌'
          : label.indexOf('보행자')>=0?'보행자'
          : label.indexOf('차로')>=0?'차로이탈'
          : label.indexOf('충돌')>=0?'건물':'기타';
    window.__crk=window.__crk||{}; window.__crk[k]=(window.__crk[k]||0)+1; }
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
  /* ★사고가 나도 목적지는 유지한다(u_5024 P2).
     예전엔 여기서 auto.on=0 으로 경로를 버렸다. 그러면 초반에 한 번만 부딪혀도
     안내가 통째로 사라지고, 차는 길잡이 없이 표류한다 — 화면에서 wp=0·auto=0 으로
     확인했다. 사람도 접촉사고가 났다고 목적지를 잊지는 않는다.
     도로로 복귀시킨 뒤 남은 경로를 계속 따라가게 한다. */
  respawnOnRoad();          // 도로로 복귀시켜 다음 시도를 가능하게
  if(auto.on && auto.wp.length){
    // 복귀 지점에서 가장 가까운 웨이포인트로 인덱스를 맞춘다(뒤로 돌아가지 않게)
    let bi=auto.i, bd=1e18;
    for(let i=auto.i;i<auto.wp.length;i++){
      const d=(auto.wp[i].x-me.x)**2+(auto.wp[i].y-me.y)**2;
      if(d<bd){bd=d;bi=i}
    }
    auto.i=bi; sync();
  }
  sync();
}

/* ---------- 물리 ---------- */
const K={};
function step(dt){
  if(crashHold){me.v=0;return}   // 사고 정지 중엔 움직이지 않는다
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
    me.x=px0;me.y=py0;me.ang=pa0;
    const nm=blds[bi].n?blds[bi].n:'건물';
    me.v=0;
    crash(nm+' 충돌',true);
  }
  /* ★차로 밖으로는 '못 나간다' — 물리적 구속(u_5027).
     도로교통법은 절대적이다. 예전엔 인도 침범을 감속+사고기록으로만 처리해서,
     차가 실제로는 인도 위를 계속 굴러다녔다(실측 25초에 사고 8~23회).
     건물은 이미 하드 구속(위치 되돌림)인데 도로만 물렁했던 것이다.
     이제 도로 밖으로 나가는 이동 자체를 무효로 만든다 — 벽과 같은 취급.
     이렇게 하면 어떤 컨트롤러(경로주행·교사·학습모델)를 쓰든 물리적으로
     차로를 벗어날 수 없다. 규칙을 지키길 '기대'하는 대신 못 어기게 만든다. */
  const r=onRoad(me.x,me.y);
  const inPark=PARK.bays.length&&Math.hypot(me.x-PARK.cx,me.y-PARK.cy)<12*S;
  if(!r.ok&&!inPark){
    const r0=onRoad(px0,py0);
    if(r0.ok){
      /* 직전엔 도로 위였다 → 이번 이동이 도로를 벗어나게 했다. 무효화한다.
         진행방향 성분만 죽이고 도로를 따라 미끄러지게 해서 그 자리에 붙어버리지 않게. */
      me.x=px0; me.y=py0;
      me.v*=0.55;
      me.offroad+=dt;
      if(me.offroad>.9){ me.offroad=0; crash('차로 이탈 시도',false); }
    }else{
      /* 이미 도로 밖(사고 직후 등) → 복귀 유도. 여기선 종전대로 감속·기록. */
      me.offroad+=dt;
      me.v*=(1-2.6*dt);
      if(me.offroad>.28){me.offroad=0;
        crash(r.edge>SIDEWALK_M*S?'도로 이탈':'인도 침범',false)}
    }
  }else me.offroad=0;

  for(const c of cars){if(!c.alive)continue;
    if(obb(me,c)){crash(c.n+' 추돌',c.t==='truck')}}
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
    const opts=nodes[nd].e.filter(i=>i!==c.si);
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
  if(auto.on&&auto.wp.length){
    g.strokeStyle=C('--green');g.globalAlpha=.6;g.lineWidth=5;g.setLineDash([4*S,3*S]);
    /* ★경로선은 '경로'만 그린다(u_5031).
       예전엔 nearestSeg(차 위치) 에서 시작해 다음 웨이포인트로 직선을 그었다.
       차가 차로에서 밀려 있으면 그 첫 획이 차로를 가로지르는 긴 대각선이 되어
       '경로가 차로를 무시한다'처럼 보였다 — 실제 경로는 멀쩡한데 그리기가 만든
       착시였다(경로선 13,715점 조밀 검사: 도로 밖 0개).
       이제 웨이포인트만 잇는다. */
    g.beginPath();
    g.moveTo(auto.wp[auto.i].x, auto.wp[auto.i].y);
    for(let i=auto.i;i<auto.wp.length;i++)g.lineTo(auto.wp[i].x,auto.wp[i].y);
    g.stroke();g.setLineDash([]);g.globalAlpha=1;
    g.fillStyle=C('--green');g.beginPath();g.arc(auto.goal.x,auto.goal.y,1.6*S,0,7);g.fill();
  }
  // 가로등
  for(const l of lamps){
    if(!inView(l.x,l.y,0))continue;
    /* ★가로등도 진하게(u_4945) — 연한 노랑 후광이 흰 배경에 묻혔다 */
    g.fillStyle='rgba(255,190,60,.55)';g.beginPath();g.arc(l.x,l.y,2.4*S,0,7);g.fill();
    g.fillStyle=C('--lamp');g.beginPath();g.arc(l.x,l.y,.9*S,0,7);g.fill();
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
    if(auto.on){auto.on=0;sync();flash('수동 전환')}}
  if(e.key==='r'||e.key==='R')reset();
  if(e.key==='h'||e.key==='H')flash('🔊 빵!');
  if(e.key==='+'||e.key==='=')cam.z=Math.min(2.2,cam.z*1.18);
  if(e.key==='-'||e.key==='_')cam.z=Math.max(.45,cam.z/1.18);
});
addEventListener('keyup',e=>K[e.key]=0);
cv.addEventListener('pointerdown',e=>{
  const r=cv.getBoundingClientRect();
  planTo((e.clientX-r.left-W/2)/cam.z+cam.x,(e.clientY-r.top-H/2)/cam.z+cam.y);
  flash('목적지 설정');
});
cv.addEventListener('wheel',e=>{e.preventDefault();
  cam.z=Math.max(.45,Math.min(2.2,cam.z*(e.deltaY<0?1.1:1/1.1)))},{passive:false});
document.getElementById('md').onclick=()=>{
  if(auto.on){auto.on=0;flash('수동 전환')}
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
  /* ★학습모드는 도로 위에서 재시작한다(u_4917).
     여기가 주차칸으로 고정돼 있어 reset()을 고쳐도 매 판 주차칸으로 돌아갔다.
     주차칸은 도로에서 13.3m 떨어져 있어 직진하면 도로에 닿기 전에 이탈 사고. */
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
  if(segs.length){
    /* ★사고 지점 근처 청크로 스트리밍이 바뀌면 옛 start 인덱스는 무효다.
       현재 위치에서 가장 가까운 '충분히 긴' 구간을 새로 고른다. */
    let bs=null,bl=-1;
    for(const q of segs){
      if(q.len < 20*S) continue;
      if(q.len > bl){ bl=q.len; bs=q; }
    }
    if(!bs) bs=segs[0];
    const A2=nodes[bs.a],B2=nodes[bs.b];
    const off2=laneOffset(bs,1,0);
    const t0=0.15;
    me.x=A2.x+(B2.x-A2.x)*t0-Math.sin(bs.ang)*off2;
    me.y=A2.y+(B2.y-A2.y)*t0+Math.cos(bs.ang)*off2;
    me.ang=bs.ang;                       // a→b 진행방향과 동일
    /* ★멀리 순간이동하면 그 구역 청크가 아직 없어 road=N 이 된다(실측 d=13.2m).
       스폰 직후 강제로 월드를 다시 스트리밍해 도로·신호등을 채운다. */
    try{ if(typeof streamWorld==='function') streamWorld(true); }catch(e){}
  }else if(PARK.bays.length){const b=PARK.bays[2];me.x=b.x;me.y=b.y;me.ang=PARK.ang}
  me.v=0;me.dmg=0;me.crashes=0;me.offroad=0;me.cool=0;
  auto.on=0;auto.wp=[];auto.i=0;
  streamWorld(true);
}
function epTick(dt){
  if(!LEARN||EP.state!=='run')return;
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
  const R=54,cx=Math.min(W-R-10,W*0.72),cy=R+12;
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
  if(auto.on && auto.wp.length){
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
        /* ★교사의 '정지' 지시만 받는다(u_5026 실측 수정).
           처음엔 thr 까지 받아 속도를 통째로 덮어썼는데, 경로주행의 가감속과
           교사의 목표속도가 매 프레임 싸워서 오히려 사고가 늘었다
           (실측: 25초 사고 8회 → 30초 23회). 되돌리고 '멈춰야 할 때 멈춘다'만
           남긴다 — 빨간불·앞차·보행자가 여기에 해당한다. */
        if(a && a.ok!==false && a.brake>0.5){
          me.v -= me.v*Math.min(1, dt*3.2*a.brake);
          if(a.brake>=1) me.v=Math.min(me.v, 0.4);
        }
      }catch(e){}
    }
  }else if(T && T.auto){
    T.last = T.drive(dt);                           // 경로 없음 = 교사가 조종
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
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

/* ===== 학습 모드 초기화 — 모든 정의가 끝난 뒤 실행(TDZ 방지) ===== */
function setLearn(v){
  LEARN=v;
  if(LEARN){hardReset();epStart();flash('학습 모드 시작')}
  else{EP.state='idle';flash('학습 모드 종료')}
}
addEventListener('keydown',e=>{if(e.key==='l'||e.key==='L')setLearn(!LEARN)});
if(LEARN){hardReset();epStart()}
/* ★검증 빌드(교사 OFF)는 LEARN 이 아니라서 hardReset() 이 한 번도 안 불렸고,
   차가 초기 주차칸(도로 밖 13.3m)에 그대로 서 있었다(실측 readout: road=N d=13.3m).
   모델이 앞으로 가도 도로가 없으니 당연히 주행이 안 된다. */
/* ★모든 빌드에서 도로 위 출발(2026-09-14 u_4950 후속).
   __SPAWN_ON_ROAD 는 --teacher-off 빌드에만 주입돼서, 교사 빌드(수집용)는
   hardReset() 이 아예 안 불리고 초기 주차칸 위치가 그대로 남았다.
   실측: 디코더로 읽은 lane=13.0m, on_road=0 — 도로 밖에서 수집하고 있었다. */
else { hardReset(); }

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
      d.onclick = ()=>{ sel=i; pick(); };
      res.appendChild(d);
    });
  }

  function pick(){
    const r = hits[sel]; if(!r) return;
    /* 건물 중심으로 바로 planTo 하면 '도로가 아닌 곳'을 목적지로 잡는다.
       가장 가까운 도로 위 지점으로 옮긴다. */
    const n = nearestSeg(r.x*S, r.y*S);
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
      pick(); e.preventDefault();
    }
    else if(e.key==='Escape'){ res.innerHTML=''; box.blur(); }
    e.stopPropagation();          // 방향키가 주행 조작으로 새지 않게
  };
  /* ★[출발]은 드롭다운 상태에 기대지 않는다(u_5003 실측).
     자동 타이핑에서는 oninput 이 안 뜨는 경우가 있어 hits 가 빈 채로 남는다.
     누를 때마다 입력값으로 새로 검색해서 첫 결과로 간다 — 사람이 쳐도 같은 동작. */
  if(go) go.onclick = ()=>{
    window.__goHit = (window.__goHit||0)+1;      // 버튼이 눌렸는지 화면으로 확인
    hits = search(box.value);
    if(!hits.length){ flash('검색 결과 없음: '+box.value); return; }
    sel = 0; pick();
  };
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

/* ★u_5809 MINIMAL LICENCE-TEST COURSE (owner-scoped: S-curve + straight + acceleration ONLY).
   Dimensions are verbatim from 도로교통법 시행규칙 [별표 23] (제65조), 개정 2021.12.31, read from
   the law.go.kr source PDF - not from a search summary:
     굴절코스(S): 폭 4.7m, 모퉁이 사이 길이 15.0m, 출입구쪽 길이 6.0m, 모퉁이 반경 1.5m, 2분 이내
     가속코스  : 직선 40m, 자동변속기는 시작~종료 20km/h 이상 유지
     검지선    : 황색실선 10~15cm, 바퀴가 접촉하면 감점(차로준수)
   Loaded ONLY with ?course=1. It builds its own geometry in a blank world and never reads or
   writes the scoped map, the router, or any existing route. */
(function(){
  if(!/[?&]course=1/.test(location.search)) return;
  const M = (typeof S==='number'? S : 6.0);          // px per metre
  const LANE_W = 4.7, GAP = 15.0, MOUTH = 6.0, R = 1.5;   // 굴절코스
  const ACC_LEN = 40.0, ACC_MIN_KMH = 20.0;               // 가속코스
  const STRAIGHT = 30.0;                                   // 직선 구간(요소 3)
  const ORIGIN = {x: 0, y: 0};

  // Centreline: straight -> S (two opposite bends) -> acceleration straight.
  // Built as a polyline in metres, then scaled to px. Left/right detection lines are offset +-w/2.
  function build(){
    const P=[]; let x=0, y=0;
    const push=(px,py,tag)=>P.push({x:px,y:py,tag});
    for(let s=0;s<=STRAIGHT;s+=1) push(x, y-s, 'straight');
    y-=STRAIGHT;
    // S-curve: right bend then left bend, each a quarter-ish arc of radius R around the mouth
    const seg=(dir)=>{
      for(let a=0;a<=90;a+=3){
        const t=a*Math.PI/180;
        push(x+dir*R*(1-Math.cos(t)), y-R*Math.sin(t), 'scurve');
      }
      x+=dir*R; y-=R;
      for(let s=0;s<=GAP/2;s+=1){ push(x+dir*s*0, y-s, 'scurve'); }
      y-=GAP/2;
    };
    seg(+1); seg(-1);
    for(let s=0;s<=MOUTH;s+=1) push(x, y-s, 'scurve');
    y-=MOUTH;
    for(let s=0;s<=ACC_LEN;s+=1) push(x, y-s, 'accel');
    return P;
  }
  const PTS = build();
  const W_HALF = LANE_W/2;

  function nearest(px,py){
    let best=null, bd=1e18;
    for(let i=0;i<PTS.length;i++){
      const dx=px/M-PTS[i].x, dy=py/M-PTS[i].y, d=dx*dx+dy*dy;
      if(d<bd){ bd=d; best=i; }
    }
    return {i:best, d:Math.sqrt(bd), p:PTS[best]};
  }

  const ST = window.__course = {
    on:1, t0:0, started:0, done:0,
    elements:{ straight:{pass:null,touch:0}, scurve:{pass:null,touch:0}, accel:{pass:null,touch:0,vmax:0} },
    touchN:0, stallN:0, timeLimit:120, vmaxKmh:0, elapsed:0, result:null, pts:PTS.length
  };

  window.__courseStart = function(){
    const p0=PTS[0], p1=PTS[1];
    me.x=p0.x*M; me.y=p0.y*M; me.ang=Math.atan2(p1.y-p0.y, p1.x-p0.x);
    me.v=0; me.steer=0; me.offroad=0; window.__parked=0;
    ST.t0=performance.now(); ST.started=1; ST.done=0; ST.result=null; ST.touchN=0; ST.stallN=0;
    for(const k in ST.elements){ ST.elements[k].pass=null; ST.elements[k].touch=0; }
    ST.elements.accel.vmax=0;
  };

  window.__courseTick = function(dt){
    if(!ST.started || ST.done) return;
    ST.elapsed = (performance.now()-ST.t0)/1000;
    const n = nearest(me.x, me.y);
    const el = n.p.tag, E = ST.elements[el];
    const kmh = Math.abs(me.v)*3.6;
    ST.vmaxKmh = Math.max(ST.vmaxKmh, kmh);
    if(el==='accel') E.vmax = Math.max(E.vmax, kmh);
    // line contact: the detection line is at +-LANE_W/2 from the centreline
    if(n.d > W_HALF){ E.touch++; ST.touchN++; }
    // stall: stopped for over 3s after the start
    if(kmh < 1 && ST.elapsed > 3){ ST.stallN++; } else { ST.stallN = 0; }
    const lastIdx = PTS.length-1;
    if(n.i >= lastIdx-1){                       // completed
      ST.done=1;
      ST.elements.straight.pass = ST.elements.straight.touch===0;
      ST.elements.scurve.pass   = ST.elements.scurve.touch===0;
      ST.elements.accel.pass    = (ST.elements.accel.touch===0 && ST.elements.accel.vmax>=ACC_MIN_KMH);
      ST.result = (ST.elements.straight.pass && ST.elements.scurve.pass && ST.elements.accel.pass
                   && ST.elapsed<=ST.timeLimit && ST.stallN<180) ? 'PASS' : 'FAIL';
    } else if(ST.elapsed > ST.timeLimit || ST.stallN > 180){
      ST.done=1; ST.result='FAIL';
      for(const k in ST.elements) if(ST.elements[k].pass===null) ST.elements[k].pass=false;
    }
  };

  window.__courseDraw = function(g){
    g.save();
    g.strokeStyle='#e8c33a'; g.lineWidth=0.12*M;      // 황색실선 10~15cm
    for(const sgn of [-1,1]){
      g.beginPath();
      for(let i=0;i<PTS.length;i++){
        const a=PTS[Math.max(0,i-1)], b=PTS[i];
        const dx=b.x-a.x, dy=b.y-a.y, L=Math.hypot(dx,dy)||1;
        const nx=-dy/L, ny=dx/L;
        const px=(b.x+nx*sgn*W_HALF)*M, py=(b.y+ny*sgn*W_HALF)*M;
        i?g.lineTo(px,py):g.moveTo(px,py);
      }
      g.stroke();
    }
    g.strokeStyle='rgba(255,255,255,.25)'; g.lineWidth=0.08*M; g.setLineDash([2*M,2*M]);
    g.beginPath();
    PTS.forEach((p,i)=> i?g.lineTo(p.x*M,p.y*M):g.moveTo(p.x*M,p.y*M));
    g.stroke(); g.setLineDash([]);
    g.restore();
  };
})();

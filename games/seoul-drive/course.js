/* ★u_5813 CURRICULUM COURSE GENERATOR (owner: turn angles 70/80/90/100 both directions, S-curve
   variants, simplest first). A course is a CONFIG, not new code per variant.

   Dimensions grounded in 도로교통법 시행규칙 [별표 23] (제65조), 개정 2021.12.31 (law.go.kr PDF):
     굴절코스 width 4.7m, corner radius 1.5m, corner-to-corner 15.0m, mouth 6.0m, 2-minute limit
     가속코스 40m straight, automatic transmission: hold >=20km/h
     detection line = yellow solid 10-15cm; any wheel touching it is a fault
   The statute's 1.5m corner radius is a LOW-SPEED crank for the 기능시험; our car's minimum turning
   radius is ~4.4m (wheelbase 2.76 / tan(0.9*0.62)), so stage 1 deliberately uses a generous radius
   and narrows it as a later stage. That is the curriculum, not a deviation from the spec.

   URL: ?course=1                 -> stage 1 default (single 90deg right turn, wide, generous R)
        ?course=1&cturn=90&cdir=R&cradius=12&cwidth=6.0&centry=30&cexit=30
        ?course=1&cs=1            -> S-curve variant (two opposite bends)
        ?cseed= is unused: the generator is deterministic, so every rep drives the identical course. */
(function(){
  if(!/[?&]course=1/.test(location.search)) return;
  const M = (typeof S==='number'? S : 6.0);
  const q = new URLSearchParams(location.search);
  const num=(k,d)=>{ const v=parseFloat(q.get(k)); return isFinite(v)? v : d; };

  const CFG = window.__courseCfg = {
    turn:   num('cturn', 90),            // turn angle in degrees
    dir:    (q.get('cdir')==='L' ? -1 : 1),
    radius: num('cradius', 12.0),        // centreline radius, m  (stage 1 = generous)
    width:  num('cwidth', 6.0),          // lane width, m         (stage 1 = wide; statute 4.7)
    entry:  num('centry', 30.0),         // straight before the turn, m
    exit:   num('cexit', 30.0),          // straight after the turn, m
    scurve: q.get('cs')==='1' ? 1 : 0,   // S variant: turn one way then the other
    limit:  num('climit', 120),          // seconds
    accel:  num('caccel', 0)             // append a 40m acceleration leg (>=20km/h) when 1
  };
  const ACC_LEN=40.0, ACC_MIN_KMH=20.0;

  /* Centreline as a metre-space polyline. Heading starts at -Y (screen up) and the arc turns by
     CFG.turn; an S repeats the arc with the sign flipped. Step 0.5m so the nearest-point search
     resolves lane departure to well under the lane width. */
  function build(){
    const P=[]; let x=0,y=0,h=-Math.PI/2, tag='straight';
    const step=(n,t)=>{ for(let s=0;s<n;s+=0.5){ x+=Math.cos(h)*0.5; y+=Math.sin(h)*0.5; P.push({x,y,tag:t}); } };
    const arc=(deg,dir,R,t)=>{
      const total=deg*Math.PI/180, ds=0.5/R;
      for(let a=0;a<total;a+=ds){ h+=dir*ds; x+=Math.cos(h)*0.5; y+=Math.sin(h)*0.5; P.push({x,y,tag:t}); }
    };
    P.push({x,y,tag});
    step(CFG.entry,'straight');
    arc(CFG.turn, CFG.dir, CFG.radius, 'turn');
    if(CFG.scurve){ step(Math.max(6, CFG.radius), 'straight'); arc(CFG.turn, -CFG.dir, CFG.radius, 'turn2'); }
    step(CFG.exit,'straight');
    if(CFG.accel) step(ACC_LEN,'accel');
    return P;
  }
  const PTS=build(), HALF=CFG.width/2;
  window.__coursePts = PTS;   // u_5815: shared with the standalone page's heading term

  function nearest(px,py){
    let bi=0,bd=1e18; const mx=px/M,my=py/M;
    for(let i=0;i<PTS.length;i++){ const dx=mx-PTS[i].x,dy=my-PTS[i].y,d=dx*dx+dy*dy; if(d<bd){bd=d;bi=i;} }
    return {i:bi,d:Math.sqrt(bd),p:PTS[bi]};
  }

  const EL=()=>{ const o={}; for(const t of ['straight','turn','turn2','accel']) o[t]={pass:null,touch:0,seen:0,maxDev:0}; return o; };
  const ST = window.__course = { on:1, cfg:CFG, pts:PTS.length, started:0, done:0,
    elements:EL(), touchN:0, stallN:0, elapsed:0, timeLimit:CFG.limit, vmaxKmh:0, accelVmax:0,
    progress:0, result:null };

  window.__courseStart = function(){
    const p0=PTS[0],p1=PTS[2]||PTS[1];
    me.x=p0.x*M; me.y=p0.y*M; me.ang=Math.atan2(p1.y-p0.y,p1.x-p0.x);
    me.v=0; me.steer=0; me.offroad=0; window.__parked=0;
    /* Install the course centreline AS THE ROUTE so the rule follower (driveAuto / Pure-Pursuit)
       drives the course itself. Without this the page keeps whatever map route it planned and the
       car would follow that instead - measured: wpLen 635 from the scoped map with ?course=1. */
    const wp=[]; 
    for(let i=0;i<PTS.length;i++){
      const a=PTS[Math.max(0,i-1)], b=PTS[i];
      const ang=Math.atan2(b.y-a.y, b.x-a.x);
      wp.push({x:b.x*M, y:b.y*M, sg:{ang:ang, roadW:CFG.width*M, l:1, o:0, w:-1, lf:1, lb:0}});
    }
    auto.wp=wp; auto.i=0; auto.on=1; auto.goal={x:wp[wp.length-1].x, y:wp[wp.length-1].y};
    window.__courseRoute=1; ST.routeInstalled=auto.wp.length;
    ST.started=1; ST.done=0; ST.result=null; ST.touchN=0; ST.stallN=0; ST.vmaxKmh=0; ST.accelVmax=0;
    ST.elements=EL(); ST.t0=performance.now(); ST.maxIdx=0;
    ST.score=0; ST.cleanSec=0; ST.lineSec=0; ST.wallSec=0; ST._lastT=performance.now();
    ST.wallN=0; ST.lineN=0; ST.endWallN=0; ST.cornerMaxDev=0; ST.finishT=0; ST.stopDist=null; ST.failWhy=null; ST.visited=0;
  };

  /* ★u_5816 SCORING. Owner: per-tick reward while clean, scaled by SPEED; penalties on wall and on
     line contact; cumulative score reported next to pass/fail.
     NORMALISATION: the owner said 'every 0.01s', but our frame tick is ~30-60fps and varies, so a
     per-FRAME score would pay a fast machine more than a slow one for identical driving. We
     integrate per SECOND instead: score += rate * dt, with dt the real elapsed frame time. The
     numbers below are therefore per-second and frame-rate independent.
       clean driving : +1.0 * (v / V_REF) per second      V_REF = 8.33 m/s (30km/h)
       line contact  : -20.0 per second in contact
       wall/off-course: -50.0 per second beyond 2x lane half-width (our 'wall')
       stall          :  0 (standing still earns nothing - no penalty needed, it simply scores 0) */
  const V_REF=8.33, R_CLEAN=1.0, P_LINE=20.0, P_WALL=50.0;
  /* ★u_5823 STRICT JUDGE (owner watched the video: the car hit the course END and was judged PASS).
     Old judge had three holes: (1) contact tested the car CENTRE only, so a body corner could cross a
     line unseen; (2) there was no end boundary at all; (3) judging stopped at 'done', which fired the
     moment the centre reached the last point - the car then rolled on past the end unjudged.
     New rules:
       - contact = any of the 4 body CORNERS: line = corner beyond HALF from the centreline,
         wall = corner beyond 2*HALF (off-course) OR corner past the END WALL (plane through the last
         centreline point, perpendicular to the final heading).
       - FINISH LINE sits FIN_BEFORE metres before the end wall; the run must cross it and then STOP
         (|v|<0.1) before the wall. Judging and scoring stay active until that stop (or timeout).
       - result: any wall contact = FAIL, any line contact = FAIL, regardless of score.
       - end-wall contact stops the car dead (crash), so it is visible on screen.
     Proof-of-travel self-check (PLAN_ODE standing rule): a car parked against the end wall has a
     corner past the wall -> wallN>0 -> FAIL; a car far off the course never visits the start ->
     not scored, never finishes -> FAIL at timeout. */
  const FIN_BEFORE = 8.0, L_IDX = PTS.length-1;
  const PL = PTS[L_IDX], PL0 = PTS[L_IDX-1], HL = Math.atan2(PL.y-PL0.y, PL.x-PL0.x);
  const P0 = PTS[0], H0 = Math.atan2(PTS[1].y-P0.y, PTS[1].x-P0.x);
  const FIN_IDX = Math.max(0, L_IDX - Math.round(FIN_BEFORE/0.5));
  window.__courseEndGeom = {finBefore:FIN_BEFORE, hl:HL, end:{x:PL.x,y:PL.y}};
  function corners(){
    const cx=me.x/M, cy=me.y/M, h=me.ang, fx=Math.cos(h), fy=Math.sin(h), rx=-Math.sin(h), ry=Math.cos(h);
    const a=(me.hm||4.6)/2, b=(me.wm||1.8)/2, C=[];
    for(const sf of [1,-1]) for(const sr of [1,-1]) C.push({x:cx+fx*a*sf+rx*b*sr, y:cy+fy*a*sf+ry*b*sr});
    return C;
  }
  function pastEnd(q){ return (q.x-PL.x)*Math.cos(HL)+(q.y-PL.y)*Math.sin(HL); }   // >0 = beyond the end wall
  /* centre's along-track distance to the end wall (m); used by the Layer-1 stop in the page */
  window.__courseEndDist = function(){ const n=nearest(me.x,me.y); return n.i<L_IDX ? (L_IDX-n.i)*0.5 : -pastEnd({x:me.x/M,y:me.y/M}); };
  window.__courseTick = function(){
    if(!ST.started||ST.done) return;
    const _now=performance.now();
    const _dt=Math.max(0, Math.min(0.1, (_now-(ST._lastT||_now))/1000)); ST._lastT=_now;
    ST.elapsed=(_now-ST.t0)/1000;
    const n=nearest(me.x,me.y), E=ST.elements[n.p.tag]; if(!E) return;
    if(n.d>HALF*4 && !ST.visited) return;   // not on the course yet: do not score
    ST.visited=1;
    const kmh=Math.abs(me.v)*3.6;
    ST.vmaxKmh=Math.max(ST.vmaxKmh,kmh); ST.progress=+(n.i/(PTS.length-1)).toFixed(3);
    E.seen++; E.maxDev=Math.max(E.maxDev,+n.d.toFixed(3));
    if(n.p.tag==='accel') ST.accelVmax=Math.max(ST.accelVmax,kmh);
    /* body-corner contact */
    let dmax=0, endHit=0;
    for(const q of corners()){
      const pe=pastEnd(q); if(pe>0) endHit=1;
      const nq=nearest(q.x*M,q.y*M);
      /* beyond either END of the polyline the nearest point is the endpoint, so nq.d would include the
         along-track gap (rear corners sit 2.3m behind the start at t=0 -> false 2.47m). Use lateral only. */
      const ps=(q.x-P0.x)*Math.cos(H0)+(q.y-P0.y)*Math.sin(H0);
      const d = (nq.i===L_IDX && pe>0) ? Math.abs((q.x-PL.x)*(-Math.sin(HL))+(q.y-PL.y)*Math.cos(HL))
              : (nq.i===0 && ps<0) ? Math.abs((q.x-P0.x)*(-Math.sin(H0))+(q.y-P0.y)*Math.cos(H0)) : nq.d;
      dmax=Math.max(dmax,d);
    }
    const wall = endHit || dmax>HALF*2, line = !wall && dmax>HALF;
    ST.cornerMaxDev=Math.max(ST.cornerMaxDev||0,+dmax.toFixed(3));
    if(endHit){ ST.endWallN=(ST.endWallN|0)+1; me.v=0; }                    // crash into the end wall
    if(wall) ST.wallN=(ST.wallN|0)+1;
    if(line) ST.lineN=(ST.lineN|0)+1;
    /* scoring (per second, unchanged rates), now on body contact */
    const _v=Math.abs(me.v);
    if(wall){ ST.score -= P_WALL*_dt; ST.wallSec=(ST.wallSec||0)+_dt; }
    else if(line){ ST.score -= P_LINE*_dt; ST.lineSec=(ST.lineSec||0)+_dt; }
    else { ST.score += R_CLEAN*(_v/V_REF)*_dt; ST.cleanSec=(ST.cleanSec||0)+_dt; }
    ST.score=+ST.score.toFixed(3);
    if(wall||line){ E.touch++; ST.touchN++; }
    ST.stallN = (kmh<1 && ST.elapsed>3) ? ST.stallN+1 : 0;
    if(n.d<=HALF*2) ST.maxIdx=Math.max(ST.maxIdx|0, n.i);
    /* finish = crossed the finish line (proof of travel: visited start + monotone progress) THEN stopped */
    const crossed = (ST.maxIdx|0)>=FIN_IDX && (ST.elements.straight.seen||0)>10;
    if(crossed && !ST.finishT) ST.finishT=ST.elapsed;
    const stopped = crossed && _v<0.1;
    const over = ST.elapsed>ST.timeLimit || (!crossed && ST.stallN>180);
    if(stopped || over){
      ST.done=1; ST.stopDist=+window.__courseEndDist().toFixed(2);
      for(const t in ST.elements){ const e=ST.elements[t];
        e.pass = e.seen===0 ? null : (e.touch===0 && !over); }
      if(CFG.accel && ST.elements.accel.seen) ST.elements.accel.pass = ST.elements.accel.pass && ST.accelVmax>=ACC_MIN_KMH;
      const req=Object.values(ST.elements).filter(e=>e.pass!==null);
      ST.failWhy = over ? 'timeout' : (ST.wallN ? 'wall' : (ST.lineN ? 'line' : null));
      ST.result=(!over && !ST.wallN && !ST.lineN && req.length && req.every(e=>e.pass)) ? 'PASS':'FAIL';
    }
  };

  /* Auto-start once the page is live. MEASURED: a single 800ms timer fired BEFORE the page's own
     init finished, which then reset the car to a map position (10969,-5414) and re-planned its own
     route (wpLen 635) - the course was loaded but nothing drove it. Re-assert until the car is
     actually on the course and our route is the one installed. */
  (function arm(){
    let tries=0;
    const iv=setInterval(function(){
      tries++;
      try{
        const at = Math.hypot(me.x/M-PTS[0].x, me.y/M-PTS[0].y) < 3;
        if(at && auto.wp.length===PTS.length && auto.on){ clearInterval(iv); return; }
        window.__courseStart();
      }catch(e){}
      if(tries>60) clearInterval(iv);
    }, 400);
  })();

  window.__courseDraw = function(g){
    g.save();
    g.strokeStyle='#e8c33a'; g.lineWidth=0.12*M;
    for(const sgn of [-1,1]){ g.beginPath();
      for(let i=1;i<PTS.length;i++){ const a=PTS[i-1],b=PTS[i];
        const dx=b.x-a.x,dy=b.y-a.y,L=Math.hypot(dx,dy)||1, nx=-dy/L,ny=dx/L;
        const px=(b.x+nx*sgn*HALF)*M, py=(b.y+ny*sgn*HALF)*M;
        i===1?g.moveTo(px,py):g.lineTo(px,py); }
      g.stroke(); }
    g.strokeStyle='rgba(255,255,255,.25)'; g.lineWidth=0.08*M; g.setLineDash([2*M,2*M]);
    g.beginPath(); PTS.forEach((p,i)=> i?g.lineTo(p.x*M,p.y*M):g.moveTo(p.x*M,p.y*M)); g.stroke();
    g.setLineDash([]);
    /* u_5823: END WALL (solid, red-grey) and FINISH LINE (white) are drawn - the model sees them */
    const nx=-Math.sin(HL), ny=Math.cos(HL), W2=HALF*2;
    g.strokeStyle='#c8453c'; g.lineWidth=0.6*M; g.beginPath();
    g.moveTo((PL.x+nx*W2)*M,(PL.y+ny*W2)*M); g.lineTo((PL.x-nx*W2)*M,(PL.y-ny*W2)*M); g.stroke();
    const PF=PTS[FIN_IDX]; g.strokeStyle='rgba(255,255,255,.8)'; g.lineWidth=0.15*M; g.beginPath();
    g.moveTo((PF.x+nx*HALF)*M,(PF.y+ny*HALF)*M); g.lineTo((PF.x-nx*HALF)*M,(PF.y-ny*HALF)*M); g.stroke();
    g.restore();
  };
})();

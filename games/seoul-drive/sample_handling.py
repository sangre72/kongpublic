#!/usr/bin/env python3
"""주행 실측 샘플러 (u_5352/u_5353): 커브·왕복2차로 핸들링 + 추월 미발동 사유.
정상 프레임은 저장하지 않고 집계만 남긴다.
사용: python3 sample_handling.py <초> "<출발>><도착>" """
import json, sys, time, subprocess, urllib.request, urllib.parse, os, collections, statistics as st
BASE=os.path.dirname(os.path.abspath(__file__))
def tel():
    try:
        d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=3)); t=d.get('top',d); ch=d.get('tch') or {}
        return t,ch,(ch.get('g2') or {}),(t.get('da') or {})
    except Exception: return None,None,None,None
secs=float(sys.argv[1]); a,b=sys.argv[2].split('>')
url='http://localhost:8901/index.html?go=1&from='+urllib.parse.quote(a)+'&to='+urllib.parse.quote(b)
r=subprocess.run(['bash',f'{BASE}/reload.sh',url,'120'],capture_output=True,text=True,timeout=300)
if r.returncode!=0: print('reload_fail'); sys.exit(1)
otWhy=collections.Counter(); otOn=0; leadClose=0
curve=[]; straight=[]; two=[]; frames=0; t0=time.time()
while time.time()-t0<secs:
    t,ch,g,da=tel()
    if not t: time.sleep(0.3); continue
    frames+=1
    v=t.get('v') or 0
    if v>2:
        xt=abs(da.get('xt') or 0); nlat=g.get('nlat'); rw=g.get('roadW'); o=g.get('o')
        vc=da.get('vc'); curving = vc is not None and vc < 13.5     # 곡률로 속도가 눌린 구간
        (curve if curving else straight).append(xt)
        if rw==6.5 and not o: two.append((xt, nlat if nlat is not None else float('nan'), g.get('nd')))
    gap=ch.get('gap'); 
    if gap is not None and gap<25: leadClose+=1; otWhy[str(ch.get('otWhy'))]+=1
    if (t.get('prog') or 0)>0.97: break
    time.sleep(0.25)
def q(xs,p): 
    xs=sorted(x for x in xs if x==x); 
    return round(xs[int(len(xs)*p)],2) if xs else None
out={'route':sys.argv[2],'frames':frames,
 'curve_xt':{'n':len(curve),'med':q(curve,.5),'p90':q(curve,.9),'max':q(curve,.999)},
 'straight_xt':{'n':len(straight),'med':q(straight,.5),'p90':q(straight,.9),'max':q(straight,.999)},
 'twolane_6.5':{'n':len(two),'xt_med':q([x for x,_,_ in two],.5),'xt_p90':q([x for x,_,_ in two],.9),
                'nlat_med':q([n for _,n,_ in two],.5),'nlat_min':q([n for _,n,_ in two],.001),'nd_med':q([d for _,_,d in two],.5)},
 'overtake':{'lead_close_frames':leadClose,'veto_reasons':dict(otWhy.most_common(8))},
 'cr':t.get('cr'),'tpN':t.get('tpN')}
print(json.dumps(out,ensure_ascii=False))

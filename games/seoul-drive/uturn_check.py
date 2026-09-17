#!/usr/bin/env python3
"""유턴 검증(u_5256/u_5259): 경로에 유턴 홉이 있는지, 유턴 직전 30m 에서 몇 차로였는지.
사용: python3 uturn_check.py <출발> <도착> [초]"""
import json, subprocess, sys, time, urllib.request, urllib.parse
def tel():
    try: return json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
    except Exception: return None
here=__file__.rsplit('/',1)[0]
a,b=sys.argv[1],sys.argv[2]; secs=float(sys.argv[3]) if len(sys.argv)>3 else 300
url='http://localhost:8901/index.html?go=1&from='+urllib.parse.quote(a)+'&to='+urllib.parse.quote(b)
r=subprocess.run(['bash',here+'/reload.sh',url,'120'],capture_output=True,text=True,timeout=300)
if r.returncode!=0: print(json.dumps({'reload_fail':r.stdout[-200:]},ensure_ascii=False)); sys.exit(1)
d=tel() or {}; t=d.get('top',d); w=t.get('wpDbg') or {}
pts=w.get('uturnPts') or []
print(json.dumps({'route':a+'→'+b,'routeM':t.get('routeM'),'uturnHops':w.get('uturnHops'),'uturnPts':pts},ensure_ascii=False),flush=True)
if not pts: sys.exit(0)
seen={}; t0=time.time(); cr0=None
while time.time()-t0<secs:
    d=tel()
    if not d: time.sleep(0.3); continue
    t=d.get('top',d); g=(d.get('tch') or {}).get('g2') or {}
    cx,cy=(t.get('carX'),t.get('carY')) if t.get('carX') is not None else (None,None)
    wd=t.get('wpDbg') or {}; car=wd.get('car')
    if car and cx is None: cx,cy=car[0],car[1]
    if cx is None: time.sleep(0.3); continue
    for i,p in enumerate(pts):
        dm=((cx-p['x'])**2+(cy-p['y'])**2)**0.5
        if 8<dm<30 and g.get('laneF') is not None:
            seen.setdefault(i,[]).append((round(dm),g.get('laneF'),g.get('nl'),g.get('aTurn'),g.get('fin')))
    if t.get('prog',0)>0.97: break
    time.sleep(0.25)
for i,v in seen.items():
    lanes=[x[1] for x in v]
    print(json.dumps({'uturn':i,'pt':pts[i],'samples':len(v),'laneF_med':sorted(lanes)[len(lanes)//2],'laneF_max':max(lanes),'nl':v[-1][2],'aTurn':v[-1][3],'fin':v[-1][4]},ensure_ascii=False))
print(json.dumps({'done':True,'prog':(tel() or {}).get('top',{}).get('prog'),'cr':(tel() or {}).get('top',{}).get('cr'),'measured':len(seen),'of':len(pts)}))

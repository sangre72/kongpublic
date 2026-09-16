#!/usr/bin/env python3
"""기하 컨트롤러(GEOM) 기준선 — DAgger 가 흉내낼 교사의 실제 성적.
모델을 끄고 같은 프로토콜(소프트리셋 + N초)로 잰다."""
import json, sys, time, urllib.request, subprocess
TEL='http://localhost:8901/tel'; CTL='http://localhost:8901/ctl'
def tel():
    try: return json.load(urllib.request.urlopen(TEL,timeout=3))
    except Exception: return None
def post(d):
    try:
        urllib.request.urlopen(urllib.request.Request(CTL,json.dumps(d).encode(),
            {'Content-Type':'application/json'}),timeout=1.5).read()
    except Exception: pass
def main(eps, secs):
    subprocess.run(['open','-a','Google Chrome'],capture_output=True); time.sleep(2)
    R=[]
    for i in range(int(eps)):
        post({'on':0,'release':1,'steer':0,'thr':0,'brake':0})   # 모델 OFF -> GEOM
        post({'reset':1}); time.sleep(1.5)
        d0=tel() or {}; cr0=int(d0.get('cr') or 0); pmax=0.0; t0=time.time()
        while time.time()-t0<float(secs):
            d=tel()
            if d:
                pmax=max(pmax,float(d.get('prog') or 0))
                if float(d.get('prog') or 0)>=0.95: break
            time.sleep(1)
        dl=tel() or {}
        r={'ep':i+1,'drv':dl.get('drv'),'prog_max':round(pmax,4),
           'crashes':int(dl.get('cr') or 0)-cr0}
        R.append(r); print(json.dumps(r),flush=True)
    import statistics as st
    print(json.dumps({'GEOM_prog_max_mean':round(st.mean(x['prog_max'] for x in R),4),
                      'GEOM_crashes_mean':round(st.mean(x['crashes'] for x in R),2)}))
if __name__=='__main__': main(sys.argv[1],sys.argv[2])

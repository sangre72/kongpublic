#!/usr/bin/env python3
"""u_5261 문제 구간 집중 확인. 구간별로 reload → secs 초 주행 → 순간이동/중앙선구속/사고 집계.
순간이동이 생기는 순간 화면을 캡처해 둔다(원인 확인용).
사용: python3 focus_test.py <초> "출발>도착" ["출발>도착" ...]"""
import json, subprocess, sys, time, urllib.request, urllib.parse
OUTD='/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp'
def tel():
    try:
        d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=3)); t=d.get('top',d); t['_tch']={k:(d.get('tch') or {}).get(k) for k in ('gap','ped','sig','sigStop','cap','br','th')}; return t, (d.get('tch') or {}).get('g2') or {}
    except Exception: return None,None
here=__file__.rsplit('/',1)[0]; secs=float(sys.argv[1])
for idx,pair in enumerate(sys.argv[2:]):
    a,b=pair.split('>')
    url='http://localhost:8901/index.html?go=1&from='+urllib.parse.quote(a)+'&to='+urllib.parse.quote(b)
    r=subprocess.run(['bash',here+'/reload.sh',url,'120'],capture_output=True,text=True,timeout=300)
    if r.returncode!=0: print(json.dumps({'route':pair,'reload_fail':r.stdout[-160:]},ensure_ascii=False),flush=True); continue
    t,_=tel(); w=(t or {}).get('wpDbg') or {}
    print(json.dumps({'route':pair,'routeM':t.get('routeM'),'wpMax':w.get('max'),'over50':w.get('over50'),'uturnHops':w.get('uturnHops')},ensure_ascii=False),flush=True)
    t0=time.time(); last_tp=0; last_cr=0; events=[]; snaps=0
    while time.time()-t0<secs:
        t,g=tel()
        if not t: time.sleep(0.5); continue
        tp=t.get('tpN') or 0
        if tp>last_tp:
            ev={'t':round(time.time()-t0),'m':round((t.get('prog') or 0)*(t.get('routeM') or 0)),'tpPath':t.get('tpPath'),'tpBld':t.get('tpBld'),'blkCenter':t.get('blkCenter'),'blkStuck':t.get('blkStuck'),'blkLast':t.get('blkLast'),'v':t.get('v'),'da':t.get('da'),'tbrk':t.get('tbrk'),'tch':t.get('_tch'),'pHead':(t.get('wpDbg') or {}).get('pHead'),'g2':{k:g.get(k) for k in ('roadW','o','nl','laneF','aTurn','aD','lat')}}
            events.append(ev); last_tp=tp
            if snaps<4:
                subprocess.run(['screencapture','-x','-R0,25,763,762',f'{OUTD}/tp_{idx}_{snaps}.png']); snaps+=1
            print(json.dumps({'teleport':ev},ensure_ascii=False),flush=True)
        cr=t.get('cr') or 0
        if cr>last_cr:
            print(json.dumps({'crash':{'t':round(time.time()-t0),'m':round((t.get('prog') or 0)*(t.get('routeM') or 0)),'crk':t.get('crk'),'v':t.get('v'),'tch':t.get('_tch'),'da':t.get('da'),'g2':{k:g.get(k) for k in ('roadW','o','nl','laneF','aTurn','aD','lat')}}},ensure_ascii=False),flush=True); last_cr=cr
        if (t.get('prog') or 0)>0.97: break
        time.sleep(0.4)
    t,_=tel()
    print(json.dumps({'result':pair,'driven_m':round((t.get('prog') or 0)*(t.get('routeM') or 0)),'routeM':t.get('routeM'),'cr':t.get('cr'),'crk':t.get('crk'),'tpN':t.get('tpN'),'tpPath':t.get('tpPath'),'tpBld':t.get('tpBld'),'blkCenter':t.get('blkCenter'),'blkStuck':t.get('blkStuck'),'jsErr':t.get('jsErr')},ensure_ascii=False),flush=True)

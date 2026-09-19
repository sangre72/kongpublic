#!/usr/bin/env python3
"""출발 정지·골목 순간이동 재현용 0.5초 폴러(2026-09-20). 사용: stall_probe.py <초> "<출발>><도착>" <out.jsonl>
   매 0.5초: v thr brk st vmax xt blk stall hold cool gap ped cap mergeWait doneM prog pos aTurn aD laneF nl lat roadW tpN cr
   끝에 tpTrace/offCrash/arTrail/startTurnaround/startRelax/offTab(앞 12행) 을 마지막 줄에 덤프."""
import json, sys, time, subprocess, urllib.request, urllib.parse
secs = int(sys.argv[1]); fr, to = sys.argv[2].split('>', 1); out = sys.argv[3]
url = 'http://localhost:8901/index.html?go=1&from=%s&to=%s' % (urllib.parse.quote(fr), urllib.parse.quote(to))
print(subprocess.run(['bash', 'reload.sh', url, '60'], capture_output=True, text=True).stdout.strip().splitlines()[-1:])
def tel():
    try: return json.load(urllib.request.urlopen('http://localhost:8901/tel', timeout=3))
    except Exception: return {}
t0 = time.time(); f = open(out, 'w', encoding='utf-8')
while time.time() - t0 < secs:
    d = tel(); da = d.get('da') or {}; g = (d.get('tch') or {}).get('g2') or {}; tc = d.get('tch') or {}
    row = {'t': round(time.time() - t0, 1), 'v': d.get('v'), 'thr': d.get('thr'), 'brk': d.get('brk'), 'st': d.get('st'),
           'vmax': da.get('vmax'), 'xt': da.get('xt'), 'blk': da.get('blk'), 'stall': da.get('stall'), 'hold': da.get('hold'), 'cool': da.get('cool'),
           'gap': tc.get('gap'), 'ped': tc.get('ped'), 'cap': tc.get('cap'), 'mw': d.get('mergeWaitN'), 'doneM': d.get('doneM'), 'prog': d.get('prog'),
           'pos': d.get('pos'), 'aTurn': g.get('aTurn'), 'aD': g.get('aD'), 'laneF': g.get('laneF'), 'nl': g.get('nl'), 'lat': g.get('lat'), 'roadW': g.get('roadW'),
           'tpN': d.get('tpN'), 'cr': d.get('cr'), 'drv': d.get('drv'), 'parked': d.get('parked'), 'wpLen': d.get('wpLen')}
    f.write(json.dumps(row, ensure_ascii=False) + '\n'); f.flush(); time.sleep(0.5)
d = tel(); w = d.get('wpDbg') or {}
f.write(json.dumps({'END': 1, 'tpTrace': d.get('tpTrace'), 'offCrash': d.get('offCrash'), 'arTrail': d.get('arTrail'), 'startTurnaround': d.get('startTurnaround'),
                    'startRelax': d.get('startRelax'), 'startBack': d.get('startBack'), 'car': w.get('car'), 'offTab': (w.get('offTab') or [])[:12], 'tpLog': d.get('tpLog'), 'jsErr': d.get('jsErr')}, ensure_ascii=False) + '\n')
f.close(); print('done', out)

#!/usr/bin/env python3
"""u_5816: score the RULE and two DEGENERATE policies on the course, before any training.
A speed-scaled positive term with crash penalties can be gamed by standing still (0 score, 0
penalty) or by flooring it (high score, occasional penalty). If the rule does not clearly outscore
both, the scoring is wrong - that check is the point of this script."""
import sys, json, time, urllib.request, subprocess
TEL='http://localhost:8901/tel'; CTL='http://localhost:8901/ctl'
def tel():
    try:
        with urllib.request.urlopen(TEL,timeout=4) as r: return json.load(r)
    except Exception: return None
def post(d):
    try:
        urllib.request.urlopen(urllib.request.Request(CTL,json.dumps(d).encode(),
            {'Content-Type':'application/json'}),timeout=2).read()
    except Exception: pass
def run(url, secs=60, mode=None):
    subprocess.run(['bash','reload.sh',url,'45'],capture_output=True)
    time.sleep(2)
    if mode=='stationary': post({'on':1,'vT':0.0})
    elif mode=='flatout':  post({'on':1,'vT':14.0,'steer':0.0,'nosteer':1})
    t0=time.time(); last=None
    while time.time()-t0 < secs:
        d=tel()
        if d:
            c=d.get('course') or {}
            last=c
            if c.get('done'): break
        time.sleep(0.25)
    return last or {}
def row(tag,c):
    return dict(policy=tag, score=c.get('score'), result=c.get('result'),
                elapsed=round(c.get('elapsed') or 0,1), prog=c.get('progress'),
                touchN=c.get('touchN'), clean_s=round(c.get('cleanSec') or 0,1),
                line_s=round(c.get('lineSec') or 0,1), wall_s=round(c.get('wallSec') or 0,1))
if __name__=='__main__':
    base='http://localhost:8901/course_page.html?course=1'
    out=[]
    out.append(row('RULE', run(base,60)))
    out.append(row('STATIONARY', run(base+'&nodrive=1',30,'stationary')))
    out.append(row('FLATOUT_NOSTEER', run(base+'&nosteer=1',60,'flatout')))
    for r in out: print(json.dumps(r,ensure_ascii=False),flush=True)

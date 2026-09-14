"""교사 시범주행 → 학습데이터 수집 (u_4926).

화면 픽셀 ↔ 그때 교사가 한 조작(조향/스로틀/브레이크/후진)을 쌍으로 저장한다.
★사고 순간도 반드시 함께 저장한다 — 나중에 강화학습에서 '하면 안 되는 것'의 자료가 된다.

최종 모델은 화면만 보고 주행한다. 교사는 자료 생성 도구일 뿐 주행에 안 쓴다.
"""
import time, os, json, subprocess
import numpy as np
import cnn_drive as C

OUT = os.path.expanduser('~/kongbot_drive_data')
os.makedirs(OUT, exist_ok=True)

JS_TICK = """
(function(){
  var t=window.__teach; if(!t) return JSON.stringify({err:'no teacher'});
  var a=t.drive(0.021);
  var s=t.state();
  return JSON.stringify({steer:a.steer||0, thr:a.thr||0, brake:a.brake||0,
                         rev:a.rev||0, mode:s.mode, v:s.v, crashes:s.crashes,
                         hold:s.crashHold, onRoad:s.onRoad, laneOff:s.laneOff,
                         obst:(a.obst===undefined?99:a.obst)});
})()
"""

def chrome_eval(js):
    """AppleScript로 Chrome 탭에서 JS 실행 — 교사 조작 + 상태 회수."""
    p = subprocess.run(['osascript','-e',
        'tell application "Google Chrome" to execute front window\'s active tab javascript %s'
        % json.dumps(js)], capture_output=True, text=True, timeout=5)
    return p.stdout.strip()

def collect(mode='fwd', seconds=60, tag='fwd'):
    subprocess.run(['open','-a','Google Chrome'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.4)
    got = C.find_canvas()
    box = (got[0], got[1], 1354, 1274) if got else (15,367,1354,1274)
    bx,by,bw,bh = box; sw,sh = bw//2, bh//2
    chrome_eval("(function(){window.__teach.setMode(%s);return 1})()" % json.dumps(mode))
    X, Y, meta = [], [], []
    t0=time.time(); n=0; crashes0=None
    while time.time()-t0 < seconds:
        ts=time.time()
        a = C.grab(bx,by,sw,sh)
        if a is None: time.sleep(.05); continue
        out = chrome_eval(JS_TICK)
        try: d = json.loads(out)
        except Exception: continue
        if 'err' in d: print('teacher missing'); break
        if crashes0 is None: crashes0 = d['crashes']
        X.append(C.preprocess(a)[0].cpu().numpy().astype(np.float16))
        Y.append([d['steer'], d['thr'], d['brake'], d['rev']])
        meta.append([d['v'], d['laneOff'], d['obst'], d['crashes'], d['hold']])
        n+=1
        dt=time.time()-ts
        if dt<.033: time.sleep(.033-dt)
    if not X: print(json.dumps({'tag':tag,'frames':0})); return
    Xa=np.stack(X); Ya=np.array(Y,dtype=np.float32); Ma=np.array(meta,dtype=np.float32)
    f=os.path.join(OUT, f'{tag}_{int(time.time())}.npz')
    np.savez_compressed(f, X=Xa, Y=Ya, M=Ma)
    print(json.dumps({'tag':tag,'frames':n,'file':os.path.basename(f),
                      'crashes':int(Ma[:,3].max()-Ma[:,3].min()),
                      'crash_frames':int((Ma[:,4]>0).sum()),
                      'MB':round(os.path.getsize(f)/1e6,2)}, ensure_ascii=False), flush=True)

if __name__=='__main__':
    import sys
    mode=sys.argv[1] if len(sys.argv)>1 else 'fwd'
    secs=float(sys.argv[2]) if len(sys.argv)>2 else 60
    collect(mode, secs, tag=mode)

"""걸음마 커리큘럼 — 단계별 학습(u_4917 오너 지시).

★왜 필요한가(실측 근거):
  기존은 1판부터 [주차장출발→도로진입→차선유지→교차로회전→장애물회피→3km목적지]
  6가지를 동시에 요구했다. 보상은 prog*8000 중심이라 직진을 아무리 잘해도
  목적지에 안 가까워지면 0점 — 걸음마를 보상한 적이 없다.
  게다가 tanh 출력 초기값이 무작위라 악셀을 50%만 밟고 조향은 좌우로 번갈아 눌렀다.
  → 앞으로도 못 가고 제자리에서 도는 게 당연한 결과였다.

단계(앞 단계 통과해야 다음으로):
  1 GO      직진: 전진거리만 보상. 사고=즉시종료
  2 LANE    차선유지: 전진 + 이탈/사고 벌점(차선은 이제 입력에 보인다)
  3 TURN    좌우회전: 교차로에서 꺾기
  4 REVERSE 후진·유턴: 막힌 곳 탈출
  5 GOAL    목적지 주행(기존 과제)
"""
import time, os, json
import numpy as np
import torch, torch.nn as nn
import cnn_drive as C

# ★통과 기준 = 점수 + '연속 성공 판수'. 한 번 잘한 건 운일 수 있으므로
#   consec 판 연속으로 기준을 넘겨야 다음 단계로 간다(u_4919 "성공할 때까지").
STAGES = {
 1: dict(name='GO',      secs=12, pass_score=260, consec=3,
         desc='직진만. 악셀 고정, 조향 최소. 사고=즉시 종료'),
 2: dict(name='LANE',    secs=18, pass_score=420, consec=3,
         desc='차선유지. 미세 조향 허용, 사고 벌점 강화'),
 3: dict(name='TURN',    secs=20, pass_score=520, consec=3,
         desc='좌우 회전. 방향 전환량으로 회전 성공 측정'),
 4: dict(name='REVERSE', secs=20, pass_score=480, consec=3,
         desc='후진·유턴. 막힌 데서 빠져나오기'),
 5: dict(name='GOAL',    secs=30, pass_score=900, consec=2,
         desc='목적지 주행'),
}


# ★조향 게이트 — 되먹임 차단(u_4921/4922)
#   카메라가 차를 따라 돌기 때문에 핸들을 계속 누르면 맵이 계속 돌아 무한회전이 된다.
#   사람처럼 "꺾고 → 손을 되돌린다". 연속 max_hold 프레임까지만 꺾고 강제로 뗀다.
_hold = {'dir': 0, 'n': 0}
def _steer_gate(steer, thresh, max_hold):
    want = -1 if steer < -thresh else (1 if steer > thresh else 0)
    if want != 0 and want == _hold['dir']:
        _hold['n'] += 1
        if _hold['n'] > max_hold:          # 너무 오래 꺾고 있으면 강제 복원
            want = 0; _hold['n'] = 0
    elif want != 0:
        _hold['dir'] = want; _hold['n'] = 1
    else:
        _hold['dir'] = 0; _hold['n'] = 0
    C.key('left',  want < 0)
    C.key('right', want > 0)

def act(net, a, stage):
    """단계별로 허용 동작을 제한한다 — 걸음마 단계에서 후진/급조향을 주면 배울 수가 없다."""
    with torch.no_grad():
        o = net(C.preprocess(a))[0].cpu().numpy()
    steer, thr, brk = float(o[0]), float(o[1]), float(o[2])
    if stage == 1:
        # ★1단계 = 조향 완전 차단(u_4921 "제자리 뱅글뱅글").
        #   카메라가 차 방향을 따라 돌기 때문에, 핸들을 꺾으면 맵도 같이 돌아
        #   화면이 바뀌고 → 또 꺾고 → 무한회전하는 되먹임이 생긴다.
        #   걸음마 1단계에서는 핸들을 아예 못 쓰게 해서 '직진'만 몸에 익힌다.
        #   모델이 배우는 건 '악셀을 언제 밟고 언제 떼는가' 하나뿐.
        # ★1단계 = 조향만 잠그고 '가속·제동'은 반드시 준다(u_4923).
        #   브레이크를 막아놨더니 앞에 오토바이가 있어도 멈출 수단이 없어 그대로 박았다.
        #   직진의 절반은 '앞이 막히면 서는 것'이다. 그게 걸음마의 핵심.
        C.key('left', False); C.key('right', False)
        brake_on = brk > 0.15
        C.key('down', brake_on)
        C.key('up', (not brake_on) and thr > -0.6)
    elif stage == 2:
        # ★조향 개방 1차: 아주 둔하게. 게다가 '연속 조향 프레임 수'를 제한해
        #   꺾음→맵회전→또꺾음 되먹임을 끊는다(사람도 한 번 꺾고 손을 되돌린다).
        brake_on = brk > 0.2
        C.key('down', brake_on)
        C.key('up', (not brake_on) and thr > -0.5)
        _steer_gate(steer, 0.55, 6)
    else:
        C.key('up', thr > -0.2 and brk <= 0.5)
        C.key('down', brk > 0.5)
        _steer_gate(steer, 0.30, 10)

def episode(net, box, stage):
    cfg = STAGES[stage]
    import subprocess
    subprocess.run(['open','-a','Google Chrome'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.3)
    got = C.find_canvas()
    if got: box = (got[0], got[1], box[2], box[3])
    bx, by, bw, bh = box
    sw, sh = bw//2, bh//2
    t0=time.time(); frames=0; moved=0.0; crash_f=0; crashes=0
    last=0.0; prev=None; miss=0; prog=0.0
    turn_amt=0.0; rev_frames=0; uturn=0; head=0.0   # 회전·후진 측정용
    try:
        while time.time()-t0 < cfg['secs']:
            ts=time.time()
            a = C.grab(bx,by,sw,sh)
            if a is None:
                miss+=1
                if miss>40: break
                time.sleep(.05); continue
            miss=0
            f=a.astype(np.int16)
            act(net, a, stage)
            # ★사고 = 화면 전체가 꽉 찬 빨강으로 정지(u_4918). 깜빡임 판별 불필요.
            red=float(f[:,:,0].mean()-f[:,:,2].mean())
            lit = red > 35                  # 가득 찬 빨강만 인정(번쩍임 오탐 제거)
            if lit:
                crash_f+=1
                if ts-last>.8: crashes+=1; last=ts
                break                       # ★모든 단계: 사고 즉시 그 판 종료
            bar=f[8:14,21:58]
            prog=float(((bar[:,:,0]>150)&(bar[:,:,1]>120)&(bar[:,:,2]<110)).mean())
            small=f[::8,::8,1]
            if prev is not None:
                dflow=float(np.abs(small-prev).mean())
                moved+=dflow
                # 좌/우 절반의 흐름 차이 = 회전 중이라는 신호(화면만으로 추정)
                lh=float(np.abs(small[:,:small.shape[1]//2]-prev[:,:small.shape[1]//2]).mean())
                rh=float(np.abs(small[:,small.shape[1]//2:]-prev[:,small.shape[1]//2:]).mean())
                d=abs(lh-rh)
                if d>0.25:
                    turn_amt+=d*0.02; head+=d*0.02
                    if head>3.0: uturn+=1; head=0.0
            prev=small
            if stage>=4 and C._down and ('down' in C._down): rev_frames+=1
            frames+=1
            dt=time.time()-ts
            if dt<.020: time.sleep(.020-dt)
    finally:
        C.release_all()
    # 단계별 보상 — 걸음마일수록 단순하게
    if stage==1:
        # 생존 시간을 주 보상으로 — '멈춰서 안 박기'가 '빨리 가서 박기'보다 낫다
        score = frames*1.2 + moved*0.4 - crash_f*40.0 - crashes*300.
    elif stage==2: score = moved - crash_f*10.0 - crashes*60.
    elif stage==3:
        # 회전 학습: 사고 없이 '방향을 실제로 바꾼' 양을 보상
        score = moved*0.5 + turn_amt*260. - crash_f*10.0 - crashes*80.
    elif stage==4:
        # 후진·유턴: 뒤로 뺀 시간 + 큰 방향전환(유턴) 보상
        score = moved*0.4 + rev_frames*3.0 + uturn*400. - crash_f*8.0 - crashes*60.
    else:          score = prog*8000. + moved*0.15 - crashes*260.
    return dict(stage=stage, name=cfg['name'], score=round(score,1),
                moved=round(moved,1), crashes=crashes, crash_frames=crash_f,
                turn=round(turn_amt,2), rev=rev_frames, uturn=uturn,
                frames=frames, prog=round(prog,3),
                fps=round(frames/max(1e-6,time.time()-t0),1))

def train(box, stage, iters=8, pop=6, elite=2, sigma=0.25):
    ck = os.path.expanduser(f'~/.kongbot_stage{stage}.pt')
    net = C.DriveNet().to(C.DEV)
    prev_ck = os.path.expanduser(f'~/.kongbot_stage{stage-1}.pt')
    for src in (ck, prev_ck):                 # 이전 단계 실력을 이어받는다
        if os.path.exists(src):
            try: net.load_state_dict(torch.load(src, map_location=C.DEV)); break
            except Exception: pass
    mu = C.get_flat(net); n = mu.size
    best = -1e18; streak = 0; cfg = STAGES[stage]
    for it in range(iters):
        cand, sc = [], []
        for k in range(pop):
            v = mu + np.random.randn(n).astype(np.float32)*sigma
            C.set_flat(net, v)
            r = episode(net, box, stage)
            if r['frames'] >= 30:
                cand.append(v); sc.append(r['score'])
            print(json.dumps(r, ensure_ascii=False), flush=True)
        if not cand: continue
        idx = np.argsort(sc)[::-1][:elite]
        mu = np.mean([cand[i] for i in idx], axis=0)
        if sc[idx[0]] > best:
            best = float(sc[idx[0]])
            C.set_flat(net, mu); torch.save(net.state_dict(), ck)
        # ★연속 성공 판정: 이번 세대에서 기준 넘긴 판이 consec개 이상이어야 통과
        need = cfg['pass_score']; hit = sum(1 for x in sc if x >= need)
        if hit >= cfg['consec']: streak += 1
        else: streak = 0
        sigma = max(0.12, sigma*0.93)
        passed = streak >= 2
        print(json.dumps({'stage':stage,'iter':it,'best':round(best,1),
                          'pass':need,'hit':hit,'need':cfg['consec'],
                          'streak':streak,'passed':passed}), flush=True)
        if passed:
            print(json.dumps({'stage':stage,'name':cfg['name'],'STAGE_PASSED':True,
                              'best':round(best,1)}, ensure_ascii=False), flush=True)
            break
    return best

if __name__ == '__main__':
    import sys, torch as _t
    box=(15,367,1354,1274)
    print(json.dumps({'device':C.DEV,'mps':_t.backends.mps.is_available()}),flush=True)
    first=int(sys.argv[1]) if len(sys.argv)>1 else 1
    last =int(sys.argv[2]) if len(sys.argv)>2 else 4
    iters=int(sys.argv[3]) if len(sys.argv)>3 else 10
    for st in range(first, last+1):
        print(json.dumps({'stage':st,'desc':STAGES[st]['desc']},ensure_ascii=False),flush=True)
        train(box, st, iters=iters)

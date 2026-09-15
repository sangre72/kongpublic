#!/usr/bin/env python3
"""학습된 CNN 이 실제로 차를 몬다 (a_5085).

★왜 drive_infer.py 를 안 쓰나(기각 사유, 실측):
  drive_infer.py 는 화살표키를 합성해서 넣는다. 그런데 game.js step() 의 키 처리는
  `if(!auto.on){...}` 블록 안에만 있다 — 즉 내비 경로가 살아 있으면 화살표가
  통째로 무시된다. 정작 보고 싶은 '경로를 따라 모델이 모는' 경우가 안 된다.
  게다가 키는 이산값이라 steer 가 항상 ±0.85 로 뭉개져, 모델이 낸 연속값
  (실측 std 0.20)을 버린다.

★대신: 로컬 서버 /ctl 에 조작값을 올리면 페이지가 20Hz 로 읽어
  me.steer / me.v 에 직접 넣는다(game.js driveModel). 아티팩트(샌드박스)였다면
  못 했겠지만 지금은 로컬 페이지라 fetch 가 된다.

입력 규약(net.py): RGB, 256x256, 0~1, (3,256,256). 출력 tanh —
  [steer(-1~1), thr, brake] (+bc_road.pt 는 4번째로 차로중심거리 보조출력).

사용: python3 model_drive.py [--model bc_final.pt] [--secs 60] [--dry]
"""
import argparse, json, os, sys, time, urllib.request
import numpy as np, torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet, preprocess
import capture as C

CTL = 'http://localhost:8901/ctl'
# ★GPU 강제(u_5100). 조용한 CPU 폴백 금지 — 못 쓰면 죽는다.
from gpu_guard import require_gpu, assert_on_gpu
DEV = require_gpu()


def post(d):
    try:
        urllib.request.urlopen(
            urllib.request.Request(CTL, json.dumps(d).encode(),
                                   {'Content-Type': 'application/json'}),
            timeout=1.0).read()
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='bc_final.pt')
    ap.add_argument('--secs', type=float, default=60)
    ap.add_argument('--dry', action='store_true', help='값만 측정하고 차는 안 몬다')
    a = ap.parse_args()

    mp = a.model if os.path.isabs(a.model) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), a.model)
    sd = torch.load(mp, map_location=DEV)
    out = sd[list(sd)[-1]].shape[0]          # 3 또는 4 (bc_road 는 보조출력 포함)
    _gpu_checked = False
    net = DriveNet(out=out).to(DEV)
    assert_on_gpu(net)                       # 가중치가 실제로 GPU 에 올라갔는지 확인
    net.load_state_dict(sd)
    net.eval()

    if C.find_window() is None:
        print(json.dumps({'err': 'no chrome window'})); return
    C.clear_selection()      # 전체선택 하이라이트가 남으면 화면이 파랗게 물든다
    """★캡처를 메인스레드에서 동기로 한다(실측으로 배경스레드를 버렸다).

    capture.start_background() 를 쓰면 이 스크립트에서 grab_canvas() 가 워커
    스레드에서만 None 을 돌려준다 — 같은 프로세스·같은 인자인데 메인스레드에서는
    (762,763,3) 이 정상으로 나온다. 실측: 배경스레드 30초에 새 프레임 1장,
    출력 std 가 0.000 으로 굳어 측정이 통째로 무효였다(CGWindowListCreateImage 는
    메인스레드/오토릴리즈풀 문맥을 탄다).
    추론이 2.5ms 라 동기로 돌려도 예산에 여유가 크다."""

    S, T, B, LAT = [], [], [], []
    nf = 0                       # 실제로 캡처에 성공한 프레임 수
    t0 = time.time()
    posted = 0
    try:
        while time.time() - t0 < a.secs:
            f = C.grab_canvas()
            if f is None:
                time.sleep(0.01); continue
            nf += 1
            x = preprocess(f, device=DEV)[None]
            if not _gpu_checked:             # 첫 프레임만: 입력도 GPU 인지 확인
                assert_on_gpu(x); _gpu_checked = True
            ts = time.time()
            with torch.no_grad():
                o = net(x)[0].cpu().numpy()
            LAT.append((time.time() - ts) * 1000)
            st, th, br = float(o[0]), float(o[1]), float(o[2])
            S.append(st); T.append(th); B.append(br)
            if not a.dry:
                if post({'on': 1, 'force': 1, 'steer': st, 'thr': th, 'brake': br}):
                    posted += 1
    finally:
        if not a.dry:
            post({'on': 0, 'steer': 0, 'thr': 0, 'brake': 0})   # 종료 시 모델 해제

    if not S:
        print(json.dumps({'err': 'no frames'})); return
    S, T, B = map(np.array, (S, T, B))
    print(json.dumps({
        'model': os.path.basename(mp), 'out': out,
        'frames': len(S), 'secs': round(time.time() - t0, 1),
        'fps': round(len(S) / (time.time() - t0), 1),
        'infer_ms': round(float(np.mean(LAT)), 2),
        'posted': posted,
        'captured': nf,
        # ★포화 여부가 핵심 판정(과거 실패 모드: ±1 에 붙어버림)
        'steer': {'mean': round(float(S.mean()), 3), 'std': round(float(S.std()), 3),
                  'min': round(float(S.min()), 3), 'max': round(float(S.max()), 3),
                  'sat_pct': round(float((np.abs(S) > 0.95).mean() * 100), 1)},
        'thr':   {'mean': round(float(T.mean()), 3), 'std': round(float(T.std()), 3)},
        'brake': {'mean': round(float(B.mean()), 3), 'std': round(float(B.std()), 3),
                  'hard_pct': round(float((B > 0.7).mean() * 100), 1)},
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()

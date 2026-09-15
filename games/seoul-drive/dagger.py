#!/usr/bin/env python3
"""DAgger — 모델이 몰고, 교사가 '나라면 이렇게 했다'를 라벨로 남긴다 (a_5170).

★왜 BC 가 여기서 막혔나(실측):
  v1 진행률 0.911 / v2 0.0 / v3 0.0. v2 의 조향 상관은 새 커리큘럼에서 0.863 이었다
  (v1 은 0.079) — 즉 '상황을 못 배운 것'이 아니다. BC 는 교사의 프레임을 흉내낼 뿐
  '도착'이라는 개념이 없어서, 한 번 틀어지면 교사가 가 본 적 없는 상태에 떨어지고
  거기엔 라벨이 없다. 사고의 75%가 차로이탈인 이유가 이것이다.

★DAgger 가 정확히 이걸 고친다:
  모델이 직접 몬다 → 모델은 자기가 잘 가는 곳이 아니라 '자기가 실제로 가는 곳'에 간다
  그 상태에서 교사의 정답을 받는다 → 다음 라운드 학습셋에 그 상태의 정답이 들어간다
  반복하면 학습분포가 모델의 방문분포로 수렴한다.

에피소드 = 소프트리셋 1회 + N초 주행. 리로드(50초)를 안 한다 —
맵 10MB 재파싱이 에피소드의 38% 를 먹는다(u_5126).

사용: python3 dagger.py --round 1 --episodes 10 --secs 45 --model bc_final.pt
"""
import argparse, hashlib, json, os, subprocess, sys, time, urllib.request
import numpy as np, torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import DriveNet, preprocess
from gpu_guard import require_gpu, assert_on_gpu
import capture as C

BASE = os.path.dirname(os.path.abspath(__file__))
CTL, TEL = 'http://localhost:8901/ctl', 'http://localhost:8901/tel'


def tel():
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=3))
    except Exception:
        return None


def post(d):
    try:
        urllib.request.urlopen(urllib.request.Request(
            CTL, json.dumps(d).encode(), {'Content-Type': 'application/json'}),
            timeout=1.5).read()
        return True
    except Exception:
        return False


def episode(net, dev, secs, ep):
    """한 에피소드: 모델이 몰고 교사 라벨을 모은다. (frames, stats)"""
    post({'reset': 1, 'on': 1, 'force': 1, 'release': 0})   # 소프트리셋 + 모델 강제 ON
    time.sleep(1.5)
    X, Y = [], []
    seen = set()
    t0 = time.time()
    d0 = tel() or {}
    p_start = float(d0.get('prog') or 0)
    cr0 = int(d0.get('cr') or 0)
    crk0 = dict(d0.get('crk') or {})
    pmax = p_start
    nmodel = ntot = 0
    dup = nolabel = nodecode = 0
    last_st, frozen = None, 0
    arrived = False

    while time.time() - t0 < secs:
        d = tel()
        if not d:
            time.sleep(0.05); continue
        ntot += 1
        if d.get('drv') == 'MODEL':
            nmodel += 1
        p = float(d.get('prog') or 0)
        pmax = max(pmax, p)
        if p >= 0.95:
            arrived = True
            break

        # --- 교사 라벨(DAgger 의 전부) ---
        t = d.get('tch') or {}
        if not t.get('ok'):
            nolabel += 1
            if nolabel > 300:
                break
            time.sleep(0.03); continue
        st, th, br = float(t['st']), float(t['th']), float(t.get('br', 0))
        if last_st is not None and abs(st - last_st) < 1e-9:
            frozen += 1
        else:
            frozen = 0
        last_st = st
        if frozen > 200:                      # 교사가 죽으면 상수 라벨이 쌓인다
            print(json.dumps({'ep': ep, 'abort': 'teacher frozen'}), flush=True)
            break

        # --- 모델 추론 + 조작(모델이 몰아야 DAgger 다) ---
        f = C.grab_canvas()
        if f is None:                          # 빨간 사고 오버레이 등 — 데이터 아님
            nodecode += 1
            time.sleep(0.02); continue
        x = preprocess(f, device=dev)[None]
        with torch.no_grad():
            o = net(x)[0].cpu().numpy()
        post({'on': 1, 'force': 1, 'steer': float(o[0]),
              'thr': float(o[1]), 'brake': float(o[2])})

        # --- 저장: 모델이 본 화면 + 교사의 정답 ---
        h = hashlib.md5(np.ascontiguousarray(f).tobytes()).digest()
        if h in seen:
            dup += 1
        else:
            seen.add(h)
            X.append((x[0].cpu().numpy() * 255).astype(np.uint8))
            # ★u_5171: 4번째 열에 '그 순간의 속도'를 넣는다(예전엔 0.0 상수였다).
            #   왜 필요한가 — 오드가 '안 움직이면 안 박는다'를 배웠는데,
            #   '움직이다 서는 제동'과 '이미 선 채로 계속 밟는 제동'을
            #   사후에 구분할 방법이 없었다. 속도가 있으면 후자를 걸러낼 수 있다.
            Y.append([st, th, br, float(d.get('v') or 0)])
        time.sleep(0.02)

    dl = tel() or {}
    crk1 = dict(dl.get('crk') or {})
    dcr = {k: int(crk1.get(k, 0)) - int(crk0.get(k, 0))
           for k in set(crk1) | set(crk0)
           if int(crk1.get(k, 0)) - int(crk0.get(k, 0)) > 0}
    stats = {
        'ep': ep, 'frames': len(X), 'dup': dup, 'nodecode': nodecode,
        'model_pct': round(100 * nmodel / max(1, ntot), 1),
        'prog_start': round(p_start, 4), 'prog_max': round(pmax, 4),
        'prog_end': round(float(dl.get('prog') or 0), 4),
        'crashes': int(dl.get('cr') or 0) - cr0, 'crash_types': dcr,
        'arrived': arrived, 'secs': round(time.time() - t0, 1),
    }
    return (np.stack(X) if X else None,
            np.array(Y, dtype=np.float32) if Y else None, stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--episodes', type=int, default=10)
    ap.add_argument('--secs', type=float, default=45)
    ap.add_argument('--model', default='bc_final.pt')
    a = ap.parse_args()

    dev = require_gpu()
    mp = a.model if os.path.isabs(a.model) else os.path.join(BASE, a.model)
    sd = torch.load(mp, map_location=dev)
    out = sd[list(sd)[-1]].shape[0]
    net = DriveNet(out=out).to(dev)
    net.load_state_dict(sd); net.eval()
    assert_on_gpu(net)

    subprocess.run(['open', '-a', 'Google Chrome'], capture_output=True)
    time.sleep(2)
    if C.find_window() is None:
        print(json.dumps({'err': 'no chrome window'})); return
    C.clear_selection()

    outd = os.path.join(BASE, 'data', 'dagger_r%d' % a.round)
    os.makedirs(outd, exist_ok=True)
    AX, AY, ST = [], [], []
    try:
        for i in range(a.episodes):
            X, Y, s = episode(net, dev, a.secs, i + 1)
            ST.append(s)
            print(json.dumps(s, ensure_ascii=False), flush=True)
            if X is not None:
                AX.append(X); AY.append(Y)
    finally:
        post({'on': 0, 'steer': 0, 'thr': 0, 'brake': 0})

    if not AX:
        print(json.dumps({'err': 'no frames collected'})); return
    X = np.concatenate(AX); Y = np.concatenate(AY)
    np.save(f'{outd}/X.npy', X); np.save(f'{outd}/Y.npy', Y)
    open(f'{outd}/DONE', 'w').write('ok\n')
    json.dump(ST, open(f'{outd}/episodes.json', 'w'), ensure_ascii=False, indent=1)

    # ★라벨 분포 확인은 필수다(u_5163). v2 는 정지프레임을 12배 증폭해
    #   스로틀 평균이 0.812 -> 0.643 이 됐고, 오드가 '서 있기'를 배웠다.
    print(json.dumps({
        'round': a.round, 'episodes': len(ST), 'frames': len(Y), 'out': outd,
        'thr_mean': round(float(Y[:, 1].mean()), 4),
        'brake_gt05_pct': round(float((Y[:, 2] > 0.5).mean() * 100), 3),
        'steer_std': round(float(Y[:, 0].std()), 4),
        'prog_max_mean': round(float(np.mean([s['prog_max'] for s in ST])), 4),
        'crashes_mean': round(float(np.mean([s['crashes'] for s in ST])), 2),
        'arrivals': sum(1 for s in ST if s['arrived']),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()

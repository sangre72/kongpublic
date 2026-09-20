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
    if net is None: post({'reset': 1, 'on': 0, 'force': 0, 'release': 1, 'steer': 0, 'thr': 0, 'brake': 0})   # 교사 주행: 리셋만, 모델 OFF
    else: post({'reset': 1, 'on': 1, 'force': 1, 'release': 0})   # 소프트리셋 + 모델 강제 ON
    time.sleep(1.5)
    X, Y = [], []
    W, TT = [], []                         # ★u_5426 프레임 가중치(사고 직전 3초=0)·프레임 시각
    P = []                                 # ★2026-09-20 모델 출력(조향·스로틀·제동) — 사후 분석용(P.npy). k=7 '왜 서 있나'를 못 봤다.
    M = []                                 # ★u_5427 상황 태그 [gap, ped, sig, turn(0/S 1/L 2/R 3/U), aD, v, laneF, nl] — 커리큘럼 단계 필터용
    seen = set()
    LK = {'n': 0, 'on': 0, 'off': 0, 'lat': 0.0, 'err': 0.0, 'outlane': 0}
    LABEL_SRC = ['teacher']   # ★2026-09-20 차선유지 지표. lat=도로중심선 기준 부호 오프셋, off=교사 목표차로 오프셋 → |lat−off| 가 차로 오차
    t0 = time.time()
    if net is None: post({'on': 0, 'force': 0, 'steer': 0, 'thr': 0, 'brake': 0})   # 교사 주행: 모델 조작 해제 → GEOM/교사가 몬다(안 그러면 drv=MODEL 에 명령 없음 → v=0·순간이동 연쇄)
    d0 = tel() or {}
    p_start = float(d0.get('prog') or 0)
    cr0 = int(d0.get('cr') or 0)
    crk0 = dict(d0.get('crk') or {})
    cr_prev = cr0; crk_prev = dict(crk0)          # W 가중치용 사고 추적(u_5426)
    pmax = p_start
    nmodel = ntot = 0
    dup = nolabel = nodecode = 0
    last_st, frozen, frozen_t = None, 0, 0
    arrived = False

    while time.time() - t0 < secs:
        d = tel()
        if not d:
            time.sleep(0.05); continue
        ntot += 1
        # ★u_5426 오너: "사고(추돌·충돌)는 가중치를 조절해서 학습이 되게끔". 회피 가능한 사고가 나면
        #   그 직전 3초 프레임의 가중치를 0 으로 둔다(그 구간의 교사 라벨은 사고로 이어진 행동이다).
        #   불가항력(정지거리 안 무단횡단)은 라벨이 잘못된 게 아니므로 가중치를 유지한다.
        try:
            cr_now = int(d.get('cr') or 0)
            if cr_now > cr_prev:
                crk_now = dict(d.get('crk') or {})
                new_types = [k for k in crk_now if int(crk_now.get(k, 0)) > int(crk_prev.get(k, 0))]
                if any('불가항력' not in k for k in new_types):
                    tc = time.time()
                    for j in range(len(W) - 1, -1, -1):
                        if TT[j] < tc - 3.0: break
                        W[j] = 0.0
                cr_prev = cr_now; crk_prev = crk_now
        except Exception:
            pass
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
        # ★2026-09-20 17:03 근본 원인: 교사 주행 수집에서 차를 모는 건 driveAuto(경로 추종)인데 조향 라벨은 teacher.js 값이었다.
        #   실측 60초: 교사 st 평균 −0.39 vs 실제 적용 st +0.02, 상관 0.08(교사 목표차로가 차 위치보다 4.6m 오른쪽).
        #   8만 장이 전부 '다른 차로로 꺾는 조향'을 가르쳤다 → 반대차로 이탈·순간이동 90회/300초. 조향 라벨 = 실제로 차를 몬 조향(da.st,
        #   driveAuto 가 교란 덮어쓰기 전에 계산한 값). 스로틀·제동은 교사 값이 그대로 적용되므로 유지. 모델 주행(DAgger)은 종전대로(교사).
        _da = d.get('da') or {}
        if net is None and isinstance(_da.get('st'), (int, float)):
            st = float(_da['st']); LABEL_SRC[0] = 'driveAuto'
        # ★2026-09-20 r109 실측: 신호 대기(st=0, v=0)에서 200프레임(1.3fps=150초) 동일 라벨 → '교사 정지'로 오판·에피소드 중단.
        #   정지 중 동일 라벨은 정상 — 움직이는데(v>1) 조향이 120초 넘게 완전히 같을 때만 죽은 것으로 본다.
        _v_now = float(d.get('v') or 0)
        if last_st is not None and abs(st - last_st) < 1e-9 and _v_now > 1.0:
            if frozen == 0: frozen_t = time.time()
            frozen += 1
        else:
            frozen = 0; frozen_t = 0
        last_st = st
        if frozen and frozen_t and time.time() - frozen_t > 120:   # 교사가 죽으면 상수 라벨이 쌓인다(주행 중 120초)
            print(json.dumps({'ep': ep, 'abort': 'teacher frozen'}), flush=True)
            break

        # --- 모델 추론 + 조작(모델이 몰아야 DAgger 다) ---
        f = C.grab_canvas()
        if f is None:                          # 빨간 사고 오버레이 등 — 데이터 아님
            nodecode += 1
            time.sleep(0.02); continue
        x = preprocess(f, device=dev)[None]
        if net is not None:
            with torch.no_grad():
                _vt = torch.tensor([[float(d.get('v') or 0) / 30.0]], device=dev)   # 속도 입력(u_5461)
                o = (net(x, _vt) if getattr(net, 'vin', False) else net(x))[0].cpu().numpy()
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
            # 5열: lane_off(차로 중심 이탈량 m). ★사고의 77%가 경계 이탈인데
            #   교사가 계산해둔 이 값이 저장되지 않아 학습에 쓰인 적이 없었다.
            # 6열: [조향, 스로틀, 제동, 속도, 좌여유, 우여유]
            # ★lane_off(방향없는 스칼라)는 v14 에서 역효과였다 — 건물충돌
            #   41→96건, 거리 2948→1370m. 좌/우를 따로 줘야 '어디로 피하나'를
            #   배운다(net.py 원설계).
            W.append(1.0); TT.append(time.time())
            try:
                g2 = t.get('g2') or {}
                try:
                    _lat = g2.get('lat'); _rw = g2.get('roadW')
                    if isinstance(_lat, (int, float)) and isinstance(_rw, (int, float)) and _rw > 0:
                        LK['n'] += 1; LK['lat'] += abs(_lat); LK['off'] += int(abs(_lat) > _rw / 2 + 0.5)
                        LK['on'] += int(bool(d.get('onroad', 1)))
                        _off = g2.get('off')
                        if isinstance(_off, (int, float)):
                            _e = abs(_lat - _off); LK['err'] += _e; LK['outlane'] += int(_e > 1.63)
                except Exception: pass
                _ext = ([float(os.environ.get('ODE_ENV', '0')), float(ep), float(len(X))] if os.environ.get('M_EXT') == '1' else [])   # u_5442: env/ep/fi (M_EXT=1 부터, 밤 수집 형식 유지)
                M.append([float(t.get('gap') if t.get('gap') is not None else 1e9),
                          float(t.get('ped') if t.get('ped') is not None else 1e9),
                          float(t.get('sig') if t.get('sig') is not None else 1e9),
                          {'S': 0, 'L': 1, 'R': 2, 'U': 3}.get(g2.get('aTurn') or 'S', 0),
                          float(g2.get('aD') if g2.get('aD') is not None else 1e9),
                          float(d.get('v') or 0), float(g2.get('laneF') or 0), float(g2.get('nl') or 0)] + _ext)
            except Exception:
                M.append([1e9, 1e9, 1e9, 0, 1e9, 0.0, 0.0, 0.0] + ([float(os.environ.get('ODE_ENV', '0')), float(ep), float(len(X))] if os.environ.get('M_EXT') == '1' else []))
            Y.append([st, th, br, float(d.get('v') or 0),
                      float(t.get('fl') if t.get('fl') is not None else -1.0),
                      float(t.get('fr') if t.get('fr') is not None else -1.0)])
            P.append([float(o[0]), float(o[1]), float(o[2])] if net is not None else [0.0, 0.0, 0.0])
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
        'w0_frames': int(sum(1 for w in W if w == 0.0)),
        'arrived': arrived, 'secs': round(time.time() - t0, 1),
        'onroad_pct': round(100 * LK['on'] / max(1, LK['n']), 1), 'offroad_pct': round(100 * LK['off'] / max(1, LK['n']), 1),
        'lat_abs_m': round(LK['lat'] / max(1, LK['n']), 2), 'tpN': int(dl.get('tpN') or 0),
        'lane_err_m': round(LK['err'] / max(1, LK['n']), 2), 'outlane_pct': round(100 * LK['outlane'] / max(1, LK['n']), 1),
        'label_src': LABEL_SRC[0],
    }
    return (np.stack(X) if X else None,
            np.array(Y, dtype=np.float32) if Y else None, stats,
            np.array(W, dtype=np.float32) if W else None,
            np.array(M, dtype=np.float32) if M else None,
            np.array(P, dtype=np.float32) if P else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--episodes', type=int, default=10)
    ap.add_argument('--secs', type=float, default=45)
    ap.add_argument('--model', default='bc_final.pt')
    a = ap.parse_args()

    dev = require_gpu()
    mp = a.model if os.path.isabs(a.model) else os.path.join(BASE, a.model)
    # ★2026-09-19 u_5431: bc_final.pt 는 옛 DriveNet 구조(h.0/h.2)라 현재 망(h.1/h.4/h.6)에 안 들어간다. 1단계(직진) 데이터는
    #   교사가 몰아 만든다 — `--model none` 이면 추론·조작을 건너뛰고 화면+교사 라벨+W/M 만 저장한다(BC 먼저, DAgger 는 새 모델 뒤).
    if a.model == 'none':
        net = None; print(json.dumps({'mode': 'teacher-drive', 'note': 'no model; GEOM/teacher drives'}), flush=True)
    else:
        sd = torch.load(mp, map_location=dev)
        out = sd[list(sd)[-1]].shape[0]
        net = DriveNet(out=out, vin=any(k.startswith('hv.') for k in sd)).to(dev)   # hv.* 키가 있으면 속도 입력 구조
        net.load_state_dict(sd); net.eval()
    if net is not None: assert_on_gpu(net)

    subprocess.run(['open', '-a', 'Google Chrome'], capture_output=True)
    time.sleep(2)
    if C.find_window() is None:
        print(json.dumps({'err': 'no chrome window'})); return
    C.clear_selection()

    outd = os.path.join(BASE, 'data', 'dagger_r%d' % a.round)
    os.makedirs(outd, exist_ok=True)
    AX, AY, ST, AW, AM = [], [], [], [], []; AP = []
    try:
        for i in range(a.episodes):
            X, Y, s, Wt, Mt, Pt = episode(net, dev, a.secs, i + 1)
            ST.append(s)
            print(json.dumps(s, ensure_ascii=False), flush=True)
            if X is not None:
                AX.append(X); AY.append(Y); AW.append(Wt); AM.append(Mt); AP.append(Pt)
    finally:
        post({'on': 0, 'steer': 0, 'thr': 0, 'brake': 0})

    if not AX:
        print(json.dumps({'err': 'no frames collected'})); return
    X = np.concatenate(AX); Y = np.concatenate(AY)
    np.save(f'{outd}/X.npy', X); np.save(f'{outd}/Y.npy', Y)
    np.save(f'{outd}/W.npy', np.concatenate(AW))     # 프레임 가중치(u_5426) — 없으면 학습기는 전부 1 로 본다
    np.save(f'{outd}/M.npy', np.concatenate(AM))     # 상황 태그(u_5427) — 단계별(커리큘럼) 프레임 선별용
    np.save(f'{outd}/P.npy', np.concatenate(AP))     # 모델 출력(2026-09-20) — Y(교사)와 나란히
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

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
PIPE = False   # --model pipe (2026-09-20 대조 실험)
SPEED_MODEL = False   # ode_v*.pt = 속도 판단 모델(2026-09-22)
LPNET = None   # --lp 조향 모델(T0 전용)
LPST = {'lp': 0, 'rule': 0, 'hold': 0, 'maxT': 0}   # 프레임 배정 집계·T0 연속 카운터·이양 최대 등급
TIER = None   # 관제망(--tier)
import numpy as np, torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import vdim_of, cond_vec, DriveNet, preprocess, preprocess_label, IMG
from gpu_guard import require_gpu, assert_on_gpu
import capture as C

BASE = os.path.dirname(os.path.abspath(__file__))
CTL, TEL = 'http://localhost:8901/ctl', 'http://localhost:8901/tel'


def tel():
    try:
        return json.load(urllib.request.urlopen(TEL, timeout=3))
    except Exception:
        return None


LAT = [-1.0, -1.0]   # [프레임 취득→명령 전송 ms, 추론 ms] — 패널 표시용(u_5520)
def post(d):
    try:
        if 'lat' not in d and LAT[0] >= 0: d['lat'] = round(LAT[0], 1); d['inf'] = round(LAT[1], 1)
        urllib.request.urlopen(urllib.request.Request(
            CTL, json.dumps(d).encode(), {'Content-Type': 'application/json'}),
            timeout=1.5).read()
        return True
    except Exception:
        return False


LAB = os.environ.get('LAB') == '1'; SEG = []; SEGN = [0]   # a_5612 픽셀 라벨 수집(?lab=1 페이지 필요)
def episode(net, dev, secs, ep):
    """한 에피소드: 모델이 몰고 교사 라벨을 모은다. (frames, stats)"""
    post({'tgt': 0, 'mode': 1, 'dOff': 0.0, 'vT': -1, 'lp': 0.0})   # ★에피소드마다 목표 인터페이스 상태 초기화(서버 _ctl 은 프로세스 간 잔존)
    LPST['lp'] = 0; LPST['rule'] = 0; LPST['hold'] = 0
    if net is None and not PIPE: post({'reset': 1, 'on': 0, 'force': 0, 'release': 1, 'steer': 0, 'thr': 0, 'brake': 0})   # 교사 주행: 리셋만, 모델 OFF
    else: post({'reset': 1, 'on': 1, 'force': 1, 'release': 0})   # 소프트리셋 + 모델 강제 ON
    time.sleep(1.5)
    X, Y = [], []
    W, TT = [], []                         # ★u_5426 프레임 가중치(사고 직전 3초=0)·프레임 시각
    P = []                                 # ★2026-09-20 모델 출력(조향·스로틀·제동) — 사후 분석용(P.npy). k=7 '왜 서 있나'를 못 봤다.
    TN = []                                # ★2026-09-22 관제망(tier net) 출력 [ntier, conf, ntier_raw] (T.npy) — 오너 u_5512 '적용'
    Q = []                                 # ★2026-09-20 u_5478 프레임 품질 [xt(경로추적오차 m), tpN, cr, t] — '차선 잘 지킨 구간만' 선별용(Q.npy)
    LP = []                                # ★2026-09-21 앞점 라벨 [lp(m, +=오른쪽), ld(m)] — 차 기준 앞점 인터페이스(tgt mode=2) 학습용(L.npy)
    M = []                                 # ★u_5427 상황 태그 [gap, ped, sig, turn(0/S 1/L 2/R 3/U), aD, v, laneF, nl] — 커리큘럼 단계 필터용
    seen = set()
    LK = {'n': 0, 'on': 0, 'off': 0, 'lat': 0.0, 'err': 0.0, 'outlane': 0}
    LABEL_SRC = ['teacher']   # ★2026-09-20 차선유지 지표. lat=도로중심선 기준 부호 오프셋, off=교사 목표차로 오프셋 → |lat−off| 가 차로 오차
    t0 = time.time()
    if net is None and not PIPE: post({'on': 0, 'force': 0, 'steer': 0, 'thr': 0, 'brake': 0})   # 교사 주행: 모델 조작 해제 → GEOM/교사가 몬다(안 그러면 drv=MODEL 에 명령 없음 → v=0·순간이동 연쇄)
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
        if p >= 0.95 and not d.get('synth'):   # 가상 샘플링(synth)은 경로를 순환하므로 '도착'으로 끝내지 않는다(2026-09-20 r400: 68초 925장에서 조기 종료)
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
        _sh = d.get('daShadow') or {}
        if (net is not None or PIPE) and isinstance(_sh.get('st'), (int, float)):
            st = float(_sh['st']); LABEL_SRC[0] = 'daShadow'   # 모델 주행 중 라벨 = 그림자 경로추종 조향(규칙 D-00)
        # ★프레임 헤더 라벨(2026-09-20): 푸시된 프레임과 같은 순간의 라벨(X-Lbl). /tel 은 20Hz 비동기라 가상 샘플링(150ms 마다 상태 교체)에선
        #   프레임/라벨이 어긋난다. 헤더가 있으면 그것을 쓴다(캡처 뒤에 덮어씀 — 아래 grab 이후 적용).
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
        _tf = time.time(); f = C.grab_canvas()
        if f is None:                          # 빨간 사고 오버레이 등 — 데이터 아님
            nodecode += 1
            time.sleep(0.02); continue
        try:
            _lb = C.push_stats().get('lbl') if hasattr(C, 'push_stats') else None
            if net is None and isinstance(_lb, dict) and isinstance(_lb.get('st'), (int, float)):
                st = float(_lb['st']); th = float(_lb.get('th') if _lb.get('th') is not None else th); br = float(_lb.get('br') if _lb.get('br') is not None else br)
                if isinstance(_lb.get('v'), (int, float)): d['v'] = float(_lb['v'])
                LABEL_SRC[0] = 'frame-hdr'
        except Exception:
            pass
        x = preprocess(f, device=dev)[None]
        if net is not None and getattr(net, 'in_ch', 3) == 6:   # 프레임 스택: [직전, 현재]
            _xp = globals().get('_PREV_X'); x = torch.cat([_xp if _xp is not None else x, x], dim=1); globals()['_PREV_X'] = x[:, 3:]
        _nt = -1; _nc = 0.0; _ntraw = -1
        if TIER is not None:   # ★관제망: 프레임마다 등급·확신도. 확신도 <0.6 → 한 등급 위(안전 편향). T2 → vT≤8, T3 → vT≤3 (보수 모드, Layer1 은 별도).
            with torch.no_grad():
                _o = torch.softmax(TIER(x[:, :3]), 1)[0]; _nc = float(_o.max()); _ntraw = int(_o.argmax()); _nt = min(3, _ntraw + (1 if _nc < 0.6 else 0))
            post({'ntier': _nt, 'nconf': round(_nc, 3)})
        if PIPE == 'pipe3':   # ★차 기준 앞점 인터페이스 검증: 직전 프레임 라벨(lp, ld)을 그대로 되돌려 준다(모델이 완벽할 때의 상한)
            _lb3 = C.push_stats().get('lbl') if hasattr(C, 'push_stats') else None
            if isinstance(_lb3, dict) and isinstance(_lb3.get('lp'), (int, float)):
                post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': float(_lb3['lp']), 'ld': float(_lb3.get('ld') or 10.0), 'vT': -1})
        elif PIPE == 'pipe2':   # ★목표 오프셋 인터페이스 검증: 오프셋 0·속도 미지정 → 추종기 그대로(관문과 같아야 함)
            post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 1, 'dOff': 0.0, 'vT': -1})   # ★mode=1 명시: 서버 _ctl 에 남은 mode=2·lp(앞점 모델 잔재)가 그대로 적용돼 제자리 회전(u_5504)
        elif PIPE:   # ★대조 실험: 경로추종기의 조향(그림자)+교사 속도제어를 모델과 같은 파이프(13fps·/ctl·150ms 신선도)로 흘린다
            post({'on': 1, 'force': 1, 'steer': st, 'thr': th, 'brake': br})
        if net is not None:
            with torch.no_grad():
                _vt = torch.tensor([[float(d.get('v') or 0) / 30.0]], device=dev)   # 속도 입력(u_5461)
                _ti = time.time(); o = (net(x, _vt) if getattr(net, 'vin', False) else net(x))[0].cpu().numpy(); LAT[1] = (time.time() - _ti) * 1000.0
            LAT[0] = (time.time() - _tf) * 1000.0
            if len(o) >= 4 and SPEED_MODEL:   # ★속도 모델(ode_v*.pt, 2026-09-22 축소안 A): 조향=추종기(경로선), 모델=목표속도(1초 뒤). vT 는 상한으로 적용(규칙 상한·정지 지시 유지).
                _vT = max(0.0, float(o[3]) * 30.0)
                if TIER is not None and _nt >= 2: _vT = min(_vT, 8.0 if _nt == 2 else 3.0)   # 관제망 보수 모드
                _rt = d.get('tier'); _rt = int(_rt) if isinstance(_rt, (int, float)) else 3
                LPST['hold'] = LPST['hold'] + 1 if _rt <= LPST['maxT'] else 0
                if LPNET is not None and LPST['hold'] >= 13 and getattr(LPNET, 'in_ch', 3) == 3:   # ★단계적 이양(u_5516): 규칙 등급 T0 가 1초 이상 이어질 때만 조향모델이 핸들. T1↑ 즉시 규칙 조향.
                    with torch.no_grad():
                        _vl = _vt
                        if getattr(LPNET, 'vdim', 1) == 8:   # ★u_5546 조건부: 경로 의도 벡터
                            _g2 = ((d.get('tch') or {}).get('g2') or {}); _vl = torch.tensor(cond_vec(d.get('v'), _g2.get('aTurn') or 'S', _g2.get('aD'), _g2.get('laneF'), _g2.get('nl'))[None], device=dev)
                        _ol = (LPNET(x[:, :3], _vl) if getattr(LPNET, 'vin', False) else LPNET(x[:, :3]))[0].cpu().numpy()
                    LPST['lp'] += 1
                    if len(_ol) >= 7: post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 3, 'pts': [float(_ol[3 + j]) * 128.0 - 64.0 for j in range(4)] + ([float(_ol[7 + j]) * 105.0 - 5.0 for j in range(4)] if len(_ol) >= 11 else []), 'ld': -1, 'vT': _vT})   # ★다점 → mode=3
                    else: post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': float(_ol[3]) * 24.0 - 12.0, 'ld': -1, 'vT': _vT})
                else:
                    LPST['rule'] += 1
                    post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 1, 'dOff': 0.0, 'vT': _vT})
            elif len(o) >= 4:   # ★앞점 모델(out=4): o[3]=(lp+8)/16 → lp. 조향은 페이지 추종기, 속도는 규칙(교사 정지 지시 포함). 2026-09-21 (A)
                post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': float(o[3]) * 24.0 - 12.0, 'ld': -1, 'vT': -1})   # ld=-1: 페이지 Ld(라벨과 동일 기준)   # LP_MAX=12 (train_lp.py 와 일치)
            else:
                post({'on': 1, 'force': 1, 'steer': float(o[0]),
                      'thr': float(o[1]), 'brake': float(o[2])})

        # --- 저장: 모델이 본 화면 + 교사의 정답 ---
        h = hashlib.md5(np.ascontiguousarray(f).tobytes()).digest()
        if h in seen:
            dup += 1
        else:
            seen.add(h)
            X.append((x[0].cpu().numpy() * 255).astype(np.uint8))
            if LAB:   # a_5612 D1: 같은 프레임의 픽셀 라벨(S.npy) — 페이지가 /frame 에 같이 밀어준 PNG
                _lab = C.push_stats().get('lab'); SEG.append(preprocess_label(_lab) if _lab is not None else np.zeros((IMG, IMG), np.uint8)); SEGN[0] += 0 if _lab is not None else 1
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
                          float(d.get('v') or 0), float(g2.get('laneF') or 0), float(g2.get('nl') or 0)] + _ext + [float(g2.get('fin')) if isinstance(g2.get('fin'), (int, float)) else -1.0])   # 12열 fin(목표 차로) — 2026-09-23 11:2x: 정상 경로에 빠져 r1300~1316 이 11열(COND=9 학습 불가)
            except Exception:
                M.append([1e9, 1e9, 1e9, 0, 1e9, 0.0, 0.0, 0.0] + ([float(os.environ.get('ODE_ENV', '0')), float(ep), float(len(X))] if os.environ.get('M_EXT') == '1' else []) + [float(g2.get('fin')) if isinstance(g2.get('fin'), (int, float)) else -1.0])   # 12열 fin = 목표 차로(07:5x 차로 의도)
            Y.append([st, th, br, float(d.get('v') or 0),
                      float(t.get('fl') if t.get('fl') is not None else -1.0),
                      float(t.get('fr') if t.get('fr') is not None else -1.0)])
            P.append([float(o[0]), float(o[1]), float(o[2]), float(o[3]) if len(o) > 3 else 0.0] if net is not None else [0.0, 0.0, 0.0, 0.0])   # 4열: lp 또는 vT 헤드(2026-09-22)
            TN.append([float(_nt), float(_nc), float(_ntraw)])
            _lbh = C.push_stats().get('lbl') if hasattr(C, 'push_stats') else None
            _lpm = _lbh.get('lpm') if isinstance(_lbh, dict) else None; _lpm = [float(z) for z in _lpm] if isinstance(_lpm, list) and len(_lpm) == 4 else [float('nan')] * 4   # ★u_5547 10/20/40/80m 앞 경로점 횡오프셋
            _lfm = _lbh.get('lfm') if isinstance(_lbh, dict) else None; _lfm = [float(z) for z in _lfm] if isinstance(_lfm, list) and len(_lfm) == 4 else [float('nan')] * 4   # 전방거리(07:3x 코너 보정)
            if os.environ.get('L12') == '1':   # ★a_5598: 차로 기하 12열 라벨(/tel geo) — ey epsi k0 lc10 lc20 lc40 li nl lw dl dr valid
                _g = d.get('geo') or {}; _lc = _g.get('lc') or [None, None, None]
                _f = lambda z: float(z) if isinstance(z, (int, float)) else float('nan')
                LP.append([_f(_g.get('ey')), _f(_g.get('epsi')), _f(_g.get('k0')), _f(_lc[0]), _f(_lc[1]), _f(_lc[2]), _f(_g.get('li')), _f(_g.get('nl')), _f(_g.get('lw')), _f(_g.get('dl')), _f(_g.get('dr')), float(_g.get('v') or 0)])
            else: LP.append(([float(_lbh['lp']), float(_lbh.get('ld') or 10.0), float(_lbh['vmax']) if isinstance(_lbh.get('vmax'), (int, float)) else float('nan')] if isinstance(_lbh, dict) and isinstance(_lbh.get('lp'), (int, float)) else [float('nan'), float('nan'), float('nan')]) + _lpm + _lfm)   # [lp, ld, vmax, lp10..lp80, lf10..lf80]
            _dq = d.get('da') or {}; _ps = d.get('pos') if isinstance(d.get('pos'), list) and len(d.get('pos')) >= 2 else [float('nan'), float('nan')]
            _car = d.get('car') or {}
            Q.append([float(_dq.get('xt') if isinstance(_dq.get('xt'), (int, float)) else 99.0), float(d.get('tpN') or 0), float(d.get('cr') or 0), time.time() - t0,
                      float(_ps[0]), float(_ps[1]), float(d.get('prog') or 0), float(_car.get('ang') if isinstance(_car.get('ang'), (int, float)) else float('nan'))])   # 8열(2026-09-24 C): car.ang — 오프라인 BEV 라벨용 헤딩   # 4~6열(2026-09-22): pos x,y, prog — 사고 지점을 회귀 케이스로 고정하기 위해(규칙 §6)
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
        'lp_frames': LPST['lp'], 'rule_steer_frames': LPST['rule'],
        'lane_err_m': round(LK['err'] / max(1, LK['n']), 2), 'outlane_pct': round(100 * LK['outlane'] / max(1, LK['n']), 1),
        'label_src': LABEL_SRC[0],
    }
    return (np.stack(X) if X else None,
            np.array(Y, dtype=np.float32) if Y else None, stats,
            np.array(W, dtype=np.float32) if W else None,
            np.array(M, dtype=np.float32) if M else None,
            np.array(P, dtype=np.float32) if P else None,
            np.array(Q, dtype=np.float32) if Q else None,
            np.array(LP, dtype=np.float32) if LP else None,
            np.array(TN, dtype=np.float32) if TN else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--episodes', type=int, default=10)
    ap.add_argument('--secs', type=float, default=45)
    ap.add_argument('--model', default='bc_final.pt')
    ap.add_argument('--tier', default=None, help='관제망 체크포인트(tier_*.pt, TierNet res=64) — 등급별 보수 모드')
    ap.add_argument('--lp-tier', type=int, default=0, help='조향모델이 핸들을 잡는 최대 규칙 등급(0=T0만, 1=T0·T1). 단계적 이양 2단계')
    ap.add_argument('--lp', default=None, help='조향(앞점) 모델 ode_lp*.pt — 규칙 등급 T0 에서만 핸들(단계적 이양, u_5516). 속도 모델(--model ode_v*)과 함께 쓴다')
    a = ap.parse_args()

    dev = require_gpu()
    mp = a.model if os.path.isabs(a.model) else os.path.join(BASE, a.model)
    # ★2026-09-19 u_5431: bc_final.pt 는 옛 DriveNet 구조(h.0/h.2)라 현재 망(h.1/h.4/h.6)에 안 들어간다. 1단계(직진) 데이터는
    #   교사가 몰아 만든다 — `--model none` 이면 추론·조작을 건너뛰고 화면+교사 라벨+W/M 만 저장한다(BC 먼저, DAgger 는 새 모델 뒤).
    global PIPE, SPEED_MODEL, TIER, LPNET
    LPNET = None; LPST['maxT'] = int(a.lp_tier)
    if a.lp:
        _lp = a.lp if os.path.isabs(a.lp) else os.path.join(BASE, a.lp); _sd = torch.load(_lp, map_location=dev)
        LPNET = DriveNet(out=_sd[list(_sd)[-1]].shape[0], vin=any(k.startswith('hv.') for k in _sd), in_ch=int(_sd['f.0.weight'].shape[1]), vdim=vdim_of(_sd)).to(dev); LPNET.load_state_dict(_sd); LPNET.eval(); assert_on_gpu(LPNET)
        print(json.dumps({'lp_net': a.lp, 'gate': 'rule tier<=%d for >=13 frames' % a.lp_tier}), flush=True)
    PIPE = a.model if a.model in ('pipe', 'pipe2', 'pipe3') else False
    SPEED_MODEL = os.path.basename(a.model).startswith('ode_v')
    TIER = None
    if a.tier:
        from train_tier import TierNet
        _tp = a.tier if os.path.isabs(a.tier) else os.path.join(BASE, a.tier)
        TIER = TierNet(res=64).to(dev); TIER.load_state_dict(torch.load(_tp, map_location=dev)); TIER.eval(); assert_on_gpu(TIER)
        print(json.dumps({'tier_net': a.tier}), flush=True)
    if PIPE:
        net = None; print(json.dumps({'mode': 'teacher-'+str(PIPE), 'note': 'driveAuto shadow steer + teacher thr/brake via /ctl at capture rate'}), flush=True)
    elif a.model == 'none':
        net = None; print(json.dumps({'mode': 'teacher-drive', 'note': 'no model; GEOM/teacher drives'}), flush=True)
    else:
        sd = torch.load(mp, map_location=dev)
        out = sd[list(sd)[-1]].shape[0]
        net = DriveNet(out=out, vin=any(k.startswith('hv.') for k in sd), in_ch=int(sd['f.0.weight'].shape[1]), vdim=vdim_of(sd)).to(dev)   # hv.* 키 = 속도 입력, f.0 입력채널 = 프레임 스택 여부
        net.load_state_dict(sd); net.eval()
    if net is not None: assert_on_gpu(net)

    subprocess.run(['open', '-a', 'Google Chrome'], capture_output=True)
    time.sleep(2)
    if C.find_window() is None:
        print(json.dumps({'err': 'no chrome window'})); return
    C.clear_selection()

    outd = os.path.join(BASE, 'data', 'dagger_r%d' % a.round)
    os.makedirs(outd, exist_ok=True)
    AX, AY, ST, AW, AM = [], [], [], [], []; AP = []; AQ = []; AL = []; AT = []
    try:
        for i in range(a.episodes):
            X, Y, s, Wt, Mt, Pt, Qt, Lt, Tt = episode(net, dev, a.secs, i + 1)
            ST.append(s)
            print(json.dumps(s, ensure_ascii=False), flush=True)
            if X is not None:
                AX.append(X); AY.append(Y); AW.append(Wt); AM.append(Mt); AP.append(Pt); AQ.append(Qt); AL.append(Lt); AT.append(Tt)
    finally:
        post({'on': 0, 'steer': 0, 'thr': 0, 'brake': 0})

    if not AX:
        print(json.dumps({'err': 'no frames collected'})); return
    X = np.concatenate(AX); Y = np.concatenate(AY)
    np.save(f'{outd}/X.npy', X); np.save(f'{outd}/Y.npy', Y)
    np.save(f'{outd}/W.npy', np.concatenate(AW))     # 프레임 가중치(u_5426) — 없으면 학습기는 전부 1 로 본다
    np.save(f'{outd}/M.npy', np.concatenate(AM))     # 상황 태그(u_5427) — 단계별(커리큘럼) 프레임 선별용
    np.save(f'{outd}/P.npy', np.concatenate(AP))     # 모델 출력(2026-09-20) — Y(교사)와 나란히
    np.save(f'{outd}/Q.npy', np.concatenate(AQ))     # 프레임 품질 [xt, tpN, cr, t] (u_5478) — 학습기가 xt<0.6·순간이동/사고 ±3초 제외에 쓴다
    np.save(f'{outd}/L.npy', np.concatenate(AL))     # 앞점 라벨 [lp, ld] (2026-09-21, tgt mode=2)
    np.save(f'{outd}/T.npy', np.concatenate(AT))     # 관제망 [ntier, conf, raw] (2026-09-22)
    if LAB and SEG: np.save(f'{outd}/S.npy', np.stack(SEG)); print(json.dumps({'S': len(SEG), 'lab_missing': SEGN[0]}), flush=True)   # a_5612 픽셀 라벨(X 와 1:1)
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

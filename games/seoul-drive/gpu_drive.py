#!/usr/bin/env python3
"""GPU 상주 파이프라인 주행(u_5532/u_5535, 2026-09-22): ScreenCaptureKit 창 캡처(IOSurface, 최대 60fps) → 전처리(툴바 제거·UI 크롭·중앙 0.6·256) →
CoreML 오드(속도 v2 + 앞점 lp, GPU/ANE 상주) → /ctl. 규칙 등급(T0)은 /tel 을 20Hz 로 읽어 게이트. 기존 dagger.py(JPEG/HTTP 13fps) 대비 지연 비교용.
사용: ODE_CROP=0.6 python3 gpu_drive.py --secs 300 --speed ode_v2.mlpackage --lp ode_lp7.mlpackage [--lp-tier 0] [--fps 60]
출력: 초당 처리 프레임, 프레임 타임스탬프→명령 전송 지연(ms) 분포, 에피소드 결과(/tel prog·cr·crk·tpN)."""
import sys, os, time, json, threading, argparse, urllib.request, math
sys.modules['tensorflow'] = None
import numpy as np, cv2, coremltools as ct
import sck_capture as SK, capture as C
from net import cond_vec

UI_CROP_TOP, IMG = 0.236, 256
CROP = float(os.environ.get('ODE_CROP', '0.6') or 0.6)
TEL = 'http://localhost:8901/tel'; CTL = 'http://localhost:8901/ctl'
st = {'frame': None, 't': 0.0, 'tel': {}, 'run': True}

def post(d):
    try: urllib.request.urlopen(urllib.request.Request(CTL, json.dumps(d).encode(), {'Content-Type': 'application/json'}), timeout=1.0).read(); return True
    except Exception: return False

def tel_thread():
    while st['run']:
        try: st['tel'] = json.load(urllib.request.urlopen(TEL, timeout=1.0))
        except Exception: pass
        time.sleep(0.05)

def prep(arr, size=None):   # BGRA 창 프레임 → (1,3,256,256) float32 RGB 0~1 (net.preprocess 와 같은 순서: 툴바 제거 → UI 크롭 → 중앙 크롭 → 리사이즈)
    tb = int(C._cache.get('toolbar', 0)); c = arr[tb:, :, :3]
    c = c[int(round(c.shape[0] * UI_CROP_TOP)):, :, :]
    if 0.2 < CROP < 1.0:
        H0, W0 = c.shape[:2]; h, w = int(H0 * CROP), int(W0 * CROP); y0, x0 = (H0 - h) // 2, (W0 - w) // 2; c = c[y0:y0 + h, x0:x0 + w]
    sz = size or IMG; c = cv2.resize(np.ascontiguousarray(c), (sz, sz), interpolation=cv2.INTER_AREA)[:, :, ::-1]   # BGR→RGB
    return np.ascontiguousarray(c.transpose(2, 0, 1)[None]).astype(np.float32) / 255.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--secs', type=float, default=300); ap.add_argument('--speed', default=None, help='속도 모델 mlpackage; 없으면 속도는 규칙(vT=-1)'); ap.add_argument('--lp', default=None)
    ap.add_argument('--lp-tier', type=int, default=0); ap.add_argument('--oracle', action='store_true', help='a_5619 진단 전용: 망 출력 대신 /tel geo 참값(ey/epsi/k0/lc20)을 같은 명령 경로(12열→MERGE_PLAN→/ctl)에 넣는다. ORACLE_SIGMA=σ(m) 가우시안 잡음. 학습·배포 경로에 절대 사용 금지'); ap.add_argument('--seg', action='store_true', help='D(a_5612): --lp 모델이 차로ID 분할(12×RES×RES 로짓)이면 seg_geo.lane_geo 로 e_y/e_psi/κ/lc20 → --geo 경로 재사용. env SEG_RES=256|384'); ap.add_argument('--bev', action='store_true', help='C: --lp 모델이 BEV 격자(3×64×64 로짓)면 bev_ctl.bev_to_geo 로 (ey,epsi,κ,lc20) 뽑아 --geo 경로로 제어'); ap.add_argument('--geo', action='store_true', help='a_5598 접근A/B: --lp 모델이 12열 기하 헤드(ey epsi k0 lc10/20/40 li nl lw dl dr valid, raw)면 목표차로(/tel want) 차로중심 20m 앞점을 mode=2 lp 로 보낸다'); ap.add_argument('--fps', type=int, default=60); ap.add_argument('--lp-vmax', type=float, default=15.0, help='모델 조향 중 속도 상한 m/s(07:1x 실측: 25m/s 에서 차로 이탈)'); a = ap.parse_args()
    _CU = getattr(ct.ComputeUnit, __import__('os').environ.get('CU', 'CPU_AND_GPU'))  # a_5577: ANE compile fail → default CPU_AND_GPU (env CU=ALL to use ANE)
    ms = ct.models.MLModel(a.speed, compute_units=_CU) if a.speed else None; ml = ct.models.MLModel(a.lp, compute_units=_CU) if a.lp else None
    lp_vdim = 1; lp_k = 1; fbuf = []   # ★A3(u_5602): CoreML img 입력 채널 3K 이면 최근 K 프레임 채널 스택
    if ml is not None:
        try: lp_k = int([i for i in ml.get_spec().description.input if i.name == 'img'][0].type.multiArrayType.shape[1]) // 3
        except Exception: lp_k = 1
    if ml is not None:
        try: lp_vdim = int([i for i in ml.get_spec().description.input if i.name == 'v'][0].type.multiArrayType.shape[-1])
        except Exception: lp_vdim = 1
    def cb(arr, t): st['frame'] = arr; st['t'] = t
    threading.Thread(target=tel_thread, daemon=True).start()
    sz = SK.start(cb, fps=a.fps); print(json.dumps({'window': sz, 'toolbar': C._cache.get('toolbar')}), flush=True)
    post({'tgt': 0, 'mode': 1, 'dOff': 0.0, 'vT': -1, 'lp': 0.0})
    d0 = st['tel'] or {}; t0 = time.time(); cr0 = int(d0.get('cr') or 0); crk0 = dict(d0.get('crk') or {}); tp0 = int(d0.get('tpN') or 0)
    n = 0; lats = []; lpN = 0; hold = 0; down = 0; prev_model = False; handovers = 0; last_t = 0.0; infs = []
    _e = __import__('os').environ; LP_RATE = float(_e.get('LP_RATE', '0.4')); LP_TAU = float(_e.get('LP_TAU', '0.4')); HAND_EXIT = float(_e.get('HAND_EXIT', '0.5'))   # ★a_5588 S1b(u_5589 zigzag): 모델 앞점 횡오프셋 명령 평활 — 변화율 제한 m/s + EMA tau s (0=끔) · 이양 해제 히스테리시스 s(진입 1s 고정)
    POLY = _e.get('POLY', '0') == '1'; POLY_K = int(_e.get('POLY_K', '4')); pbuf = []
    LP_MED = int(_e.get('LP_MED', '1')); med_buf = []; LP_LD = float(_e.get('LP_LD', '0'))
    def truth_lp(d, ld):   # 진단용: 규칙 경로 앞점 참값(da.lpm 10/20/40/80 보간) — 학습·배포 경로 사용 금지
        _m = (d.get('da') or {}).get('lpm')
        return float(np.interp(ld, [10.0, 20.0, 40.0, 80.0], [float(z) for z in _m])) if isinstance(_m, list) and len(_m) == 4 and all(isinstance(z, (int, float)) for z in _m) else float('nan')
    LP_WORLD = int(_e.get('LP_WORLD', '0')); wbuf = []   # ★a_5619: 앞점을 세계좌표 점으로 누적(도로는 안 움직인다) → 현재 차 기준으로 되돌려 직선 적합 → 지연 없이 √N 잡음 억제
    def world_lp(lp, ld, d):
        car = d.get('car') or {}; x, y, ang = car.get('x'), car.get('y'), car.get('ang')
        if not all(isinstance(z, (int, float)) for z in (x, y, ang)): return lp, ld
        ca, sa = math.cos(ang), math.sin(ang); wbuf.append((x + ca * ld - sa * lp, y + sa * ld + ca * lp)); wbuf[:] = wbuf[-LP_WORLD:]
        pts = []
        for wx, wy in wbuf:
            dx, dy = wx - x, wy - y; li = dx * ca + dy * sa; pi = -dx * sa + dy * ca
            if 2.0 < li < 45.0: pts.append((li, pi))
        if len(pts) < 3: return lp, ld
        P = np.array(pts); A = np.stack([P[:, 0], np.ones(len(P))], 1); (sl, ic), *_ = np.linalg.lstsq(A, P[:, 1], rcond=None)
        return float(sl * ld + ic), ld
    SEG_RES = int(_e.get('SEG_RES', '256')); seg_prev = (0.0, 0.0); segN = [0, 0]; SEG_DUMP = _e.get('SEG_DUMP'); seg_dump = []; SEG_MED = int(_e.get('SEG_MED', '1')); seg_buf = []; segU = [0]; SEG_ACC = float(_e.get('SEG_ACC', '0')); acc_t = None; acc_ang = None
    ORACLE_SIGMA = float(_e.get('ORACLE_SIGMA', '0')); ORACLE_SRC = _e.get('ORACLE_SRC', 'geo'); ORACLE_LD = float(_e.get('ORACLE_LD', '0')); rng = np.random.default_rng(0); orcN = [0, 0]; tr_orc = []   # a_5619
    SEG_LD = float(_e.get('SEG_LD', '0')); SEG_CAMFIX = float(_e.get('SEG_CAMFIX', '0'))
    if a.seg:
        __import__('os').environ['RES'] = str(SEG_RES)
        if SEG_LD > 0: __import__('os').environ['LC_AT'] = str(SEG_LD)
        from seg_geo import lane_geo, Accum; accum = Accum(tau=SEG_ACC) if SEG_ACC > 0 else None
    MERGE_PLAN = _e.get('MERGE_PLAN', '0') == '1'; mplan = None; bev_prev = 0.0
    if MERGE_PLAN:
        from merge_plan import MergePlannerKF; mplan = MergePlannerKF(); yaw_prev = None
    RULE_LANE = _e.get('RULE_LANE', '1') == '1'
    LANE_HOLD = _e.get('LANE_HOLD', '0') == '1'; hold_on = False; out_t = None; holdN = 0   # ★u_5604 차로내 유지: |e_y|<0.3m ∧ |e_psi|<2° → 곡률 피드포워드만(직진 유지), |e_y|>0.3 이 0.5s 지속돼야 해제
    sm = None; sm_t = None; print(json.dumps({'lp_rate': LP_RATE, 'lp_tau': LP_TAU, 'hand_exit': HAND_EXIT, 'poly': POLY, 'poly_k': POLY_K}), flush=True)
    LP_TRACE = _e.get('LP_TRACE'); tr_hand = []; tr_raw = []   # ★a_5588 addendum2: 흔들림 원인 귀속용 프레임 추적(이양 시각·모델 lp20 원값/평활값)
    wv = []; wv_now = None; wv_ang = None   # ★a_5581 S2 흔들림 지표(u_5578/5579): 직선·완만 T0 구간의 g2.lat(도로 절대 횡위치) 시계열
    while time.time() - t0 < a.secs:
        SK.pump(0.002)
        if st['frame'] is None or st['t'] == last_t: continue
        last_t = st['t']; arr = st['frame']; d = st['tel'] or {}
        v = float(d.get('v') or 0.0); x = prep(arr); vin = np.array([[v / 30.0]], np.float32)
        ti = time.time()
        if ms is not None: o = ms.predict({'img': x, 'v': vin}); o = list(o.values())[0].ravel(); vT = max(0.0, float(o[3]) * 30.0)
        else: vT = -1.0   # 규칙 속도
        tier = d.get('tier'); tier = int(tier) if isinstance(tier, (int, float)) else 3
        # ★u_5539 판정기 깜빡임: 진입 1초 유지 + ★되돌림도 0.5초 유지(순간 T3 1프레임에 핸들이 튀지 않게). 도로이탈·명령 끊김(T3 이 offroad/stale 인 경우)은 즉시.
        if tier <= a.lp_tier: hold += 1; down = 0
        else:
            down += 1
            if tier == 3 and (d.get('offroad') or (d.get('mdl') or {}).get('stale')): hold = 0
            elif down >= int(a.fps * HAND_EXIT): hold = 0
        model_now = (ml is not None or a.oracle) and hold >= a.fps
        if (ml is None or model_now) and d.get('now') != wv_now:   # 조향 주체(규칙 or 모델)가 실제로 핸들 잡는 동안, /tel 갱신마다 1표본(20Hz). 게이트: 회전까지 >80m ∧ 헤딩 변화 완만 ∧ 주행 중(aTurn 은 다음 회전 종류라 직진 판정에 안 씀). 도로(sw) 바뀌면 lat 기준이 바뀌므로 구간 분리
            wv_now = d.get('now'); g2w = ((d.get('tch') or {}).get('g2') or {}); ang = (d.get('car') or {}).get('ang'); latw = g2w.get('lat')
            if float(g2w.get('aD') or 1e9) > 80 and v > 3 and isinstance(latw, (int, float)) and isinstance(ang, (int, float)) and wv_ang is not None and abs(ang - wv_ang) < 0.02: wv.append((time.time(), float(latw), g2w.get('sw')))
            wv_ang = ang if isinstance(ang, (int, float)) else None
        if model_now != prev_model: handovers += 1; prev_model = model_now; tr_hand.append((time.time(), 1 if model_now else 0, tier))
        if not model_now: sm = None
        if model_now: vT = min(vT, a.lp_vmax) if vT >= 0 else a.lp_vmax   # ★모델 조향 중 속도 상한
        if model_now:   # 1초 이상 이양 등급 유지 시 모델 조향
            vl = vin
            if lp_vdim == 8:
                g2 = ((d.get('tch') or {}).get('g2') or {}); vl = cond_vec(v, g2.get('aTurn') or 'S', g2.get('aD'), g2.get('laneF'), g2.get('nl'))[None]
            xin = x
            if a.seg and SEG_RES != IMG: xin = prep(arr, SEG_RES)
            if lp_k > 1:
                fbuf.append(x); fbuf[:] = fbuf[-lp_k:]
                while len(fbuf) < lp_k: fbuf.insert(0, fbuf[0])
                xin = np.concatenate(fbuf, 1)   # (1,3K,256,256) 과거→현재
            if a.oracle and ORACLE_SRC == 'da':   # 이분 R2: 규칙 추종기 자체 앞점(da.lp/ld)을 /ctl 로 되먹임 = 인터페이스(지연·신선도)만 검사
                _da = d.get('da') or {}
                if not (isinstance(_da.get('lp'), (int, float)) and isinstance(_da.get('ld'), (int, float))): post({'tgt': 0, 'mode': 1}); orcN[1] += 1; continue
                _dlp = float(_da['lp']) + (float(rng.normal(0, ORACLE_SIGMA)) if ORACLE_SIGMA > 0 else 0.0)   # 지각 잡음 허용치 σ 스위프(프레임 독립 가우시안)
                if ORACLE_LD > 0 and isinstance(_da.get('lpm'), list) and len(_da['lpm']) == 4 and all(isinstance(z, (int, float)) for z in _da['lpm']):   # 앞점 거리 고정(10/20/40/80 보간): Ld↑ → 잡음 민감도↓ 검증
                    _dlp = float(np.interp(ORACLE_LD, [10.0, 20.0, 40.0, 80.0], [float(z) for z in _da['lpm']])) + (float(rng.normal(0, ORACLE_SIGMA)) if ORACLE_SIGMA > 0 else 0.0); _da = dict(_da, ld=ORACLE_LD)
                if LP_MED > 1: med_buf.append(_dlp); med_buf[:] = med_buf[-LP_MED:]; _dlp = float(np.median(med_buf))
                _dld = float(_da['ld'])
                if LP_WORLD > 0: _dlp, _dld = world_lp(_dlp, _dld, d)
                orcN[0] += 1; lpN += 1; post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': _dlp, 'ld': _dld, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': 0.0}); tr_raw.append((time.time(), float(_da['lp']), float(_da['lp']))); continue
            if a.oracle:   # ★a_5619 ORACLE: 참값을 12열 형식으로(train_geo SCALE 역변환). 망 호출 없음(지연 경로는 동일: 캡처 틱 → /tel → 명령)
                _go = d.get('geo') or {}; _gl = _go.get('lc') or [None, None, None]
                if not (_go.get('v') and isinstance(_gl[1], (int, float))): post({'tgt': 0, 'mode': 1}); orcN[1] += 1; continue   # 무효(교차로 오투영 등) → 규칙
                _oe, _op, _ok, _ol20 = float(_go['ey']), float(_go['epsi']), float(_go.get('k0') or 0.0), float(_gl[1])
                if ORACLE_SIGMA > 0: _oe += float(rng.normal(0, ORACLE_SIGMA)); _ol20 += float(rng.normal(0, ORACLE_SIGMA))
                _lio = float(_go.get('li') or 0); orcN[0] += 1; tr_orc.append((time.time(), float(d.get('now') or 0), _oe, _op))
                ol = np.array([_oe / 2.0, _op / 0.5, _ok / 0.05, 0.0, _ol20 / 16.0, 0.0, _lio / 8.0, 0.0, 3.25 / 5.0, 0.0, 0.0, 1.0], dtype=np.float64); lpN += 1
            else: ol = list(ml.predict({'img': xin, 'v': vl}).values())[0].ravel(); lpN += 1
            ol = np.array(ol, dtype=np.float64); k = 4 if (len(ol) >= 7 and not (a.geo or a.bev or a.seg or a.oracle)) else 1; lat_m = (ol[3:3 + k] * 128.0 - 64.0) if k == 4 else np.array([ol[3] * 24.0 - 12.0]); tn = time.time(); raw20 = float(lat_m[1] if k == 4 else lat_m[0])
            if LP_MED > 1 and not (a.geo or a.bev or a.seg or a.oracle):   # a_5619: 시간 중앙값 N 프레임(지연 ≈N/2 프레임, EMA 보다 위상지연 작음) — 프레임 잡음 억제
                med_buf.append(lat_m.copy()); med_buf[:] = med_buf[-LP_MED:]; lat_m = np.median(np.stack(med_buf), 0)
                if k == 4: ol[3:7] = (lat_m + 64.0) / 128.0
                else: ol[3] = (lat_m[0] + 12.0) / 24.0
            if (LP_RATE > 0 or LP_TAU > 0) and not (a.geo or a.bev or a.seg or a.oracle):   # 명령측 평활(픽셀 모델 출력은 그대로, /ctl 로 보내는 횡오프셋만)
                if sm is None: sm = lat_m.copy(); sm_t = tn
                else:
                    dt = max(1e-3, tn - sm_t); sm_t = tn
                    if LP_RATE > 0: lat_m = np.clip(lat_m, sm - LP_RATE * dt, sm + LP_RATE * dt)
                    sm = sm + (dt / (LP_TAU + dt)) * (lat_m - sm) if LP_TAU > 0 else lat_m
                if k == 4: ol[3:7] = (sm + 64.0) / 128.0
                else: ol[3] = (sm[0] + 12.0) / 24.0
            if LP_TRACE and not (a.geo or a.bev or a.seg or a.oracle): tr_raw.append((tn, raw20, float(sm[1] if (sm is not None and k == 4) else (sm[0] if sm is not None else raw20))))
            if a.seg:   # ★D: 마스크 → 현재 차로(규칙층 laneF+1) 기하 → 12열 형식(BEV 경로와 같은 재구성). 목표 차로 이동(shift)은 아래 _lp/planner 가 더한다
                _mk = np.asarray(ol, dtype=np.float32).reshape(12, SEG_RES, SEG_RES).argmax(0).astype(np.uint8)
                _geo = d.get('geo') or {}; _rl = _geo.get('rl'); _lis = _geo.get('li')   # 목표 차로 = 경로 의도 rl(규칙층, 라벨 번호 규약), 없으면 지도상 현재 차로 li+1. 교사 laneF 는 실제 차로가 아니다(D-00)
                _tc = int(_rl) if isinstance(_rl, (int, float)) and _rl >= 1 else (int(_lis) + 1 if isinstance(_lis, (int, float)) else 1); _lfv = float(_tc - 1)
                _gs = lane_geo(_mk, _tc); _det = np.isfinite(_gs['ey'])
                if SEG_CAMFIX != 0 and _det and isinstance(d.get('camErr'), (int, float)):   # 화면 기울기(카메라 회전 지연) 보정: 화면 기준 (ld, lc) → 차 기준 회전
                    _ce = SEG_CAMFIX * float(d['camErr']); _ldc = SEG_LD if SEG_LD > 0 else 20.0
                    _gs = dict(_gs, ep=_gs['ep'] - _ce, lc20=float(_gs['lc20'] * math.cos(_ce) - _ldc * math.sin(_ce)))
                if SEG_ACC > 0:   # orch NEXT: 규칙층 자차운동 보상 누적(τ=SEG_ACC s) → 누적 목표차로 맵에서 기하. 미결정 프레임은 워프만(상태 유지)
                    _tn2 = time.time(); _dt = (_tn2 - acc_t) if acc_t else 0.03; acc_t = _tn2
                    _ang2 = (d.get('car') or {}).get('ang'); _dps = ((_ang2 - acc_ang + math.pi) % (2 * math.pi) - math.pi) if (isinstance(_ang2, (int, float)) and acc_ang is not None) else 0.0; acc_ang = _ang2 if isinstance(_ang2, (int, float)) else acc_ang
                    accum.step(_mk, v, _dps, min(_dt, 0.2), determined=_det); _ga = accum.geo(_tc)
                    if np.isfinite(_ga['ey']): _gs = _ga; _det = True
                if not _det:   # 교차로·회전 등 미결정: 규칙 조향에 넘긴다(직전 e_y 유지는 우회전 진입에서 건물로 몰았다, 기아 회귀 실측)
                    segN[0] += 1; segU[0] += 1; post({'tgt': 0, 'mode': 1}); seg_buf.clear(); continue
                seg_prev = (_gs['ey'], _gs['lc20']); segN[0] += 1; segN[1] += int(_gs['used'] == _tc)
                if SEG_MED > 1:   # 시간 중앙값(프레임 N): 픽셀 양자화·마스크 깜빡임 억제(e_y, e_psi, lc20)
                    seg_buf.append((_gs['ey'], _gs['ep'], _gs['lc20'])); seg_buf[:] = seg_buf[-SEG_MED:]; _mb = np.median(np.array(seg_buf), 0); _gs = dict(_gs, ey=float(_mb[0]), ep=float(_mb[1]), lc20=float(_mb[2]))
                if SEG_DUMP and segN[0] % 20 == 0 and len(seg_dump) < 30: seg_dump.append((xin[0].copy(), _mk.copy(), _lfv, _gs['ey'], _gs['used']))   # 진단: 입력·마스크 표본
                ol = np.array([_gs['ey'] / 2.0, _gs['ep'] / 0.5, _gs['k0'] / 0.05, 0.0, _gs['lc20'] / 16.0, 0.0, _lfv / 8.0, 0.0, 3.25 / 5.0, 0.0, 0.0, 1.0], dtype=np.float64)
            if a.bev and len(ol) >= 3 * 64 * 64:   # ★C: BEV 격자 → 기하 4값 → 아래 --geo 경로 재사용(ol 을 12열 형식으로 재구성)
                from bev_ctl import bev_to_geo
                _g2b = ((d.get('tch') or {}).get('g2') or {}); _lfb = _g2b.get('laneF'); _wb = _g2b.get('want'); _sh = ((float(_wb) - float(_lfb)) * 3.25) if isinstance(_lfb, (int, float)) and isinstance(_wb, (int, float)) else 0.0
                _r = bev_to_geo(np.asarray(ol, dtype=np.float32).reshape(3, 64, 64), _sh, bev_prev)
                if _r is None: _r = (bev_prev, 0.0, 0.0, 0.0)
                bev_prev = _r[0]; _lfv = float(_lfb) if isinstance(_lfb, (int, float)) else 0.0
                ol = np.array([_r[0] / 2.0, _r[1] / 0.5, _r[2] / 0.05, 0.0, (_r[3] - _sh) / 16.0, 0.0, _lfv / 8.0, 0.0, 3.25 / 5.0, 0.0, 0.0, 1.0], dtype=np.float64)
            if (a.geo or a.bev or a.seg or a.oracle) and len(ol) >= 12:   # 기하 헤드 디코딩(train_geo SCALE): ey=o0*2 epsi=o1*.5 k0=o2*.05 lc=o3..5*16 li=o6*8 nl=o7*8
                _ey, _ep, _k0 = float(ol[0]) * 2.0, float(ol[1]) * 0.5, float(ol[2]) * 0.05; _lc20 = float(ol[4]) * 16.0; _li = float(ol[6]) * 8.0; _nl = max(1.0, float(ol[7]) * 8.0); _lw = 3.25
                _g2 = ((d.get('tch') or {}).get('g2') or {}); _want = _g2.get('want'); _tgt = float(_want) if isinstance(_want, (int, float)) else round(_li)
                _lf = _g2.get('laneF')   # ★A'(2026-09-24 orch): 차로번호·차로수·목표차로는 규칙층(지도/경로)에서; 망은 국소 기하만. 망 li 는 보조 로그
                if RULE_LANE and isinstance(_lf, (int, float)): _li = float(_lf)
                _lp = _lc20 + (_tgt - round(_li)) * _lw   # 목표 차로 중심의 20m 앞 횡오프셋(차 기준)
                _ld = SEG_LD if (a.seg and SEG_LD > 0) else 20.0   # a_5619: seg 경로 앞점 거리 고정(LC_AT 와 같이)
                if MERGE_PLAN:
                    _ang = (d.get('car') or {}).get('ang'); _yr = None
                    if isinstance(_ang, (int, float)):
                        if yaw_prev is not None: _dth = (_ang - yaw_prev[0] + math.pi) % (2 * math.pi) - math.pi; _yr = _dth / max(1e-3, time.time() - yaw_prev[1])
                        yaw_prev = (_ang, time.time())
                    _lp, _h = mplan.step(time.time(), _ey, _ep, _k0, v, _yr, (_tgt - round(_li)) * _lw); holdN += int(_h)
                if LANE_HOLD and not MERGE_PLAN:
                    tn2 = time.time(); inb = abs(_ey) < 0.3 and abs(_ep) < math.radians(2.0)
                    if hold_on:
                        if abs(_ey) > 0.3: out_t = out_t or tn2; hold_on = not (tn2 - out_t >= 0.5)
                        else: out_t = None
                    elif inb: hold_on = True; out_t = None
                    if hold_on: _lp = 200.0 * _k0 + (_tgt - round(_li)) * _lw; holdN += 1   # 곡률만: 20m 앞 차로중심 ≈ ½·κ·L²
                if POLY:   # ★접근 B-lite(2026-09-24 03:4x): 같은 헤드의 3점(10/20/40m)을 폴리라인으로 보고, 속도 비례 앞점 Ld 에서 보간 + 최근 K 프레임 시간 앙상블(중앙값)
                    _pts = np.array([float(ol[3]) * 16.0, _lc20, float(ol[5]) * 16.0]); pbuf.append(_pts)
                    if len(pbuf) > POLY_K: pbuf.pop(0)
                    _pm = np.median(np.array(pbuf), 0); _ld = float(np.clip(0.9 * v + 6.0, 8.0, 24.0))
                    _lc = float(np.interp(_ld, [10.0, 20.0, 40.0], _pm)); _lp = _lc + (_tgt - round(_li)) * _lw
                if LP_RATE > 0 or LP_TAU > 0:
                    tn = time.time()
                    if sm is None: sm = np.array([_lp]); sm_t = tn
                    else:
                        dt = max(1e-3, tn - sm_t); sm_t = tn
                        if LP_RATE > 0: _lp = float(np.clip(_lp, sm[0] - LP_RATE * dt, sm[0] + LP_RATE * dt))
                        sm = sm + (dt / (LP_TAU + dt)) * (_lp - sm) if LP_TAU > 0 else np.array([_lp])
                    _lp = float(sm[0])
                post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': _lp, 'ld': _ld, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': round((time.time() - ti) * 1000, 1), 'geo': [round(_ey, 2), round(_ep, 3), round(_lc20, 2), round(_li, 2)], 'hold': 1 if (LANE_HOLD and hold_on) else 0})
                if LP_TRACE: tr_raw.append((time.time(), truth_lp(d, _ld), _lp))   # (t, 참값 lp@ld, 모델 lp) — 진단
            elif len(ol) >= 7:   # ★다점(10/20/40/80m, ±64m 인코딩; 11출력이면 전방거리 4 추가) → 페이지 mode=3
                if LP_LD > 0:   # a_5619: 앞점 거리 고정(참값 실측: 속도기반 Ld(8~24m) σ.4 → 37/분, 고정 20m → 12.6): pts 보간 → mode 2
                    _lpf = float(np.interp(LP_LD, [10.0, 20.0, 40.0, 80.0], [float(ol[3 + j]) * 128.0 - 64.0 for j in range(4)]))
                    post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': _lpf, 'ld': LP_LD, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': round((time.time() - ti) * 1000, 1)}); tr_raw.append((time.time(), truth_lp(d, LP_LD), _lpf)); continue
                if LP_WORLD > 0:   # a_5619: 모델 lp(페이지 Ld 에 보간) → 세계좌표 누적 직선적합 → mode 2 단일 앞점
                    _dal = (d.get('da') or {}).get('ld'); _ldw = float(_dal) if isinstance(_dal, (int, float)) and _dal > 0 else 20.0
                    _lpw = float(np.interp(_ldw, [10.0, 20.0, 40.0, 80.0], [float(ol[3 + j]) * 128.0 - 64.0 for j in range(4)])); _lpw, _ldw = world_lp(_lpw, _ldw, d)
                    post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': _lpw, 'ld': _ldw, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': round((time.time() - ti) * 1000, 1)}); tr_raw.append((time.time(), raw20, _lpw)); continue
                post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 3, 'pts': [float(ol[3 + j]) * 128.0 - 64.0 for j in range(4)] + ([float(ol[7 + j]) * 105.0 - 5.0 for j in range(4)] if len(ol) >= 11 else []), 'ld': -1, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': round((time.time() - ti) * 1000, 1)})
            else:
                post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 2, 'lp': float(ol[3]) * 24.0 - 12.0, 'ld': -1, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': round((time.time() - ti) * 1000, 1)})
        else:
            post({'on': 1, 'force': 1, 'tgt': 1, 'mode': 1, 'dOff': 0.0, 'vT': vT, 'lat': round((time.time() - last_t) * 1000, 1), 'inf': round((time.time() - ti) * 1000, 1)})
        infs.append((time.time() - ti) * 1000); lats.append((time.time() - last_t) * 1000); n += 1
        if d.get('arrived') or (isinstance(d.get('prog'), (int, float)) and d['prog'] >= 0.95): break
    st['run'] = False; SK.stop(); post({'tgt': 0, 'mode': 1, 'dOff': 0.0, 'vT': -1, 'lp': 0.0, 'on': 0, 'release': 1})
    d = st['tel'] or {}; secs = time.time() - t0
    crk = {k: int(v) - int(crk0.get(k, 0)) for k, v in (d.get('crk') or {}).items() if int(v) - int(crk0.get(k, 0)) > 0}
    if LP_TRACE: np.savez(LP_TRACE + '_' + time.strftime('%H%M%S') + '.npz', wv=np.array([(q[0], q[1]) for q in wv], dtype=np.float64), hand=np.array(tr_hand, dtype=np.float64), raw=np.array(tr_raw, dtype=np.float64))
    if a.oracle and LP_TRACE: np.save(LP_TRACE + '_oracle.npy', np.array(tr_orc, np.float64))   # (t_cmd, t_tel(now), ey_in, epsi_in)
    if SEG_DUMP and seg_dump: np.savez_compressed(SEG_DUMP, x=np.stack([z[0] for z in seg_dump]), m=np.stack([z[1] for z in seg_dump]), lf=np.array([z[2] for z in seg_dump]), ey=np.array([z[3] for z in seg_dump]), used=np.array([z[4] for z in seg_dump]))
    weave = None   # p95 진폭(2초 이동평균 대비 편차, 정상 오프셋은 벌점 X) · 부호 교차/분(히스테리시스 0.1m) · score=amp_p95×sc_min
    if len(wv) >= 40:
        segs = []; cur = []
        for q in wv:
            if cur and (q[2] != cur[-1][2] or q[0] - cur[-1][0] > 1.0 or abs(q[1] - cur[-1][1]) > 0.5): segs.append(cur); cur = []   # 도로 바뀜·표본 끊김·lat 기준 점프(>0.5m/50ms, 조각 방향 반전) = 구간 분리
            cur.append(q)
        segs.append(cur); devs = []; sc = 0; mins = 0.0
        for sg in segs:
            if len(sg) < 20: continue
            tw = np.array([q[0] for q in sg]); lw = np.array([q[1] for q in sg]); rm = np.array([lw[(tw >= t - 1.0) & (tw <= t + 1.0)].mean() for t in tw]); dev = lw - rm; devs += list(dev); mins += (tw[-1] - tw[0]) / 60.0; sgn = 0
            for x in dev:
                if x > 0.1 and sgn <= 0: sc += (sgn < 0); sgn = 1
                elif x < -0.1 and sgn >= 0: sc += (sgn > 0); sgn = -1
        mins = max(1e-6, mins); ap = float(np.percentile(np.abs(devs), 95)) if devs else 0.0
        weave = {'n': int(len(wv)), 'min': round(float(mins), 2), 'amp_p95': round(ap, 3), 'sc_min': round(sc / mins, 2), 'score': round(ap * sc / mins, 3)}
    print(json.dumps({'secs': round(secs, 1), 'frames': n, 'hz': round(n / secs, 1), 'lat_ms_p50': round(float(np.median(lats)), 1) if lats else None, 'lat_ms_p90': round(float(np.percentile(lats, 90)), 1) if lats else None,
                      'inf_ms_p50': round(float(np.median(infs)), 2) if infs else None, 'lp_frames': lpN, 'seg_target_found': (round(segN[1] / segN[0], 3) if segN[0] else None), 'seg_undetermined': (round(segU[0] / segN[0], 3) if segN[0] else None), 'oracle_frames': orcN[0], 'oracle_invalid': orcN[1], 'oracle_sigma': ORACLE_SIGMA, 'handovers': handovers, 'prog': d.get('prog'), 'crashes': int(d.get('cr') or 0) - cr0, 'crash_types': crk, 'tpN': int(d.get('tpN') or 0) - tp0, 'tier_hist': d.get('tierN'), 'weave': weave, 'hold_frames': holdN}, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()

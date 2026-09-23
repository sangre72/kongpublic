#!/usr/bin/env python3
"""GPU 상주 파이프라인 주행(u_5532/u_5535, 2026-09-22): ScreenCaptureKit 창 캡처(IOSurface, 최대 60fps) → 전처리(툴바 제거·UI 크롭·중앙 0.6·256) →
CoreML 오드(속도 v2 + 앞점 lp, GPU/ANE 상주) → /ctl. 규칙 등급(T0)은 /tel 을 20Hz 로 읽어 게이트. 기존 dagger.py(JPEG/HTTP 13fps) 대비 지연 비교용.
사용: ODE_CROP=0.6 python3 gpu_drive.py --secs 300 --speed ode_v2.mlpackage --lp ode_lp7.mlpackage [--lp-tier 0] [--fps 60]
출력: 초당 처리 프레임, 프레임 타임스탬프→명령 전송 지연(ms) 분포, 에피소드 결과(/tel prog·cr·crk·tpN)."""
import sys, os, time, json, threading, argparse, urllib.request
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

def prep(arr):   # BGRA 창 프레임 → (1,3,256,256) float32 RGB 0~1 (net.preprocess 와 같은 순서: 툴바 제거 → UI 크롭 → 중앙 크롭 → 리사이즈)
    tb = int(C._cache.get('toolbar', 0)); c = arr[tb:, :, :3]
    c = c[int(round(c.shape[0] * UI_CROP_TOP)):, :, :]
    if 0.2 < CROP < 1.0:
        H0, W0 = c.shape[:2]; h, w = int(H0 * CROP), int(W0 * CROP); y0, x0 = (H0 - h) // 2, (W0 - w) // 2; c = c[y0:y0 + h, x0:x0 + w]
    c = cv2.resize(np.ascontiguousarray(c), (IMG, IMG), interpolation=cv2.INTER_AREA)[:, :, ::-1]   # BGR→RGB
    return np.ascontiguousarray(c.transpose(2, 0, 1)[None]).astype(np.float32) / 255.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--secs', type=float, default=300); ap.add_argument('--speed', default=None, help='속도 모델 mlpackage; 없으면 속도는 규칙(vT=-1)'); ap.add_argument('--lp', default=None)
    ap.add_argument('--lp-tier', type=int, default=0); ap.add_argument('--fps', type=int, default=60); ap.add_argument('--lp-vmax', type=float, default=15.0, help='모델 조향 중 속도 상한 m/s(07:1x 실측: 25m/s 에서 차로 이탈)'); a = ap.parse_args()
    _CU = getattr(ct.ComputeUnit, __import__('os').environ.get('CU', 'CPU_AND_GPU'))  # a_5577: ANE compile fail → default CPU_AND_GPU (env CU=ALL to use ANE)
    ms = ct.models.MLModel(a.speed, compute_units=_CU) if a.speed else None; ml = ct.models.MLModel(a.lp, compute_units=_CU) if a.lp else None
    lp_vdim = 1
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
    sm = None; sm_t = None; print(json.dumps({'lp_rate': LP_RATE, 'lp_tau': LP_TAU, 'hand_exit': HAND_EXIT}), flush=True)
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
        model_now = ml is not None and hold >= a.fps
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
            ol = list(ml.predict({'img': x, 'v': vl}).values())[0].ravel(); lpN += 1
            ol = np.array(ol, dtype=np.float64); k = 4 if len(ol) >= 7 else 1; lat_m = (ol[3:3 + k] * 128.0 - 64.0) if k == 4 else np.array([ol[3] * 24.0 - 12.0]); tn = time.time(); raw20 = float(lat_m[1] if k == 4 else lat_m[0])
            if LP_RATE > 0 or LP_TAU > 0:   # 명령측 평활(픽셀 모델 출력은 그대로, /ctl 로 보내는 횡오프셋만)
                if sm is None: sm = lat_m.copy(); sm_t = tn
                else:
                    dt = max(1e-3, tn - sm_t); sm_t = tn
                    if LP_RATE > 0: lat_m = np.clip(lat_m, sm - LP_RATE * dt, sm + LP_RATE * dt)
                    sm = sm + (dt / (LP_TAU + dt)) * (lat_m - sm) if LP_TAU > 0 else lat_m
                if k == 4: ol[3:7] = (sm + 64.0) / 128.0
                else: ol[3] = (sm[0] + 12.0) / 24.0
            if LP_TRACE: tr_raw.append((tn, raw20, float(sm[1] if (sm is not None and k == 4) else (sm[0] if sm is not None else raw20))))
            if len(ol) >= 7:   # ★다점(10/20/40/80m, ±64m 인코딩; 11출력이면 전방거리 4 추가) → 페이지 mode=3
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
                      'inf_ms_p50': round(float(np.median(infs)), 2) if infs else None, 'lp_frames': lpN, 'handovers': handovers, 'prog': d.get('prog'), 'crashes': int(d.get('cr') or 0) - cr0, 'crash_types': crk, 'tpN': int(d.get('tpN') or 0) - tp0, 'tier_hist': d.get('tierN'), 'weave': weave}, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()

#!/usr/bin/env python3
"""모델 주행 사고 분류 하네스 (a_5102).

기존 drive_test.py 의 GUI 절차(경로 설정 → 목적지 가기)를 재사용하고,
사고 종류별 카운터는 화면 글자를 읽지 않고 /tel 텔레메트리로 받는다
(이 프로젝트는 스크린샷 글자 판독 금지 — 오독 사고 이력).

사용: python3 crash_probe.py <목적지> --secs 40 [--model bc_final.pt|geom]
"""
import argparse, json, subprocess, sys, time, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive_test as DT

BASE = 'http://localhost:8901'


def tel():
    try:
        return json.loads(urllib.request.urlopen(BASE + '/tel', timeout=1).read())
    except Exception:
        return {}


def ctl(d):
    try:
        urllib.request.urlopen(urllib.request.Request(
            BASE + '/ctl', json.dumps(d).encode(),
            {'Content-Type': 'application/json'}), timeout=1).read()
    except Exception:
        pass


def setup_route(dest):
    DT.chrome_front()
    subprocess.run([DT.KT, 'input', 'chord', 'cmd', 'r', '--yes'], capture_output=True)
    time.sleep(14)
    # ★a11y 로 '도착' 입력칸을 직접 찾는다. drive_test.probe_buttons 의
    #   '버튼과 같은 줄의 AXTextField' 규칙은 u_5096 이후 레이아웃(버튼이 별도
    #   줄로 내려감)에서 맞지 않아 빈 좌표를 집는다 — 실측으로 목적지가 안 들어갔다.
    DT.probe_buttons()
    import re
    pid = DT.sh(['pgrep', '-x', 'Google Chrome']).split()
    out = DT.sh([DT.KT, 'see', '--pid', pid[0], '--a11y'], timeout=60) if pid else ''
    fields = [(int(m.group(1)), int(m.group(2)))
              for m in re.finditer(r'AXTextField\s+@\((\d+),(\d+)\)', out)]
    # 주소창(y<130)을 빼고, '경로 설정' 버튼 바로 위 줄의 칸이 목적지다
    ry = DT.BTN['route'][1]
    cand = [f for f in fields if 130 < f[1] < ry]
    if cand:
        DT.BTN['search'] = max(cand, key=lambda f: f[1])   # 버튼에 가장 가까운 = 도착
    DT.click(*DT.BTN['search']); time.sleep(0.5)
    DT.key('backspace', 40); time.sleep(0.3)
    DT.type_text(dest); time.sleep(1.2)
    DT.click(*DT.BTN['route']); time.sleep(2.5)
    DT.click(*DT.BTN['go']); time.sleep(1.0)
    return dict(DT.BTN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dest')
    ap.add_argument('--secs', type=float, default=40)
    ap.add_argument('--model', default='bc_final.pt')
    ap.add_argument('--no-route', action='store_true')
    a = ap.parse_args()

    ctl({'on': 0, 'steer': 0, 'thr': 0, 'brake': 0})
    btn = {} if a.no_route else setup_route(a.dest)

    t0 = tel()
    crk0 = dict(t0.get('crk') or {})
    cr0 = int(t0.get('cr') or 0)
    p0 = float(t0.get('prog') or 0)

    proc = None
    if a.model != 'geom':
        # 모델 버튼을 켠다 — /ctl on=1 이 켜주므로 추론루프만 띄우면 된다
        proc = subprocess.Popen(
            [sys.executable, 'model_drive.py', '--model', a.model,
             '--secs', str(a.secs)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    trace = []
    t_start = time.time()
    while time.time() - t_start < a.secs:
        d = tel()
        if d:
            trace.append({'t': round(time.time() - t_start, 1),
                          'v': d.get('v'), 'prog': d.get('prog'),
                          'cr': d.get('cr'), 'drv': d.get('drv'),
                          'st': d.get('st'), 'thr': d.get('thr'),
                          'brk': d.get('brk'), 'onroad': d.get('onroad'),
                          'crk': d.get('crk')})
        time.sleep(0.5)

    mo = ''
    if proc:
        try:
            mo = proc.communicate(timeout=20)[0]
        except Exception:
            proc.kill()
    ctl({'on': 0, 'steer': 0, 'thr': 0, 'brake': 0})

    t1 = tel()
    crk1 = dict(t1.get('crk') or {})
    delta = {k: crk1.get(k, 0) - crk0.get(k, 0)
             for k in set(crk1) | set(crk0)
             if crk1.get(k, 0) - crk0.get(k, 0) > 0}
    vs = [x['v'] for x in trace if x.get('v') is not None]
    ps = [x['prog'] for x in trace if x.get('prog') is not None]
    print(json.dumps({
        'dest': a.dest, 'model': a.model, 'secs': a.secs,
        'crash_total': int(t1.get('cr') or 0) - cr0,
        'crash_by_type': delta,
        'prog_start': p0, 'prog_end': (ps[-1] if ps else None),
        'prog_max': (max(ps) if ps else None),
        'prog_gain': round((max(ps) if ps else 0) - p0, 4),
        'v_mean': round(sum(vs) / len(vs), 2) if vs else None,
        'v_max': max(vs) if vs else None,
        'v_zero_pct': round(100.0 * sum(1 for v in vs if v < 0.5) / len(vs), 1) if vs else None,
        'drv': trace[-1]['drv'] if trace else None,
        'onroad_pct': round(100.0 * sum(1 for x in trace if x.get('onroad') == 1) / len(trace), 1) if trace else None,
        'samples': len(trace),
        'model_out': mo.strip().splitlines()[-1] if mo.strip() else '',
        'buttons': btn,
    }, ensure_ascii=False))
    with open('/tmp/crash_trace.json', 'w') as f:
        json.dump(trace, f, ensure_ascii=False)


if __name__ == '__main__':
    main()

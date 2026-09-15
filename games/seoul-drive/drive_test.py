#!/usr/bin/env python3
"""a_5055 — 목적지 도착 자동 테스트 하네스.

오너 u_5052: "목적지 정상 도착할 때까지 반복 테스트·확인·평가·수정".
수동 kongtrol 클릭 + 화면 디코드를 자동화해서, 실패 '지점'을 통계로 뽑는다.

재사용(새로 짜지 않음): capture.grab_canvas() / decode.decode()

판정:
  ARRIVED = progress >= 0.97
  STUCK   = 40초 연속 v<0.5 이고 progress 변화 < 0.002
  TIMEOUT = 시간 초과

★GUI 규칙(a_5055, 실사고 반영):
  · 매 캡처 전 Chrome 활성화 — 안 하면 터미널이 찍힌다.
  · 텍스트 삭제는 backspace 반복. cmd+a 금지(페이지 전체선택 사고).

사용:
  python3 drive_test.py 코엑스 [--timeout 300] [--runs 1]
"""
import argparse, json, subprocess, sys, time

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import capture
import decode as dec

KT = '/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol'

# a11y 좌표(a_5055 브리프). 창 크기가 바뀌면 --probe 로 재조회.
BTN = {'search': (350, 208), 'route': (451, 208), 'go': (545, 208), 'park': (625, 208)}

ARRIVE_P = 0.97
STUCK_SEC = 40.0
STUCK_DP = 0.002
STUCK_V = 0.5
NOPROG_SEC = 60.0    # 움직이는데 진행률이 안 오르는 상태 허용 시간


def sh(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ''


def chrome_front():
    """★매 캡처/입력 전 필수. 백그라운드면 클릭이 조용히 무시되고 캡처엔 터미널이 찍힌다."""
    sh(['osascript', '-e', 'tell application "Google Chrome" to activate'])
    time.sleep(0.4)


def click(x, y):
    chrome_front()
    sh([KT, 'input', 'click', str(x), str(y), '--yes'])


def key(name, repeat=1):
    cmd = [KT, 'input', 'key', name, '--yes']
    if repeat > 1:
        cmd = [KT, 'input', 'key', name, '--repeat', str(repeat), '--yes']
    sh(cmd, timeout=60)


def type_text(s):
    sh([KT, 'input', 'text', s, '--yes'], timeout=60)


def probe_buttons():
    """a11y 로 버튼 좌표 재조회(창 크기 변동 대비). 실패하면 기본값 유지."""
    pid = sh(['pgrep', '-x', 'Google Chrome']).split()
    if not pid:
        return
    out = sh([KT, 'see', '--pid', pid[0], '--a11y'], timeout=60)
    import re
    lines = out.splitlines()
    # 1차: 버튼 먼저(검색창을 버튼 y 기준으로 찾기 때문에 순서가 중요하다)
    for line in lines:
        m = re.search(r'@\((\d+),(\d+)\).*·\s*(경로 설정|목적지 가기|주차)\s*$', line)
        if m:
            x, y, nm = int(m.group(1)), int(m.group(2)), m.group(3)
            BTN[{'경로 설정': 'route', '목적지 가기': 'go', '주차': 'park'}[nm]] = (x, y)
    # 2차: 검색창은 '버튼과 같은 줄'에 있는 AXTextField 다. 값이 비었는지로 고르면
    #      페이지 하단의 다른 입력칸(@170,1317)이 잡힌다(실측 오탐).
    for line in lines:
        m2 = re.search(r'AXTextField\s+@\((\d+),(\d+)\)', line)
        if m2:
            x, y = int(m2.group(1)), int(m2.group(2))
            if abs(y - BTN['route'][1]) <= 6 and x < BTN['route'][0]:
                BTN['search'] = (x, y)


def sample():
    """한 프레임 디코드. 실패하면 None."""
    chrome_front()
    img = capture.grab_canvas()
    if img is None:
        return None
    return dec.decode(img)


def one_run(dest, timeout, poll=1.0):
    t_run = time.time()
    # 1) 새로고침 + 청크 로딩 대기
    chrome_front()
    sh([KT, 'input', 'chord', 'cmd', 'r', '--yes'])
    time.sleep(14)

    # 2) 목적지 입력 — ★backspace 반복으로만 지운다(cmd+a 금지)
    click(*BTN['search'])
    time.sleep(0.5)
    key('backspace', 40)
    time.sleep(0.3)
    type_text(dest)
    time.sleep(1.0)

    # 3) 경로 설정 → 목적지 가기
    click(*BTN['route'])
    time.sleep(2.0)
    click(*BTN['go'])
    time.sleep(1.0)

    t0 = time.time()
    samples = 0
    pmax = 0.0
    crashes = 0
    vsum = 0.0
    vn = 0
    onroad = 0
    decoded = 0
    # STUCK 추적: 저속+진행정지가 연속 유지된 시간
    stall_t0 = None
    stall_p = None
    move_t0 = None
    move_p = None
    stuck_at_p = None
    stuck_at_s = None
    verdict = 'TIMEOUT'
    last = {}

    crash0 = None
    # ★u_5060: 장거리는 타임아웃으로 끊지 않는다. 목적지 도착이 목표다.
    #   사고가 나면 그 자리에서 종료(사고 = 실패), 사고가 없으면 도착까지 간다.
    #   timeout 은 안전장치로만 남긴다(매우 크게).
    while time.time() - t0 < timeout:
        d = sample()
        samples += 1
        if d:
            decoded += 1
            last = d
            p = float(d.get('progress', 0.0))
            v = float(d.get('v', 0.0))
            pmax = max(pmax, p)
            c_now = int(d.get('crashes', 0))
            if crash0 is None: crash0 = c_now
            crashes = max(crashes, c_now)
            if c_now > crash0:                       # ★사고 발생 → 즉시 종료
                verdict = 'CRASHED'
                stuck_at_p = p
                stuck_at_s = round(time.time() - t0, 1)
                break
            vsum += v
            vn += 1
            onroad += int(d.get('on_road', 0))

            if p >= ARRIVE_P:
                verdict = 'ARRIVED'
                break

            # STUCK(사양): 저속 + 진행정지가 STUCK_SEC 이상
            if v < STUCK_V:
                if stall_t0 is None:
                    stall_t0, stall_p = time.time(), p
                elif abs(p - stall_p) >= STUCK_DP:
                    stall_t0, stall_p = time.time(), p      # 진행했으면 타이머 리셋
                elif time.time() - stall_t0 >= STUCK_SEC:
                    verdict = 'STUCK'
                    stuck_at_p = p
                    stuck_at_s = round(time.time() - t0, 1)
                    break
            else:
                stall_t0, stall_p = None, None

            # ★NO_PROGRESS(추가): 차는 움직이는데(v 정상) 진행률이 안 오르는 경우.
            #   실측 1회차 코엑스: avg_v=7.12 인데 progress 0.034 고정 → 사양의 STUCK
            #   조건(v<0.5)에 걸리지 않아 TIMEOUT 으로만 찍혔다. 그러면 '어디서' 막혔는지
            #   기록이 안 남는다. 제자리 선회·경로이탈이 이 형태라 따로 잡는다.
            if move_t0 is None or abs(p - move_p) >= STUCK_DP:
                move_t0, move_p = time.time(), p
            elif time.time() - move_t0 >= NOPROG_SEC:
                verdict = 'NO_PROGRESS'
                stuck_at_p = p
                stuck_at_s = round(time.time() - t0, 1)
                break
        time.sleep(poll)

    return {
        'dest': dest,
        'verdict': verdict,
        't_end': round(time.time() - t0, 1),
        'progress_max': round(pmax, 4),
        'crashes': crashes,
        'stuck_at_progress': round(stuck_at_p, 4) if stuck_at_p is not None else None,
        'stuck_at_s': stuck_at_s,
        'avg_v': round(vsum / vn, 2) if vn else 0.0,
        'onroad_pct': round(100.0 * onroad / decoded, 1) if decoded else 0.0,
        'samples': samples,
        'decoded': decoded,
        'last': {k: (round(v, 3) if isinstance(v, float) else v)
                 for k, v in last.items()
                 if k in ('progress', 'v', 'crashes', 'on_road', 'auto',
                          'wp_idx', 'wp_len', 'path_dist', 'path_angd')},
        'setup_s': round(t0 - t_run, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dest')
    ap.add_argument('--timeout', type=float, default=300)
    ap.add_argument('--runs', type=int, default=1)
    ap.add_argument('--poll', type=float, default=1.0)
    ap.add_argument('--probe', action='store_true', help='a11y 로 버튼 좌표 재조회')
    ap.add_argument('--no-resize', action='store_true', help='창 규격화를 건너뛴다')
    a = ap.parse_args()

    # ★창 규격화를 항상 먼저 한다(u_5078 오너 지시).
    #   창 크기가 바뀌면 캔버스 해상도와 버튼 좌표가 같이 틀어진다. 리사이즈 → 좌표 재조회 순서.
    if not a.no_resize:
        import drive_window
        st = drive_window.ensure()
        print(json.dumps({'window': st}, ensure_ascii=False), file=sys.stderr)
        probe_buttons()          # 창이 바뀌었으니 좌표는 반드시 다시 읽는다
        print(json.dumps({'buttons': BTN}, ensure_ascii=False), file=sys.stderr)
    elif a.probe:
        probe_buttons()
        print(json.dumps({'buttons': BTN}, ensure_ascii=False), file=sys.stderr)

    out = []
    for i in range(a.runs):
        r = one_run(a.dest, a.timeout, a.poll)
        r['run'] = i + 1
        out.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)

    if a.runs > 1:
        n = len(out)
        arr = sum(1 for r in out if r['verdict'] == 'ARRIVED')
        stk = [r for r in out if r['verdict'] in ('STUCK', 'NO_PROGRESS')]
        summary = {
            'runs': n,
            'arrival_rate': round(100.0 * arr / n, 1),
            'verdicts': {v: sum(1 for r in out if r['verdict'] == v)
                         for v in ('ARRIVED', 'STUCK', 'NO_PROGRESS', 'TIMEOUT')},
            'avg_progress_max': round(sum(r['progress_max'] for r in out) / n, 4),
            'avg_crashes': round(sum(r['crashes'] for r in out) / n, 2),
            # 실패 지점 분포: 어느 진행률에서 막히는가
            'stuck_at_progress': sorted(r['stuck_at_progress'] for r in stk
                                        if r['stuck_at_progress'] is not None),
        }
        print(json.dumps({'summary': summary}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()

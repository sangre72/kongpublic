#!/usr/bin/env python3
"""강남역 -> 시청 자율주행 실측 하네스.

WHY 새 파일: drive_test.py 는 목적지 한 칸만 채우는 구형 1행 UI 를 가정한다.
     현재 UI 는 2행이다(출발 필드+[출발지 설정] / 도착 필드+[경로 설정][목적지 가기]).
     출발지를 강남역으로 '명시적으로' 세팅해야 오너 요구(강남역->시청)를 만족한다.

★decode() 는 빨간 사고 오버레이가 화면을 덮는 동안 None 을 돌려준다.
  None 은 '측정값 0' 이 아니라 '측정 불가'다. 절대 데이터로 섞지 않는다.
  대신 연속 None 자체를 사고 신호로 취급한다(오버레이 = 사고 표시).

판정: ARRIVED(progress>=0.97) / CRASHED(crashes 증가) / STUCK / NO_PROGRESS
"""
import argparse, json, re, subprocess, sys, time
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import capture, decode as dec, drive_window

KT = '/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol'
ARRIVE_P, STUCK_SEC, STUCK_DP, STUCK_V, NOPROG_SEC = 0.97, 40.0, 0.002, 0.5, 90.0

UI = {}

def sh(c, t=60):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=t).stdout
    except Exception: return ''

def front():
    sh(['osascript', '-e', 'tell application "Google Chrome" to activate']); time.sleep(0.35)

def click(k):
    """★a11y 의 @x 는 요소에 따라 '중심'이기도 '좌측경계'이기도 하다(실측).
       필드 폭이 34~646px 로 널뛰므로 중심을 계산해 누르되, 화면 밖으로 나가지
       않도록 캔버스 폭(763)에 물린다. 좌측경계+6 도 후보로 재시도한다."""
    front(); x, y = UI[k]
    w = UI.get('_w', {}).get(k, 0)
    if w:                                       # 텍스트필드: 중심 추정
        x = min(max(x, 8), 755) if w < 60 else min(x + 8, 755)
    sh([KT, 'input', 'click', str(x), str(y), '--yes']); time.sleep(0.4)

def probe():
    """a11y 로 UI 좌표를 전부 재조회한다. 하드코딩 금지.

    ★행 귀속은 '출발'/'도착' AXStaticText 라벨 기준이다.
      버튼 기준으로 묶었더니 실패했다 — 인포바가 뜨거나 필드 폭이 변하면
      레이아웃이 2행에서 3행으로 리플로우돼(실측: 버튼 y 270->313) 필드와
      버튼이 더 이상 같은 행이 아니다. 라벨은 항상 자기 필드와 같은 행에 있다.
    """
    pid = sh(['pgrep', '-x', 'Google Chrome']).split()
    if not pid: raise SystemExit('Chrome not running')
    out = sh([KT, 'see', '--pid', pid[0], '--a11y'], 90)
    btn, fields, labels = {}, [], {}
    for ln in out.splitlines():
        m = re.search(r'AXButton\s+@\((\d+),(\d+)\).*·\s*(출발지 설정|경로 설정|목적지 가기|주차|모델|모델 ON)\s*$', ln)
        if m: btn[m.group(3)] = (int(m.group(1)), int(m.group(2)))
        m2 = re.search(r'AXTextField\s+@\((\d+),(\d+)\)\s+\[(\d+)x\d+\]', ln)
        if m2:
            x, y, w = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
            if y > 150: fields.append((x, y, w))       # 주소창(y~102) 제외
        m3 = re.search(r'AXStaticText\s+@\((\d+),(\d+)\).*·\s*(출발|도착)\s*$', ln)
        if m3: labels[m3.group(3)] = int(m3.group(2))
    for need in ('출발지 설정', '경로 설정', '목적지 가기'):
        if need not in btn: raise SystemExit('button not found: %s' % need)
    UI.update({'set_start': btn['출발지 설정'], 'route': btn['경로 설정'],
               'go': btn['목적지 가기']})
    if '모델' in btn or '모델 ON' in btn:
        UI['model'] = btn.get('모델') or btn['모델 ON']
    UI.setdefault('_w', {})
    for lbl, key in (('출발', 'f_start'), ('도착', 'f_dest')):
        if lbl not in labels: continue
        near = [f for f in fields if abs(f[1] - labels[lbl]) <= 10]
        if near:
            x, y, w = near[0]
            UI[key] = (x, y); UI['_w'][key] = w
            UI.setdefault('_row', {})[key] = y
    for k in ('f_start', 'f_dest'):
        if k not in UI:
            raise SystemExit('field not found: %s (fields=%s labels=%s)' % (k, fields, labels))
    return dict(UI)

def field_value(key):
    """a11y 로 그 입력칸의 현재 값을 읽는다. ★화면 눈대중 금지."""
    pid = sh(['pgrep', '-x', 'Google Chrome']).split()
    out = sh([KT, 'see', '--pid', pid[0], '--a11y'], 90)
    ty = UI[key][1]
    for ln in out.splitlines():
        m = re.search(r'AXTextField\s+@\((\d+),(\d+)\)\s+\[\d+x\d+\]\s*·?\s*(.*)$', ln)
        if m and abs(int(m.group(2)) - ty) <= 8:
            return m.group(3).strip()
    return None

def type_into(key, text, tries=8):
    """★입력칸은 '지워졌는지'를 a11y 로 확인하고 친다.

    실사고 2건:
      1) 이전 값 '코엑스' 가 안 지워져 '코엑스시청' 이 들어갔고, 그 상태로 남아있던
         옛 경로(wp_len=243)를 새 경로로 오독했다.
      2) 필드 좌측 끝(x=234)을 클릭하면 포커스가 안 잡혀 backspace 가 통째로 무시된다.
         필드가 34px 로 좁아져 있어서 a11y 의 @x 는 사실상 왼쪽 경계다.
         ⇒ 중심(x + w/2)을 클릭한다. 또 한 번에 20타 넘게 보내면 도중에 포커스가
           풀려 남는다(실측 '엑스코엑스' 에서 멈춤) ⇒ 클릭+20타를 라운드로 반복한다.
    """
    if field_value(key) == text:
        return text                                  # ★이미 맞는 값이면 건드리지 않는다
    for _ in range(tries):
        click(key)                                   # 매 라운드 포커스를 다시 잡는다
        sh([KT, 'input', 'key', 'backspace', '--repeat', '20', '--yes'], 60)
        time.sleep(0.45)
        cur = field_value(key)
        if cur in (None, ''):
            break
    else:
        raise SystemExit('could not clear %s, still %r' % (key, field_value(key)))
    # ★타이핑 뒤에도 값이 틀리면(자동완성이 앞에 끼어드는 실측 사례 '코엑스시청')
    #   지우기+타이핑을 통째로 다시 한다. 확인 없이 진행하면 엉뚱한 목적지로 달린다.
    for _ in range(tries):
        click(key)
        sh([KT, 'input', 'text', text, '--yes'], 60); time.sleep(1.0)
        got = field_value(key)
        if got == text:
            return got
        for _ in range(4):                      # 다시 비운다
            click(key)
            sh([KT, 'input', 'key', 'backspace', '--repeat', '20', '--yes'], 60)
            time.sleep(0.4)
            if field_value(key) in (None, ''):
                break
    raise SystemExit('field %s = %r, expected %r' % (key, field_value(key), text))

def model_btn():
    """[모델] 버튼의 현재 좌표와 라벨을 그때그때 다시 읽는다.
       ★캐시 금지: 레이아웃이 2행/3행으로 리플로우되면 좌표가 (374,313)↔(388,257)
         로 옮겨다니고, 라벨도 '모델'↔'모델 ON' 으로 바뀐다(실측 둘 다 발생)."""
    pid = sh(['pgrep', '-x', 'Google Chrome']).split()
    if not pid: return None
    out = sh([KT, 'see', '--pid', pid[0], '--a11y'], 90)
    for ln in out.splitlines():
        m = re.search(r'AXButton\s+@\((\d+),(\d+)\).*·\s*(모델 ON|모델)\s*$', ln)
        if m: return (int(m.group(1)), int(m.group(2)), m.group(3))
    return None

def model_off():
    """★모델 주행을 끄고 기하(GEOM) 주행으로 되돌린다(a_5085).

    실사고 2건:
      1) /ctl 이 on=1 을 보내 MDL.on 이 켜진 채였고, 모델은 steer=0 thr=0 만
         내보내 차가 v=0 으로 서 있었다(HUD 'DRV=MODEL st=0.00 thr=0.00').
      2) 그걸 끄는 클릭이 옛 좌표로 나가 빗나갔다 — 그 런은 8598m 중 313m 에서
         멈춘 채 끝났다.
    ⇒ 매번 좌표·라벨을 새로 읽고, 라벨이 '모델 ON' 이면 눌러서 끈다.
      setModel(false) 가 userOff=true 를 세워 /ctl 이 다시 켜지 못하게 막는다.
    """
    for _ in range(4):
        b = model_btn()
        if b is None: return 'NO_BTN'
        x, y, label = b
        if label == '모델':                    # 이미 꺼짐
            return 'OFF'
        front()
        sh([KT, 'input', 'click', str(x), str(y), '--yes']); time.sleep(1.2)
    return 'STILL_ON'

def hud_shot(tag):
    """사고 순간 HUD 줄을 그림으로 남긴다. 'cr=N[차로이탈:2]' 같은 종류별 카운터가
       여기에만 있다(디코더 코드픽셀에는 사고 '종류'가 없다)."""
    path = '/tmp/hud_%s.png' % tag
    sh(['screencapture', '-x', '-R0,700,763,180', path])
    return path

def sample():
    front()
    img = capture.grab_canvas()
    return None if img is None else dec.decode(img)

def setup(start, dest, wait):
    capture._cache.clear()          # ★창/인포바가 바뀌면 캡처 rect 가 어긋나 옛 프레임을 읽는다
    # ★첫 CGWindowListCreateImage 는 30초 블록된다(실측). 주행 루프 안에서 맞으면
    #   93초에 2샘플밖에 못 찍는다. 여기서 실제 디코드가 될 때까지 선납한다.
    front()
    for _ in range(5):
        img = capture.grab_canvas()
        if img is not None and dec.decode(img) is not None: break
    # ★?nomodel=1 — /ctl 이 on=1 을 보내도 모델 주행이 안 켜진다(game.js MDL.userOff).
    #   기하(GEOM) 주행을 측정하는 게 목적이므로 항상 이 URL 로 연다.
    sh(['bash', '/Users/bumsuklee/git/kong-bot/games/seoul-drive/reload.sh',
        'http://localhost:8901/index.html?nomodel=1', str(wait)], t=wait + 40)
    probe()
    # ★[모델] 버튼은 누르지 않는다. URL 의 ?nomodel=1 이 MDL.userOff 를 세워
    #   이미 잠가뒀는데, 버튼을 누르면 setModel(true) 가 돌아 userOff=false 로
    #   풀려 버린다 — 실측으로 이 클릭이 오히려 모델 주행을 켰다(HUD DRV=MODEL rx=1195).
    type_into('f_start', start); click('set_start'); time.sleep(1.5)
    type_into('f_dest', dest)
    # ★엔터로 확정한다. 페이지의 onkeydown 이 search+pick 을 직접 돌리고 [목적지 가기]를
    #   활성화한다. 버튼 클릭은 텍스트 길이에 따라 x 가 밀려 불안정하다.
    # ★엔터 직전에 반드시 그 칸을 다시 클릭해 포커스를 잡는다 — type_into 뒤에
    #   포커스가 풀려 있으면 엔터가 페이지로 새고, 목적지가 안 잡힌 채
    #   wp_len=2 짜리 빈 경로가 만들어진다(실측).
    probe()
    for _ in range(6):
        click('f_dest'); time.sleep(0.3)
        sh([KT, 'input', 'key', 'enter', '--yes'], 60); time.sleep(3.5)
        d = sample()
        if d and int(d.get('wp_len', 0)) > 5 and int(d.get('wp_first_ok', 0)) == 1:
            break
    probe()                                  # 확정 후 버튼 좌표 재조회
    for _ in range(8):                       # 경로 생성 대기
        d = sample()
        if d and int(d.get('wp_len', 0)) > 1: return d
        time.sleep(1.0)
    return sample()

def drive(dest, timeout, poll):
    # ★[목적지 가기]를 눌렀는지 auto_on 으로 확증한다. 클릭 성공을 가정하지 않는다.
    #   실사고: 클릭이 안 먹어 auto_on=0 인 채 78초를 서 있었고 STUCK 으로 오분류했다.
    started = False
    for _ in range(4):
        # ★매 시도마다 좌표를 다시 읽는다. model_off() 클릭이나 flash 메시지로
        #   레이아웃이 리플로우되면 [목적지 가기] 가 옮겨가 클릭이 빗나간다
        #   (실측: 버튼 y 270 <-> 313 이동).
        try: probe()
        except SystemExit: pass
        click('go'); time.sleep(1.5)
        d = sample()
        if d and int(d.get('auto_on', 0)) == 1:
            started = True; break
    if not started:
        return {'verdict': 'GO_NOT_ENGAGED', 'model_btn': model_btn(), 'note': 'auto_on stayed 0 after 4 clicks',
                'last': sample(), 'trail': []}
    t0 = time.time()
    pmax, crash0, crashes = 0.0, None, 0
    dec_n, none_streak, max_none = 0, 0, 0
    vsum = vn = onroad = 0
    stall_t0 = stall_p = move_t0 = move_p = None
    verdict, at, last = 'TIMEOUT', None, {}
    trail = []
    while time.time() - t0 < timeout:
        d = sample()
        if d is None:                         # ★None = 측정불가. 데이터로 안 쓴다.
            none_streak += 1; max_none = max(max_none, none_streak)
            time.sleep(poll); continue
        none_streak = 0; dec_n += 1; last = d
        p, v = float(d['progress']), float(d['v'])
        pmax = max(pmax, p); vsum += v; vn += 1; onroad += int(d['on_road'])
        c = int(d['crashes'])
        if crash0 is None: crash0 = c
        crashes = max(crashes, c)
        if len(trail) < 4000:
            trail.append((round(time.time()-t0,1), round(p,4), round(v,2),
                          int(d['wp_idx']), int(d['wp_len']), int(d['on_road']), c))
        if c > crash0:
            verdict = 'CRASHED'; at = d
            at = dict(at); at['hud'] = hud_shot('crash_%d' % int(time.time()))
            at['url'] = sh(['osascript', '-e',
                'tell application "Google Chrome" to get URL of active tab of front window']).strip()
            break
        # ★도착 판정(실측으로 바로잡음).
        #   progress = auto.i/auto.wp.length 인데 auto.i 는 '세그먼트 인덱스'라
        #   끝에서 N-1 로 saturate 한다 — 전 구간(8598/8598m)을 다 달려도
        #   progress 는 0.909 언저리에서 멈춘다. 0.97 임계는 영원히 안 걸린다.
        #   게임의 진짜 도착 처리는 auto.on=0 + '목적지 도착' flash 다.
        #   ⇒ 경로 끝부분에서 auto_on 이 0 으로 떨어지면 도착으로 본다.
        if int(d.get('auto_on', 1)) == 0 and p >= 0.80:
            verdict = 'ARRIVED'; at = dict(d)
            at['hud'] = hud_shot('arrive_%d' % int(time.time()))
            break
        if v < STUCK_V:
            if stall_t0 is None: stall_t0, stall_p = time.time(), p
            elif abs(p - stall_p) >= STUCK_DP: stall_t0, stall_p = time.time(), p
            elif time.time() - stall_t0 >= STUCK_SEC:
                verdict = 'STUCK'; at = d; break
        else: stall_t0 = stall_p = None
        if move_t0 is None or abs(p - move_p) >= STUCK_DP: move_t0, move_p = time.time(), p
        elif time.time() - move_t0 >= NOPROG_SEC:
            verdict = 'NO_PROGRESS'; at = d; break
        time.sleep(poll)
    keep = ('progress','v','crashes','on_road','wp_idx','wp_len','path_dist','path_angd','lane')
    return {'verdict': verdict, 't_s': round(time.time()-t0, 1),
            'progress_max': round(pmax, 4), 'crashes': crashes,
            'fail_at': {k: (round(at[k],3) if isinstance(at[k],float) else at[k])
                        for k in keep} if at else None,
            'avg_v': round(vsum/vn, 2) if vn else 0.0,
            'onroad_pct': round(100.0*onroad/dec_n, 1) if dec_n else 0.0,
            'decoded': dec_n, 'max_none_streak': max_none,
            'last': {k: (round(last[k],3) if isinstance(last[k],float) else last[k])
                     for k in keep} if last else None,
            'trail': trail}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='강남역')
    ap.add_argument('--dest', default='시청')
    ap.add_argument('--timeout', type=float, default=900)
    ap.add_argument('--runs', type=int, default=1)
    ap.add_argument('--poll', type=float, default=1.0)
    ap.add_argument('--wait', type=int, default=15)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    print(json.dumps({'window': drive_window.ensure()}, ensure_ascii=False), file=sys.stderr)
    res = []
    for i in range(a.runs):
        s = setup(a.start, a.dest, a.wait)
        print(json.dumps({'run': i+1, 'after_route': s}, ensure_ascii=False, default=str), file=sys.stderr)
        if not s or int(s.get('wp_len', 0)) <= 1:
            r = {'verdict': 'NO_ROUTE', 'after_route': s}
        else:
            r = drive(a.dest, a.timeout, a.poll)
            r['wp_len'] = int(s['wp_len'])
        r['run'] = i+1
        res.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != 'trail'},
                         ensure_ascii=False, default=str), flush=True)
    if a.out:
        open(a.out, 'w').write(json.dumps(res, ensure_ascii=False, default=str, indent=1))

if __name__ == '__main__':
    main()

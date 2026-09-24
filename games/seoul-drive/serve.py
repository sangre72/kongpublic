"""로컬 개발 서버 (u_5079 오너 지시: 클로드 배포 말고 로컬에서).

WHY charset: python -m http.server 는 Content-Type 에 charset 을 안 붙여서
     한글이 전부 깨진다(실측: '강남대로' -> '媛쒬...'). utf-8 을 명시한다.
WHY no-cache: 빌드할 때마다 새 파일을 봐야 하므로 캐시를 끈다.

★WHY ThreadingTCPServer (2026-09-15): 기존 TCPServer 는 단일 스레드라
  keep-alive 연결 하나가 붙잡으면 서버 전체가 먹통이 된다. 실측으로 그 상태를
  만났다 — ESTABLISHED 3개, curl 이 8초 타임아웃까지 응답 0바이트.
  페이지가 모델 제어채널(/ctl)을 폴링하므로 연결이 상시 유지된다. 스레드 필수.

★/ctl = 모델 주행 제어채널 (a_5085).
  POST /ctl  {"on":1,"steer":..,"thr":..,"brake":..}  ← 파이썬 추론루프가 쓴다
  GET  /ctl  → 같은 JSON                              ← 페이지가 읽는다
  게임은 샌드박스가 아니라 로컬 페이지이므로 fetch 로 바로 읽을 수 있다.
  키보드 주입(drive_infer.py)은 auto.on 일 때 game.js step() 이 키를 통째로
  무시해서 못 쓴다(실측: game.js:1645 `if(!auto.on)` 안에만 키 처리가 있다).
"""
import functools, http.server, socketserver, os, json, threading

PORT = 8901
os.chdir(os.path.dirname(os.path.abspath(__file__)))

_ctl = {'on': 0, 'steer': 0.0, 'thr': 0.0, 'brake': 0.0, 'seq': 0, 'rst': 0, 'tgt': 0, 'dOff': 0.0, 'vT': -1.0, 'mode': 1, 'lp': 0.0, 'ld': 10.0, 'ntier': -1, 'nconf': 0.0, 'lat': -1.0, 'inf': -1.0, 'pts': None,
        'teach': '', 'force': 0, 'release': 0}   # teach = 교사 모드(fwd|left|right|off), u_5144
# ★rst = 소프트리셋 요청 카운터(u_5126). 페이지가 값이 바뀐 걸 보면 한 번 리셋한다.
#   새 엔드포인트/연결을 만들지 않고 이미 20Hz 로 도는 /ctl 폴링에 얹는다.
_gets = [0]   # 페이지가 실제로 폴링하는지 확인용(a_5085 검증)
# ★진단용 텔레메트리(사고 종류별 카운터). 페이지가 /ctl GET 의 쿼리로 올려준다.
#   HUD 텍스트를 스크린샷에서 읽는 것은 이 프로젝트에서 금지(글자 오독 사고)이므로
#   이미 20Hz 로 도는 폴링에 실어 보낸다 — 새 연결도, 새 타이머도 만들지 않는다.
_tel = {}
_lock = threading.Lock()
# ★/frame (2026-09-20, PLAN_ODE §9-1): 페이지가 그린 캔버스 JPEG 를 POST 로 밀어주고, 추론 루프가 GET 으로 읽는다.
#   screencapture 0.7~1.3fps 병목을 우회한다. 페이지는 /ctl 의 push=1 을 볼 때만 보낸다 — 최근 2초 안에 누군가
#   GET /frame 을 했을 때만 켠다(소비자 없으면 비용 0). GET ?since=<seq> 로 같은 프레임은 204 로 돌려보낸다.
import time as _time
_frame = {'b': None, 'seq': 0, 't': 0.0, 'get_t': 0.0, 'posts': 0}


class H(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        t = super().guess_type(path)
        if t in ('text/html', 'application/javascript', 'text/javascript', 'text/css'):
            return t + '; charset=utf-8'
        return t

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def _json(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.split('?')[0] == '/ctl':
            q = self.path.split('?', 1)[1] if '?' in self.path else ''
            with _lock:
                _gets[0] += 1
                if q:
                    import urllib.parse
                    for k, v in urllib.parse.parse_qsl(q):
                        if k == 'tel':
                            try:
                                _tel.clear(); _tel.update(json.loads(v))
                            except Exception:
                                pass
                d = dict(_ctl); d['gets'] = _gets[0]
                d['push'] = 1 if (_time.time() - _frame['get_t']) < 2.0 else 0
                return self._json(d)
        if self.path.split('?')[0] == '/frame':
            q = self.path.split('?', 1)[1] if '?' in self.path else ''
            since = -1
            try:
                import urllib.parse
                since = int(dict(urllib.parse.parse_qsl(q)).get('since', -1))
            except Exception:
                pass
            with _lock:
                _frame['get_t'] = _time.time()
                b, seq, t, lbl = _frame['b'], _frame['seq'], _frame['t'], _frame.get('lbl') or ''; laboff = _frame.get('laboff') or 0
            if b is None or seq <= since:
                self.send_response(204); self.send_header('X-Seq', str(seq)); self.end_headers(); return
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(b)))
            self.send_header('X-Seq', str(seq))
            self.send_header('X-Age-Ms', str(int((_time.time() - t) * 1000)))
            if lbl: self.send_header('X-Lbl', lbl)
            if laboff: self.send_header('X-LabOff', str(laboff))
            self.end_headers(); self.wfile.write(b); return
        if self.path.split('?')[0] == '/tel':
            with _lock:
                return self._json(dict(_tel))
        return super().do_GET()

    def do_POST(self):
        if self.path.split('?')[0] == '/frame':
            n = int(self.headers.get('Content-Length') or 0)
            b = self.rfile.read(n) if n > 0 else b''
            with _lock:
                if b:
                    _frame['b'] = b; _frame['seq'] += 1; _frame['t'] = _time.time(); _frame['posts'] += 1
                    _frame['lbl'] = self.headers.get('X-Lbl') or ''
                    _frame['laboff'] = int(self.headers.get('X-LabOff') or 0)   # a_5612: JPEG 뒤에 붙은 라벨 PNG 시작 오프셋(0=없음)   # 같은 프레임의 라벨(조향·스로틀·제동·속도) — 프레임/라벨 동기
                seq = _frame['seq']
            self.send_response(200); self.send_header('X-Seq', str(seq)); self.send_header('Content-Length', '0'); self.end_headers(); return
        if self.path.split('?')[0] != '/ctl':
            self.send_error(404); return
        n = int(self.headers.get('Content-Length') or 0)
        try:
            d = json.loads(self.rfile.read(n) or b'{}')
        except Exception:
            self.send_error(400); return
        with _lock:
            for k in ('on', 'steer', 'thr', 'brake', 'force', 'release', 'tgt', 'dOff', 'vT', 'mode', 'lp', 'ld', 'ntier', 'nconf', 'lat', 'inf'):
                if k in d:
                    _ctl[k] = float(d[k])
            if isinstance(d.get('pts'), list) and len(d['pts']) in (4, 8): _ctl['pts'] = [float(z) for z in d['pts']]   # ★u_5547 다점 앞점(10/20/40/80m 횡오프셋)
            elif 'mode' in d and float(d['mode']) != 3: _ctl['pts'] = None
            # ★teach(교사 모드)는 문자열이라 float 변환 대상이 아니다(u_5153).
            #   기존엔 허용 키 목록에 없어서 POST 가 조용히 무시됐고, 그래서
            #   '좌회전 수집' 단계인데 좌 25 / 우 350 이 나왔다 — 모드가 안 바뀐 것이다.
            #   model_drive.py 가 20Hz 로 POST 하므로, teach 를 안 보내면 유지한다.
            if 'teach' in d:
                _ctl['teach'] = str(d['teach'])
            if d.get('reset'):
                _ctl['rst'] = int(_ctl.get('rst', 0)) + 1
            # ★release 는 1회성 신호다(u_5169 실사고).
            #   서버에 남아 있으면 페이지가 폴링할 때마다 모델을 꺼버린다 —
            #   실측: on=1 force=1 인데도 drv=GEOM 이 계속 유지됐다.
            #   한 번 전달된 뒤에는 스스로 0 으로 돌아간다.
            if _ctl.get('release'):
                _ctl['_rel_seen'] = _ctl.get('_rel_seen', 0) + 1
                if _ctl['_rel_seen'] > 1:
                    _ctl['release'] = 0; _ctl['_rel_seen'] = 0
            _ctl['seq'] += 1
            return self._json(dict(_ctl))

    def log_message(self, *a):
        pass


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


with S(('127.0.0.1', PORT), H) as s:
    s.serve_forever()

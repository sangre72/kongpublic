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

_ctl = {'on': 0, 'steer': 0.0, 'thr': 0.0, 'brake': 0.0, 'seq': 0}
_gets = [0]   # 페이지가 실제로 폴링하는지 확인용(a_5085 검증)
# ★진단용 텔레메트리(사고 종류별 카운터). 페이지가 /ctl GET 의 쿼리로 올려준다.
#   HUD 텍스트를 스크린샷에서 읽는 것은 이 프로젝트에서 금지(글자 오독 사고)이므로
#   이미 20Hz 로 도는 폴링에 실어 보낸다 — 새 연결도, 새 타이머도 만들지 않는다.
_tel = {}
_lock = threading.Lock()


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
                return self._json(d)
        if self.path.split('?')[0] == '/tel':
            with _lock:
                return self._json(dict(_tel))
        return super().do_GET()

    def do_POST(self):
        if self.path.split('?')[0] != '/ctl':
            self.send_error(404); return
        n = int(self.headers.get('Content-Length') or 0)
        try:
            d = json.loads(self.rfile.read(n) or b'{}')
        except Exception:
            self.send_error(400); return
        with _lock:
            for k in ('on', 'steer', 'thr', 'brake'):
                if k in d:
                    _ctl[k] = float(d[k])
            _ctl['seq'] += 1
            return self._json(dict(_ctl))

    def log_message(self, *a):
        pass


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


with S(('127.0.0.1', PORT), H) as s:
    s.serve_forever()

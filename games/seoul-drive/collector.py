"""로컬 학습데이터 수집 서버 (2026-09-14).

로컬 파일로 게임을 열면 아티팩트 db를 못 쓴다. 대신 페이지가 이 서버로
라벨을 POST 하고, 서버는 같은 시각의 화면도 같이 캡처해 쌍으로 저장한다.

  python3 collector.py <out_dir> [seconds]
"""
import sys, os, json, time, threading, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/kongbot_drive_data')
DUR = int(sys.argv[2]) if len(sys.argv) > 2 else 300
os.makedirs(os.path.join(OUT, 'frames'), exist_ok=True)
LABELS = []
T0 = time.time()

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        try: LABELS.extend(json.loads(self.rfile.read(n)))
        except Exception: pass
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    def log_message(self, *a): pass

def shots():
    while time.time() - T0 < DUR:
        ts = int(time.time() * 1000)
        subprocess.run(['screencapture', '-x', f'{OUT}/frames/{ts}.png'], check=False)

srv = HTTPServer(('127.0.0.1', 8777), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
th = threading.Thread(target=shots); th.start(); th.join()
json.dump([{'rows': LABELS}], open(f'{OUT}/labels.json', 'w'))
srv.shutdown()
print(json.dumps({'labels': len(LABELS),
                  'frames': len(os.listdir(f'{OUT}/frames')), 'out': OUT}))

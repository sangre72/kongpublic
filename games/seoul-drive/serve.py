"""로컬 개발 서버 (u_5079 오너 지시: 클로드 배포 말고 로컬에서).

WHY charset: python -m http.server 는 Content-Type 에 charset 을 안 붙여서
     한글이 전부 깨진다(실측: '강남대로' -> '媛쒬...'). utf-8 을 명시한다.
WHY no-cache: 빌드할 때마다 새 파일을 봐야 하므로 캐시를 끈다.
"""
import functools, http.server, socketserver, os

PORT = 8901
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class H(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        t = super().guess_type(path)
        if t in ('text/html', 'application/javascript', 'text/javascript', 'text/css'):
            return t + '; charset=utf-8'
        return t

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), H) as s:
    s.serve_forever()

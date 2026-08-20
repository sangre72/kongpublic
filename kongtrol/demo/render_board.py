#!/usr/bin/env python3
"""지뢰찾기 보드를 실제 PNG로 렌더(순수 Python, PIL 불요). kongtrol ScreenSensor(파일소스)가 읽을 대상.
관용 지뢰찾기 색상: 닫힘=회색(160), 열림=밝은회색(240), 숫자 1=파랑 2=초록 3=빨강."""
import sys, zlib, struct

CELL = 80
NUMCOLOR = {1:(0,0,255), 2:(0,128,0), 3:(255,0,0)}

def png(width, height, rgb_rows):
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    raw = b''
    for row in rgb_rows:
        raw += b'\x00' + bytes([v for px in row for v in px])
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw, 9)
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')

def render(board, opened, flagged, path):
    rows, cols = len(board), len(board[0])
    W, H = cols*CELL, rows*CELL
    px = [[(255,255,255)]*W for _ in range(H)]
    def fill(x0,y0,w,h,color):
        for y in range(y0, min(y0+h,H)):
            for x in range(x0, min(x0+w,W)):
                px[y][x] = color
    def draw_digit(cx, cy, color):
        # 간단한 두꺼운 십자/블록으로 숫자 위치에 색점(중심 샘플이 그 색 잡게)
        for y in range(cy-18, cy+18):
            for x in range(cx-10, cx+10):
                if 0<=y<H and 0<=x<W: px[y][x]=color
    for r in range(rows):
        for c in range(cols):
            x0,y0=c*CELL,r*CELL
            if flagged[r][c]:
                fill(x0,y0,CELL,CELL,(255,255,0))
            elif opened[r][c]:
                fill(x0,y0,CELL,CELL,(240,240,240))
                v=board[r][c]
                if isinstance(v,int) and v in NUMCOLOR:
                    draw_digit(x0+CELL//2,y0+CELL//2,NUMCOLOR[v])
            else:
                fill(x0,y0,CELL,CELL,(160,160,160))
            # 격자선
            for x in range(x0,min(x0+CELL,W)): 
                if y0<H: px[y0][x]=(128,128,128)
            for y in range(y0,min(y0+CELL,H)):
                if x0<W: px[y][x0]=(128,128,128)
    with open(path,'wb') as f:
        f.write(png(W,H,px))
    print(f"rendered {W}x{H} -> {path}", flush=True)

# 데모 보드(solution). 열림/깃발 상태 인자로.
SOL = [[1,'M',1,0,0],[1,1,1,0,0],[0,0,0,0,0],[0,1,1,1,0],[0,1,'M',1,0]]
if __name__=='__main__':
    path = sys.argv[1] if len(sys.argv)>1 else '/tmp/ms_board.png'
    # 시나리오: 일부 열림(숫자 보임) + 나머지 닫힘 — kongtrol이 인식·판단할 상태
    opened=[[False]*5 for _ in range(5)]
    flagged=[[False]*5 for _ in range(5)]
    for (r,c) in [(0,0),(1,0),(1,1),(1,2),(0,2)]: opened[r][c]=True  # 숫자셀 열림
    render(SOL,opened,flagged,path)

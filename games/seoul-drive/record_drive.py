#!/usr/bin/env python3
"""주행 화면을 캡처해 타임랩스 영상으로 만든다 (u_5202).

오너: "이번 건은 영상 녹화에서 타임랩스로 해서 보내 줘"

screencapture 로 캔버스 영역만 주기적으로 찍고 ffmpeg 로 이어붙인다.
화면 전체가 아니라 게임 캔버스만 담는다(로컬 정보 노출 방지, security §9).

사용: python3 record_drive.py <초> <출력.mp4> [캡처간격초]
"""
import os, subprocess, sys, time, shutil

REGION = '0,25,763,762'          # 게임 캔버스 영역(브라우저 크롬 제외)


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 300
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/drive.mp4'
    every = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

    tmp = '/tmp/drv_frames'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    subprocess.run(['open', '-a', 'Google Chrome'], capture_output=True)
    time.sleep(1.5)

    n = 0
    t0 = time.time()
    while time.time() - t0 < secs:
        f = '%s/f%05d.png' % (tmp, n)
        subprocess.run(['screencapture', '-x', '-R' + REGION, f], capture_output=True)
        if os.path.exists(f):
            n += 1
        time.sleep(every)

    if n < 10:
        print('프레임 부족: %d' % n); return

    # 타임랩스: 캡처 간격 1초짜리를 30fps 로 이어붙이면 30배속
    subprocess.run([
        'ffmpeg', '-y', '-framerate', '30', '-i', tmp + '/f%05d.png',
        '-vf', 'scale=720:-2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-preset', 'fast', '-crf', '26', out,
    ], capture_output=True)

    if os.path.exists(out):
        mb = os.path.getsize(out) / 1e6
        print('완료: %s (%d프레임, %.1fMB, %.0f배속)' % (out, n, mb, 30 * every))
    else:
        print('ffmpeg 실패')
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()

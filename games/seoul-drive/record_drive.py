#!/usr/bin/env python3
"""주행 화면을 캡처해 타임랩스 영상으로 만든다 (u_5202).

오너: "이번 건은 영상 녹화에서 타임랩스로 해서 보내 줘"

screencapture 로 캔버스 영역만 주기적으로 찍고 ffmpeg 로 이어붙인다.
화면 전체가 아니라 게임 캔버스만 담는다(로컬 정보 노출 방지, security §9).

★2026-09-19: REGION 만으로는 탭바·주소창·Chrome 사이드패널이 같이 찍혔다.
  ffmpeg 단계에서 crop 을 한 번 더 걸어 브라우저 크롬을 잘라낸다.
  기본 crop = 위쪽 75px 제거(탭바+주소창). 사용한 crop 은 콘솔에 찍는다.

사용: python3 record_drive.py <초> <출력.mp4> [캡처간격초] [crop=W:H:X:Y]
  crop 예) crop=763:687:0:75   (ffmpeg crop 필터 순서: 폭:높이:X:Y)
  crop=none 이면 자르지 않는다.
환경변수 REGION='x,y,w,h' 로 캡처 영역을 바꿀 수 있다(기본 0,25,763,762).
"""
import os, subprocess, sys, time, shutil

REGION = os.environ.get('REGION', '0,25,763,762')   # 게임 캔버스 영역(screencapture -R)
CHROME_TOP = 105          # 실측 2026-09-19: 탭바+주소창+색띠 ≈105 논리px(레티나 캡처 210px)


def default_crop():
    """REGION 에서 위쪽 CHROME_TOP px 을 제외한 ffmpeg crop 문자열."""
    _, _, w, h = [int(v) for v in REGION.split(',')]
    return '%d:%d:0:%d' % (w, h - CHROME_TOP, CHROME_TOP)


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 300
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/drive.mp4'
    every = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    crop = default_crop()
    for a in sys.argv[4:]:
        if a.startswith('crop='):
            crop = a[5:]
    if crop in ('none', ''):
        crop = None

    tmp = '/tmp/drv_frames'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    subprocess.run(['open', '-a', 'Google Chrome'], capture_output=True)
    time.sleep(1.5)

    print('캡처 영역 REGION=%s, crop=%s' % (REGION, crop or '없음'))
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
    # crop 은 scale 앞에 건다(레티나면 PNG 픽셀이 2배이므로 iw/ih 비율로 자른다)
    vf = 'scale=720:-2'
    if crop:
        w, h, x, y = [int(v) for v in crop.split(':')]
        rw, rh = [int(v) for v in REGION.split(',')][2:]
        vf = 'crop=iw*%d/%d:ih*%d/%d:iw*%d/%d:ih*%d/%d,' % (w, rw, h, rh, x, rw, y, rh) + vf
    subprocess.run([
        'ffmpeg', '-y', '-framerate', '30', '-i', tmp + '/f%05d.png',
        '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-preset', 'fast', '-crf', '26', out,
    ], capture_output=True)

    if os.path.exists(out):
        mb = os.path.getsize(out) / 1e6
        print('완료: %s (%d프레임, %.1fMB, %.0f배속, crop=%s)' % (out, n, mb, 30 * every, crop or '없음'))
    else:
        print('ffmpeg 실패')
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()

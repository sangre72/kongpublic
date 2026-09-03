"""kong-kkokko — 상시 웨이크워드 리스너 + STT + orch 터미널 주입.

파이프라인:
  [mic 상시] → 롤링버퍼(1.5s)에 대해 경량 whisper(base)로 웨이크워드("콩아"/"콩") 탐지
            → 매치 시 발화 캡처(무음까지 or 최대 N초) → whisper(small)로 STT(한국어)
            → 앞머리 프로젝트명 토큰 파싱 → 그 프로젝트 orch tty 로 텍스트 주입.

웨이크워드 방식 선택(ar_ 근거):
  한국어 커스텀 웨이크워드("콩아")를 지원하는 깔끔한 사전학습 모델(openWakeWord/Porcupine)이
  없어서(둘 다 영어권 키워드 위주·커스텀 한국어 학습 필요), NEW-UI-GATE 취지로 무리한 신규
  모델학습 대신 = 경량 whisper(base) 롤링-STT 로 웨이크워드 문자열만 검사하고, 매치될 때만
  full 캡처+상위모델 STT 로 승격하는 방식을 택함. base 는 2s 윈도우 0.27s(실측)로 상시 가동에
  충분히 가볍고, 새 native-dep(pyaudio/porcupine) 불요.

로컬 전용(security §5): 클라우드 STT API 미사용(마이크=민감정보). whisper 로컬 캐시만.

stage 플래그로 단계별 검증:
  --stage wakeword : 웨이크워드 탐지만(매치 시 콘솔 출력, 주입 안 함) — STEP1 증명
  --stage stt      : 웨이크워드→캡처→STT 텍스트 콘솔 출력(주입 안 함) — STEP2 증명
  --stage full     : 웨이크워드→STT→터미널 주입 end-to-end(기본) — STEP3
"""

from __future__ import annotations

import argparse
import queue
import threading
import sys
import time

import numpy as np

try:
    import sounddevice as sd
except Exception as e:  # noqa: BLE001
    print(f"[FATAL] sounddevice import 실패: {e}", file=sys.stderr)
    sys.exit(1)

import whisper

import target_registry as reg
from inject import inject_to_tty
from widget import MicState, MicWidget

SR = 16000                    # whisper 표준 16kHz
BLOCK_SEC = 0.5               # 마이크 콜백 블록
# ★a_3600 진단: base(및 small/medium)는 '고립된 0.4s 콩아' 를 신뢰성있게 인식 못함(실측:
#   콩아→'구네'/''/'고맙습니다', 반복해도 '고마워'). whisper 는 짧은-무음패딩 발화를 no-speech 로
#   버리거나 환각. → 완화: (1) 롤링윈도우 넓혀 문맥 확보(1.5→2.8s), (2) 변주 대폭 확장 + 퍼지매칭
#   (ㅋ/ㄱ 혼동), (3) short-utter 리콜 위해 decode 파라미터 튜닝(no_speech_threshold 완화).
#   그래도 base 한계 상존 → --debug 로 유저 실제-마이크 raw 캡처 권장(합성음≠실음성).
ROLL_SEC = 2.8               # 웨이크워드 판정 롤링 윈도우(넓혀 문맥 확보)
# 웨이크워드 + base/small 오인식 변주(실측 raw-sample 기반 확장). 퍼지매칭과 병용.
WAKE_WORDS = (
    "콩아", "콩", "꽁아", "공아", "쿵아", "콩하", "콩앙", "콩야", "꼬아", "코아",
    "쿤아", "쿵", "꽁", "공",
)
CAPTURE_MAX_SEC = 6.0         # 웨이크 후 최대 발화 캡처
# ★a_3600: orch 실측 ambient RMS≈0.0137(무음에도 배경소음이 0.008 게이트 통과) → 게이트 상향.
#   단 이 값은 환경별로 다르므로 --debug 로 실제 ambient-vs-speech RMS 확인 후 조정 권장.
SILENCE_RMS = 0.015          # 이 RMS 미만 = 무음(발화 끝/무음창 판정)
SILENCE_HOLD_SEC = 1.0        # 이만큼 연속 무음이면 발화 종료

# short-utterance 리콜용 decode 옵션(no-speech 게이트/환각억제 완화 — a_3600 실측).
_WAKE_DECODE = dict(
    language="ko", fp16=False, condition_on_previous_text=False,
    temperature=0.0, without_timestamps=True,
)


def _rms(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))


def _fuzzy_wake(text: str) -> bool:
    """웨이크워드 매칭 — 정확부분일치 OR 편집거리≤1 퍼지(base ㅋ/ㄱ·모음 혼동 흡수)."""
    import difflib
    t = text.strip().replace(" ", "")
    if not t:
        return False
    if any(w in t for w in WAKE_WORDS):
        return True
    # 슬라이딩 2~3글자 창으로 변주와 근접도 검사(짧은 오인식 토큰 대응).
    for w in ("콩아", "콩"):
        for i in range(len(t) - 1):
            for L in (len(w), len(w) + 1):
                seg = t[i:i + L]
                if seg and difflib.SequenceMatcher(None, seg, w).ratio() >= 0.8:
                    return True
    return False


def _contains_wakeword(text: str) -> bool:
    return _fuzzy_wake(text)


def _strip_wakeword(text: str) -> str:
    """STT 결과 앞의 웨이크워드를 제거해 실제 명령만 남긴다."""
    t = text.strip()
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        idx = t.find(w)
        if idx != -1:
            return t[idx + len(w):].lstrip(" ,.!?~").strip()
    return t


class Listener:
    def __init__(self, wake_model: str, stt_model: str, stage: str, debug: bool = False) -> None:
        self.debug = debug  # a_3600: raw whisper 출력 매 사이클 print(진단용).
        print(f"[load] wake-model={wake_model} …", flush=True)
        self.wake = whisper.load_model(wake_model)
        if stt_model == wake_model:
            self.stt = self.wake
        else:
            print(f"[load] stt-model={stt_model} …", flush=True)
            self.stt = whisper.load_model(stt_model)
        self.stage = stage
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        # 마이크 상태 위젯(a_3593)용 공유 상태. 오디오 콜백은 float/bool 대입만(비차단).
        # ★a_3597 fix: 위젯 tk 는 반드시 프로세스 메인스레드에서 돌린다(macOS Cocoa 제약 —
        #   비메인스레드 Tk()=NSException abort). 그래서 위젯은 main() 이 메인스레드에서 띄우고,
        #   오디오/whisper 루프(run())를 백그라운드 스레드로 돌린다(설계 반전).
        self.mic_state = MicState()

    def _audio_cb(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            print(f"[mic] {status}", file=sys.stderr)
        block = indata[:, 0].copy()
        # 위젯 볼륨 미터용 정규화 RMS(대입만 — 비차단). ~0.05 RMS 를 풀스케일로 스케일.
        self.mic_state.level = min(1.0, _rms(block) / 0.05)
        self.q.put(block)

    def _transcribe(self, model, audio: np.ndarray, wake: bool = False) -> str:  # noqa: ANN001
        # wake 단계는 short-utterance 리콜용 튜닝 옵션(_WAKE_DECODE) 사용.
        opts = _WAKE_DECODE if wake else dict(language="ko", fp16=False)
        r = model.transcribe(audio.astype(np.float32), **opts)
        return (r.get("text") or "").strip()

    def _capture_utterance(self, roll: np.ndarray) -> np.ndarray:
        """웨이크 감지 후, 무음까지(또는 최대치까지) 이어지는 발화를 캡처."""
        buf = [roll]
        silent_for = 0.0
        start = time.time()
        while time.time() - start < CAPTURE_MAX_SEC:
            try:
                block = self.q.get(timeout=BLOCK_SEC * 2)
            except queue.Empty:
                break
            buf.append(block)
            if _rms(block) < SILENCE_RMS:
                silent_for += len(block) / SR
                if silent_for >= SILENCE_HOLD_SEC:
                    break
            else:
                silent_for = 0.0
        return np.concatenate(buf)

    def _dispatch(self, command: str) -> None:
        project = reg.parse_project_token(command)
        tty, name = reg.resolve_tty(project)
        # 프로젝트명 토큰이 명령 앞머리에 있으면 명령에서 떼어낸다.
        payload = command
        if project:
            low = payload.lower()
            i = low.find(project) if project in low else payload.find(project)
            if i != -1:
                payload = payload[i + len(project):].lstrip(" ,.!?~한테에게").strip() or command
        if not payload:
            print("[skip] 빈 명령")
            return
        if tty is None:
            print(f"[fail] project={name} tty 미등록/미존재 — 주입 생략. payload={payload!r}")
            return
        ok, msg = inject_to_tty(tty, payload)
        print(f"[inject→{name}] ok={ok} :: {msg} :: payload={payload!r}")

    def run(self) -> None:
        roll_len = int(ROLL_SEC * SR)
        rolling = np.zeros(roll_len, dtype=np.float32)
        print(f"[ready] stage={self.stage} — say a wake word: {WAKE_WORDS[:2]} … (Ctrl-C to stop)", flush=True)
        with sd.InputStream(
            samplerate=SR, channels=1, blocksize=int(BLOCK_SEC * SR),
            dtype="float32", callback=self._audio_cb,
        ):
            while True:
                block = self.q.get()
                rolling = np.concatenate([rolling, block])[-roll_len:]
                cur_rms = _rms(rolling)
                if cur_rms < SILENCE_RMS:
                    if self.debug:
                        print(f"[debug-raw] rms={cur_rms:.4f} <gate({SILENCE_RMS}) → skip", flush=True)
                    continue  # 무음 창은 STT 생략(비용 절감)
                text = self._transcribe(self.wake, rolling, wake=True)
                if self.debug:
                    print(f"[debug-raw] rms={cur_rms:.4f} text={text!r} wake={_contains_wakeword(text)}", flush=True)
                if not _contains_wakeword(text):
                    continue
                print(f"[WAKE] heard: {text!r}")
                self.mic_state.wake_flash = 1.0
                if self.stage == "wakeword":
                    continue
                # 승격: 발화 캡처 + 상위모델 STT. 캡처 동안은 wakeword-listen 아님 → gray.
                self.mic_state.armed = False
                utter = self._capture_utterance(rolling)
                full = self._transcribe(self.stt, utter)
                self.mic_state.armed = True
                command = _strip_wakeword(full)
                print(f"[STT] full={full!r} → command={command!r}")
                if self.stage == "stt":
                    continue
                if command:
                    self._dispatch(command)
                # 롤링 버퍼 리셋(방금 발화가 다음 창에 잔류해 재트리거되는 것 방지)
                rolling = np.zeros(roll_len, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description="kong-kkokko voice dispatcher")
    ap.add_argument("--stage", choices=["wakeword", "stt", "full"], default="full")
    ap.add_argument("--wake-model", default="base", help="상시 웨이크워드 탐지 모델(가벼울수록 좋음)")
    ap.add_argument("--stt-model", default="small", help="발화 STT 모델(large-v3=느림 u_3590, small 권장)")
    ap.add_argument("--widget", action="store_true", help="마이크 상태 플로팅 위젯 표시(a_3593)")
    ap.add_argument("--debug", action="store_true", help="raw whisper 출력·RMS 매 사이클 print(a_3600 진단)")
    args = ap.parse_args()
    listener = Listener(args.wake_model, args.stt_model, args.stage, debug=args.debug)

    if not args.widget:
        # 위젯 없음 → 오디오/whisper 루프를 메인스레드에서 그대로.
        try:
            listener.run()
        except KeyboardInterrupt:
            print("\n[stop] bye")
        return

    # ★a_3597 fix: 위젯 켜짐 → tk 는 메인스레드(macOS Cocoa 제약), 리스너는 백그라운드 스레드.
    stop = threading.Event()

    def _bg() -> None:
        try:
            listener.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:  # noqa: BLE001
            print(f"[listener] EXC: {e}", file=sys.stderr)
        finally:
            stop.set()

    t = threading.Thread(target=_bg, daemon=True)
    t.start()
    # MicWidget.run_mainthread() 는 이 메인스레드를 tk mainloop 로 점유(블로킹) — 정상.
    try:
        MicWidget(listener.mic_state, stop=stop).run_mainthread()
    except KeyboardInterrupt:
        print("\n[stop] bye")
        stop.set()


if __name__ == "__main__":
    main()

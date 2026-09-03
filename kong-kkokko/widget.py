"""kong-kkokko 마이크 상태 위젯 — 작은 always-on-top 플로팅 창(tkinter, stdlib, no extra dep).

~50×58px, 타이틀바 없음(overrideredirect), 화면 우상단(메뉴바 근처, u_3588 공간선호) 배치.
표시:
  - 상단 상태 점: green=listening/wakeword-armed, gray=idle/muted.
  - 하단 볼륨 미터: 현재 RMS 레벨 바(말하는 동안 움직임).

★a_3597 fix(macOS Cocoa 제약): tkinter mainloop 는 반드시 프로세스 '메인스레드'에서 돌아야 한다.
  비메인스레드에서 Tk() 생성 시 NSException 으로 프로세스가 abort 되고(실증), 그 여파로
  메인스레드 오디오/whisper 루프까지 멈춘다(CPU 0.1% 고착). → 설계 반전:
  위젯이 '메인스레드'를 mainloop 로 점유하고(run_mainthread), 오디오/whisper 루프(Listener.run)는
  kkokko.main() 이 '백그라운드 스레드'로 돌린다. 오디오-콜백은 MicState 필드 대입만(비차단).

메뉴바 아이콘(NSStatusItem 등가) 옵션: 순수 파이썬으론 `rumps` 라이브러리가 근접하나 추가 dep
+ 별도 이벤트루프라 stdlib tkinter 플로팅 창을 택함(경량·무설치). ar_ 에 근거 기록.
"""

from __future__ import annotations

import threading  # noqa: F401 (stop 이벤트 타입 힌트용 — main() 이 생성해 넘김)


class MicState:
    """오디오 루프 ↔ 위젯 공유 상태(단일 대입만 — GIL 하 thread-safe)."""

    def __init__(self) -> None:
        self.armed: bool = True     # True=listening(green), False=idle/muted(gray)
        self.level: float = 0.0     # 0.0~1.0 볼륨(정규화 RMS)
        self.wake_flash: float = 0.0  # 웨이크 감지 순간 강조(초 카운트다운, 옵션)


class MicWidget:
    def __init__(self, state: MicState, stop=None) -> None:  # noqa: ANN001
        self.state = state
        self.stop = stop  # threading.Event | None — set 되면 위젯도 닫는다(리스너 종료 연동).

    def run_mainthread(self) -> None:
        """★반드시 프로세스 메인스레드에서 호출(macOS Cocoa 제약). tk mainloop 로 블로킹."""
        try:
            import tkinter as tk
        except Exception as e:  # noqa: BLE001
            print(f"[widget] tkinter 불가 — 위젯 없이 리스너만: {e}")
            # 위젯이 없어도 리스너(백그라운드 스레드)는 계속 돌아야 하므로 stop 을 기다린다.
            if self.stop is not None:
                self.stop.wait()
            return

        W, H = 50, 58
        root = tk.Tk()
        root.overrideredirect(True)          # 타이틀바/크롬 제거
        root.attributes("-topmost", True)    # always-on-top
        try:
            root.attributes("-alpha", 0.92)
        except tk.TclError:
            pass
        # 우상단 배치(메뉴바 아래 근처).
        sw = root.winfo_screenwidth()
        root.geometry(f"{W}x{H}+{sw - W - 12}+34")

        cv = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="#1c1c1e")
        cv.pack()
        dot = cv.create_oval(W // 2 - 8, 8, W // 2 + 8, 24, fill="#34c759", outline="")
        # 볼륨 바(하단, 아래에서 위로 차오름).
        bar = cv.create_rectangle(10, H - 6, W - 10, H - 6, fill="#0a84ff", outline="")

        def tick() -> None:
            if self.stop is not None and self.stop.is_set():
                root.destroy()  # 리스너 종료 → 위젯도 닫고 mainloop 반환.
                return
            armed = self.state.armed
            cv.itemconfig(dot, fill="#34c759" if armed else "#6e6e73")  # green / gray
            lvl = max(0.0, min(1.0, self.state.level))
            top = (H - 6) - int(lvl * (H - 18))  # 바 높이
            cv.coords(bar, 10, top, W - 10, H - 6)
            cv.itemconfig(bar, fill="#0a84ff" if armed else "#3a3a3c")
            root.after(100, tick)  # 100ms 폴링(비차단)

        # 드래그로 이동 가능(overrideredirect 창).
        def _press(e):  # noqa: ANN001
            root._dx, root._dy = e.x, e.y

        def _drag(e):  # noqa: ANN001
            root.geometry(f"+{e.x_root - root._dx}+{e.y_root - root._dy}")

        cv.bind("<Button-1>", _press)
        cv.bind("<B1-Motion>", _drag)

        tick()
        try:
            root.mainloop()
        except Exception:  # noqa: BLE001
            pass

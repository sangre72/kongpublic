# kong-kkokko

Always-on **wakeword → STT → orch-terminal injection** voice dispatcher (local-only, Python).

Say **"콩아 …"** (or "콩 …"), speak a command, and it is transcribed (local Whisper) and
typed straight into a target project's orchestrator Terminal session.

## Pipeline

```
[mic, always-on]
  → rolling 1.5s buffer, lightweight Whisper (base) checks for wakeword ("콩아"/"콩")
  → on match: capture utterance (until ~1s silence, max 6s)
  → Whisper (small) STT → Korean text
  → parse leading project name token → that project's orch tty (logs/.orch_tty_orch)
  → inject via Terminal "do script" (NOT System Events — permission-free, pure-IO)
```

## Wakeword approach (why rolling-STT, not openWakeWord/Porcupine)

No clean pretrained wakeword model supports a **custom Korean** phrase ("콩아") out of the box
(openWakeWord/Porcupine are English-keyword-centric; custom KR = training a model). Rather than
train a new model, the wake stage runs **lightweight Whisper `base`** over a short rolling window
and just string-matches the wakeword — promoting to full capture + higher-tier STT only on a hit.

Measured (this machine, CPU): `base` transcribes a 2s window in **~0.27–0.31s** — light enough for
always-on. STT stage `small` = **~0.44–0.52s** on a 4s utterance. `large-v3` deliberately avoided
(user flagged too slow for realtime, u_3590); `medium` (~1.18s) available as a quality fallback.

## Usage

```bash
bash run.sh                          # full pipeline (wakeword → STT → inject)
bash run.sh --stage wakeword         # STEP1: only prove wakeword triggers (prints, no inject)
bash run.sh --stage stt              # STEP2: wakeword → STT text (prints, no inject)
bash run.sh --stt-model medium       # higher-quality STT (slower)
```

First mic access will trigger a macOS microphone-permission prompt — grant it.

**Threading note (macOS):** with `--widget`, the tkinter widget runs on the **main thread**
(Cocoa/AppKit requires GUI on the main thread — a non-main-thread `Tk()` aborts the process with
an `NSException`), and the audio + Whisper loop runs on a **background thread**. Without `--widget`
the audio loop stays on the main thread. Either way the audio callback only assigns to a shared
`MicState` (non-blocking).

## Target registry (multi-project ready)

`target_registry.py` maps a spoken project name → that project's orch tty file. Currently only
`kong-bot` exists (→ `logs/.orch_tty_orch`, registered by `session_register_tty.sh`). Add a line
per new project later; no project token in the utterance → defaults to `kong-bot`.

## Security / privacy

- **Local Whisper only** — no cloud STT API (mic audio is sensitive; security-guideline §5).
- Injected text is **sanitized** for osascript (quotes/newlines/control chars) before injection —
  STT output is treated as untrusted (security-guideline §2, no shell/script-string injection).
- Uses Terminal `do script` (permission-free), never System Events (pure-IO convention, §3).

## Files

| file | role |
|------|------|
| `kkokko.py` | entrypoint: mic loop, wakeword detect, STT, staged run |
| `target_registry.py` | project-name → orch tty mapping |
| `inject.py` | Terminal `do script` injection (+ sanitize) |
| `run.sh` | launcher |
| `requirements.txt` | deps (whisper, sounddevice, numpy) |

## Verified

- py_compile OK (all modules).
- Registry resolves `kong-bot` → real orch tty; token parsing + default-fallback OK.
- End-to-end on synthesized KR audio: wakeword "콩아" detected (base 0.31s) → STT (small 0.44s) →
  command stripped → dispatch. (macOS `say` TTS mangles some syllables — a synthesis artifact, not
  a real-mic issue.)
- **Live injection proven**: `inject_to_tty` → `SUCCESS(tty)` into the orch session.
- Not yet run against a **live microphone** end-to-end (needs a person to speak + grant mic
  permission) — that final confirm is the user's.

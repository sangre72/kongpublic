#!/usr/bin/env bash
# kong-kkokko launcher. Runs the always-on wakeword→STT→inject listener.
# usage: bash run.sh [--stage wakeword|stt|full] [--wake-model base] [--stt-model small]
# Local-only (no cloud STT). Needs mic permission (macOS will prompt on first mic access).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
exec python3 kkokko.py "$@"

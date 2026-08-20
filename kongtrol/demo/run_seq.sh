#!/usr/bin/env bash
# run_seq.sh <seqfile>  — labeled chrome executor (a_66). 0 LLM · 0 shot in worker context.
#   Seq: app / dump / click_label / click / key / chord / text / wait
#   Example:  app Google Chrome
#             dump
#             click_label Reload
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/target/release/kongtrol"
FILE="${1:?seq file}"
exec "$BIN" --yes input run "$FILE"

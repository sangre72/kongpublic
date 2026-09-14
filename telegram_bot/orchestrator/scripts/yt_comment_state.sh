#!/bin/bash
# yt_comment_state.sh — per-date first-comment progress marking for the fortune upload job.
#
# WHY(u_4849): without durable per-date marking, a worker re-runs today's videos
# (duplicate comments) or silently misses tomorrow's. State must survive session end.
#
# Usage:
#   yt_comment_state.sh mark <YYYY-MM-DD> <zodiac> [pinned|nopin]   # record one done
#   yt_comment_state.sh done <YYYY-MM-DD> <zodiac>                  # is it done? exit 0=yes
#   yt_comment_state.sh list <YYYY-MM-DD>                           # show that date's progress
#   yt_comment_state.sh next <YYYY-MM-DD>                           # print next zodiac to do
#   yt_comment_state.sh status                                      # all dates summary
#
# Store: logs/yt_comment_state.tsv   (date \t zodiac \t pinned \t timestamp)
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
S="$ROOT/logs/yt_comment_state.tsv"
touch "$S"
ORDER="rat ox tiger rabbit dragon snake horse goat monkey rooster dog pig"
KR_rat=쥐띠; KR_ox=소띠; KR_tiger=호랑이띠; KR_rabbit=토끼띠; KR_dragon=용띠; KR_snake=뱀띠
KR_horse=말띠; KR_goat=양띠; KR_monkey=원숭이띠; KR_rooster=닭띠; KR_dog=개띠; KR_pig=돼지띠

cmd="${1:-status}"; d="${2:-}"; z="${3:-}"; pin="${4:-pinned}"

case "$cmd" in
  mark)
    [ -n "$d" ] && [ -n "$z" ] || { echo "usage: mark <date> <zodiac> [pinned|nopin]"; exit 1; }
    if awk -F'\t' -v d="$d" -v z="$z" '$1==d && $2==z{f=1} END{exit !f}' "$S"; then
      echo "ALREADY $d $z"
    else
      printf '%s\t%s\t%s\t%s\n' "$d" "$z" "$pin" "$(date '+%Y-%m-%d %H:%M:%S')" >> "$S"
      echo "MARKED $d $z ($pin)"
    fi
    ;;
  done)
    awk -F'\t' -v d="$d" -v z="$z" '$1==d && $2==z{f=1} END{exit !f}' "$S"
    ;;
  list)
    [ -n "$d" ] || { echo "usage: list <date>"; exit 1; }
    n=0
    for k in $ORDER; do
      eval "kr=\$KR_$k"
      if awk -F'\t' -v d="$d" -v z="$k" '$1==d && $2==z{f=1} END{exit !f}' "$S"; then
        p=$(awk -F'\t' -v d="$d" -v z="$k" '$1==d && $2==z{print $3}' "$S" | tail -1)
        echo "  OK   $kr ($p)"; n=$((n+1))
      else
        echo "  --   $kr"
      fi
    done
    echo "$d : $n/12"
    ;;
  next)
    [ -n "$d" ] || { echo "usage: next <date>"; exit 1; }
    for k in $ORDER; do
      if ! awk -F'\t' -v d="$d" -v z="$k" '$1==d && $2==z{f=1} END{exit !f}' "$S"; then
        eval "kr=\$KR_$k"; echo "$k ($kr)"; exit 0
      fi
    done
    echo "ALL-DONE"
    ;;
  status)
    cut -f1 "$S" | sort -u | while read -r dd; do
      [ -n "$dd" ] || continue
      c=$(awk -F'\t' -v d="$dd" '$1==d' "$S" | wc -l | tr -d ' ')
      echo "$dd : $c/12"
    done
    ;;
  *) echo "unknown cmd: $cmd"; exit 1;;
esac

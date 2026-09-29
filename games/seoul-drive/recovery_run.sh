#!/usr/bin/env bash
# u_5774: rule baseline on perturbation recovery, widened sample.
# pghold must cover recovery_baseline's 12s scoring window; pgrid is the CLEAR gap after it.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./chrome_guard.sh; chrome_guard || exit 9
source ./park_page.sh;    arm_park_trap
N=${1:-40}; PGRID=${PGRID:-3}; PGHOLD=${PGHOLD:-7}
ROUTE=${ROUTE:-'강동대로>삼학사로14길'}
FROM=${ROUTE%%>*}; TO=${ROUTE##*>}
curl -s -X POST -H 'Content-Type: application/json' -d '{"on":0,"mode":0,"park":1}' \
     http://localhost:8901/ctl >/dev/null 2>&1 || true          # rule §11: reset /ctl before every run
URL="http://localhost:8901/index.html?go=1&from=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$FROM")&to=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$TO")&pgrid=${PGRID}&pghold=${PGHOLD}&pgey=0.6,1.0,1.5&pgep=10,18,25"
bash reload.sh "$URL" 60 >/dev/null 2>&1 || { echo "reload failed"; exit 1; }
echo "df=$(df -g / | awk 'NR==2{print $4"GB"}') route=$ROUTE pgrid=$PGRID pghold=$PGHOLD n=$N"
python3 recovery_baseline.py "$N"

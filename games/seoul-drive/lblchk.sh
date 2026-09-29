#!/bin/bash
# u_5753: 300s teacher-driven collection with ?lblchk=1 so the page logs (delta, delta/maxSteer,
# xt, v, _st, me.steer) per tick, while dagger stores the frame-header label the SAME way it
# always does. Then we compare stored label vs the page's own record for the same run.
cd /Users/bumsuklee/git/kong-bot/games/seoul-drive
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 PYTHONIOENCODING=utf-8 ODE_CROP=0.6 L12=1 M_EXT=1 LAB=1 STORE_RES=256
source ./chrome_guard.sh; chrome_guard "lblchk" || exit 9
source ./park_page.sh; trap park_page EXIT
source ./pagelock.sh; lock_page "lblchk" || { echo "PAGE BUSY"; exit 9; }; trap unlock_page EXIT
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
curl -s "http://localhost:8901/ctl?reset=1" -o /dev/null --max-time 5
bash reload.sh "http://localhost:8901/index.html?go=1&lab=1&lblchk=1&from=형촌6길&to=역삼로78길" 120 2>&1 | tail -1 >/dev/null
echo "=== lblchk run $(date +%H:%M:%S) ==="
rm -rf data/dagger_r3900
python3 dagger.py --round 3900 --episodes 1 --secs 180 --model none 2>&1 | grep -E '"ep"|"S"|label_src|Traceback|Error' | cut -c1-200
curl -s "http://localhost:8901/ctl?tel=1" -o /dev/null --max-time 5
python3 - <<'PY'
import urllib.request, json
d=json.load(urllib.request.urlopen('http://localhost:8901/tel',timeout=8))
print('lblN in tel:', d.get('lblN'))
PY
echo LBLCHK_DONE

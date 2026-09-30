#!/usr/bin/env bash
# u_5801: does the command-path smoothing destroy the perception signal?
# LP_TRACE writes raw=(t, truth_lp@ld, model_lp) per frame, which is the pair we need.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./chrome_guard.sh; chrome_guard || exit 9
source ./park_page.sh;    arm_park_trap
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
SECS=${SECS:-240}   # u_5801: long enough that every arm gets a comparable stretch of road
ROUTE=${ROUTE:-'형촌6길>역삼로78길'}
F=${ROUTE%%>*}; TO=${ROUTE##*>}
enc(){ python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1"; }
for cfg in "0.4 0.4" "1.5 0.1" "0 0"; do
  set -- $cfg; R=$1; TAU=$2
  TAG="r${R}_t${TAU}"
  curl -s -X POST -H 'Content-Type: application/json' -d '{"on":0,"mode":0,"park":1}' http://localhost:8901/ctl >/dev/null 2>&1 || true
  bash reload.sh "http://localhost:8901/index.html?from=$(enc "$F")&to=$(enc "$TO")" 60 >/dev/null 2>&1 || { echo "$TAG reload fail"; continue; }
  rm -f $T/uc_${TAG}_*.npz
  LP_LD=20 LP_RATE=$R LP_TAU=$TAU LP_TRACE=$T/uc_${TAG} \
    python3 gpu_drive.py --secs $SECS --speed $T/ode_v9.mlpackage --lp models/ode_geo_wide.mlpackage \
      --geo --lp-tier 2 --lp-vmax 8 > $T/uc_${TAG}.log 2>&1
  echo "=== LP_RATE=$R LP_TAU=$TAU"
  python3 - "$T" "$TAG" <<'PY'
import sys, glob, numpy as np, json
T,TAG=sys.argv[1],sys.argv[2]
fs=sorted(glob.glob(f'{T}/uc_{TAG}_*.npz'))
if not fs: print(json.dumps({'tag':TAG,'err':'no trace'})); raise SystemExit
z=np.load(fs[-1]); raw=z['raw']
if raw.size==0: print(json.dumps({'tag':TAG,'err':'empty raw'})); raise SystemExit
t,tru,mod=raw[:,0],raw[:,1],raw[:,2]
m=np.isfinite(tru)&np.isfinite(mod)
tru,mod=tru[m],mod[m]
out={'tag':TAG,'frames':int(m.sum())}
out['sd_truth_raw']=round(float(tru.std()),4)
if len(tru)>50 and tru.std()>1e-6 and mod.std()>1e-9:
    out.update(corr=round(float(np.corrcoef(mod,tru)[0,1]),3),
               var_ratio=round(float(mod.var()/tru.var()),4),
               sd_cmd=round(float(mod.std()),3), sd_truth=round(float(tru.std()),3),
               mean_abs_frame_delta=round(float(np.abs(np.diff(mod)).mean()),5))
print(json.dumps(out))
PY
done

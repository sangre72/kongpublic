#!/usr/bin/env bash
# ground_vl.sh — REMOTE VL grounding (a_47). REMOTE-ONLY. No local daemon. No UI-TARS.
#   ping prints served model id. Holo* → 0-1000 norm → shot px → LOGICAL.
#   else Qwen path KEEP: resize-px → orig-px → LOGICAL.
#   Output always LOGICAL for `kongtrol input click X Y --scale 1.0`.
# ENDPOINT: ${VL_REMOTE_EP:-http://192.168.45.183:8000} OpenAI /v1 (vLLM).
#   Qwen jitter interim: 3-sample median when VL_CONSENSUS=1 (default on).
# 사용:
#   ground_vl.sh find "<요소 설명>" [스샷]  → FOUND <lx> <ly> or NOTFOUND
#   ground_vl.sh ping                      → READY <ep> id=<model> | DOWN <ep>
set -u
EP="${VL_REMOTE_EP:-http://192.168.45.183:8000}"
MODEL="${VL_REMOTE_MODEL:-cpatonn/Qwen3-VL-8B-Instruct-AWQ-4bit}"
RESIZE_W="${VL_RESIZE_W:-768}"
CONSENSUS="${VL_CONSENSUS:-1}"
D="${TMPDIR:-/tmp}/kongtrol_vl_remote"
mkdir -p "$D"

# retina: screencapture W / logical-screen W; fallback 2.0 on this Mac.
# VL_RETINA_SCALE overrides. Do NOT reuse VISION_SCALE (that's ground.sh emit scale).
retina_scale() {
  local shot="$1"
  VL_RETINA_SCALE="${VL_RETINA_SCALE:-}" SHOT="$shot" python3 - <<'PY'
import os, struct, ctypes, ctypes.util
ov=os.environ.get("VL_RETINA_SCALE","").strip()
if ov:
    print(ov); raise SystemExit
shot=os.environ["SHOT"]
try:
    with open(shot,"rb") as f:
        f.read(16); iw, _ih = struct.unpack(">II", f.read(8))
except Exception:
    print("2.0"); raise SystemExit
lw=0
try:
    lib=ctypes.util.find_library("CoreGraphics")
    cg=ctypes.cdll.LoadLibrary(lib)
    cg.CGMainDisplayID.restype=ctypes.c_uint32
    did=cg.CGMainDisplayID()
    cg.CGDisplayPixelsWide.argtypes=[ctypes.c_uint32]
    cg.CGDisplayPixelsWide.restype=ctypes.c_ulong
    lw=int(cg.CGDisplayPixelsWide(did))
except Exception:
    lw=0
if lw>0 and iw>0:
    r=iw/float(lw)
    if 1.8<=r<=2.2: print("2.0"); raise SystemExit
    if 0.9<=r<=1.1: print("1.0"); raise SystemExit
    if 2.8<=r<=3.2: print("3.0"); raise SystemExit
print("2.0")  # this Mac fallback (4112 shot / 2056 logical)
PY
}

served_id() {
  curl -s -m 6 "$EP/v1/models" 2>/dev/null | python3 -c '
import sys,json
try:
    d=json.load(sys.stdin)
    print(d["data"][0]["id"])
except Exception:
    print("")
'
}

is_holo() {
  local id="$1"
  [[ "$id" == *[Hh]olo* ]]
}

ping_srv() {
  local id
  id=$(served_id)
  if [ -n "$id" ]; then
    echo "READY $EP id=$id"
    return 0
  fi
  echo "DOWN $EP"
  return 1
}

WARM_MARK="$D/.warmed"
warmup() {
  [ -f "$WARM_MARK" ] && { echo "WARM (이미 예열)"; return 0; }
  local mid; mid=$(served_id); [ -n "$mid" ] && MODEL="$mid"
  local px="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
  local t0 t1
  t0=$(python3 -c "import time;print(time.time())")
  curl -s -m 40 "$EP/v1/chat/completions" -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"max_tokens\":1,\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$px\"}},{\"type\":\"text\",\"text\":\"hi\"}]}]}" >/dev/null 2>&1
  t1=$(python3 -c "import time;print(time.time())")
  touch "$WARM_MARK"
  python3 -c "print('WARMED %.1fs (cold였으면 이 1회만 김·이후 warm)'%($t1-$t0))"
}

# one remote call → print "x y" (model-native units) or FAIL
vl_xy() {
  local img="$1" model="$2" prompt="$3"
  python3 - "$img" "$model" "$prompt" > "$D/req.json" <<'PY'
import sys,json,base64
img,model,prompt=sys.argv[1],sys.argv[2],sys.argv[3]
b64=base64.b64encode(open(img,"rb").read()).decode()
print(json.dumps({"model":model,"max_tokens":80,"temperature":0,"messages":[
  {"role":"user","content":[
    {"type":"image_url","image_url":{"url":"data:image/png;base64,"+b64}},
    {"type":"text","text":prompt}]}]}))
PY
  local resp
  resp=$(curl -s -m 45 "$EP/v1/chat/completions" -H "Content-Type: application/json" -d @"$D/req.json") \
    || { echo "FAIL"; return 1; }
  printf '%s' "$resp" | python3 -c '
import sys,json,re
try:
    d=json.loads(sys.stdin.read()); t=d["choices"][0]["message"]["content"]
except Exception:
    print("FAIL"); raise SystemExit
m=re.search(r"\"?x\"?\s*:\s*(-?\d+).*?\"?y\"?\s*:\s*(-?\d+)", t, re.S) or re.search(r"(\d{1,4})\s*[, ]\s*(\d{1,4})", t)
if not m:
    print("FAIL"); raise SystemExit
print(int(m.group(1)), int(m.group(2)))
'
}

png_wh() {
  python3 -c "import struct;f=open('$1','rb');f.read(16);print(*struct.unpack('>II',f.read(8)))"
}

find_el() {
  local desc="$1" shot="${2:-}"
  [ -f "$WARM_MARK" ] || warmup >/dev/null 2>&1
  [ -z "$shot" ] && { shot="$D/frame.png"; screencapture -x "$shot" 2>/dev/null || { echo "NOTFOUND (capture)"; return 1; }; }
  [ -f "$shot" ] || { echo "NOTFOUND (no shot)"; return 1; }

  local mid
  mid=$(served_id)
  [ -n "$mid" ] && MODEL="$mid"
  [ -z "$mid" ] && mid="$MODEL"

  local dims iw ih
  dims=$(png_wh "$shot") || { echo "NOTFOUND (png dims)"; return 1; }
  iw=$(echo $dims|cut -d' ' -f1); ih=$(echo $dims|cut -d' ' -f2)
  local retina; retina=$(retina_scale "$shot")

  local small="$D/small.png"
  sips -Z "$RESIZE_W" "$shot" --out "$small" >/dev/null 2>&1 || small="$shot"
  local sdims sw sh
  sdims=$(png_wh "$small") || { echo "NOTFOUND (small dims)"; return 1; }
  sw=$(echo $sdims|cut -d' ' -f1); sh=$(echo $sdims|cut -d' ' -f2)

  local path n i xy xs="" ys=""
  if is_holo "$mid"; then
    path="holo"
    n=1
    local prompt="Output ONLY {\"x\":int,\"y\":int}, 0-1000 normalized, center of ${desc}. (0,0)=top-left. No explanation."
    xy=$(vl_xy "$small" "$mid" "$prompt")
    [[ "$xy" == FAIL* || -z "$xy" ]] && { echo "NOTFOUND (REMOTE 좌표없음)"; return 1; }
    xs=$(echo $xy|cut -d' ' -f1); ys=$(echo $xy|cut -d' ' -f2)
  else
    path="qwen"
    n=1; [ "$CONSENSUS" = "1" ] && n=3
    local prompt="Output ONLY a JSON object {\"x\":int,\"y\":int} giving the center pixel coordinate of this UI element in the image: ${desc}. The image is ${sw}x${sh} pixels, (0,0)=top-left. No explanation, no other text."
    local ok=0
    for i in $(seq 1 "$n"); do
      xy=$(vl_xy "$small" "$mid" "$prompt")
      if [[ "$xy" != FAIL* && -n "$xy" ]]; then
        xs="${xs} $(echo $xy|cut -d' ' -f1)"
        ys="${ys} $(echo $xy|cut -d' ' -f2)"
        ok=$((ok+1))
      fi
    done
    [ "$ok" -eq 0 ] && { echo "NOTFOUND (REMOTE 좌표없음)"; return 1; }
    # median of samples
    local med
    med=$(XS="$xs" YS="$ys" python3 -c '
import os
xs=sorted(int(v) for v in os.environ["XS"].split())
ys=sorted(int(v) for v in os.environ["YS"].split())
print(xs[len(xs)//2], ys[len(ys)//2])
')
    xs=$(echo $med|cut -d' ' -f1); ys=$(echo $med|cut -d' ' -f2)
  fi

  PATHNAME="$path" X="$xs" Y="$ys" IW="$iw" IH="$ih" SW="$sw" SH="$sh" RET="$retina" MID="$mid" \
  python3 -c '
import os
path,x,y=os.environ["PATHNAME"],int(os.environ["X"]),int(os.environ["Y"])
iw,ih=int(os.environ["IW"]),int(os.environ["IH"])
sw,sh=int(os.environ["SW"]),int(os.environ["SH"])
ret=float(os.environ["RET"])
if path=="holo":
    # 0-1000 of the image VL saw → orig shot px (norm invariant to resize)
    px=x*iw/1000.0; py=y*ih/1000.0
else:
    # Qwen KEEP: resize-px → orig-px
    px=x*iw/float(sw); py=y*ih/float(sh)
lx=int(round(px/ret)); ly=int(round(py/ret))
print(f"FOUND {lx} {ly}")
'
  echo "vl model=$mid path=$path retina=$retina shot=${iw}x${ih} small=${sw}x${sh} native=$xs,$ys samples=${n}" >&2
}

case "${1:-}" in
  find)   shift; find_el "$@";;
  ping)   ping_srv;;
  warmup) warmup;;
  start|stop) echo "SKIP ($1 불필요 — REMOTE 상주. 로컬 데몬 폐기됨)";;
  *) echo "usage: ground_vl.sh find \"<desc>\" [shot] | ping | warmup"; exit 2;;
esac

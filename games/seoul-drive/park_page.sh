# ★u_5709 (MUST, 2026-09-28): 주행을 켠 스크립트가 끈다. 종료·오류·kill 어느 경로로 끝나도 차를 세운다.
# ★u_5765 (2026-09-29, 같은 사고 2회째) 실측으로 확인한 것:
#   (1) 옛 park_page 는 제어 인터페이스만 껐다 → 교사(TEACH)가 계속 몰아 벽에 박힌 채 사고 36·순간이동 20.
#   (2) 래퍼만 죽이면 자식(dagger.py/gpu_drive.py)이 계속 몬다 → 자식을 먼저 죽인다.
#   (3) /ctl park=1 은 v 를 ~0.5 로 떨어뜨리지만 autoOn 은 1 로 남아 교사가 다시 가속한다.
#       auto=0 파라미터는 없다 → **go=1 없는 기본 URL 로 리로드**하는 것만이 확실히 세우는 방법이다.
_park_kill_children(){
  pkill -P $$ 2>/dev/null || true
  pkill -f "dagger.py --round" 2>/dev/null || true
  pkill -f "gpu_drive.py --secs" 2>/dev/null || true
  sleep 1
}
park_page(){
  _park_kill_children
  curl -s -X POST -H 'Content-Type: application/json' \
    -d '{"on":0,"force":0,"release":1,"tgt":0,"mode":1,"lp":0.0,"ld":-1,"dOff":0.0,"vT":-1,"park":1}' \
    http://localhost:8901/ctl >/dev/null 2>&1 || true
  bash "$(dirname "${BASH_SOURCE[0]}")/reload.sh" "http://localhost:8901/index.html" 45 >/dev/null 2>&1 || true
}
# 상단에서 `arm_park_trap` 한 줄. 이미 다른 trap 이 있으면 'park_page; 그것' 형태로 합칠 것(뒤의 trap 이 앞을 덮어쓴다).
arm_park_trap(){ trap 'park_page' EXIT INT TERM HUP; }

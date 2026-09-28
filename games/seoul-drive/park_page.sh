# ★u_5709 (MUST, 2026-09-28): 라운드 사이·종료 시 반드시 페이지를 주차한다.
# 사고: 수집 종료 후 주행 상태로 방치 → 자곡로 건물에 박힌 채 '건물 충돌' 1,172회 누적(v=0, prog 99.8%),
#       수집기가 안 돌고 있어 기록도 안 남았다. 주행을 켠 스크립트는 자기가 끈다.
park_page(){
  curl -s -X POST -H 'Content-Type: application/json' \
    -d '{"on":0,"force":0,"release":1,"tgt":0,"mode":1,"lp":0.0,"ld":-1,"dOff":0.0,"vT":-1,"park":1}' \
    http://localhost:8901/ctl >/dev/null 2>&1 || true
}

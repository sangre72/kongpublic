# 모델 전환은 오케가 알아서 한다 (MUST — 오너 u_5663/u_5664, 2026-09-26)

> 오너: "웨이크 명령 니가 실행할 수 있음", "적절한 모델을 니가 변경해가면서 할 수 있음. 기본 룰에 적어둬"

## 규칙
- **오케(orch)는 워커와 자기 자신의 모델을 스스로 바꾼다.** 오너에게 묻지 않는다.
  - 워커: `bash telegram_bot/orchestrator/scripts/orch_wake_worker.sh --model <opus|fable|sonnet|haiku> "<지시>"`
  - 오케 자신: `bash telegram_bot/orchestrator/scripts/orch_wake_self.sh --model <m> "<메모>"`
  - `/model` 은 **그 세션에만 즉시 적용**된다(세션 살아 있는 채로 바뀜). `.env ORCH_WORKER_MODEL` 은 다음 워커 spawn 용이고, 이 하네스에서 직접 편집은 권한 거부됨 → 세션 전환은 위 명령으로.
- **작업 성격에 맞춰 고른다**(실측 기준, [[feedback-worker-model-tier-by-task]]):
  - 복잡한 GUI 판단·원인 규명·설계 = opus
  - 정해진 순서 실행·수집·반복 측정 = fable/sonnet, 단순 대기·폴링 = haiku
  - 한도(주간 사용량)가 임박하면 낮은 등급으로 내리고 텔레그램에 1줄 보고.
- 전환했으면 **어느 세션을 무엇으로 왜** 바꿨는지 1줄 보고(1D 중간보고 규칙).

## 확인
워커 창 제목·`osascript ... get contents of selected tab` 로 전환 여부를 눈으로 확인한다.
세션 모델을 '다음 세션부터 적용'이라고 단정하지 말 것 — 2026-09-26 워커가 그렇게 잘못 보고했다가 정정했다.

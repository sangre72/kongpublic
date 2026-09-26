# 모델 전환은 오케가 알아서 한다 (MUST — 오너 u_5663/u_5664, 2026-09-26)

> 오너: "웨이크 명령 니가 실행할 수 있음", "적절한 모델을 니가 변경해가면서 할 수 있음. 기본 룰에 적어둬"

## 규칙
- **오케(orch)는 워커와 자기 자신의 모델을 스스로 바꾼다.** 오너에게 묻지 않는다.
  - 워커: `bash telegram_bot/orchestrator/scripts/orch_wake_worker.sh --model <opus|fable|sonnet|haiku> "<지시>"`
  - 오케 자신: `bash telegram_bot/orchestrator/scripts/orch_wake_self.sh --model <m> "<메모>"`
  - `/model` 은 **그 세션에만 즉시 적용**된다(세션 살아 있는 채로 바뀜). `.env ORCH_WORKER_MODEL` 은 다음 워커 spawn 용이고, 이 하네스에서 직접 편집은 권한 거부됨 → 세션 전환은 위 명령으로.
- **등급 순서(오너 정정 u_5665): fable > opus > sonnet > haiku.** fable 이 최상위다.
  - **초고난이도 = fable**: 논문 검토·아키텍처 설계·근본원인 규명·평가 설계·새 접근 고안.
  - **고난이도 실행 = opus**: 복잡한 GUI 판단, 다단계 구현, 디버깅.
  - **정해진 순서 실행·수집·반복 측정 = sonnet**, 단순 대기·폴링 = haiku.
  - fable 은 비싸고 주간 한도가 따로 있다 → **한도 임박 시 opus 로 내리고**, 초고난이도 과제가 오면 그때만 올린다. 내릴 때·올릴 때 텔레그램 1줄.
- 전환했으면 **어느 세션을 무엇으로 왜** 바꿨는지 1줄 보고(1D 중간보고 규칙).

## 확인
워커 창 제목·`osascript ... get contents of selected tab` 로 전환 여부를 눈으로 확인한다.
세션 모델을 '다음 세션부터 적용'이라고 단정하지 말 것 — 2026-09-26 워커가 그렇게 잘못 보고했다가 정정했다.

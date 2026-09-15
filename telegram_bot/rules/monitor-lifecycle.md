# Monitor 생명주기 (MUST — u_5020, 2026-09-15)

> Monitor 를 걸었으면 **끝낼 책임도 같이 진다.** 한 세션에서 버려진 Monitor 11개가
> 22~23시간 동안 돌고 있었다(오너 지적: "14개 쉘이 다 필요한건가").

## 왜 생기나 (실측 원인, 빈도순)
1. ★**결과를 다른 경로로 얻고 잊는다** — Monitor 걸어두고, 답답해서 Bash 로 직접
   확인하고, 결과 얻고 다음 작업으로. Monitor 는 남는다. **가장 잦다.**
2. **조건이 영영 안 온다** — 감시 대상이 실패하거나 방법을 바꿔서 완료파일이
   안 생긴다. `until` 이 거짓이니 무한히 돈다.
3. **TaskStop 을 안 쓴다** — 타임아웃으로 죽길 기다린다. persistent:true 는 그마저 안 된다.

## 규칙
- **R1** 다른 방법으로 결과를 확인했으면 **그 자리에서 TaskStop**. "이따"는 없다.
- **R2** 감시 대상이 실패·변경돼 조건이 무의미해지면 즉시 TaskStop.
- **R3** `until` 에 성공조건만 넣지 말고 **실패조건도** 넣는다:
  ```bash
  # 나쁨 — 작업이 죽어도 영원히 돈다
  until [ -f $OUT ]; do sleep 30; done
  # 좋음 — 완료되거나 프로세스가 죽으면 빠져나온다
  until [ -f $OUT ] || ! pgrep -f "<작업명>" >/dev/null; do sleep 30; done
  ```
- **R4** 알림이 **한 번**이면 Monitor 말고 `Bash run_in_background` + 종료하는 명령.
  Monitor 는 '여러 번 알림'용이다.
- **R5** 작업 묶음이 끝나면 남은 Monitor 점검(상세: `kaymaps/_common/RECIPE_monitor_lifecycle.txt`).

## 점검
자식이 `sleep` 뿐인 쉘 = 버려진 Monitor. 경과시간이 길면 확실하다.

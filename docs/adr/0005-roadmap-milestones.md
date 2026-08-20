# 0005. 로드맵 · 마일스톤 (위험도 오름차순)

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: R6 §5, README §3

## Context

kongtrol 은 크로스플랫폼(macOS · Linux · Windows) OS 제어 CLI 로, 프로세스·서비스·스케줄러·시스템정보 조회부터 **실제 유저 입력 주입**까지 다룬다. 이 기능들은 위험도 편차가 극심하다: 시스템 조회(read-only)는 승격조차 불요하지만, 입력 주입은 키로거·RAT 와 기술적으로 동일하며 TCC/Wayland 포털/UIPI 등 플랫폼별 권한 모델이 가장 복잡하다.

따라서 "무엇을 먼저 만드느냐"가 곧 보안 설계다. 강력한 기능을 먼저 풀면 방어 프레임(확인·dry-run·audit)이 미완성인 상태에서 최고위험 표면을 노출한다. 마일스톤을 **위험도 오름차순**으로 배치하고, 위험 명령의 공통 방어 프레임을 앞 단계에서 완성한 뒤 그 위에 입력 주입을 얹는다.

## Decision

**위험도 오름차순 마일스톤(M0→M6)을 채택한다. 최고위험인 입력 주입(M5)을 마지막에 둔다.**

핵심 원칙:
- M0 에서 골격 + 방어 프레임 기반(전역 `--json`/`--dry-run`/`--yes`, audit/config, core trait 5종, platform cfg 팩토리)을 먼저 세운다.
- M1 은 read-only 조회만 담아 **승격 불요·안전한 첫 릴리스**로 조기 가치를 낸다.
- M2 에서 [0004](./0004-security-model.md) 4중 방어(확인·`--yes`·`--dry-run`·audit)를 프로세스 kill 에 처음 적용해 실전 검증한다.
- M3·M4 로 권한상승 위임과 스케줄러 추상화를 넓히고, **M5 입력 주입은 방어 프레임이 검증된 뒤에만** 얹는다.

### 마일스톤 표

| 단계 | 범위 | 위험도 | 산출 | 완료조건(DoD) |
|------|------|--------|------|---------------|
| **M0 골격** | clap 스캐폴딩 + core trait 5종 정의(빈 구현) + 전역플래그(`--json`/`--dry-run`/`--yes`) + audit/config 기반 + platform cfg 팩토리 | 없음 | 그릇·trait 슬롯 | `kongtrol --version` 동작 · trait 슬롯 존재 · 3플랫폼 빌드 통과 · 전역플래그 파싱 |
| **M1 조회 MVP** | SystemInfo(R5) + process list/info/tree(R1, READ 전용) | 낮음(read-only, 승격 불요) | 안전한 첫 릴리스 | 3플랫폼에서 sys info · process list 를 JSON+테이블 출력 · 권한 불요 |
| **M2 프로세스 제어** | kill/killall(R1, MUTATE) | 중 | 4중 방어 실전 검증 | 확인프롬프트·`--yes`·`--dry-run`·audit 동작 · 제어 후 존재 재확인(Windows 무증상 실패 대응) · PID+create_time 튜플 식별(PID 재사용 방지) |
| **M3 서비스 제어** | service start/stop/restart/enable(R2) | 중~상 | 권한상승 위임 로직 | systemd(D-Bus)·launchd(bootstrap/bootout)·Windows SCM 백엔드 각 동작 · system/user scope 분리 · 권한부족시 exit 3+안내 |
| **M4 스케줄러** | schedule add/remove/run(R3) | 중 | OS 스케줄러 추상화 | cron 공용입력→OS백엔드(cron/systemd timer/launchd/Task Scheduler) 변환 · croner 로 다음 실행시각 프리뷰 · 표현식 사전검증 |
| **M5 입력주입 ★최고위험 마지막** | input click/move/type/key + device 조회(R5) · TCC/포털/UIPI 권한처리 · rate 제한 · allowlist | **최상** | 가장 강력·마지막 | Win(SendInput)·mac(CGEvent)·Linux X11(XTest) 주입 동작 · 권한 프리플라이트 · 조용한 실패 금지 · **보안 리뷰 필수** · Wayland 는 [0006](./0006-platform-priority.md) 우선순위 따름 |
| **M6 확장(선택)** | `adapters/` 에 web(axum)·telegram(teloxide) 어댑터(core 재사용) | 전송로 보안 별도 | CLI/서버/봇 코어 공유 | CLI/서버/봇이 동일 core 공유 · 어댑터는 얇게 |

### 각 마일스톤 상세 (범위·위험도·DoD)

**M0 — 골격 (위험도: 없음)**
- 범위: clap 스캐폴딩, core trait 5종(ProcessManager·ServiceManager·Scheduler·InputInjector·SystemInfo)의 빈 구현, 전역 플래그(`--json`/`--dry-run`/`--yes`), audit/config 기반, platform cfg 팩토리.
- DoD: `kongtrol --version` 동작 · trait 슬롯 존재 · 3플랫폼(macOS/Linux/Windows) 빌드 통과 · 전역 플래그 파싱 확인.
- 의의: 이후 마일스톤이 "trait 를 채우기만" 하면 되도록 그릇을 완성한다.

**M1 — 조회 MVP (위험도: 낮음, read-only·승격 불요)**
- 범위: SystemInfo(R5), process list/info/tree(R1). READ 전용.
- DoD: 3플랫폼에서 `sys info`·`process list` 를 JSON + 사람용 테이블로 출력 · 승격 권한 불요.
- 의의: 위험 없이 배포 가능한 첫 릴리스로 조기 가치 확보.

**M2 — 프로세스 제어 (위험도: 중)**
- 범위: kill/killall(R1, MUTATE). [0004](./0004-security-model.md) 4중 방어 첫 적용.
- DoD: 확인프롬프트·`--yes`·`--dry-run`·audit 동작 · 제어 후 대상 존재 재확인(Windows 무증상 실패 대응) · PID+create_time 튜플로 식별(PID 재사용 방지).
- 의의: 방어 프레임을 가장 단순한 MUTATE 에서 실전 검증한다.

**M3 — 서비스 제어 (위험도: 중~상)**
- 범위: service start/stop/restart/enable(R2). 권한상승 위임(sudo/UAC/polkit).
- DoD: systemd(D-Bus)·launchd(bootstrap/bootout)·Windows SCM 백엔드가 각각 동작 · system/user scope 분리 · 권한부족 시 exit 3 + 승격 안내.

**M4 — 스케줄러 (위험도: 중)**
- 범위: schedule add/remove/run(R3).
- DoD: cron 을 공용 입력 포맷으로 받아 OS 백엔드(cron/systemd timer/launchd/Task Scheduler)로 변환 · croner 로 다음 실행시각 프리뷰 · 등록 전 표현식 사전검증.

**M5 — 입력 주입 ★최고위험, 마지막 (위험도: 최상)**
- 범위: input click/move/type/key + device 조회(R5). TCC/포털/UIPI 권한처리, rate 제한, allowlist.
- DoD: Win(SendInput)·mac(CGEvent)·Linux X11(XTest) 주입 동작 · 권한 프리플라이트 · 조용한 실패 금지 · **보안 리뷰 필수** · Wayland 지원 시점은 [0006](./0006-platform-priority.md) 우선순위를 따름.
- **왜 마지막인가(R6 §5 인용)**: 입력 주입은 가장 강력·가장 위험하며 권한 모델이 가장 복잡(TCC/Wayland/UIPI)하다. 앞 단계에서 확인·dry-run·audit 프레임을 완성한 뒤 그 위에 얹어야 안전하다.

**M6 — 확장 (선택, 위험도: 전송로 보안 별도)**
- 범위: `adapters/` 에 web(axum)·telegram(teloxide) 얇은 어댑터. core 재사용.
- DoD: CLI/서버/봇이 동일 core 를 공유 · 어댑터는 얇게 유지 · 전송로(네트워크) 보안은 별도 설계.

## Consequences

- **긍정**: 각 마일스톤이 독립 릴리스 가능하며 위험이 점증한다. 방어 프레임(4중 방어·audit)이 M2 에서 조기 검증되어 M5 입력 주입 시 재사용된다. read-only M1 이 조기 가치를 낸다.
- **부정/비용**: 가장 화려한 기능(입력 주입)이 가장 늦게 나와 초기 데모 임팩트가 약하다. M5 전까지 방어 프레임을 앞당겨 투자해야 한다.
- **트레이드오프**: 데모 임팩트를 희생해 보안·안정성을 얻는다. 위험 도구에서는 합당한 교환이다.

## Alternatives

| 대안 | 판정 | 근거 |
|------|------|------|
| ① 입력 주입을 먼저(가장 화려한 기능) | ❌ 탈락 | 방어 프레임(확인·dry-run·audit) 미완성 상태로 최고위험 표면을 노출. R6 §5 원칙(위험도 오름차순)에 정면 위배 |
| ② 3플랫폼 전부 병행 완성 후 릴리스 | ❌ 탈락 | 초기 검증이 지연되고, [0006](./0006-platform-priority.md) 의 macOS 우선 전략과 상충 |
| ③ 조회+제어를 한번에 | ❌ 탈락 | read-only 안전 릴리스(M1)의 조기 가치와 4중 방어의 점진 검증(M2) 이점을 잃음 |

## Open questions

- 각 마일스톤의 목표 기간(일정 산정 미정).
- M5 보안 리뷰의 주체와 체크리스트(누가·무엇을 기준으로 리뷰할지).
- M6 착수 트리거(web/telegram 어댑터를 실제 요구하는 사용자 수요 시점).

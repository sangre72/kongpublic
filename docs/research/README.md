# OS Control CLI — 리서치 종합 (2026-08-13)

> 크로스플랫폼(macOS + Linux + Windows) "OS 상의 모든 객체(프로세스·앱·서비스·스케줄러)를 조회·제어하고, 실제 유저 액션(마우스·키보드·입력 디바이스)까지 주입하는" **CLI 도구**를 만들기 위한 사전 리서치.
>
> **확정 요구사항**: ① 타겟 = 크로스플랫폼 3종  ② 제어 깊이 = 풀 제어(조회+생성/삭제/설정) + 실제 유저 액션 주입  ③ 형태 = 우선 CLI(추후 웹·텔레그램 확장 열어둠)

---

## 0. 이 문서의 위치

리서치를 6개 도메인으로 나눠 병렬 조사했다. 각 문서는 `docs/research/` 아래에 있고, 이 README가 진입점·요약이다.

| 문서 | 도메인 | 핵심 추천 |
|------|--------|-----------|
| [R1-process-management.md](./R1-process-management.md) | 프로세스 관리 | 조회=`sysinfo`/`gopsutil` 위임, 제어(kill/signal/priority)=플랫폼 어댑터 직접 구현(Windows signal 부재 비대칭) |
| [R2-services-daemons.md](./R2-services-daemons.md) | 서비스/데몬 | 공통 인터페이스 + 백엔드(Linux systemd D-Bus·macOS launchd bootstrap·Windows SCM), `service-manager` 크레이트 차용 |
| [R3-schedulers.md](./R3-schedulers.md) | 스케줄러/예약작업 | OS 네이티브 어댑터(cron·systemd timer·launchd·Task Scheduler) + cron을 공용 입력 포맷 + `croner`로 다음 실행시각 자체 계산 |
| [R4-application-control.md](./R4-application-control.md) | 앱 제어(열거·실행·창관리) | 열거/실행=전 플랫폼 안정, 창 제어=플랫폼별 네이티브 분기(★Wayland 미성숙 → 능력 프로빙·graceful degradation) |
| [R5-gui-automation-input.md](./R5-gui-automation-input.md) | GUI 자동화·입력 주입 | `enigo` 기반 + 플랫폼 백엔드(CGEvent/SendInput/XTest/libei), Phase1=Win·mac·X11 → Phase3=Wayland. **★최대 리스크** |
| [R6-architecture-language-security.md](./R6-architecture-language-security.md) | 아키텍처·언어·보안(종합) | **언어=Rust**, CLI=`clap` v4, trait+platform cfg 추상화, 보안 4중 방어, MVP 로드맵 |

> ⚠ 문서 내 라벨 주의: R6 본문 명령 트리에서 R3/R4 번호가 뒤바뀌어 표기된 곳이 있음(input을 R3, schedule을 R4로 적음). **실제 매핑은 위 표 기준**: R3=스케줄러, R4=앱제어, R5=GUI/입력.

---

## 1. 핵심 결론 (TL;DR)

1. **언어 = Rust** (Plan B = Go)
   - 단일 정적 바이너리(설치 편의) + 이 도메인이 이미 Rust로 프로덕션 검증됨(**RustDesk** 원격제어가 `enigo`로 입력주입) + 위험 코드에 메모리 안전.
   - Python/Node = 단일 바이너리 배포 요구와 상충 → 비추천(PoC 한정).

2. **아키텍처 = trait(공통 인터페이스) + 플랫폼별 구현 분리**
   - `core/`에 `ProcessManager`·`ServiceManager`·`Scheduler`·`InputInjector`·`SystemInfo` 5개 trait, `platform/{macos,linux,windows}`에 cfg-gated 구현.
   - R1~R5가 각각 하나의 trait 슬롯에 "어떤 라이브러리/API로 구현하나"만 채우는 구조. 추후 `adapters/`에 웹(axum)·텔레그램(teloxide) 얇은 어댑터만 얹으면 코어 재사용.

3. **"어디서나 100% 동작하는 단일 방법은 없다"** — 특히 입력주입
   - 난이도: **Linux Wayland(최난)** > macOS(TCC 권한) > Windows(UIPI) > Linux X11(최이).
   - Wayland는 표준 입력주입 API가 없어 컴포지터별 파편화(libei+포털 vs uinput/root). → 초기 릴리스는 Win·mac·X11 우선, Wayland는 별도 단계.

4. **보안 = 최상위 축** (이 도구는 그 자체로 공격도구화 가능)
   - 위험 명령(입력주입·kill·service stop·schedule remove) = **4중 방어**: ①확인 프롬프트 ②`--yes` 명시 ③`--dry-run` ④audit log(항상).
   - 비승격 기본 실행, 승격은 OS 표준 경로(sudo/UAC) 위임 — 도구가 자격증명 수집·저장 안 함.
   - **TCC/권한 우회·private API 금지**(2025 TCC 우회 CVE들 존재) — OS 정상 승인 팝업만 유발.

---

## 2. 명령 트리 초안 (osctl)

```
osctl [--json] [--yes] [--dry-run] [--verbose] <domain> <verb> [args]

  process    list | info <pid> | tree | kill <pid> [--signal TERM] | killall <name>
  service    list | status <name> | start|stop|restart|enable|disable <name>
  schedule   list | add <name> --cmd "..." --cron "..." | remove <name> | run <name>
  app        list | launch <name> | quit <name> | focus <name>        (R4)
  input  ★위험  click <x> <y> | move <x> <y> | type "<text>" | key "ctrl+c" | scroll <dx> <dy>
  sys        info | cpu | mem | disk | net | uptime
  device     list | info <id>

  osctl --version | completions <shell> | config <get|set|path>
```
- 위험 등급 태깅: READ / MUTATE / **DANGEROUS**. DANGEROUS = 4중 방어 게이트 강제.
- 출력: 사람용 테이블(위험도=색상+텍스트 라벨 병기) / `--json`(기계용 envelope).

---

## 3. 단계적 개발 로드맵 (위험도 오름차순)

| 단계 | 범위 | 위험도 |
|------|------|--------|
| **M0 골격** | clap 스캐폴딩 + core trait 정의 + 전역 플래그(`--json/--dry-run/--yes`) + audit/config 기반 + platform cfg 팩토리 | 없음 |
| **M1 MVP (조회)** | SystemInfo + process list/info/tree (READ 전용) | 낮음 |
| **M2 프로세스 제어** | kill/killall — 4중 방어 첫 적용 | 중 |
| **M3 서비스 제어** | service start/stop/restart/enable + 권한상승 위임 | 중~상 |
| **M4 스케줄러** | schedule add/remove/run | 중 |
| **M5 입력주입 ★최고위험 마지막** | input click/move/type/key + device. TCC/포털/UIPI 권한, rate 제한, allowlist | **최상** |
| **M6 확장(선택)** | adapters/에 web·telegram 어댑터(core 재사용) | 전송로 보안 별도 |

> 입력주입을 마지막에 두는 이유: 가장 강력·위험·권한복잡. 앞 단계에서 확인·dry-run·audit 프레임을 완성한 뒤 얹어야 안전.

---

## 4. 미해결·후속 결정 사항 (다음 단계에서 확정)

- [ ] **앱 이름/코드네임** 확정 (임시 `osctl`).
- [ ] **초기 타겟 플랫폼 우선순위** — 현재 개발 환경 = macOS(darwin). MVP를 macOS 먼저 완성 후 Linux/Windows 확장할지, 처음부터 3종 병행할지.
- [ ] **Wayland 지원 시점** — M5에서 X11만 먼저 vs libei까지 한 번에.
- [ ] **allowlist 정책 기본값** — 초기엔 확인 프롬프트 기본, allowlist는 opt-in으로 시작할지.
- [ ] **저장소** — 이 리서치는 kong-bot 리포의 `docs/research/`에 있음. 실제 CLI 코드를 별도 리포로 뺄지, 이 리포 하위에 둘지.

---

## 5. 다음 액션 제안

리서치 단계 완료. 다음은 **아키텍처 확정(ADR) → M0 골격 설계서 작성 → 구현 착수** 순.
바로 이어서 할 수 있는 것:
1. 위 §4 미해결 사항을 유저와 확정.
2. 확정 후 **M0(골격) + M1(조회 MVP) 구현 지시서**를 작성해 워커에 위임.

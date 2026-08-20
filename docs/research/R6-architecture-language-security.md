# R6 — CLI 아키텍처 · 언어/런타임 선택 · 보안·권한 모델

> 크로스플랫폼(macOS+Linux+Windows) "OS Control CLI" 종합 설계 문서.
> R1~R5(프로세스·서비스·입력주입·스케줄러·시스템정보 등)를 담는 **그릇(아키텍처)**을 정의한다.
> 조사 기준: 2026-08, WebSearch 실측. 제어 깊이 = 풀 제어 + 실제 유저 액션(입력 주입)까지.

---

## 0. 요약 (TL;DR)

- **언어 1순위 추천: Rust** — 단일 정적 바이너리 배포, 크로스플랫폼 입력주입/시스템 크레이트 생태계 성숙(enigo·sysinfo·service-manager), 프로덕션 검증(RustDesk v1.4.6 원격제어가 enigo 사용). 메모리 안전으로 저수준 코드 리스크↓.
- **CLI 프레임워크: `clap` v4**(derive) — ripgrep·bat·fd 등 프로덕션 검증, 서브커맨드 중첩·`--json` 처리 용이.
- **아키텍처: trait 기반 추상화 계층** — `Process`/`Service`/`Input`/`Scheduler`/`SysInfo` trait 정의 → `platform/{macos,linux,windows}` 구현 분리. R1~R5가 각각 이 trait에 꽂힌다.
- **보안 = 최상위 축**: 위험 명령(입력주입·kill·service·삭제)은 **기본 dry-run 아님이지만 확인 프롬프트 + `--yes` + `--dry-run` + audit log + allowlist** 4중 방어. 권한상승은 최소권한·지점 명시.
- **로드맵**: MVP(조회 read-only) → 프로세스/서비스 제어 → 스케줄러 → **입력주입(최고 위험, 마지막)**.

---

## 1. 언어/런타임 비교

### 1-1. 비교표

| 축 | **Rust** ★1순위 | **Go** | **Python** | **Node/TS** |
|---|---|---|---|---|
| 단일 바이너리 배포 | ✅ 정적 링크 단일 exe, 런타임 불요 | ✅ 단일 exe(가장 쉬움, `CGO_ENABLED=0` 크로스컴파일) | ❌ PyInstaller 번들 크고 취약(OS별 재빌드·안티바이러스 오탐) | ❌ pkg/nexe 번들 대형, native addon 재빌드 |
| 입력주입 라이브러리 | ✅ **enigo 0.6.x**(가장 인기, Win/mac/X11, Wayland/libei feature flag) | ✅ **robotgo**(성숙, 근래 pure-Go CGO-free 백엔드 추가) | △ pyautogui/pynput(성숙하나 인터프리터 의존) | △ **nut.js**(TS, N-API native addon 다수) |
| 프로세스/시스템 API | ✅ **sysinfo**(크로스플랫폼 표준, kill/signal 지원) | ✅ gopsutil 성숙 | ✅ psutil(사실상 표준) | △ 표준 미흡, native 의존 |
| 서비스 관리 | ✅ **service-manager**(launchd/systemd/Windows SCM 통합), daemon-kit | △ 직접 구현 多 | △ 직접 구현 | △ 직접 구현 |
| 저수준 접근 용이성 | ✅ FFI 직접·`windows`/`core-foundation`/`nix` 크레이트 성숙 | △ CGO 필요 시 툴체인 부담 | ✅ ctypes/cffi 쉬움 | △ node-gyp 빌드 부담 |
| 성능(저수준·이벤트루프) | ✅ 최상, GC 없음 | ✅ 우수(GC 있음) | ❌ 인터프리터 느림 | △ V8, GC |
| 메모리 안전(위험 도구엔 중요) | ✅ 컴파일러 보장 | △ GC·nil panic | △ 런타임 | △ 런타임 |
| 개발 속도 | △ 러닝커브·컴파일 시간 | ✅ 빠름·단순 | ✅ 가장 빠름 | ✅ 빠름 |
| 크로스컴파일 편의 | △ 타깃 툴체인 세팅 필요 | ✅ **가장 쉬움** | ❌ OS별 실행환경 | ❌ native addon OS별 |
| 프로덕션 검증(이 도메인) | ✅ **RustDesk**(원격제어 v1.4.6, enigo 내장), ripgrep/fd | ✅ robotgo 다수 RPA | ✅ 자동화 스크립트 다수 | ✅ nut.js 테스트 자동화 |

### 1-2. 1순위 추천: **Rust** — 근거

1. **배포 편의 + 성능 동시 충족**: "우선 CLI 도구, 설치 편의" 요구 → 런타임 의존 없는 단일 정적 바이너리. Python/Node는 번들링 비대·OS별 재빌드로 탈락. Go도 우수하나 아래 2·3 때문에 Rust 우위.
2. **이 도메인 생태계가 이미 Rust로 검증됨**: **RustDesk**(프로덕션 원격제어, 2026-03 v1.4.6)가 `libs/enigo`로 입력주입을 수행 — "풀 제어 + 유저 액션 주입" 요구와 정확히 동일한 부담을 실제 프로덕션에서 감당 중. enigo·sysinfo·service-manager 3종이 각각 입력·프로세스·서비스를 크로스플랫폼으로 커버.
3. **위험 도구엔 메모리 안전이 자산**: 입력주입·프로세스 kill·서비스 제어·FFI를 다루는 도구는 저수준 버그 = 시스템 크래시/보안취약. Rust 컴파일러 보장이 이 리스크를 구조적으로 낮춤.
4. **확장성**: 추후 웹/텔레그램 확장 시 코어 로직을 그대로 라이브러리 크레이트로 두고 `axum`(웹)·`teloxide`(텔레그램) 얇은 어댑터만 추가 가능 → CLI/서버/봇이 동일 코어 공유.

> **Plan B = Go**: 크로스컴파일 최강·개발속도 우위가 절대적 우선이면 Go(robotgo가 CGO-free 백엔드 추가로 배포 부담 완화). 단 서비스관리 통합 라이브러리·메모리안전은 Rust가 앞섬.
> **비추천 = Python/Node**: 단일 바이너리 배포 요구와 상충. 프로토타입/PoC 단계 한정 사용은 가능.

---

## 2. CLI 프레임워크 · 명령 트리 초안

### 2-1. 프레임워크: `clap` v4 (derive 매크로)

- ripgrep·bat·fd·hundreds of CLI가 사용하는 사실상 표준. 2026 벤치 기준 파싱 30%↑·메모리 50%↓ 개선.
- 서브커맨드 **다단계 중첩** 지원 → `osctl <domain> <verb> [args]` 트리에 적합.
- `--json` / `--dry-run` / `--yes` 전역 플래그를 상위 `Cli` 구조체에 두고 하위 전파.

### 2-2. 명령 트리 (초안)

```
osctl [--json] [--yes] [--dry-run] [--verbose] <domain> <verb> [args]

  process   (R1)   list | info <pid> | tree | kill <pid> [--signal TERM] | killall <name>
  service   (R2)   list | status <name> | start <name> | stop <name> | restart <name>
                   | enable <name> | disable <name>
  input     (R3)   ★위험  click <x> <y> [--button left] | move <x> <y> | type "<text>"
                   | key <combo>  (예: "ctrl+c") | scroll <dx> <dy>
  schedule  (R4)   list | add <name> --cmd "..." --cron "..." | remove <name> | run <name>
  sys       (R5)   info | cpu | mem | disk | net | uptime
  device    (R3+)  list | info <id>              (외부디바이스 조회, 주입은 input 하위)

  # 공통
  osctl --version | osctl completions <shell> | osctl config <get|set|path>
```

**설계 규칙**
- 동사 표준: 조회=`list`/`info`/`status`, 변경=`start`/`stop`/`kill`/`add`/`remove` — 위험도 명확 분리(read verb vs mutate verb).
- **위험 등급 태깅**: 각 서브커맨드에 위험도 메타(READ / MUTATE / DANGEROUS). `input`·`kill`·`service stop`·`schedule remove` = DANGEROUS → §4 확인 게이트 강제.

### 2-3. 출력·설정·로깅

| 항목 | 설계 |
|---|---|
| 사람용 출력 | `comfy-table`/`tabled` 크레이트로 정렬 테이블. 색상 = 위험도 표시(빨강=DANGEROUS) — **색상 단독 아님**, 텍스트 라벨 병기(a11y·상태표기 원칙). |
| 기계용 출력 | `--json` → `serde_json` 직렬화 envelope `{ "data": ..., "meta": { "requestId": ... } }` / 에러 `{ "error": { "code", "message", "requestId" } }`. |
| 설정 파일 | `directories` 크레이트로 OS별 표준 경로(macOS `~/Library/Application Support/osctl`, Linux `~/.config/osctl`, Windows `%APPDATA%\osctl`). TOML(`config.toml`) — allowlist·기본 confirm 정책 저장. |
| 로깅 | `tracing` + `tracing-subscriber`. **감사 로그(audit)는 별도 append-only 파일**(§4). |
| exit code | 0=성공, 2=사용자거부(confirm no), 3=권한부족, 4=대상없음, 5=플랫폼미지원. |

---

## 3. 크로스플랫폼 추상화 계층 설계

### 3-1. 핵심 패턴: trait(공통 인터페이스) + 플랫폼별 구현 분리

R1~R5는 각각 하나의 **domain trait**로 정의되고, 플랫폼별 구현이 그 trait를 impl 한다. CLI 핸들러는 trait만 알고 구체 OS 구현을 모른다(의존성 역전).

```
src/
  main.rs               # clap 파서 → 핸들러 디스패치
  cli/                  # 명령 정의(clap derive) + 출력 포맷 + 위험도 게이트
  core/                 # ★플랫폼 무관 trait + 도메인 타입 (그릇)
    process.rs          #   trait ProcessManager   (R1)
    service.rs          #   trait ServiceManager   (R2)
    input.rs            #   trait InputInjector     (R3) ★DANGEROUS
    schedule.rs         #   trait Scheduler         (R4)
    sysinfo.rs          #   trait SystemInfo        (R5)
    error.rs            #   OsctlError, Platform 열거
    security/           #   confirm·audit·allowlist·privilege (§4, 플랫폼 무관 정책)
  platform/             # ★플랫폼별 구현 (cfg-gated)
    macos/              #   CGEventPost·launchd·libproc 등
    linux/              #   uinput/libei·systemd(D-Bus)·/proc
    windows/            #   SendInput·SCM·WinAPI
  adapters/             # (추후) web(axum)·telegram(teloxide) — core 재사용
```

### 3-2. trait 예시 (개념)

```rust
// core/input.rs — R3가 꽂히는 슬롯
pub trait InputInjector {
    fn move_mouse(&self, x: i32, y: i32) -> Result<(), OsctlError>;
    fn click(&self, btn: MouseButton) -> Result<(), OsctlError>;
    fn type_text(&self, text: &str) -> Result<(), OsctlError>;
    fn key_combo(&self, combo: &KeyCombo) -> Result<(), OsctlError>;
}

// 플랫폼 팩토리: cfg 로 컴파일 타임 선택 → 단일 바이너리 안에 해당 OS 구현만
pub fn injector() -> Box<dyn InputInjector> {
    #[cfg(target_os = "macos")]   { Box::new(platform::macos::MacInput::new()) }
    #[cfg(target_os = "linux")]   { Box::new(platform::linux::LinuxInput::new()) }
    #[cfg(target_os = "windows")] { Box::new(platform::windows::WinInput::new()) }
}
```

- **R1~R5 통합 규칙**: 각 R 리서치가 "어떤 크레이트/시스템 API로 이 trait를 구현하는가"만 채우면 됨. 예: R3 → enigo(또는 직접 FFI), R1 → sysinfo, R2 → service-manager.
- **미지원 플랫폼**: trait 메서드가 `Err(OsctlError::Unsupported { platform, feature })` 반환 → CLI가 exit 5로 안내(추측·무시 금지).
- **파일 라인 관리**: trait/타입 정의는 도메인별 파일 분리(§3-1 트리)로 각 파일 ~200~300줄 유지 목표.

### 3-3. 라이브러리 매핑(현 시점 후보 — R1~R5가 확정)

| 계층(trait) | 담당 R | 후보 라이브러리 | 성숙도(2026) |
|---|---|---|---|
| ProcessManager | R1 | `sysinfo` | 크로스플랫폼 표준, kill/signal 지원 |
| ServiceManager | R2 | `service-manager` / `daemon-kit` | launchd·systemd·Windows SCM 통합 |
| InputInjector ★ | R3 | `enigo` 0.6.x (또는 직접 FFI) | 가장 인기·RustDesk 프로덕션 사용, Wayland/libei는 feature flag(실험적) |
| Scheduler | R4 | `service-manager`+cron / OS 스케줄러 래핑 | R4 확정 |
| SystemInfo | R5 | `sysinfo` | 표준 |

---

## 4. 보안·권한 모델 (★이 프로젝트 최상위 축)

> 이 도구는 입력주입·프로세스킬·서비스제어 = 그 자체로 **공격도구화 가능**. `.claude/rules/security-guideline.md` 정신에 따라 보안 = done 조건. 설계 원칙: **강력한 기능일수록 마찰(friction)을 의도적으로 넣는다.**

### 4-1. 권한상승 필요 지점 (최소권한 원칙)

| 작업 | macOS | Linux | Windows | 최소권한 원칙 |
|---|---|---|---|---|
| 프로세스 조회 | 일반 권한 | 일반(타인 proc 일부 제한) | 일반 | 상승 불요 |
| 자기 프로세스 kill | 일반 | 일반 | 일반 | 상승 불요 |
| 타 유저/시스템 프로세스 kill | root(sudo) | root(sudo) | Admin(UAC) | **필요 시에만** 승격, 나머지는 비승격 실행 |
| 서비스 start/stop/enable | root(launchctl) | root(systemctl) | Admin(SCM) | 대상 서비스 단위로만 |
| **입력 주입** | **TCC Accessibility + PostEvent 권한**(사용자 승인 팝업) | uinput 그룹 권한 or libei 포털 승인(Wayland) | 일반(SendInput) 단 UIPI로 상위 무결성 창엔 차단 | OS 권한 모델 존중, 우회 금지 |
| 스케줄러 등록(시스템) | root(launchd) | root(systemd) | Admin(작업 스케줄러) | 유저 스코프 우선, 시스템 스코프는 명시 |

**원칙**
- **비승격 기본 실행**. 승격 필요 명령은 실행 전 "이 명령은 관리자 권한이 필요합니다"를 알리고 OS 표준 승격 경로(sudo/UAC 프롬프트)로 위임 — 도구가 자체적으로 자격증명 수집·저장하지 않음.
- **TCC/권한 우회 금지**: 2026년 TCC 우회 CVE(CVE-2025-43530, CVE-2025-31250)들이 문제된 만큼, 본 도구는 OS 권한 팝업을 **정상 경로로 유발**하고 우회 API·private API를 사용하지 않는다(공격도구화 방지 핵심).

### 4-2. 오남용 방지 4중 방어 (위험 명령)

DANGEROUS 등급(`input *`, `process kill/killall`, `service stop/disable`, `schedule remove`) 실행 시:

| 방어층 | 설계 | 근거 |
|---|---|---|
| **① 확인 프롬프트** | 대화형이면 대상·영향 요약 후 y/N. 파괴적 기본값 = No. | dangerous CLI 설계 관행 |
| **② `--yes` 명시** | 비대화(스크립트)에선 `--yes` 없으면 거부(exit 2). "무심코 실행" 차단. | 자동화 검토가능성 |
| **③ `--dry-run`** | 실제 실행 없이 "무엇을 할지" 동일 결정 로직으로 출력. | dry-run = 의도와 실행 분리 |
| **④ audit log** | 모든 DANGEROUS 명령 = append-only 감사 로그(who/when/cmd/args/결과/승격여부) 기록. `--yes` 여부 무관 항상. | 모든 tool call provenance 기록 |

추가:
- **allowlist(선택)**: `config.toml`에 허용 대상 목록(예: kill 가능 프로세스명, 제어 가능 서비스명). blocklist 아닌 **allowlist 우선**(AI/자동화 보안 권고와 동일). 미설정 시 대화형 확인으로 대체.
- **rate/scope 제한**: 입력주입 대량 반복(예: 자동 클릭 봇) 오남용 방지 위해 반복 횟수 상한 옵션·경고.
- **입력 신뢰 금지**: `type "<text>"`·`key <combo>` 인자는 그대로 시스템에 주입되므로, 셸 인젝션이 아닌 **직접 이벤트 API**(SendInput/CGEventPost/uinput)로만 전달 — 절대 셸 문자열로 재구성하지 않음(command injection 원천 차단).

### 4-3. 크로스플랫폼 권한 모델 차이 요약

| 플랫폼 | 입력주입 관문 | 서비스/프로세스 | 비고 |
|---|---|---|---|
| **macOS** | TCC — Accessibility + Input Monitoring + PostEvent 사용자 승인. `CGEventPost`로 주입. | launchd, root 필요. | TCC 팝업 정상 유발, 우회 CVE 사용 금지. Sequoia/Tahoe에서 권한 강화. |
| **Linux** | X11=바로 주입 가능 / **Wayland=libei + xdg-desktop-portal RemoteDesktop 승인** or uinput(그룹 권한). | systemd(D-Bus), root. polkit로 부분 위임 가능. | Wayland 전환 고려 필수(enigo도 libei feature flag). |
| **Windows** | `SendInput` 일반 권한이나 **UIPI**: 낮은 무결성→높은 무결성 창 주입 차단. | SCM, Admin(UAC). | UAC 승격은 OS 프롬프트 위임. |

### 4-4. 공격도구화 방지 설계 원칙(요약)
1. 권한 우회·private API·TCC 조작 절대 금지 — OS 정상 승인 경로만.
2. 강력 기능 = 마찰 내장(확인·dry-run·audit).
3. 비승격 기본, 승격은 명시·최소·OS 위임.
4. 감사 로그 항상. 무결성 보존(append-only).
5. allowlist 우선, 입력은 이벤트 API 직접 전달(문자열 재구성 금지).

---

## 5. 단계적 개발 로드맵 (위험도 오름차순)

| 단계 | 범위 | 위험도 | 산출 |
|---|---|---|---|
| **M0 골격** | clap CLI 스캐폴딩 + core trait 정의(빈 구현) + `--json`/`--dry-run`/`--yes` 전역 플래그 + audit/config 기반 + platform cfg 팩토리 | 없음 | 그릇 완성, R1~R5가 꽂을 슬롯 |
| **MVP (M1) 조회** | R5 SystemInfo + R1 process list/info/tree (READ 전용) | 낮음(read-only) | 안전한 첫 릴리스, 승격 불요 |
| **M2 프로세스 제어** | R1 kill/killall (MUTATE) — §4 확인 게이트 첫 적용 | 중 | 4중 방어 실전 검증 |
| **M3 서비스 제어** | R2 service start/stop/restart/enable (승격 지점·크로스플랫폼 SCM/systemd/launchd) | 중~상 | 권한상승 위임 로직 |
| **M4 스케줄러** | R4 schedule add/remove/run | 중 | OS 스케줄러 추상화 |
| **M5 입력주입 ★최고 위험 마지막** | R3 input click/move/type/key + device 조회. TCC/포털/UIPI 권한 처리, rate 제한, allowlist | **최상** | 가장 강력·마지막. 보안 리뷰 필수 |
| **M6 확장(선택)** | adapters/ 에 web(axum)·telegram(teloxide) 어댑터 — core 재사용 | (전송로 보안 별도) | CLI/서버/봇 코어 공유 |

> **입력주입을 마지막에** 두는 이유: 가장 강력·가장 위험·권한 모델 복잡(TCC/Wayland/UIPI). 앞 단계에서 확인·dry-run·audit 프레임을 완성한 뒤 그 위에 얹어야 안전.

---

## 6. 참고 링크

**입력주입**
- enigo (crates.io / 버전): https://crates.io/crates/enigo/versions
- enigo GitHub: https://github.com/enigo-rs/enigo
- RustDesk(enigo 프로덕션 사용): https://github.com/rustdesk/rustdesk , https://deepwiki.com/rustdesk/rustdesk
- robotgo(Go): https://github.com/go-vgo/robotgo
- pyautogui(Python): https://github.com/asweigart/pyautogui
- nut.js(Node/TS): https://nutjs.dev/ , https://github.com/nut-tree/nut.js/

**프로세스/시스템/서비스**
- sysinfo: https://crates.io/crates/sysinfo , https://github.com/GuillaumeGomez/sysinfo
- service-manager-rs: https://github.com/chipsenkbeil/service-manager-rs , https://docs.rs/service-manager/latest/service_manager/
- daemon-kit: https://medium.com/rustaceans/daemon-kit-cross-platform-daemon-management-in-rust-4ccb2f78d8b0

**CLI 프레임워크**
- clap 사용 가이드(2026): https://oneuptime.com/blog/post/2026-02-03-rust-clap-cli-applications/view , https://dasroot.net/posts/2026/01/building-cli-tools-clap-rust/
- Rust vs Go CLI 비교: https://github.com/jbelmont/rust-vs-go-cli-comparison

**보안·권한 모델**
- macOS TCC/CGEventPost/PostEvent: https://hacktricks.wiki/en/macos-hardening/macos-security-and-privilege-escalation/macos-security-protections/macos-input-monitoring-screen-capture-accessibility.html
- TCC 우회 CVE-2025-43530: https://securityonline.info/new-tcc-bypass-cve-2025-43530-exposes-macos-to-unchecked-automation/
- TCC 우회 CVE-2025-31250: https://wts.dev/posts/tcc-who/
- 최소권한/allowlist/dry-run 설계: https://kodekloud.com/blog/least-privilege-for-ai-agents-securing-kubectl-terraform-and-cloud-clis/ , https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
- 최소권한 원칙: https://en.wikipedia.org/wiki/Principle_of_least_privilege

---

## 부록: 내부 교차 점검

| 관점 | 점검 결과 |
|---|---|
| 👔 기획자 | 요구(크로스플랫폼·풀제어·입력주입·CLI우선·추후 확장) 전부 반영. adapters/로 웹·텔레그램 확장 슬롯 명시. |
| 💻 개발자 | trait+platform cfg 팩토리로 R1~R5 통합 슬롯 명확. 각 R이 "trait 구현 라이브러리"만 채우면 됨. |
| 🧪 테스터 | 언어 추천은 프로덕션 사례(RustDesk v1.4.6·enigo)·버전 실측(enigo 0.6.x) 근거. 미지원 플랫폼 = Unsupported 반환 규정. |
| 👤 사용자 | 단일 바이너리(설치 편의)·확인/dry-run(안전)·`--json`(자동화) 제공. 위험 명령 마찰로 사고 방지. |

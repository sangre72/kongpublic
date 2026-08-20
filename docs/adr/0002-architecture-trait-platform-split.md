# 0002. 아키텍처 = core trait + platform cfg-gated 구현 분리

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: R6(§3), R1~R5 전체

## Context

kongtrol 은 3플랫폼(macOS · Linux · Windows)에서 프로세스 · 서비스 · 스케줄러 · 앱 · 입력 6개 도메인을 다룬다. 각 도메인은 OS마다 API · 권한 · 동작이 근본적으로 다르다(예: POSIX signal vs Windows 부재, Wayland 프로토콜 부재). 이 이질성을 어떻게 하나의 CLI 코드베이스로 흡수할지 정한다.

> ★리서치 라벨 주의(research/README): R6 본문 명령트리에서 R3/R4 번호가 뒤바뀐 표기가 있으나 **실제 매핑은 R3=스케줄러, R4=앱제어, R5=GUI/입력**. 이 ADR은 실제 매핑 기준.

## Decision

`core/` 에 플랫폼 무관 **domain trait** 를 정의하고, `platform/{macos,linux,windows}` 에 cfg-gated 구현을 분리한다. CLI 핸들러는 trait 만 알고 구체 OS 구현을 모른다(**의존성 역전**). R1~R5 가 각각 하나의 trait 슬롯에 "어떤 라이브러리/API로 구현하나"만 채운다.

### core trait 6종

| trait | 담당 R | 도메인 |
|-------|--------|--------|
| `ProcessManager` | R1 | 프로세스 조회 · 제어(kill/signal/priority) |
| `ServiceManager` | R2 | 서비스/데몬 |
| `Scheduler` | R3 | 스케줄러/예약작업 |
| `AppController` | R4 | 앱 열거 · 실행 · 창 제어 |
| `InputInjector` ★ | R5 | 입력 주입 (**DANGEROUS**) |
| `SystemInfo` | R5 | 시스템 정보 조회 |

### 디렉터리 트리

```
src/
  main.rs               # clap 파서 → 핸들러 디스패치
  cli/                  # 명령 정의(clap derive) + 출력 포맷 + 위험도 게이트
  core/                 # 플랫폼 무관 trait + 도메인 타입
    process.rs          #   trait ProcessManager   (R1)
    service.rs          #   trait ServiceManager   (R2)
    schedule.rs         #   trait Scheduler        (R3)
    app.rs              #   trait AppController    (R4)
    input.rs            #   trait InputInjector    (R5) ★DANGEROUS
    sysinfo.rs          #   trait SystemInfo       (R5)
    error.rs            #   KongtrolError, Platform 열거
    security/           #   confirm·audit·allowlist·privilege (0004, 플랫폼 무관 정책)
  platform/             # 플랫폼별 구현 (cfg-gated)
    macos/              #   CGEventPost·launchd·libproc 등
    linux/              #   uinput/libei·systemd(D-Bus)·/proc·XTest
    windows/            #   SendInput·SCM·WinAPI
  adapters/             # (M6) web(axum)·telegram(teloxide) — core 재사용
```

### trait 예시 (개념, R6 §3-2)

```rust
// core/input.rs — R5(입력주입)가 꽂히는 슬롯
pub trait InputInjector {
    fn move_mouse(&self, x: i32, y: i32) -> Result<(), KongtrolError>;
    fn click(&self, btn: MouseButton) -> Result<(), KongtrolError>;
    fn type_text(&self, text: &str) -> Result<(), KongtrolError>;
    fn key_combo(&self, combo: &KeyCombo) -> Result<(), KongtrolError>;
}

// cfg 팩토리: 컴파일 타임 선택 → 단일 바이너리에 해당 OS 구현만 포함
pub fn injector() -> Box<dyn InputInjector> {
    #[cfg(target_os = "macos")]   { Box::new(platform::macos::MacInput::new()) }
    #[cfg(target_os = "linux")]   { Box::new(platform::linux::LinuxInput::new()) }
    #[cfg(target_os = "windows")] { Box::new(platform::windows::WinInput::new()) }
}
```

### 플랫폼별 구현 라이브러리 매핑 (R6 §3-3 + 각 R)

| trait | 구현 라이브러리/API |
|-------|---------------------|
| ProcessManager | `sysinfo`(조회) + `nix`/`windows`(제어 — Windows signal 부재 흡수) |
| ServiceManager | `service-manager`(launchd · systemd D-Bus · Windows SCM) |
| Scheduler | OS 네이티브(cron · systemd timer · launchd · Task Scheduler) + `croner`(다음 실행시각 계산) |
| AppController | `x-win`/`active-win-pos-rs`(조회) + 네이티브(제어: AX/Win32/wmctrl 등) |
| InputInjector | `enigo` 0.6.x (+ `libei` feature for Wayland) |
| SystemInfo | `sysinfo` **0.39.x**(확정, ★rustc 1.95+ 전제 — 0.39.6 빌드 검증 [FEASIBILITY](./FEASIBILITY.md)) |

> sysinfo 버전 = **0.39.x 확정**(2026-08-13). ProcessManager 조회도 동일 크레이트. 0.38→0.39 API 브레이킹 없음(PoC 무수정 컴파일).

### 미지원 플랫폼 규칙 (R6 §3-2) ★

trait 메서드가 미지원 시 `Err(KongtrolError::Unsupported { platform, feature })` 반환 → CLI 가 **exit code 5**([0003](./0003-cli-surface.md))로 안내. **추측 · 무시 · 조용한 실패 금지.** 예: Wayland 창제어(R4 §3), Windows graceful 종료 부재(R1 §2-2).

## Consequences

- R1~R5 통합 규칙 = 각 R 이 "trait 구현 라이브러리"만 채우면 됨 → 도메인 병렬 개발 가능.
- 단일 정적 바이너리에 실행 OS 구현만 컴파일(cfg-gated) → 배포 이점([0001](./0001-language-rust.md)) 유지.
- trait/타입을 도메인별 파일 분리로 각 ~200~300줄 유지(code-structure 준수).
- 비용: cfg-gated 코드는 3플랫폼 CI 빌드 없이는 컴파일 검증 불가 → CI 매트릭스 필수.

## Alternatives

| 후보 | 탈락 이유 |
|------|-----------|
| 단일 God-module(플랫폼 분기 if/match 난립) | 확장 · 테스트 곤란, 파일 비대(code-structure 위반) |
| 런타임 dyn 로딩/플러그인 | 단일 정적 바이너리 배포 이점 상실 |
| 만능 크로스플랫폼 크레이트 하나 의존 | R4(창제어) · R1(제어) 성숙도 부족 → 불가(R4 §4, R1 §3) |

## Open questions

- trait 를 sync 로 둘지 async(adapters 의 axum/teloxide 대비)로 둘지 — M0([0005](./0005-roadmap-milestones.md))에서 확정.
- cfg-gated 코드의 3플랫폼 CI 빌드 검증 파이프라인 구성.

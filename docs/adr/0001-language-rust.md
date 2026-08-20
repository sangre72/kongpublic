# 0001. 언어 = Rust

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: R6(§1), R1, R5

## Context

kongtrol 은 macOS · Linux · Windows 3플랫폼에서 프로세스 · 서비스 · 스케줄러 · 앱 · **입력 주입**까지 조회 · 제어하는 CLI 다. 확정 요구는 ① 우선 CLI(설치 편의) ② 풀 제어 + 실제 유저 액션 주입 ③ 추후 웹 · 텔레그램 확장. 이 요구를 만족하는 구현 언어/런타임을 정한다.

핵심 제약: **단일 정적 바이너리 배포**(런타임 의존 없이 3플랫폼 설치), 저수준 OS API(입력주입 · kill · FFI) 안전성, 크로스플랫폼 입력/시스템/서비스 생태계 성숙도.

## Decision

- **언어 = Rust** (1순위). Plan B = Go.
- **CLI 프레임워크 = `clap` v4 (derive)**. ripgrep · bat · fd 등 프로덕션 검증, 2026 벤치 파싱 30%↑ · 메모리 50%↓. 서브커맨드 다단계 중첩(`kongtrol <domain> <verb>`)에 적합([0003](./0003-cli-surface.md)).
- 코어를 라이브러리 크레이트로 두고, 추후 `axum`(웹) · `teloxide`(텔레그램) 얇은 어댑터만 얹어 재사용([0002](./0002-architecture-trait-platform-split.md), [0005](./0005-roadmap-milestones.md) M6).

### 근거 (R6 §1-2)

1. **배포 편의 + 성능 동시 충족** — 런타임 의존 없는 단일 정적 바이너리. "우선 CLI · 설치 편의" 요구에 정확히 부합.
2. **이 도메인이 이미 Rust로 프로덕션 검증** — **RustDesk v1.4.6**(2026-03, 원격제어)가 `libs/enigo` 로 입력주입을 수행. "풀 제어 + 유저 액션 주입"과 동일한 부담을 실제 프로덕션에서 감당 중.
3. **위험 도구엔 메모리 안전이 자산** — 입력주입 · 프로세스 kill · 서비스 제어 · FFI 저수준 버그 = 시스템 크래시/보안취약. Rust 컴파일러 보장이 이 리스크를 구조적으로 낮춤.
4. **확장성** — 코어를 그대로 두고 어댑터만 추가 → CLI/서버/봇이 동일 코어 공유.

### 핵심 크레이트 생태계 (R6 §1-1 · §3-3)

| 계층 | 크레이트 | 근거 |
|------|----------|------|
| 입력 주입 | **enigo 0.6.x** | RustDesk 프로덕션 사용, MIT/Apache, Win/mac/X11(+Wayland libei feature) |
| 프로세스 · 시스템 조회 | **sysinfo 0.39.x** (확정, ★rustc 1.95+ 전제) | 크로스플랫폼 표준, MIT. 0.39.6 빌드 검증 완료([FEASIBILITY](./FEASIBILITY.md)) |
| 서비스 관리 | **service-manager** | launchd/systemd/Windows SCM 통합 |
| CLI | **clap v4** | 사실상 표준, derive |

## Consequences

### 긍정
- 3플랫폼 단일 정적 바이너리 = 설치 · 배포 최단순.
- 저수준 코드 메모리 안전 → 위험 도구의 구조적 리스크 완화.
- enigo · sysinfo · service-manager 재사용으로 구현량 절감.
- 코어 라이브러리화로 웹/텔레그램 확장 시 코어 무변경.

### 부정/비용
- 러닝커브 · 컴파일 시간(Go 대비).
- 크로스컴파일 타깃 툴체인 세팅 필요(Go의 `CGO_ENABLED=0` 대비 번거로움).
- `sysinfo` 가 0.x 라 API 잦은 변경(R1) — 제어(kill/signal/priority)는 `nix` · `windows` 크레이트로 직접 보강([0002](./0002-architecture-trait-platform-split.md)).

## Alternatives (고려했으나 탈락)

| 후보 | 강점 | 탈락 이유 |
|------|------|-----------|
| **Go (Plan B)** | 크로스컴파일 최강(`CGO_ENABLED=0`) · 개발속도. robotgo(입력) · gopsutil(프로세스) · kardianos/service | 서비스관리 통합 라이브러리(service-manager) · 메모리안전은 Rust 우위. **크로스컴파일 · 개발속도가 절대 우선이면 Go 재고 가능**(조건부 여지). |
| **Python** | psutil 제어 API 완성도 최고 | 단일 바이너리 배포 요구와 상충(PyInstaller 번들 크고 취약 · OS별 재빌드 · 안티바이러스 오탐). PoC/레퍼런스 한정. |
| **Node/TS** | 개발속도 | nut.js 2025 유료화(prebuilt 구독 $75/월 · npm 공개배포 중단) · robotjs 방치 · native addon OS별 재빌드. 비추천. |

## Open questions

- ~~sysinfo 버전 결정~~ → **✅ 확정(2026-08-13): sysinfo 0.39.x + rustc 1.95+ 전제**(툴체인 1.97.1 업글·0.39.6 빌드 검증 완료, [FEASIBILITY](./FEASIBILITY.md)). 잔여: 0.x API 변동 대비 조회는 sysinfo·제어는 nix/windows 격리([0002](./0002-architecture-trait-platform-split.md)) + 버전 핀 유지.
- 저장소 분리 여부(research/README §4) — 이 리포 하위 vs 별도 리포. 구현 지시 시 확정.

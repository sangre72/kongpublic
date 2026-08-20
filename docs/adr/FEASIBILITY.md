# FEASIBILITY — kongtrol ADR 구현가능성 검증

- 검증일: 2026-08-13 · 검증자: worker_1(kongewalker)
- 목적: docs/adr/ ADR 6종이 [이론상 좋은 설계]에 그치지 않고 [실제 Rust로 구현 가능]한지 실증.
- 방법: crates.io/docs.rs/GitHub 실측(WebSearch/WebFetch) + 최소 PoC 빌드(cargo, scratchpad 임시 — 본 소스 오염 없음).
- ★추측 없음. 확인 못 한 항목은 "미확인" 명시.

---

## 0. 종합 판정 (TL;DR)

> **판정: 구현 가능 (realizable). 치명 블로커 0건. 조정 필요 3건(경미~중). 갭① 해소(2026-08-13).**
> M0(골격)·M1(조회 MVP)은 **PoC로 실동작 실증**됨. M2~M5는 크레이트·API 실재 확인, 단 아래 갭을 ADR/구현에 반영해야 함.

| 갭 | 심각도 | 해결 |
|----|--------|------|
| ① ~~sysinfo 0.39.x = rustc 1.95+ 필요~~ → **✅ 해소(2026-08-13)** | ~~중~~ → 해결 | rustc **1.97.1** 업글 완료(orch) → sysinfo **0.39.6 빌드·실동작 검증 성공**(process list 650개·--json·release 977K). 0.38→0.39 API 브레이킹 없음. **버전정책=0.39.x 확정** |
| ② nix에 `setpriority`(nice) 없음 | 경미 | signal(kill)은 nix 정상 제공. nice는 `libc::setpriority`(unsafe) 또는 `rustix::process::set_priority_process` |
| ③ croner = 스케줄러 아님(파서/다음시각 계산기) | 중(설계) | add/remove·영속화·실행루프는 OS 네이티브 백엔드(cron/systemd/launchd/Task Scheduler)에 위임(ADR 0002 원설계와 일치). croner는 "다음 실행시각 계산·검증"에만 사용 |
| ④ enigo `key_combo` 전용 메서드 부재 | 경미 | `key(mod, Press)`+`key(k, Click)`+`key(mod, Release)` 조립으로 완전 커버 |

---

## 1. 크레이트별 실측 표

출처: crates.io API·docs.rs·GitHub (2026-08-13). ✅확인 / ⚠주의 / ❌불가.

| 크레이트 | ADR지정 | 실측 최신 | 유지상태 | 핵심 API 실재 | 플랫폼 | 판정 |
|---|---|---|---|---|---|---|
| **enigo** | 0.6.x | 0.6.1 (2025-08-28) | 활발 | `Mouse::move_mouse`·`Mouse::button`·`Keyboard::text`·`Keyboard::key`·`raw` 실재 | Win·macOS·X11·Wayland(libei)·BSD | ✅ |
| **sysinfo** | 0.39.x | 0.39.6 (2026-07-09) | 활발 | `processes()`·`process()`·`refresh_*()`·`Process::kill()`·`kill_with(Signal)` 실재 | 크로스플랫폼 | ⚠ (버전=rustc 1.95, 갭①) |
| **service-manager** | 3플랫폼 | 0.11.0 (2026-02-18) | 유지 | `ServiceManager` trait install/uninstall/start/stop/status. Launchd/Systemd/Sc(Win) 구현 | mac·Linux·Win + OpenRC/rc.d/WinSW | ✅ |
| **croner** | cron | 3.0.1 (2025-10-27) | 유지 | `Cron::from_str`·`find_next_occurrence`·`find_previous_occurrence`·`CronIterator`·`describe()` | 크로스플랫폼(순수 로직) | ⚠ (파서지 스케줄러 아님, 갭③) |
| **clap** | v4 | 4.6.6 (2026-08-06) | 매우 활발 | derive·중첩 subcommand | 크로스플랫폼 | ✅ (PoC 실증) |
| **directories** | 설정경로 | 6.0.0 (2025-01-12) | 안정 | `ProjectDirs::from`·`config_dir()` | XDG·Win KnownFolder·macOS Std | ✅ |
| **comfy-table** | 택1 | 8.0.0 (2026-08-05) | 활발 | 테이블 빌더·자동 래핑 | 크로스플랫폼 | ✅ |
| **tabled** | 택1 | 0.21.0 (2026-05-31) | 활발 | struct/enum pretty print | 크로스플랫폼 | ✅ |
| **tracing** | 로깅 | 0.1.44 (2025-12-18) | 활발 | 구조화 로깅 | 크로스플랫폼 | ✅ |
| **tracing-subscriber** | 로깅 | 0.3.23 (2026-03-13) | 활발 | subscriber 조합 | 크로스플랫폼 | ✅ |
| **serde_json** | JSON | 1.0.151 (2026-07-20) | 매우 활발 | JSON 직렬화(envelope) | 크로스플랫폼 | ✅ (PoC 실증) |
| **nix** | Unix signal/prio | 0.31.3 (2026-05-11) | 유지 | `sys::signal::kill(Pid,Signal)` 실재. **setpriority 없음** | Unix 전용 | ⚠ (갭②) |
| **windows** | Win32 FFI | 0.62.2 (2025-10-06) | 매우 활발 | Win32 바인딩 | Windows 타깃 | ✅ |

> 테이블 출력은 comfy-table·tabled 둘 다 실존·활발 — 어느 쪽이든 무방(ADR 0003 "택1" 유효).

---

## 2. ADR 0002 trait 메서드 → 제공 크레이트 vs 직접 FFI

| trait 메서드 | 제공 크레이트 / API | 상태 |
|---|---|---|
| `move_mouse` | enigo `Mouse::move_mouse(x,y,Coordinate)` | ✅ |
| `click` | enigo `Mouse::button(Button, Direction::Click)` | ✅ (이름=button) |
| `type_text` | enigo `Keyboard::text(&str)` | ✅ |
| `key_combo` | enigo `Keyboard::key(Key, Press/Release)` 조립 | ✅ (전용 헬퍼 없음, 갭④) |
| `process list` | sysinfo `System::processes()` | ✅ **PoC 실동작** |
| `process kill` | sysinfo `Process::kill()`/`kill_with(Signal)` + nix `kill(Pid,Signal)`(세밀 시그널) | ✅ |
| `process priority(nice)` | **nix 미제공** → `libc::setpriority`(unsafe) 또는 `rustix::process::set_priority_process` | ❌ FFI 필요(갭②) |
| `service start/stop` | service-manager `ServiceManager::start/stop` | ✅ |
| `schedule add/remove` | **croner=계산만**. add/remove·영속·실행루프는 OS 네이티브 백엔드 직접 구현 | ⚠ 로직만(갭③) |

---

## 3. 플랫폼 컴파일 가능성 (cfg-gate 함정)

- **enigo OS별 조건부 의존성 정상 분리 ✅**: `cfg(target_os="windows")`→windows, `cfg(target_os="macos")`→objc/CoreGraphics/AppKit, `cfg(all(unix,not(macos)))`→libc/x11rb/wayland/reis(libei)/xkb. cfg 게이팅 함정 없음.
- **windows crate non-Windows 빌드 안전 ✅**: 어느 호스트에서도 컴파일(생성 바인딩). `[target.'cfg(windows)'.dependencies]` 선언 또는 사용부 `#[cfg(windows)]` 게이팅하면 non-Win 빌드 실패 없음. → ADR 0002 platform cfg 분리 구조 실현 가능.
- **★enigo `libei` feature 실재 확인 ✅**: GitHub Cargo.toml `[features]`에 `libei`(의존 reis·futures·nom) 존재. `wayland`·`x11rb`(기본)·`xdo`·`xdg_desktop`도 함께. → ADR 0006 Wayland 경로(libei) 실재.

---

## 4. 권한/실행 현실성

- **★macOS TCC(Accessibility) 미승인 시 enigo = 명시적 에러 ✅**: `Enigo::new(&Settings)` → `Result<Self, NewConError>`. `NewConError`에 **`NoPermission`** variant 존재("does not have the permission to simulate input"). → ADR 0004·0002의 "조용한 실패 금지·미지원은 에러 반환" 원칙이 enigo 레벨에서 실제 가능. 미승인 시 `NoPermission` 감지 → exit 3(권한부족) 매핑 가능.
- **Wayland libei**: enigo `libei` feature로 시도, GNOME≥46/KDE≥6.1 + xdg-desktop-portal RemoteDesktop 사용자 승인 조건(ADR 0006). feature 실재하나 컴포지터 커버리지는 런타임 의존 → ADR 0006 폴백 체인(libei→ydotool→미지원 에러) 유효.

---

## 5. 최소 PoC 결과 (실빌드 — scratchpad 임시, 본 소스 무오염)

환경(초기): cargo/rustc 1.89.0. **갱신(2026-08-13): rustc/cargo 1.97.1 업글 후 sysinfo 0.39.6 재검증.** macOS(arm64).

| 항목 | 결과 |
|------|------|
| `cargo new` + `cargo add sysinfo clap --features derive` | ✅ (초기 sysinfo 0.38.4·clap 4.6.6 해석) |
| `cargo build` (clap 명령트리 + sysinfo 조회) | ✅ 통과 (objc2-core-foundation 등 macOS 네이티브 의존 자동 해석) |
| `kongtrol process list` 실행 | ✅ 실제 프로세스 조회·출력(650여 개) |
| `--json` envelope 출력 | ✅ `{"data":{"count":...},"meta":{"requestId":"poc"}}` (ADR 0003 포맷) |
| `--version` / `--help` (subcommand 트리) | ✅ clap 자동 생성 동작 |
| release 단일 바이너리 크기 | ✅ ~1.0M (ADR 0001 단일 정적 바이너리 배포 실증) |
| **★sysinfo 0.39.6 빌드(rustc 1.97.1)** | ✅ **통과(11.07s)** — process list 650개·`--json`·release **977K**. 0.38→0.39 PoC 코드 무수정 컴파일 = **API 브레이킹 없음**. 갭① 해소 |

> M0(clap 골격+전역플래그)·M1(process list 조회 READ)의 **핵심 구조가 실제 컴파일·실행**됨. ADR 0003 명령트리·전역플래그·JSON envelope·exit·단일바이너리 설계가 이론이 아닌 실물로 검증됨.

---

## 6. 마일스톤별 실현성 (ADR 0005)

| 마일스톤 | realizable? | 근거·조건 |
|----------|-------------|-----------|
| **M0 골격** | ✅ 실증 | PoC로 clap+trait+전역플래그 빌드·실행 확인. sysinfo 0.39.6 확정(갭① 해소) → **blocker 0** |
| **M1 조회 MVP** | ✅ 실증 | `process list` 653개 실조회. sysinfo `SystemInfo`·`ProcessManager(조회)` 실동작 |
| **M2 프로세스 제어** | ✅ 가능 | sysinfo `kill/kill_with` + nix `kill(signal)`. nice는 libc/rustix FFI(갭②) |
| **M3 서비스 제어** | ✅ 가능 | service-manager 0.11.0 3플랫폼 커버(launchd/systemd/Sc). 권한상승은 OS 위임(ADR 0004) |
| **M4 스케줄러** | ⚠ 가능(조정) | croner=다음시각 계산·검증만. add/remove·실행은 OS 네이티브 백엔드 직접 구현(갭③, ADR 0002 원설계와 부합) |
| **M5 입력주입** | ✅ 가능 | enigo 0.6.1(move/button/text/key), libei feature 실재, NoPermission 에러 감지. Wayland는 런타임 컴포지터 의존(ADR 0006 폴백) |
| **M6 확장** | 미검증 | axum/teloxide는 이번 범위 밖(웹실측 안 함). 추후 검증 |

---

## 7. ADR 수정 필요 항목

1. ~~[ADR 0001·0002] sysinfo 버전 명시 조정~~ → **✅ 확정(2026-08-13)**: 유저 결정 = **sysinfo 0.39.x + rustc 1.95+ 전제**. rustc 1.97.1 업글·0.39.6 빌드 검증 완료. ADR 0001·0002에 각주 반영.
2. **[ADR 0002] nix 역할 정정** — nix는 signal(kill)만. nice(setpriority)는 `libc`/`rustix`로 명시(nix가 아님).
3. **[ADR 0002·0005] croner 역할 명확화** — "스케줄 엔진"이 아니라 "cron 파싱·다음 실행시각 계산·검증". 등록/영속/실행은 OS 네이티브 백엔드 담당(원설계와 실은 일치, 문구만 명확화).
4. **[ADR 0002] enigo key_combo** — 전용 메서드 없음, Press/Release 조립임을 구현 노트로.

> 위 4건 모두 **치명 블로커 아님**(설계 골격 유효). 구현 착수 전 ADR에 각주로 반영 권장.

---

## 8. 결론

- **M0 착수 가능(blocker 0)**: sysinfo 0.39.6 + rustc 1.97.1 빌드 검증 완료. PoC가 M0·M1 골격을 실물로 증명.
- **블로커 0**, 조정 3건(갭②③④, 전부 경미~중, 대체수단 명확). 갭① 해소.
- 다음: M0 구현 지시서 작성(또는 ADR 0007 perception-decision-loop 선행).

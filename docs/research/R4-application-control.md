# R4 — 애플리케이션 제어 (Application Control) 리서치

> 크로스플랫폼(macOS + Linux + Windows) "OS Control CLI" 도구의 R4 = **앱 제어** 영역.
> 조사일: 2026-08-13 · 방법: WebSearch 실측(근거 링크 하단).

---

## 1. 개요 — "프로세스 제어"와 "앱 제어"의 차이

| 구분 | 대상 추상 | 식별자 | 예시 동작 |
|------|-----------|--------|-----------|
| **프로세스 제어**(R3 등) | 실행 중 OS 프로세스(PID) | PID, 실행파일 경로 | kill, nice, 메모리/CPU 조회 |
| **앱 제어(R4)** | "설치된 애플리케이션" 논리 단위 (1 앱 = N 프로세스/창) | 번들ID(macOS)·.desktop id(Linux)·AppUserModelID/제품코드(Windows) | 앱 **열거**(설치목록), **실행**, **창 포커스/최소화/종료**, **frontmost 조회** |

핵심: 앱 제어는 **UI 창(window)·설치 메타데이터** 레벨이라 OS/데스크톱환경(DE)별 편차가 프로세스 제어보다 훨씬 크다. 특히 Linux는 **X11 vs Wayland**에서 근본적으로 갈린다(§3).

---

## 2. 플랫폼별 비교표

### 2-1. 설치된 앱 열거

| 플랫폼 | 소스 | 방법(CLI/API) | 비고 |
|--------|------|----------------|------|
| **macOS** | `/Applications`, LaunchServices DB | 디렉터리 스캔 + `lsregister -dump`, NSWorkspace `urlsForApplications(withBundleIdentifier:)` | `lsregister` = `.../LaunchServices.framework/.../Support/lsregister`(비공개 경로). 앱=`.app` 번들. `system_profiler SPApplicationsDataType`도 가능(느림) |
| **Linux** | XDG `.desktop` 파일 | `/usr/share/applications`, `~/.local/share/applications` 스캔 → `Name`/`Exec`/`Icon` 파싱 | XDG Desktop Entry 표준. Flatpak/Snap은 별도 경로 추가 |
| **Windows** | 레지스트리 Uninstall + AppX/UWP + Start Menu | `HKLM/HKCU\...\CurrentVersion\Uninstall`(+`Wow6432Node`) 조회, `Get-AppxPackage`(UWP), `Get-StartApps`(AUMID) | ★레지스트리만으론 Store 내장앱(계산기·사진) 누락 → **레지스트리 + AppX 병행 필수** |

### 2-2. 앱 실행(launch)

| 플랫폼 | 방법 | 비고 |
|--------|------|------|
| **macOS** | `open -a "AppName"` / `open -b <bundleId>` / NSWorkspace `openApplication(at:)` | 파일 연결 실행 `open <file>` |
| **Linux** | `.desktop`의 `Exec=` 실행 or `gio launch app.desktop` / `xdg-open <file>`(연결앱) | `xdg-open`은 "기본앱으로 파일 열기"용, 앱 자체 실행과 구분 |
| **Windows** | `start "" "App"` / ShellExecute / `Start-Process`, UWP는 `explorer shell:AppsFolder\<AUMID>` | AUMID로 UWP 실행 |

### 2-3. 창 제어(포커스·최소화·종료·frontmost)

| 플랫폼 | 열거/포커스/최소화/종료 | frontmost(활성앱) 조회 | 권한 |
|--------|--------------------------|-------------------------|------|
| **macOS** | AppleScript/JXA(`System Events` → `tell process`), Accessibility API(AXUIElement) | NSWorkspace `frontmostApplication`, `runningApplications` | ★Accessibility + Automation TCC 권한(§5) |
| **Linux/X11** | `wmctrl`(EWMH), `xdotool`(XTEST) — 열거·activate·minimize·close 전부 가능 | `xdotool getactivewindow` | 거의 무제한(X11 설계상 앱 간 접근 허용) |
| **Linux/Wayland** | ★**표준 프로토콜 없음** — DE별 상이(§3) | 컴포지터별 상이 | 컴포지터 정책 |
| **Windows** | Win32 `EnumWindows`/`FindWindow` + `SetForegroundWindow`/`ShowWindow(SW_MINIMIZE)` + `PostMessage(WM_CLOSE)` | `GetForegroundWindow` | ★foreground 제약(§5-3) |

---

## 3. ★ Wayland 제약 (가장 중요한 플랫폼 한계)

Wayland는 보안 설계상 **"한 프로그램이 다른 창을 이동·리사이즈·최대화·닫도록 요청하는 내장 프로토콜이 없다"**. 그 결과:

| 도구 | X11 | Wayland | 실측 사실 |
|------|-----|---------|-----------|
| `wmctrl` | ✅ 완전 동작 | ❌ 전혀 안 됨 | EWMH(X11 전용) 의존 |
| `xdotool` | ✅ 완전 동작 | ⚠️ 대부분 실패 | XTEST/Xlib(X11 전용). typing·window search 미동작 |
| `wlrctl` | — | △ wlroots 계열만(Sway 등) + 비기본 프로토콜 지원 시 | GNOME/KDE Mutter/KWin엔 부적합 |
| `kdotool` | — | △ **KDE Plasma+Wayland 전용** | KWin 스크립팅 기반 |
| GNOME 확장 + D-Bus | — | △ **GNOME 전용** — 확장 설치·JS 메서드를 D-Bus로 노출해야 창 제어 | 서드파티가 임의로 못 함 |

**결론(Wayland)**: 컴포지터마다 별도 구현 필요 → **범용 창 제어 불가**. GNOME=확장+D-Bus, KDE=kdotool/KWin 스크립트, wlroots=wlrctl. XDG Portal에도 임의 창 조작 API는 없음. **CLI는 "X11이면 xdotool/wmctrl, Wayland면 감지 후 제한 기능만 + DE별 백엔드" 전략이 현실적.**

---

## 4. 크로스플랫폼 라이브러리 (WebSearch 실측)

| 라이브러리 | 언어 | 범위 | 앱 제어 관점 적합성 |
|------------|------|------|----------------------|
| **x-win** (crates.io) | Rust | Win10/11, Linux(X server, GNOME ≤45), macOS 10.6+ | 활성창/열린창 **열거**·title·position·size 조회. ★자기 창 생성용 아님(타 앱 창 정보 조회) — 조회엔 적합, 제어(포커스/종료)는 별도 |
| **active-win-pos-rs** (crates.io) | Rust | Win/macOS/Linux(**X11+Wayland 일부**) | 활성창 속성 조회. Wayland 일부 지원 명시 |
| **windows** crate | Rust | Windows 전용 | Win32 API 전량 호출(FindWindow/SetForegroundWindow 등) — 창 **제어**용 저수준 |
| **winit / tao / app_window** | Rust | 전 플랫폼 | ★**자기 앱 창 생성·관리** 라이브러리 — **타 앱 창 제어 아님**. R4 용도엔 부적합(오해 주의) |

**요지**: "타 애플리케이션 창을 조회"하는 크로스플랫폼 크레이트는 존재(x-win·active-win-pos-rs)하나, **열거·정보조회 위주**다. 실제 **포커스/최소화/종료 "제어"는 플랫폼별 네이티브 API 직접 호출**(macOS AX/AppleScript, Win32, X11/DE별)이 사실상 표준이며 완전한 크로스플랫폼 "제어" 단일 크레이트는 성숙도 낮음.

---

## 5. 권한/보안 고려

### 5-1. macOS (가장 까다로움)
- **TCC**(Transparency, Consent, Control)가 창 제어를 게이팅. AXUIElement로 다른 프로세스 UI 트리를 읽으려면 **Accessibility 권한** 필요, 합성 입력/제어엔 **Automation(kTCCServicePostEvent)** 권한 필요. 사용자 명시 동의(시스템 설정 승인) 필수.
- AppleScript `tell application "System Events"`로 창 조작 시에도 동일 TCC 승인 요구.
- ★2025~2026 알려진 이슈: `AXIsProcessTrusted`가 per-process 캐시를 읽어 OS 업데이트(Sequoia→Tahoe/26) 후 권한 재검증이 캐시 무효화 안 되는 버그 → CLI가 "권한 있음"으로 오판 가능. **런타임 권한 재확인 로직 필요.**

### 5-2. Linux
- X11: 앱 간 창 접근이 사실상 자유(설계상 격리 없음) → 권한 문제 적으나 **보안적으론 오히려 X11의 약점**.
- Wayland: 격리가 강해 권한이 아니라 **프로토콜 부재**가 벽(§3).

### 5-3. Windows — foreground 제약
- `SetForegroundWindow`는 아무 프로세스나 임의 창을 앞으로 못 가져옴. 조건: 호출 프로세스가 이미 foreground이거나 / foreground lock timeout 만료(`SPI_GETFOREGROUNDLOCKTIMEOUT`) / `AllowSetForegroundWindow`로 위임받음 등.
- 우회는 focus-stealing으로 간주(정상 앱은 taskbar flash로 대체). CLI는 이 제약을 문서화하고 실패 시 graceful 처리 필요.
- UWP/AppX 열거·설치제거는 관리자 권한 또는 `-AllUsers` 시 상승 필요.

---

## 6. ★ 추천 — 이 CLI의 앱 제어 구현 접근

1. **계층 분리**: `enumerate`(열거) / `launch`(실행) / `window`(창 제어) 3서브명령. 열거·실행은 전 플랫폼 안정적으로 구현, 창 제어는 "가용성 매트릭스"로 능력 광고(capability probing).
2. **플랫폼별 네이티브 백엔드 채택**(단일 만능 크레이트 지양 — 성숙도 부족):
   - macOS: NSWorkspace(열거·실행·frontmost) + AppleScript/AX(창 제어). **시작 시 TCC 권한 프리플라이트 체크** + 미승인 안내.
   - Windows: 레지스트리+`Get-AppxPackage`(열거), `Start-Process`/ShellExecute(실행), `windows` crate Win32(창 제어). foreground 제약 문서화.
   - Linux: **런타임에 `XDG_SESSION_TYPE` 감지** → X11이면 `wmctrl`/`xdotool`(또는 x11 크레이트) 풀기능 / Wayland면 DE 감지(GNOME→D-Bus 확장, KDE→kdotool/KWin script, wlroots→wlrctl) 후 **지원되는 부분만** + "Wayland 제약" 명시.
3. **조회는 크로스플랫폼 크레이트 재사용**: 활성창/열린창 열거는 `x-win` 또는 `active-win-pos-rs`로 통일(구현 절감), 실제 "제어"만 네이티브.
4. **실패는 조용히 능력 없음 반환**(권한/프로토콜 부재를 에러가 아닌 `unsupported`로) — 크로스플랫폼 CLI UX 일관성.
5. **보안 원칙**: 창 종료(`WM_CLOSE`/AX close)는 강제 kill이 아닌 정상 종료 요청 우선. macOS Automation/Accessibility 권한은 사용자 동의 없이 우회 금지.

**근거 요약**: Wayland에 범용 창 제어 프로토콜이 없어(§3) 단일 구현 불가 → DE 감지·백엔드 분기 불가피. macOS는 TCC, Windows는 foreground lock이라는 서로 다른 게이트가 있어(§5) "능력 프로빙 + graceful degradation"이 유일하게 일관된 크로스플랫폼 설계다.

---

## 7. 참고 링크

- Wayland 창 제어 파편화: https://www.semicomplete.com/blog/xdotool-and-exploring-wayland-fragmentation/
- xdotool/Wayland 이슈(리포지토리): https://github.com/jordansissel/xdotool
- wmctrl 대안 정리: https://linuxvox.com/blog/what-are-the-alternatives-to-wmctrl/
- GNOME Shell 개발(Mutter/D-Bus 맥락): https://blogs.gnome.org/shell-dev/2025/09/10/gnome-kiosk-updates/
- x-win crate: https://crates.io/crates/x-win
- active-win-pos-rs crate: https://crates.io/crates/active-win-pos-rs
- windows crate(Win32): https://crates.io/crates/windows
- winit(자기창 관리 — 구분용): https://github.com/rust-windowing/winit
- NSWorkspace/frontmost 실측: https://jaredh159.com/posts/querying-running-applications-in-macos/
- LaunchServices/lsregister: https://newosxbook.com/tools/lsdtrip.html
- Apple Manipulating Applications: https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/Workspace/Articles/ManipulatingApplications.html
- macOS Accessibility/AX 자동화 실패 모드: https://fazm.ai/t/macos-accessibility-automation
- macOS TCC(HackTricks): https://angelica.gitbook.io/hacktricks/macos-hardening/macos-security-and-privilege-escalation/macos-security-protections/macos-tcc
- Windows 설치앱 열거(레지스트리+AppX): https://theitbros.com/how-to-get-list-of-installed-programs-in-windows/
- Get-AppxPackage/UWP: https://woshub.com/uninstall-apps-with-powershell-windows/
- SetForegroundWindow 제약: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow
- AllowSetForegroundWindow: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-allowsetforegroundwindow

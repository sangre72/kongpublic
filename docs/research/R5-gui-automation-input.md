# R5 — GUI 자동화 + 입력 디바이스 시뮬레이션 리서치

> OS Control CLI (macOS + Linux + Windows) 크로스플랫폼 도구의 GUI 자동화·입력 주입 담당 리서치.
> 조사일: 2026-08-13 / 기준: 2026년 최신 stable, WebSearch 실측 근거.
> ★이 도메인은 **플랫폼 편차·권한 제약이 전체 CLI 중 가장 크다.** 특히 Linux Wayland 가 병목.

---

## 1. 개요 — "실제 유저 액션 시뮬레이션"의 의미와 난이도

"실제 유저처럼 마우스를 움직이고 클릭하고 키를 누른다"는 것은, **OS 의 입력 스택 최하단(커널/컴포지터/윈도우 서버)에 가짜 이벤트를 주입(inject)**하는 행위다. 이는 브라우저 자동화(Selenium/Playwright, 앱 내부 DOM 제어)와 근본적으로 다르다 — **OS 전역**에 작용하며 어떤 앱이든 조작 가능하지만, 그만큼 **키로거·리모트 조종 멀웨어와 기술적으로 동일**하기 때문에 모든 현대 OS 가 강력한 권한 게이트로 막는다.

**난이도 순위 (높을수록 어려움):**

| 순위 | 플랫폼 | 핵심 장벽 |
|------|--------|-----------|
| 1 (최난) | **Linux Wayland** | 보안 모델상 임의 입력 주입 원천 차단. 컴포지터별 파편화(GNOME/KDE/wlroots 제각각) |
| 2 | **macOS** | Accessibility + (모니터링 시) Input Monitoring/Screen Recording 권한 필수. TCC 승인 UI |
| 3 | **Windows** | UIPI(무결성 레벨) — 낮은 권한→높은 권한 앱 입력 주입 차단. UAC 창은 SecureDesktop |
| 4 (최이) | **Linux X11** | XTest 확장으로 비교적 자유롭게 주입 가능(X11 자체가 보안 약함) |

핵심 결론 선제시: **"어디서나 100% 동작하는 단일 방법은 없다."** 플랫폼별 백엔드를 분기하고, Wayland 는 별도 취급하며, 권한 미승인 시 명확히 실패를 알리는 설계가 필수.

---

## 2. 플랫폼별 입력 주입 방법 비교표

| 항목 | macOS | Linux X11 | Linux Wayland | Windows |
|------|-------|-----------|---------------|---------|
| **핵심 API** | CGEvent (Quartz Event Services) — `CGEventCreateKeyboardEvent`/`MouseEvent` + `CGEventPost` | XTest 확장 (`XTestFakeKeyEvent` 등) | ❌ 표준 주입 API 없음. `libei`+포털 or `/dev/uinput` | `SendInput` (Win32 winuser.h) |
| **권한 요구** | **Accessibility** 권한(주입 시). 모니터링 시 Input Monitoring, 캡처 시 Screen Recording | 없음 (X 서버 접근권만) | libei: 포털 사용자 승인 / uinput: `input` 그룹·root·udev | 없음(단, UIPI 무결성 규칙) |
| **전역 주입** | ✅ (권한 승인 후) | ✅ | △ (컴포지터 정책·포커스 존중) | ✅ (동일/하위 무결성 대상만) |
| **좌표계 주의** | flipped 없음, 논리 픽셀 | 화면 픽셀 | 컴포지터 의존 | 물리 픽셀(DPI aware 필요) |
| **주요 제약** | TCC 다이얼로그 승인 필요, 앱 서명·번들 권장 | Wayland 세션에선 Xwayland 앱에만 도달 | 컴포지터마다 지원 상이, root/포털 필요 | UAC 창·상위 무결성 앱엔 주입 불가 |
| **근거** | Apple Quartz Event Services, HackTricks TCC | pynput limitations | rustdesk #4515, wdotool, semicomplete blog | MS Learn SendInput, Project Zero 2026-02 |

**macOS 권한 세부** (WebSearch 실측):
- `CGEventTap` 생성 시 `defaultTap` → **Accessibility** 권한 요청 트리거, `listenOnly` → **Input Monitoring** 권한.
- 입력 **주입(post)** = Accessibility 권한. 입력 **감시(monitor)** = Input Monitoring. **화면 캡처** = Screen Recording. 세 권한은 별개.
- Input Monitoring 은 샌드박스·App Store 앱도 `CGPreflightListenEventAccess`/`CGRequestListenEventAccess` 로 요청 가능. Accessibility 는 사용자가 시스템 설정에서 수동 토글 필요.

**Windows UIPI 세부** (WebSearch 실측):
- `SendInput` 은 UIPI 대상 — **동일하거나 더 낮은 무결성 레벨**의 앱에만 입력 주입 가능. 상위 무결성 앱(관리자 권한 창 등)엔 차단.
- 우회: 매니페스트 `uiAccess=true` + 보안 위치 설치 + 서명 → UIPI 우회 가능. 단 배포 부담 큼.
- UAC 승인 창은 **SecureDesktop** 에 뜨므로 어떤 방법으로도 자동 주입 불가(설계 의도). ★2026-02 Google Project Zero 가 UIAccess 남용 우회 사례 발표 — 이 경로는 보안상 민감하니 CLI 가 정당 용도로만 쓰도록 명시.

---

## 3. ★Wayland 제약 상세 — 왜 어렵고 무엇이 필요한가

Wayland 는 X11 의 보안 취약점(임의 앱이 다른 앱의 입력을 훔치거나 주입 가능)을 근본 해결하려는 설계라, **"임의 프로세스가 전역 입력을 주입한다"는 것 자체를 거부**한다. 그래서 X11 의 `XTest` 같은 만능 주입 API 가 존재하지 않는다.

### 3가지 우회 경로 비교 (WebSearch 실측)

| 경로 | 원리 | 권한 | 포커스 인식 | Flatpak/샌드박스 | 컴포지터 지원 | 평가 |
|------|------|------|-------------|------------------|----------------|------|
| **① libei + XDG RemoteDesktop 포털** | 앱이 포털로 세션 요청 → 사용자 승인 → `libei` 로 컴포지터에 emulated input 전송 | 포털 다이얼로그 사용자 승인 | ✅ 존중 | ✅ 호환 | GNOME ≥46, KDE Plasma ≥6.1 | ★**미래 표준·권장** |
| **② `/dev/uinput` (ydotool)** | 커널 uinput 으로 가상 입력 디바이스 생성 → 커널 레벨 이벤트. 컴포지터 우회 | root 또는 `input` 그룹 + udev 규칙, `ydotoold` 데몬 필요 | ❌ 포커스 무시 | ❌ 비호환 | 컴포지터 무관(커널단) | 강력하나 침습적·데몬 필요 |
| **③ Xwayland 폴백** | Wayland 세션 내 X11 호환 레이어에 XTest | 없음 | 제한적 | - | Xwayland 실행 시 | ⚠️ **Xwayland 앱에만 도달**, 네이티브 Wayland 앱엔 무효 |

### 핵심 시사점
- **ydotool**: `/dev/uinput` 에 write → root 또는 정교한 udev 규칙 필요, `ydotoold` 백그라운드 데몬 상주, 포커스/윈도우 관리 인식 없음, Flatpak 비호환. 강력하지만 "실제 유저처럼"과는 거리(창 포커스 무시).
- **libei 경로**: GNOME 46+/KDE Plasma 6.1+ 에서 커널 권한·input 그룹·udev **없이** 동작, 사용자 승인 기반이라 보안 모델에 부합. `wdotool`(libei+wlroots 기반 xdotool 호환 도구) 같은 신규 프로젝트가 이 방향. **2026 기준 이것이 정답 방향이나 아직 컴포지터 커버리지가 완전치 않음.**
- **파편화**: semicomplete 블로그가 지적하듯 Wayland 는 "컴포지터마다 프로토콜 지원이 달라" 단일 코드로 모든 배포판 커버 불가. GNOME/KDE/wlroots(Sway 등) 3갈래를 각각 대응해야 함.

**Wayland 대응 전략 결론:** ① libei/포털 우선 시도 → ② 실패 시 ydotool(uinput) 폴백(권한 안내) → ③ 그래도 안되면 명확히 "이 컴포지터는 미지원" 에러. 절대 "조용히 아무것도 안 함" 금지.

---

## 4. 크로스플랫폼 라이브러리 비교표 (WebSearch 실측)

| 라이브러리 | 언어 | 최신버전/시점 | Win | macOS | X11 | Wayland | 화면인식 | 유지보수 | 라이선스 | 비고 |
|-----------|------|--------------|:---:|:-----:|:---:|:-------:|:--------:|----------|----------|------|
| **enigo** | Rust | **0.6.1** (2025-08-28) | ✅ | ✅ | ✅ | △ libei(feature flag, 버그有) | ❌ | ✅ **활발** | MIT/Apache-2.0 | RustDesk 등 프로덕션. Wayland 는 `libei`+`smol`/`tokio` feature. ★Rust CLI 라면 1순위 |
| **PyAutoGUI** | Python | 0.9.54 (~2023, **2년+ 정체**) | ✅ | ✅ | ✅ | ❌ | ✅ 내장(이미지매칭) | ❌ **사실상 미유지** | BSD-3 | 화면인식 강점이나 유지보수 중단. 포크(PyAutoGUI-ng) 존재 |
| **pynput** | Python | 1.7.6 (2021) | ✅ | ✅ | ✅ | ⚠️ Xwayland 한정 | ❌ | △ 저속 | LGPL-3.0 | 입력 주입+**모니터링(리스너)** 강점. macOS root/화이트리스트 필요 |
| **robotjs** | Node | 0.6.0 (**미유지, N-API 이전 정체**) | ✅ | ✅ | ✅ | ❌ | △ pixel/화면 | ❌ **방치** | MIT | 신규 Node 버전 빌드 문제 다수. 사실상 폐기 |
| **nut.js** | Node | 4.x (**2025 라이선스 전환**) | ✅ | ✅ | ✅ | ❌ | ✅ OpenCV 기반 | ⚠️ 유료화 | **소스=오픈, prebuilt=유료구독($75/mo)** | robotjs 후계였으나 npm 공개 배포 중단. 커뮤니티 포크 `@nut-tree-fork/nut-js` |
| **AutoHotkey** | (자체 스크립트) | v2.x | ✅ | ❌ | ❌ | ❌ | △ | ✅ | GPL-2.0 | **Windows 전용**. 크로스플랫폼 CLI 엔 부적합 |
| **ydotool** | C (CLI/데몬) | 활발 | ❌ | ❌ | △ | ✅ uinput | ❌ | ✅ | AGPL-3.0 주의 | Wayland 입력 주입용 외부 도구. AGPL 라이선스 유의 |

### 라이브러리 실측 핵심
- **enigo (Rust)**: 0.6.0/0.6.1 이 **2025-08-28 릴리스** — 활발. Wayland 는 `libei` feature 활성화 시 시도하나 "버그 있음"으로 feature flag 뒤에 숨김. RustDesk(원격제어 프로덕션)가 채택. MIT/Apache 듀얼 라이선스로 상업 이용 안전.
- **PyAutoGUI**: 2025-10 기준 "마지막 커밋 2년 전, 미유지" 확인. Wayland 미지원. **이미지 매칭 내장**이 유일 강점이나 유지보수 리스크 큼.
- **nut.js**: 메인테이너가 "오픈소스 포기" 선언(nutjs.dev/blog/i-give-up). **소스는 여전히 오픈이나 npm prebuilt 패키지 배포 중단** → 직접 빌드 or 유료 구독($75/월 Solo). 커뮤니티 포크 `@nut-tree-fork/nut-js`(4.2.6, ~1년 전)로 연명. **의존 시 리스크.**
- **robotjs**: N-API 이전 실패로 최신 Node 지원 정체, 사실상 방치.
- 어느 라이브러리도 **Wayland 를 완전 지원하지 못함** — 이는 라이브러리 문제가 아니라 §3 의 플랫폼 근본 제약.

---

## 5. 화면 인식 · 좌표 · 멀티모니터

| 기능 | 권장 접근 | 세부 |
|------|-----------|------|
| **화면 캡처** | **mss** (Python) / **scrap·xcap**(Rust) | mss 는 순수 ctypes, 네이티브 API 사용: Win=BitBlt, macOS=CoreGraphics, Linux=X11. 멀티모니터 개별/전체 캡처 지원 |
| **픽셀 조회** | 캡처 후 NumPy/이미지버퍼 인덱싱 | 단일 픽셀만 필요해도 영역 캡처가 대개 더 빠름 |
| **이미지 매칭** | **OpenCV `matchTemplate`** | 템플릿을 큰 이미지 위로 슬라이딩하며 매칭. 정확하나 스케일/회전 취약 → 멀티스케일 or 특징점(ORB) 보완 |
| **멀티모니터 좌표** | 가상 데스크톱 전역 좌표계로 통일 | 모니터별 offset·DPI 스케일 정규화 필수. macOS Retina(논리 vs 물리 픽셀) 특히 주의 |
| **macOS 캡처 권한** | **Screen Recording** 권한(TCC) | 입력 주입(Accessibility)과 **별개 권한**. 둘 다 필요 |
| **Wayland 캡처** | XDG **ScreenCast 포털** + PipeWire | X11 스크린샷 방식 차단. 포털+PipeWire 스트림이 표준 |

**핵심:** 화면 캡처 역시 macOS(Screen Recording 권한)·Wayland(ScreenCast 포털) 에서 권한 게이트 존재. 입력 주입과 별도로 승인 흐름 필요.

---

## 6. 외부 HID 디바이스 현실성 평가

| 케이스 | 라이브러리 | 현실성 | 평가 |
|--------|-----------|--------|------|
| **HID 디바이스 읽기**(게임패드·시리얼) | hidapi (Win/Linux/macOS/BSD), gilrs(게임패드) | ✅ 실용적 | hidapi 는 USB/BT HID 크로스플랫폼 읽기 표준. gilrs 는 SDL 매핑 기반 게임패드 |
| **가상 HID 디바이스 생성(주입)** | Linux uinput / Win 은 드라이버 필요 / macOS 매우 제한 | ⚠️ 플랫폼 편차 큼 | Linux 는 uinput 으로 가능(=ydotool 방식). Win/macOS 는 커널 드라이버·서명 필요로 사실상 비현실 |
| **게임에 입력 주입** | DLL injection 등 | ❌ 비권장 | 안티치트 충돌·멀웨어 오탐. CLI 범위 밖 |

**결론:** HID 는 **"읽기(입력 수신)"는 hidapi/gilrs 로 실용적**이나, **"물리 디바이스 시뮬레이션(가상 HID 주입)"은 크로스플랫폼으로 비현실적**(Linux uinput 만 예외). CLI 의 GUI 자동화는 §2 의 OS 입력 API(CGEvent/SendInput/XTest/libei) 로 구현하고, HID 는 별도 선택 기능(주로 읽기)으로 격리 권장. 초기 범위에서 제외해도 무방.

---

## 7. 권한 / 보안 고려 (★입력 주입 = 강력하고 위험)

입력 주입 기능은 **키로거·RAT(원격 조종 트로이목마)와 기술적으로 동일**하다. 정당한 자동화 도구도 오용·악용될 수 있으므로 보안 설계 필수.

| 위협/이슈 | 대응 |
|-----------|------|
| **권한 상승 오용** (Win UIPI 우회, macOS Accessibility 탈취) | 정당 용도 명시. `uiAccess` 매니페스트·서명 남용 금지. 2026-02 Project Zero UIAccess 우회 사례 인지 |
| **무단 입력 주입** | 사용자가 명시적으로 시작한 세션에서만 동작. 백그라운드 상시 주입 금지 |
| **자격증명 탈취 위험** (화면캡처+입력=비밀번호 훔침 가능) | 캡처/입력 로그에 민감정보 저장 금지. 마스킹 |
| **macOS TCC** | Accessibility/Input Monitoring/Screen Recording **3권한 개별 요청**·명확한 사유 고지 |
| **Wayland 보안 모델 존중** | libei/포털(사용자 승인) 우선. uinput(root) 은 "동의된 고급 모드"로만, 기본 비활성 |
| **감사 로그** | 무슨 입력을 언제 주입했는지 audit 가능하게(오남용 추적) |
| **명확한 실패** | 권한 미승인 시 조용히 실패 금지 → "X 권한이 필요합니다: [설정 경로]" 안내 |

**원칙:** 이 기능은 "사용자가 자신의 머신에서 명시적으로 승인한 자동화"로 한정하고, 원격/은닉 조종으로 오해될 동작(백그라운드 상주 주입, 은밀한 권한 획득)을 배제한다.

---

## 8. ★추천 — 이 CLI 의 GUI 자동화·입력 구현 권장 접근

### 8-1. 코어 라이브러리 선택 (언어별)

| CLI 구현 언어 | 1순위 | 근거 |
|--------------|-------|------|
| **Rust** | **enigo 0.6.x** | 유일하게 활발히 유지+MIT/Apache+RustDesk 프로덕션 검증+libei Wayland 시도. ★최우선 권장 |
| Python | pynput(입력)+mss(캡처)+opencv(매칭) 조합 | PyAutoGUI 는 유지보수 중단으로 비권장. 조합으로 구성 |
| Node | ⚠️ 신중 | robotjs 방치·nut.js 유료화. 신규 채택 비권장 |

**전체 권장: Rust + enigo 기반.** 입력 주입 커버리지·유지보수·라이선스·Wayland 대응(libei) 모두에서 2026 기준 최선.

### 8-2. 플랫폼별 백엔드 아키텍처
```
InputBackend (trait/interface)
 ├─ macOS   → CGEvent (Accessibility 권한 프리플라이트 → 미승인 시 안내)
 ├─ Windows → SendInput (DPI-aware, UIPI 한계 문서화)
 ├─ Linux-X11 → XTest
 └─ Linux-Wayland → ① libei+포털 시도 → ② ydotool/uinput 폴백 → ③ 미지원 명시 에러
```
- enigo 사용 시 위 대부분을 라이브러리가 추상화하나, **Wayland 는 feature flag(`libei`)·폴백·권한 안내를 CLI 가 명시적으로 감싸야** 함.

### 8-3. 단계적 도입안 (MVP → 확장)

| 단계 | 범위 | 이유 |
|------|------|------|
| **Phase 1 (MVP)** | Win(SendInput) + macOS(CGEvent) + Linux **X11** 마우스/키보드 주입 | 가장 잘 동작·검증된 3경로. 권한 프리플라이트+안내 포함 |
| **Phase 2** | 화면 캡처(mss/xcap) + OpenCV 이미지 매칭 + 멀티모니터 좌표 정규화 | GUI 요소 찾기. macOS Screen Recording 권한 흐름 추가 |
| **Phase 3** | **Wayland**: libei/포털 우선 + ydotool 폴백 | 최난도. 컴포지터별(GNOME/KDE/wlroots) 대응·명확한 미지원 안내 |
| **Phase 4 (선택)** | HID **읽기**(hidapi/gilrs) | 물리 디바이스 수신. 주입(가상 HID)은 범위 제외 권장 |

### 8-4. 필수 설계 원칙
1. **권한 프리플라이트**: 실행 전 필요 권한 체크 → 미승인 시 정확한 안내(설정 경로 포함). 조용한 실패 금지.
2. **Wayland 를 1급 시민으로 분기**: "Linux = X11" 가정 금지. 세션 타입(`XDG_SESSION_TYPE`) 감지 후 분기.
3. **DPI/멀티모니터 정규화**: 논리 vs 물리 픽셀, 모니터 offset 을 좌표 API 진입점에서 통일.
4. **보안·감사**: 명시적 사용자 승인 세션에서만 동작, 주입 audit 로그, 민감정보 마스킹.
5. **폴백 체인 + 명확한 미지원 에러**: 특히 Wayland. "안 되는데 조용함" 절대 금지.

---

## 9. 참고 링크

**입력 주입 / 플랫폼:**
- Apple Quartz Event Services: https://developer.apple.com/documentation/coregraphics/quartz-event-services
- macOS Input Monitoring/Screen Capture/Accessibility (HackTricks): https://hacktricks.wiki/en/macos-hardening/macos-security-and-privilege-escalation/macos-security-protections/macos-input-monitoring-screen-capture-accessibility.html
- Windows SendInput (MS Learn): https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
- UIPI Issues (MS Learn / Power Automate): https://learn.microsoft.com/en-us/troubleshoot/power-platform/power-automate/desktop-flows/ui-automation/uipi-issues
- Bypassing Administrator Protection via UI Access (Project Zero, 2026-02): https://projectzero.google/2026/02/windows-administrator-protection.html

**Wayland:**
- Input emulation on Wayland via libei + RemoteDesktop portal (rustdesk #4515): https://github.com/rustdesk/rustdesk/discussions/4515
- wdotool (libei + wlroots, not /dev/uinput): https://github.com/cushycush/wdotool
- Exploring the Fragmentation of Wayland (semicomplete): https://www.semicomplete.com/blog/xdotool-and-exploring-wayland-fragmentation/
- ydotool (uinput 기반): https://github.com/ReimuNotMoe/ydotool

**라이브러리:**
- enigo (Rust): https://github.com/enigo-rs/enigo — crates: https://crates.io/crates/enigo/versions
- enigo CHANGES: https://github.com/enigo-rs/enigo/blob/main/CHANGES.md
- PyAutoGUI: https://pypi.org/project/PyAutoGUI/ / Wayland issue #111: https://github.com/asweigart/pyautogui/issues/111
- pynput limitations: https://pynput.readthedocs.io/en/latest/limitations.html
- nut.js "I give up" (라이선스 전환): https://nutjs.dev/blog/i-give-up / pricing: https://nutjs.dev/pricing/pricing
- robotjs: https://www.npmjs.com/package/robotjs

**화면 인식 / HID:**
- mss (스크린 캡처): https://pypi.org/project/mss/
- OpenCV Template Matching: https://docs.opencv.org/4.13.0/d4/dc6/tutorial_py_template_matching.html
- hidapi: https://github.com/libusb/hidapi
- gilrs (게임패드, Rust): https://docs.rs/gilrs/latest/gilrs/

---

## 내부 교차 점검

| 관점 | 점검 결과 |
|------|-----------|
| 👔 기획자 | 요구된 8개 산출물 항목 모두 커버. 범위 내(입력·화면·HID·권한·추천) |
| 💻 개발자 | 플랫폼별 API·백엔드 아키텍처·feature flag·폴백 체인 구현 수준까지 제시 |
| 🧪 테스터 | 버전(enigo 0.6.1/2025-08-28, nut.js 유료화, PyAutoGUI 미유지)·컴포지터 버전(GNOME46/KDE6.1) 실측 확인 |
| 👤 사용자 | 권한 안내·명확한 실패·보안(오용 방지) 사용자 관점 반영 |

**리스크 등급: 상** (Wayland 파편화 = 최대 미해결 변수, nut.js/PyAutoGUI 유지보수 리스크).

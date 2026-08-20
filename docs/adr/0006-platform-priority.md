# 0006. 플랫폼 우선순위 = macOS 먼저 → Linux(X11) → Windows → Wayland

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: R5(GUI 자동화·입력 주입), R4(앱 제어), README §4(미해결 항목)

## Context

kongtrol 은 macOS·Linux·Windows 3개 OS를 지원하는 크로스플랫폼 OS 제어 CLI다. "어디서나 100% 동작하는 단일 방법은 없다"(R5 §1)는 것이 리서치의 핵심 결론이며, 특히 입력 주입·창 제어에서 플랫폼별 편차가 크다. 따라서 3개 플랫폼을 동시에 완성하려 하기보다 **개발·검증 효율이 가장 높은 순서**로 단계적으로 확장해야 한다.

README §4는 두 가지를 미해결 항목으로 남겨두었다.
1. **초기 타겟 플랫폼 우선순위** — 현재 개발 환경은 macOS(darwin). MVP를 macOS 먼저 완성할지, 3종을 처음부터 병행할지.
2. **Wayland 지원 시점** — M5(입력 주입)에서 X11만 먼저 할지, libei까지 한 번에 갈지.

이 ADR이 두 항목을 확정한다.

### 입력 주입 난이도 (R5 §1, 낮을수록 쉬움)

| 난이도 | 플랫폼 | 핵심 장벽 |
|--------|--------|-----------|
| 최이(1) | Linux X11 | XTest 확장으로 비교적 자유 (X11 자체 보안이 약함) |
| 중(2) | Windows | UIPI — 낮은 무결성→높은 무결성 앱 주입 차단 |
| 상(3) | macOS | TCC — Accessibility 등 사용자 승인 팝업 필수 |
| 최난(4) | Linux Wayland | 표준 주입 API 부재, 컴포지터별 파편화 |

기술 난이도만 보면 X11이 가장 쉽지만, **현재 개발 환경이 macOS**라는 실용적 이점이 우선순위를 좌우한다.

## Decision

초기 개발 환경 = **macOS(darwin)**. MVP를 **macOS에서 먼저 완성**한 뒤 **Linux(X11) → Windows → Wayland** 순으로 확장한다.

### 개발/확장 순서

| 순위 | 플랫폼 | 선정 이유 | 완성 시점 |
|------|--------|-----------|-----------|
| 1 | **macOS** | 현재 개발 환경(README §4) — 즉시 반복·검증 가능 | MVP 우선 완성 |
| 2 | **Linux X11** | 입력 주입 최이(R5 §1), XTest로 자유로운 주입 | macOS 다음 |
| 3 | **Windows** | UIPI 무결성 규칙 문서화 필요하나 SendInput 자체는 명확 | X11 다음 |
| 4 | **Linux Wayland** | 최난 — 프로토콜 부재·파편화. M5 후반 또는 후속 | 마지막 |

- macOS를 먼저 두는 이유: 개발자가 macOS에서 작업하므로 코드 수정→실행→검증 루프가 가장 빠르다. 가장 까다로운 TCC 권한 흐름을 초기부터 다뤄두면 이후 플랫폼 권한 모델 설계가 안정된다.
- 그 뒤 가장 쉬운 X11 → Windows 순으로 실기 검증을 넓히고, 최난인 Wayland를 마지막에 둔다.

### Wayland 지원 시점

- **M5(입력 주입) 단계에서 X11을 먼저 완성**하고, Wayland는 그 **이후**(M5 후반 또는 후속)에 착수한다. 근거: R5 §8-3 로드맵이 Phase1(Windows·macOS·X11) → Phase3(Wayland)로 명시.
- Wayland는 **표준 입력 주입/창 제어 프로토콜이 없어**(R4 §3, R5 §3) 컴포지터별(GNOME/KDE/wlroots)로 갈라진다. enigo 조차 Wayland(libei)를 버그 있는 feature flag 뒤에 숨긴다(R5 §4). → X11과 동시에 진행하면 리스크가 폭증하므로 분리한다.

**Wayland 대응 전략 (R5 §3, 폴백 체인)**

| 순서 | 경로 | 권한 | 평가 |
|------|------|------|------|
| ① | libei + xdg-desktop-portal RemoteDesktop 포털 | 포털 다이얼로그 사용자 승인 | 미래 표준·권장 (GNOME≥46, KDE Plasma≥6.1) |
| ② | ydotool (`/dev/uinput`) 폴백 | root 또는 `input` 그룹 + udev | 강력하나 침습적, 데몬 상주, 포커스 무시 |
| ③ | "이 컴포지터는 미지원" 명확한 에러 | — | **조용한 실패 절대 금지** |

**앱 제어(R4)의 Wayland 창 제어도 동일 원칙** — 런타임에 `XDG_SESSION_TYPE`을 감지해 X11/Wayland를 분기한다.

| 세션 | 창 제어 방법 |
|------|-------------|
| X11 | wmctrl / xdotool 풀 기능 |
| Wayland: GNOME | D-Bus 확장 |
| Wayland: KDE | kdotool / KWin script |
| Wayland: wlroots(Sway 등) | wlrctl |

지원되지 않는 조합은 에러가 아닌 `unsupported` 반환(graceful degradation)으로 처리한다. 자세한 아키텍처 계약은 [0002](./0002-architecture-trait-platform-split.md), 단계별 범위는 [0005](./0005-roadmap-milestones.md) 참조.

### README §4 미해결 항목 해소

| README §4 항목 | 이 ADR의 결정 |
|----------------|---------------|
| 초기 타겟 플랫폼 우선순위 | **macOS 먼저** → Linux(X11) → Windows → Wayland |
| Wayland 지원 시점 | **M5에서 X11 먼저**, Wayland는 M5 후반/후속 |

## Consequences

- **긍정**: 개발 환경(macOS)에서 반복 속도가 최대. 가장 어려운 TCC/권한 흐름을 초기에 정립해 이후 플랫폼 설계 기준이 잡힘. Wayland 리스크를 X11에서 격리해 M5의 나머지가 지연되지 않음.
- **부정/비용**: Windows·Linux는 개발 환경 밖이라 실기 또는 CI VM 확보 전까지 검증이 지연됨. Wayland 사용자는 초기 릴리스에서 입력/창 제어 일부를 못 씀 → 문서에 "현재 미지원" 명시 필요.
- **완화**: 각 플랫폼 미지원 기능은 `Err(Unsupported)`로 반환하고 사용자에게 대안(X11 세션 등)을 안내한다([0002]).

## Alternatives

| 대안 | 내용 | 탈락 이유 |
|------|------|-----------|
| 3플랫폼 처음부터 병행 | macOS·Linux·Windows 동시 개발 | 개발 환경(macOS) 반복 속도 이점 상실, 초기 검증 지연, 미완성 플랫폼 다수 |
| Linux X11을 먼저 | 입력 주입이 가장 쉬우니(R5 §1) X11부터 | 개발 환경이 macOS라 즉시 검증 이점이 더 큼 |
| Wayland를 X11과 동시 | M5에서 X11+Wayland 한 번에 | 파편화·프로토콜 부재로 리스크 폭증, enigo도 feature flag로 숨김 |

## Open questions

- Windows·Linux 실기 테스트 환경 확보 방안 (CI VM vs 실기 vs 클라우드 러너).
- Wayland 컴포지터 지원 범위·우선순위 (GNOME / KDE / wlroots 중 어디를 먼저).
- 각 플랫폼의 "완성 판정 기준"(DoD) 정의 — 어떤 명령까지 통과해야 해당 플랫폼을 완료로 볼지([0005]와 연동).

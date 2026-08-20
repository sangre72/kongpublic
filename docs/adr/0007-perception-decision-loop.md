# 0007. perception-decision-loop (화면 인식·판단 폐루프)

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: [GAME-LITMUS](./GAME-LITMUS.md)(§2 화면인식·§3 판단·§4 타이밍·§6 신규ADR), R5 §5
- 관련 ADR: [0002](./0002-architecture-trait-platform-split.md)(trait 구조)·[0004](./0004-security-model.md)(보안)·[0005](./0005-roadmap-milestones.md)(로드맵)

## Context

기존 ADR 6종은 [마우스·키보드 입력 주입]만 다룬다([0004](./0004-security-model.md) input). 그러나 게임 플레이 리트머스(유저 검증 기준: 지뢰찾기·테트리스 실제 플레이)가 드러냈듯, "게임을 플레이"하려면 **[화면 읽고 → 상태 파악 → 룰 기반 판단 → 액션]** 폐루프가 필수다. 입력만으론 "눈 감고 클릭"에 불과.

[GAME-LITMUS](./GAME-LITMUS.md) 갭 분석: [화면 인식]은 리서치 R5 §5에만 있고 ADR로 미승격, [판단·폐루프] 축은 문서 전체에 부재 = 문서 최대 빈틈. 이 ADR이 그 축을 정식 아키텍처 결정으로 승격한다.

## Decision

### 1. core trait 2종 신설 ([0002](./0002-architecture-trait-platform-split.md) trait 5종에 추가 → 총 7종)

| trait | 책임 | 구현(M7) |
|-------|------|----------|
| **`ScreenSensor`** | 화면 캡처 + 상태 추출 | xcap(캡처) + 좌표격자·픽셀색(추출) |
| **`DecisionEngine`** | 게임/작업별 룰·휴리스틱 판단 | 게임별 플러그인(core는 인터페이스만) |

```rust
// core/screen.rs — 화면 인식(캡처+상태추출)
pub trait ScreenSensor {
    fn capture(&self, region: Option<Region>) -> Result<Frame>;      // xcap
    fn extract_state<S>(&self, frame: &Frame, grid: &GridSpec) -> Result<S>; // 좌표격자+픽셀색
}

// core/decision.rs — 판단(게임별 플러그인이 impl)
pub trait DecisionEngine {
    type State;   // 게임 상태(지뢰찾기 격자 / 테트리스 보드)
    type Action;  // 다음 액션(클릭 좌표 / 키 시퀀스)
    fn decide(&self, state: &Self::State) -> Result<Self::Action>;
}
```

- `DecisionEngine` 은 게임별 플러그인으로 분리: `minesweeper`(기초룰+CSP+확률), `tetris`(4-feature 휴리스틱). core 는 인터페이스만.

### 2. 폐루프 아키텍처

```
loop {
    frame  = ScreenSensor::capture(region)          // 캡처
    state  = ScreenSensor::extract_state(frame, grid) // 상태 추출(격자+픽셀색)
    action = DecisionEngine::decide(state)          // 판단(룰/휴리스틱)
    InputInjector::act(action)                       // 액션(0004 게이트 경유)
    // rate 제한 · 사이클 예산 준수
}
```

- **사이클 예산**([GAME-LITMUS](./GAME-LITMUS.md) §4): 그리드 튜닝 **~30ms** / 오프더셀프 나이브 **50–100ms**. OCR 매프레임 금지(수백ms~초).
- rate 제한: 입력주입 대량 반복 오남용 방지([0004](./0004-security-model.md) rate/scope) — 폐루프에도 반복 상한.

### 3. 판단 방식 = 룰봇/휴리스틱 (ML 배제)

[GAME-LITMUS](./GAME-LITMUS.md) §3 근거:
- **지뢰찾기**: 기초 제약룰 + CSP(집합차감/연결요소) + 확률 추측. Beginner/Intermediate ~100%, Expert ~70% 무추측(**~30%는 본질적 추측 불가피**).
- **테트리스**: 4-feature 휴리스틱(Aggregate Height −0.51/Complete Lines +0.76/Holes −0.36/Bumpiness −0.18) + 1-lookahead. 경량·실시간.
- **ML 배제**: 학습 파이프라인·GPU 부담·비결정·설명불가 + ★테트리스는 RL(DQN/PPO)이 휴리스틱보다 점수·효율 열세(2025 비교연구). CLI 실시간 도구엔 오버킬.

### 4. 크레이트

| 용도 | 채택 | 비채택(근거) |
|------|------|--------------|
| 화면 캡처 | **xcap 0.9.8**(크로스플랫폼 유일, 활발) | screenshots(xcap로 통합·deprecated)·scrap(방치) |
| 픽셀 처리 | **image** | — |
| 상태 추출 | 좌표격자+픽셀색(산술+색 샘플링) | **OCR(ocrs/leptess)=과잉·느림**·**OpenCV=시스템 의존성 무거움** |

## Consequences

### 긍정
- 게임 리트머스(지뢰찾기·테트리스) 검증 가능해짐 — 폐루프가 [상태 인식→판단] 축을 채움.
- ScreenSensor·DecisionEngine 이 core trait 로 편입 → 게임 외 자동화(UI 상태 기반 작업)에도 재사용.
- 판단을 게임별 플러그인으로 분리 → core 무변경으로 새 게임/작업 추가.

### 부정/비용
- macOS 캡처 = **TCC "화면 기록" 권한**(입력의 Accessibility와 **별개**). 미승인 시 xcap이 검은/빈 화면 반환(조용한 실패) → 감지 로직 필요.
- 실시간 고 gravity 테트리스(≥1G)는 캡처+인식 오버헤드로 한계([GAME-LITMUS](./GAME-LITMUS.md) §4).
- 화면 캡처 = 민감정보(비밀번호 등) 노출 가능 → 로그 마스킹 필요.

### 보안·권한 ([0004](./0004-security-model.md) 연계)
- 화면 캡처 로그에 민감정보 저장 금지·마스킹.
- macOS Screen Recording TCC 미승인 = 조용한 실패 감지 → "화면 기록 권한 필요: [설정 경로]" 안내(exit 3).
- ★**범위 경계**: [브라우저 게임·사용자 자기 머신·명시 승인 세션] 한정. **안티치트 우회·네이티브 게임 봇 금지**(합성입력은 브라우저 게임만 수용, 네이티브 Raw Input/안티치트는 차단 — [GAME-LITMUS](./GAME-LITMUS.md) §4). [0004](./0004-security-model.md) 공격도구화 방지 정신 계승.

### 마일스톤 편입 ([0005](./0005-roadmap-milestones.md))
- **M7 (perception loop)**: M5(입력주입) 이후 별도 트랙. ScreenSensor+DecisionEngine+폐루프. 게임 리트머스는 M7 후 검증.
- 착수 순서(GAME-LITMUS §7 PoC): PoC-1 브라우저 지뢰찾기(정적·무압박) → PoC-3 브라우저 테트리스(저레벨).

## Alternatives

| 후보 | 탈락 이유 |
|------|-----------|
| **OCR(ocrs/leptess)로 상태 추출** | 셀당 OCR = 속도·복잡도·의존성 대비 비효율. 그리드 컬러 인식이 Tesseract 대비 50–200배 빠름([GAME-LITMUS](./GAME-LITMUS.md) §4). 지뢰찾기 숫자도 색 판별로 대체 |
| **OpenCV 템플릿 매칭 전면 채택** | 시스템 OpenCV 설치 필수(libclang 헤더 파싱, 빌드·배포 부담 큼). 크로스플랫폼 단일 바이너리([0001](./0001-language-rust.md))와 상충. 좌표격자+픽셀색으로 대부분 대체, 보조로만 |
| **ML(강화학습) 판단** | 학습 파이프라인·GPU·비결정·설명불가. 테트리스는 성능조차 휴리스틱에 열세. CLI 도구엔 오버킬 |
| **폐루프 없이 입력만(현행 6종)** | "눈 감고 클릭" — 게임 리트머스 통과 불가. 이 ADR의 존재 이유 |
| 에뮬레이터 메모리 직접 읽기(StackRabbit 방식) | 특정 에뮬 종속·범용성 없음. kongtrol은 실제 화면 플레이가 목표(범용 OS 제어 도구) |

## Open questions

- 실시간 고 gravity 테트리스(≥1G·킬스크린) 한계 — M7 범위에서 저~중 레벨만 목표할지, 예측(look-ahead) 기법으로 확장할지.
- Wayland 캡처 = xcap 제한적(ScreenCast 포털+PipeWire 필요). 컴포지터별(GNOME/KDE/wlroots) 차이([0006](./0006-platform-priority.md) 연계) — M7에서 X11 우선.
- xcap 미승인 TCC 시 Rust `Err` 반환 여부 vs 검은 화면 — kongtrol 실측 필요([FEASIBILITY](./FEASIBILITY.md) 미확인 항목).
- `extract_state` 제네릭 시그니처 확정(게임별 State 타입 바인딩) — M7 구현 시.
- DecisionEngine 플러그인 등록 방식(정적 dispatch vs dyn).

# 비전 GUI 에이전트 벽돌파 리서치 (a_20, u_35/36)

> 목표: kongtrol 좌표 정밀도 벽을 넘을 **[정밀도 + 속도 동시]** 최선안.
> 현 baseline: Claude 스샷 폐루프 (정밀 △ 수동환산 · 느림 스샷왕복 2~5s/step).
> 리서치: WebSearch (2025~2026), 벤치·출처 기반.

## 1. UI grounding 모델 (스샷 → 픽셀좌표) 비교

| 모델 | 방식 | ScreenSpot-V2 | ScreenSpot-Pro(고해상도) | 로컬(Apple Silicon) | 라이선스 |
|---|---|---|---|---|---|
| **UI-TARS-1.5-7B** (ByteDance) | 순수비전 end-to-end (x,y) | **91.6%** | **61.6%** (SOTA) | ✅ Ollama 4GB(Q4) | Apache-2.0 |
| UI-TARS-72B | 동일 대형 | — | 38.1% | △ 무거움 | Apache-2.0 |
| OS-Atlas-7B | bbox 중심점 | — | 18.9% | ✅ HF | 오픈 |
| UGround-7B | 비전 grounding | — | 16.5% | ✅ HF | 오픈 |
| AriaUI | 비전 | — | 11.3% | ✅ HF | 오픈 |
| **OmniParser V2** (MS) | YOLOv8 아이콘검출+Florence-2 캡션 → set-of-marks(LLM 미포함·파서) | — | 39.6 avg | ✅ HF(macOS 가이드), 0.6~0.8s/frame(강GPU) | MIT |

- 방식: 대부분 (x,y) 픽셀좌표 또는 bbox 중심점 출력. 정확=좌표가 정답 bbox 안.
- ★고해상도(ScreenSpot-Pro)는 전반 낮음 → 실사용은 일반 해상도(V2)가 관건. UI-TARS-1.5-7B가 V2 91.6%로 압도.

## 2. computer-use 에이전트 (아키텍처·좌표방식)

| 에이전트 | 좌표 방식 | 판단/좌표 분리 | ScreenSpot-Pro | 로컬 | 라이선스 |
|---|---|---|---|---|---|
| **UI-TARS-1.5-7B** | 순수비전 스샷→직접(x,y) | 통합(1모델) | **61.6%** | ✅ Ollama | Apache-2.0 |
| Anthropic Computer Use (Claude) | 클라우드 비전→좌표 | 통합 | 27.7% | ✗ 클라우드 | 상용 |
| OpenAI Operator/CUA | 클라우드 비전 | 통합 | 23.4% | ✗ | 상용 |
| **Agent-S2** (simular) | ★Compositional: generalist(계획)+specialist grounding(좌표) Mixture-of-Grounding | ★★분리 | OSWorld 34.5% SOTA급 | △ grounding 로컬 | 오픈(2504.00906) |
| **OmniParser V2** | 파서=좌표(set-of-marks), LLM=판단 | ★★분리 | 39.6 | ✅ MIT | MIT |
| macos-use/Tactile | a11y tree(AXUIElement)+스샷보조 | 분리 | 구조기반 | ✅ Swift MCP | 오픈 |

## 3. 속도 기법 (★현 병목=스샷왕복 2~5s/step, 10스텝=20~50s)

| 기법 | 이득 | 비고 |
|---|---|---|
| **★a11y tree (macOS AXUIElement)** | 요소 좌표 **<100ms**(로컬·픽셀 클라우드 전송 0) | 모든 앱 UI 계층 구조 노출. **단** 커스텀렌더(캔버스·차트·이미지)는 못 봄→비전 폴백 |
| **★하이브리드(a11y+비전)** | a11y로 빠르게 식별+비전으로 시각보완 = 속도+이해 동시 | 가장 유력 |
| set-of-marks(SoM) | 요소 번호 마킹→LLM은 "번호" 선택(픽셀추측 제거)→정밀↑ | OmniParser 방식 |
| 로컬 grounding+원격 판단 분리 | planning이 지연 50~75% 차지→grounding 로컬화로 좌표지연 제거 | Agent-S2 패턴 |

- ★주의(OSWorld-Human): 현 CUA는 극단 지연(사람 수분→12분), planning 호출이 지연 지배.

## 4. ★★추천 (정밀도+속도 동시 · kongtrol=Rust 눈+손 + Claude 판단)

### 추천 1 (기본): a11y tree(AXUIElement) 1차 grounding + Claude 판단 + 비전 보조
- **근거**: a11y가 **<100ms** 좌표 제공 → 현 2~5초 스샷루프 벽 [직접 해결]. macOS AXUIElement가 Keynote 등 네이티브앱 요소를 구조로 노출(role·title·pixel-bbox). Claude는 "무엇을 클릭"만 판단(a11y 요약 or 스샷 보고), 좌표는 a11y에서 즉시.
- **연동**: kongtrol(Rust)에 AXUIElement 조회 추가 → 요소 목록 획득 → Claude 선택 → kongtrol 물리클릭. 커스텀 UI만 비전 폴백.
- **설치**: 추가 모델 불필요(시스템 권한만·이미 승인). **가장 가볍고 빠름**.

### 추천 2 (폴백): 로컬 UI-TARS-1.5-7B (Ollama) = 좌표 전문가 + Claude = 판단
- **근거**: ScreenSpot-Pro 61.6%(Claude 27.7%의 2배+), V2 91.6%. 순수비전이라 a11y 못 잡는 커스텀 UI(캔버스·차트·도형·이미지) 커버. Apple Silicon Ollama 로컬(4GB·15~45 tok/s).
- **연동**: kongtrol 스샷→Ollama UI-TARS(localhost:11434)에 "요소X 좌표?"→(x,y) 반환→Claude 판단 결합. Agent-S2식 [Claude 계획 + UI-TARS grounding] 분리.
- **설치**: `ollama pull 0000/ui-tars-1.5-7b` (7B Q4 ~4GB).

### ★최선 = 하이브리드 (추천1 + 추천2 폴백)
- **a11y 기본(초고속 <100ms)** → a11y가 못 보는 요소(캔버스·커스텀렌더)만 **UI-TARS 로컬 비전 grounding 폴백**.
- = [정밀도(a11y 정확+UI-TARS 61.6%) + 속도(a11y <100ms)] 동시 충족. Keynote 텍스트박스·버튼=a11y, 도형/이미지 캔버스=UI-TARS.

## 5. PoC 다음 스텝
1. **a11y**: kongtrol에 AXUIElement 요소 덤프 서브명령 추가 (`kongtrol see --a11y` → 요소 role/title/pixel-bbox JSON). Rust `core-foundation`+`accessibility-sys` crate 또는 Swift helper FFI.
2. **UI-TARS 폴백**: `ollama pull 0000/ui-tars-1.5-7b` → localhost:11434 좌표 질의 래퍼(kongtrol 스샷 전송→(x,y)).
3. **벤치**: 두 방식 스텝당 지연·정밀도 실측(Keynote 버튼/텍스트박스 대상). a11y vs 비전 vs 하이브리드 비교.

## 출처
- UI-TARS: arXiv 2501.12326 · seed.bytedance.com UI-TARS-1.5 blog · ollama.com/0000/ui-tars-1.5-7b
- OmniParser V2: microsoft.com research · huggingface.co/microsoft/OmniParser-v2.0
- ScreenSpot-Pro: arxiv 2504.07981
- OS-Atlas: arXiv 2410.23218 · Agent-S2: arXiv 2504.00906
- a11y/macos-use: macos-use.dev · OSWorld-Human: arXiv 2506.16042

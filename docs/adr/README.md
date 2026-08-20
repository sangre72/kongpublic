# ADR — kongtrol 아키텍처 결정 기록

> **kongtrol** = 크로스플랫폼(macOS · Linux · Windows) OS 객체(프로세스 · 서비스 · 스케줄러 · 앱 · 입력) 조회 · 제어 CLI.
> 바이너리/커맨드명 = `kongtrol`. (리서치 단계 임시명 `osctl` → **kongtrol** 로 통일.)
>
> 이 디렉터리는 **구현 착수 전 확정용 ADR(Architecture Decision Record) 세트**다. 형식 = MADR(Status/Context/Decision/Consequences/Alternatives).
> 근거 = [리서치 6문서](../research/) (R1~R6 + README) 의 실측 결론. 코드는 아직 없으며, 구현은 다음 지시(별도 a_)에서 M0(골격)부터 시작한다.

---

## ADR 인덱스

| # | 제목 | Status | 한 줄 결정 |
|---|------|--------|-----------|
| [0001](./0001-language-rust.md) | 언어 = Rust | Accepted (2026-08-13) | Rust(1순위) + clap v4. Plan B=Go. 단일 정적 바이너리 · RustDesk/enigo 프로덕션 검증 · 메모리 안전 · 코어 크레이트 재사용. Python/Node 탈락. |
| [0002](./0002-architecture-trait-platform-split.md) | 아키텍처 = core trait + platform 분리 | Accepted (2026-08-13) | `core/` 도메인 trait 6종 + `platform/{macos,linux,windows}` cfg-gated 구현 분리(의존성 역전). 미지원 = `KongtrolError::Unsupported` → exit 5(조용한 실패 금지). |
| [0003](./0003-cli-surface.md) | CLI 표면 | Accepted (2026-08-13) | clap v4 명령 트리(`kongtrol <domain> <verb>`) + READ/MUTATE/DANGEROUS 위험등급 태깅 + 테이블/JSON 이중출력 + exit code 규약(0/2/3/4/5) + directories 기반 설정경로. |
| [0004](./0004-security-model.md) | 보안 · 권한 모델 ★최상위축 | Accepted (2026-08-13) | 4중 방어(확인 · --yes · --dry-run · audit) + 최소권한/OS 표준 승격 위임 + TCC/권한우회 금지 + allowlist 우선 + 입력=이벤트API 직접전달. 공격도구화 방지 5원칙. |
| [0005](./0005-roadmap-milestones.md) | 로드맵 · 마일스톤 | Accepted (2026-08-13) | 위험도 오름차순 M0 골격 → M1 조회MVP → M2 프로세스 → M3 서비스 → M4 스케줄러 → **M5 입력주입(최고위험 마지막)** → M6 확장(web/telegram). |
| [0006](./0006-platform-priority.md) | 플랫폼 우선순위 | Accepted (2026-08-13) | macOS(개발환경) 먼저 → Linux(X11) → Windows → Wayland. Wayland는 M5에서 X11 먼저 완성 후(libei/포털 → ydotool 폴백 → 명확한 미지원 에러). |
| [0007](./0007-perception-decision-loop.md) | 화면인식·판단 폐루프 | Accepted (2026-08-13) | core trait 2종 신설(ScreenSensor·DecisionEngine) + 폐루프(capture→extract→decide→act). 판단=룰봇/휴리스틱(ML 배제). 캡처=xcap(OCR/OpenCV 비채택). 게임 리트머스용 M7, 브라우저 게임 한정. |

---

## 핵심 축 요약

- **언어(0001)**: Rust + clap v4. 이 도메인이 이미 Rust로 프로덕션 검증됨(RustDesk v1.4.6 원격제어가 enigo로 입력주입). 단일 정적 바이너리 = 설치 편의.
- **구조(0002)**: R1~R5가 각각 하나의 `core` trait 슬롯에 "어떤 라이브러리/API로 구현하나"만 채운다. CLI 핸들러는 trait만 알고 OS 구현을 모른다. 추후 `adapters/`(axum·teloxide)로 웹·텔레그램 확장.
- **보안(0004) = 최상위 설계축**: 이 도구는 그 자체로 공격도구화 가능(입력주입·kill·서비스제어 = 키로거·RAT와 기술적으로 동일). **강력한 기능일수록 마찰(friction)을 의도적으로 넣는다.** DANGEROUS 명령엔 4중 방어. OS 정상 승인 경로만(TCC/권한 우회 금지 — CVE-2025-43530 등).
- **단계(0005·0006)**: 위험도 오름차순으로 얹고(입력주입 마지막), 플랫폼은 개발환경(macOS)부터 확장. Wayland는 파편화·프로토콜 부재로 최난도 → 마지막.

---

## 리서치 미해결항목(research/README §4) → ADR 해소 매핑

| 미해결항목 | 해소 ADR | 결정 |
|-----------|---------|------|
| 앱 이름/코드네임(임시 osctl) | (본 세트 전체) | **kongtrol** 로 확정 |
| 초기 타겟 플랫폼 우선순위 | [0006](./0006-platform-priority.md) | macOS 먼저 → Linux(X11) → Windows → Wayland |
| Wayland 지원 시점 | [0006](./0006-platform-priority.md) | M5에서 X11 먼저, Wayland는 그 이후(libei/포털) |
| allowlist 정책 기본값 | [0004](./0004-security-model.md) | allowlist 우선, 미설정 시 대화형 확인 대체(기본값 세부는 Open questions) |
| 저장소 분리 여부 | — | 각 ADR Open questions 로 잔류(구현 지시 시 확정) |

> 남은 오픈이슈는 각 ADR 하단 **Open questions** 참조.

---

## 다음 단계

진행: 리서치 → **ADR 확정** → [FEASIBILITY](./FEASIBILITY.md)(구현가능성·blocker 0) → [GAME-LITMUS](./GAME-LITMUS.md)(게임 리트머스) → **M0 골격 완료**(kongtrol/ 실코드) → **ADR 0007**(perception loop) 완료.
다음 = **③ 지뢰찾기 PoC**(브라우저, [GAME-LITMUS](./GAME-LITMUS.md) §7 PoC-1). 단 PoC는 M1(조회 MVP)과 무관하게 착수 가능(폐루프는 M7 트랙, [0005](./0005-roadmap-milestones.md) 참조).

> 부속 문서: [FEASIBILITY.md](./FEASIBILITY.md)(크레이트 실측·PoC), [GAME-LITMUS.md](./GAME-LITMUS.md)(게임 플레이 기준 검증).

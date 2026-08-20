# kongtrol 갭 분석 + 일반 앱 온보딩 구상안 (u_517, 2026-08-16)

> 근거: 이 세션(u_439~517)에서 실제로 겪은 문제 + AppAgent(Tencent)·Voyager(arXiv 2305.16291) 논문 메커니즘.

## 1. 현재 구조 요약

- **kongtrol**(Rust): trait 5종(`SystemInfo/ProcessManager/ServiceManager/Scheduler/InputInjector`) + `perception/`(a11y 덤프, enigo+CGEvent 액션, sensor/locator/runner).
- **orchestrator**(Python): `orchestrator.py`+`protocol_store.py` — u_/a_/ar_ 자연어 텍스트 파일을 정규식(`read_field`, `normalize_status`)으로 파싱. 스키마 없음.
- **kaymaps/keynote/**: RECIPE_*.txt 7개 + a_/seq 노트 다수, 순수 파일명 나열식. 총 1054줄, 인덱스·검색 구조 없음.
- 워커(kongewalker)는 별도 세션에서 스크린샷+a11y로 판단 후 orch에 ar_ 텍스트로 보고.

## 2. 부족한 부분 목록 (실제 사례 기반)

### 2-1. 속도/효율
- **매 스텝 스샷→분석 반복**(u_504): K8 원칙("계획 먼저, 판단 반복 금지")이 문서화돼 있음에도 실행 중 계속 재발 — 원칙이 코드로 강제되지 않고 지시서(a_)에만 의존.
- **Speculative multi-action 부재**: AppAgent/논문들이 "관찰 1회→액션 N개"를 정식 메커니즘으로 갖는 반면, kongtrol은 이걸 "K8 원칙"이라는 사람이 매번 되새겨야 하는 규범으로만 갖고 있음. 코드 레벨 배치 실행기가 없음.

### 2-2. 시스템 경계의 한계
- **CGEvent 합성 클릭이 OS 보호 UI에 안 먹힘**(ar_482): `perception/actor.rs`의 `click_at`은 HID 레벨 CGEvent를 posting하지만, loginwindow가 띄우는 "응용 프로그램 강제 종료" 창은 반응 없음(5회 시도 실패). pure-IO 원칙(System Events/osascript 금지, `pure-io-no-system-events` 메모리)의 구조적 한계 — 시스템 레벨 대화상자는 애초에 자동화 대상 밖일 가능성.
- **대응**: 이런 창은 애초에 뜨지 않게 하는 예방(메모리 여유 확보)이 최선이고, 발생 시 사람 개입을 전제로 한 명시적 fallback 경로가 필요.

### 2-3. 지식 관리(레시피)
- **RECIPE 파일이 순수 텍스트 나열**: `kaymaps/keynote/`에 7개 RECIPE + 수십 개 노트 파일. 검색은 사람이 `ls`/`grep`으로 직접. Voyager의 "임베딩 벡터로 스킬 검색"에 해당하는 인프라 전무.
- **레시피 등재에 검증 단계 없음**: 1회 성공하면 곧바로 RECIPE로 기록(`tool-recipe-learning` 메모리). Voyager는 self-verification 통과해야 라이브러리 등재 — kongtrol은 이 게이트가 없어 잘못된 레시피가 그대로 남을 위험(실제로 a_476→a_477→a_479로 3번 정정된 "강제종료 대응" 사례).
- **레시피가 앱별로 완전히 분리**: Keynote 전용 좌표·절차가 다른 앱에 전혀 재사용 안 됨. 앱 공통 패턴(파일 열기, 종료, 도형 생성 등)을 추상화한 상위 레이어가 없음.

### 2-4. 프로토콜 신뢰성
- **자연어 한글 지시가 파싱 신뢰성 낮음**: u_487("붉은색 프로세스를 선택하고 재계를 진행")를 "강제종료"로, 이후 다시 "아무것도 안 함"으로 두 번 오독(telegram-korean-typo-misread-caution 메모리). 프로토콜이 자유서식 한글 텍스트라 구조화 파싱이 불가능하고, 오독 시 되돌리기 어려운 조치(강제종료 지시)로 번질 위험이 실제로 있었음.
- **heartbeat 폴링 간격 vs 실제 진행 혼동**(worker-heartbeat-polling-interval): ScheduleWakeup 4분 간격이 "정체"로 오인됨. 구조화된 진행률(%, 남은 단계 수) 필드가 없어 텍스트 서술에만 의존.

### 2-5. 결정론화 미흡(최근에야 도입)
- 색상 지정: 처음엔 육안 슬라이더 조정 → 나중에야 Hex 직접입력으로 결정론화(a_485).
- 좌표 배치: 처음엔 "대충 그리고 나중에 옮김" → 나중에야 "생성 즉시 정위치"(a_486).
- 두 원칙 모두 사람이 반복 지적한 뒤에야 반영됨 — 새 앱을 처음 만날 때 이런 시행착오가 매번 반복될 구조.

### 2-6. 세션/컨텍스트 관리
- 워커 세션은 auto-compact 미적용(worker-session-no-autocompact 메모리) — 장시간 작업 시 컨텍스트 누적으로 품질 저하, 사람이 수동 재시작해야 함.

## 3. 일반적인 앱 온보딩 패턴 구상안

AppAgent의 탐색(exploration)/배포(deployment) 2단계 + Voyager의 스킬 라이브러리를 kongtrol에 맞게 구체화.

### 3-1. 단계별 워크플로우

**Phase 0 — 앱 식별**
- 대상 앱 pid/이름 확정 → `kaymaps/<app>/` 디렉토리 존재 여부로 "이미 배운 앱"인지 판별(AppAgent의 문서 베이스 감지에 대응).
- 없으면 Phase 1(탐색)로, 있으면 Phase 2(배포)로 직행.

**Phase 1 — 탐색(새 앱 최초 접촉 시 1회)**
1. a11y 덤프로 최상위 UI 구조(메뉴바·주요 버튼·캔버스 영역) 확인.
2. 공통 동작(파일 열기/저장/종료, 전체화면 토글, 실행 취소) 각각 1회 수행 → 성공하면 RECIPE로 즉시 기록, 실패하면 "이 앱은 이 동작 자동화 불가"로 명시 기록(빈 자리로 남기지 않음).
3. **self-verification 게이트 추가**(Voyager 방식 도입): 레시피는 "1회 성공 = 즉시 등재"가 아니라 "같은 절차 2회 연속 재현 성공" 후에만 등재. 이렇게 하면 a_476→479 같은 3연속 정정 낭비를 줄임.

**Phase 2 — 배포(레시피 존재 시 매번)**
1. `kaymaps/<app>/RECIPE_index.md`(신규, 아래 3-2) 를 먼저 읽어 필요한 레시피만 로드.
2. K8 원칙을 코드 레벨로 강제: 좌표가 결정론적(numeric/Hex)인 경우 스샷 확인 없이 배치 실행, 시각 판단이 꼭 필요한 지점에서만 1회 스샷.
3. 레시피에 없는 새 동작을 만나면 Phase 1처럼 임시 탐색 후, 검증 통과 시 레시피 추가(지속적 성장 — Voyager의 "ever-growing skill library").

### 3-2. 스킬 라이브러리 저장/검색 방식 제안

- **저장 구조**: `kaymaps/<app>/recipes/<verb>_<object>.md`(현재 파일명 규칙 유지) + `kaymaps/<app>/RECIPE_index.json`을 신규 추가.
  ```json
  {"name": "force_quit_dialog", "app": "system", "desc": "강제종료 대화상자 대응: 일시정지 앱 선택→재개클릭→닫기", "verified_runs": 2, "file": "RECIPE_force_quit_dialog.txt"}
  ```
- **검색**: 당장 벡터DB 도입은 과함(레시피 수 적음) — `desc` 필드 키워드 매칭으로 시작하고, 레시피 수가 많아지면(수십 개↑) 임베딩 유사도 검색으로 전환. Voyager 방식 그대로 "설명 임베딩→키, 절차→값" 구조로 확장 가능하게 index.json을 설계해둠.
- **공통 vs 앱전용 분리**: `kaymaps/_common/`에 앱 무관 패턴(강제종료 대화상자, 전체화면 토글 관례 등)을 두고, `kaymaps/<app>/`은 그 앱 고유 좌표만. 지금은 `RECIPE_force_quit_dialog.txt`가 keynote/ 안에 있어 다른 앱에서 재사용하려면 사람이 직접 찾아야 함.

### 3-3. 프로토콜 신뢰성 개선 제안

- u_ 메시지에 "종료/삭제/강제" 등 비가역 키워드가 포함되면, orch가 즉시 실행 지시를 내리기 전에 1줄 요약으로 되묻는 걸 표준 절차화(현재는 사람 판단에만 의존).
- ar_ 상태 필드에 구조화 진행률(`[PROGRESS] 3/4`) 추가해 heartbeat 간격과 무관하게 진행 상황 파악 가능하게.

## 4. 참고자료

- AppAgent (Tencent): [GitHub](https://github.com/TencentQQGYLab/AppAgent) — exploration/deployment 2단계, self-generated documentation, deployment 시 문서 베이스 자동 감지("없으면 성공률 미보장").
- AppAgent v2: [arXiv HTML](https://arxiv.org/html/2408.11824v1) — RAG 기반 지식베이스 검색/갱신.
- Voyager (arXiv 2305.16291): [arXiv](https://arxiv.org/html/2305.16291) — 자동 커리큘럼 + 성장형 스킬 라이브러리(임베딩 검색) + 반복 프롬프팅(환경피드백+실행오류+self-verification).

# 0004. 보안·권한 모델 (★최상위 설계축)

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: R6 §4, R5 §7, R1~R4 권한 절
- ★이 ADR = 프로젝트 done 조건. 공격도구화 방지 원칙 명문화.

## Context

kongtrol 은 OS 상의 프로세스·서비스·스케줄러·앱·입력을 **풀 제어**하는 CLI 다.
문제는 이 기능 집합이 **그 자체로 공격도구화 가능**하다는 점이다. 특히 입력 주입
(`input *`)은 기술적으로 **키로거·RAT(원격 조종 트로이목마)와 동일**하며(R5 §1·§7),
프로세스 kill·서비스 stop·스케줄 remove 역시 시스템을 마비시킬 수 있다.

따라서 보안은 부가 기능이 아니라 **kongtrol 의 최상위 설계축이자 done 조건**이다.
`.claude/rules/security-guideline.md` 정신에 따라, 아래 핵심 원칙을 전 도메인에
일관 적용한다: **강력한 기능일수록 마찰(friction)을 의도적으로 넣는다.**

이 ADR 은 [0003 CLI 표면](./0003-cli-surface.md)이 정의한 위험 등급
(READ / MUTATE / DANGEROUS) 태깅을 전제로, DANGEROUS 명령에 걸리는 방어 계층과
플랫폼 권한 모델·공격도구화 방지 원칙을 확정한다. 로드맵상 실제 적용 순서는
[0005 로드맵](./0005-roadmap-milestones.md)을 따른다(M2 에서 4중 방어 첫 실전,
M5 입력 주입은 최고위험이라 마지막).

## Decision

### 원칙: 강력한 기능일수록 마찰(friction)을 의도적으로 넣는다

편의성과 안전성이 충돌하면 **안전성을 택한다**. 파괴적 명령은 "무심코 실행"이
불가능하도록 설계한다. 이 원칙이 아래 모든 세부 결정의 뿌리다.

### 4중 방어 (DANGEROUS 명령)

DANGEROUS 등급(`input *`, `process kill/killall`, `service stop/disable`,
`schedule remove`) 실행 시 아래 4층을 **모두** 통과해야 한다(R6 §4-2).

| 층 | 방어 | 세부 |
|----|------|------|
| ① | **확인 프롬프트** | 대화형이면 대상·영향 요약 후 `y/N`. **파괴적 기본값 = No**. |
| ② | **`--yes` 명시** | 비대화(스크립트·파이프)에선 `--yes` 없으면 거부(**exit 2**). "무심코 실행" 차단. |
| ③ | **`--dry-run`** | 실제 실행 없이 **동일 결정 로직**으로 "무엇을 할지"만 출력. 의도와 실행 분리. |
| ④ | **audit log** | 모든 DANGEROUS 명령 = **append-only 감사 로그**(who/when/cmd/args/결과/승격여부). `--yes` 여부 무관 **항상** 기록. |

- ①②는 **입력 게이트**(실행 전 동의 확보), ③은 **미리보기**, ④는 **사후 추적**이다.
- `--dry-run` 과 실제 실행은 **같은 결정 코드 경로**를 타야 한다(미리보기와 실제 동작
  불일치 = 신뢰 붕괴).

### 최소권한 · OS 표준 승격 위임

- **비승격 기본 실행**(R6 §4-1). kongtrol 은 root/Admin 으로 상시 실행되지 않는다.
- 승격이 필요한 명령(타 유저 프로세스 kill, 시스템 서비스 제어, 시스템 스케줄 등록)은
  실행 전 **"이 명령은 관리자 권한이 필요합니다"**를 고지하고, **OS 표준 승격 경로
  (sudo / UAC)로 위임**한다.
- kongtrol 은 **자격증명을 자체 수집·저장하지 않는다**. sudo 래핑·비밀번호 캐싱 금지.
- 권한 부족 실패는 **명확한 에러(exit 3)**로 반환. 조용히 무시 금지(R1~R2 권한 절).

### 입력 신뢰 금지 (이벤트 API 직접 전달)

- `type "<text>"`·`key <combo>` 인자는 시스템에 **그대로** 주입된다. 이를 **셸 문자열로
  재구성하지 않는다** → 반드시 **직접 이벤트 API**(SendInput / CGEventPost / uinput /
  XTest)로만 전달한다. command injection 원천 차단(R6 §4-2·R5).
- 스케줄러 표현식·명령 인자도 **파서(croner 등)로 사전 검증** 후 **배열 인자로 exec**
  한다. cron 라인·plist·XML 삽입 공격 차단(R3 §4).
- 사용자가 넘긴 어떤 문자열도 셸에 그대로 넣지 않는다(shell=false 원칙).

### allowlist 우선

- `config.toml` 에 **허용 대상 목록**(kill 가능 프로세스명, 제어 가능 서비스명 등)을
  둔다. **blocklist 아닌 allowlist 우선**(AI/자동화 보안 권고, R6 §4-2).
- allowlist 미설정 시 대화형 확인으로 대체(안전 쪽으로 degrade).
- **rate/scope 제한**: 입력 주입 대량 반복(자동 클릭 봇 등) 오남용 방지를 위해 반복 횟수
  상한 옵션·경고를 둔다.

### 플랫폼별 권한 관문 표

(R6 §4-3 + R5 §2 실측)

| 플랫폼 | 입력 주입 관문 | 서비스/프로세스 | 비고 |
|--------|----------------|-----------------|------|
| **macOS** | TCC — Accessibility + Input Monitoring + PostEvent 사용자 승인, `CGEventPost` 로 주입 | launchd, root | TCC 팝업 **정상 유발**, 우회 CVE 금지. Sequoia/Tahoe 권한 강화 |
| **Linux** | X11 = 바로 주입 / Wayland = `libei`+xdg-desktop-portal RemoteDesktop 승인 or `uinput`(input 그룹) | systemd(D-Bus), root, polkit 부분 위임 | Wayland 전환 고려 필수 |
| **Windows** | `SendInput` 일반 권한이나 **UIPI**: 낮은 무결성→높은 무결성 창 주입 차단. UAC 창 = SecureDesktop 주입 불가 | SCM, Admin(UAC) | UAC 승격 = OS 프롬프트 위임 |

### 공격도구화 방지 5원칙

(R6 §4-4 — 이 프로젝트의 헌법)

1. **권한 우회·private API·TCC 조작 절대 금지** — OS 정상 승인 경로만 사용.
   근거: **CVE-2025-43530, CVE-2025-31250**(2025~2026 macOS TCC 우회 CVE)가
   문제된 만큼, kongtrol 은 이런 우회를 재현하지 않는다. Windows 는 **2026-02
   Google Project Zero UIAccess 남용 우회 사례**(R5 §2·§7)를 인지하되 정당 용도로만.
2. **강력 기능 = 마찰 내장**(확인·dry-run·audit).
3. **비승격 기본**, 승격은 명시·최소·OS 위임.
4. **감사 로그 항상**, append-only 무결성 보존.
5. **allowlist 우선**, 입력은 이벤트 API 직접 전달(문자열 재구성 금지).

### 추가 안전장치 (R5 §7)

- **백그라운드 상시 주입 금지** — 사용자가 명시적으로 시작한 세션에서만 동작.
- **민감정보 마스킹** — 캡처/입력 로그에 비밀번호 등 민감정보 저장 금지.
- **조용한 실패 금지** — 권한 미승인 시 `"X 권한이 필요합니다: [설정 경로]"` 안내.

## Consequences

**긍정**
- 사고·오남용 위험이 구조적으로 낮아진다(파괴적 명령에 다층 마찰).
- audit log 로 모든 위험 동작의 provenance 추적 가능.
- OS 권한 모델을 존중하므로 안티멀웨어 오탐·CVE 재현 리스크 회피.

**부정/비용**
- 자동화 사용성 저하(스크립트는 `--yes` 필수). 단 이는 의도된 마찰.
- 4중 방어·audit·allowlist 구현이 각 도메인 개발에 상시 오버헤드로 추가됨.
- Wayland·TCC 등 플랫폼별 권한 관문 대응 코드가 필요(우회로 단순화 불가).

## Alternatives

| 대안 | 판정 | 사유 |
|------|------|------|
| 방어 없이 편의 우선 | ❌ 탈락 | 오남용·사고 위험. 공격도구화 방치. |
| blocklist 방식 | ❌ 탈락 | 누락 시 위험. allowlist 가 보안 권고. |
| 도구 자체 sudo 래핑 / 자격증명 저장 | ❌ 탈락 | 자격증명 관리 리스크. OS 위임이 안전. |
| TCC 우회로 UX 매끄럽게 | ❌ 탈락 | CVE 재현·공격도구화. **절대 금지**. |

## Open questions

- **allowlist 기본값 정책**: 초기엔 확인 프롬프트 기본 vs allowlist opt-in
  (README §4 오픈이슈) — M2 착수 시 확정.
- **audit 로그 회전·보존기간**: append-only 파일의 rotation·retention 정책.
- **rate limit 기본 임계값**: 입력 주입 반복 횟수 상한의 기본값(M5 에서 확정).

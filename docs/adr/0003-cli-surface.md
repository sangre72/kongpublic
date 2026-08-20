# 0003. CLI 표면 = clap v4 명령 트리 · 위험등급 · 출력 · exit code

- Status: Accepted (2026-08-13)
- Deciders: kongtrol 팀
- Context 관련 리서치: R6(§2), R1~R5

## Context

kongtrol 은 사람(대화형)과 자동화(스크립트/봇) 양쪽이 사용한다. 6개 도메인 × 다수 verb 를 일관된 커맨드 표면으로 노출하고, 위험 명령을 구조적으로 구분하며, 사람용·기계용 출력을 동시에 제공해야 한다. CLI 프레임워크 · 명령 트리 · 위험등급 · 출력 · exit code · 설정경로를 정한다.

## Decision

- **`clap` v4 (derive)**. 명령 = `kongtrol [전역플래그] <domain> <verb> [args]`.
- **전역 플래그**(상위 `Cli` 구조체 → 하위 전파): `--json` `--yes` `--dry-run` `--verbose`.

### 명령 트리 (R6 §2-2 + research/README)

```
kongtrol [--json] [--yes] [--dry-run] [--verbose] <domain> <verb> [args]

  process   (R1)  list | info <pid> | tree | kill <pid> [--signal TERM] | killall <name>
  service   (R2)  list | status <name> | start|stop|restart|enable|disable <name>
  schedule  (R3)  list | add <name> --cmd "..." --cron "..." | remove <name> | run <name>
  app       (R4)  list | launch <name> | quit <name> | focus <name>
  input     (R5)  ★DANGEROUS  click <x> <y> | move <x> <y> | type "<text>" | key "ctrl+c" | scroll <dx> <dy>
  sys       (R5)  info | cpu | mem | disk | net | uptime
  device          list | info <id>

  kongtrol --version | completions <shell> | config <get|set|path>
```

- **동사 표준**(R6 §2-2): 조회 = `list`/`info`/`status`, 변경 = `start`/`stop`/`kill`/`add`/`remove`. read verb 와 mutate verb 로 위험도를 명확 분리.
- CLI 커맨드명은 관용(process/service/kill 등) 사용. 이 단계는 UI/데이터 컬럼이 아닌 내부 CLI 설계이므로 MOIS 네이밍 대상 아님(NAME).

### 위험 등급 태깅 (R6 §2-2)

각 서브커맨드에 위험도 메타 라벨을 붙인다. **DANGEROUS** = [0004](./0004-security-model.md) 의 4중 방어 게이트 강제.

| 등급 | 대상 |
|------|------|
| READ | `process list/info/tree`, `service list/status`, `schedule list`, `app list`, `sys *`, `device *` |
| MUTATE | `service start/restart/enable`, `schedule add/run`, `app launch/quit/focus`, `input move/scroll` |
| **DANGEROUS** | `process kill/killall`, `service stop/disable`, `schedule remove`, `input click/type/key` |

### 출력 포맷 (R6 §2-3)

| 대상 | 설계 |
|------|------|
| 사람용 | `comfy-table`/`tabled` 정렬 테이블. 위험도 = 빨강 색상 + **텍스트 라벨 병기**(색상 단독 금지 — accessibility-guideline: 색상만으로 상태표기 금지). |
| 기계용 | `--json` → `serde_json` envelope. 성공 `{ "data": ..., "meta": { "requestId": ... } }` / 에러 `{ "error": { "code", "message", "requestId" } }`. |

### exit code 규약 (R6 §2-3)

| code | 의미 |
|------|------|
| 0 | 성공 |
| 2 | 사용자 거부(confirm no) |
| 3 | 권한 부족 |
| 4 | 대상 없음 |
| 5 | 플랫폼 미지원([0002](./0002-architecture-trait-platform-split.md) Unsupported) |

### 설정 파일 · 로깅 (R6 §2-3)

- `directories` 크레이트로 OS 표준 경로: macOS `~/Library/Application Support/kongtrol`, Linux `~/.config/kongtrol`, Windows `%APPDATA%\kongtrol`.
- `config.toml`(TOML) — allowlist · 기본 confirm 정책 저장([0004](./0004-security-model.md)).
- 로깅 = `tracing` + `tracing-subscriber`. audit 는 별도 append-only 파일([0004](./0004-security-model.md)).

## Consequences

- 도메인 × verb 트리로 발견성 · 응집 확보, 위험도 태깅이 보안 게이트([0004](./0004-security-model.md))와 1:1 연결.
- `--json` envelope 로 자동화 · 봇 어댑터(M6)가 동일 출력 계약 재사용.
- 표준 exit code 로 스크립트가 실패 원인 분기 가능.
- 비용: 위험도 메타를 모든 서브커맨드에 부착 · 유지해야 함(누락 시 게이트 우회 위험).

## Alternatives

| 후보 | 탈락 이유 |
|------|-----------|
| 플랫한 분리 바이너리(kongtrol-kill 등) | 도메인 응집 · 발견성 저하 |
| 위험도 태깅 없이 모두 동일 취급 | [0004](./0004-security-model.md) 보안 모델과 상충 |
| JSON만 또는 사람용만 단일 출력 | CLI 는 사람 + 자동화 둘 다 대상 |

## Open questions

- completions 자동생성(`clap_complete`) 지원 셸 범위.
- `config set` 의 검증 스키마.
- `--verbose` 로그 레벨 단계 정의.

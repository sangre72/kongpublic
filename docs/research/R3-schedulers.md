# R3 — 스케줄러 / 예약작업 리서치

> OS Control CLI 크로스플랫폼(macOS + Linux + Windows) 스케줄러 관리 리서치
> 작성일: 2026-08-13 · 조사환경: macOS 26.5 (arm64) · 근거: WebSearch 실측(하단 링크)

## 1. 개요

예약작업(스케줄) 관리는 OS마다 네이티브 백엔드가 완전히 다르다. **단일 크로스플랫폼
"진짜 표준"은 존재하지 않으며**, 각 OS의 네이티브 스케줄러를 얇게 래핑하는 방식이 사실상 유일한
안정적 접근이다. 조사 대상 백엔드:

- **Linux**: `cron`(crontab) — 이식성 최강 / `systemd timer`(.timer + .service) — 로깅·미실행 복구 우수 / `anacron` — 상시가동 아닌 머신용
- **macOS**: `launchd`(LaunchAgents/LaunchDaemons plist) — Apple 공식 권장 / `cron` — 레거시(동작하나 deprecated)
- **Windows**: `Task Scheduler` — `schtasks.exe`(레거시 CLI) / PowerShell `ScheduledTasks` 모듈(객체지향, 권장) / Task Scheduler 2.0 COM API(`Schedule.Service`)

핵심 난제: (1) 표현식 형식이 4종 모두 다름(5필드 cron ↔ systemd OnCalendar ↔ plist 딕셔너리 ↔ Task Scheduler 트리거), (2) 유저 레벨 vs 시스템 레벨 권한 모델이 상이, (3) "다음 실행시각" 계산은 백엔드가 직접 안 주는 경우가 많아 별도 cron 파서 필요.

## 2. 플랫폼별 스케줄러 비교표

| 항목 | cron (Linux/macOS레거시) | systemd timer (Linux) | launchd (macOS) | Task Scheduler (Windows) |
|------|--------------------------|------------------------|-----------------|--------------------------|
| **정의 위치** | `crontab` (유저별 spool, `/etc/crontab`) | `.timer`+`.service` unit 파일 | `.plist` (LaunchAgents/Daemons) | Task Store (XML, `\Windows\System32\Tasks`) |
| **목록 조회** | `crontab -l` | `systemctl list-timers [--all]` | `launchctl list` | `Get-ScheduledTask` / `schtasks /Query` |
| **다음 실행시각** | ✗ (자체 미제공 → 파서 필요) | ✓ `list-timers` 가 NEXT 열 출력 | ✗ (자체 미제공) | ✓ `Get-ScheduledTaskInfo` `.NextRunTime` |
| **생성** | `crontab -e` / 파일 write 후 `crontab file` | unit 파일 작성 + `systemctl enable --now foo.timer` | plist 작성 + `launchctl bootstrap`/`load` | `Register-ScheduledTask` / `schtasks /Create` |
| **수정** | 재작성 후 `crontab` 재적용 | unit 편집 + `systemctl daemon-reload` | unload → plist 수정 → load | `Set-ScheduledTask` |
| **삭제** | `crontab -r` (전체) / 라인 제거 | `systemctl disable --now`  + unit 삭제 | `launchctl bootout`/`unload` + plist 삭제 | `Unregister-ScheduledTask` / `schtasks /Delete` |
| **활성/비활성** | 라인 주석(`#`) | `systemctl enable/disable`, `start/stop` | `launchctl enable/disable` | `Enable-/Disable-ScheduledTask` |
| **표현식 형식** | 5필드(`분 시 일 월 요일`) | `OnCalendar=DOW YYYY-MM-DD HH:MM:SS` + `OnBootSec`/`OnUnitActiveSec` | plist `StartCalendarInterval`(dict: Minute/Hour/Day/Weekday/Month) 또는 `StartInterval`(초) | 트리거 객체(Daily/Weekly/AtLogon/AtStartup, `-At` 시각) |
| **표현식 검증툴** | 외부 파서 | `systemd-analyze calendar "Mon..Fri 09:00"` | ✗ | ✗ (모듈 검증) |
| **미실행 복구**(sleep/off) | ✗ 건너뜀 | ✓ `Persistent=true` | ✓ wake 시 coalesce 실행 | ✓ "Run task ASAP after missed start" |
| **로깅** | mail/syslog | ✓ `journalctl -u foo.service` | 콘솔/파일 리다이렉트 지정 | 이벤트 로그(Task Scheduler 운영로그) |
| **유저 레벨** | `crontab -e`(root 불필요) | `systemctl --user`(+`loginctl enable-linger`) | `~/Library/LaunchAgents` | 현재 사용자 계정 태스크 |
| **시스템 레벨** | `/etc/cron.d`, root crontab | 시스템 유닛(`/etc/systemd/system`), root | `/Library/LaunchDaemons`(root) | SYSTEM 계정(관리자 권한 필요) |
| **표준 상태(2026)** | ✅ 안정·이식성 최강 | ✅ 안정·systemd 배포판 권장 | ✅ Apple 공식(cron 대체) | ✅ Windows 표준 |

## 3. cron 표현식 · 크로스플랫폼 라이브러리 (WebSearch 실측)

### 3-1. cron 표현식 파서 / "다음 실행시각" 계산
백엔드가 다음 실행시각을 안 주는 경우(cron·launchd)를 위해 파서 필수.

| 라이브러리 | 생태계 | 특징 | 상태 |
|-----------|--------|------|------|
| **croner** (Hexagon/croner-rust) | Rust | cron 패턴 파싱·**next/previous 실행시각**·타임존 인식, JS croner의 Rust 포팅. 경량 | ✅ 활발 |
| **cronexpr** | Rust | crontab 파싱 + next timestamp 반복(POSIX/Vixie 확장) | ✅ 활발 |
| **cron** (zslayton/cron) | Rust | 클래식 cron 파서, chrono 통합 | ✅ 성숙 |
| **cron-parser** | Rust | 타임존 지원 파싱 | ✅ |
| **croniter** (pallets-eco/croniter) | Python | `get_next(datetime)`, zoneinfo/pytz 타임존, 초·연(1970–2099) 확장 필드 | ✅ Pallets Eco 유지 |

권장(Rust CLI 가정 시): **croner** — next/prev + 타임존, 표현식 검증 겸용. Python 이라면 **croniter**.

### 3-2. 네이티브 백엔드 통합 크로스플랫폼 도구/라이브러리
| 이름 | 접근 | 백엔드 커버 | 참고 |
|------|------|-------------|------|
| **OpenCode Scheduler plugin** | OS 네이티브 스케줄러 래핑 | launchd(mac)·systemd(Linux)·Task Scheduler(Win), cron fallback | 우리가 지향하는 아키텍처 선례 |
| **zephyr-scheduler** (Rust) | Unix 전용 데몬(자체 프로세스 상주) | systemd/launchd 서비스 통합, interval+CRON | Windows 미포함, 프로세스 상주형 |
| **tokio-cron-scheduler** (Rust) | **인프로세스**(OS 스케줄러 미사용) | ✗(앱 살아있어야만 동작) | OS 예약작업 관리 목적엔 부적합 |
| **crony-cli / croner-scheduler** (Rust) | cron 관리 CLI / 스레드 스케줄러 | cron 중심 | 참고용 |

> ⚠️ 주의: `tokio-cron-scheduler`·`job_scheduler` 등 "인프로세스 스케줄러"는 **자기 프로세스가 살아있는 동안만** 동작 → OS 예약작업(재부팅 후에도 유지) 요구사항과 다름. 혼동 금지.

## 4. 권한 / 보안 고려

| 구분 | 유저 레벨 | 시스템 레벨 |
|------|-----------|-------------|
| cron | `crontab -e`, root 불필요 | root(`/etc/cron.d`, `/etc/crontab`) |
| systemd | `systemctl --user`, 단 **로그아웃 시 정지** → `loginctl enable-linger USER` 로 상주 | `sudo systemctl`(`/etc/systemd/system`) |
| launchd | `~/Library/LaunchAgents`(GUI 세션 필요) | `/Library/LaunchDaemons` → **root 필요**, `bootstrap system/` |
| Task Scheduler | 현재 사용자 컨텍스트 | SYSTEM/다른 사용자 → **관리자(UAC) 필요**, `-User "SYSTEM"` |

보안 원칙(프로젝트 security-guideline 준수):
- **입력 신뢰 금지**: 사용자가 넘긴 명령/표현식을 쉘에 그대로 넣지 말 것. 명령은 배열 인자로 exec, 표현식은 파서(croner 등)로 **사전 검증** 후 백엔드에 전달(인젝션 방지 — cron 라인·plist·XML 삽입 공격 차단).
- **권한 상승 명시**: 시스템 레벨 등록은 sudo/UAC 필요를 사용자에게 명확히 고지하고, 기본은 **유저 레벨**로 최소권한.
- **파일 경로 검증**: plist/unit 파일 write 시 경로 traversal 방지, 소유권·퍼미션 확인.
- **비밀정보**: 태스크 명령에 자격증명 평문 삽입 지양(env 참조 권장).

## 5. 추천 — CLI 스케줄러 관리 구현 접근

**결론: "네이티브 백엔드 얇은 래퍼(adapter) + 통합 cron 파서" 아키텍처.** (리스크: 중)

1. **백엔드 어댑터 패턴** — 단일 통합 표준(가상 스케줄러)을 만들지 말고, OS별 어댑터로 분리:
   - Linux: **cron 우선(기본)**, systemd 사용 가능 시 옵션 제공(로깅·복구 필요 태스크). 근거: cron = 이식성·단순·root 불필요, systemd = journald 로깅·`Persistent` 복구.
   - macOS: **launchd 우선**(Apple 공식, cron deprecated). cron 은 fallback만.
   - Windows: **PowerShell `ScheduledTasks` 모듈**(객체지향, `Get-ScheduledTaskInfo.NextRunTime` 등 구조화 데이터). `schtasks.exe` 는 최소 fallback. COM API 는 복잡도 대비 이득 적음.
   - 선례: OpenCode Scheduler 플러그인이 정확히 이 구조(launchd/systemd/Task Scheduler + cron fallback).
2. **표현식은 cron 을 공용 입력 포맷**으로 채택(사용자에게 가장 친숙·이식적), 내부에서 각 백엔드 형식으로 변환:
   - cron → systemd `OnCalendar` 매핑, cron → launchd `StartCalendarInterval` dict 매핑, cron → Task Scheduler 트리거 매핑.
   - 5필드 cron 범위를 넘는 것(초 단위·복잡 캘린더)은 백엔드 네이티브 표현식 직접 입력을 별도 옵션으로 허용.
3. **"다음 실행시각"은 croner(Rust)/croniter(Python) 로 자체 계산** — systemd·Task Scheduler 는 네이티브 값 사용, cron·launchd 는 파서로 보완. 통일된 출력.
4. **권한 계층**: 기본 유저 레벨, `--system` 플래그로만 상승(sudo/UAC 안내). systemd 유저 타이머는 `enable-linger` 자동 안내.
5. **표현식 검증 게이트**: 등록 전 파서로 유효성·다음 5회 실행시각 프리뷰 → 인젝션·오타 동시 방지(§4 보안).

Plan B: 어댑터 구현 부담이 크면 초기엔 **Linux=cron / macOS=launchd / Windows=schtasks** 최소 3백엔드만, systemd·COM 은 후속 확장.

## 6. 참고 링크

**크로스플랫폼 도구 / Rust 스케줄러**
- OpenCode Scheduler plugin(launchd/systemd/Task Scheduler): https://github.com/different-ai/opencode-scheduler
- zephyr-scheduler: https://crates.io/crates/zephyr-scheduler/dependencies
- tokio-cron-scheduler(인프로세스): https://crates.io/crates/tokio-cron-scheduler
- croner-scheduler(threaded): https://github.com/Hexagon/croner-scheduler-rust
- crony-cli: https://lib.rs/crates/crony-cli
- Rust cron 스케줄러 구축 가이드(2026-01): https://oneuptime.com/blog/post/2026-01-25-task-scheduler-cron-expressions-rust/view

**cron 표현식 파서**
- croner(Rust, next/prev·타임존): https://github.com/Hexagon/croner-rust · https://docs.rs/croner
- cronexpr(Rust): https://docs.rs/cronexpr/latest/cronexpr/
- cron(zslayton, Rust): https://github.com/zslayton/cron
- cron-parser(Rust): https://lib.rs/crates/cron-parser
- croniter(Python): https://github.com/pallets-eco/croniter · https://pypi.org/project/croniter/

**systemd timer**
- ArchWiki systemd/Timers: https://wiki.archlinux.org/title/Systemd/Timers
- cron vs systemd timers: https://xtom.com/blog/systemd-vs-cron-linux-task-scheduling/
- systemd user timer 설정(enable-linger): https://www.xf.is/2020/06/27/configuring-systemd-user-timer/
- SUSE Working with systemd Timers: https://documentation.suse.com/smart/systems-management/html/systemd-working-with-timers/index.html

**launchd (macOS)**
- launchd.plist(5) man: https://keith.github.io/xcode-man-pages/launchd.plist.5.html
- StartInterval/StartCalendarInterval 예제: https://alvinalexander.com/mac-os-x/launchd-plist-examples-startinterval-startcalendarinterval/
- launchd로 예약작업 설정: https://blog.darnell.io/automation-on-macos-with-launchctl/

**Windows Task Scheduler**
- Get-ScheduledTask: https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/get-scheduledtask?view=windowsserver2025-ps
- Register-ScheduledTask: https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/register-scheduledtask?view=windowsserver2025-ps
- PowerShell로 태스크 생성·관리: https://woshub.com/how-to-create-scheduled-task-using-powershell/
- COM API 접근(Schedule.Service): https://devblogs.microsoft.com/scripting/using-scheduled-tasks-and-scheduled-jobs-in-powershell/

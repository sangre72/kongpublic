# R1 — 프로세스 관리 (Cross-Platform OS Control CLI)

> 리서치 담당: R1 (프로세스 관리) · 작성일 2026-08-13 · 기준: 최신 안정(2026)
> 대상 플랫폼: macOS · Linux · Windows

## 1. 개요 — 무엇을 제어하는가

프로세스 관리 = OS 상의 실행 단위(process)를 **조회(read)** 하고 **제어(control)** 하는 것.

| 구분 | 세부 항목 |
|------|-----------|
| **조회(read)** | PID·이름·실행경로·명령줄(cmdline)·상태(running/sleep/zombie)·부모PID(PPID)·소유자(UID/user)·CPU%·메모리(RSS/VMS)·스레드 수·시작시각·열린 FD/핸들 |
| **제어(control)** | 종료(terminate=SIGTERM / kill=SIGKILL)·우선순위 변경(nice / Windows priority class)·suspend(SIGSTOP)·resume(SIGCONT)·wait(종료 대기) |

핵심 난점: **POSIX(macOS/Linux)는 signal 기반**, **Windows는 signal 부재**(별도 Win32 API). 이 비대칭이 크로스플랫폼 추상화의 핵심 과제.

---

## 2. 플랫폼별 네이티브 방법

### 2-1. 조회

| 기능 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 프로세스 목록 | `ps -axo pid,ppid,user,%cpu,%mem,comm`, `sysctl` (KERN_PROC), libproc | `/proc/[pid]/{stat,status,cmdline,cwd,exe}`, `ps` | `tasklist`, WMI `Win32_Process`, `EnumProcesses`(PSAPI), `NtQuerySystemInformation` |
| CPU/메모리 | `proc_pidinfo()` (libproc) | `/proc/[pid]/stat`, `/proc/[pid]/statm` | `GetProcessMemoryInfo`, `GetProcessTimes` (PSAPI) |
| 명령줄 | `sysctl KERN_PROCARGS2` (권한 제약 있음) | `/proc/[pid]/cmdline` | `QueryFullProcessImageName`, WMI `CommandLine` |
| 소유자 | `proc_pidinfo` / `ps -o user` | `/proc/[pid]/status` (Uid 필드) | `OpenProcessToken` + `GetTokenInformation` |

> macOS 주의: `/proc` **없음**. `sysctl`·libproc·`proc_pidinfo` 사용. SIP(System Integrity Protection)로 타 프로세스 cmdline/env 접근 제한 강함.

### 2-2. 제어

| 기능 | macOS / Linux (POSIX) | Windows |
|------|------------------------|---------|
| 정상 종료 | `kill(pid, SIGTERM)` / `kill -15` | `taskkill /PID <n>`, `TerminateProcess`(강제만), WM_CLOSE 전송(GUI) |
| 강제 종료 | `kill(pid, SIGKILL)` / `kill -9` | `taskkill /F /PID <n>`, `TerminateProcess(hProc, code)` |
| suspend | `kill(pid, SIGSTOP)` | `NtSuspendProcess` / thread 단위 `SuspendThread`, Sysinternals `pssuspend` |
| resume | `kill(pid, SIGCONT)` | `NtResumeProcess` / `ResumeThread`, `pssuspend -r` |
| 우선순위 | `nice`/`renice`, `setpriority()` (-20~19) | `SetPriorityClass` (IDLE~REALTIME), `start /HIGH` |
| 종료 대기 | `waitpid()`, `pidfd_open`+poll(Linux≥5.3), `kqueue`(mac/BSD) | `WaitForSingleObject(hProc)` |

> Windows 특이점: **정상 종료(graceful) 네이티브 API 없음**. `TerminateProcess`는 항상 강제(SIGKILL 상당). "정상 종료"는 WM_CLOSE / CTRL_C_EVENT(콘솔) 전송으로 흉내내야 하며 신뢰도 낮음. suspend/resume은 문서화 안 된 `NtSuspendProcess`/`NtResumeProcess` 또는 스레드 단위 처리 필요.

---

## 3. 크로스플랫폼 라이브러리 비교 (2026 실측)

| 항목 | **psutil** (Python) | **gopsutil** (Go) | **sysinfo** (Rust) |
|------|---------------------|-------------------|--------------------|
| 최신 버전 | **7.2.2** (2026-01-28), 8.0.0 예정 | **v4.26.4** (2026-04-29, 6월 추가 릴리스) | **0.39.3** (2026) |
| 유지보수 | 매우 활발(원조 프로젝트, 15년+) | 활발(매월말 태그, psutil 이식판) | 활발(83.9M 다운로드) |
| 성숙도 | ★★★★★ 사실상 표준 | ★★★★☆ | ★★★☆☆ (0.x, API 잦은 변경) |
| 플랫폼 | Win/Linux/macOS/FreeBSD/OpenBSD/NetBSD/Solaris | Win/Linux/macOS/FreeBSD/OpenBSD 등 | Win/Linux/macOS/FreeBSD/Android/iOS(+non-supported는 no-op) |
| 조회 커버리지 | 최광범위(FD·connections·환경변수·io_counters 등) | 넓음(psutil 이식, 일부 필드 누락) | **중간** — 기본 필드 위주 |
| 제어: kill/term | ✅ terminate(SIGTERM)/kill(SIGKILL) 구분 | ✅ `SendSignal`/`Terminate`/`Kill` | ⚠️ **`Signal::Kill`만 전 플랫폼 보장**, 그 외 signal은 미지원 시 no-op |
| 제어: suspend/resume | ✅ 크로스플랫폼 | ✅ `Suspend`/`Resume` | ⚠️ Unix signal(STOP/CONT) 경유, Windows 보장 X |
| 제어: nice/priority | ✅ `nice()` (Win priority class 매핑) | ✅ `Nice`/`SetNice` | ❌ 우선순위 API 없음 |
| 권한 처리 | ✅ `AccessDenied`/`NoSuchProcess` 예외 명확 | Go error 반환(플랫폼별 편차) | `Option`/bool 반환, 실패 원인 불명확 |
| cgo/네이티브 의존 | C 확장(빌드 필요, wheel 제공) | **순수 Go, cgo 없음**(struct 이식) | 순수 Rust + OS FFI |
| 라이선스 | **BSD-3-Clause** | **BSD-3-Clause** | **MIT** |

**출처**: psutil 7.2.2 [PyPI/HISTORY](https://github.com/giampaolo/psutil/blob/master/HISTORY.rst) · gopsutil v4.26.4 [pkg.go.dev](https://pkg.go.dev/github.com/shirou/gopsutil/v4) · sysinfo 0.39.3 [crates.io](https://crates.io/crates/sysinfo).

### 3-1. 라이브러리별 제어 성숙도 요약
- **psutil**: 세 후보 중 **제어 API가 가장 완성도 높음**. Windows에서 terminate/kill/suspend/resume/priority 전부 크로스플랫폼 매핑. 단 Windows kill의 `AccessDenied` 미발생 버그 이력([#1595](https://github.com/giampaolo/psutil/issues/1595)), 간헐적 AccessDenied([#1924](https://github.com/giampaolo/psutil/issues/1924)) 존재 → 결과 검증 필요.
- **gopsutil**: 조회는 강력, 제어는 제공하나 Windows suspend/resume·signal 처리에 플랫폼별 편차. 순수 Go라 배포(단일 바이너리) 유리.
- **sysinfo**: 조회 중심 라이브러리. **제어는 `Signal::Kill`만 안정**([Signal enum](https://docs.rs/sysinfo/latest/sysinfo/enum.Signal.html)). suspend/resume/priority는 자체 미비 → 별도 crate(`nix`, Win32 FFI) 병행 필요.

---

## 4. 권한 / 보안 고려사항

| 상황 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 자기 프로세스 조회/제어 | sudo 불필요 | sudo 불필요 | 관리자 불필요 |
| 자기 프로세스 cmdline/env | 대부분 OK | OK | OK |
| **타 유저 프로세스 조회** | 기본 목록/PID는 OK, cmdline·상세는 SIP/권한 제약 | 목록 OK, 상세 일부 제한(`hidepid` 마운트 시) | 목록 OK, 상세는 권한 필요 |
| **타 유저 프로세스 종료** | **root(sudo) 필요** | **root(sudo) 필요** | **관리자(Administrator) 필요** |
| 시스템/보호 프로세스 | SIP로 차단(root도 불가 다수) | root라도 커널/PID1 제약 | PPL(Protected Process Light)·안티멀웨어 보호 프로세스는 관리자도 종료 불가 |
| 우선순위 상향(nice<0) | root 필요 | root 필요(또는 rtprio capability) | REALTIME 등 고우선순위는 관리자 필요 |

### 보안 주의점
- **최소권한 원칙**: CLI가 무분별하게 관리자/root로 실행되지 않도록. 권한 상승은 실제 필요한 제어 명령에서만.
- **권한 실패는 명확한 에러로**: psutil 스타일 `AccessDenied`/`NoSuchProcess` 구분 노출. Windows는 종료 성공처럼 보이나 실패하는 케이스([#1595](https://github.com/giampaolo/psutil/issues/1595)) → **제어 후 프로세스 존재 재확인**으로 결과 검증.
- **PID 재사용(race)**: 조회 후 종료 사이 PID가 재할당될 수 있음 → 시작시각(create_time) 병행 확인으로 오종료 방지.
- **보호 프로세스**: 종료 불가를 정상 응답으로 처리(사용자에게 "권한/보호로 불가" 안내), 무한 재시도 금지.

---

## 5. 추천 — 이 CLI의 프로세스 관리 구현 접근

### 5-1. 언어/라이브러리 선택
- **Rust 코어 + `sysinfo`(조회) + 제어 보강**을 1순위 추천:
  - 근거: 단일 정적 바이너리 배포(3플랫폼 무런타임), MIT 라이선스, 안전성.
  - 단, `sysinfo`는 **조회에만 사용**. 제어(term/kill/suspend/resume/priority)는 `sysinfo`의 kill 한계 때문에 **플랫폼별 얇은 어댑터**로 직접 구현: Unix는 `nix`(signal·setpriority), Windows는 `windows` crate(`TerminateProcess`/`NtSuspendProcess`/`SetPriorityClass`).
- **대안(Plan B) — Go + `gopsutil`**: cgo 없는 순수 Go로 크로스컴파일이 가장 단순하고 제어 API도 내장. Rust 대비 조회/제어 균형이 좋아 팀이 Go에 익숙하면 이쪽이 총비용 최저.
- **Python + psutil은 참조 구현/프로토타이핑용**: 제어 API 완성도는 최고지만 배포(런타임·C확장 wheel) 부담 → 최종 CLI 코어로는 비추천, 대신 **동작 기준(reference)** 으로 삼아 Rust/Go 어댑터를 검증.

### 5-2. 아키텍처 원칙
1. **조회/제어 분리**: 조회는 라이브러리 위임, 제어는 플랫폼 어댑터(trait/interface)로 추상화 — Windows의 signal 부재를 어댑터 내부에서 흡수.
2. **graceful→force 2단계 종료**: terminate(SIGTERM / WM_CLOSE) 시도 → 타임아웃 후 kill(SIGKILL / TerminateProcess). Windows graceful은 best-effort임을 명시.
3. **제어 결과 검증 필수**: 종료 명령 후 create_time 포함 재조회로 실제 종료 확인(Windows 무증상 실패 대응).
4. **권한 에러 표준화**: `AccessDenied`/`NoSuchProcess`/`Protected` 3분류로 통일된 exit code·메시지.
5. **PID+create_time 튜플**로 타깃 식별(PID 재사용 방지).

### 5-3. 결론
> **조회는 성숙 라이브러리(sysinfo/gopsutil) 위임, 제어는 플랫폼별 어댑터로 직접 구현**하되, **psutil을 동작 기준 레퍼런스로 사용**. 배포 단순성 우선이면 Go+gopsutil, 안전성/성능/단일바이너리 우선이면 Rust+sysinfo(+nix/windows) 조합.

리스크: **중** (조회는 안정, 제어의 Windows 비대칭·권한 처리가 핵심 리스크 — 어댑터 계층과 결과 검증으로 완화 가능).

---

## 6. 참고 링크

- psutil 릴리스/HISTORY (7.2.2, 2026-01): https://github.com/giampaolo/psutil/blob/master/HISTORY.rst
- psutil PyPI: https://pypi.org/project/psutil/
- psutil 플랫폼 지원: https://psutil.readthedocs.io/latest/platform.html
- psutil Windows kill AccessDenied #1595: https://github.com/giampaolo/psutil/issues/1595
- psutil 간헐 AccessDenied #1924: https://github.com/giampaolo/psutil/issues/1924
- psutil suspend/resume Windows #145: https://github.com/giampaolo/psutil/issues/145
- gopsutil v4 (pkg.go.dev): https://pkg.go.dev/github.com/shirou/gopsutil/v4
- gopsutil 릴리스: https://github.com/shirou/gopsutil/releases
- Rust sysinfo crates.io: https://crates.io/crates/sysinfo
- Rust sysinfo Signal enum: https://docs.rs/sysinfo/latest/sysinfo/enum.Signal.html
- Rust sysinfo Process: https://docs.rs/sysinfo/latest/sysinfo/struct.Process.html
- Sysinternals pssuspend(Windows suspend/resume): https://learn.microsoft.com/en-us/sysinternals/downloads/pssuspend

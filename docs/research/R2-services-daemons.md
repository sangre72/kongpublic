# R2 — 서비스/데몬 관리 리서치 (크로스플랫폼 OS Control CLI)

> 담당: R2 (서비스/데몬) · 작성일: 2026-08-13 · 기준: 2026년 최신+안정, WebSearch 실측
> 범위: Linux(systemd) · macOS(launchd) · Windows(Service/SCM) 서비스 조회·제어·권한·크로스플랫폼 추상화

## 1. 개요

3대 OS는 각각 **완전히 다른 서비스(데몬) 관리 모델**을 가진다. 공통 개념은 존재하나(서비스 목록·상태·start/stop/enable-at-boot) 명령·API·권한 체계·"unit 정의 파일" 포맷이 전부 다르다.

- **Linux**: `systemd` 가 사실상 표준(RHEL·Ubuntu·SUSE·Debian·Fedora 등). `systemctl` CLI 또는 **D-Bus API**(`org.freedesktop.systemd1`)로 제어. 구형은 SysVinit / Upstart, 경량 배포판(Alpine·Gentoo)은 OpenRC.
- **macOS**: `launchd`(PID 1) 가 유일한 서비스 매니저. `launchctl` CLI 로 제어, 서비스 정의는 **plist** 파일. 신형 문법은 `bootstrap`/`bootout`(domain-target 기반), 구형은 `load`/`unload`(legacy).
- **Windows**: **SCM(Service Control Manager, `services.exe`)** 가 in-memory 서비스 DB 소유. `sc.exe`, PowerShell `*-Service` cmdlet, MMC 스냅인이 모두 그 뒤의 **Service Control API(RPC)** 를 호출.

핵심 함의: 이 CLI는 **얇은 추상화 인터페이스 하나** + **플랫폼별 백엔드 3종**으로 설계해야 한다. 서비스 제어는 대부분 **관리자/root 권한**이 필요하다.

## 2. 플랫폼별 서비스 모델 비교표

### 2-1. 조회 (query)

| 작업 | Linux systemd | macOS launchd | Windows SCM |
|------|---------------|---------------|-------------|
| 서비스 목록 | `systemctl list-units --type=service` / `list-unit-files` | `launchctl list` (domain: `launchctl print system`) | `Get-Service` / `sc.exe query` |
| 상태(running) | `systemctl status <svc>` / `is-active` | `launchctl print system/<label>` (PID·last exit) | `Get-Service <n>` (Status=Running/Stopped) / `sc.exe query <n>` |
| 부팅자동시작 여부 | `systemctl is-enabled <svc>` | plist `RunAtLoad`/`KeepAlive` 키 + 설치 위치 | `Get-Service`→`StartType` / `sc.exe qc <n>` (AUTO_START) |
| 의존성 | `systemctl list-dependencies <svc>` | (명시 의존성 개념 약함; `WatchPaths`/socket activation) | `sc.exe qc <n>` (DEPENDENCIES 필드) |
| enabled 목록 | `systemctl list-unit-files --state=enabled` | plist 설치 디렉터리 스캔 | `Get-Service \| ? StartType -eq Automatic` |

### 2-2. 제어 (control)

| 작업 | Linux systemd | macOS launchd (신형) | Windows SCM |
|------|---------------|----------------------|-------------|
| start | `systemctl start <svc>` | `launchctl kickstart <domain>/<label>` (또는 bootstrap) | `Start-Service <n>` / `sc.exe start <n>` |
| stop | `systemctl stop <svc>` | `launchctl bootout <domain>/<label>` | `Stop-Service <n>` / `sc.exe stop <n>` |
| restart | `systemctl restart <svc>` | bootout → bootstrap (원자적 restart 없음) | `Restart-Service <n>` |
| enable (부팅시) | `systemctl enable <svc>` (심링크 생성) | plist 를 LaunchDaemons/Agents 에 배치 + `RunAtLoad=true` | `Set-Service <n> -StartupType Automatic` / `sc.exe config <n> start=auto` |
| disable | `systemctl disable <svc>` | plist 제거 또는 `launchctl disable <domain>/<label>` | `Set-Service -StartupType Disabled` / `sc.exe config start=disabled` |
| enable+start 동시 | `systemctl enable --now <svc>` | bootstrap (RunAtLoad 시 즉시 실행) | (2단계 필요) |

### 2-3. 정의 파일 · API · 위치

| 항목 | Linux systemd | macOS launchd | Windows SCM |
|------|---------------|---------------|-------------|
| unit/정의 포맷 | `.service` INI-style unit 파일 | `.plist` (XML/property list) | 레지스트리 `HKLM\SYSTEM\CurrentControlSet\Services` |
| 정의 위치 | `/etc/systemd/system` (관리자), `/usr/lib/systemd/system` (패키지), `~/.config/systemd/user` (유저) | 데몬: `/Library/LaunchDaemons`, `/System/Library/LaunchDaemons`; 에이전트: `~/Library/LaunchAgents`, `/Library/LaunchAgents`, `/System/Library/LaunchAgents` | 레지스트리 + 바이너리 경로 |
| 프로그래밍 API | **D-Bus** `org.freedesktop.systemd1` (StartUnit/StopUnit/EnableUnitFiles 등) | IPC(문서화 안 됨) → 실무는 `launchctl` 서브프로세스 | **Win32 Service Control API** (OpenSCManager/CreateService/ControlService), WMI `Win32_Service` |
| daemon 등록 갱신 | `systemctl daemon-reload` | bootstrap 시 재파싱 | 즉시 반영 |

### 2-4. LaunchDaemons vs LaunchAgents (macOS 고유)

| 구분 | LaunchDaemon | LaunchAgent |
|------|--------------|-------------|
| 실행 컨텍스트 | 시스템 부팅 시, root(또는 지정 UID), **유저 로그인 불필요** | 유저 로그인 세션 내, GUI 접근 가능 |
| domain-target | `system` (root 필요) | `gui/<uid>` 또는 `user/<uid>` |
| 위치 | `/Library/LaunchDaemons` (서드파티), `/System/...`(OS) | `~/Library/LaunchAgents`(유저), `/Library/LaunchAgents`(전역) |
| 권한 | 로드에 **sudo(root) 필수**; plist 권한 부적절하면 launchctl 거부 | 유저 권한으로 로드 가능 |

## 3. 크로스플랫폼 추상화 가능성 · 기존 라이브러리 (WebSearch 실측)

3개 모델을 **install/start/stop/enable/status 단일 인터페이스**로 감싸는 성숙한 라이브러리가 이미 존재한다. "직접 sc/launchctl/systemctl 텍스트 파싱"보다 이들 백엔드를 참고/차용하는 것이 안전.

| 라이브러리 | 언어 | 지원 백엔드 | 유저/시스템 레벨 | 비고 |
|-----------|------|-------------|------------------|------|
| **service-manager** | Rust | systemd, OpenRC, launchd, Windows(`sc.exe`+WinSW), FreeBSD rc.d | ✅ `set_level(System/User)` | install/uninstall/start/stop/status + RestartPolicy. 크로스플랫폼 커버리지 가장 넓음 |
| uni_service_manager | Rust | systemd, launchd, Windows | ✅ user+system | 플랫폼 무관 API |
| cross-platform-service | Rust | Windows(`windows-rs`), Linux(D-Bus systemd) | 부분 | macOS 미흡, 네이티브 API 직접 호출(서브프로세스 회피) |
| **kardianos/service** | Go | Windows, systemd/Upstart/SysV/OpenRC, launchd | 주로 system | 가장 널리 쓰이는 Go 표준. install/start/stop + 인터랙티브/서비스 실행 감지. fork 다수(percona·k0s) |
| **node-windows / node-mac / node-linux** (coreybutler) | Node.js | 각 1플랫폼 | system | 플랫폼별 개별 패키지. `os-service`/`node-service`(nssm 사용)가 통합 시도 |

관찰: **Rust `service-manager`** 가 백엔드 폭(systemd+OpenRC+launchd+Windows+rc.d)·유저/시스템 레벨·restart policy까지 가장 포괄적. Go 진영은 **kardianos/service** 가 사실상 표준. 어느 것도 "임의 서비스 조회+제어(관리)"보다는 "자기 프로그램을 서비스로 등록"에 초점이 맞춰진 경향이 있어, **목록/상태 조회 부분은 CLI 래핑을 보완**해야 할 수 있음.

## 4. 권한 / 보안 고려 (권한상승 필요 지점)

| 작업 범위 | Linux | macOS | Windows |
|-----------|-------|-------|---------|
| 시스템 서비스 조회 | 대개 비특권 가능(`list`/`status`) | `launchctl print system` 은 root 권장 | `Get-Service`/`sc query` 비특권 가능 |
| 시스템 서비스 start/stop/enable | **root 필요**(sudo 또는 polkit 인증) | **root 필요**(`system/` domain, sudo) | **관리자(UAC 상승) 필요**; SCM 이 ACL 검사 |
| 유저 서비스 조회/제어 | `systemctl --user` = 해당 유저 권한(root 불필요) | `gui/<uid>`/`user/<uid>` = 유저 권한 | (유저 레벨 서비스 개념 없음 — 항상 SCM) |
| 권한 위임 메커니즘 | **polkit** 로 특정 유저에 세분 허용 가능; sudoers `systemctl` 허용 시 권한상승 취약점 주의 | plist 파일 권한/소유 검증(부적절 시 거부) | 서비스별 DACL, `SeServiceLogonRight` |

보안 주의(러시아 룰렛 아님 — 실제 CVE 근거):
- Linux: `systemctl` 을 sudo/SUID 로 무분별 허용하면 **임의 서비스 등록·실행 → 권한상승**(HackTricks 류 대표 벡터). polkit 자체 취약점(CVE-2021-3560) 이력.
- 이 CLI는 권한상승을 **자동으로 감행하지 말고**, 필요 시 명시적으로 sudo/UAC 상승을 유도하고 실패를 명확한 에러로 반환해야 한다(권한 없는 조작을 조용히 무시하는 launchctl legacy `load` 문제 회피).

## 5. 추천 — 이 CLI의 서비스 관리 구현 접근

**A. 아키텍처: 얇은 공통 인터페이스 + 플랫폼별 백엔드 (trait/interface)**
```
ServiceManager { list(), status(name), start, stop, restart, enable, disable }
  ├─ LinuxBackend   → 1차: systemd D-Bus API, 폴백: systemctl 서브프로세스; OpenRC/SysV 는 detect 후 CLI 래핑
  ├─ MacBackend     → launchctl 신형 문법(bootstrap/bootout/kickstart/print, domain-target)
  └─ WindowsBackend → Win32 Service Control API(네이티브) 우선, 폴백: sc.exe / PowerShell
```

**B. 구현 우선순위·근거**
1. **기존 크레이트/라이브러리 차용 우선**: Rust면 `service-manager`(systemd+OpenRC+launchd+Windows+rc.d, user/system level, restart policy 커버), Go면 `kardianos/service`. 바퀴 재발명 대신 검증된 백엔드를 쓰되, **"임의 서비스 목록·상태 조회"가 부족하면 CLI 래핑으로 보완**.
2. **Linux는 systemd 우선, D-Bus API 선호**: 텍스트 파싱보다 D-Bus(`org.freedesktop.systemd1`) 가 구조적·안정적. OpenRC/SysV 는 `detect → CLI 래핑` 폴백.
3. **macOS는 신형 launchctl 문법(bootstrap/bootout/kickstart/print)** 사용. legacy `load`/`unload` 는 broken plist 에서 조용히 exit 0 하는 문제로 회피. **LaunchDaemon(system, root) vs LaunchAgent(gui/user)** 를 명확히 구분해 CLI 옵션(`--scope system|user`)으로 노출.
4. **Windows는 Win32 Service Control API 네이티브 호출** 우선(`sc.exe` 파싱은 폴백). PowerShell `Set-Service` 는 logon 계정 설정 등 일부 기능 미지원이므로 API/`sc config` 병용.
5. **권한 모델 명시화**: system-scope 조작은 root/UAC 필요를 사전 감지 → 부족 시 명확한 에러+권한상승 안내. user-scope(`systemctl --user`, `gui/<uid>`)는 무권한 경로로 우선 지원.
6. **공통 상태 모델 정규화**: 3플랫폼의 상태를 `{Running, Stopped, Enabled/AutoStart, Disabled}` 로 정규화한 DTO 로 반환(플랫폼 원문 필드는 raw로 보존).

**C. 리스크**: 중(中). 각 백엔드가 성숙 라이브러리로 커버되나, "임의 서비스 관리"(등록 아닌 조회+제어) 커버리지·에러 정규화·권한 상승 UX 가 실질 작업량. macOS launchd 는 문서화 부족으로 CLI 래핑 의존 불가피.

## 6. 참고 링크

- systemd/systemctl (enable/disable/status): https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/system_administrators_guide/chap-managing_services_with_systemd
- systemd D-Bus API (Python 예): https://pi3g.com/enabling-and-disabling-a-systemd-service-in-python-using-dbus/
- launchd/launchctl 튜토리얼: https://www.launchd.info/
- launchctl 신형 vs legacy(bootstrap/bootout): https://gist.github.com/masklinn/a532dfe55bdeab3d60ab8e46ccc38a68
- LaunchAgents vs LaunchDaemons·권한: https://mundobytes.com/en/How-to-use-launchagents-and-launchdaemons-on-macOS/
- launchctl new subcommand 기초: https://www.alansiu.net/2023/11/15/launchctl-new-subcommand-basics-for-macos/
- Windows SCM (Win32 apps): https://learn.microsoft.com/en-us/windows/win32/services/service-control-manager
- sc.exe 레퍼런스: https://ss64.com/nt/sc.html
- PowerShell Set-Service: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/set-service
- Rust service-manager 크레이트: https://crates.io/crates/service-manager · https://docs.rs/service-manager/latest/service_manager/
- Rust uni_service_manager: https://crates.io/crates/uni_service_manager
- Go kardianos/service: https://github.com/kardianos/service
- Node os-service: https://www.npmjs.com/package/os-service
- systemctl polkit/권한상승 주의: https://medium.com/@ashrafal3oni/understanding-systemctl-and-systemd-services-for-privilege-escalation-01201f976f85

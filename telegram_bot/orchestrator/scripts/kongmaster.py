#!/usr/bin/env python3
"""kongmaster — orch/worker claude proc-liveness watchdog + auto-restart.

Role-definition source-of-truth (full rationale, scope-boundary, CON, recovery
sequence design) = telegram_bot/orchestrator/kongmaster.txt (a_949). This
docstring is a short pointer only — edit kongmaster.txt for anything beyond
inline implementation notes, to avoid doc/code drift (a_949 CON).

Reg: a_946(build) / a_947(proc-first-gate fix) / a_948(tty-lifecycle+bootout) /
a_949(this doc-split).
"""
import subprocess
import time
import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOGS = os.path.join(ROOT, "logs")
CLAUDE_JSON = os.path.expanduser("~/.claude.json")

POLL_INTERVAL_SEC = 20
THRESHOLD_SEC = 90  # heartbeat 무갱신 임계값(보수적, a_946 CONSTRAINTS)
BOOT_WAIT_SEC = 12  # claude 부팅 후 텍스트 주입까지 대기(대략적, output감지 대신)
BOOT_VERIFY_RETRY_SEC = 3  # boot-wait 후 실제 claude proc 등장 확인 재시도 간격
BOOT_VERIFY_MAX_TRIES = 5  # BOOT_WAIT_SEC(12s) 후 추가로 최대 15s 더 재확인

ROLES = {
    "orch": {
        "tty": "ttys000",
        "heartbeat_files": [".orch_alive", ".orch_tick"],
        "load_cmd": "och.txt 파일의 역할 파악",
        "window_title_hint": "orch",
        "launchd_jobs": ["com.kongbot.orch-tick", "com.kongbot.orch-watch2"],
    },
    "worker": {
        "tty": "ttys001",
        "heartbeat_files": [".worker1_tick"],
        "load_cmd": "worker_1.txt 파일의 역할 분석",
        "window_title_hint": "worker",
        "launchd_jobs": ["com.kongbot.worker1-tick", "com.kongbot.worker1-watch2"],
    },
}
# ★a_947 fix: tty is a snapshot at kongmaster start (from `ps` at deploy time). If the
# actual orch/worker tty differs (e.g. restarted in a new terminal window), ROLES[*]["tty"]
# must be updated — auto-detect isn't safe (multiple claude procs could exist transiently
# during a manual restart). TODO(follow-up): make tty self-healing after a successful
# restart_role() call instead of a static value.


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] kongmaster: {msg}", flush=True)


def heartbeat_age_sec(role):
    """role의 heartbeat 파일들 중 가장 최근 mtime 기준 경과초. 파일 전부 없으면 None(판단불가)."""
    ages = []
    for fname in ROLES[role]["heartbeat_files"]:
        path = os.path.join(LOGS, fname)
        if os.path.exists(path):
            ages.append(time.time() - os.path.getmtime(path))
    if not ages:
        return None
    return min(ages)  # 가장 최근(가장 작은 age) 하나라도 살아있으면 그걸 기준


def claude_pids():
    """현재 떠있는 claude --dangerously-skip-permissions 프로세스 (pid, tty) 목록."""
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,tty,command"],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception as e:
        log(f"ps 실패: {e}")
        return []
    result = []
    for line in out.splitlines()[1:]:
        parts = line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        pid, tty, cmd = parts
        if "claude" in cmd and "--dangerously-skip-permissions" in cmd:
            result.append((pid.strip(), tty.strip()))
    return result


def role_proc_alive(role):
    """★a_947 fix: role의 지정 tty에 claude 프로세스가 실제로 떠있는지(1차 게이트).
    heartbeat 파일은 launchd M1(worker1-tick 등)이 세션과 무관하게 계속 갱신할 수
    있어(예: 터미널 창만 닫히고 claude 프로세스는 죽었는데 launchd tick은 여전히
    도는 경우), heartbeat만으로는 "claude 세션이 살아있다"를 보장 못 한다.
    proc-existence를 먼저 확인하고, 없으면 heartbeat와 무관하게 즉시 dead 판정."""
    tty = ROLES[role]["tty"]
    return any(t == tty for _pid, t in claude_pids())


def is_role_alive(role):
    """★a_947: proc-existence(해당 tty)가 1차 게이트, heartbeat-age는 2차(hang 감지용)."""
    if not role_proc_alive(role):
        return False, f"claude proc absent on {ROLES[role]['tty']}"
    age = heartbeat_age_sec(role)
    if age is None:
        # heartbeat 파일 자체가 없음 — proc은 살아있으니 판단보류(재기동 안 함)
        return True, "proc alive, no heartbeat file(inconclusive, no restart)"
    if age > THRESHOLD_SEC:
        return False, f"proc alive but heartbeat stale {age:.0f}s(threshold {THRESHOLD_SEC}s) — hang"
    return True, f"proc alive, heartbeat {age:.0f}s ago"


def ensure_trust_dialog_accepted():
    """★a_952 fix: claude가 trust-dialog에서 막혀 부팅 없이 즉시 종료되는 근본원인 차단.
    ~/.claude.json projects[ROOT].hasTrustDialogAccepted가 false(또는 미존재)면 true로
    설정 — idempotent(이미 true면 no-op). restart_role() 새 터미널 오픈 '직전' 매번 호출:
    이 파일은 claude 버전업 등으로 리셋될 수 있어 한 번 고쳐도 영구 보장이 아니다."""
    try:
        with open(CLAUDE_JSON, "r") as f:
            data = json.load(f)
    except Exception as e:
        log(f"trust-dialog 체크 실패(~/.claude.json 읽기): {e}")
        return False

    projects = data.setdefault("projects", {})
    proj = projects.setdefault(ROOT, {})
    if proj.get("hasTrustDialogAccepted") is True:
        return True  # 이미 정상 — no-op

    proj["hasTrustDialogAccepted"] = True
    try:
        with open(CLAUDE_JSON, "w") as f:
            json.dump(data, f, indent=2)
        log(f"trust-dialog 자동수정: projects[{ROOT}].hasTrustDialogAccepted false→true")
        return True
    except Exception as e:
        log(f"trust-dialog 자동수정 실패(~/.claude.json 쓰기): {e}")
        return False


def bootout_role_launchd(role):
    """★a_948: kongmaster의 유일한 승인된 M1/M2 정지 경로.
    NEVER-STOP-M1/M2 규칙(worker_1.txt L5)은 "살아있는 동안" 적용 — kongmaster가
    proc-dead를 이미 확정하고 재기동을 결정한 '이후'에만, 딱 이 시점에만 launchd
    bootout 허용(a_948 CON: 이 경로 외 누구도 "죽은 것 같다"는 판단만으로 M1/M2를
    끄면 안 됨). bootout으로 heartbeat 파일을 깨끗한 상태로 리셋해 새 세션의 M1/M2가
    stale-carryover 없이 새로 소유권을 갖게 한다."""
    uid = os.getuid()
    domain = f"gui/{uid}"
    for job in ROLES[role]["launchd_jobs"]:
        try:
            subprocess.run(
                ["launchctl", "bootout", f"{domain}/{job}"],
                capture_output=True, text=True, timeout=10,
            )
            log(f"{role} launchd bootout: {job} (kongmaster-owned dead-confirmed restart)")
        except Exception as e:
            log(f"{role} launchd bootout 실패({job}): {e}")


def restart_role(role):
    """proc-dead 확정 후: launchd bootout(heartbeat 클린리셋) → 새 Terminal 창에서
    claude 재기동 → 역할 로딩 명령 자동 입력. 새 세션이 자신의 P0(session_p0.sh)로
    M1/M2를 다시 arm하면서 launchd도 새로 bootstrap됨(기존 ensure_tick 스크립트 경로)."""
    load_cmd = ROLES[role]["load_cmd"]
    log(f"{role} 재기동 시작")

    bootout_role_launchd(role)

    # ★a_952: 새 터미널 열기 직전 매번 trust-dialog 상태 보장(idempotent).
    # 여기서 실패해도 시도는 계속 — osascript-open은 시도하되 아래 boot-verify가
    # proc-미등장으로 실패를 잡아낸다(silent-untrust-exit 재발 시 로그에 남음).
    ensure_trust_dialog_accepted()

    pids_before = {pid for pid, _tty in claude_pids()}

    # ★a_952 fix: ROLES[role]["tty"]는 kongmaster 기동시점 snapshot이라 새로 여는
    # 터미널의 tty와 다를 수 있음(known limitation, 코드 상단 TODO 참고 — 실제로
    # ttys001 static value인데 새 창은 ttys011 등으로 열려 boot-verify가 false-negative
    # 내는 사고 발생). `tty of newTab`으로 새 창의 실제 tty를 직접 얻어와 그걸
    # 기준으로 검증 + ROLES 갱신(self-healing, 다음 사이클부터 정확).
    open_script = f'''
    tell application "Terminal"
        activate
        set newTab to do script "cd {ROOT} && claude --dangerously-skip-permissions"
        delay 1
        set custom title of front window to "kongmaster-{role}"
        return tty of newTab
    end tell
    '''
    try:
        osa_result = subprocess.run(["osascript", "-e", open_script], check=True, timeout=15, capture_output=True, text=True)
        new_tty_path = osa_result.stdout.strip()  # e.g. "/dev/ttys011"
        new_tty = new_tty_path.replace("/dev/", "")
        log(f"{role} 새 터미널 오픈(kongmaster_pid={os.getpid()}, new_tty={new_tty})")
        if new_tty and new_tty != ROLES[role]["tty"]:
            log(f"{role} tty self-heal: {ROLES[role]['tty']} -> {new_tty}(snapshot-drift 보정)")
            ROLES[role]["tty"] = new_tty
    except Exception as e:
        log(f"{role} 새 터미널 오픈 실패: {e}")
        return False

    log(f"{role} claude 부팅 대기 {BOOT_WAIT_SEC}s")
    time.sleep(BOOT_WAIT_SEC)

    # ★a_952: blind-sleep만으로 "부팅 성공" 단정 금지 — trust-dialog에서 막히면
    # claude가 즉시 종료돼 새 claude proc이 끝내 안 나타난다(원래 버그 재현 형태).
    # BOOT_WAIT_SEC 이후 추가로 최대 BOOT_VERIFY_MAX_TRIES회 재확인.
    new_pid = None
    for attempt in range(BOOT_VERIFY_MAX_TRIES):
        pids_now = {pid for pid, tty in claude_pids() if tty == ROLES[role]["tty"]}
        fresh = pids_now - pids_before
        if fresh:
            new_pid = sorted(fresh)[0]
            break
        log(f"{role} boot-verify 재시도 {attempt+1}/{BOOT_VERIFY_MAX_TRIES}(새 claude proc 미등장, tty={ROLES[role]['tty']})")
        time.sleep(BOOT_VERIFY_RETRY_SEC)

    if new_pid is None:
        log(f"{role} 부팅 실패 확정 — trust-dialog fix 후에도 새 claude proc이 {ROLES[role]['tty']}에 안 나타남(exit-on-untrusted 재발 가능성)")
        return False

    # ppid 체인 증명(a_952 TASK 3): new_pid → 부모(터미널 shell) → ... → osascript/kongmaster 인과관계 로깅
    try:
        chain = [new_pid]
        cur = new_pid
        for _ in range(6):
            ppid_out = subprocess.run(["ps", "-o", "ppid=", "-p", cur], capture_output=True, text=True, timeout=5).stdout.strip()
            if not ppid_out or ppid_out == "1":
                chain.append(ppid_out or "1")
                break
            chain.append(ppid_out)
            cur = ppid_out
        log(f"{role} ppid 체인(new_claude_pid→...→root): {' -> '.join(chain)} (kongmaster_pid={os.getpid()})")
    except Exception as e:
        log(f"{role} ppid 체인 추적 실패(비치명적): {e}")

    log(f"{role} 부팅 확인됨(new_pid={new_pid})")

    # ★2 arms 중복방지 지시: 역할로딩 명령 뒤에 이어서 주입 — 새 세션이 부팅 끝나고
    # 자기 역할(P0)로 M1/M2 arm할 때, 기존 launchd/scheduler가 이미 떠있으면(중복)
    # 재기동하지 말고 skip하라는 지시(dedup-arm). 매 재기동마다 자동 포함(구두로
    # 매번 별도 전달할 필요 없게).
    dedup_arm_cmd = (
        "부팅이 다 끝나면 니 역할에 맞는 2 arms(M1/M2) 중복되지 않게 띄워 — "
        "arm 전 기존 launchd/scheduler 이미 떠있으면(중복) 재기동하지 말고 skip. "
        "ensure_tick 스크립트에서 already-running 체크 필수."
    )
    inject_script = f'''
    tell application "Terminal"
        activate
        do script "{load_cmd}" in front window
        delay 1
        do script "{dedup_arm_cmd}" in front window
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", inject_script], check=True, timeout=15)
    except Exception as e:
        log(f"{role} 역할로딩 명령 주입 실패: {e}")
        return False

    log(f"{role} 재기동 완료(역할로딩 명령 + dedup-arm 지시 주입: '{load_cmd}')")
    return True


def check_and_recover(role):
    alive, reason = is_role_alive(role)
    if alive:
        return
    log(f"{role} 죽음/멈춤 감지 — {reason}")

    # 레이스 방지: 재확인(프로세스가 그 사이 살아났을 수 있음)
    time.sleep(3)
    alive2, reason2 = is_role_alive(role)
    if alive2:
        log(f"{role} 재확인시 정상(false-positive 방지) — {reason2}, 재기동 취소")
        return

    restart_role(role)


def main_loop():
    log(f"시작 — poll={POLL_INTERVAL_SEC}s threshold={THRESHOLD_SEC}s root={ROOT}")
    while True:
        for role in ROLES:
            try:
                check_and_recover(role)
            except Exception as e:
                log(f"{role} 체크 중 예외: {e}")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check-once":
        # 동작확인용 1회 판정 모드(재기동 안 함, dry-run)
        for role in ROLES:
            alive, reason = is_role_alive(role)
            log(f"{role}: alive={alive} ({reason})")
        sys.exit(0)
    main_loop()

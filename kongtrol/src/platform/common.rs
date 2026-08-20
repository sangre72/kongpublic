//! 플랫폼 공통 구현 — sysinfo 기반 SystemInfo · ProcessManager 조회(READ).
//! sysinfo 0.39.x 는 크로스플랫폼이라 조회는 공통. 제어(kill 등)는 platform 별 stub(M2에서 nix/windows).
use crate::core::{
    KongtrolError, ProcessInfo, ProcessManager, Result, SysSummary, SystemInfo, unsupported,
};
use sysinfo::System;

/// sysinfo 기반 SystemInfo(M1 실동작). READ 전용, 승격 불요.
pub struct SysInfoImpl;

impl SystemInfo for SysInfoImpl {
    fn summary(&self) -> Result<SysSummary> {
        let mut sys = System::new_all();
        sys.refresh_all();
        Ok(SysSummary {
            os: System::long_os_version().unwrap_or_else(|| "unknown".into()),
            kernel: System::kernel_version().unwrap_or_else(|| "unknown".into()),
            cpu_count: sys.cpus().len(),
            mem_total_bytes: sys.total_memory(),
        })
    }
}

/// sysinfo 기반 ProcessManager. 조회(list/info)=M1 실동작, 제어(kill)=M2 stub(Unsupported).
pub struct ProcImpl;

impl ProcessManager for ProcImpl {
    fn list(&self) -> Result<Vec<ProcessInfo>> {
        let mut sys = System::new_all();
        sys.refresh_all();
        let mut out: Vec<ProcessInfo> = sys
            .processes()
            .iter()
            .map(|(pid, p)| ProcessInfo {
                pid: pid.as_u32(),
                name: p.name().to_string_lossy().to_string(),
                cpu: p.cpu_usage(),
                mem_bytes: p.memory(),
            })
            .collect();
        out.sort_by_key(|p| p.pid);
        Ok(out)
    }

    fn info(&self, pid: u32) -> Result<ProcessInfo> {
        let mut sys = System::new_all();
        sys.refresh_all();
        sys.process(sysinfo::Pid::from_u32(pid))
            .map(|p| ProcessInfo {
                pid,
                name: p.name().to_string_lossy().to_string(),
                cpu: p.cpu_usage(),
                mem_bytes: p.memory(),
            })
            .ok_or_else(|| KongtrolError::NotFound {
                what: format!("pid {pid}"),
            })
    }

    fn kill(&self, _pid: u32, _signal: Option<&str>) -> Result<()> {
        // TODO(M2): DANGEROUS. Unix=nix kill(signal), Windows=windows crate. 결과 재확인.
        Err(unsupported("process kill (M2 예정)"))
    }
}

// ── M3~M5 미구현 trait stub (Unsupported 반환, 조용한 실패 금지) ──
use crate::core::{InputInjector, Scheduler, ServiceManager, ServiceInfo};

/// Scheduler stub(M4 예정).
pub struct UnsupportedScheduler;
impl Scheduler for UnsupportedScheduler {
    fn list(&self) -> Result<Vec<String>> {
        Err(unsupported("schedule (M4 예정)"))
    }
    fn add(&self, _name: &str, _cmd: &str, _cron: &str) -> Result<()> {
        Err(unsupported("schedule add (M4 예정)"))
    }
    fn remove(&self, _name: &str) -> Result<()> {
        Err(unsupported("schedule remove (M4 예정)"))
    }
}

/// InputInjector stub ★DANGEROUS(M5 예정, 최고위험 마지막).
pub struct UnsupportedInput;
impl InputInjector for UnsupportedInput {
    fn move_mouse(&self, _x: i32, _y: i32) -> Result<()> {
        Err(unsupported("input move (M5 예정)"))
    }
    fn click(&self, _button: &str) -> Result<()> {
        Err(unsupported("input click (M5 예정)"))
    }
    fn type_text(&self, _text: &str) -> Result<()> {
        Err(unsupported("input type (M5 예정)"))
    }
    fn key_combo(&self, _combo: &str) -> Result<()> {
        Err(unsupported("input key (M5 예정)"))
    }
}

/// ServiceManager stub(플랫폼 미분류 fallback).
pub struct UnsupportedService;
impl ServiceManager for UnsupportedService {
    fn list(&self) -> Result<Vec<ServiceInfo>> {
        Err(unsupported("service (M3 예정)"))
    }
    fn status(&self, _name: &str) -> Result<ServiceInfo> {
        Err(unsupported("service status (M3 예정)"))
    }
    fn start(&self, _name: &str) -> Result<()> {
        Err(unsupported("service start (M3 예정)"))
    }
    fn stop(&self, _name: &str) -> Result<()> {
        Err(unsupported("service stop (M3 예정)"))
    }
}

//! platform — cfg-gated 팩토리 (ADR 0002). 컴파일 타깃 OS 구현만 바이너리에 포함.
//! M0: SystemInfo·Process 조회는 common(sysinfo) 실동작, 나머지 trait 는 stub(Unsupported).
pub mod common;

#[cfg(target_os = "macos")]
pub mod macos;
#[cfg(target_os = "linux")]
pub mod linux;
#[cfg(target_os = "windows")]
pub mod windows;

use crate::core::{
    InputInjector, ProcessManager, Scheduler, ServiceManager, SystemInfo,
};

/// SystemInfo 팩토리(M1 실동작, 플랫폼 공통 sysinfo).
pub fn system_info() -> Box<dyn SystemInfo> {
    Box::new(common::SysInfoImpl)
}

/// ProcessManager 팩토리(조회 실동작, 제어 stub).
pub fn process_manager() -> Box<dyn ProcessManager> {
    Box::new(common::ProcImpl)
}

/// ServiceManager 팩토리(M3). 현재 전 플랫폼 stub.
pub fn service_manager() -> Box<dyn ServiceManager> {
    #[cfg(target_os = "macos")]
    {
        Box::new(macos::MacServiceStub)
    }
    #[cfg(target_os = "linux")]
    {
        Box::new(linux::LinuxServiceStub)
    }
    #[cfg(target_os = "windows")]
    {
        Box::new(windows::WinServiceStub)
    }
    #[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
    {
        Box::new(common::UnsupportedService)
    }
}

/// Scheduler 팩토리(M4). stub.
pub fn scheduler() -> Box<dyn Scheduler> {
    Box::new(common::UnsupportedScheduler)
}

/// InputInjector 팩토리 ★DANGEROUS(M5, 최고위험 마지막). stub.
pub fn input_injector() -> Box<dyn InputInjector> {
    Box::new(common::UnsupportedInput)
}

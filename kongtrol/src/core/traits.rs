//! core domain trait 5종 (ADR 0002). CLI 핸들러는 trait 만 알고 OS 구현을 모름(의존성 역전).
//! R1~R5 가 각각 하나의 trait 슬롯에 "어떤 라이브러리/API로 구현하나"만 채운다.
//! M0 = trait 정의만. 구현은 platform/* stub(Unsupported) → M1+ 에서 채움.
use super::error::Result;
use super::types::{ProcessInfo, ServiceInfo, SysSummary};

/// R5 — 시스템 정보 조회(READ). M1 첫 구현 대상.
pub trait SystemInfo {
    fn summary(&self) -> Result<SysSummary>;
}

/// R1 — 프로세스 조회·제어. 조회=sysinfo, 제어(kill/signal/priority)=nix/windows(M2).
pub trait ProcessManager {
    fn list(&self) -> Result<Vec<ProcessInfo>>;
    fn info(&self, pid: u32) -> Result<ProcessInfo>;
    /// DANGEROUS(0004 게이트). M2.
    fn kill(&self, pid: u32, signal: Option<&str>) -> Result<()>;
}

/// R2 — 서비스/데몬(service-manager). M3.
pub trait ServiceManager {
    fn list(&self) -> Result<Vec<ServiceInfo>>;
    fn status(&self, name: &str) -> Result<ServiceInfo>;
    fn start(&self, name: &str) -> Result<()>;
    /// DANGEROUS(0004). M3.
    fn stop(&self, name: &str) -> Result<()>;
}

/// R3 — 스케줄러(OS 네이티브 + croner 계산). M4.
pub trait Scheduler {
    fn list(&self) -> Result<Vec<String>>;
    fn add(&self, name: &str, cmd: &str, cron: &str) -> Result<()>;
    /// DANGEROUS(0004). M4.
    fn remove(&self, name: &str) -> Result<()>;
}

/// R5 — 입력 주입 ★DANGEROUS(enigo). 최고위험, M5(마지막).
/// ★입력 신뢰 금지(0004): 인자는 이벤트 API 로 직접 전달, 셸 문자열 재구성 금지.
pub trait InputInjector {
    fn move_mouse(&self, x: i32, y: i32) -> Result<()>;
    fn click(&self, button: &str) -> Result<()>;
    fn type_text(&self, text: &str) -> Result<()>;
    fn key_combo(&self, combo: &str) -> Result<()>;
}

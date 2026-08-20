//! 도메인 타입 · 위험 등급 (ADR 0003 위험등급 태깅, ADR 0002 도메인 타입).
use serde::Serialize;

/// 명령 위험 등급(ADR 0003). DANGEROUS = 0004 4중 방어 게이트 강제.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum RiskLevel {
    /// 조회 전용(list/info/status). 게이트 없음.
    Read,
    /// 상태 변경(start/enable/add). 경고.
    Mutate,
    /// 파괴적/고위험(kill/stop/remove/input). 4중 방어(0004).
    Dangerous,
}

impl RiskLevel {
    pub fn label(&self) -> &'static str {
        match self {
            RiskLevel::Read => "READ",
            RiskLevel::Mutate => "MUTATE",
            RiskLevel::Dangerous => "DANGEROUS",
        }
    }
}

/// 프로세스 요약(ProcessManager 조회 결과, M1에서 채움).
#[derive(Debug, Clone, Serialize)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: String,
    pub cpu: f32,
    pub mem_bytes: u64,
}

/// 시스템 정보 요약(SystemInfo, M1).
#[derive(Debug, Clone, Serialize)]
pub struct SysSummary {
    pub os: String,
    pub kernel: String,
    pub cpu_count: usize,
    pub mem_total_bytes: u64,
}

/// 서비스 상태(ServiceManager, M3).
#[derive(Debug, Clone, Serialize)]
pub struct ServiceInfo {
    pub name: String,
    pub running: bool,
    pub enabled: bool,
}

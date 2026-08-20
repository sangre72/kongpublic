//! core — 플랫폼 무관 trait · 도메인 타입 · error · security 정책 (ADR 0002 그릇).
pub mod error;
pub mod perception;
pub mod security;
pub mod traits;
pub mod types;

pub use error::{KongtrolError, Result, unsupported};
#[allow(unused_imports)]
pub use error::Platform; // M1+ 공개 API 슬롯(현재 내부 error.rs 에서만 사용).
pub use perception::{DecisionEngine, Frame, GridSpec, Region, ScreenSensor};
pub use traits::{InputInjector, ProcessManager, Scheduler, ServiceManager, SystemInfo};
pub use types::{ProcessInfo, RiskLevel, ServiceInfo, SysSummary};

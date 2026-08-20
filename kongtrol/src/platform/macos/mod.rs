//! macOS platform — launchd·CGEventPost·libproc (ADR 0002). M0=service stub, M3+ 실装.
use crate::core::{Result, ServiceInfo, ServiceManager, unsupported};

/// macOS ServiceManager stub → M3에서 launchd(bootstrap/bootout) 실装.
pub struct MacServiceStub;
impl ServiceManager for MacServiceStub {
    fn list(&self) -> Result<Vec<ServiceInfo>> {
        Err(unsupported("service list (macOS launchd, M3 예정)"))
    }
    fn status(&self, _name: &str) -> Result<ServiceInfo> {
        Err(unsupported("service status (macOS, M3 예정)"))
    }
    fn start(&self, _name: &str) -> Result<()> {
        Err(unsupported("service start (macOS, M3 예정)"))
    }
    fn stop(&self, _name: &str) -> Result<()> {
        Err(unsupported("service stop (macOS, M3 예정)"))
    }
}

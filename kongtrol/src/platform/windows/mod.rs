//! Windows platform — SCM·SendInput·WinAPI (ADR 0002). M0=service stub, M3+ 실装.
use crate::core::{Result, ServiceInfo, ServiceManager, unsupported};

/// Windows ServiceManager stub → M3에서 SCM(Service Control API) 실装.
pub struct WinServiceStub;
impl ServiceManager for WinServiceStub {
    fn list(&self) -> Result<Vec<ServiceInfo>> {
        Err(unsupported("service list (Windows SCM, M3 예정)"))
    }
    fn status(&self, _name: &str) -> Result<ServiceInfo> {
        Err(unsupported("service status (Windows, M3 예정)"))
    }
    fn start(&self, _name: &str) -> Result<()> {
        Err(unsupported("service start (Windows, M3 예정)"))
    }
    fn stop(&self, _name: &str) -> Result<()> {
        Err(unsupported("service stop (Windows, M3 예정)"))
    }
}

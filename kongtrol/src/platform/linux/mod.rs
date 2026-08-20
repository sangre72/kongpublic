//! Linux platform — systemd(D-Bus)·XTest·uinput/libei (ADR 0002). M0=service stub, M3+ 실装.
use crate::core::{Result, ServiceInfo, ServiceManager, unsupported};

/// Linux ServiceManager stub → M3에서 systemd(D-Bus) 실装.
pub struct LinuxServiceStub;
impl ServiceManager for LinuxServiceStub {
    fn list(&self) -> Result<Vec<ServiceInfo>> {
        Err(unsupported("service list (Linux systemd, M3 예정)"))
    }
    fn status(&self, _name: &str) -> Result<ServiceInfo> {
        Err(unsupported("service status (Linux, M3 예정)"))
    }
    fn start(&self, _name: &str) -> Result<()> {
        Err(unsupported("service start (Linux, M3 예정)"))
    }
    fn stop(&self, _name: &str) -> Result<()> {
        Err(unsupported("service stop (Linux, M3 예정)"))
    }
}

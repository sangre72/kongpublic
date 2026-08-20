//! kongtrol 공통 에러 · 플랫폼 열거 (ADR 0002 §미지원 규칙, ADR 0003 exit code).
use std::fmt;

/// 지원 플랫폼. 미지원 기능은 `KongtrolError::Unsupported` 로 반환(조용한 실패 금지).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Platform {
    MacOS,
    Linux,
    Windows,
    Unknown,
}

impl Platform {
    /// 컴파일 타깃 기준 현재 플랫폼(cfg 게이팅).
    pub const fn current() -> Self {
        #[cfg(target_os = "macos")]
        {
            Platform::MacOS
        }
        #[cfg(target_os = "linux")]
        {
            Platform::Linux
        }
        #[cfg(target_os = "windows")]
        {
            Platform::Windows
        }
        #[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
        {
            Platform::Unknown
        }
    }
}

impl fmt::Display for Platform {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match self {
            Platform::MacOS => "macos",
            Platform::Linux => "linux",
            Platform::Windows => "windows",
            Platform::Unknown => "unknown",
        };
        f.write_str(s)
    }
}

/// kongtrol 전역 에러. `code()` 는 ADR 0003 exit code 규약과 매핑.
#[derive(Debug)]
pub enum KongtrolError {
    /// 사용자 거부(확인 프롬프트 No). exit 2.
    UserDeclined,
    /// 권한 부족(승격 필요). exit 3.
    PermissionDenied { detail: String },
    /// 대상 없음(프로세스/서비스 등). exit 4.
    NotFound { what: String },
    /// 플랫폼/기능 미지원. exit 5. ★추측·무시 금지.
    Unsupported { platform: Platform, feature: String },
    /// 그 외 내부 오류. exit 1.
    Internal { detail: String },
}

impl KongtrolError {
    /// ADR 0003 exit code 규약: 0=성공 / 2=거부 / 3=권한 / 4=대상없음 / 5=미지원 / 1=기타.
    pub fn code(&self) -> i32 {
        match self {
            KongtrolError::UserDeclined => 2,
            KongtrolError::PermissionDenied { .. } => 3,
            KongtrolError::NotFound { .. } => 4,
            KongtrolError::Unsupported { .. } => 5,
            KongtrolError::Internal { .. } => 1,
        }
    }

    /// `--json` 에러 envelope 의 machine-readable code.
    pub fn kind(&self) -> &'static str {
        match self {
            KongtrolError::UserDeclined => "user_declined",
            KongtrolError::PermissionDenied { .. } => "permission_denied",
            KongtrolError::NotFound { .. } => "not_found",
            KongtrolError::Unsupported { .. } => "unsupported",
            KongtrolError::Internal { .. } => "internal",
        }
    }
}

impl fmt::Display for KongtrolError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            KongtrolError::UserDeclined => write!(f, "사용자가 작업을 거부했습니다"),
            KongtrolError::PermissionDenied { detail } => {
                write!(f, "권한 부족: {detail}")
            }
            KongtrolError::NotFound { what } => write!(f, "대상 없음: {what}"),
            KongtrolError::Unsupported { platform, feature } => {
                write!(f, "{platform} 에서 미지원 기능: {feature}")
            }
            KongtrolError::Internal { detail } => write!(f, "내부 오류: {detail}"),
        }
    }
}

impl std::error::Error for KongtrolError {}

/// 편의: 현재 플랫폼에서 미지원 에러 생성.
pub fn unsupported(feature: &str) -> KongtrolError {
    KongtrolError::Unsupported {
        platform: Platform::current(),
        feature: feature.to_string(),
    }
}

pub type Result<T> = std::result::Result<T, KongtrolError>;

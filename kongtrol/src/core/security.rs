//! 보안 정책 스텁 (ADR 0004). M0=자리확보, M2에서 4중 방어 실装.
//! 4중 방어: ①확인 프롬프트 ②--yes 명시 ③--dry-run ④audit log(항상).
use super::error::{KongtrolError, Result};
use super::types::RiskLevel;

/// DANGEROUS 명령 실행 전 게이트(0004 4중 방어). M0=골격, M2에서 확인/audit 채움.
pub struct Gate {
    pub yes: bool,
    pub dry_run: bool,
}

impl Gate {
    pub fn new(yes: bool, dry_run: bool) -> Self {
        Self { yes, dry_run }
    }

    /// 위험 등급에 따라 실행 허용 여부 판정.
    /// M0 스텁: DANGEROUS + 비대화(--yes 없음)면 거부(exit 2 자리). 확인 프롬프트·audit 는 M2.
    pub fn check(&self, risk: RiskLevel, _action: &str) -> Result<()> {
        match risk {
            RiskLevel::Read | RiskLevel::Mutate => Ok(()),
            RiskLevel::Dangerous => {
                // TODO(M2): 대화형 확인 프롬프트 + audit append-only 로그.
                if self.yes {
                    Ok(())
                } else {
                    Err(KongtrolError::UserDeclined)
                }
            }
        }
    }
}

/// audit 로그 스텁(0004 ④, append-only). M2에서 who/when/cmd/args/결과/승격 기록.
pub fn audit(_action: &str, _args: &str) {
    // TODO(M2): directories config 경로 하위 append-only 파일에 기록.
}

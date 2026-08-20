//! 출력 포맷 (ADR 0003): 사람용 테이블(comfy-table) + 기계용 JSON envelope.
use crate::core::KongtrolError;
use serde::Serialize;
use serde_json::json;

/// `--json` 성공 envelope: `{ "data": ..., "meta": { "requestId": ... } }`.
pub fn json_ok<T: Serialize>(data: &T, request_id: &str) {
    let env = json!({ "data": data, "meta": { "requestId": request_id } });
    println!("{}", serde_json::to_string_pretty(&env).unwrap_or_default());
}

/// `--json` 에러 envelope: `{ "error": { "code", "message", "requestId" } }`.
pub fn json_err(err: &KongtrolError, request_id: &str) {
    let env = json!({
        "error": { "code": err.kind(), "message": err.to_string(), "requestId": request_id }
    });
    eprintln!("{}", serde_json::to_string_pretty(&env).unwrap_or_default());
}

/// 사람용 에러 출력(색상+텍스트 라벨 병기는 M1+; M0=텍스트).
pub fn human_err(err: &KongtrolError) {
    eprintln!("오류: {err}");
}

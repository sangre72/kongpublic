//! 로컬 VL(vision-language) 서버 연동(a_922/934). 스샷→640px 리사이즈→base64→로컬LLM 판단 위임.
//! ★unlabeled 보조수단(docs/appkb/unexpected-state.md 원칙과 일관) — a11y 우선, VL은 라벨 없는
//!   캔버스 렌더링 UI(CapCut 등)에서만 최소 사용. ar_926 실측: 640px가 속도(1.0s)·정확도 최적.
use crate::core::{KongtrolError, Result, ScreenSensor};
use crate::perception::sensor::XcapSensor;
use base64::Engine;

const VL_ENDPOINT: &str = "http://192.168.45.183:8000/v1/chat/completions";
const VL_MODEL: &str = "cpatonn/Qwen3-VL-8B-Instruct-AWQ-4bit";
const RESIZE_WIDTH: u32 = 640;

/// 화면 캡처 → 640px 리사이즈 → 로컬 VL 서버에 프롬프트와 함께 전송 → 응답 텍스트 반환.
/// 로컬서버 다운/타임아웃 시 에러 반환(크래시 금지, graceful fallback).
pub fn ask_vl(prompt: &str) -> Result<String> {
    let sensor = XcapSensor;
    let frame = sensor.capture(None)?;

    let img = image::RgbaImage::from_raw(frame.width, frame.height, frame.pixels).ok_or_else(
        || KongtrolError::Internal { detail: "프레임→이미지 변환 실패".into() },
    )?;
    let dynamic = image::DynamicImage::ImageRgba8(img);
    let resized = dynamic.resize(
        RESIZE_WIDTH,
        RESIZE_WIDTH * dynamic.height() / dynamic.width().max(1),
        image::imageops::FilterType::Triangle,
    );

    let mut png_bytes: Vec<u8> = Vec::new();
    resized
        .write_to(&mut std::io::Cursor::new(&mut png_bytes), image::ImageFormat::Png)
        .map_err(|e| KongtrolError::Internal { detail: format!("PNG 인코딩 실패: {e}") })?;
    let b64 = base64::engine::general_purpose::STANDARD.encode(&png_bytes);

    let payload = serde_json::json!({
        "model": VL_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                { "type": "text", "text": prompt },
                { "type": "image_url", "image_url": { "url": format!("data:image/png;base64,{b64}") } }
            ]
        }],
        "max_tokens": 300
    });

    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()
        .map_err(|e| KongtrolError::Internal { detail: format!("HTTP 클라이언트 생성 실패: {e}") })?;

    let resp = client
        .post(VL_ENDPOINT)
        .json(&payload)
        .send()
        .map_err(|e| KongtrolError::Internal { detail: format!("VL 서버 연결 실패({VL_ENDPOINT}): {e}") })?;

    if !resp.status().is_success() {
        return Err(KongtrolError::Internal {
            detail: format!("VL 서버 응답 오류: HTTP {}", resp.status()),
        });
    }

    let body: serde_json::Value = resp
        .json()
        .map_err(|e| KongtrolError::Internal { detail: format!("VL 응답 파싱 실패: {e}") })?;

    body["choices"][0]["message"]["content"]
        .as_str()
        .map(|s| s.to_string())
        .ok_or_else(|| KongtrolError::Internal { detail: "VL 응답에 content 없음".into() })
}

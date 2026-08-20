//! xcap 0.9.8 기반 ScreenSensor 구현 (ADR 0007). 화면 캡처 → Frame(RGBA).
//! ★macOS: 화면 기록 TCC 권한 필요. 미승인 시 검은/빈 화면 가능 → 호출부에서 감지.
use crate::core::{Frame, KongtrolError, Region, Result, ScreenSensor};

pub struct XcapSensor;

/// 파일 이미지 기반 ScreenSensor(ADR 0007). 실화면 캡처 대신 PNG 파일에서 Frame 생성.
/// 용도: 세션 GUI/디스플레이 제약 시 실제 격자 이미지로 인식·판단 파이프라인을 실증.
pub struct FileSensor {
    pub path: String,
}

impl ScreenSensor for FileSensor {
    fn capture(&self, region: Option<Region>) -> Result<Frame> {
        let img = image::open(&self.path)
            .map_err(|e| KongtrolError::NotFound {
                what: format!("이미지 파일 {} ({e})", self.path),
            })?
            .to_rgba8();
        let (w, h) = (img.width(), img.height());
        let full = Frame { width: w, height: h, pixels: img.into_raw() };
        match region {
            None => Ok(full),
            Some(r) => Ok(crop(&full, r)),
        }
    }
}

impl ScreenSensor for XcapSensor {
    fn capture(&self, region: Option<Region>) -> Result<Frame> {
        let monitors = xcap::Monitor::all().map_err(|e| KongtrolError::Internal {
            detail: format!("monitor 열거 실패: {e}"),
        })?;
        let mon = monitors.first().ok_or_else(|| KongtrolError::NotFound {
            what: "모니터".into(),
        })?;
        let img = mon.capture_image().map_err(|e| KongtrolError::Internal {
            detail: format!("캡처 실패(화면기록 TCC 권한 확인): {e}"),
        })?;
        let (fw, fh) = (img.width(), img.height());
        let full = Frame {
            width: fw,
            height: fh,
            pixels: img.into_raw(),
        };
        match region {
            None => Ok(full),
            Some(r) => Ok(crop(&full, r)),
        }
    }
}

/// Frame 을 Region 으로 크롭(격자 영역만).
fn crop(src: &Frame, r: Region) -> Frame {
    let x0 = r.x.max(0) as u32;
    let y0 = r.y.max(0) as u32;
    let w = r.w.min(src.width.saturating_sub(x0));
    let h = r.h.min(src.height.saturating_sub(y0));
    let mut pixels = Vec::with_capacity((w * h * 4) as usize);
    for y in y0..y0 + h {
        for x in x0..x0 + w {
            if let Some((r_, g, b)) = src.rgb(x, y) {
                pixels.extend_from_slice(&[r_, g, b, 255]);
            } else {
                pixels.extend_from_slice(&[0, 0, 0, 255]);
            }
        }
    }
    Frame { width: w, height: h, pixels }
}

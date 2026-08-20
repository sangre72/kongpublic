//! ADR 0007 — perception-decision-loop core trait 2종 + 타입.
//! ScreenSensor(화면 캡처+상태추출) · DecisionEngine(룰/휴리스틱 판단).
use super::error::Result;

/// 화면 영역(캡처 대상). None=전체 화면.
#[derive(Debug, Clone, Copy)]
pub struct Region {
    pub x: i32,
    pub y: i32,
    pub w: u32,
    pub h: u32,
}

/// 캡처된 프레임(RGBA 픽셀 버퍼).
pub struct Frame {
    pub width: u32,
    pub height: u32,
    /// RGBA8, row-major.
    pub pixels: Vec<u8>,
}

impl Frame {
    /// (x,y) 픽셀의 RGB 반환(범위 밖=None).
    pub fn rgb(&self, x: u32, y: u32) -> Option<(u8, u8, u8)> {
        if x >= self.width || y >= self.height {
            return None;
        }
        let i = ((y * self.width + x) * 4) as usize;
        Some((self.pixels[i], self.pixels[i + 1], self.pixels[i + 2]))
    }
}

/// 격자 스펙(좌상단 원점 + 셀 크기 + 행/열). 좌표격자 산술의 기준(ADR 0007 §2).
#[derive(Debug, Clone, Copy)]
pub struct GridSpec {
    pub origin_x: u32,
    pub origin_y: u32,
    pub cell: u32,
    pub cols: u32,
    pub rows: u32,
}

impl GridSpec {
    /// (row,col) 셀 중심의 프레임 픽셀 좌표.
    pub fn cell_center(&self, row: u32, col: u32) -> (u32, u32) {
        (
            self.origin_x + col * self.cell + self.cell / 2,
            self.origin_y + row * self.cell + self.cell / 2,
        )
    }
}

/// R7 — 화면 인식: 캡처 + 상태 추출(ADR 0007 ScreenSensor).
pub trait ScreenSensor {
    fn capture(&self, region: Option<Region>) -> Result<Frame>;
}

/// R7 — 판단: 상태 → 다음 액션(ADR 0007 DecisionEngine). 게임별 플러그인이 impl.
pub trait DecisionEngine {
    type State;
    type Action;
    /// 프레임+격자 → 게임 상태 추출(좌표격자+픽셀색).
    fn extract_state(&self, frame: &Frame, grid: &GridSpec) -> Result<Self::State>;
    /// 상태 → 다음 액션(룰/휴리스틱). 확정 수 없으면 None(추측 필요).
    fn decide(&self, state: &Self::State) -> Result<Option<Self::Action>>;
}

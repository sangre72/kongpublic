//! 지뢰찾기 플러그인 (ADR 0007 DecisionEngine). 격자 픽셀색 인식 + 기초룰 solver.
//! ★대상 = 네이티브 지뢰찾기 앱(브라우저 아님). GAME-LITMUS §3 기초룰+CSP 중 기초룰.
use crate::core::{DecisionEngine, Frame, GridSpec, Result};

/// 셀 상태. 숫자(1~8)·빈칸·닫힘·깃발·지뢰.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Cell {
    Closed,
    Empty,       // 열린 0
    Number(u8),  // 열린 1~8
    Flag,
    Unknown,
}

/// 지뢰찾기 보드 상태.
pub struct Board {
    pub rows: u32,
    pub cols: u32,
    pub cells: Vec<Cell>, // row-major
}

impl Board {
    pub fn at(&self, r: u32, c: u32) -> Cell {
        self.cells[(r * self.cols + c) as usize]
    }
    fn neighbors(&self, r: u32, c: u32) -> Vec<(u32, u32)> {
        let mut v = Vec::new();
        for dr in -1i32..=1 {
            for dc in -1i32..=1 {
                if dr == 0 && dc == 0 {
                    continue;
                }
                let nr = r as i32 + dr;
                let nc = c as i32 + dc;
                if nr >= 0 && nr < self.rows as i32 && nc >= 0 && nc < self.cols as i32 {
                    v.push((nr as u32, nc as u32));
                }
            }
        }
        v
    }
}

/// 액션: 좌클릭(열기)·우클릭(깃발) 할 셀(row,col).
#[derive(Debug, Clone, Copy)]
pub enum MsAction {
    Open(u32, u32),
    Flag(u32, u32),
}

/// 셀 중심 픽셀색 → Cell 분류. 색 임계값은 대상 앱에 맞게 설정(기본=관용 지뢰찾기 색).
pub struct MinesweeperEngine {
    /// 닫힘 셀 배경색(회색 계열). RGB.
    pub closed_rgb: (u8, u8, u8),
    /// 색 매칭 허용 오차.
    pub tol: u8,
}

impl Default for MinesweeperEngine {
    fn default() -> Self {
        // 관용 지뢰찾기: 닫힘=진회색, 열림=밝은회색, 숫자색 1=파랑 2=초록 3=빨강...
        Self { closed_rgb: (160, 160, 160), tol: 40 }
    }
}

impl MinesweeperEngine {
    fn near(&self, a: (u8, u8, u8), b: (u8, u8, u8)) -> bool {
        let d = |x: u8, y: u8| (x as i32 - y as i32).unsigned_abs();
        d(a.0, b.0) <= self.tol as u32 && d(a.1, b.1) <= self.tol as u32 && d(a.2, b.2) <= self.tol as u32
    }

    /// 픽셀색 → 숫자색 매핑(1=파랑,2=초록,3=빨강,4=남색). 관용 지뢰찾기 팔레트.
    fn number_of(&self, rgb: (u8, u8, u8)) -> Option<u8> {
        let palette: [((u8, u8, u8), u8); 4] = [
            ((0, 0, 255), 1),
            ((0, 128, 0), 2),
            ((255, 0, 0), 3),
            ((0, 0, 128), 4),
        ];
        for (c, n) in palette {
            if self.near(rgb, c) {
                return Some(n);
            }
        }
        None
    }
}

impl DecisionEngine for MinesweeperEngine {
    type State = Board;
    type Action = MsAction;

    /// 프레임+격자 → Board. ★셀 중앙 소영역(±cell/6) 다중 샘플로 분류.
    ///  단일 픽셀 샘플은 격자 원점 ±수px 오차(locator 자동탐지)나 격자선에 걸리면 오판 →
    ///  중앙부 여러 점을 보고 [숫자색 발견 우선 / 아니면 배경 다수결(닫힘 vs 열림)]으로 견고화.
    fn extract_state(&self, frame: &Frame, grid: &GridSpec) -> Result<Board> {
        let mut cells = Vec::with_capacity((grid.rows * grid.cols) as usize);
        let rad = (grid.cell / 6).max(1); // 중앙 샘플 반경.
        for r in 0..grid.rows {
            for c in 0..grid.cols {
                let (cx, cy) = grid.cell_center(r, c);
                let (mut num, mut closed, mut bright, mut total) = (None, 0u32, 0u32, 0u32);
                // 중앙부 3x3 격자점 샘플(rad 간격).
                for dy in [-(rad as i32), 0, rad as i32] {
                    for dx in [-(rad as i32), 0, rad as i32] {
                        let sx = (cx as i32 + dx).max(0) as u32;
                        let sy = (cy as i32 + dy).max(0) as u32;
                        let rgb = frame.rgb(sx, sy).unwrap_or((0, 0, 0));
                        total += 1;
                        if let Some(n) = self.number_of(rgb) {
                            num = Some(n); // 숫자색은 소수 픽셀에만 → 하나라도 발견 우선.
                        } else if self.near(rgb, self.closed_rgb) {
                            closed += 1;
                        } else if rgb.0 as u32 + rgb.1 as u32 + rgb.2 as u32 > 600 {
                            bright += 1;
                        }
                    }
                }
                let cell = if let Some(n) = num {
                    Cell::Number(n)
                } else if closed * 2 >= total {
                    Cell::Closed
                } else if bright * 2 >= total {
                    Cell::Empty
                } else {
                    Cell::Unknown
                };
                cells.push(cell);
            }
        }
        Ok(Board { rows: grid.rows, cols: grid.cols, cells })
    }

    /// 기초 제약룰(GAME-LITMUS §3-a): 열린 숫자셀 주변으로 안전셀/지뢰 결정.
    ///  - 인접 지뢰수 == 인접 깃발수 → 나머지 닫힘 셀은 안전(Open).
    ///  - 인접 지뢰수 - 깃발수 == 남은 닫힘수 → 남은 닫힘 전부 지뢰(Flag).
    fn decide(&self, board: &Board) -> Result<Option<MsAction>> {
        for r in 0..board.rows {
            for c in 0..board.cols {
                if let Cell::Number(n) = board.at(r, c) {
                    let nb = board.neighbors(r, c);
                    let flags = nb.iter().filter(|(a, b)| board.at(*a, *b) == Cell::Flag).count() as u8;
                    let closed: Vec<_> = nb.iter().filter(|(a, b)| board.at(*a, *b) == Cell::Closed).collect();
                    if closed.is_empty() {
                        continue;
                    }
                    // 규칙1: 지뢰수=깃발수 → 나머지 닫힘 안전
                    if n == flags {
                        let (tr, tc) = closed[0];
                        return Ok(Some(MsAction::Open(*tr, *tc)));
                    }
                    // 규칙2: 지뢰수-깃발수 = 남은닫힘수 → 전부 지뢰
                    if n.saturating_sub(flags) as usize == closed.len() {
                        let (tr, tc) = closed[0];
                        return Ok(Some(MsAction::Flag(*tr, *tc)));
                    }
                }
            }
        }
        // 오프닝 무브(첫 수): 확정 룰로 둘 수 없음 AND 아직 열린 셀이 하나도 없음(전부 Closed).
        // 첫 수 = 정보 0 → 관용상 중앙 오픈으로 게임 시작(정보를 만들어 확정 룰이 돌기 시작).
        // ★열린 셀이 있는데도 확정 없음 → 아래로 안 내려가고 None(추측 회피, 종료).
        let any_opened = board
            .cells
            .iter()
            .any(|c| matches!(c, Cell::Number(_) | Cell::Empty));
        if !any_opened {
            let (mr, mc) = (board.rows / 2, board.cols / 2);
            return Ok(Some(MsAction::Open(mr, mc)));
        }
        Ok(None) // 확정 수 없음(추측 필요 — 확률계층 미구현, GAME-LITMUS §3-c는 향후)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{DecisionEngine, Frame, GridSpec};

    /// 합성 프레임 생성: 각 셀 중심에 지정 RGB 채운 격자.
    fn frame_from(cells_rgb: &[&[(u8, u8, u8)]], cell: u32) -> (Frame, GridSpec) {
        let rows = cells_rgb.len() as u32;
        let cols = cells_rgb[0].len() as u32;
        let (w, h) = (cols * cell, rows * cell);
        let mut px = vec![0u8; (w * h * 4) as usize];
        for (r, row) in cells_rgb.iter().enumerate() {
            for (c, &(rr, gg, bb)) in row.iter().enumerate() {
                // 셀 전체를 그 색으로(중심 샘플이 잡히게)
                for yy in 0..cell {
                    for xx in 0..cell {
                        let x = c as u32 * cell + xx;
                        let y = r as u32 * cell + yy;
                        let i = ((y * w + x) * 4) as usize;
                        px[i] = rr; px[i + 1] = gg; px[i + 2] = bb; px[i + 3] = 255;
                    }
                }
            }
        }
        let grid = GridSpec { origin_x: 0, origin_y: 0, cell, cols, rows };
        (Frame { width: w, height: h, pixels: px }, grid)
    }

    #[test]
    fn extract_classifies_cells_by_color() {
        // 1행: 숫자1(파랑)·닫힘(회색)·빈칸(밝음)
        let blue = (0, 0, 255);
        let gray = (160, 160, 160);
        let bright = (240, 240, 240);
        let (frame, grid) = frame_from(&[&[blue, gray, bright]], 20);
        let eng = MinesweeperEngine::default();
        let board = eng.extract_state(&frame, &grid).unwrap();
        assert_eq!(board.at(0, 0), Cell::Number(1), "파랑=숫자1");
        assert_eq!(board.at(0, 1), Cell::Closed, "회색=닫힘");
        assert_eq!(board.at(0, 2), Cell::Empty, "밝음=빈칸");
    }

    #[test]
    fn rule1_number_equals_flags_opens_rest() {
        // 규칙1: 숫자셀의 인접 지뢰수 == 인접 깃발수 → 나머지 닫힘 안전(Open).
        // 2x2 배치: (0,0)=Number(1) 의 이웃 (0,1)=Flag·(1,0)=Closed·(1,1)=Empty.
        // 지뢰수1 == 깃발수1 → 닫힘 (1,0) 은 안전 → Open(1,0).
        let eng = MinesweeperEngine::default();
        let board = Board {
            rows: 2,
            cols: 2,
            cells: vec![Cell::Number(1), Cell::Flag, Cell::Closed, Cell::Empty],
        };
        match eng.decide(&board).unwrap() {
            Some(MsAction::Open(1, 0)) => {}
            other => panic!("규칙1 기대(Open 1,0), 실제 {other:?}"),
        }
    }

    #[test]
    fn opening_move_opens_center_when_all_closed() {
        // 오프닝 무브: 전부 닫힘(열린 셀 0) → 확정 수 없음 → 중앙 셀 Open 으로 게임 시작.
        // 3x3 전부 Closed → 중앙 (1,1) Open.
        let eng = MinesweeperEngine::default();
        let board = Board { rows: 3, cols: 3, cells: vec![Cell::Closed; 9] };
        match eng.decide(&board).unwrap() {
            Some(MsAction::Open(1, 1)) => {}
            other => panic!("오프닝무브 기대(Open 1,1 중앙), 실제 {other:?}"),
        }
    }

    #[test]
    fn no_opening_when_already_opened_and_unresolved() {
        // 열린 셀이 있는데 확정 룰로 못 풀면 → None(추측 회피). 오프닝 무브 재발동 금지.
        // 2x2: (0,0)=Number(1) 인접 닫힘 2·깃발 0 → 규칙1/2 미해당 → 열린셀 존재 → None.
        let eng = MinesweeperEngine::default();
        let board = Board {
            rows: 2,
            cols: 2,
            cells: vec![Cell::Number(1), Cell::Closed, Cell::Closed, Cell::Closed],
        };
        assert!(
            eng.decide(&board).unwrap().is_none(),
            "열린셀 있고 확정 없음 → None(추측 회피, 오프닝 재발동 안 함)"
        );
    }

    #[test]
    fn rule2_all_remaining_are_mines() {
        // 규칙2: 지뢰수 - 깃발수 == 남은 닫힘수 → 닫힘 전부 지뢰(Flag).
        // 2x2: (0,0)=Number(2), 이웃 (0,1)=Closed·(1,0)=Closed·(1,1)=Empty.
        // 지뢰수2 - 깃발0 == 닫힘2 → 닫힘 전부 지뢰 → Flag.
        let eng = MinesweeperEngine::default();
        let board = Board {
            rows: 2,
            cols: 2,
            cells: vec![Cell::Number(2), Cell::Closed, Cell::Closed, Cell::Empty],
        };
        match eng.decide(&board).unwrap() {
            Some(MsAction::Flag(..)) => {}
            other => panic!("규칙2 기대(Flag), 실제 {other:?}"),
        }
    }
}

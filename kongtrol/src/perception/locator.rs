//! locator — 화면 픽셀만으로 대상 앱 창·격자를 스스로 탐지 (ADR 0007 확장, u_15).
//! ★"좌표 받아쓰기"(--win·app_geom.json) 폐기 → 사람이 눈으로 찾듯 전체화면을 보고 격자를 찾음.
//! 방법 = [색 세그멘테이션 + 격자선 주기성]. 지뢰찾기·테트리스 등 격자성 강한 대상에 견고.
//! 창이 어디 있든·이동해도 픽셀 특징으로 재탐지. 못 찾으면 명확히 None(추측 금지).
use crate::core::{Frame, GridSpec, Region};

/// 탐지 결과: 대상 창 영역 + 격자 스펙(자동 산출) + 신뢰도(0~1).
#[derive(Debug, Clone)]
pub struct Detection {
    pub region: Region,
    pub grid: GridSpec,
    pub confidence: f32,
}

/// 격자 탐지기. 대상 팔레트(닫힘 셀 배경색 등)를 기준으로 격자형 영역을 찾는다.
/// ★minesweeper 색판정과 팔레트 공유(중복정의 금지, 3R): closed_rgb·tol 을 주입받는다.
pub struct GridLocator {
    /// 대상 배경색(격자 셀의 지배색). 지뢰찾기=닫힘 회색(160). 테트리스=보드 배경.
    pub target_rgb: (u8, u8, u8),
    /// 색 매칭 허용 오차.
    pub tol: u8,
    /// 다운샘플 간격(px). 전체화면 스캔 비용↓(예 2=격행격열). 정밀도와 트레이드.
    pub step: u32,
    /// ★무채색 모드: 켜면 [R≈G≈B 이고 명도 gray_lo~gray_hi]인 픽셀 전부를 타겟으로.
    ///   지뢰찾기=닫힘(160)·열림(240)·격자선(128) 모두 무채색 → 플레이가 진행돼 셀이 열려도
    ///   격자 [전체]를 창으로 잡음(닫힘색만 보면 열린셀 많아질 때 창을 부분만 잡는 버그 방지).
    pub grayscale: bool,
    pub gray_lo: u8,
    pub gray_hi: u8,
}

impl GridLocator {
    /// 지뢰찾기용 기본값. ★무채색 모드 ON(닫힘·열림·격자선 명도 120~250 무채색 전부 타겟).
    pub fn minesweeper() -> Self {
        Self { target_rgb: (160, 160, 160), tol: 40, step: 2, grayscale: true, gray_lo: 120, gray_hi: 250 }
    }

    fn near(&self, a: (u8, u8, u8)) -> bool {
        if self.grayscale {
            // 무채색(채널 최대-최소 차 작음) + 명도 범위.
            let mx = a.0.max(a.1).max(a.2);
            let mn = a.0.min(a.1).min(a.2);
            let lum = luma(a);
            return (mx - mn) <= 24 && lum >= self.gray_lo && lum <= self.gray_hi;
        }
        let b = self.target_rgb;
        let d = |x: u8, y: u8| (x as i32 - y as i32).unsigned_abs();
        d(a.0, b.0) <= self.tol as u32 && d(a.1, b.1) <= self.tol as u32 && d(a.2, b.2) <= self.tol as u32
    }

    /// 전체화면 Frame → 대상 격자 탐지. 없으면 None.
    /// ① 타겟색 픽셀 마스크 → ② 최대 연결영역 바운딩박스(=창 후보) → ③ 격자선 피치로 rows/cols 역산.
    pub fn locate(&self, frame: &Frame) -> Option<Detection> {
        let bbox = self.largest_target_bbox(frame)?;
        // 바운딩박스가 너무 작으면(노이즈) 기각.
        if bbox.w < 30 || bbox.h < 30 {
            return None;
        }
        // 격자 피치(셀 크기) 역산: bbox 내부 수평선의 경계(색 급변) 주기.
        let (cell, cols, rows, grid_conf) = self.infer_grid(frame, &bbox)?;
        // 창 영역 = bbox, 격자 원점 = bbox 좌상단.
        let region = Region { x: bbox.x, y: bbox.y, w: bbox.w, h: bbox.h };
        let grid = GridSpec { origin_x: bbox.x as u32, origin_y: bbox.y as u32, cell, cols, rows };
        // 신뢰도 = 격자 규칙성(피치 균일도) × 타겟색 채움비율.
        let fill = bbox.fill_ratio;
        let confidence = (grid_conf * 0.6 + fill * 0.4).clamp(0.0, 1.0);
        Some(Detection { region, grid, confidence })
    }

    /// 타겟색 픽셀의 최대 연결영역 바운딩박스(투영 히스토그램 기반 근사).
    /// 정밀 연결요소 대신, 타겟색 밀도가 높은 [행·열 구간]의 교집합으로 사각영역 산출(격자앱=사각).
    fn largest_target_bbox(&self, frame: &Frame) -> Option<BBox> {
        let (w, h) = (frame.width, frame.height);
        let s = self.step.max(1);
        // 행별·열별 타겟색 카운트(다운샘플).
        let mut row_cnt = vec![0u32; h as usize];
        let mut col_cnt = vec![0u32; w as usize];
        let mut total = 0u32;
        let mut y = 0;
        while y < h {
            let mut x = 0;
            while x < w {
                if let Some(rgb) = frame.rgb(x, y) {
                    if self.near(rgb) {
                        row_cnt[y as usize] += 1;
                        col_cnt[x as usize] += 1;
                        total += 1;
                    }
                }
                x += s;
            }
            y += s;
        }
        if total < 50 {
            return None; // 타겟색 거의 없음 → 대상 없음.
        }
        // 카운트가 임계 이상인 [연속 최대 구간] = 창의 세로/가로 범위.
        let row_thr = (row_cnt.iter().copied().max().unwrap_or(0) as f32 * 0.2) as u32;
        let col_thr = (col_cnt.iter().copied().max().unwrap_or(0) as f32 * 0.2) as u32;
        // max_gap = step×3: 다운샘플로 스캔 안 된 인덱스(0 카운트) + 격자선 갭 흡수.
        let mg = s * 3;
        let (y0, y1) = longest_run_gap(&row_cnt, row_thr, mg)?;
        let (x0, x1) = longest_run_gap(&col_cnt, col_thr, mg)?;
        let (bw, bh) = (x1 - x0 + 1, y1 - y0 + 1);
        // 채움비율: bbox 내 타겟색 샘플 / 전체 샘플.
        let mut hit = 0u32;
        let mut samp = 0u32;
        let mut yy = y0;
        while yy <= y1 {
            let mut xx = x0;
            while xx <= x1 {
                if let Some(rgb) = frame.rgb(xx, yy) {
                    samp += 1;
                    if self.near(rgb) { hit += 1; }
                }
                xx += s;
            }
            yy += s;
        }
        let fill_ratio = if samp > 0 { hit as f32 / samp as f32 } else { 0.0 };
        Some(BBox { x: x0 as i32, y: y0 as i32, w: bw, h: bh, fill_ratio })
    }

    /// bbox 내부 격자선(경계) 주기로 셀 피치·행렬수 역산.
    /// 중앙 수평선을 가로질러 색 급변(셀경계) 위치들의 간격 중앙값 = cell.
    fn infer_grid(&self, frame: &Frame, b: &BBox) -> Option<(u32, u32, u32, f32)> {
        // 가로 스캔라인(bbox 세로 중앙)에서 경계(밝기 급변) x 좌표 수집.
        let my = (b.y as u32) + b.h / 2;
        let edges_x = self.edge_positions_h(frame, b.x as u32, b.y as u32 + b.h - 1, my, b.w);
        // 세로 스캔라인(bbox 가로 중앙)에서 경계 y 좌표.
        let mx = (b.x as u32) + b.w / 2;
        let edges_y = self.edge_positions_v(frame, b.y as u32, b.x as u32 + b.w - 1, mx, b.h);
        let pitch_x = median_gap(&edges_x)?;
        let pitch_y = median_gap(&edges_y)?;
        // 셀은 정사각 가정(지뢰찾기·테트리스) → 두 피치 평균.
        let cell = ((pitch_x + pitch_y) / 2).max(1);
        if cell < 6 {
            return None; // 너무 촘촘 = 격자 아님(텍스트 등).
        }
        // ★반올림 나눗셈: bbox 가 격자 실크기보다 1~수px 작게 잡히면(경계 anti-alias)
        //   내림 나눗셈은 마지막 행/열을 통째로 잃음(797/160=4.98→4 오답). 반올림으로 교정.
        let cols = ((b.w as f32 / cell as f32).round() as u32).max(1);
        let rows = ((b.h as f32 / cell as f32).round() as u32).max(1);
        // 규칙성 신뢰도: 두 피치가 비슷할수록(정사각 격자)·경계 개수가 rows/cols 에 부합할수록↑.
        let sq = 1.0 - ((pitch_x as f32 - pitch_y as f32).abs() / cell as f32).min(1.0);
        let expect = (cols + rows) as f32;
        let got = (edges_x.len() + edges_y.len()) as f32;
        let regularity = 1.0 - ((got - expect).abs() / expect.max(1.0)).min(1.0);
        let conf = (sq * 0.5 + regularity * 0.5).clamp(0.0, 1.0);
        Some((cell, cols, rows, conf))
    }

    /// 수평 스캔라인(y=my)에서 밝기 급변(셀 경계) x 좌표들.
    fn edge_positions_h(&self, frame: &Frame, x0: u32, _y_end: u32, my: u32, width: u32) -> Vec<u32> {
        let mut edges = Vec::new();
        let mut prev = None::<u8>;
        for x in x0..x0 + width {
            let lum = frame.rgb(x, my).map(luma).unwrap_or(0);
            if let Some(p) = prev {
                if (lum as i32 - p as i32).abs() > 30 {
                    edges.push(x);
                }
            }
            prev = Some(lum);
        }
        dedup_close(&edges, 3)
    }

    /// 수직 스캔라인(x=mx)에서 밝기 급변 y 좌표들.
    fn edge_positions_v(&self, frame: &Frame, y0: u32, _x_end: u32, mx: u32, height: u32) -> Vec<u32> {
        let mut edges = Vec::new();
        let mut prev = None::<u8>;
        for y in y0..y0 + height {
            let lum = frame.rgb(mx, y).map(luma).unwrap_or(0);
            if let Some(p) = prev {
                if (lum as i32 - p as i32).abs() > 30 {
                    edges.push(y);
                }
            }
            prev = Some(lum);
        }
        dedup_close(&edges, 3)
    }
}

/// 바운딩박스 + 채움비율.
struct BBox {
    x: i32,
    y: i32,
    w: u32,
    h: u32,
    fill_ratio: f32,
}

fn luma((r, g, b): (u8, u8, u8)) -> u8 {
    ((r as u32 * 30 + g as u32 * 59 + b as u32 * 11) / 100) as u8
}

/// 값이 threshold 이상인 최장 구간 [start,end] 인덱스.
/// ★max_gap: 임계 미만이 연속 max_gap 이하면 같은 구간으로 이어붙임(다운샘플 step 으로 생기는
///   0-갭·격자선 어두운 픽셀 갭을 흡수 — 없으면 구간이 1픽셀마다 끊겨 bbox 가 붕괴함).
fn longest_run_gap(cnt: &[u32], thr: u32, max_gap: u32) -> Option<(u32, u32)> {
    if thr == 0 {
        return None;
    }
    let (mut best_s, mut best_e, mut best_len) = (0u32, 0u32, 0u32);
    let mut cur_s = None::<u32>;
    let mut gap = 0u32;
    for (i, &v) in cnt.iter().enumerate() {
        let i = i as u32;
        if v >= thr {
            let s = *cur_s.get_or_insert(i);
            gap = 0;
            let len = i - s + 1;
            if len > best_len { best_len = len; best_s = s; best_e = i; }
        } else if cur_s.is_some() {
            gap += 1;
            if gap > max_gap { cur_s = None; gap = 0; }
        }
    }
    if best_len > 0 { Some((best_s, best_e)) } else { None }
}

/// 정렬된 경계 위치들 → 격자 셀 피치 추정.
/// ★최빈 gap(mode) 기반: 규칙적 격자에서 셀 피치는 [가장 빈번한 간격]. 숫자·글자 경계가
///   만드는 자잘한 노이즈 gap 이나 셀 배수 gap 에 흔들리는 median 보다 견고.
///   ±허용오차(6px)로 비슷한 gap 을 한 버킷으로 묶어 최다 버킷의 대표값 반환.
fn median_gap(pos: &[u32]) -> Option<u32> {
    if pos.len() < 2 {
        return None;
    }
    let mut gaps: Vec<u32> = pos.windows(2).map(|w| w[1] - w[0]).filter(|&g| g > 8).collect();
    if gaps.is_empty() {
        return None;
    }
    gaps.sort_unstable();
    // 슬라이딩 버킷(±6): 각 gap 을 중심으로 ±6 안에 든 gap 수가 최다인 지점 = 최빈 피치.
    let (mut best_g, mut best_cnt) = (gaps[0], 0usize);
    for &g in &gaps {
        let cnt = gaps.iter().filter(|&&x| x.abs_diff(g) <= 6).count();
        if cnt > best_cnt {
            best_cnt = cnt;
            // 그 버킷의 평균으로 대표(안정화).
            let sum: u32 = gaps.iter().filter(|&&x| x.abs_diff(g) <= 6).sum();
            best_g = sum / cnt as u32;
        }
    }
    Some(best_g)
}

/// 서로 min_gap 이내로 붙은 좌표들을 하나로 병합(경계 두께 노이즈 제거).
fn dedup_close(sorted: &[u32], min_gap: u32) -> Vec<u32> {
    let mut out = Vec::new();
    let mut last = None::<u32>;
    for &v in sorted {
        if last.map(|l| v - l >= min_gap).unwrap_or(true) {
            out.push(v);
            last = Some(v);
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 합성 프레임: 배경(검정) 위 특정 위치에 회색 격자(닫힘셀+경계선) 그림.
    fn frame_with_grid(fw: u32, fh: u32, ox: u32, oy: u32, cell: u32, rows: u32, cols: u32) -> Frame {
        let mut px = vec![0u8; (fw * fh * 4) as usize];
        for r in 0..rows {
            for c in 0..cols {
                for yy in 0..cell {
                    for xx in 0..cell {
                        let x = ox + c * cell + xx;
                        let y = oy + r * cell + yy;
                        if x >= fw || y >= fh { continue; }
                        // 셀 내부=회색160, 경계(가장자리 1px)=어두운 회색128(격자선).
                        let edge = xx == 0 || yy == 0 || xx == cell - 1 || yy == cell - 1;
                        let v = if edge { 128 } else { 160 };
                        let i = ((y * fw + x) * 4) as usize;
                        px[i] = v; px[i + 1] = v; px[i + 2] = v; px[i + 3] = 255;
                    }
                }
            }
        }
        Frame { width: fw, height: fh, pixels: px }
    }

    #[test]
    fn locates_grid_region_and_pitch() {
        // 800x600 화면의 (200,150)에 40px 셀 5x5 격자 → 그 영역·셀크기 탐지.
        let frame = frame_with_grid(800, 600, 200, 150, 40, 5, 5);
        let loc = GridLocator::minesweeper();
        let det = loc.locate(&frame).expect("격자 탐지 성공해야");
        // 영역 원점이 대략 (200,150) 근처(±cell).
        assert!((det.region.x - 200).abs() <= 40, "x 원점 근사: {}", det.region.x);
        assert!((det.region.y - 150).abs() <= 40, "y 원점 근사: {}", det.region.y);
        // 셀 피치 40 근사(±8).
        assert!((det.grid.cell as i32 - 40).abs() <= 8, "cell 근사: {}", det.grid.cell);
    }

    #[test]
    fn moved_window_still_detected() {
        // 창을 다른 위치(500,50)로 옮겨도 탐지(좌표 하드코딩 아님 = 화면추적 증명).
        let frame = frame_with_grid(1000, 700, 500, 50, 40, 5, 5);
        let det = GridLocator::minesweeper().locate(&frame).expect("이동해도 탐지");
        assert!((det.region.x - 500).abs() <= 40, "이동창 x: {}", det.region.x);
        assert!((det.region.y - 50).abs() <= 40, "이동창 y: {}", det.region.y);
    }

    #[test]
    fn no_grid_returns_none() {
        // 타겟색 없는 화면(전부 검정) → None(추측 금지).
        let frame = Frame { width: 400, height: 300, pixels: vec![0u8; 400 * 300 * 4] };
        assert!(GridLocator::minesweeper().locate(&frame).is_none(), "격자 없으면 None");
    }




}

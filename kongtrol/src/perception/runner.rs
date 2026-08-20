//! 지뢰찾기 폐루프 실행기 (ADR 0007): capture → extract_state → decide → act.
//! 지뢰찾기=턴제·무압박(GAME-LITMUS §4-3) → 사이클 간 여유 sleep 가능.
use super::actor::EnigoActor;
use super::minesweeper::{Cell, MinesweeperEngine, MsAction};
use super::sensor::{FileSensor, XcapSensor};
use crate::core::{DecisionEngine, GridSpec, Region, Result, ScreenSensor};

/// 화면 소스: 실제 화면 캡처(xcap) 또는 파일 이미지(FileSensor).
pub enum Source {
    Screen,
    Image(String),
}

/// 폐루프 1회 결과(증거 로깅용).
pub struct CycleReport {
    pub opened: u32,
    pub flagged: u32,
    pub number_cells: u32,
    pub closed_cells: u32,
    pub last_action: Option<String>,
}

/// 폐루프 실행. `screen_region` = 앱 창 영역(격자 좌표계 기준). `max_cycles` 사이클.
/// `dry_run` = act(클릭) 생략, 인식·판단만(권한 없거나 검증용).
pub fn run(
    grid: GridSpec,
    screen_region: Region,
    max_cycles: u32,
    dry_run: bool,
    source: Source,
    click_scale: f32,
    human: bool,
) -> Result<Vec<CycleReport>> {
    // 화면 소스 선택: 실화면(xcap) or 파일 이미지(FileSensor).
    let screen: Box<dyn ScreenSensor> = match source {
        Source::Screen => Box::new(XcapSensor),
        Source::Image(p) => Box::new(FileSensor { path: p }),
    };
    let engine = MinesweeperEngine::default();
    // act 는 필요 시점에만 생성(권한 없으면 dry_run 으로 폴백 가능하도록 호출부 판단).
    // ★human=사람속도(커서 보간이동)로 클릭 — 유저가 과정을 눈으로 보게(a_16).
    let mut actor: Option<EnigoActor> =
        if dry_run { None } else { Some(EnigoActor::with_human(human)?) };

    let mut reports = Vec::new();
    for cycle in 0..max_cycles {
        // capture: 앱 창 영역만(격자 기준 좌표는 창-상대).
        let frame = screen.capture(Some(screen_region))?;
        // extract_state: 격자 픽셀색 → Board.
        let board = engine.extract_state(&frame, &grid)?;

        let mut rep = CycleReport {
            opened: 0,
            flagged: 0,
            number_cells: board.cells.iter().filter(|c| matches!(c, Cell::Number(_))).count() as u32,
            closed_cells: board.cells.iter().filter(|c| **c == Cell::Closed).count() as u32,
            last_action: None,
        };

        // decide: 기초룰로 다음 액션.
        match engine.decide(&board)? {
            Some(action) => {
                let (kind, r, c) = match action {
                    MsAction::Open(r, c) => ("open", r, c),
                    MsAction::Flag(r, c) => ("flag", r, c),
                };
                // 격자(row,col) → 화면 절대좌표(창 offset + 셀중심). 캡처 좌표계=물리px.
                let (cx, cy) = grid.cell_center(r, c);
                let sx = screen_region.x + cx as i32;
                let sy = screen_region.y + cy as i32;
                // ★클릭은 논리 좌표계(enigo/CoreGraphics 이벤트=논리pt) → 물리÷scale 로 변환.
                //   scale=1.0 이면 물리=논리(무변환). Retina 앱창(scale 2.0) 등에서 필수.
                let lx = (sx as f32 / click_scale).round() as i32;
                let ly = (sy as f32 / click_scale).round() as i32;
                rep.last_action = Some(format!("{kind} r{r}c{c} @screen({sx},{sy})→click({lx},{ly})"));

                if let Some(a) = actor.as_mut() {
                    match action {
                        MsAction::Open(..) => {
                            a.left_click(lx, ly)?;
                            rep.opened += 1;
                        }
                        MsAction::Flag(..) => {
                            a.right_click(lx, ly)?;
                            rep.flagged += 1;
                        }
                    }
                }
                reports.push(rep);
            }
            None => {
                rep.last_action = Some("확정 수 없음(추측 필요) — 종료".into());
                reports.push(rep);
                break;
            }
        }
        // 무압박 게임: 다음 캡처 전 화면 갱신 대기.
        std::thread::sleep(std::time::Duration::from_millis(150));
        let _ = cycle;
    }
    Ok(reports)
}

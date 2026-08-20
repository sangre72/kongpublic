//! kongtrol — 크로스플랫폼 OS 제어 CLI. M0 골격(ADR 0001~0006).
//! main = clap 파서 → 위험게이트(0004) → 도메인 디스패치 → 출력 envelope(0003) → exit code.
//
// M0 = 골격 단계: trait 메서드·에러 variant·팩토리 상당수가 향후 마일스톤(M1~M5)용 슬롯이라
// 아직 호출되지 않는다. 이는 ADR 0002/0005 의 의도된 구조이므로 dead_code 를 crate 레벨에서 허용.
// (M1 부터 하나씩 사용되며 자연 해소 — 골격을 지금 정의해 두는 것이 목적.)
#![allow(dead_code)]
mod cli;
mod core;
mod perception;
mod platform;

use clap::Parser;
use cli::output;
use cli::{Cli, Domain, GameVerb, InputVerb, ProcessVerb, ServiceVerb, SysVerb, risk_of};
use core::security::Gate;
use core::{GridSpec, KongtrolError, Region, Result, unsupported};
use perception::actor::{key_from_name, modifier_from_name};

/// 요청 식별자(M0=고정 스텁; M1+ 에서 uuid/카운터).
const REQUEST_ID: &str = "m0-stub";

fn main() {
    let cli = Cli::parse();
    if cli.verbose {
        tracing_subscriber::fmt()
            .with_max_level(tracing::Level::DEBUG)
            .init();
    }

    // 위험 게이트(0004 4중 방어 자리). DANGEROUS + 비--yes = 거부(M2에서 확인 프롬프트).
    let gate = Gate::new(cli.yes, cli.dry_run);
    let risk = risk_of(&cli.domain);
    if let Err(e) = gate.check(risk, "dispatch") {
        return finish(Err(e), cli.json);
    }

    // dry-run: 실제 실행 없이 무엇을 할지만(0004 ③). M0=간단 안내.
    if cli.dry_run {
        println!("[dry-run] {} 등급 명령 — 실제 실행 안 함 (M0 스텁)", risk.label());
        return finish(Ok(()), cli.json);
    }

    let result = dispatch(&cli.domain, cli.json, cli.human);
    finish(result, cli.json);
}

/// 도메인 디스패치. 조회(sys/process)는 M1 실동작, 나머지는 Unsupported(exit 5).
fn dispatch(domain: &Domain, json: bool, human: bool) -> Result<()> {
    match domain {
        Domain::Sys { verb } => match verb {
            SysVerb::Info => {
                let s = platform::system_info().summary()?;
                if json {
                    output::json_ok(&s, REQUEST_ID);
                } else {
                    println!(
                        "OS: {}\nKernel: {}\nCPU: {} cores\nMem: {} MB",
                        s.os,
                        s.kernel,
                        s.cpu_count,
                        s.mem_total_bytes / 1_048_576
                    );
                }
                Ok(())
            }
        },
        Domain::Process { verb } => {
            let pm = platform::process_manager();
            match verb {
                ProcessVerb::List => {
                    let list = pm.list()?;
                    if json {
                        output::json_ok(&list, REQUEST_ID);
                    } else {
                        println!("{:>7}  {:>6}  {}", "PID", "MEM_MB", "NAME");
                        for p in list.iter().take(30) {
                            println!(
                                "{:>7}  {:>6}  {}",
                                p.pid,
                                p.mem_bytes / 1_048_576,
                                p.name
                            );
                        }
                        println!("... 총 {} 프로세스", list.len());
                    }
                    Ok(())
                }
                ProcessVerb::Info { pid } => {
                    let p = pm.info(*pid)?;
                    if json {
                        output::json_ok(&p, REQUEST_ID);
                    } else {
                        println!("PID {} {} (mem {} MB)", p.pid, p.name, p.mem_bytes / 1_048_576);
                    }
                    Ok(())
                }
                ProcessVerb::Kill { pid, signal } => {
                    // DANGEROUS(M2). 현재 stub → Unsupported.
                    pm.kill(*pid, signal.as_deref())
                }
            }
        }
        Domain::Service { verb } => {
            let sm = platform::service_manager();
            match verb {
                ServiceVerb::List => {
                    let _ = sm.list()?;
                    Ok(())
                }
                ServiceVerb::Status { name } => {
                    let _ = sm.status(name)?;
                    Ok(())
                }
            }
        }
        Domain::Schedule => platform::scheduler().list().map(|_| ()),
        Domain::Input { verb } => dispatch_input(verb, human),
        Domain::App => Err(unsupported("app (M5+ 예정)")),
        Domain::Device => Err(unsupported("device (예정)")),
        Domain::Game { verb } => dispatch_game(verb, json, human),
        Domain::See { a11y, pid, compact, vl } => {
            if let Some(prompt) = vl {
                return dispatch_see_vl(prompt, json);
            }
            dispatch_see(*a11y, *pid, *compact, json)
        }
    }
}

/// ★로컬 VL 서버 판단 위임(a_922/934) — a11y 라벨 없는 캔버스 UI 최소 보조수단.
fn dispatch_see_vl(prompt: &str, json: bool) -> Result<()> {
    let answer = perception::vl::ask_vl(prompt)?;
    if json {
        output::json_ok(&serde_json::json!({"answer": answer}), "vl-answer");
    } else {
        println!("{answer}");
    }
    Ok(())
}

/// 화면 인식(눈) 디스패치 — a11y 접근성트리 덤프 (a_21 grounding).
#[cfg(target_os = "macos")]
fn dispatch_see(a11y: bool, pid: Option<i32>, compact: bool, json: bool) -> Result<()> {
    if !a11y {
        return Err(unsupported("see (—a11y 플래그 필요)"));
    }
    let els = perception::a11y::dump_app(pid)?;
    // --compact (a_66): labeled-only + role/label/cx/cy. Cuts worker-context tokens
    // (Playwright MCP snapshot style). AX walk cost unchanged.
    let view: Vec<_> = els
        .iter()
        .filter(|e| !compact || !e.label.is_empty())
        .collect();
    if json {
        let arr: Vec<_> = view
            .iter()
            .map(|e| {
                let cx = (e.x + e.w / 2.0).round();
                let cy = (e.y + e.h / 2.0).round();
                if compact {
                    serde_json::json!({"role": e.role, "label": e.label, "cx": cx, "cy": cy})
                } else {
                    serde_json::json!({
                        "role": e.role, "label": e.label,
                        "cx": cx, "cy": cy,
                        "x": e.x.round(), "y": e.y.round(), "w": e.w.round(), "h": e.h.round(),
                    })
                }
            })
            .collect();
        output::json_ok(&arr, "a11y-dump");
    } else {
        eprintln!("[a11y] 요소 {}개{}", view.len(), if compact { " compact" } else { "" });
        for e in &view {
            let (cx, cy) = ((e.x + e.w / 2.0).round(), (e.y + e.h / 2.0).round());
            if compact {
                println!("{}\t{}\t{:.0}\t{:.0}", e.role, e.label, cx, cy);
            } else {
                println!("{:<22} @({:.0},{:.0}) [{}x{}] · {}", e.role, cx, cy, e.w as i32, e.h as i32, e.label);
            }
        }
    }
    Ok(())
}

#[cfg(not(target_os = "macos"))]
fn dispatch_see(_a11y: bool, _pid: Option<i32>, _compact: bool, _json: bool) -> Result<()> {
    Err(unsupported("see --a11y (macOS 전용)"))
}

/// 입력 도메인 디스패치 (★DANGEROUS). 물리 키/텍스트 주입 (a_13 게임키·a_14 타이핑).
fn dispatch_input(verb: &InputVerb, human: bool) -> Result<()> {
    use perception::actor::EnigoActor;
    if let InputVerb::Run { path } = verb {
        // a_66: one process, dump-once, N labeled acts. LLM/shot = 0 between steps.
        let rep = perception::seq::run_file(std::path::Path::new(path), human)?;
        for line in &rep.lines {
            eprintln!("[seq] {line}");
        }
        eprintln!(
            "[seq] done ok={} fail={} dump_elems={} dump_ms={} elapsed_ms={}",
            rep.steps_ok, rep.steps_fail, rep.dump_elems, rep.dump_ms, rep.elapsed_ms
        );
        return Ok(());
    }
    let mut actor = EnigoActor::with_human(human)?;
    match verb {
        InputVerb::Key { name, repeat } => {
            let key = key_from_name(name)?;
            for _ in 0..*repeat {
                actor.tap_key(key)?;
            }
            eprintln!("[input] key {name} ×{repeat} 주입");
            Ok(())
        }
        InputVerb::Chord { modifier, key } => {
            let m = modifier_from_name(modifier)?;
            let k = key_from_name(key)?;
            actor.chord(m, k)?;
            eprintln!("[input] chord {modifier}+{key} 주입");
            Ok(())
        }
        InputVerb::Text { value } => {
            actor.type_text(value)?;
            eprintln!("[input] text {}자 타이핑", value.chars().count());
            Ok(())
        }
        InputVerb::TypeFile { path } => {
            let s = std::fs::read_to_string(path).map_err(|e| KongtrolError::NotFound {
                what: format!("타이핑 파일 {path} ({e})"),
            })?;
            actor.type_text(&s)?;
            eprintln!("[input] file {path} → {}자 타이핑", s.chars().count());
            Ok(())
        }
        InputVerb::Click { x, y, right, double, scale } => {
            // ★비전코어(a_18): AI 가 스샷(물리px) 보고 좌표 지정 → 논리(÷scale) 변환해 클릭.
            let (lx, ly) = ((*x as f32 / scale).round() as i32, (*y as f32 / scale).round() as i32);
            if *double {
                actor.double_click(lx, ly)?;
                eprintln!("[input] double-click 물리({x},{y})→논리({lx},{ly})");
            } else if *right {
                actor.right_click(lx, ly)?;
                eprintln!("[input] right-click 물리({x},{y})→논리({lx},{ly})");
            } else {
                actor.left_click(lx, ly)?;
                eprintln!("[input] click 물리({x},{y})→논리({lx},{ly})");
            }
            Ok(())
        }
        InputVerb::Move { x, y, scale } => {
            let (lx, ly) = ((*x as f32 / scale).round() as i32, (*y as f32 / scale).round() as i32);
            actor.move_to(lx, ly)?;
            eprintln!("[input] move 물리({x},{y})→논리({lx},{ly})");
            Ok(())
        }
        InputVerb::Drag { x1, y1, x2, y2, scale } => {
            let (lx1, ly1) = ((*x1 as f32 / scale).round() as i32, (*y1 as f32 / scale).round() as i32);
            let (lx2, ly2) = ((*x2 as f32 / scale).round() as i32, (*y2 as f32 / scale).round() as i32);
            actor.drag(lx1, ly1, lx2, ly2)?;
            let (cx, cy) = actor.location();
            eprintln!(
                "[input] drag 물리(({x1},{y1})→({x2},{y2}))→논리(({lx1},{ly1})→({lx2},{ly2})) cursor=({cx},{cy})"
            );
            Ok(())
        }
        InputVerb::Run { .. } => unreachable!("run handled above"),
        InputVerb::Location => {
            let (lx, ly) = actor.location();
            eprintln!("[input] location 논리({lx},{ly})");
            println!("{lx},{ly}");
            Ok(())
        }
    }
}

/// 게임 도메인 디스패치 (M7, ADR 0007). 지뢰찾기 폐루프 실행.
fn dispatch_game(verb: &GameVerb, json: bool, human: bool) -> Result<()> {
    match verb {
        GameVerb::Minesweeper {
            grid_x,
            grid_y,
            cell,
            cols,
            rows,
            win,
            cycles,
            click_scale,
            sense_only,
            image,
        } => {
            let grid = GridSpec {
                origin_x: *grid_x,
                origin_y: *grid_y,
                cell: *cell,
                cols: *cols,
                rows: *rows,
            };
            // 창 영역·격자 결정 (우선순위):
            //  ① image 소스 = 파일 전체가 격자(원점 0,0).
            //  ② --win 지정 = 수동 오버라이드(하위호환). CLI grid_x/cell/rows/cols 사용.
            //  ③ 실화면 + --win 미지정 = ★locator 자동탐지(u_15 화면추적, 좌표 받아쓰기 폐기).
            let (region, grid, source) = match image {
                Some(p) => (
                    Region { x: 0, y: 0, w: cols * cell, h: rows * cell },
                    grid,
                    perception::runner::Source::Image(p.clone()),
                ),
                None => match win {
                    Some(_) => (
                        parse_region(win.as_deref())?,
                        grid,
                        perception::runner::Source::Screen,
                    ),
                    None => {
                        // 자동탐지: 전체화면 캡처 → locator 로 대상 창·격자 탐지.
                        use perception::locator::GridLocator;
                        use perception::sensor::XcapSensor;
                        use core::ScreenSensor;
                        let full = XcapSensor.capture(None)?;
                        let det = GridLocator::minesweeper().locate(&full).ok_or_else(|| {
                            KongtrolError::NotFound {
                                what: "화면에서 지뢰찾기 격자(자동탐지 실패 — 대상 창이 보이는지 확인)".into(),
                            }
                        })?;
                        eprintln!(
                            "[locator] 자동탐지: region=({},{},{},{}) grid={}x{} cell={} conf={:.2}",
                            det.region.x, det.region.y, det.region.w, det.region.h,
                            det.grid.rows, det.grid.cols, det.grid.cell, det.confidence
                        );
                        // ★runner 는 region 으로 crop 캡처(0,0 기준 프레임) → grid 원점을 0,0 으로 리셋.
                        //   locator 가 낸 grid.origin 은 [전체화면 절대좌표]라 crop 프레임엔 안 맞음.
                        let g = core::GridSpec { origin_x: 0, origin_y: 0, ..det.grid };
                        (det.region, g, perception::runner::Source::Screen)
                    }
                },
            };
            eprintln!(
                "[minesweeper] 대상={} region=({},{},{},{}), 격자 {}x{} cell={} — {}",
                match image { Some(p) => format!("이미지 파일 {p}"), None => "네이티브 앱 창".into() },
                region.x, region.y, region.w, region.h, grid.rows, grid.cols, grid.cell,
                if *sense_only { "인식만(sense-only)" } else { "인식+클릭" }
            );
            // image 소스는 파일 좌표=물리=논리 동일 → scale 무시(1.0). 실화면만 click_scale 적용.
            let cscale = if image.is_some() { 1.0 } else { *click_scale };
            let reports =
                perception::runner::run(grid, region, *cycles, *sense_only, source, cscale, human)?;
            if json {
                let summary: Vec<_> = reports
                    .iter()
                    .map(|r| {
                        serde_json::json!({
                            "opened": r.opened, "flagged": r.flagged,
                            "numberCells": r.number_cells, "closedCells": r.closed_cells,
                            "action": r.last_action,
                        })
                    })
                    .collect();
                output::json_ok(&summary, "m7-minesweeper");
            } else {
                for (i, r) in reports.iter().enumerate() {
                    println!(
                        "cycle {}: 숫자셀 {} · 닫힘 {} · open {} · flag {} · {}",
                        i, r.number_cells, r.closed_cells, r.opened, r.flagged,
                        r.last_action.as_deref().unwrap_or("-")
                    );
                }
                println!("폐루프 {} 사이클 완료", reports.len());
            }
            Ok(())
        }
    }
}

/// "x,y,w,h" → Region. None=전체화면.
fn parse_region(s: Option<&str>) -> Result<Region> {
    match s {
        None => Ok(Region { x: 0, y: 0, w: 100_000, h: 100_000 }),
        Some(s) => {
            let parts: Vec<i64> = s.split(',').filter_map(|p| p.trim().parse().ok()).collect();
            if parts.len() != 4 {
                return Err(KongtrolError::Internal {
                    detail: format!("--win 형식 오류(x,y,w,h 기대): {s}"),
                });
            }
            Ok(Region {
                x: parts[0] as i32,
                y: parts[1] as i32,
                w: parts[2] as u32,
                h: parts[3] as u32,
            })
        }
    }
}

/// 결과 → 출력 + exit code(ADR 0003: 0/2/3/4/5).
fn finish(result: Result<()>, json: bool) {
    match result {
        Ok(()) => std::process::exit(0),
        Err(e) => {
            if json {
                output::json_err(&e, REQUEST_ID);
            } else {
                output::human_err(&e);
            }
            std::process::exit(e.code());
        }
    }
}

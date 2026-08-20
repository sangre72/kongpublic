//! CLI 명령 정의(clap derive) + 위험등급 (ADR 0003).
//! `kongtrol [--json] [--yes] [--dry-run] [--verbose] <domain> <verb>`.
pub mod output;

use crate::core::RiskLevel;
use clap::{Parser, Subcommand};

/// kongtrol — 크로스플랫폼 OS 제어 CLI.
#[derive(Parser, Debug)]
#[command(name = "kongtrol", version, about = "크로스플랫폼 OS 객체 조회·제어 CLI")]
pub struct Cli {
    /// 기계용 JSON envelope 출력.
    #[arg(long, global = true)]
    pub json: bool,
    /// DANGEROUS 명령 비대화 승인(0004 4중 방어 ②).
    #[arg(long, global = true)]
    pub yes: bool,
    /// 실제 실행 없이 무엇을 할지만 출력(0004 ③).
    #[arg(long, global = true)]
    pub dry_run: bool,
    /// 상세 로그.
    #[arg(long, global = true)]
    pub verbose: bool,
    /// ★사람속도 모드(a_16): 커서 보간이동(순간이동 금지)·타이핑 글자당 딜레이. 과정이 눈에 보이게.
    #[arg(long, global = true)]
    pub human: bool,
    #[command(subcommand)]
    pub domain: Domain,
}

/// 도메인 서브커맨드(ADR 0003 명령트리). M0=slot, 대부분 미구현(Unsupported).
#[derive(Subcommand, Debug)]
pub enum Domain {
    /// 프로세스 조회·제어 (R1).
    Process {
        #[command(subcommand)]
        verb: ProcessVerb,
    },
    /// 시스템 정보 (R5).
    Sys {
        #[command(subcommand)]
        verb: SysVerb,
    },
    /// 서비스/데몬 (R2, M3).
    Service {
        #[command(subcommand)]
        verb: ServiceVerb,
    },
    /// 스케줄러 (R3, M4).
    Schedule,
    /// 앱 제어 (R4, M5+).
    App,
    /// 입력 주입 ★DANGEROUS (R5, M5). 키보드 물리키·텍스트(a_13 테트리스·a_14 메모장).
    Input {
        #[command(subcommand)]
        verb: InputVerb,
    },
    /// 외부 디바이스 조회.
    Device,
    /// 게임 자동 플레이 (M7 perception loop, ADR 0007). ★대상=네이티브 앱.
    Game {
        #[command(subcommand)]
        verb: GameVerb,
    },
    /// ★화면 인식(눈) — a11y 접근성트리 덤프 (a_21 비전 grounding·READ).
    See {
        /// macOS 접근성트리(AXUIElement) 요소 덤프 → 요소 role·label·좌표(JSON). <100ms grounding.
        #[arg(long)]
        a11y: bool,
        /// 대상 앱 PID(권장 — 스크립트가 `pgrep -x <App>` 로 넘김). 미지정 시 최전면 자동조회 시도.
        #[arg(long)]
        pid: Option<i32>,
        /// a_66: labeled-only + role/label/cx/cy (cut worker-context tokens).
        #[arg(long)]
        compact: bool,
        /// ★로컬 VL 서버(a_922/934) 판단 위임 — a11y 라벨 없는 캔버스 UI 최소 보조수단.
        /// 스샷 640px 리사이즈→로컬LLM 전송→판단 텍스트 반환. --a11y/--pid/--compact와 배타.
        #[arg(long)]
        vl: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
pub enum GameVerb {
    /// 지뢰찾기 자동 플레이(폐루프). ★네이티브 앱 대상(브라우저 아님).
    Minesweeper {
        /// 격자 좌상단 x (창-상대 픽셀).
        #[arg(long, default_value_t = 0)]
        grid_x: u32,
        /// 격자 좌상단 y.
        #[arg(long, default_value_t = 0)]
        grid_y: u32,
        /// 셀 크기(px).
        #[arg(long, default_value_t = 24)]
        cell: u32,
        #[arg(long, default_value_t = 9)]
        cols: u32,
        #[arg(long, default_value_t = 9)]
        rows: u32,
        /// 대상 앱 창 영역(화면 절대): x,y,w,h. 미지정=전체화면.
        #[arg(long)]
        win: Option<String>,
        /// 폐루프 최대 사이클.
        #[arg(long, default_value_t = 20)]
        cycles: u32,
        /// ★캡처(물리px)↔클릭(논리pt) 좌표계 배수. Retina=2.0 등. 클릭좌표=물리÷scale.
        ///   xcap 캡처는 물리 프레임버퍼, enigo 클릭은 논리 포인트 → 이 값으로 변환(기본 1.0).
        #[arg(long, default_value_t = 1.0)]
        click_scale: f32,
        /// act(클릭) 생략, 인식·판단만(권한 없거나 검증용).
        #[arg(long)]
        sense_only: bool,
        /// 화면 캡처 대신 PNG 이미지 파일에서 인식(세션 GUI 제약 시 파이프라인 실증용).
        #[arg(long)]
        image: Option<String>,
    },
}

/// 입력 주입 서브커맨드(★DANGEROUS). 물리 키/텍스트.
#[derive(Subcommand, Debug)]
pub enum InputVerb {
    /// 특수키 1회(left·right·up·down·space·enter·esc). 테트리스 등 게임 조작.
    Key {
        /// 키 이름: left/right/up/down/space/enter/esc/cmd-n 등.
        name: String,
        /// 반복 횟수.
        #[arg(long, default_value_t = 1)]
        repeat: u32,
    },
    /// 조합키(modifier+key). 예 `chord cmd n`(신규메모 ⌘N). modifier=cmd/ctrl/alt/shift.
    Chord {
        /// 수식키: cmd/meta·ctrl·alt·shift.
        modifier: String,
        /// 함께 누를 키: n·a·s·c·v 등 단일 문자, 또는 enter/esc 등.
        key: String,
    },
    /// 유니코드 텍스트 타이핑(한글 포함). 메모장 등.
    Text {
        /// 타이핑할 문자열.
        value: String,
    },
    /// 파일 내용을 텍스트로 타이핑(긴 소설 등).
    TypeFile {
        /// 읽어서 타이핑할 파일 경로.
        path: String,
    },
    /// ★순수 마우스 클릭(a_18 비전코어 손): 물리좌표 (x,y) 좌/우클릭. AI가 스샷 보고 좌표 지정.
    Click {
        /// 물리 화면 좌표 x(픽셀).
        x: i32,
        /// 물리 화면 좌표 y(픽셀).
        y: i32,
        /// 우클릭.
        #[arg(long)]
        right: bool,
        /// 더블클릭.
        #[arg(long)]
        double: bool,
        /// 클릭 좌표계 배수(입력÷scale=논리). default 1.0=LOGICAL (INV1). enigo 는 논리pt.
        #[arg(long, default_value_t = 1.0)]
        scale: f32,
    },
    /// ★순수 마우스 이동(a_18 비전코어 손): 논리좌표 커서 이동만(클릭 없음).
    Move {
        x: i32,
        y: i32,
        #[arg(long, default_value_t = 1.0)]
        scale: f32,
    },
    /// ★press-drag-release (G6): start→mouse-down→보간→mouse-up. LOGICAL + --scale 1.0.
    Drag {
        /// start x (물리px; ÷scale = 논리pt)
        x1: i32,
        /// start y
        y1: i32,
        /// end x
        x2: i32,
        /// end y
        y2: i32,
        /// 클릭 좌표계 배수(입력÷scale=논리). default 1.0=LOGICAL (INV1).
        #[arg(long, default_value_t = 1.0)]
        scale: f32,
    },
    /// a_66: run a seq file (dump-once + labeled clicks/keys). no per-step LLM.
    Run {
        /// Seq file path (app/dump/click_label/click/key/chord/text/wait).
        path: String,
    },
    /// ★현재 커서 논리좌표 조회(u_764: "당연히 조회가능해야지" — location() 내부함수는 있었으나
    ///   CLI 단독노출 안돼있던 gap). 검증workflow(유저가 마우스 옮겨둔 지점 읽기 등)에 필수.
    Location,
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[test]
    fn parses_drag_verb_scale_default() {
        let cli = Cli::try_parse_from(["kongtrol", "input", "drag", "10", "20", "110", "80"]).unwrap();
        match cli.domain {
            Domain::Input {
                verb: InputVerb::Drag {
                    x1,
                    y1,
                    x2,
                    y2,
                    scale,
                },
            } => {
                assert_eq!((x1, y1, x2, y2), (10, 20, 110, 80));
                assert!((scale - 1.0).abs() < f32::EPSILON);
            }
            other => panic!("expected drag, got {other:?}"),
        }
    }

    #[test]
    fn parses_drag_verb_with_scale() {
        let cli = Cli::try_parse_from([
            "kongtrol", "input", "drag", "200", "100", "400", "300", "--scale", "2.0",
        ])
        .unwrap();
        match cli.domain {
            Domain::Input {
                verb: InputVerb::Drag { scale, .. },
            } => assert!((scale - 2.0).abs() < f32::EPSILON),
            other => panic!("expected drag, got {other:?}"),
        }
    }

    #[test]
    fn parses_input_run_and_see_compact() {
        let cli = Cli::try_parse_from(["kongtrol", "input", "run", "/tmp/a.seq"]).unwrap();
        match cli.domain {
            Domain::Input {
                verb: InputVerb::Run { path },
            } => assert_eq!(path, "/tmp/a.seq"),
            other => panic!("expected run, got {other:?}"),
        }
        let cli = Cli::try_parse_from(["kongtrol", "see", "--a11y", "--compact", "--pid", "1"]).unwrap();
        match cli.domain {
            Domain::See { a11y, compact, pid, vl } => {
                assert!(a11y && compact);
                assert_eq!(pid, Some(1));
                assert_eq!(vl, None);
            }
            other => panic!("expected see, got {other:?}"),
        }
    }
}

#[derive(Subcommand, Debug)]
pub enum ProcessVerb {
    /// 프로세스 목록 (READ).
    List,
    /// 프로세스 정보 (READ).
    Info { pid: u32 },
    /// 프로세스 종료 ★DANGEROUS (M2).
    Kill {
        pid: u32,
        #[arg(long)]
        signal: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
pub enum SysVerb {
    /// 시스템 요약 (READ).
    Info,
}

#[derive(Subcommand, Debug)]
pub enum ServiceVerb {
    /// 서비스 목록 (READ, M3).
    List,
    /// 서비스 상태 (READ, M3).
    Status { name: String },
}

/// 서브커맨드 → 위험 등급 매핑(ADR 0003 위험등급 태깅).
pub fn risk_of(domain: &Domain) -> RiskLevel {
    match domain {
        Domain::Process { verb } => match verb {
            ProcessVerb::List | ProcessVerb::Info { .. } => RiskLevel::Read,
            ProcessVerb::Kill { .. } => RiskLevel::Dangerous,
        },
        Domain::Sys { .. } => RiskLevel::Read,
        Domain::Service { verb } => match verb {
            ServiceVerb::List | ServiceVerb::Status { .. } => RiskLevel::Read,
        },
        Domain::Schedule | Domain::App | Domain::Device => RiskLevel::Read,
        Domain::Input { .. } => RiskLevel::Dangerous,
        // 게임 플레이 = 입력 주입 포함 → DANGEROUS(0004 게이트). sense_only 도 캡처는 함.
        Domain::Game { .. } => RiskLevel::Dangerous,
        // See = 화면 인식만(눈, 입력 없음) → READ.
        Domain::See { .. } => RiskLevel::Read,
    }
}

//! One-process labeled sequence runner (a_66).
//! Dump a11y ONCE → resolve labels → click/key/text/wait. No per-step LLM/shot.
//! Seq file (one verb / line, `#` comment):
//!   app Google Chrome
//!   dump
//!   click_label Inbox
//!   click 100 200
//!   dbl_label Foo
//!   key esc
//!   chord cmd s
//!   text hello
//!   wait 80
use crate::core::{KongtrolError, Result};
use crate::perception::actor::{self, EnigoActor};
use std::path::Path;
use std::time::Instant;

#[derive(Debug, Clone, PartialEq)]
pub enum Step {
    App(String),
    Dump,
    ClickLabel { label: String, double: bool },
    Click { x: i32, y: i32, double: bool },
    Key(String),
    Chord { modifier: String, key: String },
    Text(String),
    Wait(u64),
}

#[derive(Debug, Default)]
pub struct RunReport {
    pub steps_ok: u32,
    pub steps_fail: u32,
    pub dump_elems: usize,
    pub dump_ms: u128,
    pub elapsed_ms: u128,
    pub lines: Vec<String>,
}

pub fn parse(src: &str) -> Result<Vec<Step>> {
    let mut out = Vec::new();
    for (i, raw) in src.lines().enumerate() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let step = parse_line(line).map_err(|e| KongtrolError::Internal {
            detail: format!("seq L{}: {e}", i + 1),
        })?;
        out.push(step);
    }
    if out.is_empty() {
        return Err(KongtrolError::Internal {
            detail: "seq empty (need dump/click_label/click/key/…)".into(),
        });
    }
    Ok(out)
}

fn parse_line(line: &str) -> std::result::Result<Step, String> {
    let mut parts = line.splitn(2, char::is_whitespace);
    let verb = parts.next().unwrap_or("");
    let rest = parts.next().unwrap_or("").trim();
    match verb {
        "app" => {
            if rest.is_empty() {
                return Err("app <ProcessName>".into());
            }
            Ok(Step::App(rest.to_string()))
        }
        "dump" => Ok(Step::Dump),
        "click_label" | "lbl" => need_rest(rest, "click_label <label>")
            .map(|l| Step::ClickLabel { label: l, double: false }),
        "dbl_label" => need_rest(rest, "dbl_label <label>")
            .map(|l| Step::ClickLabel { label: l, double: true }),
        "click" => xy(rest, false),
        "dbl" | "double" => xy(rest, true),
        "key" => need_rest(rest, "key <name>").map(Step::Key),
        "chord" => {
            let mut it = rest.split_whitespace();
            let m = it.next().ok_or("chord <mod> <key>")?;
            let k = it.next().ok_or("chord <mod> <key>")?;
            Ok(Step::Chord {
                modifier: m.to_string(),
                key: k.to_string(),
            })
        }
        "text" => need_rest(rest, "text <str>").map(Step::Text),
        "wait" => {
            let ms: u64 = rest.parse().map_err(|_| "wait <ms>")?;
            Ok(Step::Wait(ms))
        }
        other => Err(format!("unknown verb '{other}'")),
    }
}

fn need_rest(rest: &str, hint: &str) -> std::result::Result<String, String> {
    if rest.is_empty() {
        Err(hint.into())
    } else {
        Ok(rest.to_string())
    }
}

fn xy(rest: &str, double: bool) -> std::result::Result<Step, String> {
    let mut it = rest.split_whitespace();
    let x: i32 = it.next().ok_or("click <x> <y>")?.parse().map_err(|_| "click x")?;
    let y: i32 = it.next().ok_or("click <x> <y>")?.parse().map_err(|_| "click y")?;
    Ok(Step::Click { x, y, double })
}

pub fn run_file(path: &Path, human: bool) -> Result<RunReport> {
    let src = std::fs::read_to_string(path).map_err(|e| KongtrolError::NotFound {
        what: format!("seq {path:?} ({e})"),
    })?;
    run(&parse(&src)?, human)
}

pub fn run(steps: &[Step], human: bool) -> Result<RunReport> {
    let t0 = Instant::now();
    let mut actor = EnigoActor::with_human(human)?;
    let mut app: Option<String> = None;
    let mut dump: Vec<(String, i32, i32, f64)> = Vec::new(); // label,cx,cy,area
    let mut dumped = false;
    let mut rep = RunReport::default();

    for step in steps {
        match step {
            Step::App(name) => {
                app = Some(name.clone());
                dumped = false;
                dump.clear();
                rep.lines.push(format!("app {name}"));
                rep.steps_ok += 1;
            }
            Step::Dump => {
                let (n, ms) = do_dump(app.as_deref(), &mut dump)?;
                dumped = true;
                rep.dump_elems = n;
                rep.dump_ms = ms;
                rep.lines.push(format!("dump elems={n} {ms}ms"));
                rep.steps_ok += 1;
            }
            Step::ClickLabel { label, double } => {
                if !dumped {
                    let (n, ms) = do_dump(app.as_deref(), &mut dump)?;
                    dumped = true;
                    rep.dump_elems = n;
                    rep.dump_ms = ms;
                    rep.lines.push(format!("dump(auto) elems={n} {ms}ms"));
                }
                match resolve(label, &dump) {
                    Some((x, y)) => {
                        if *double {
                            actor.double_click(x, y)?;
                        } else {
                            actor.left_click(x, y)?;
                        }
                        rep.lines.push(format!(
                            "{} '{label}' -> {x} {y}",
                            if *double { "dbl_label" } else { "click_label" }
                        ));
                        rep.steps_ok += 1;
                    }
                    None => {
                        rep.lines.push(format!("NOTFOUND '{label}'"));
                        rep.steps_fail += 1;
                        return Err(KongtrolError::NotFound {
                            what: format!("seq label '{label}'"),
                        });
                    }
                }
            }
            Step::Click { x, y, double } => {
                if *double {
                    actor.double_click(*x, *y)?;
                } else {
                    actor.left_click(*x, *y)?;
                }
                rep.lines.push(format!("click {x} {y}"));
                rep.steps_ok += 1;
            }
            Step::Key(name) => {
                actor.tap_key(actor::key_from_name(name)?)?;
                rep.lines.push(format!("key {name}"));
                rep.steps_ok += 1;
            }
            Step::Chord { modifier, key } => {
                actor.chord(actor::modifier_from_name(modifier)?, actor::key_from_name(key)?)?;
                rep.lines.push(format!("chord {modifier}+{key}"));
                rep.steps_ok += 1;
            }
            Step::Text(s) => {
                actor.type_text(s)?;
                rep.lines.push(format!("text {}ch", s.chars().count()));
                rep.steps_ok += 1;
            }
            Step::Wait(ms) => {
                std::thread::sleep(std::time::Duration::from_millis(*ms));
                rep.lines.push(format!("wait {ms}"));
                rep.steps_ok += 1;
            }
        }
    }
    rep.elapsed_ms = t0.elapsed().as_millis();
    Ok(rep)
}

fn resolve(label: &str, dump: &[(String, i32, i32, f64)]) -> Option<(i32, i32)> {
    let mut cand: Vec<&(String, i32, i32, f64)> =
        dump.iter().filter(|(l, _, _, _)| l == label).collect();
    if cand.is_empty() {
        cand = dump.iter().filter(|(l, _, _, _)| l.contains(label)).collect();
    }
    cand.sort_by(|a, b| a.3.partial_cmp(&b.3).unwrap_or(std::cmp::Ordering::Equal));
    cand.first().map(|e| (e.1, e.2))
}

fn do_dump(app: Option<&str>, out: &mut Vec<(String, i32, i32, f64)>) -> Result<(usize, u128)> {
    #[cfg(not(target_os = "macos"))]
    {
        let _ = app;
        let _ = out;
        return Err(crate::core::unsupported("seq dump (macOS a11y only)"));
    }
    #[cfg(target_os = "macos")]
    {
        let pid = match app {
            Some(name) => pid_of(name)?,
            None => None,
        };
        let t = Instant::now();
        let els = crate::perception::a11y::dump_app(pid)?;
        let ms = t.elapsed().as_millis();
        out.clear();
        for e in &els {
            if e.label.is_empty() {
                continue;
            }
            let cx = (e.x + e.w / 2.0).round() as i32;
            let cy = (e.y + e.h / 2.0).round() as i32;
            out.push((e.label.clone(), cx, cy, e.w * e.h));
        }
        Ok((els.len(), ms))
    }
}

#[cfg(target_os = "macos")]
fn pid_of(name: &str) -> Result<Option<i32>> {
    let out = std::process::Command::new("pgrep")
        .args(["-x", name])
        .output()
        .map_err(|e| KongtrolError::Internal {
            detail: format!("pgrep {name}: {e}"),
        })?;
    let s = String::from_utf8_lossy(&out.stdout);
    let pid = s.split_whitespace().next().and_then(|p| p.parse().ok());
    if pid.is_none() {
        return Err(KongtrolError::NotFound {
            what: format!("app '{name}' not running"),
        });
    }
    Ok(pid)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_core_verbs() {
        let s = parse(
            "# c\napp Google Chrome\ndump\nclick_label Inbox\nclick 10 20\nkey esc\nchord cmd s\ntext hi\nwait 80\n",
        )
        .unwrap();
        assert_eq!(s[0], Step::App("Google Chrome".into()));
        assert_eq!(s[1], Step::Dump);
        assert_eq!(
            s[2],
            Step::ClickLabel {
                label: "Inbox".into(),
                double: false
            }
        );
        assert_eq!(s[3], Step::Click { x: 10, y: 20, double: false });
        assert_eq!(s[4], Step::Key("esc".into()));
        assert_eq!(s[6], Step::Text("hi".into()));
        assert_eq!(s[7], Step::Wait(80));
    }

    #[test]
    fn rejects_unknown() {
        assert!(parse("explode now").is_err());
        assert!(parse("").is_err());
    }
}

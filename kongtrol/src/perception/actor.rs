//! enigo 0.6.x 기반 입력 액션 (ADR 0007 act, 0004 입력신뢰금지=이벤트 API 직접).
//! ★macOS: Accessibility TCC 권한 필요. 미승인 = NoPermission 에러(조용한 실패 아님, 0007 실증).
use crate::core::{KongtrolError, Result};
use enigo::{Button, Coordinate, Direction, Enigo, Key, Keyboard, Mouse, Settings};

pub struct EnigoActor {
    enigo: Enigo,
    /// ★사람속도 모드(a_16, u_17): 커서 보간이동(순간이동 금지)·타이핑 글자당 딜레이.
    ///   유저가 "사람처럼 실시간으로 움직이는 과정"을 보고싶어함 → 눈에 보이게.
    human: bool,
}

impl EnigoActor {
    /// 생성. Accessibility 미승인 시 PermissionDenied(exit 3)로 변환(0007 조용한 실패 금지).
    pub fn new() -> Result<Self> {
        Self::with_human(false)
    }

    /// human=true 면 사람속도(커서 보간·타이핑 딜레이) 모드.
    pub fn with_human(human: bool) -> Result<Self> {
        let enigo = Enigo::new(&Settings::default()).map_err(|e| {
            // enigo NoPermission → 권한 부족(exit 3) + 안내.
            KongtrolError::PermissionDenied {
                detail: format!(
                    "입력 주입 권한 없음({e:?}). macOS: 시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용(Accessibility) 에서 터미널/kongtrol 승인 필요"
                ),
            }
        })?;
        Ok(Self { enigo, human })
    }

    /// 절대 화면좌표 좌클릭(셀 열기).
    pub fn left_click(&mut self, x: i32, y: i32) -> Result<()> {
        self.click_at(Button::Left, x, y)
    }

    /// 절대 화면좌표 우클릭(깃발).
    pub fn right_click(&mut self, x: i32, y: i32) -> Result<()> {
        self.click_at(Button::Right, x, y)
    }

    /// 더블클릭(텍스트박스 편집 진입 등 — a_18 비전코어). 좌클릭 2회 연속.
    pub fn double_click(&mut self, x: i32, y: i32) -> Result<()> {
        self.click_at(Button::Left, x, y)?;
        std::thread::sleep(std::time::Duration::from_millis(80));
        self.click_at(Button::Left, x, y)
    }

    /// 커서 이동만(클릭 없음 — a_18 비전코어 손). human 이면 보간이동.
    pub fn move_to(&mut self, x: i32, y: i32) -> Result<()> {
        self.move_and(x, y)
    }

    /// press-drag-release (G6): start → mouse-down → interpolate → mouse-up.
    /// macOS uses CGEvent LeftMouseDragged (same HID path as click_at).
    pub fn drag(&mut self, x1: i32, y1: i32, x2: i32, y2: i32) -> Result<()> {
        self.drag_at(x1, y1, x2, y2)
    }

    /// 현재 커서 논리pt (검증용).
    pub fn location(&mut self) -> (i32, i32) {
        self.enigo.location().unwrap_or((-1, -1))
    }

    /// 좌표 이동 후 press→(대기)→release 분리 클릭.
    /// ★macOS: enigo button 이 일부 앱 canvas 에 클릭 미전달(이동 이벤트는 전달됨 — 실측 Enter
    ///   이벤트 수신 O·Button 이벤트 X) → core-graphics 로 순수 Mouse Down/Up 을 직접 posting.
    ///   그 외 플랫폼 = enigo press/release.
    /// ★2026-08-18(u_710/713/714 실사고): 사람 실마우스=색상휠 클릭 100%성공(유저 직접확인 3점),
    ///   kongtrol 순간이동+즉시클릭=Krita색상위젯(Qt)에서 반복실패(a_643·645·649~654). 1차수정(클릭직전
    ///   MouseMoved 1개 추가)은 부분개선에 그침(ar_654: 간헐적). 2차수정 — 근본원인: 이동 자체가 여전히
    ///   enigo(별도 CGEventSource)의 순간이동(move_and, Abs 2회)이었고 그 위에 CGEvent 1개만 얹은 것 =
    ///   "사람처럼 이동"이 아니라 "워프 후 제스처 흉내"에 불과했음. 진짜수정: 이동 전체를 이 함수의 CGEvent
    ///   MouseMoved 스텝보간으로 대체(enigo.move_mouse 미사용) — 시작점→목표점까지 여러 MouseMoved 를
    ///   전부 같은 CGEventSource·같은 이벤트스트림으로 posting 후 down/up. 사람이 손을 움직여 도착하는
    ///   과정 전체를 하나의 스트림으로 재현.
    #[cfg(target_os = "macos")]
    fn click_at(&mut self, button: Button, x: i32, y: i32) -> Result<()> {
        use core_graphics::event::{CGEvent, CGEventTapLocation, CGEventType, CGMouseButton, EventField};
        use core_graphics::event_source::{CGEventSource, CGEventSourceStateID};
        use core_graphics::geometry::CGPoint;
        let (down, up, cgbtn) = match button {
            Button::Right => (CGEventType::RightMouseDown, CGEventType::RightMouseUp, CGMouseButton::Right),
            _ => (CGEventType::LeftMouseDown, CGEventType::LeftMouseUp, CGMouseButton::Left),
        };
        let src = CGEventSource::new(CGEventSourceStateID::HIDSystemState)
            .map_err(|_| input_err("CGEventSource 생성 실패"))?;
        // ★이동 전체를 CGEvent MouseMoved 보간으로 수행(enigo 미사용) — down/up 과 동일 src·동일 스트림.
        let (sx, sy) = self.enigo.location().unwrap_or((x, y));
        let dist = (((x - sx).pow(2) + (y - sy).pow(2)) as f64).sqrt();
        let steps = ((dist / 20.0) as i32).clamp(8, 30);
        for i in 1..=steps {
            let t = i as f64 / steps as f64;
            let e = 0.5 - 0.5 * (std::f64::consts::PI * t).cos(); // ease-in-out
            let cx = sx as f64 + (x - sx) as f64 * e;
            let cy = sy as f64 + (y - sy) as f64 * e;
            let step_pt = CGPoint::new(cx.round(), cy.round());
            let ev = CGEvent::new_mouse_event(src.clone(), CGEventType::MouseMoved, step_pt, cgbtn)
                .map_err(|_| input_err("mouse move-step 이벤트 생성 실패"))?;
            ev.post(CGEventTapLocation::HID);
            std::thread::sleep(std::time::Duration::from_millis(15));
        }
        let pt = CGPoint::new(x as f64, y as f64);
        // 목표점 정확 안착 MouseMoved(마지막 hover 상태 확정).
        let ev_final_move = CGEvent::new_mouse_event(src.clone(), CGEventType::MouseMoved, pt, cgbtn)
            .map_err(|_| input_err("mouse final-move 이벤트 생성 실패"))?;
        ev_final_move.post(CGEventTapLocation::HID);
        std::thread::sleep(std::time::Duration::from_millis(40));
        let ev_down = CGEvent::new_mouse_event(src.clone(), down, pt, cgbtn)
            .map_err(|_| input_err("mouse down 이벤트 생성 실패"))?;
        // ★클릭 상태 필드(=1) 필수: 없으면 macOS/앱이 '유효 클릭'으로 인식 안 하고 무시하는 경우 있음.
        ev_down.set_integer_value_field(EventField::MOUSE_EVENT_CLICK_STATE, 1);
        ev_down.post(CGEventTapLocation::HID);
        std::thread::sleep(std::time::Duration::from_millis(60));
        let ev_up = CGEvent::new_mouse_event(src, up, pt, cgbtn)
            .map_err(|_| input_err("mouse up 이벤트 생성 실패"))?;
        ev_up.set_integer_value_field(EventField::MOUSE_EVENT_CLICK_STATE, 1);
        ev_up.post(CGEventTapLocation::HID);
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }

    /// 비-macOS: enigo press/release.
    #[cfg(not(target_os = "macos"))]
    fn click_at(&mut self, button: Button, x: i32, y: i32) -> Result<()> {
        self.move_and(x, y)?;
        self.enigo.button(button, Direction::Press).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(60));
        self.enigo.button(button, Direction::Release).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }

    /// 특수키 1회 누름(방향키·space 등 — 테트리스 조작 a_13).
    pub fn tap_key(&mut self, key: Key) -> Result<()> {
        self.enigo.key(key, Direction::Click).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }

    /// 조합키(modifier + key). 예 ⌘N 신규메모(a_14). modifier press→key click→modifier release.
    pub fn chord(&mut self, modifier: Key, key: Key) -> Result<()> {
        self.enigo.key(modifier, Direction::Press).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(30));
        self.enigo.key(key, Direction::Click).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(30));
        self.enigo.key(modifier, Direction::Release).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }

    /// 유니코드 텍스트 타이핑(한글 포함 — 메모장 a_14).
    /// ★human 모드: 글자(grapheme 근사=char)마다 80~150ms 딜레이 → 사람 타이핑 리듬(눈에 보임).
    pub fn type_text(&mut self, s: &str) -> Result<()> {
        if !self.human {
            return self.enigo.text(s).map_err(input_err);
        }
        for ch in s.chars() {
            let buf = ch.to_string();
            self.enigo.text(&buf).map_err(input_err)?;
            // 글자별 딜레이 — index 로 변주(80~150ms, Math.random 불가라 char code 로 변주).
            let d = 80 + (ch as u32 % 70) as u64;
            std::thread::sleep(std::time::Duration::from_millis(d));
        }
        Ok(())
    }

    fn move_and(&mut self, x: i32, y: i32) -> Result<()> {
        if self.human {
            return self.move_smooth(x, y);
        }
        // ★enigo 0.6 Abs 이동은 1회 호출 시 델타필드(MOUSE_EVENT_DELTA) 계산이 어긋나
        //   목표에 안 닿는 사례(실측: 500,528 요청→커서 181,1231). 2회 호출로 수렴시킴
        //   (1회차로 근처 이동→location 갱신→2회차 델타≈0 로 정확 안착).
        self.enigo
            .move_mouse(x, y, Coordinate::Abs)
            .map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(30));
        self.enigo
            .move_mouse(x, y, Coordinate::Abs)
            .map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(30));
        Ok(())
    }

    /// ★사람속도 커서 이동: 현재 위치→목표를 N스텝 보간(각 스텝 sleep) → 커서가 눈에 보이게
    ///   부드럽게 움직임(순간이동 금지, a_16). ease-in-out 로 사람처럼 가속·감속.
    fn move_smooth(&mut self, tx: i32, ty: i32) -> Result<()> {
        let (sx, sy) = self.enigo.location().unwrap_or((tx, ty));
        let dist = (((tx - sx).pow(2) + (ty - sy).pow(2)) as f64).sqrt();
        // 거리 비례 스텝(최소 12, 최대 40) — 총 이동시간 대략 0.4~0.9s.
        let steps = ((dist / 25.0) as i32).clamp(12, 40);
        for i in 1..=steps {
            let t = i as f64 / steps as f64;
            // ease-in-out(코사인): 시작·끝 느리고 중간 빠름 = 사람 손동작.
            let e = 0.5 - 0.5 * (std::f64::consts::PI * t).cos();
            let cx = sx as f64 + (tx - sx) as f64 * e;
            let cy = sy as f64 + (ty - sy) as f64 * e;
            self.enigo
                .move_mouse(cx.round() as i32, cy.round() as i32, Coordinate::Abs)
                .map_err(input_err)?;
            std::thread::sleep(std::time::Duration::from_millis(18));
        }
        // 마지막 목표 정확 안착(보간 반올림 오차 보정).
        self.enigo.move_mouse(tx, ty, Coordinate::Abs).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }

    /// 보간 경로(start 제외, end 포함). human=ease-in-out 다스텝, else 선형 소수스텝.
    pub fn drag_waypoints(x1: i32, y1: i32, x2: i32, y2: i32, human: bool) -> Vec<(i32, i32)> {
        let dist = (((x2 - x1).pow(2) + (y2 - y1).pow(2)) as f64).sqrt();
        let steps = if human {
            ((dist / 25.0) as i32).clamp(12, 40)
        } else {
            ((dist / 40.0) as i32).clamp(6, 20)
        };
        let mut pts = Vec::with_capacity((steps + 1) as usize);
        for i in 1..=steps {
            let t = i as f64 / steps as f64;
            let e = if human {
                0.5 - 0.5 * (std::f64::consts::PI * t).cos()
            } else {
                t
            };
            pts.push((
                (x1 as f64 + (x2 - x1) as f64 * e).round() as i32,
                (y1 as f64 + (y2 - y1) as f64 * e).round() as i32,
            ));
        }
        if pts.last() != Some(&(x2, y2)) {
            pts.push((x2, y2));
        }
        pts
    }
}

/// macOS: move → LeftMouseDown → LeftMouseDragged* → LeftMouseUp (click_at 과 동일 HID).
#[cfg(target_os = "macos")]
impl EnigoActor {
    fn drag_at(&mut self, x1: i32, y1: i32, x2: i32, y2: i32) -> Result<()> {
        use core_graphics::event::{CGEvent, CGEventTapLocation, CGEventType, CGMouseButton, EventField};
        use core_graphics::event_source::{CGEventSource, CGEventSourceStateID};
        use core_graphics::geometry::CGPoint;
        self.move_and(x1, y1)?;
        let src = CGEventSource::new(CGEventSourceStateID::HIDSystemState)
            .map_err(|_| input_err("CGEventSource 생성 실패"))?;
        let start = CGPoint::new(x1 as f64, y1 as f64);
        let ev_down = CGEvent::new_mouse_event(src.clone(), CGEventType::LeftMouseDown, start, CGMouseButton::Left)
            .map_err(|_| input_err("mouse down 이벤트 생성 실패"))?;
        ev_down.set_integer_value_field(EventField::MOUSE_EVENT_CLICK_STATE, 1);
        ev_down.post(CGEventTapLocation::HID);
        std::thread::sleep(std::time::Duration::from_millis(40));
        let sleep_ms = if self.human { 18 } else { 8 };
        for (x, y) in Self::drag_waypoints(x1, y1, x2, y2, self.human) {
            let pt = CGPoint::new(x as f64, y as f64);
            let ev = CGEvent::new_mouse_event(src.clone(), CGEventType::LeftMouseDragged, pt, CGMouseButton::Left)
                .map_err(|_| input_err("mouse dragged 이벤트 생성 실패"))?;
            ev.set_integer_value_field(EventField::MOUSE_EVENT_CLICK_STATE, 1);
            ev.post(CGEventTapLocation::HID);
            std::thread::sleep(std::time::Duration::from_millis(sleep_ms));
        }
        let end = CGPoint::new(x2 as f64, y2 as f64);
        let ev_up = CGEvent::new_mouse_event(src, CGEventType::LeftMouseUp, end, CGMouseButton::Left)
            .map_err(|_| input_err("mouse up 이벤트 생성 실패"))?;
        ev_up.set_integer_value_field(EventField::MOUSE_EVENT_CLICK_STATE, 1);
        ev_up.post(CGEventTapLocation::HID);
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }
}

/// 비-macOS: enigo press → Abs 보간이동 → release.
#[cfg(not(target_os = "macos"))]
impl EnigoActor {
    fn drag_at(&mut self, x1: i32, y1: i32, x2: i32, y2: i32) -> Result<()> {
        self.move_and(x1, y1)?;
        self.enigo.button(Button::Left, Direction::Press).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(40));
        let sleep_ms = if self.human { 18 } else { 8 };
        for (x, y) in Self::drag_waypoints(x1, y1, x2, y2, self.human) {
            self.enigo.move_mouse(x, y, Coordinate::Abs).map_err(input_err)?;
            std::thread::sleep(std::time::Duration::from_millis(sleep_ms));
        }
        self.enigo.button(Button::Left, Direction::Release).map_err(input_err)?;
        std::thread::sleep(std::time::Duration::from_millis(40));
        Ok(())
    }
}

fn input_err<E: std::fmt::Debug>(e: E) -> KongtrolError {
    KongtrolError::Internal { detail: format!("입력 주입 실패: {e:?}") }
}

/// 키 이름 → enigo Key (seq runner + CLI share).
pub fn key_from_name(name: &str) -> Result<Key> {
    let k = match name.to_lowercase().as_str() {
        "left" => Key::LeftArrow,
        "right" => Key::RightArrow,
        "up" => Key::UpArrow,
        "down" => Key::DownArrow,
        "space" => Key::Space,
        "enter" | "return" => Key::Return,
        "esc" | "escape" => Key::Escape,
        "tab" => Key::Tab,
        "backspace" | "bs" => Key::Backspace,
        "delete" | "del" | "fwd" => Key::Delete,
        s if s.chars().count() == 1 => Key::Unicode(s.chars().next().unwrap()),
        other => {
            return Err(KongtrolError::NotFound {
                what: format!("지원 안 하는 키 이름: {other} (방향키·space·enter·esc·tab·backspace·delete·단일문자)"),
            });
        }
    };
    Ok(k)
}

/// 수식키 이름 → enigo Key.
pub fn modifier_from_name(name: &str) -> Result<Key> {
    let k = match name.to_lowercase().as_str() {
        "cmd" | "command" | "meta" => Key::Meta,
        "ctrl" | "control" => Key::Control,
        "alt" | "option" => Key::Alt,
        "shift" => Key::Shift,
        other => {
            return Err(KongtrolError::NotFound {
                what: format!("지원 안 하는 수식키: {other} (cmd/ctrl/alt/shift)"),
            });
        }
    };
    Ok(k)
}

#[cfg(test)]
mod tests {
    use super::EnigoActor;

    #[test]
    fn waypoints_end_at_target_and_exclude_start() {
        let pts = EnigoActor::drag_waypoints(10, 20, 110, 80, false);
        assert!(!pts.is_empty(), "보간 점 필요");
        assert_ne!(pts[0], (10, 20), "start 는 move 단계, waypoints 제외");
        assert_eq!(*pts.last().unwrap(), (110, 80), "마지막=end");
    }

    #[test]
    fn human_uses_more_steps() {
        let linear = EnigoActor::drag_waypoints(0, 0, 400, 0, false);
        let human = EnigoActor::drag_waypoints(0, 0, 400, 0, true);
        assert!(human.len() >= linear.len(), "human 스텝 ≥ linear");
        assert!(linear.len() >= 6 && linear.len() <= 21);
        assert!(human.len() >= 12 && human.len() <= 41);
    }

    #[test]
    fn zero_distance_still_lands_on_end() {
        let pts = EnigoActor::drag_waypoints(50, 50, 50, 50, false);
        assert_eq!(*pts.last().unwrap(), (50, 50));
    }
}

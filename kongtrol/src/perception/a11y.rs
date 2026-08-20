//! a11y — macOS 접근성트리(AXUIElement) 덤프 = 비전 grounding 벽돌파 (a_21 PhaseA, a_20 추천1).
//! ★스샷 왕복(2~5s/step) 없이 [요소 좌표 <100ms]. 최전면 앱의 UI 요소(role·label·bbox)를
//!   구조로 획득 → 판단주체(Claude)가 클릭좌표 즉시 결정. 커스텀 UI(캔버스)만 비전 폴백.
//! ★macOS 전용. Accessibility TCC 권한 필요(손쉬운 사용 — 이미 승인).
#![cfg(target_os = "macos")]
use crate::core::{KongtrolError, Result};
use accessibility_sys::{
    kAXChildrenAttribute, kAXDescriptionAttribute, kAXErrorSuccess, kAXFocusedApplicationAttribute,
    kAXFocusedUIElementAttribute, kAXPositionAttribute, kAXRoleAttribute, kAXSizeAttribute,
    kAXTitleAttribute, kAXValueAttribute, kAXValueTypeCGPoint, kAXValueTypeCGSize,
    AXIsProcessTrusted, AXUIElementCopyAttributeValue, AXUIElementCreateApplication,
    AXUIElementCreateSystemWide, AXUIElementGetPid, AXUIElementRef, AXValueGetValue, AXValueRef,
};
use core_foundation::array::{CFArrayGetCount, CFArrayGetValueAtIndex, CFArrayRef};
use core_foundation::base::{CFGetTypeID, CFRelease, CFTypeRef, TCFType};
use core_foundation::string::{CFString, CFStringGetTypeID, CFStringRef};
use std::os::raw::c_void;

/// 접근성트리에서 추출한 UI 요소(클릭·타이핑 대상 후보).
pub struct A11yElement {
    pub role: String,
    pub label: String, // title 우선, 없으면 description/value.
    pub x: f64,        // 물리 아님·논리 좌상단(스크린 좌표계, AXPosition).
    pub y: f64,
    pub w: f64,
    pub h: f64,
}

/// 최전면 앱의 접근성 요소 트리를 덤프. 의미있는(라벨 or 클릭가능) 요소만.
/// ★반환 좌표 = AX 스크린 좌표(논리pt·좌상단). 클릭 시 중심 = (x+w/2, y+h/2).
/// 대상 앱의 접근성 요소 덤프. pid 지정 시 그 앱, None 이면 최전면(systemwide) 시도.
/// ★systemwide focused-app 은 macOS 에서 종종 null → pid 지정이 확실(스크립트가 pgrep 로 넘김).
pub fn dump_app(pid: Option<i32>) -> Result<Vec<A11yElement>> {
    unsafe {
        if !AXIsProcessTrusted() {
            return Err(KongtrolError::PermissionDenied {
                detail: "접근성(손쉬운 사용) TCC 미승인 — 시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용에 터미널/kongtrol 추가".into(),
            });
        }
        let app = match pid {
            Some(p) if p > 0 => {
                let a = AXUIElementCreateApplication(p);
                if a.is_null() {
                    return Err(internal(&format!("pid {p} 앱 요소 생성 실패")));
                }
                a
            }
            _ => {
                // 최전면 시도: focused application → focused element pid.
                let system = AXUIElementCreateSystemWide();
                let a = copy_element_attr(system, kAXFocusedApplicationAttribute)
                    .or_else(|| app_via_focused_pid(system));
                CFRelease(system as CFTypeRef);
                a.ok_or_else(|| KongtrolError::PermissionDenied {
                    detail: "최전면 앱 자동조회 실패 — --pid <PID> 로 대상 지정 권장(스크립트: pgrep -x Keynote)".into(),
                })?
            }
        };
        let mut out = Vec::new();
        walk(app, &mut out, 0);
        CFRelease(app as CFTypeRef);
        Ok(out)
    }
}

/// systemwide focused UI element 의 pid → AXUIElementCreateApplication(pid) 로 앱 요소 획득(폴백).
unsafe fn app_via_focused_pid(system: AXUIElementRef) -> Option<AXUIElementRef> {
    let focused = copy_element_attr(system, kAXFocusedUIElementAttribute)?;
    let mut pid: i32 = 0;
    let err = AXUIElementGetPid(focused, &mut pid);
    CFRelease(focused as CFTypeRef);
    if err == kAXErrorSuccess && pid > 0 {
        let app = AXUIElementCreateApplication(pid);
        if app.is_null() {
            None
        } else {
            Some(app)
        }
    } else {
        None
    }
}

/// 요소 트리 재귀 순회(깊이 제한으로 폭주 방지).
unsafe fn walk(elem: AXUIElementRef, out: &mut Vec<A11yElement>, depth: u32) {
    if depth > 60 || out.len() > 4000 {
        return;
    }
    let role = copy_string_attr(elem, kAXRoleAttribute).unwrap_or_default();
    let label = copy_string_attr(elem, kAXTitleAttribute)
        .or_else(|| copy_string_attr(elem, kAXDescriptionAttribute))
        .or_else(|| copy_string_attr(elem, kAXValueAttribute))
        .unwrap_or_default();
    // 위치·크기(AXValue → CGPoint/CGSize).
    if let (Some((x, y)), Some((w, h))) = (copy_point(elem), copy_size(elem)) {
        // 의미있는 요소만: 라벨이 있거나 클릭 가능 역할(버튼·메뉴·필드·셀 등). 컨테이너 순수요소 제외.
        let meaningful = !label.is_empty()
            || role.contains("Button")
            || role.contains("MenuItem")
            || role.contains("TextField")
            || role.contains("TextArea")
            || role.contains("CheckBox")
            || role.contains("PopUpButton")
            || role.contains("Cell")
            || role.contains("Tab");
        if meaningful && w > 0.0 && h > 0.0 {
            out.push(A11yElement { role: role.clone(), label, x, y, w, h });
        }
    }
    // children 재귀.
    if let Some(children) = copy_children(elem) {
        let n = CFArrayGetCount(children);
        for i in 0..n {
            let child = CFArrayGetValueAtIndex(children, i) as AXUIElementRef;
            if !child.is_null() {
                walk(child, out, depth + 1);
            }
        }
        CFRelease(children as CFTypeRef);
    }
}

/// 속성값을 AXUIElementRef 로 복사(자식 앱요소 등).
unsafe fn copy_element_attr(elem: AXUIElementRef, attr: &str) -> Option<AXUIElementRef> {
    let cf = CFString::new(attr);
    let mut value: CFTypeRef = std::ptr::null();
    let err = AXUIElementCopyAttributeValue(elem, cf.as_concrete_TypeRef(), &mut value);
    if err == kAXErrorSuccess && !value.is_null() {
        Some(value as AXUIElementRef)
    } else {
        None
    }
}

/// 문자열 속성 복사. ★값이 실제 CFString 일 때만(AXValue/AXTitle 이 숫자·배열일 수 있어
///   무조건 CFString 캐스팅 시 crash — CFGetTypeID 로 타입 확인 필수).
unsafe fn copy_string_attr(elem: AXUIElementRef, attr: &str) -> Option<String> {
    let cf = CFString::new(attr);
    let mut value: CFTypeRef = std::ptr::null();
    let err = AXUIElementCopyAttributeValue(elem, cf.as_concrete_TypeRef(), &mut value);
    if err != kAXErrorSuccess || value.is_null() {
        return None;
    }
    let s = if CFGetTypeID(value) == CFStringGetTypeID() {
        cfstring_to_string(value as CFStringRef)
    } else {
        None
    };
    CFRelease(value);
    s.filter(|s| !s.is_empty())
}

/// children 배열 복사.
unsafe fn copy_children(elem: AXUIElementRef) -> Option<CFArrayRef> {
    let cf = CFString::new(kAXChildrenAttribute);
    let mut value: CFTypeRef = std::ptr::null();
    let err = AXUIElementCopyAttributeValue(elem, cf.as_concrete_TypeRef(), &mut value);
    if err == kAXErrorSuccess && !value.is_null() {
        Some(value as CFArrayRef)
    } else {
        None
    }
}

/// AXPosition(CGPoint).
unsafe fn copy_point(elem: AXUIElementRef) -> Option<(f64, f64)> {
    let cf = CFString::new(kAXPositionAttribute);
    let mut value: CFTypeRef = std::ptr::null();
    if AXUIElementCopyAttributeValue(elem, cf.as_concrete_TypeRef(), &mut value) != kAXErrorSuccess
        || value.is_null()
    {
        return None;
    }
    #[repr(C)]
    struct CGPoint {
        x: f64,
        y: f64,
    }
    let mut p = CGPoint { x: 0.0, y: 0.0 };
    let ok = AXValueGetValue(
        value as AXValueRef,
        kAXValueTypeCGPoint,
        &mut p as *mut _ as *mut c_void,
    );
    CFRelease(value);
    if ok {
        Some((p.x, p.y))
    } else {
        None
    }
}

/// AXSize(CGSize).
unsafe fn copy_size(elem: AXUIElementRef) -> Option<(f64, f64)> {
    let cf = CFString::new(kAXSizeAttribute);
    let mut value: CFTypeRef = std::ptr::null();
    if AXUIElementCopyAttributeValue(elem, cf.as_concrete_TypeRef(), &mut value) != kAXErrorSuccess
        || value.is_null()
    {
        return None;
    }
    #[repr(C)]
    struct CGSize {
        w: f64,
        h: f64,
    }
    let mut s = CGSize { w: 0.0, h: 0.0 };
    let ok = AXValueGetValue(
        value as AXValueRef,
        kAXValueTypeCGSize,
        &mut s as *mut _ as *mut c_void,
    );
    CFRelease(value);
    if ok {
        Some((s.w, s.h))
    } else {
        None
    }
}

/// CFStringRef → String.
unsafe fn cfstring_to_string(s: CFStringRef) -> Option<String> {
    if s.is_null() {
        return None;
    }
    // core-foundation 의 wrap_under_get_rule 로 안전 변환(retain 하지 않고 읽기).
    let cfs = CFString::wrap_under_get_rule(s);
    Some(cfs.to_string())
}

fn internal(m: &str) -> KongtrolError {
    KongtrolError::Internal { detail: m.into() }
}

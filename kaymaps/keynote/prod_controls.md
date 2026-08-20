# Keynote production format controls (a_236)

- project: /Users/bumsuklee/git/kong-bot
- fs: True (보기 → 전체 화면 종료 확인, 종료 클릭 안 함)
- green_clicked: False
- win: 2056x1290 @ (1028,684)
- traffic lights dump (do not click green): red (14,53) green (54,53)
- rows: 376 · labeled=311 · unlabeled=65
- coverage: {'color': True, 'line': 'partial', 'align': True, 'font': True, 'size': True, 'opacity': True, 'opacity_slider_drag': True}
- captured_at: 2026-08-14T22:00:44
- role_input: enriched a_246 · n=16
- a_249: HEX=Y (보기>색상 보기) · line-weight=partial · 파일 menu items=28 · green=N


## HOW-TO (pre · steps · wait · result · role · input)

### fill-expand — 채우기 패널 펼침
- **role**: 도형/상자 채우기 UI 진입 — 색·그라디언트·이미지 채우기 하위 패널을 연다
- **input**: click-only (채우기 well xy). 펼친 뒤 fill-types로 유형 선택
- **pre**: 도형/텍스트상자 선택 + 포맷 라디오 + 스타일 탭
- **steps**:
  1. click_label 포맷 (or xy 1908,72)
  1. click_label 스타일 (or xy 1831,107)
  1. dump → 채우기 well unlabeled @(2007,328)[68x25] → click 2007 328
  1. wait 400
- **wait**: 400ms
- **result**: 현재 채우기·색상 채우기·그라디언트 채우기·이미지 채우기·채우지 않음 노출

### fill-types — 채우기 유형 선택
- **role**: 채우기 모드 결정 — 단색/그라디언트/이미지/없음 중 슬라이드 톤에 맞는 유형
- **input**: select: 색상 채우기|그라디언트|이미지|채우지 않음. HEX: use hex-via-colors-panel (보기>색상 보기) — 예 F6F1EA
- **pre**: fill-expand 후
- **steps**:
  1. labeled: 색상 채우기 / 그라디언트 채우기 / 이미지 채우기 static 영역 click 또는 채우지 않음 checkbox
- **wait**: 300ms
- **result**: 채우기 모드 전환. HEX 입력 필드는 a11y 미노출(색상 패널 별도 경로 필요) | HEX path found a_249

### border-expand — 테두리/선 펼침
- **role**: 윤곽선(테두리) 편집 진입 — 카드·도형 경계선 유무·스타일
- **input**: click-only well → 테두리 없음 체크 또는 선 스타일 선택. 굵기 예: 1pt (선 굵기 필드 a11y partial)
- **pre**: 도형 선택 + 스타일 탭
- **steps**:
  1. dump → 테두리 well unlabeled @(2007,377)[68x25] → click 2007 377
  1. wait 400
- **wait**: 400ms
- **result**: 테두리 없음 체크 노출. 선 굵기 pt a11y 미노출(partial). see border-enable · line-stroke-enable

### opacity-stepper — 불투명도 스텝퍼
- **role**: 오브젝트 투명도 미세 조정 — 오버레이·워터마크·겹침 레이어
- **input**: click-only steppers (±1% 근사). 목표 값 예: 90 / 70 / 35
- **pre**: 도형 선택 + 스타일 탭. 필드 100%
- **steps**:
  1. dump unlabeled steppers: up @(2034,537)[15x11] / down @(2034,548)[15x11]
  1. click 2034 548 ×N
  1. wait 200
- **wait**: 200ms
- **result**: 실측: 100%→97% (down×3 ≈ -1%/click). 필드 라벨 '100%' 등

### opacity-drag — 불투명도 트랙 드래그
- **role**: 투명도 빠른 러프 조정 — 스텝퍼보다 큰 폭 변경
- **input**: drag-only (트랙 xy). 목표 % 예: 35. 숫자 타이핑 없음
- **pre**: 도형 선택 + 스타일. 슬라이더 트랙 y≈542, x≈1860–1990 (필드 왼쪽)
- **steps**:
  1. drag 1920 542 → 1860 542 (scale 1.0)
  1. wait 400
- **wait**: 400ms
- **result**: 실측: 97%→35%. knob 자체 a11y 없음 → 트랙 xy 추정 후 drag

### opacity-field — 불투명도 숫자 입력
- **role**: 투명도 정밀 수치 입력 — 레시피 재현·일관 토큰
- **input**: type percent: 100 | 90 | 70 | 35 (필드 클릭 → cmd+a → text → enter)
- **pre**: 스타일 탭 불투명도 필드
- **steps**:
  1. click 1999 542 (or click_label on current % value if unique)
  1. chord cmd a
  1. text <n>
  1. key enter
  1. wait 200
- **wait**: 200ms
- **result**: 값 커밋. (포커스 실패 시 필드 유지 가능 — re-dump)

### font-family — 서체/폰트
- **role**: 본문/제목 서체 지정 — 브랜드 타이포 일치
- **input**: select font: Apple SD Gothic Neo | Helvetica Neue | 본고딕 등 (팝업 메뉴)
- **pre**: 텍스트 선택 + 포맷 + 텍스트 탭
- **steps**:
  1. click_label 텍스트 (format subtab 1922,107)
  1. click_label Helvetica Neue (or current font popup)
  1. wait 400 → pick font from menu
- **wait**: 400ms
- **result**: AXPopUpButton 서체 변경

### font-size-stepper — 폰트 크기 스텝퍼
- **role**: 글자 크기 미세 조정 — 히어로/섹션/캡션 계층
- **input**: click-only steppers (±1pt). 목표 예: HERO 40 | SECTION 14 | HEADING 28 | body 16
- **pre**: 텍스트 탭. 크기 필드 예 116pt @(2002,326)
- **steps**:
  1. dump steppers unlabeled up @(2034,321) / down @(2034,332)
  1. click 2034 332 ×N
  1. wait 200
- **wait**: 200ms
- **result**: 실측: 116pt→114pt (down×2)

### font-size-field — 폰트 크기 숫자 입력
- **role**: 글자 크기 정밀 입력 — ABOUT 카피 pt 스펙 반영
- **input**: type pt: 40 | 28 | 16 | 14 | 12 (필드 → cmd+a → text → enter)
- **pre**: 텍스트 탭 크기 필드
- **steps**:
  1. click 2002 326
  1. chord cmd a / text <n> / key enter
- **wait**: 200ms
- **result**: pt 값 반영

### text-style-checks — 볼드/이탤릭/밑줄/취소선
- **role**: 강조 서체 속성 — 제목 강조·링크 유사 밑줄 등
- **input**: click-only: 볼드체 | 이탤릭체 | 밑줄체 | 취소선 (토글)
- **pre**: 텍스트 탭
- **steps**:
  1. click_label 볼드체 | 이탤릭체 | 밑줄체 | 취소선
- **wait**: 200ms
- **result**: AXCheckBox 토글

### text-color — 텍스트 색상
- **role**: 글자 색 — 브랜드 톤·대비 AA 텍스트
- **input**: select/popup 텍스트 색상. HEX 예: 1A1A1A | 2C2C2C | F6F1EA (HEX a11y 미노출 시 팔레트 클릭)
- **pre**: 텍스트 탭
- **steps**:
  1. click_label 텍스트 색상 (popup 1837,436) 또는 well xy 2010,357
  1. wait 400
  1. dump — HEX 필드 유무 확인(패널 종류에 따라 a11y 다름)
- **wait**: 400ms
- **result**: well 클릭이 추가 텍스트 옵션으로 펼쳐질 수 있음. 색상 팝업은 라벨 '텍스트 색상'

### para-align — 단락/세로 정렬
- **role**: 문단·박스 안 텍스트 정렬 — 카드 중앙/좌측 레이아웃
- **input**: click-only: 왼쪽|가운데|오른쪽|좌우 정렬 + 상단|중앙|하단 (세로)
- **pre**: 텍스트 탭
- **steps**:
  1. click_label 왼쪽|가운데|오른쪽|좌우 정렬
  1. click_label 상단|중앙|하단 (세로)
- **wait**: 200ms
- **result**: 단락·세로 정렬 적용

### align-size-wh — 정렬 크기 W/H
- **role**: 오브젝트 가로·세로 크기 — 16:9 카드·히어로 박스 치수
- **input**: type W/H pt 예: W=720 H=200 | W=500 H=366 (정렬 탭 필드 → cmd+a → text → enter). 비율 유지 체크 시 연동
- **pre**: 오브젝트 선택 + 정렬 탭
- **steps**:
  1. click_label 정렬 (subtab 2013,107)
  1. dump fields: W left @(1903,266) H right @(1992,266) — 실측 라벨 pt 값
  1. click 1903 266 → chord cmd a → text <w> → key enter
  1. wait 300
- **wait**: 300ms
- **result**: 실측 W 1730pt→500pt. H 366pt 유지. 비율 유지 체크 시 연동

### align-pos-xy — 정렬 위치 X/Y
- **role**: 오브젝트 캔버스 위치 — 그리드·여백 맞춤
- **input**: type X/Y pt 예: X=80 Y=120 | X=95 Y=203 (위치 필드 숫자 입력)
- **pre**: 정렬 탭. 위치 섹션
- **steps**:
  1. fields: X @(1903,346) Y @(1992,346) 실측 95pt / 203pt
  1. click field → cmd a → text → enter
- **wait**: 300ms
- **result**: 위치 이동. 스테퍼 unlabeled @1945/2034 y 340-351

### align-rotate — 회전 각도
- **role**: 오브젝트 회전·뒤집기 — 장식 도형·아이콘 각도
- **input**: type deg 예: 0 | 15 | 270 또는 click-only 수평/수직 뒤집기
- **pre**: 정렬 탭
- **steps**:
  1. field 0° @(1908,442)
  1. 또는 steppers @1945,436/447
  1. flip: click_label 수평으로 뒤집습니다 | 수직으로 뒤집습니다
- **wait**: 300ms
- **result**: 각도 변경/뒤집기

### preselect-object — 전제: 오브젝트 선택
- **role**: 슬라이드 편집 전제 — 대상 오브젝트를 포커스해 포맷 패널을 도형/텍스트 모드로 연다
- **input**: click-only (객체 목록 라벨 예: 프레젠테이션 제목). 텍스트 입력 없음
- **pre**: FS Keynote 문서 열림
- **steps**:
  1. 객체 목록 좌측: click 프레젠테이션 제목 필드 @(241,188) 또는 해당 셀
  1. wait 300
  1. 포맷 패널에 도형 스타일 / 스타일·텍스트·정렬 3탭 보이면 선택 성공
  1. 미선택 시 슬라이드 배경 UI(표준/다이내믹)만 보임
- **wait**: 300ms
- **result**: 도형 스타일 헤더 노출

### hex-via-colors-panel — HEX 입력 (보기>색상 보기)
- **role**: 단색 채우기/텍스트 색을 16진수로 정확히 지정 — 브랜드 팔레트 재현
- **input**: type HEX without #: F6F1EA (필드 라벨 16진수 색상 #). RGB 예: R246 G241 B234
- **pre**: Keynote FS. 대상 오브젝트 선택 권장. BAN green. BAN 전체 화면 종료
- **steps**:
  1. click_label 보기 (menubar 419,20 or toolbar)
  1. click_label 색상 보기 (menu item y≈553 — NOT 전체 화면 종료 y≈778)
  1. wait 600
  1. click_label 색상 슬라이더 (Colors window toolbar ~81,978)
  1. wait 400
  1. ensure popup RGB 슬라이더
  1. dump → HEX field: label 16진수 색상 # · AXTextField cx≈233 cy≈1210 (@(202,1198)[62x24])
  1. click 202 1198 → chord cmd a → text F6F1EA → key enter
  1. wait 300
- **wait**: 600ms
- **result**: 실측 a_249: 필드 147068→F6F1EA, RGB 20/112/104→246/241/234. Colors window title may be 텍스트 색상

### hex-rgb-fields — RGB 슬라이더 숫자 필드
- **role**: HEX와 동일 색의 채널 단위 미세 조정
- **input**: type 0-255 per channel: 빨간색 / 초록색 / 파란색 fields (예 246,241,234)
- **pre**: 색상 보기 + 색상 슬라이더 + RGB 슬라이더
- **steps**:
  1. dump fields: R @(207,1057) G @(207,1104) B @(207,1151) (y order may vary)
  1. click field → cmd a → text <0-255> → enter
- **wait**: 200ms
- **result**: 채널 값 반영, HEX 필드 동기화

### border-enable — 테두리 켜기 (텍스트상자/도형)
- **role**: 카드·박스 윤곽선 on/off
- **input**: click-only: 테두리 well → uncheck 테두리 없음
- **pre**: 오브젝트 선택 + 포맷 + 스타일 (도형 스타일)
- **steps**:
  1. dump → 테두리 well unlabeled @(2007,377)[68x25]
  1. click 2007 377
  1. wait 400
  1. click_label 테두리 없음 (checkbox ~1929,544) to uncheck if on
  1. wait 400
- **wait**: 400ms
- **result**: 테두리 없음 토글 가능. 선 굵기 pt 필드는 a11y 미노출(partial)

### line-stroke-enable — 선 오브젝트 스트로크 켜기
- **role**: 삽입된 선/연결선 표시·숨김
- **input**: click-only: 선 well → uncheck 선 없음. weight pt not in a11y
- **pre**: 삽입>선>선 으로 선 생성 후 객체목록 '선' 선택 + 스타일 (선 스타일)
- **steps**:
  1. click_label 삽입 → 선 → 선 (submenu @(531,212))
  1. drag canvas to place
  1. object list click 선
  1. dump → 선 well @(2007,328) → click
  1. click_label 선 없음 to uncheck
  1. wait 400
- **wait**: 400ms
- **result**: 선 없음 토글 실측. 굵기(pt)/끝점 필드는 dump에 없음 — custom drawing 추정. line-weight=partial

### file-menu-map — 파일 메뉴 항목 맵
- **role**: 저장·내보내기·닫기 등 문서 수명주기 (실행 시 BAN 종료/닫기 클릭)
- **input**: click-only open menu then esc. BAN click 닫기/종료
- **pre**: Keynote front
- **steps**:
  1. click_label 파일 (menubar 139,20)
  1. wait 400 · dump AXMenuItem
  1. key esc (do not click 닫기)
- **wait**: 400ms
- **result**: a_249 dump N=28 items: 신규… 열기… 최근 사용 열기 닫기 모두 닫기 저장… 별도 저장… 복제 이름 변경… 다음으로 이동… 다음으로 복귀 공유… 활동 설정… 다음으로 내보내기 파일 크기 줄이기… 고급 암호 설정… 테마 변경... 테마 저장… 프린트…

## COORDS (id · label · cx cy · bind)

| tab | label | role | cx | cy | bind |
|-----|-------|------|----|----|------|
| 스타일 | Apple | AXMenuBarItem | 44 | 39 | label |
| 스타일 | Keynote | AXMenuBarItem | 117 | 39 | label |
| 스타일 | 파일 | AXMenuBarItem | 160 | 39 | label |
| 스타일 | 편집 | AXMenuBarItem | 203 | 39 | label |
| 스타일 | 삽입 | AXMenuBarItem | 246 | 39 | label |
| 스타일 | 슬라이드 | AXMenuBarItem | 311 | 39 | label |
| 스타일 | 포맷 | AXMenuBarItem | 354 | 39 | label |
| 스타일 | 정렬 | AXMenuBarItem | 397 | 39 | label |
| 스타일 | 보기 | AXMenuBarItem | 440 | 39 | label |
| 스타일 | 재생 | AXMenuBarItem | 483 | 39 | label |
| 스타일 | 윈도우 | AXMenuBarItem | 537 | 39 | label |
| 스타일 | 도움말 | AXMenuBarItem | 591 | 39 | label |
| 스타일 | 무제.key | AXImage | 1052 | 45 | label |
| 스타일 | — | AXStaticText | 1122 | 45 | label |
| 스타일 | 편집됨 | AXMenuButton | 1173 | 45 | label |
| 스타일 | 무제.key | AXStaticText | 1107 | 60 | label |
| 스타일 | 보기 | AXMenuButton | 194 | 93 | label |
| 스타일 | 확대/축소 | AXMenuButton | 257 | 93 | label |
| 스타일 | 슬라이드 추가 | AXCheckBox | 331 | 93 | label |
| 스타일 | 재생 | AXButton | 671 | 93 | label |
| 스타일 | 표 | AXCheckBox | 1006 | 93 | label |
| 스타일 | 차트 | AXCheckBox | 1054 | 93 | label |
| 스타일 | 텍스트 | AXButton | 1102 | 93 | label |
| 스타일 | 도형 | AXCheckBox | 1150 | 93 | label |
| 스타일 | 미디어 | AXMenuButton | 1202 | 93 | label |
| 스타일 | 주석 | AXButton | 1250 | 93 | label |
| 스타일 | 공유 | AXButton | 1589 | 93 | label |
| 스타일 | 포맷 | AXRadioButton | 1937 | 93 | label |
| 스타일 | 애니메이션 | AXRadioButton | 1994 | 93 | label |
| 스타일 | 문서 | AXRadioButton | 2051 | 93 | label |
| 스타일 | 스타일 | AXRadioButton | 1877 | 122 | label |
| 스타일 | 텍스트 | AXRadioButton | 1966 | 122 | label |
| 스타일 | 정렬 | AXRadioButton | 2059 | 122 | label |
| 스타일 | 텍스트 | AXTextField | 237 | 129 | label |
| 스타일 | 텍스트 상자 삽입 | AXImage | 195 | 133 | label |
| 스타일 |  | AXCell | 320 | 137 | xy |
| 스타일 | 프레젠테이션 부제 | AXTextField | 283 | 163 | label |
| 스타일 | 텍스트 상자 삽입 | AXImage | 195 | 167 | label |
| 스타일 |  | AXCell | 320 | 171 | xy |
| 스타일 | 프레젠테이션 제목 | AXTextField | 283 | 197 | label |
| 스타일 | 텍스트 상자 삽입 | AXImage | 195 | 201 | label |
| 스타일 | 뒤로 | AXButton | 1810 | 202 | label |
| 스타일 | 앞으로 | AXButton | 2057 | 202 | label |
| 스타일 |  | AXCell | 320 | 205 | xy |
| 스타일 | 저자 및 날짜 | AXTextField | 267 | 231 | label |
| 스타일 | 텍스트 상자 삽입 | AXImage | 195 | 235 | label |
| 스타일 |  | AXCell | 320 | 239 | xy |
| 스타일 | 도형 스타일 | AXStaticText | 2057 | 286 | label |
| 스타일 | 채우기 | AXStaticText | 1850 | 334 | label |
| 스타일 |  | AXButton | 2041 | 340 | xy |
| 스타일 | 테두리 | AXStaticText | 1850 | 383 | label |
| 스타일 |  | AXButton | 2041 | 389 | xy |
| 스타일 | 그림자 | AXStaticText | 1850 | 432 | label |
| 스타일 |  | AXButton | 2041 | 438 | xy |
| 스타일 | 반사 | AXStaticText | 2041 | 481 | label |
| 스타일 |  | AXCheckBox | 1817 | 485 | xy |
| 스타일 | 불투명도 | AXStaticText | 1845 | 530 | label |
| 스타일 |  | AXButton | 2041 | 542 | xy |
| 스타일 | 100% | AXTextField | 2025 | 553 | label |
| 스타일 |  | AXButton | 2041 | 553 | xy |
| 스타일 | 제목 | AXCheckBox | 1850 | 613 | label |
| 스타일 | 상단 | AXPopUpButton | 2041 | 614 | label |
| 스타일 | 설명 | AXCheckBox | 1850 | 639 | label |
| 스타일 | 슬라이드 대상체 필터 | AXButton | 325 | 1320 | label |
| 스타일 |  | AXTextField | 304 | 1325 | xy |
| 스타일 | 검색 | AXButton | 171 | 1326 | label |
| 스타일 | 검색 | AXButton | 25 | 1329 | label |
| 스타일 | 무제.key | AXWindow | 2056 | 1329 | label |
| 스타일 |  | AXTextField | 341 | 1330 | xy |
| 스타일 | 검색 결과 | AXTable | 361 | 1330 | label |
| 스타일-채우기확장 | Apple | AXMenuBarItem | 44 | 39 | label |
| 스타일-채우기확장 | Keynote | AXMenuBarItem | 117 | 39 | label |
| 스타일-채우기확장 | 파일 | AXMenuBarItem | 160 | 39 | label |
| 스타일-채우기확장 | 편집 | AXMenuBarItem | 203 | 39 | label |
| 스타일-채우기확장 | 삽입 | AXMenuBarItem | 246 | 39 | label |
| 스타일-채우기확장 | 슬라이드 | AXMenuBarItem | 311 | 39 | label |
| 스타일-채우기확장 | 포맷 | AXMenuBarItem | 354 | 39 | label |
| 스타일-채우기확장 | 정렬 | AXMenuBarItem | 397 | 39 | label |
| 스타일-채우기확장 | 보기 | AXMenuBarItem | 440 | 39 | label |
| 스타일-채우기확장 | 재생 | AXMenuBarItem | 483 | 39 | label |
| 스타일-채우기확장 | 윈도우 | AXMenuBarItem | 537 | 39 | label |
| 스타일-채우기확장 | 도움말 | AXMenuBarItem | 591 | 39 | label |
| 스타일-채우기확장 | 무제.key | AXImage | 1052 | 45 | label |
| 스타일-채우기확장 | 무제.key | AXStaticText | 1107 | 60 | label |
| 스타일-채우기확장 | 보기 | AXMenuButton | 194 | 93 | label |
| 스타일-채우기확장 | 확대/축소 | AXMenuButton | 257 | 93 | label |
| 스타일-채우기확장 | 슬라이드 추가 | AXCheckBox | 331 | 93 | label |
| 스타일-채우기확장 | 재생 | AXButton | 671 | 93 | label |
| 스타일-채우기확장 | 표 | AXCheckBox | 1006 | 93 | label |
| 스타일-채우기확장 | 차트 | AXCheckBox | 1054 | 93 | label |
| 스타일-채우기확장 | 텍스트 | AXButton | 1102 | 93 | label |
| 스타일-채우기확장 | 도형 | AXCheckBox | 1150 | 93 | label |
| 스타일-채우기확장 | 미디어 | AXMenuButton | 1202 | 93 | label |
| 스타일-채우기확장 | 주석 | AXButton | 1250 | 93 | label |
| 스타일-채우기확장 | 공유 | AXButton | 1589 | 93 | label |
| 스타일-채우기확장 | 포맷 | AXRadioButton | 1937 | 93 | label |
| 스타일-채우기확장 | 애니메이션 | AXRadioButton | 1994 | 93 | label |
| 스타일-채우기확장 | 문서 | AXRadioButton | 2051 | 93 | label |
| 스타일-채우기확장 | 스타일 | AXRadioButton | 1877 | 122 | label |
| 스타일-채우기확장 | 텍스트 | AXRadioButton | 1966 | 122 | label |
| 스타일-채우기확장 | 정렬 | AXRadioButton | 2059 | 122 | label |
| 스타일-채우기확장 | 텍스트 | AXTextField | 237 | 129 | label |
| 스타일-채우기확장 | 텍스트 상자 삽입 | AXImage | 195 | 133 | label |
| 스타일-채우기확장 |  | AXCell | 320 | 137 | xy |
| 스타일-채우기확장 | 프레젠테이션 부제 | AXTextField | 283 | 163 | label |
| 스타일-채우기확장 | 텍스트 상자 삽입 | AXImage | 195 | 167 | label |
| 스타일-채우기확장 |  | AXCell | 320 | 171 | xy |
| 스타일-채우기확장 | 프레젠테이션 제목 | AXTextField | 283 | 197 | label |
| 스타일-채우기확장 | 텍스트 상자 삽입 | AXImage | 195 | 201 | label |
| 스타일-채우기확장 | 뒤로 | AXButton | 1810 | 202 | label |
| 스타일-채우기확장 | 앞으로 | AXButton | 2057 | 202 | label |
| 스타일-채우기확장 |  | AXCell | 320 | 205 | xy |
| 스타일-채우기확장 | 저자 및 날짜 | AXTextField | 267 | 231 | label |
| 스타일-채우기확장 | 텍스트 상자 삽입 | AXImage | 195 | 235 | label |
| 스타일-채우기확장 |  | AXCell | 320 | 239 | xy |
| 스타일-채우기확장 | 도형 스타일 | AXStaticText | 2057 | 286 | label |
| 스타일-채우기확장 | 채우기 | AXStaticText | 1850 | 334 | label |
| 스타일-채우기확장 |  | AXButton | 2041 | 340 | xy |
| 스타일-채우기확장 | 현재 채우기 | AXStaticText | 1861 | 378 | label |
| 스타일-채우기확장 | 테두리 | AXStaticText | 1850 | 383 | label |
| 스타일-채우기확장 |  | AXButton | 2041 | 389 | xy |
| 스타일-채우기확장 | 색상 채우기 | AXStaticText | 2024 | 414 | label |
| 스타일-채우기확장 | 그림자 | AXStaticText | 1850 | 432 | label |
| 스타일-채우기확장 |  | AXButton | 2041 | 438 | xy |
| 스타일-채우기확장 | 반사 | AXStaticText | 2041 | 481 | label |
| 스타일-채우기확장 |  | AXCheckBox | 1817 | 485 | xy |
| 스타일-채우기확장 | 불투명도 | AXStaticText | 1845 | 530 | label |
| 스타일-채우기확장 |  | AXButton | 2041 | 542 | xy |
| 스타일-채우기확장 | 그라디언트 채우기 | AXStaticText | 1892 | 550 | label |
| 스타일-채우기확장 | 100% | AXTextField | 2025 | 553 | label |
| 스타일-채우기확장 |  | AXButton | 2041 | 553 | xy |
| 스타일-채우기확장 | 이미지 채우기 | AXStaticText | 1872 | 602 | label |
| 스타일-채우기확장 | 제목 | AXCheckBox | 1850 | 613 | label |
| 스타일-채우기확장 | 상단 | AXPopUpButton | 2041 | 614 | label |
| 스타일-채우기확장 | 설명 | AXCheckBox | 1850 | 639 | label |
| 스타일-채우기확장 | 채우지 않음 | AXCheckBox | 2033 | 663 | label |
| 스타일-채우기확장 | 슬라이드 대상체 필터 | AXButton | 325 | 1320 | label |
| 스타일-채우기확장 |  | AXTextField | 304 | 1325 | xy |
| 스타일-채우기확장 | 검색 | AXButton | 171 | 1326 | label |
| 스타일-채우기확장 | 검색 | AXButton | 25 | 1329 | label |
| 스타일-채우기확장 | 무제.key | AXWindow | 2056 | 1329 | label |
| 스타일-채우기확장 |  | AXTextField | 341 | 1330 | xy |
| 스타일-채우기확장 | 검색 결과 | AXTable | 361 | 1330 | label |
| 스타일-테두리확장 | Apple | AXMenuBarItem | 44 | 39 | label |
| 스타일-테두리확장 | Keynote | AXMenuBarItem | 117 | 39 | label |
| 스타일-테두리확장 | 파일 | AXMenuBarItem | 160 | 39 | label |
| 스타일-테두리확장 | 편집 | AXMenuBarItem | 203 | 39 | label |
| 스타일-테두리확장 | 삽입 | AXMenuBarItem | 246 | 39 | label |
| 스타일-테두리확장 | 슬라이드 | AXMenuBarItem | 311 | 39 | label |
| 스타일-테두리확장 | 포맷 | AXMenuBarItem | 354 | 39 | label |
| 스타일-테두리확장 | 정렬 | AXMenuBarItem | 397 | 39 | label |
| 스타일-테두리확장 | 보기 | AXMenuBarItem | 440 | 39 | label |
| 스타일-테두리확장 | 재생 | AXMenuBarItem | 483 | 39 | label |
| 스타일-테두리확장 | 윈도우 | AXMenuBarItem | 537 | 39 | label |
| 스타일-테두리확장 | 도움말 | AXMenuBarItem | 591 | 39 | label |
| 스타일-테두리확장 | 무제.key | AXImage | 1052 | 45 | label |
| 스타일-테두리확장 | 무제.key | AXStaticText | 1107 | 60 | label |
| 스타일-테두리확장 | 보기 | AXMenuButton | 194 | 93 | label |
| 스타일-테두리확장 | 확대/축소 | AXMenuButton | 257 | 93 | label |
| 스타일-테두리확장 | 슬라이드 추가 | AXCheckBox | 331 | 93 | label |
| 스타일-테두리확장 | 재생 | AXButton | 671 | 93 | label |
| 스타일-테두리확장 | 표 | AXCheckBox | 1006 | 93 | label |
| 스타일-테두리확장 | 차트 | AXCheckBox | 1054 | 93 | label |
| 스타일-테두리확장 | 텍스트 | AXButton | 1102 | 93 | label |
| 스타일-테두리확장 | 도형 | AXCheckBox | 1150 | 93 | label |
| 스타일-테두리확장 | 미디어 | AXMenuButton | 1202 | 93 | label |
| 스타일-테두리확장 | 주석 | AXButton | 1250 | 93 | label |
| 스타일-테두리확장 | 공유 | AXButton | 1589 | 93 | label |
| 스타일-테두리확장 | 포맷 | AXRadioButton | 1937 | 93 | label |
| 스타일-테두리확장 | 애니메이션 | AXRadioButton | 1994 | 93 | label |
| 스타일-테두리확장 | 문서 | AXRadioButton | 2051 | 93 | label |
| 스타일-테두리확장 | 스타일 | AXRadioButton | 1877 | 122 | label |
| 스타일-테두리확장 | 텍스트 | AXRadioButton | 1966 | 122 | label |
| 스타일-테두리확장 | 정렬 | AXRadioButton | 2059 | 122 | label |
| 스타일-테두리확장 | 텍스트 | AXTextField | 237 | 129 | label |
| 스타일-테두리확장 | 텍스트 상자 삽입 | AXImage | 195 | 133 | label |
| 스타일-테두리확장 |  | AXCell | 320 | 137 | xy |
| 스타일-테두리확장 | 프레젠테이션 부제 | AXTextField | 283 | 163 | label |
| 스타일-테두리확장 | 텍스트 상자 삽입 | AXImage | 195 | 167 | label |
| 스타일-테두리확장 |  | AXCell | 320 | 171 | xy |
| 스타일-테두리확장 | 프레젠테이션 제목 | AXTextField | 283 | 197 | label |
| 스타일-테두리확장 | 텍스트 상자 삽입 | AXImage | 195 | 201 | label |
| 스타일-테두리확장 | 뒤로 | AXButton | 1810 | 202 | label |
| 스타일-테두리확장 | 앞으로 | AXButton | 2057 | 202 | label |
| 스타일-테두리확장 |  | AXCell | 320 | 205 | xy |
| 스타일-테두리확장 | 저자 및 날짜 | AXTextField | 267 | 231 | label |
| 스타일-테두리확장 | 텍스트 상자 삽입 | AXImage | 195 | 235 | label |
| 스타일-테두리확장 |  | AXCell | 320 | 239 | xy |
| 스타일-테두리확장 | 도형 스타일 | AXStaticText | 2057 | 286 | label |
| 스타일-테두리확장 | 채우기 | AXStaticText | 1850 | 334 | label |
| 스타일-테두리확장 |  | AXButton | 2041 | 340 | xy |
| 스타일-테두리확장 | 테두리 | AXStaticText | 1850 | 383 | label |
| 스타일-테두리확장 |  | AXButton | 2041 | 389 | xy |
| 스타일-테두리확장 | 그림자 | AXStaticText | 1850 | 432 | label |
| 스타일-테두리확장 |  | AXButton | 2041 | 438 | xy |
| 스타일-테두리확장 | 반사 | AXStaticText | 2041 | 481 | label |
| 스타일-테두리확장 |  | AXCheckBox | 1817 | 485 | xy |
| 스타일-테두리확장 | 불투명도 | AXStaticText | 1845 | 530 | label |
| 스타일-테두리확장 |  | AXButton | 2041 | 542 | xy |
| 스타일-테두리확장 | 35% | AXTextField | 2025 | 553 | label |
| 스타일-테두리확장 |  | AXButton | 2041 | 553 | xy |
| 스타일-테두리확장 | 테두리 없음 | AXCheckBox | 2024 | 554 | label |
| 스타일-테두리확장 | 제목 | AXCheckBox | 1850 | 613 | label |
| 스타일-테두리확장 | 상단 | AXPopUpButton | 2041 | 614 | label |
| 스타일-테두리확장 | 설명 | AXCheckBox | 1850 | 639 | label |
| 스타일-테두리확장 | 슬라이드 대상체 필터 | AXButton | 325 | 1320 | label |
| 스타일-테두리확장 |  | AXTextField | 304 | 1325 | xy |
| 스타일-테두리확장 | 검색 | AXButton | 171 | 1326 | label |
| 스타일-테두리확장 | 검색 | AXButton | 25 | 1329 | label |
| 스타일-테두리확장 | 무제.key | AXWindow | 2056 | 1329 | label |
| 스타일-테두리확장 |  | AXTextField | 341 | 1330 | xy |
| 스타일-테두리확장 | 검색 결과 | AXTable | 361 | 1330 | label |
| 정렬 | Apple | AXMenuBarItem | 44 | 39 | label |
| 정렬 | Keynote | AXMenuBarItem | 117 | 39 | label |
| 정렬 | 파일 | AXMenuBarItem | 160 | 39 | label |
| 정렬 | 편집 | AXMenuBarItem | 203 | 39 | label |
| 정렬 | 삽입 | AXMenuBarItem | 246 | 39 | label |
| 정렬 | 슬라이드 | AXMenuBarItem | 311 | 39 | label |
| 정렬 | 포맷 | AXMenuBarItem | 354 | 39 | label |
| 정렬 | 정렬 | AXMenuBarItem | 397 | 39 | label |
| 정렬 | 보기 | AXMenuBarItem | 440 | 39 | label |
| 정렬 | 재생 | AXMenuBarItem | 483 | 39 | label |
| 정렬 | 윈도우 | AXMenuBarItem | 537 | 39 | label |
| 정렬 | 도움말 | AXMenuBarItem | 591 | 39 | label |
| 정렬 | 무제.key | AXImage | 1052 | 45 | label |
| 정렬 | 무제.key | AXStaticText | 1107 | 60 | label |
| 정렬 | 보기 | AXMenuButton | 194 | 93 | label |
| 정렬 | 확대/축소 | AXMenuButton | 257 | 93 | label |
| 정렬 | 슬라이드 추가 | AXCheckBox | 331 | 93 | label |
| 정렬 | 재생 | AXButton | 671 | 93 | label |
| 정렬 | 표 | AXCheckBox | 1006 | 93 | label |
| 정렬 | 차트 | AXCheckBox | 1054 | 93 | label |
| 정렬 | 텍스트 | AXButton | 1102 | 93 | label |
| 정렬 | 도형 | AXCheckBox | 1150 | 93 | label |
| 정렬 | 미디어 | AXMenuButton | 1202 | 93 | label |
| 정렬 | 주석 | AXButton | 1250 | 93 | label |
| 정렬 | 공유 | AXButton | 1589 | 93 | label |
| 정렬 | 포맷 | AXRadioButton | 1937 | 93 | label |
| 정렬 | 애니메이션 | AXRadioButton | 1994 | 93 | label |
| 정렬 | 문서 | AXRadioButton | 2051 | 93 | label |
| 정렬 | 스타일 | AXRadioButton | 1877 | 122 | label |
| 정렬 | 텍스트 | AXRadioButton | 1966 | 122 | label |
| 정렬 | 정렬 | AXRadioButton | 2059 | 122 | label |
| 정렬 | 텍스트 | AXTextField | 237 | 129 | label |
| 정렬 | 텍스트 상자 삽입 | AXImage | 195 | 133 | label |
| 정렬 |  | AXCell | 320 | 137 | xy |
| 정렬 | 프레젠테이션 부제 | AXTextField | 283 | 163 | label |
| 정렬 |  | AXButton | 1858 | 166 | xy |
| 정렬 |  | AXButton | 1916 | 166 | xy |
| 정렬 |  | AXButton | 1984 | 166 | xy |
| 정렬 |  | AXButton | 2042 | 166 | xy |
| 정렬 | 텍스트 상자 삽입 | AXImage | 195 | 167 | label |
| 정렬 |  | AXCell | 320 | 171 | xy |
| 정렬 | 프레젠테이션 제목 | AXTextField | 283 | 197 | label |
| 정렬 | 텍스트 상자 삽입 | AXImage | 195 | 201 | label |
| 정렬 |  | AXCell | 320 | 205 | xy |
| 정렬 | 정렬 | AXMenuButton | 1915 | 223 | label |
| 정렬 | 배열 | AXMenuButton | 2041 | 223 | label |
| 정렬 | 저자 및 날짜 | AXTextField | 267 | 231 | label |
| 정렬 | 텍스트 상자 삽입 | AXImage | 195 | 235 | label |
| 정렬 |  | AXCell | 320 | 239 | xy |
| 정렬 |  | AXButton | 1952 | 266 | xy |
| 정렬 |  | AXButton | 2041 | 266 | xy |
| 정렬 | 1730pt | AXTextField | 1936 | 277 | label |
| 정렬 |  | AXButton | 1952 | 277 | xy |
| 정렬 | 366pt | AXTextField | 2025 | 277 | label |
| 정렬 |  | AXButton | 2041 | 277 | xy |
| 정렬 | 비율 유지 | AXCheckBox | 2055 | 316 | label |
| 정렬 |  | AXButton | 1952 | 345 | xy |
| 정렬 |  | AXButton | 2041 | 345 | xy |
| 정렬 | 위치 | AXStaticText | 1871 | 355 | label |
| 정렬 |  | AXButton | 1952 | 356 | xy |
| 정렬 |  | AXButton | 2041 | 356 | xy |
| 정렬 | 95pt | AXTextField | 1936 | 357 | label |
| 정렬 | 203pt | AXTextField | 2025 | 357 | label |
| 정렬 |  | AXButton | 1952 | 441 | xy |
| 정렬 |  | AXButton | 1952 | 452 | xy |
| 정렬 | 0° | AXTextField | 1936 | 453 | label |
| 정렬 | 수평으로 뒤집습니다 | AXButton | 1998 | 453 | label |
| 정렬 | 수직으로 뒤집습니다 | AXButton | 2041 | 453 | label |
| 정렬 | 잠금 | AXButton | 1915 | 517 | label |
| 정렬 | 잠금 해제 | AXButton | 2041 | 517 | label |
| 정렬 | 그룹화 해제 | AXButton | 2041 | 552 | label |
| 정렬 | 그룹화 | AXButton | 1915 | 553 | label |
| 정렬 | 슬라이드 대상체 필터 | AXButton | 325 | 1320 | label |
| 정렬 |  | AXTextField | 304 | 1325 | xy |
| 정렬 | 검색 | AXButton | 171 | 1326 | label |
| 정렬 | 검색 | AXButton | 25 | 1329 | label |
| 정렬 | 무제.key | AXWindow | 2056 | 1329 | label |
| 정렬 |  | AXTextField | 341 | 1330 | xy |
| 정렬 | 검색 결과 | AXTable | 361 | 1330 | label |
| 텍스트 | Apple | AXMenuBarItem | 44 | 39 | label |
| 텍스트 | Keynote | AXMenuBarItem | 117 | 39 | label |
| 텍스트 | 파일 | AXMenuBarItem | 160 | 39 | label |
| 텍스트 | 편집 | AXMenuBarItem | 203 | 39 | label |
| 텍스트 | 삽입 | AXMenuBarItem | 246 | 39 | label |
| 텍스트 | 슬라이드 | AXMenuBarItem | 311 | 39 | label |
| 텍스트 | 포맷 | AXMenuBarItem | 354 | 39 | label |
| 텍스트 | 정렬 | AXMenuBarItem | 397 | 39 | label |
| 텍스트 | 보기 | AXMenuBarItem | 440 | 39 | label |
| 텍스트 | 재생 | AXMenuBarItem | 483 | 39 | label |
| 텍스트 | 윈도우 | AXMenuBarItem | 537 | 39 | label |
| 텍스트 | 도움말 | AXMenuBarItem | 591 | 39 | label |
| 텍스트 | 무제.key | AXImage | 1052 | 45 | label |
| 텍스트 | 무제.key | AXStaticText | 1107 | 60 | label |
| 텍스트 | 보기 | AXMenuButton | 194 | 93 | label |
| 텍스트 | 확대/축소 | AXMenuButton | 257 | 93 | label |
| 텍스트 | 슬라이드 추가 | AXCheckBox | 331 | 93 | label |
| 텍스트 | 재생 | AXButton | 671 | 93 | label |
| 텍스트 | 표 | AXCheckBox | 1006 | 93 | label |
| 텍스트 | 차트 | AXCheckBox | 1054 | 93 | label |
| 텍스트 | 텍스트 | AXButton | 1102 | 93 | label |
| 텍스트 | 도형 | AXCheckBox | 1150 | 93 | label |
| 텍스트 | 미디어 | AXMenuButton | 1202 | 93 | label |
| 텍스트 | 주석 | AXButton | 1250 | 93 | label |
| 텍스트 | 공유 | AXButton | 1589 | 93 | label |
| 텍스트 | 포맷 | AXRadioButton | 1937 | 93 | label |
| 텍스트 | 애니메이션 | AXRadioButton | 1994 | 93 | label |
| 텍스트 | 문서 | AXRadioButton | 2051 | 93 | label |
| 텍스트 | 스타일 | AXRadioButton | 1877 | 122 | label |
| 텍스트 | 텍스트 | AXRadioButton | 1966 | 122 | label |
| 텍스트 | 정렬 | AXRadioButton | 2059 | 122 | label |
| 텍스트 | 텍스트 | AXTextField | 237 | 129 | label |
| 텍스트 | 텍스트 상자 삽입 | AXImage | 195 | 133 | label |
| 텍스트 |  | AXCell | 320 | 137 | xy |
| 텍스트 | 프레젠테이션 부제 | AXTextField | 283 | 163 | label |
| 텍스트 | 업데이트 | AXButton | 2041 | 166 | label |
| 텍스트 | 텍스트 상자 삽입 | AXImage | 195 | 167 | label |
| 텍스트 |  | AXCell | 320 | 171 | xy |
| 텍스트 | 제목* | AXButton | 1980 | 173 | label |
| 텍스트 | 프레젠테이션 제목 | AXTextField | 283 | 197 | label |
| 텍스트 | 텍스트 상자 삽입 | AXImage | 195 | 201 | label |
| 텍스트 |  | AXCell | 320 | 205 | xy |
| 텍스트 | 스타일 | AXRadioButton | 1910 | 227 | label |
| 텍스트 | 레이아웃 | AXRadioButton | 2031 | 227 | label |
| 텍스트 | 저자 및 날짜 | AXTextField | 267 | 231 | label |
| 텍스트 | 텍스트 상자 삽입 | AXImage | 195 | 235 | label |
| 텍스트 |  | AXCell | 320 | 239 | xy |
| 텍스트 | 서체 | AXStaticText | 1824 | 275 | label |
| 텍스트 | Helvetica Neue | AXPopUpButton | 2041 | 308 | label |
| 텍스트 |  | AXButton | 2041 | 326 | xy |
| 텍스트 | 볼드체 | AXPopUpButton | 1962 | 337 | label |
| 텍스트 | 116pt | AXTextField | 2025 | 337 | label |
| 텍스트 |  | AXButton | 2041 | 337 | xy |
| 텍스트 |  | AXButton | 2041 | 368 | xy |
| 텍스트 | 볼드체 | AXCheckBox | 1842 | 369 | label |
| 텍스트 | 이탤릭체 | AXCheckBox | 1882 | 369 | label |
| 텍스트 | 밑줄체 | AXCheckBox | 1922 | 369 | label |
| 텍스트 | 취소선 | AXCheckBox | 1964 | 369 | label |
| 텍스트 | 문자 스타일 | AXStaticText | 1858 | 396 | label |
| 텍스트 | 없음 | AXButton | 2041 | 399 | label |
| 텍스트 | 텍스트 색상 | AXPopUpButton | 1876 | 444 | label |
| 텍스트 | 왼쪽 | AXCheckBox | 1862 | 498 | label |
| 텍스트 | 가운데 | AXCheckBox | 1921 | 498 | label |
| 텍스트 | 오른쪽 | AXCheckBox | 1980 | 498 | label |
| 텍스트 | 좌우 정렬 | AXCheckBox | 2041 | 498 | label |
| 텍스트 | 단락 정렬 | AXGroup | 2039 | 500 | label |
| 텍스트 | 단락 수준 | AXGroup | 2039 | 529 | label |
| 텍스트 | 들여쓰기 감소 | AXCheckBox | 1921 | 530 | label |
| 텍스트 | 들여쓰기 증가 | AXCheckBox | 2041 | 530 | label |
| 텍스트 | 상단 | AXCheckBox | 1881 | 559 | label |
| 텍스트 | 중앙 | AXCheckBox | 1960 | 559 | label |
| 텍스트 | 세로 정렬 | AXGroup | 2039 | 559 | label |
| 텍스트 | 하단 | AXCheckBox | 2041 | 559 | label |
| 텍스트 | 세로 텍스트 | AXCheckBox | 1883 | 603 | label |
| 텍스트 | 간격 | AXStaticText | 1839 | 649 | label |
| 텍스트 | 0.8 | AXPopUpButton | 2041 | 652 | label |
| 텍스트 | 구분점 및 목록 | AXStaticText | 1887 | 697 | label |
| 텍스트 | 없음 | AXButton | 2041 | 700 | label |
| 텍스트 | 슬라이드 대상체 필터 | AXButton | 325 | 1320 | label |
| 텍스트 |  | AXTextField | 304 | 1325 | xy |
| 텍스트 | 검색 | AXButton | 171 | 1326 | label |
| 텍스트 | 검색 | AXButton | 25 | 1329 | label |
| 텍스트 | 무제.key | AXWindow | 2056 | 1329 | label |
| 텍스트 |  | AXTextField | 341 | 1330 | xy |
| 텍스트 | 검색 결과 | AXTable | 361 | 1330 | label |

## VERIFIED LIVE
- opacity_stepper: 100%→97% via down xy 2034,548
- opacity_drag: 97%→35% drag 1920,542→1860,542
- font_size_stepper: 116pt→114pt down 2034,332
- align_w_field: 1730pt→500pt field 1903,266
- fs_after: 전체 화면 종료 still in 보기 menu

## BAN
- green traffic light (toggles FS off)
- 전체 화면 종료 / 재생 / Keynote 종료 / Terminal / osascript
- invent coords without dump (INV1)
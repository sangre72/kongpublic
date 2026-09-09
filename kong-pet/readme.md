# 🐾 KongPet

종(강아지/고양이/물고기)을 고르면 귀여운 캐릭터가 모든 웹페이지 우측 하단에 상주하는 Chrome 확장 프로그램 (Manifest V3).

## 흐름 (a_3819 피벗: AI 불필요)
1. **설정(옵션 페이지)** 에서 🐶강아지 / 🐱고양이 / 🐠물고기 중 하나 선택.
2. 종별 포즈 미리보기 확인 + 펫 이름 입력 → **이 캐릭터로 결정**.
3. 모든 페이지 우측 하단에 캐릭터가 상주(포즈 순환 애니메이션), 클릭하면 반응(bounce + 말풍선).

## 캐릭터 아트 (고정 번들)
- 사진 업로드/AI 분석 **없음**. 종별 캐릭터는 **미리 생성된 고정 아트**를 확장에 번들(`assets/pets/<species>/<pose>.png`, 256×256).
- 아트 출처: 로컬 krea2(ComfyUI GGUF T2I) 생성 (RECIPE_krea2_gguf_t2i.txt). 외부 API·키 불필요.
- 포즈 세트: 강아지 idle/wag/tilt · 고양이 idle/loaf(식빵)/groom(세수) · 물고기 idle/flare.
- **애니메이션(a_3820)**: 포즈 전환 = 이중 레이어 크로스페이드(0.22s), idle 순환 = 5.5~9.5s 랜덤 홀드 + 30% 확률 double-idle(더 자연스러움), 클릭 시 non-idle 포즈로 팝.
- **살아있는 미세모션(a_3822, Path B)**: 정적 포즈 이미지에 CSS 절차적 모션 — 육상동물=호흡(가벼운 세로 squash-stretch 3.6s), 물고기=헤엄(상하 bob + 좌우 회전 3s). 비디오 없이 "살아있는" 느낌. `prefers-reduced-motion` 존중.
  - ※ Path A(MiniMax i2v 비디오)는 테스트했으나 채택 안 함 — 아래 참고.

## ⏸ Path A (MiniMax i2v 비디오) — 테스트 후 미채택
- RECIPE_minimax_h3_i2v.txt 파이프라인으로 강아지 합성이미지(캐릭터+배경)→루프 비디오 생성 시도(turbo 196s, quality 380s per 0.9s 클립).
- **결과: 두 프리셋 모두 순수 검정 출력**(8KB mp4, 전 프레임 픽셀값 0). first_frame 입력 시 MPS nvfp4/awq 양자화 경로 문제(레시피에 문서화된 취약점). 육안 QA로 확인.
- **미채택 사유**(품질 문제 외에도): ①클립당 200~380초로 종×상태 조합 다수엔 비현실적, ②MiniMax H3 커뮤니티 라이선스가 한국 self-host 전면 제외 → 배포용 확장에 부적합, ③`<video>` 다수 번들 = 확장 용량 급증. Path B(절차적 CSS)가 배포 관점에서도 정답.
- **비주얼 QA(a_3821, 필수 프로세스)**: 모든 생성 이미지는 셰이핑 전 Read 도구로 실제 육안 확인 후에만 번들. (이전 fish/idle 곰-물고기 키메라 버그 재발 방지.)

## 배경 장면 (16:9, a_3821)
- 종별 16:9 배경 씬 번들(`assets/bg/*.jpg`, 640×360): 강아지=들녘(dog_field), 고양이=집(cat_home), 물고기=어항(fish_aquarium)/밤바다(fish_nightsea, 선택).
- 위젯 우측 하단에 라운드 "무대(stage)" 카드로 배경 표시, 그 위에 캐릭터가 떠 있음. 옵션 페이지에서 배경 선택 가능(물고기는 2종).
- krea2 동일 파이프라인 생성, 캐릭터/동물 없는 빈 씬(negative에 명시).

## ⏸ 사진 개인화 (향후 재도입 가능, 현재 보류)
- 이전 설계(a_3815/3816/3817)는 사진 업로드 → Gemini vision 분석 → Gemini 이미지 생성(멀티 스타일 옵션 선택)이었으나, u_4023 "AI 필요없어, 단순해서"로 **드롭**.
- 관심 있으면 되살릴 수 있는 미래 기능으로 보존: 사진→개인화 아바타(Gemini `gemini-2.5-flash` 분석 + `gemini-2.5-flash-image` 생성, user-supplied 키). git 히스토리(a_3817 시점 background.js)에 구현 존재.

## 설치(개발자 모드)
`chrome://extensions` → 개발자 모드 ON → "압축해제된 확장 프로그램을 로드" → `kong-pet/` 선택.

## 파일 구조
- `manifest.json` — MV3, content_scripts(전 페이지), options_ui, service_worker.
- `background.js` — Gemini 분석 + 멀티옵션 이미지 생성(병렬, `Promise.allSettled`).
- `options.html` / `options.js` — 키/사진 업로드 UI, 옵션 그리드, 선택.
- `content/pet-widget.js` + `.css` — 상주 오버레이 위젯, idle/클릭 반응.

## 동물 종류 & idle 포즈 (a_3817)
설정에서 🐶강아지 / 🐱고양이 / 🐠물고기 선택 → 종별 idle 포즈 세트가 적용됩니다.
- 포즈는 **스프라이트시트 1장이 아니라 포즈마다 개별 이미지 호출**로 생성(더 저렴·안정적), `chrome.storage.local`에 상태별 저장, 위젯이 ~8초마다 순환.
- 강아지: idle(앉기) / wag(꼬리흔들) / tilt(고개갸웃)
- 고양이: idle(앉기) / loaf(식빵자세) / groom(세수)
- 물고기: idle(헤엄) / flare(지느러미 펼침)

## 쿠팡파트너스 추천 위젯 (a_3817)
위젯 위에 4-슬롯 패널(위→아래):
1. **광고** — 시각적 자리만 예약(placeholder, "광고" 라벨). 실제 광고 서빙 로직은 향후.
2. **오늘의 베스트** — Coupang **카테고리별 베스트상품** 엔드포인트(`.../products/bestcategories/{categoryId}`, 반려동물용품 catId=1010). 검색 API엔 인기순 정렬이 없어 별도 엔드포인트 사용.
3. **할인 베스트** — 종별 키워드 검색 결과 중 최고 할인율.
4. **신상품** — 종별 키워드 검색 결과의 최신 항목.
- 종→키워드: dog→"강아지 용품", cat→"고양이 용품", fish→"어항 용품".
- **10 calls/hr 제한**: 결과를 `chrome.storage.local`에 캐시(1일 1회 갱신), 렌더마다 호출 안 함. 위젯 1회 로드 = 총 2 API콜(best-category + search).
- 쿠팡 키(Access/Secret) 없으면 패널만 조용히 비활성(펫 아바타는 정상).
- 서명: HMAC-SHA256, `CEA algorithm=HmacSHA256, access-key=…, signed-date=YYMMDDTHHMMSSZ, signature=…` (service worker `crypto.subtle`).

## 이번 패스 범위 (a_3819 기준)
- ✅ 종 선택 → 고정 번들 아트 → 이름 → 상주.
- ✅ 클릭 반응 + idle 포즈 순환.
- ✅ 쿠팡 4-슬롯 추천 패널.
- ⏭ 향후 슬롯: 나이/종 세부맞춤, 계절한정, 최근본상품, 커뮤니티인기.
- ⏭ 향후: 사진 개인화(위 보류 항목), 의상 커스터마이즈, 리더보드, 공동 육성 소셜(Happy Dog류).

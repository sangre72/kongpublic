# LOGIN-HANDOFF (session-dead → user logs in on phone)

> orch+worker standing recipe. ANY site login wall → send that site's remote method **now**. no ask-first. no live re-research.

## RULES

| # | rule |
|---|------|
| 1 | **0 password type** — never type pw / OTP / 6-digit / recovery. |
| 2 | **0 secret in ar/tg** — no pw, OTP, 6-digit, recovery, `qrcodesession`. shot only. |
| 3 | **wall = needs-info STOP** after sendPhoto+KO. do not keep clicking. |
| 4 | **already-inbox / already-in** (goal screen, not wall) = **continue task**. |
| 5 | site default **known** → **do not ask** "어느 방법?". |
| 6 | only **screen-shown** or **cited typical**. never invent QR/prompt. |
| 7 | unverified site → send **wall shot** + documented-if-any caption + mark UNVERIFIED. |

## FLOW (every wall)

```
URL+a11y detect wall?
  NO + on goal screen → CONTINUE original task
  YES → open that site's default remote UI (table)
      → shot method (or wall if none shown)
      → tg sendPhoto chat <CHAT_ID> caption=KO (table)
      → ar [STATUS] needs-info STOP
user finishes on phone
session back / inbox → resume original task
```

Send: `telegram_io.send_photo_file` · load `orchestrator/.env` like `scripts/ask_telegram.py` · caption KO ≤1024 · CHAT `<CHAT_ID>`(from `orchestrator/.env` `TELEGRAM_CHAT_ID`).

## 1-page table

| site | detect (URL / a11y) | send-what (immediate) | user-does | then-resume |
|------|---------------------|------------------------|-----------|-------------|
| **Naver** VERIFIED ar_62 | URL `nid.naver.com` / `nidlogin` / `mode=qrcode`. a11y win/AXWebArea=`NAVER 로그인`. fields 아이디·비밀번호. btn `QR 코드 로그인` / `패스키` / `일회용 번호`. QR shown: AXImage=`QR Code` + heading=`QR 코드를 촬영하고 로그인 하세요`. | click **QR 코드 로그인** (no ask). shot QR (+ optional full methods). caption **`네이버 QR 로그인 — 폰에서 네이버앱 스캔`**. | 네이버앱 → 검색창 옆 렌즈 → QR 스캔 → 확인숫자 탭. 만료(~3min)면 워커가 QR 재클릭(ar_64). | mail/goal URL 재진입. inbox=continue. |
| **Google** DOC typical | URL `accounts.google.com` (`identifier` / `challenge` / `ServiceLogin`) · gmail/youtube sign-in. a11y: `Check your phone` / `Google sent a notification` / `Tap Yes` / `Use your passkey` / `Try another way` / `로그인`. | **if prompt shown** → shot that. caption **`구글 로그인 — 폰 알림에서 예`**. **if passkey/QR shown** → shot that. caption **`구글 패스키 — 폰에서 확인/QR 스캔`**. no prompt yet + account chooser → click known account only (no pw). empty-id-only wall → send wall (do not type pw). | 폰 Google 알림 **Yes** ([prompt](https://support.google.com/accounts/answer/7026266)). or 패스키/폰 QR ([passkey](https://support.google.com/accounts/answer/13548313) § phone passkey). | goal URL. signed-in=continue. |
| **Facebook** UNVERIFIED remote-first | URL `facebook.com/login` · `m.facebook.com`. a11y `Log in` / 이메일·비밀번호. | **if passkey or "confirm/approve login" shown** → shot that. caption **`페이스북 — 폰 앱에서 로그인 승인`**. else wall shot. caption **`페북 로그인벽 — 폰에서 승인/패스키. 비번 입력 안 함 (미검증)`**. no facebook.com QR-login in help (Messenger/group QR ≠ login; device-login QR = apps only). | 폰 Facebook 앱: 2FA **승인** 또는 패스키. ([2FA confirm](https://www.facebook.com/help/148233965247823) · [approve recognized device](https://www.facebook.com/help/132694786861712) · [passkey](https://www.facebook.com/help/1181045243159511)). | goal URL. |
| **X / Twitter** UNVERIFIED remote-first | URL `x.com/i/flow/login` · `twitter.com/i/flow/login` · `x.com/login`. a11y `Sign in to X`. | **if passkey shown** → shot. caption **`X 패스키 — 폰/기기에서 확인`**. else wall shot. caption **`X 로그인벽 — 패스키 있으면 폰에서. 비번 입력 안 함 (미검증)`**. official X QR = follow, **not** login ([QR](https://help.x.com/en/using-x/qr-codes)). | 폰에서 **passkey** ([help](https://help.x.com/en/managing-your-account/how-to-use-passkey)). 2FA app/code is after password — worker never types it. | goal URL. |
| **Apple** UNVERIFIED remote-first | URL `appleid.apple.com` · `idmsa.apple.com` · `account.apple.com`. a11y `Apple ID` / `Apple Account` / verification-code. | **if trusted-device / code-wait shown** → shot (no code in caption). caption **`Apple 로그인 — 폰에서 허용. 코드는 직접 입력`**. else wall shot. caption **`Apple 로그인벽 — 신뢰기기에서 허용 (미검증, QR없음)`**. | 신뢰기기 알림 **Allow** → 6자리. user types code on Mac (worker never types). ([102606](https://support.apple.com/en-us/102606) · [102660](https://support.apple.com/en-us/102660)). | goal URL. |
| **OTHER** | login/signin URL · a11y password field + Log in / 로그인 · heading 로그인. | wall shot. caption **`로그인벽 — 폰에서 원격 가능하면 처리. 방법 모름`**. do not invent QR. | user finishes on phone if they can. | goal URL or user says skip. |

## Naver (do not re-research)

Reuse **a_62 / ar_62** only. QR click → shot → KO "폰에서 네이버앱 스캔". methods on that screen: QR · 아이디·비번 링크 · 찾기/가입. pre-QR wall also had 패스키 · 일회용번호. default=QR always.

## Cite (no invent)

| site | source | what is documented | what is NOT |
|------|--------|--------------------|-------------|
| Naver | ar_62 screen 2026-08-14 | QR login + 확인숫자 | — |
| Google | [7026266](https://support.google.com/accounts/answer/7026266) prompt · [13548313](https://support.google.com/accounts/answer/13548313) passkey/phone-QR | phone tap / passkey | this-run live UI |
| Facebook | [148233965247823](https://www.facebook.com/help/148233965247823) · [132694786861712](https://www.facebook.com/help/132694786861712) · [1181045243159511](https://www.facebook.com/help/1181045243159511) | 2FA confirm/approve · passkey | facebook.com QR-login (unverified; not in help) |
| X | [passkey](https://help.x.com/en/managing-your-account/how-to-use-passkey) · [2FA](https://help.x.com/en/managing-your-account/two-factor-authentication) · [QR=follow](https://help.x.com/en/using-x/qr-codes) | passkey · 2FA after pw | desktop QR-login (unverified; QR help ≠ login) |
| Apple | [102606](https://support.apple.com/en-us/102606) · [102660](https://support.apple.com/en-us/102660) | Allow on trusted device + 6-digit | passwordless/QR web login (unverified) |

UNVERIFIED = Facebook · X/Twitter · Apple (no Naver-style remote-first verified on screen; no official web QR-login).

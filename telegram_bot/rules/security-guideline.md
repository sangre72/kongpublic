# Security guideline — malicious-script/XSS prevention (MUST, user 2026-08-01)

> # ⭐ TOP principle (user 2026-08-01): security check = always highest priority
> **Security check + standard-compliance = this project's absolute top.** Ahead of any feature·schedule·convenience.
> XSS·injection·auth-bypass·secret-leak·malicious-file etc = **done condition** — not done without security check (sanitize·CSP·file-verify·auth) passing.
> New screen·input·file·API added → security check mandatory. All workers·all tasks, always on.

> **Prevent security-violating script use(보안위배 스크립트 방지).** User·external input (command·text·uploaded file·API param etc): block malicious script (`<script>`, `on*=`, `javascript:`, `data:` etc) or injection payload from being planted·executed at root. Sensitive info → security = top axis w/ standard-compliance.

All tasks of this project(incl orchestrator·worker) always on.

## 1. XSS/injection prevention (input→store→render/exec whole path)
- **No direct HTML/markup render(직접렌더 금지)** — only after **sanitize**.
  - Rich text(HTML) body = **2-layer defense**:
    1. **On store(server)**: allowlist tags/attrs only. Strip `<script>`·`on*`·`style`·`javascript:`/`data:` URL·`<iframe>`(outside allowlist).
    2. **On render(defensive)**: re-sanitize w/ DOM-sanitize lib then show.
  - Allowed tags (rich-text output only): p,br,strong,em,u,s,h1~h4,ul,ol,li,blockquote,a,img,table/tr/th/td,code,pre.
  - `a[href]`=http/https/mailto only + rel="noopener noreferrer". `img[src]`=allowed domains(self/CDN) only, alt.
- **Plain-text input**(non-HTML): no markup render → default escape safe. No raw HTML insertion.
- **Command/shell/external-process call**: don't compose user input directly into shell string — pass via arg array·param binding(prevent command injection).
- Server·worker: **don't trust input(입력 신뢰 금지)** — schema validate + sanitize. Client/caller-side validation alone not trusted.

## 2. CSP (Content-Security-Policy) hardening (when web UI/dashboard exists)
- If web-exposed screen exists, minimize script-exec surface via CSP.
  - `script-src 'self'` base + allow needed scripts via nonce/hash. Remove inline script(`unsafe-inline`)·`unsafe-eval` in prod.
  - `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`(clickjacking), `form-action 'self'`, `connect-src` self+allowed origins.
  - No authz decision on proxy/middleware alone — re-verify at actual handler(CVE-2025-29927 class).

## 3. File-upload/input-file security (attachment·media·download asset)
- Executable files (exe/js/html/svg etc script-capable) **block**. MIME·ext allowlist.
- Stored filename = **server random gen**(prevent path-traversal·overwrite), don't trust original filename. Block traversal(`../`) on path compose.
- SVG = XSS vector → block or sanitize. Consider image re-encode.
- Private files = serve via auth, no direct exposure.

## 4. Etc
- Auth/authz: don't rely on token·session verify at request entry alone — re-verify at actual handler.
- External API/network calls via common client layer → consistent auth-fail·error handling(0 stale-data leak on error).
- Secrets: env/server-only, no client/public-channel exposure, no commit.
- Query/command: use param binding·arg array(watch injection on string compose).
- Deps: periodic vulnerable-package check.

## Verify
- Input·render paths: **XSS/injection payload injection test**(`<script>`, `<img onerror>`, `javascript:` link, shell metachar) neutralized on store·render·exec.
- 0 non-sanitized markup render paths.

Rationale: user "prevent security-violating script use". 2-layer defense(store sanitize + render re-sanitize). Sensitive-info-handling service.

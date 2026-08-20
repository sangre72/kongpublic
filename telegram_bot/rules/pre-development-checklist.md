# Dev start·done checklist (MUST — derived from full audit)

> After initial core features(auth·data processing·I/O) impl, **multi-perspective full audit** derived gate, applied to all feature dev.
> Kept **together with** existing rules(security·naming·modularization etc) — this doc = their summary gate.
> Security detail: [security-guideline.md](./security-guideline.md), network saving: [network-budget.md](./network-budget.md).

## ★ Absolute top axes (done conditions)
1. **Security** — no done without below security items passing.
2. **Naming consistency** — new identifier/field name = no done without following project naming convention.

---

## A. Before start (design) — write first
- [ ] **Create field/input list** written, **Update = same list + attachment parity** designed (feature-consistency).
- [ ] **Permission/role×feature table**(role × feature) draft.
- [ ] **New field/identifier** → project naming-convention mapping → fix type/length.
- [ ] **mock if needed**: only in designated mock location. **No direct mock import in core modules**(via injection).
- [ ] **Module boundary**: external exposure via public interface(barrel/`__init__` etc) only. No circular-ref violation.

## B. During impl — Security (top)
- [ ] **Don't trust input(입력 신뢰 금지)**: server·worker entry point schema validate + sanitize. Caller-side validation alone not trusted.
- [ ] **XSS/injection**: text = default escape(no markup render). Rich HTML = sanitize 2-layer(store sanitize + render re-sanitize). Raw HTML only after sanitize. Command·shell call = arg array/param binding(no string compose).
- [ ] **Authz**: UI hide ≠ authz. Mutation handler: role·**ownership re-verify**. No entry-point(middleware/proxy)-only authz(CVE-2025-29927 class).
- [ ] **No response exposure**: don't put internal identifier·email·password·internal mapping key in response. Public identifier only.
- [ ] **File upload/input file**: ext+MIME allowlist, block exec/script/SVG/HTML, stored filename server-random, private file auth-serving, block path traversal.
- [ ] **Secrets**: env·server-only. No signing·auth w/ fallback constant(fail if unset). No public-channel exposure·no commit.
- [ ] **Rate-limit**: sensitive paths(auth·state-change·retry). ※ in-memory stub = **shared store(Redis etc) required before multi-instance**.

## C. During impl — API/data (when applicable)
- [ ] Interface standard: query/create/update/delete ops with consistent convention. (HTTP API → GET/POST/PATCH/DELETE.)
- [ ] Response format unified: success/error envelope consistent. validation error detail = `{issues:[{path,message}]}` unified.
- [ ] Paging: page/size convention, size cap. Bulk query = store-side search(no memory filter). Sort param convention.
- [ ] Error: try/except, no stack·internal-raw exposure, status·branch judged by **structured error code**(no natural-language string matching).
- [ ] Schema/interface doc register — 0 miss on endpoint/handler add.
- [ ] Store: audit-columns·NOT NULL·DEFAULT·constraint·FK·index·**soft-delete flag + query-time filter**·high-freq-update = version optimistic lock. Polymorphic ref = orphan-cleanup plan.

## D. During impl — UI/accessibility (when UI/dashboard exists)
- [ ] Design tokens only(no hardcoded color), verify light/dark.
- [ ] Semantic markup·heading hierarchy·keyboard op·focus-visible·contrast AA.
- [ ] Form: label + aria-invalid + aria-describedby(error), required mark + sr-only "(필수)".
- [ ] Image alt, icon aria-label/aria-hidden, toggle aria-pressed, state-change aria-live.
- [ ] Status badge = color+text together. empty/skeleton/error state UI.
- [ ] List/view pattern(view-switch·search-filter-sort·paging·URL-sync) reuse.

## E. Before done — verify gate (no done without passing)
- [ ] **Parity one-line check**: every field·attachment made on create — **viewable·changeable in update path?** No → no done.
- [ ] **Security scenario**: self allow / other deny / admin(per policy) / unauth deny. XSS·injection payload neutralized.
- [ ] **Naming**: input key·schema key·field name = project convention. New word registered in convention.
- [ ] **Static-analysis·type-check 0 error** + change-related tests(+ UI = accessibility violation 0). Related tests+core-regression instead of full re-run(network saving).
- [ ] **End-to-end completeness**: backend op has matching call? / UI/output shows real data? / data passed between steps?
- [ ] **Permission/role×feature table** final left in result.

## F. Before deploy/operation (P0 — else prod breaks)
- [ ] Inject stable identifier as fixed env across deploys(prevent session·state break on redeploy/scale-out).
- [ ] Config boot-validation(process exit if required secret·connection-info unset).
- [ ] Healthcheck(liveness·readiness) + graceful shutdown(SIGTERM→drain→connection cleanup).
- [ ] Containerize(non-root) + persistent storage real impl(prevent local-disk loss).
- [ ] Migration automation(idempotent runner), backup(point-in-time recovery).
- [ ] **Access-audit log**(sensitive-info query record) load.
- [ ] CSP hardening(remove `unsafe-eval`→nonce→enforce), rate-limit shared store, custom error page, fixed timezone.

Rationale: user "as guide for future dev find·check issues, security·naming = top level". Multi-perspective full audit.

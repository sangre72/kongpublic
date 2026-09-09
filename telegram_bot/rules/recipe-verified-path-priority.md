# Recipe verified-path priority (MUST — u_4037/4038 2026-09-06)

> recipe∋multi-path(old-vs-new,quant-A-vs-B) → verified-working=TOP+★USE-FIRST, broken-path=★USE-BAN@top(¬buried-mid-file). worker reads top-down, stale-first-listed=re-fail-repeat.

## Trigger
recipe-file history-accumulates(A tried→failed→B found-working, but A stays first/only note) → new session/worker re-picks A(top-listed) → repeat-fail(cf MiniMax i2v nvfp4/awq text-encoder: L7 said "GGUF forbidden,use safetensors" but safetensors=black-screen-cause, later GGUF-fix buried mid-file unread).

## Rule
1. verified-working path(latest confirmed-success, cite date+ar_ref) = **file-TOP**, marked ★★★★★USE-FIRST.
2. broken/superseded path = **also file-TOP**(not deleted, kept for history) marked ★★★★★USE-BAN + reason(1-line: what failed, how verified e.g. ffprobe+pixel-check).
3. mid-file original write-up stays(don't rewrite history) but top-banner make unambiguous which wins on conflict.
4. this applies to ANY recipe/doc where multiple attempts left conflicting guidance(kaymaps/RECIPE_*, ComfyUI workflow notes, model/quant choice notes) — not MiniMax-specific.

## Verify
new job dispatched against a multi-path recipe → orch/worker re-check top-banner FIRST before mid-file detail, confirm no conflicting "used-path" vs "banned-path" mismatch before running.

Basis: user 2026-09-06(u_4037) — KongPet MiniMax i2v test used nvfp4/awq(banned-in-practice) path causing black-screen, because the GGUF-verified-working fix from an earlier session(2026-08-28) was buried mid-recipe below the original failed-approach note. u_4038: generalize as standing .claude/rules doc, K7-compressed.

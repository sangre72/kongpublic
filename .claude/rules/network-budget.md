# Network budget rules (MUST — rewritten 2026-08-27 a_2740, was Playwright/npm-specific sky doc)

> Network only when needed. Same underlying concern as sky's origin incident(repeated reinstall = wasted GB) — re-scoped to this repo's actual heavy operations.

Applies: kong-bot repo all work(esp. worker automation, model/video pipelines).

## Forbidden
1. **No repeated `pip`/`brew`/`cargo` reinstall** — verify already-installed first(`pip show <pkg>`/`brew list`/`cargo build` cache) before reinstalling. kongtrol(Rust) = rebuild only on actual source change, not per-task.
2. **No redundant kongtrol full rebuild** — `cargo build --release` only when `kongtrol/src/*.rs` changed. Binary at `kongtrol/target/release/kongtrol` persists across sessions, verify via `test -x` first(cf kongtrol-base-reference.md).
3. **No repeated video/image re-encode** of the same source — ffmpeg/ffprobe output is deterministic; if a variant already exists in `jobs/<job>/`, verify via ffprobe metadata before regenerating from scratch.
4. **No repeated large-model download**(GGUF/safetensors weights) — check local model dir(`kong-models/` or ComfyUI models path) first, large weights are multi-GB and one-time.
5. **No unneeded WebSearch/WebFetch** — internal/local-tool impl unneeded. Research-marked task only.
6. **No remote large assets fetched when a local/generated equivalent exists** — prefer local generation(CineBot/ComfyUI/kongtrol-driven) over pulling stock assets from network.

## Allowed
- WebSearch/WebFetch on explicit research task(e.g. checking canonical character-design refs before generation, per worker_1.txt §COMFYUI-OVERNIGHT-LEARNING pt.3).
- First-time env setup(skip if already done) — new pkg needed → install that pkg only.
- Model/weight download when genuinely new(not yet in local cache) — verify absence first, don't assume.

## Verify lightweight
- Before any install/download/rebuild/re-encode: one quick existence-check command(`ls`/`pip show`/`test -x`/`ffprobe`) costs near-zero, always run it first.
- Long video-gen pipelines(CineBot 12-scene batch etc): reuse cached backend results where the recipe already notes cache-first behavior(e.g. RECIPE_fortune_12_full_flow.txt's "cache-first" tooltip) rather than forcing full-regen.

Basis: user 2026-08-27(u_2740) — prior version's Playwright/npm/tsc references don't exist in this repo(no Next.js/Playwright here); real heavy-network risks here are pip/brew/cargo reinstall, kongtrol rebuild, video re-encode, and multi-GB model downloads.

# SPEED (a_66) — how we run fast

Cite: Playwright MCP snapshot+ref (no vision) · browser-use index · agent-browser `batch` · Agent-S2 planner/executor split. Anti-pattern: Claude CU / OpenAI CUA shot-every-step.

| Do | Don't |
|----|-------|
| `kongtrol --yes input run seq` (1 dump→N acts) | per-step LLM after each click |
| `see --a11y --compact` | dump full JSON into worker chat |
| orch milestone shot | worker Read(png) between steps |
| VL unlabeled only | local UI-TARS (90s+ BANNED) |

Seq verbs: `app` `dump` `click_label` `dbl_label` `click` `key` `chord` `text` `wait`

Target: labeled step after dump <0.5s. ground.sh cache TTL=5s = fallback only.

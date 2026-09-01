# Cognitive-Science-Inspired Judgment-Model Synthesis (2026-08-31)

Original-thinking research task(u_3212~3213): draw on cognitive science/humanities/embodied cognition/
disability-compensation patterns to find a genuinely novel angle beyond standard ML distillation, since
the plain "distill a small model" framing(task3) doesn't by itself explain HOW to reach human-level
judgment speed+accuracy.

## 1. Fast accurate judgment without millions of examples
Predictive-coding/Bayesian-brain research + chunking/expertise research(chess masters, NDM) converge on:
experts don't perceive faster from scratch — they've compiled situation→typical-response TEMPLATES
(chunks), collapsing recognition+action-selection into one retrieval step. A GUI button/modal-dismiss-X
is a "chunk," not a fresh classification target every time.

**Architectural implication**: two-speed system — (a) fast amortized matcher against a growing chunk-
library(learned UI-state→action templates, cheap retrieval), gated by (b) confidence/precision estimate
that falls back to slow deliberate reasoning(VLM) only when novel/low-confidence. The chunk library GROWS
by promoting successful slow-path episodes into the fast cache(mirrors Fitts' motor-learning stages:
cognitive→associative→autonomous) — not offline-curated training data.

## 2. Direct perception-action coupling(Gibson affordances, sensorimotor contingency theory)
Skilled action isn't perceive→classify→plan→act — it's direct coupling(perceiving IS detecting action-
possibility). Maps to: instead of "screenshot→classify all elements→scene-graph→LLM-plans→click," want a
model that directly outputs "clickable-here, toward-this-goal" from joint (screen-state, goal) — action
head SHARES representation with perception head, trained jointly, not chained as 2 serial black-box models
(most current GUI-agent literature — OS-Atlas/ShowUI/InfiGUI-G1 — still does the serial-staged version).

Caveat(honest): full "no world-model at all" overclaims — SMC theory is contested, multi-step GUI tasks
genuinely need lookahead planning sometimes. Useful version = "direct coupling as DEFAULT fast path,
explicit planning as expensive fallback" — same routing shape as §1, different discipline, converging
independently = a real signal, not coincidence.

## 3. Blind-navigation analogy(a11y-tree-first, vision-fallback)
Strongest/most literal analogy — same information source, not just inspiration. Screen-reader research:
blind users build understanding via hierarchical STRUCTURAL traversal, and experts develop chunked
navigation idioms(jump-by-heading etc) — same chunking story, non-visual modality.
Where it fails: blind-accessibility failure catalogs(custom canvas/unlabeled ARIA) are likely the SAME
places our a11y-tree-first agent needs vision fallback — free curated "where structure isn't enough" list.
**Honest limit**: this analogy is a ROBUSTNESS/reliability source(what signal to trust), NOT a SPEED
source — screen-reader interaction is generally slower than sighted, not faster. Don't overclaim.

## 4. Two concrete buildable proposals

**Proposal A(strong, from §1+§2 convergence) — "Compiled chunk cache with precision-gated fallback"**:
Fast embedding-lookup model: (a11y-state-hash, goal-embedding) → cached action. Cache populated by
PROMOTION from successful slow-path(VLM) episodes, not offline labeling — live, continuously-growing
byproduct of the agent's own work. Confidence = retrieval-distance in the cache itself(not a separate
classifier) — below threshold triggers full VLM deliberation.
Risk: cache staleness on UI changes(needs invalidation/versioning via a11y-tree-diff novelty detection),
inherits slow-path mistakes(same failure mode as human expertise ossifying on shifted context — known,
studied problem with known mitigation patterns).

**Proposal B(riskier, less literature backing) — "Affordance-joint action head"**:
Collapse ground-then-policy(2 stages/models, current standard) into ONE small head: (a11y-region-features,
goal) → joint (action-type, target-affordance-vector) directly — ported from robotic grasp-affordance-map
work(predict affordance heatmap directly from image+goal, no object-class-then-grasp-lookup detour).
Explicitly flagged as unvalidated for GUI tasks specifically — a real experiment, not a safe bet.

## Overall honest assessment
Load-bearing ideas = chunking/expertise-compilation(§1) + affordance/direct-coupling(§2) — independently
converge on the same two-speed, precision-gated architecture from different disciplines. Disability-
analogy(§3) is real but narrower than hoped(signal-prioritization only, not speed). Proposal A is the
most immediately buildable next step; Proposal B is the higher-risk/higher-novelty bet worth prototyping
separately once A's cache-and-fallback plumbing exists(A is arguably a PREREQUISITE for testing B fairly).

REF: u_3212~3214(2026-08-31), agent-id af9180e4de169b23e.

# Lightweight/Distilled GUI-Judgment Model — SOTA Survey (2026-08-31)

Task3 grounding research: is a small local model realistic for the remaining ambiguous/icon-only UI-
judgment cases our a11y-first pipeline can't resolve?

## 1. SOTA for lightweight GUI-grounding models
- **TinyClick**(270M, Samsung R&D Poland+Warsaw Univ Tech, Florence-2-Base backbone,
  [arXiv:2410.11871](https://arxiv.org/abs/2410.11871), Oct2024/Interspeech2025): **73.8% ScreenSpot**,
  beats SeeClick(9.6B, 53.4%) AND GPT-4V(16.2%) on same benchmark. Best real citable small-model number.
- No model under 100M params with real accuracy numbers found — genuine gap, not glossed over.
- GoClick(230M, [arXiv:2604.23941](https://arxiv.org/abs/2604.23941)) targets low-latency mobile, only
  qualitative claims, no hard numbers extracted.
- OmniParser v2(Microsoft, YOLO-class icon detector+Florence-2 captioner): 39.6 avg ScreenSpot Pro, claims
  60% latency cut vs v1 — specific "0.6-0.8s/frame" figure NOT verifiable against Microsoft primary sources.
- ★No source anywhere reports verified sub-200ms end-to-end grounding decision. Closest: UI-TARS-2 4.0s/round
  unquantized → 2.5s/round W4A8-quantized. Our 0.2s target is genuinely aggressive vs published SOTA.

## 2. Classical ML(decision-tree etc) vs neural
- No paper directly compares decision-tree/XGBoost vs CNN for UI-element classification — literature jumped
  straight from raw features to neural/LLM, this gap is itself informative.
- AndroidWorld: text/a11y-only agents BEAT multimodal(30.6% vs 25.4%) — native Android a11y trees complete.
- WebVoyager: vision BEAT a11y/text-only(59.1% vs 40.1%) — web a11y trees often incomplete/noisy.
- ★Conclusion: when a11y labels are good(matches our already-working ~200ms a11y path), classical/tabular
  ML is plausible+sufficient. For icon-only/unlabeled elements(the actual remaining gap), vision is NOT
  optional — Rico's CNN icon classifier hit 94% covering 78% of zero-a11y-semantic elements; OmniParser built
  explicitly because icons are "semantically opaque." No textual signal exists to build tabular features from
  in that case — structurally requires a small CNN/ViT.

## 3. Bootstrapping recipe for solo dev
- Confidence-threshold cascades(cheap-first, escalate-if-uncertain, log escalations as training data) = active
  real pattern: ["Rational Tuning of LLM Cascades"](https://arxiv.org/pdf/2501.09345),
  ["Is Escalation Worth It?"](https://arxiv.org/pdf/2605.06350). Caveat: raw softmax ≠ calibrated confidence,
  needs temperature-scaling against own logged outcomes.
- HuggingFace `transformers` Trainer supports custom teacher-student loss directly — most practical on-ramp,
  no specialized framework needed(DistilBERT/TinyBERT = reference pattern).
- Export: ONNX→CoreML via `coremltools` standard, but has a real gotcha(§4). `torch.jit.trace`→direct CoreML
  often more robust than ONNX round-trip for correctness.
- **Practical recipe specific to us**: instrument existing VLM-fallback calls(already firing on ambiguous/
  icon-only elements) to log `(a11y features, screenshot crop, VLM answer)` NOW — free, we're already paying
  for those calls. A few hundred–low-thousands of examples → tiny CNN/ViT or frozen-backbone+linear-head via
  HF Trainer → coremltools export = realistic weekend-scale project. No documented solo-dev case study of this
  exact loop exists — it's a reasonable synthesis of established sub-patterns, not an off-the-shelf framework.

## 4. Apple Silicon MPS pitfalls(best-documented section, real GitHub issues)
- PyTorch MPS operator gaps real+ongoing: [#77754](https://github.com/pytorch/pytorch/issues/77754)(missing
  ops), [#151189](https://github.com/pytorch/pytorch/issues/151189)(linalg_solve_ex),
  [#136624](https://github.com/pytorch/pytorch/issues/136624)(arange+bfloat16).
  `PYTORCH_ENABLE_MPS_FALLBACK=1` SILENTLY falls back to CPU per-op — real trap for latency-sensitive
  pipeline(degrades perf without erroring).
- Memory leaks: [#114096](https://github.com/pytorch/pytorch/issues/114096)(combined device+dtype `.to()`),
  [#152344](https://github.com/pytorch/pytorch/issues/152344)(SDPA fp32 leak, 2025).
- ★FP8/low-bit quantization has NO true MPS hardware path — Apple Silicon has no native FP8/FP4 compute, gets
  emulated via upcast to BF16/FP32(negates the point). Directly relevant: matches our own already-hit MPS
  fp16/fp8 VAE bug(RECIPE_krea2_gguf_t2i.txt, RECIPE_minimax_h3_i2v.txt) — same class of problem recurring.
- ONNX Runtime CoreMLExecutionProvider SILENTLY downcasts FP32→FP16 with legacy NeuralNetwork format
  (undocumented) — detect via round-trip cast test, fix by forcing `ModelFormat: "MLProgram"`.
- W8A8 int8 fast path real per Apple's own coremltools docs, but ONLY on A17 Pro/M4+ silicon(concrete:
  ResNet50 W8A8=0.77ms vs 0.94ms fp, iPhone15 Pro). Machines older than M4 don't get this path.
- ANE conversion trap: ANE's native primitive is convolution(matmul only works as 1×1-conv special case) —
  transformer-heavy small models may not map cleanly, any unsupported op forces costly CPU-round-trip
  fallback, monolithic deep-transformer conversion reported to make converter SILENTLY DIE with no error.

## Bottom line
- a11y-only structured classification(possibly classical ML) can likely absorb MORE "ambiguous but labeled"
  cases than our current VLM handles — cheap to try, low risk, do this first.
- For genuinely icon-only/unlabeled/visual-confirmation cases: no shortcut avoids a small vision model
  (CNN/ViT). TinyClick(270M/73.8% ScreenSpot) = best public reference for what's achievable at that scale.
- 0.2s target is aggressive vs all published SOTA — realistic path is either detector-only(YOLO-class, cf
  OmniParser's detector stage) or accept a larger model with real optimization work.
- Main engineering RISK is the CoreML/ONNX export step(documented MPS immaturity), NOT the ML methodology
  itself — budget real debugging time there specifically, echoing our own prior MPS fp8 incident.

REF: u_3204(task3 kickoff), agent-id a09b2eed31dde67cc.

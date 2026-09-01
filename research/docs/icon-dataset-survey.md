# Icon Training-Data Source Survey (2026-09-01)

Task: find real, accessible, properly-licensed labeled icon data to train a small CNN classifier
(cf Rico's 94%-accuracy icon classifier) after CLIP zero-shot embedding failed(u_3232~3238,
ar_2983 — negative discrimination gap, 0% real-world usable).

## 1. Rico dataset — downloadable, but not where expected
- Official host: interactionmining.org/archive/rico(NOT interacticon.com — dead DNS).
- Direct GCS download confirmed(curl 200): `unique_uis.tar.gz`=6.47GB + `ui_layout_vectors.zip`=8.2MB.
- Stats: 9.3k apps, 66,261 unique UI screens.
- License: custom `copyright.txt` — permissive-ish but requires indemnifying UIUC, not standard OSS.
- Mirrors also on HuggingFace(`creative-graphic-design/Rico`) and Kaggle.
- ★The 94%-accuracy icon classifier itself is NOT in base Rico — it's in a separate follow-on repo:
  **RICO-Semantics**(github.com/google-research-datasets/rico_semantics), CC BY-SA 4.0, ~500k
  annotations, 97 icon classes. Archived/read-only as of Apr2026 but still browsable+downloadable.

## 2. Icon library licenses — all usable for training
None of these have an ML-training restriction(all silent on it = permitted under standard
interpretation, attribution-only obligations):
| Library | License | Count | Labels |
|---|---|---|---|
| Material Symbols | Apache 2.0 | 2,500+ | clean semantic(`arrow_back` etc) |
| Font Awesome Free | CC BY 4.0(SVG)/OFL(font-only) | ~2,000 | clean |
| Feather | MIT | 286 | clean |
| Bootstrap Icons | MIT | 2,000+ | clean |
| Tabler | MIT-family | 6,184 | clean |
Caveat: Font Awesome's "brands" logo subset is trademark-sensitive — exclude it, use SVG/JS not
OFL font files.

## 3. Post-Rico academic datasets(downloadable, verified)
- **RICO-Semantics/IconNet**(Google Research, arXiv:2210.02663, 2022) — ~78K icon-function
  annotations, verified live via GitHub API.
- **semantic-icon-classifier**(github.com/datadrivendesign/semantic-icon-classifier, MIT, ~100k
  images, 99 functional classes) — strongest direct functional-label match, but fragile(Google
  Drive zips, sparse repo maintenance).
- Enrico and CLAY checked+rejected — label screen-level design topics or coarse UI types, not
  icon function specifically.

## 4. Fastest practical combo(honest recommendation)
- **Fastest baseline**: `boostvolt/icon-dataset`(github.com/boostvolt/icon-dataset) — 142,416
  pre-rasterized 224×224 images, 100 functional classes, pre-split 80/10/10, ready to train
  immediately. ★Caveat: archived Dec2023, NO LICENSE STATED — legal risk if shipped externally,
  fine for internal/research use(verify before any redistribution).
- **Best-licensed complement**: self-rasterize Material Symbols+Feather+Bootstrap Icons(Apache
  2.0/MIT, trivial with `resvg`/`cairosvg`) for a few thousand clean properly-licensed images
  across ~15-30 common function categories(back/save/delete/search/settings/share/menu/close/
  add/edit/home etc).
- **For UI-realistic icons**(vs flat vector icons): crop from RICO-Semantics using its bounding
  boxes+97-class labels — more representative of real GUI-automation targets, but needs a
  cropping/preprocessing step, not ready-to-train.
- **Harder than it sounds**: mixing multiple icon libraries under one label introduces visual-
  style inconsistency(fill vs outline, corner radius, stroke width) — no direct study exists for
  icon classifiers specifically(domain-generalization literature SUGGESTS it's plausibly
  beneficial for robustness, but this is inference not verified). Taxonomies also don't match 1:1
  across sources(Rico's 97-135 classes vs a practical ~20-30 class taxonomy) — expect manual
  label-mapping work regardless of source choice.

## Recommendation
Start with `boostvolt/icon-dataset` for a fast internal-use baseline, backfill/replace with
self-rasterized Material Symbols+Feather+Bootstrap Icons for anything shipping externally, use
RICO-Semantics crops if screen-realistic icon style matters more than raw volume.

REF: u_3238~3239(2026-09-01), agent-id ab02618680cc9e973, follows CLIP-embedding failure(ar_2983).

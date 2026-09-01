# Training Data Sources — Provenance & License Tracker

Records every external dataset/data-source considered or used for the icon-judgment-model research
(`research/src/icon_learning/`). Kept for compliance/audit purposes — record BEFORE downloading,
not after, per u_3240/u_3241(2026-09-01).

## Format
Each entry: name, source URL, license(exact wording/tag), access date, usage scope(internal-
research-only vs redistributable), evidence(how we verified the license claim).

---

## boostvolt/icon-dataset
- URL: https://github.com/boostvolt/icon-dataset
- Content: 142,416 pre-rasterized 224×224 images, 100 functional classes, pre-split 80/10/10
- **License: NONE STATED** — verified via WebFetch(2026-09-01): "No license found... repository
  content... no license file or licensing information is mentioned or visible in the navigation,
  file listing, or documentation sections displayed."
- Archived status: "This repository was archived by the owner on Dec 26, 2023. It is now
  read-only." (independently confirmed via WebFetch, same query)
- ★Legal interpretation: absent license = default copyright-holder-retains-all-rights, NOT
  public domain. Redistribution/external-shipping = NOT permitted without explicit owner contact.
- **Usage scope: INTERNAL RESEARCH ONLY.** Do not bundle into any shipped product, do not
  redistribute the dataset itself, do not publish derived model weights trained purely on this
  set without independent re-verification of licensing status closer to ship-time.
- Evidence: WebFetch query run 2026-09-01, response text preserved in this file(above). No
  separate screenshot file captured — GitHub repo pages are text-queryable and the WebFetch
  response itself constitutes the timestamped evidence record.

## attach-class rebalancing (a_2989, u_3268)
- Approach: Inverse-frequency class-weighting via CrossEntropyLoss weight parameter
- Source: boostvolt/icon-dataset attach class (original 9 train, 1 val, 2 test)
- License: Derived from boostvolt (no external license stated)
- Usage scope: INTERNAL RESEARCH per boostvolt policy
- Purpose: Address severe attach-class undersampling via loss weighting (not data augmentation)
  - Class weights computed as inverse of per-class sample counts
  - attach class (9 samples) gets highest weight; camera/folder (3000+ samples) get lowest weight
  - This penalizes model more heavily for attach misclassifications, forcing it to learn the small class despite limited data
- Alternative (not implemented): real app toolbar screenshots (Keynote/Mail/Chrome paperclip icons)
  - Would require live kongtrol a11y + screencapture interaction
  - Deferred to future iteration
- Added: 2026-09-01, a_2989 class-weighted retrain

## Material Symbols(Google)
- URL: https://github.com/google/material-design-icons (or fonts.google.com/icons)
- License: Apache License 2.0(explicit, standard OSS license — training use permitted, silent
  on ML use = permitted under standard interpretation, attribution obligations apply)
- Usage scope: safe for internal AND external/redistributable use(subject to Apache 2.0 terms —
  include license notice if redistributing).
- Not yet downloaded(planned).

## Feather Icons
- URL: https://github.com/feathericons/feather
- License: MIT
- Usage scope: safe for internal AND external use.
- Not yet downloaded(planned).

## Bootstrap Icons
- URL: https://github.com/twbs/icons
- License: MIT
- Usage scope: safe for internal AND external use.
- Not yet downloaded(planned).

## RICO-Semantics(Google Research)
- URL: https://github.com/google-research-datasets/rico_semantics
- License: CC BY-SA 4.0
- Content: ~500k icon-function annotations, 97 icon classes, built on base Rico dataset
- Status: archived/read-only as of Apr2026, still browsable+downloadable(per research agent
  verification, 2026-09-01)
- Usage scope: CC BY-SA 4.0 = share-alike, redistribution permitted WITH same-license + attribution
  requirement on any derivative dataset/work built from it — check this constraint before any
  external release of anything derived from this source.
- Not yet downloaded(planned).

## Rico(base dataset, interactionmining.org)
- URL: https://interactionmining.org/archive/rico(NOTE: interacticon.com is DEAD DNS, do not use)
- License: custom `copyright.txt` — permissive-ish but requires indemnifying UIUC(University of
  Illinois), not a standard OSS license — read full terms before any use beyond casual research.
- Content: 9.3k apps, 66,261 unique UI screens, 6.47GB(unique_uis.tar.gz)
- Usage scope: internal research only until copyright.txt terms fully reviewed.
- Not yet downloaded.

---

## Process note
Before downloading ANY new source not listed here: add an entry to this file FIRST(name, URL,
license claim, evidence), then download. Network-budget rule(verify-first) applies — don't
re-download if already verified present locally.

## Distribution policy(user-decided, 2026-09-01, u_3243~3245)
- Raw datasets(esp. no-license/gray-area sources like boostvolt) = NEVER redistributed, internal
  research/training use only.
- Trained model WEIGHTS(not raw data) + explicit data-source attribution in this file = the
  realistic lowest-risk compromise if a model needs to ship beyond internal use.
- ★Honest caveat: this is NOT a guaranteed-safe position — AI-training-copyright law is an
  unsettled area globally(multiple active lawsuits over whether trained-model-weights infringe
  source-material copyright). "Weights-only + attribution" reduces risk, does not eliminate it.
  Re-evaluate before any external/commercial release, don't treat this note as final legal
  clearance.

REF: u_3239~3242(2026-09-01), research/docs/icon-dataset-survey.md(full research findings).

# ZION — Monthly Prediction System — ROADMAP & RECIPE (v0.1)

Clean-slate monthly system built on a proper out-of-sample method.
Supersedes legacy HYACINTH monthly. References HYACINTH_X (canonical original) as method spec.
CYCLOPS is discarded as a foundation (its OOS is contaminated) — salvage non-OOS ideas only.

## FOUNDATIONAL DISCIPLINE (applies to every stage — non-negotiable)

- **PIT / as-issued only.** No reprint look-ahead. Every feature uses only what was published as of decision month `t`.
- **Expanding window.** Train on ALL rows up to the usable boundary; never a fixed rolling lookback.
- **3-month label gap (forced by horizon).** At decision month `t`, the newest usable *label* is month `t−3` (its outcome resolves at `t`). Training set = rows through `t−3`. Features may use data through `t`.
- **Selection inside the fold.** Features, tiers, models, thresholds — ALL chosen per-fold on data ≤ `t−3`. No house-wide picking anywhere. (This is the exact defect ZION exists to eliminate.)
- **Abstain by default.** Act only where OOS edge is proven. A dark board is a valid, honest output.
- **Honest numbers.** Report as-issued OOS, not reprint. Correct annualization (elapsed time, never row-count `len(r)/52`). Sortino-first.

---

## STAGE 0 — DATA AUDIT GATE  (writes `audit_pass.flag`; nothing downstream runs without it)

- **0a. Core dataset row-level audit** — target column + anchor/date column + feature columns present, typed, non-degenerate.
- **0b. PIT integrity certification** — dates monotonic; no feature timestamped ahead of its true publication; no reprint contamination; publication lag recorded per series.
- **0c. Target-alignment audit** — 3-month-ahead outcome aligned correctly (guard the shift/horizon off-by-one: "return at row t must be t+3's realized outcome, not t's"). Direction and magnitude both checked.
- **0d. Event/holiday calendar** — settlement dates, trading-day availability, month-boundary rules.
- **GATE:** all checks pass → `audit_pass.flag`. Spine is hard-gated on it.

## STAGE 1 — PIT DATA LAYER / PANEL ASSEMBLY

- **1a. Raw series ingestion** via PIT loaders (as-issued FRED, price settlement, any splice handling e.g. TED→BAA10Y).
- **1b. Publication-lag alignment** per series (each series shifted to when it was actually knowable).
- **1c. Feature construction** — as-of-`t` only; no forward-filled future values.
- **1d. Target construction** — `t+3` outcome: direction (primary) + return (magnitude).
- **1e. As-issued monthly panel freeze** — one row per decision month, frozen at issue.
- **1f. Panel validation** — re-assert Stage 0 invariants on the assembled panel.

## STAGE 2 — FEATURE ADMISSION / PHASE −1 SCREEN  (decorrelation-admission)

- **2a. Candidate feature universe** — economic priors, not data-dredged.
- **2b. Phase −1 decorrelation screen** — rank on ΔdivRatio (NOT Δeff-bets, which is vol-confounded).
- **2c. Redundancy / collinearity pruning.**
- **2d. Admission list.**
- **CRITICAL:** if admission is used to *select*, it MUST run inside each fold (per-fold on data ≤ `t−3`). A house-wide Phase −1 screen is itself a leak. Alternative: fix the admission list a-priori from economic reasoning so no selection variance enters. → DECISION D2.

## STAGE 3 — WALK-FORWARD OOS ENGINE  (the spine)

- **3a. Fold generator** — expanding window, monthly roll; per fold: train = rows ≤ `t−3`, predict outcome at `t+3`.
- **3b. In-fold feature/predictor selection** — on training rows only.
- **3c. In-fold model fit** — model family per DECISION D3.
- **3d. In-fold tier/conviction assignment** — tier grammar, conviction-only, retention veto; assigned per fold.
- **3e. One-step-ahead prediction emission** — 3-month-ahead call for decision month `t`.
- **3f. OOS prediction stream assembly** — one prediction per decision month, stitched across folds.
- **3g. Coverage-selection guard** — verify months-acted is NOT merely months-market-rose (the coverage-selection leak); measure corr(acted, market-up) and report.

## STAGE 4 — CONVERGENCE / MULTI-ENGINE AGREEMENT

- **4a. Independent engines/lenses** — each blind to the others.
- **4b. Agreement scoring.**
- **4c. CONVERGENCE_TRACK forward scoring.**
- **4d. Abstain-by-default gate** — act only where engines converge AND per-fold OOS edge clears bar.

## STAGE 5 — NULL / VALIDATION HARNESS   (→ DECISION D4: role & inclusion)

- **5a. Max-stat placebo** across cells (guards multiple-comparisons on tier/cell selection) — DESCRIPTIVE cross-check, not the primary gate.
- **5b. Primary evidence remains walk-forward OOS on as-issued tapes.** (Shuffled-null is retired per operator ruling — do not use.)

## STAGE 6 — EVALUATION LEDGER

- **6a. OOS accuracy** — as-issued, honest.
- **6b. Money test vs buy-hold benchmark** — use traded returns, not buy-hold proxy, where a traded instrument exists.
- **6c. Correct annualization** — elapsed calendar time; NEVER row-count `len(r)/52`.
- **6d. Sortino-first** — Sortino-LB + plateau (declared standard; not re-litigated). MaxDD reported. Sharpe secondary.
- **6e. Within-regime reporting hooks** — structure so Stage 7 can segment without recompute.

## STAGE 7 — RUPTURE ANALYSIS   (added AFTER clean system is standing)

- **7a. Retrospective change-point detection on the underlying series** (reporting/segmentation).
- **7b. Retrospective change-point on the OOS performance stream** (edge-rupture detection).
- **7c. Within-regime evaluation** — never quote a number blended across a structural break.
- **7d. Causal / PIT online detector** — detect a rupture at `t` using only data ≤ `t`.
- **7e. Validation** — causal detector vs retrospective; only adopt after it demonstrably tracks.
- **7f. Acting version** — drop pre-rupture training / re-anchor. Enabled only post-validation.

## STAGE 8 — LIVE / FORWARD EMISSION & TRACKING

- **8a. Monthly runner** — emit current decision month's 3-month-ahead call.
- **8b. As-issued tape freeze** — predictions frozen at issue; never backfilled from reprints.
- **8c. Forward resolution** — score once the 3-month horizon closes.
- **8d. Scheduling** — launchd (SSL_CERT_FILE guard; no duplicate jobs).
- **8e. Dashboard / alert** — match the severity word, not a substring.

## STAGE 9 — BOOK ASSEMBLY / MULTI-ASSET   (after single-asset clean)

- **9a. Add assets one at a time** through the identical spine.
- **9b. Cross-asset decorrelation, sleeve sizing, gross cap, risk-concentration caps.**
- **9c. Currency tilt** — declared tilt, not hedge.

---

## OPEN DECISIONS (operator ruling required)

- **D1. First asset.** Proposed: Gold (comparable to your WF pilot). 
- **D2. Feature admission.** In-fold Phase −1 screen (adaptive, some selection variance) vs fixed a-priori economic prior (zero selection variance). Proposed: fixed a-priori for v1, add in-fold screen as an experiment.
- **D3. Model family (monthly).** Parsimonious (logistic/threshold) vs four-model cascade. Proposed: parsimonious first — monthly data is scarce (~600 usable months), cascade risks overfit.
- **D4. Null harness.** Include max-stat placebo as descriptive cross-check, or go pure-OOS-only? Proposed: keep placebo descriptive-only, OOS is the gate.
- **D5. Target.** Direction primary + tier-conditioned range for magnitude (publish range, not point target). Proposed: adopt.

## STATUS
- Tree scaffolded: stage0_audit, stage1_pit_data, stage2_walkforward, stage4_ledger, data, reports, lib, spec.
- Mapping pass running: monthly dataset inventory, HYACINTH_X method spec, CYCLOPS OOS-defect flags, CYCLOPS salvage list. Reconcile on arrival.

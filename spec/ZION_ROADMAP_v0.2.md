# ZION — Monthly Prediction System — ROADMAP & RECIPE (v0.2, data-reconciled)

Clean-slate monthly system on a proper out-of-sample method.
Supersedes legacy HYACINTH monthly. HYACINTH_X = canonical method spec. CYCLOPS = discarded foundation (contaminated OOS); salvage non-OOS ideas only.

## RECONCILED DATA ANCHORS (from mapping pass)
- **Feature panel:** `~/Desktop/HYACINTH_X/combined_macro_0826.csv` — monthly, `Date` anchor (first-of-month), 1871→2026-08, 1868 rows, ~4677 cols. Shiller core + appended market/macro series.
- **Trusted directional record:** `~/Desktop/HYACINTH_X/MONTHLY_ASISSUED_LEDGER.csv` (1-month horizon — see D0).
- **Gold config (reference):** outcome `Gold_Close`; GROUNDED features = Dollar_Index, M2_Money, Industrial_Production, GS10_Rate, Fed_Funds_Rate, US_2Y_Treasury, Copper_Close, WTI_Crude_Close, Gold_Close, Term_Spread_10Y_2Y; always pull Date + US_CPI; default start 1971.
- **PIT loaders (reference):** `~/Desktop/AEGIS/WF_PILOT/BF.py` — `fetch_fred_series` + TED→BAA10Y splice at seam 2022-01-21.
- **Stage-0 splice detector (reference):** `lib_pipeline.py:stage0_audit` (line 151).
- **CONTAMINATED — do NOT reproduce:** `lib_pipeline.py:red_dawn_tier` (line 487) — fixed 50/25/25 split, house-wide pooled predictor selection (itertools.combinations over all vars, pooled across assets), floors tuned on revealed TEST.
- **Correct annualization (reference):** `final_portfolio.py:197` — `eq[-1]**(12/n)-1`, n=months. DEFECT to avoid: `len(r)/52`.

## HORIZON — legacy vs ZION (D0, gates everything)
- Legacy monthly target (HYACINTH_X RED_DAWN + CYCLOPS): `sign(outcome.pct_change().shift(-1))` = **1-month-ahead direction**.
- ZION design (operator-stated): **3-month-ahead**, rolling monthly → forces training boundary at `t−3`.
- Target must be rebuilt for the chosen horizon; ZION record not directly comparable to the 1-month ledger.

## FOUNDATIONAL DISCIPLINE (every stage)
- PIT / as-issued only; no reprint look-ahead.
- Expanding window; never fixed rolling lookback.
- Label gap = horizon H (H=3 forces train ≤ `t−3`); features may use ≤ `t`.
- Selection INSIDE the fold — features, tiers, models, thresholds. Never house-wide. (The ZION reason-for-being.)
- Abstain by default; act only on proven OOS edge. Dark board is valid output.
- **NO FORCED PREDICTION (hard rule).** Do NOT reproduce CYCLOPS's terminal step that manufactures a call to fill an empty slot. The pipeline ends in exactly two states: a gated in-regime call, or ABSTAIN. If nothing qualifies in the regime, abstain. Enforcement points:
  - Stage 3: no cell clears Wilson-LB gate on the fold → ABSTAIN (no default-to-majority).
  - Stage 4: engines don't converge (k < threshold) → ABSTAIN (no "closest engine wins").
  - Stage 14/CASSANDRA: `_asset_history_fallback` (10y mean) is never emitted as a call; VETO/ABSTAIN stands.
  - Stage 7: outside any validated regime, or during flagged collapse → ABSTAIN.
- Honest numbers: as-issued OOS; calendar annualization; Sortino-first.

---

## STAGE 0 — DATA AUDIT GATE  → `audit_pass.flag` (hard gate; spine won't run without it)
- 0a Core row-level audit: target + `Date` anchor + features present, typed, non-degenerate.
- 0b PIT integrity: monotonic dates; per-series publication lag; no reprint contamination; no feature timestamped ahead of publication. (Reuse splice detector from lib_pipeline stage0_audit, retyped.)
- 0c Target alignment: outcome on row `t` = the H-month-forward realized result; guard the shift/horizon off-by-one.
- 0d Event/holiday calendar: settlement, trading-day availability, month boundaries.

## STAGE 1 — PIT DATA LAYER / PANEL ASSEMBLY
- 1a Ingest raw series via PIT loaders (as-issued FRED, price settlement, TED splice).
- 1b Publication-lag alignment per series.
- 1c Features as-of-`t` only.
- 1d Target = H-month-forward: direction (primary) + return (magnitude).
- 1e As-issued monthly panel freeze (one row per decision month).
- 1f Panel validation vs Stage 0 invariants.

## STAGE 2 — FEATURE ADMISSION / PHASE −1 SCREEN
- 2a Candidate universe from economic priors (not dredged).
- 2b Phase −1 decorrelation screen — rank on ΔdivRatio (NOT Δeff-bets).
- 2c Redundancy/collinearity prune.
- 2d Admission list.
- LEAK-GUARD (D2): if admission selects, it runs in-fold on ≤ `t−3`; house-wide screen = leak. v1 default: fixed a-priori list; in-fold screen as measured experiment.

## STAGE 3 — WALK-FORWARD OOS ENGINE (the spine)
- 3a Folds: expanding window, monthly roll; train ≤ `t−3`, predict outcome at `t+H`.
- 3b In-fold feature/predictor selection (train rows only).
- 3c In-fold model fit (family per D3).
- 3d In-fold tier/conviction (conviction-only, retention veto; Wilson-LB shrinkage per fold).
  - LB GATE = 0.45 (operator-set): TRAIN-side cell-admission floor inside the fold (admits a candidate to be ranked). NOT the final emit bar — winner chosen on validation/OOS Wilson-LB, then convergence + abstain on top. 0.45 lets candidates through; honesty comes from walk-forward + abstain.
- 3e Emit one H-month-ahead call for `t`.
- 3f Assemble OOS prediction stream.
- 3g Coverage-selection guard: report corr(acted, market-up); acted-months must not equal merely market-rose months.

## STAGE 4 — CONVERGENCE / MULTI-ENGINE AGREEMENT
- 4a Independent engines/lenses (blind to each other).
- 4b Agreement scoring.
- 4c CONVERGENCE_TRACK forward scoring.
- 4d Abstain-by-default gate: act only where engines converge AND per-fold OOS edge clears bar.

## STAGE 5 — NULL / VALIDATION HARNESS (D4)
- 5a Max-stat placebo across cells (multiple-comparison correction) — DESCRIPTIVE cross-check only.
- 5b Primary evidence = walk-forward OOS on as-issued tapes. Shuffled-null retired (do not use).

## STAGE 6 — EVALUATION LEDGER
- 6a OOS accuracy (as-issued).
- 6b Money test vs buy-hold (traded returns, not proxy).
- 6c Annualization over elapsed calendar time (NEVER len(r)/52).
- 6d Sortino-first (Sortino-LB + plateau); MaxDD reported; Sharpe secondary.
- 6e Within-regime reporting hooks (for Stage 7).

## STAGE 7 — RUPTURE ANALYSIS (after clean system stands; salvage `rupture_monthly.py`)
- COLLAPSE TRIGGER (operator-set): OOS accuracy dropping BELOW CHANCE → ABSTAIN (throttle, never resize). Must be change-point-confirmed and CAUSAL (≤ t). Regime analysis may increase caution / trigger abstention; it may NOT rescue a failed OOS by hindsight carve-out.
- 7a Retrospective change-point on underlying series.
- 7b Retrospective change-point on OOS performance stream.
- 7c Within-regime evaluation (never blend across break).
- 7d Causal/PIT online detector (≤ `t` only).
- 7e Validate causal vs retrospective.
- 7f Acting version (drop pre-rupture training / re-anchor) — post-validation only.

## STAGE 8 — LIVE / FORWARD EMISSION & TRACKING
- 8a Monthly runner emits current H-month-ahead call.
- 8b As-issued tape freeze (frozen at issue; never backfilled).
- 8c Forward resolution once horizon closes.
- 8d launchd scheduling (SSL_CERT_FILE guard; no duplicate jobs).
- 8e Dashboard/alert (match severity word, not substring).

## STAGE 9 — BOOK ASSEMBLY / MULTI-ASSET (after single-asset clean)
- 9a Add assets one at a time through identical spine.
- 9b Cross-asset decorrelation, sleeve sizing, gross cap, risk-concentration caps.
- 9c Currency exposure as declared tilt, not hedge.

---

## SALVAGE FROM CYCLOPS (non-OOS; retype clean, do not import)
- Stage-0 basis-splice discriminator (`lib_pipeline.py:151`).
- PIT loaders + TED→BAA10Y splice (`BF.py:140-197`); CONTAMINATED_VARS/TIMELY_VARS revision-leak controls.
- 27-type ternary pair grammar (`score_folds.py:11-27`).
- Derived ratio features (`DERIVED_VARS`, STATIONARY skip-deflation set).
- Exposure/numeraire leak-exclusion (`lib_pipeline.py:227-235`).
- Wilson-LB conviction shrinkage + hard-n floor (`lib_pipeline.py:254-262`).
- Frequency adapters (INFL_PERIODS/CARRY_BARS/BAR_UNIT).
- `rupture_monthly.py` + regime reporting (Stage 7).
- DISCARD: fixed 50/25/25 split, test_acc/wf_acc selection, pooled house-wide picking, post-TEST floor tuning.

## OPEN DECISIONS
- D0 Horizon: 3-month (operator-stated) vs legacy 1-month. — GATES Stage 1 target + Stage 3 gap.
- D1 First asset: proposed Gold.
- D2 Feature admission: fixed a-priori (v1) vs in-fold Phase −1 screen.
- D3 Model family: parsimonious (v1) vs cascade.
- D4 Null harness: placebo descriptive-only vs pure-OOS.
- D5 Target: direction primary + tier-conditioned range for magnitude.

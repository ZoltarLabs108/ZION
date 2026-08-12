# ZION MONTHLY RECIPE — with diagnostic presentation spec

The recipe runs stage by stage. Each stage emits a fixed-format DIAGNOSTIC block
(printed table style, matching HYACINTH_X's log-table convention) so results are
presented identically every run. Discovered by executing each stage on real data.
Discipline (all stages): PIT/as-issued only · 1-mo direction target · t-3 embargo ·
expanding window · in-fold selection only · abstain-not-force · rank on Wilson-LB.

---

## PARADIGM — sequential one-step-ahead WF (NOT CYCLOPS train/test)
The defining methodological break. Every ZION number is produced this way; the old
CYCLOPS train/test numbers are discarded, not ported.

| | CYCLOPS train/test (contaminated) | ZION sequential one-step-ahead |
|---|---|---|
| split | ONE fixed chronological split (50/25/25, 0.65 tail) | NO fixed split; refit every month, reset windows |
| training | fit ONCE on the whole sample | retrain on ALL-past at each month, roll forward 1 |
| test set | one static held-out block | every month, one step into the future |
| selection | HOUSE-WIDE on full sample (leaks) | IN-FOLD only, past-only |
| hyperparams (N) | tuned on/near test | FROZEN on disjoint pre-1990 design sample |
| the question | "does a fixed model survive a held-out chunk?" | "forecasting next month every month, how often right?" |

Only the second question is honest. "test_acc/wf_acc" from CYCLOPS is a misnomer and
must never be cited. See [[contamination register C6 house-wide selection]].

## CONTAMINATION REGISTER — resolve + anticipate (standing, all assets)
Every leak found becomes a permanent guard. Format: source · manifests as · resolve · anticipate.

- **C1 Unit/vintage splice** · giant single-month level break + full range separation (Copper 2000-08, ~2000x), corrupts z-scores/cells straddling the seam · resolve: drop pre-splice segment or the series · anticipate: Stage-0 unit-aware splice detector, BLOCK on hard splice, per-series vintage check.
- **C2 Publication-timing leak** · mid-month series (Industrial_Production, US_CPI, M2_Money) used as-of-1st-of-month → inflated acc that collapses when lagged (M2/Term_Spread 50.7%→34.0%) · resolve: PIT publication-lag (≥1mo; INDPRO/M2 realistically ~2mo at a 1st-of-month decision) · anticipate: PITlag flag in Stage 0, explicit lag calendar per series in Stage 1, never use a value before its real release date.
- **C3 Drift-capture as skill** · long-horizon (3mo) accuracy dominated by the asset's own trend; high raw OOS acc (60-68%) but ≤0 edge vs always-predict-majority · resolve: net the drift baseline, rank on EDGE (acc−drift), never raw acc · anticipate: always report drift + edge; a call only counts if it beats always-trend.
- **C4 Overlapping-window autocorrelation** · H-month horizon rolled monthly overlaps by H−1 → independence violated, Wilson-LB too tight · resolve: overlap-adjusted LB (eff n≈n/H) · anticipate: always print LB_ovl; treat nominal LB as an upper bound.
- **C5 Multiple-comparison / best-of-N** · sweeping many pairs×types, the best clears 50% by luck (lone survivor out of dozens) · resolve: max-stat placebo (permute labels, re-run the ENTIRE selection, tail test) = Stage 5 · anticipate: never quote best-of-N without placebo; always report N tested.
- **C6 House-wide selection** · picking predictors on the full sample then scoring "OOS" (the original contamination) · resolve: ALL selection in-fold only · anticipate: fold-local everything — the ZION invariant.
- **C7 Coverage-selection leak** · months acted ≈ months the asset rose · resolve: report corr(acted, up); abstain must be direction-blind · anticipate: coverage guard in Stage 3.
- **C8 Rate/spread zero-crossing** · pct_change on near-zero/negative series explodes → false splice/outliers (Fed_Funds, Term_Spread) · resolve: unit-aware ops (absolute-point for RATE_LIKE) · anticipate: classify RATE_LIKE columns; never pct_change them.
- **C9 Reprint vs as-issued drift** · tapes silently revised → reprint acc ≫ as-issued (~85% vs ~52%) · resolve: score only frozen-at-issue calls (MIMESIS) · anticipate: never backfill from reprints.

Open guards not yet built: C5 (max-stat placebo = Stage 5, next), exact per-series lag calendar (Stage 1).

---

## STAGE 0 — DATA AUDIT GATE   [status: BUILT + RUN 2026-08-12]

Purpose: certify the monthly core dataset before any modeling. Writes
`audit_pass.flag`; spine is hard-gated on `verdict==PASS`.

### Diagnostic format (the exact presentation)
```
[identity]  rows=N   feature cols audited=K   panel range D0 -> D1
[anchor]    monotonic=bool   duplicate_dates=n   month_gaps(>35d)=n
[target]    def=sign(<outcome>.pct_change().shift(-1)) [1-mo dir]
            usable=n   up=n (p%)   down=n (p%)   first <outcome> row DATE
[features]  table, one row per feature:
            feature | nonnull | cov% | start | zeros | stale | splice | PITlag
[gate]      Date monotonic: OK/FAIL   dup dates: OK/FAIL   hard splices: <list|none>
[VERDICT]   PASS | BLOCK
```
Column meanings: `stale` = count of repeated consecutive values (zero-bound/carry);
`splice` ∈ {clean, spike, SPLICE, n/a}; `PITlag`=LAG if the series publishes mid-month
(Industrial_Production, US_CPI, M2_Money) and must be lag-aligned in Stage 1.

### Gate rule
BLOCK if: Date not monotonic, OR duplicate dates, OR any GROUNDED feature shows a
hard SPLICE (level break with full 24-mo separation). Else PASS (spikes = WARN only).

### Refinements discovered by running (locked in)
1. SPLICE detection is UNIT-AWARE: `pct_change` jump (>60%) for price/index levels;
   absolute-point jump (>3.0pp) for RATE_LIKE series {GS10, Fed_Funds, US_2Y,
   Term_Spread} that can be zero/negative — pct_change misfires on zero-crossing.
2. Known real defect for Stage 1: `Copper_Close` unit splice at 2000-08-01
   (pre-2000 ~2000x too large). Must rescale / restrict-post-2000 / drop before use.
3. Coverage column defines the effective modeling window (staggered feature starts:
   GS10 1871, IndProd 1919, CPI 1947, FedFunds 1954, M2 1959, Gold 1968, Dollar 1973,
   US_2Y/Term_Spread 1976, WTI 1986, Copper 1992->clean 2000).

### Gold run result (2026-08-12)
VERDICT=BLOCK — sole cause: Copper_Close real splice. Anchor clean; target 684 usable
(52.5% up); rates cleared after unit-aware fix.  File: `stage0_audit/audit.py`.

---

## STAGE 1 — ORACLE (predictor + outcome presentation)   [format spec 2026-08-12]

Presents the predictor, the primary outcome, every constituent variable, the headline
accuracy, the 27-type distribution, graphs, and the historical analogue.

### PHASE 1 — CANONICAL ORDERED STEPS (run in this order, every asset)
1. SHILLER pre-agent — if official Shiller data not yet released, build the skeleton from
   FRED (timely replica); superseded when official data arrives (as-issued).
2. STAGE-0 AUDIT GATE — hygiene: datetime (monotonic, first-of-month, dedup, month-gaps);
   NaN rules (coverage, drop-vs-PIT-ffill, never fabricate); UNIT-AWARE splice; coverage.
   BLOCK on failure. Data must leave this step clean. (Establishes SPINE + FREQUENCY.)
3. ASSEMBLE constituents — outcome + predictor legs (num, den) + inflation series.
4. DISCRETE adjustment — adjust EACH constituent individually BEFORE the ratio: CPI-real
   each leg; 10-yr smoothing where defined (CAPE). Never adjust after forming the ratio.
5. FORM predictor ratio = num/den (or a precomputed adjusted ratio column, e.g. CAPE).
6. CHOOSE N (predictor lookback, months) by PRE-1990 design-sample sweep, then FREEZE.
   N CONSTRAINT: N >= 3 AND a multiple of 3 -> N in {3,6,9,12} (aligns to QUARTERLY
   reporting). Sweep only these. Fallback: first-40% design window if <40 pre-1990 obs.
   N is the change-window for the signal and the 3 legs; horizon stays 1 month ahead
   (independent of N). (SP500 -> N=6 @ 63.4%; Gold -> N=12 flat; Silver -> N=9 flat.)
7. BUILD 27 sub-types = sign triple of (ratio change, num change, den change) over N
   months, +-0.5 SD dead zone (thresholds fit on TRAIN only).
8. SEQUENTIAL ONE-STEP-AHEAD WALK-FORWARD from 1990 — retrain all-past each month, predict
   1 month ahead, roll, reset monthly. NO LB / NO OOS gates here (pure measurement).

### END-OF-PHASE-1 DIAGNOSTICS (REQUIRED — all emitted every run)
- [provenance] predictor ratio; inflation series (discrete, pre-ratio).
- [predictor]  direction = sign of N-month change; note asset-not-in-numerator if so.
- [N chosen]   N + FULL pre-1990 sweep, flagged FLAT (no-signal, ~50% all N) vs PEAKED.
- [data]       rows, date range, coverage/hygiene notes.
- [OVERALL]    ungated sequential-WF accuracy + n (LB informational, NOT a gate).
- headline sentence: descriptive (in-sample) AND walk-forward, labeled.
- month-by-month graph: predictions vs outcomes (cumulative + rolling acc + hit/miss strip).
- FINAL STEP: ALL 27 sub-types with n + sequential-WF accuracy (+ LB informational).
  NO TRUNCATION — print all 27 including empty (n=0) and tiny-n cells; never a top-k
  subset. Truncation hides the cells that overturn verdicts (full-algo convention).
No-edge is an acceptable end state; gates/abstention are deferred to later phases.
Runner: `stage1_pit_data/oracle_stage.py` (config-driven, all assets).

### Headline accuracy sentence (report BOTH, labeled)
`Overall <predictor> prediction accuracy: XX.XX% (matches / total)`
- predictor = CAPE 6-month-change direction; outcome = S&P the FOLLOWING month.
- DESCRIPTIVE (in-sample full history): legacy 56.19%; ZION recompute 56.9%.
- WALK-FORWARD (from 1990, one-step-ahead): raw rule 58.3% (LB 53.6%), learned
  CAPE-type cell 60.8% (LB 56.1%). Always state which one.

### Predictor lookback N — DECISION D6b: FIX N=6 a-priori
Never choose N from the full-sample sweep (that is C6 house-wide selection). Head-to-head
WF: fixed N=6 = 58.3% > fixed N=1 = 57.4% = in-fold-selected N (which picks N=1 every
month). Data-driven N selection underperforms the fixed economic choice. → fix N=6.

### "No movement" / dead zone — DECISION D6 (open, operator to confirm)
Legacy RED DAWN: `CAPE_TYPE_FLAT_THRESHOLD=0.005` applied to `.diff(6)` ABSOLUTE level
changes of CAPE/Price/Earnings (mislabeled "±0.5%"; almost never flags price flat).
ZION current: ±0.5 train-SD adaptive. Neither is a true ±0.5%. RECOMMEND: true ±0.5%
band on `pct_change(6)` of each component. LOCK THIS before type counts are trusted.

### 27-type distribution string (format)
`<Outcome> Type Distribution: T1:<count>(<acc%>[F]), T2:..., ...` — one entry per
POPULATED type; `F` suffix flags acc<50%; per-type acc = next-month Match mean.
Types = triple sign of (CAPE change / Price change / Earnings change), 3^3=27.
Real example (legacy): `T1:607(64%), T2:25(80%), T3:288(65%), T4:38(37%F), ...`

### Constituent variables presented
Predictor CAPE; outcome SP_Price (real); constituents SP_Price, Earnings, Dividend, CPI,
GS10_Rate + derived Real_Price/Real_Earnings/Real_Dividend/Real_TR_Price. CPI is the
deflator (excluded from adjustment; base = most-recent CPI).

### Graphs (9): price; all-variables ±σ; SP/CAPE overlay; candlestick (log-y);
10-year CAPE prediction; individual-horizon (1M..5Y); cumulative-horizon; epoch 3-panel;
prediction-vs-best-historical-match.

### Historical-analogue report
Best 60-month window by RMSE (Pearson-corr tiebreak) vs predicted trajectory at months
{1,3,6,12,24,36,48,60}; writes `oracle_historical_MMYY.json` (era_name, modern_parallel,
match_period, match_rmse, match_correlation, actual_5y_return, key_lesson, current_cape).

### Bridging monthly report (HYACINTH_X <-> CYCLOPS)
EXISTS: `ASSET_PIPELINE/CYCLOPS_NEWSLETTER_MMYY.md` (CYCLOPS Monthly Letter) — SPY/CAPE
from HYACINTH_X appears as the "anchor" engine inside the CYCLOPS five-asset monthly.
Supporting: `COMBINED_RECIPE.md`, `INTEGRATION.md`.

### META / GENERALIZATION (run on ANY asset with analogous variables)
This stage is asset-agnostic. Slot in analogues, everything else identical:
- predictor = a valuation/pressure RATIO (SPY: CAPE = price / 10y-real-earnings; Gold:
  an analogous ratio, e.g. gold / real-rate or gold / M2, chosen by economic prior).
- outcome = the ASSET's own next-period direction (nominal, tradeable).
- constituents = every variable needed to COMPUTE predictor + outcome (SPY: price,
  earnings, CPI, real_price, real_earnings). Cyclically adjust legs via the SHILLER/real
  path where inflation matters.
- 27 sub-types = triple sign of (ratio change / numerator change / denominator change).
- N: chosen by SWEEP ON PRE-1990 data, then FROZEN (never from full sample).
- dead zone: +-0.5 SD on pct_change(N) of each leg (D6 resolved).
- final diagnostic: per-sub-type SEQUENTIAL ONE-STEP-AHEAD walk-forward accuracy.

### THIS STEP ESTABLISHES: spine + frequency + hygiene
- SPINE: the audited, aligned master panel every downstream stage consumes.
- FREQUENCY: monthly cadence + horizon are fixed here (SPY/CAPE: 1-month-ahead).
- HYGIENE (mandatory, this step): datetime monotonic + first-of-month aligned + dedup +
  gap check; NaN RULES (per-series coverage, drop vs PIT-ffill, never fabricate);
  cyclical adjustment; unit-aware splice. Data must leave this step CLEAN or it BLOCKs.

### SHILLER (separate pre-agent)  [from legacy build_shiller_replica.py]
Builds the Shiller skeleton (SP_Price, Earnings, CPI -> CAPE) from FRED in the months
BEFORE the official Shiller `ie_data` workbook is released, so monthly predictions stay
timely instead of waiting on Shiller's lag. Named agent SHILLER; runs upstream of ORACLE
and hands it a complete backbone. Its replica rows are superseded when official Shiller
data arrives (as-issued: the replica is what a live run that month actually saw).

### MANDATORY PROVENANCE + DIAGNOSTICS (printed EVERY run, every asset)
Every ORACLE run must emit, in order:
- [provenance] predictor RATIO = num/den ; inflation series used for adjustment (or "none").
- [predictor]  direction = sign of N-month change in (num/den); note if asset excluded from numerator.
- [N chosen]   N + the FULL pre-1990 sweep (per-N match). A FLAT sweep (all N within a
  few pts of 50%) is an early NO-SIGNAL flag => expect a dead OOS; a PEAKED sweep flags a
  live predictor. (SPY/CAPE: N=1 @ 60.4% peaked -> 67% OOS. GOLD Dollar/M2: 45-51% flat -> 48% OOS, no edge.)
- [data]       rows + date range.
- [WF result]  sequential 1-step-ahead from 1990: acted acc, n, Wilson-LB, abstained.
- 27 sub-type table (below).
Runner: `stage2_walkforward` parameterized `oracle_asset(outcome, num, den, infl, deflate)`.

### NO-EDGE IS AN ACCEPTABLE OUTPUT AT THIS STAGE (operator, 2026-08-12)
ORACLE establishes the single anchor predictor + its honest diagnostic baseline — it is
NOT required to show edge. A flat pre-1990 sweep / sub-50% WF (e.g. Gold Dollar/M2 = 48%)
is a valid result, recorded and passed forward as the baseline. Edge is pursued
downstream: Stage 2 (feature admission), Stage 3 (multi-predictor cascade), Stage 4
(convergence). Never force or fabricate edge to make an anchor "work" here.

### PER-ASSET PREDICTOR RATIOS (config — operator-set)
| asset | outcome | predictor ratio (num/den) | note |
|---|---|---|---|
| S&P 500 | SP_Price | CAPE = Real_Price / Real_Earnings | cyclical (10y earnings) + CPI real |
| Gold | Gold_Close | Dollar_Index / M2_Money | gold NOT in numerator; CPI adj; result: NO edge (48%) |
| Silver | Silver_Close | Dollar_Index / M2_Money (PROPOSED, confirm) | data starts 2000-08 (short); flat, 45% no edge |
| WTI | WTI_Crude_Close | Dollar_Index / M2_Money (PROPOSED, confirm) | data from 1986; thin pre-1990 (N sweep only {3,6}); flat, 51% |
| USD | Dollar_Index | GS10_Rate / M2_Money (PROPOSED, confirm) | predictor MUST be dollar-free (no circularity); 47% below chance |

THE FIVE (2026-08-12): S&P500, Gold, Silver, WTI, USD (dropped Platinum, Natural Gas).

### RULE — LEG UNIQUENESS (enforced in oracle_stage.check_leg_uniqueness)
Every numerator and denominator may be chosen ONCE across all five assets — no predictor
leg is shared. Forces independent/orthogonal predictors (no two assets ride the same
signal). Module PASSES/FAILS this before running. Also: USD's predictor may never contain
Dollar_Index (circularity); no asset's own price in its own numerator; avoid spliced
(Copper) and zero-crossing (Term_Spread) legs.

### CYCLICAL-ADJUSTMENT STATUS (per asset)
Only S&P is adjusted on its own CYCLE (CAPE 10-yr earnings smoothing) + CPI. The other
four have NO cycle-based adjustment (no earnings analog); CPI-real applied only to
price/quantity legs, rate legs left nominal. Giving each asset its own cycle is an open
per-asset modeling task.

### REQUIRED DIAGNOSTIC: per-asset 27-type tables (all five)
The full 27-sub-type sequential-WF table, ONE UNIQUE TABLE PER ASSET, is part of the
system output every run (no truncation). Current distinct proposed set (leg-uniqueness PASS):
S&P=Real_Price/Real_Earnings (CAPE); Gold=Dollar_Index/M2_Money; Silver=Industrial_Production/GS10_Rate;
WTI=US_2Y_Treasury/Fed_Funds_Rate; USD=Gold_Close/US_CPI. Confirmed: S&P, Gold. PROPOSED: Silver, WTI, USD.
Result: only S&P shows edge (63.4%); Gold 51.3%, Silver 51.8%, WTI 53.1%, USD 52.3% flat.

### REUSABLE RUNNER + HYGIENE (seamless multi-asset)
`stage1_pit_data/oracle_stage.py` — config-driven; add an asset = one ASSETS entry
(outcome, num, den, deflate, optional ratio_col for a precomputed adjusted ratio like CAPE).
Runs identical step on all. `ratio_col` lets an asset supply an already-cyclically-adjusted
ratio (SP500=CAPE); else ratio=num/den with discrete CPI-real legs.
HYGIENE FALLBACK: if an asset lacks >=40 pre-1990 obs for the N-sweep, the design sample
auto-falls back to the first 40% of that asset's history (printed as design=...). This is
what let Silver run despite starting 2000-08.
DATA GAPS are the real blocker, not code: Silver needs pre-2000 history added (SHILLER/
ingestion) to share the 1990+ footing; Platinum needs adding to the panel entirely. Any
asset starting at 2000-08 must be Stage-0 audited for the copper-style unit splice first.

### FINAL DIAGNOSTIC OF THIS STEP (locked): 27 sub-types x WF accuracy
Table: T# | ratio/num/den sign triple | n | WF_acc | Wilson-LB | production(act/abstain).
Sequential one-step-ahead (retrain all-past each month, predict 1 ahead, reset monthly).
SPY/CAPE result (real legs, N=1, +-0.5 SD, 1990+): ACTED 67.0% (n=197, LB 60.2%); edge
concentrated in CAPE-up momentum types T27 (83.9%) / T26 (73.1%); down-side near chance;
flat-CAPE sub-types abstain. Cumulative-accuracy path + hit/miss strip accompany it.

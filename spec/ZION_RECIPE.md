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

## LOCKED PARAMETERS (single source of truth — all values operator-set)
- Horizon: 3-month-forward direction. target = sign(outcome[t+3]/outcome[t] - 1).
- Cadence: monthly, first-of-month decision.
- Training: expanding window, frontier <= t-3 (label gap = horizon); ALL selection in-fold.
- OOS scoring starts 1990. Design sample = pre-1990 (first-40% fallback for short history).
- Predictor N (change window): N in {3,6,9,12} (>=3, multiple of 3 = quarterly), FROZEN from
  the pre-1990 sweep, per asset (SPY 6, Gold 6, Silver 9, WTI 3, USD 6).
- Dead zone: +-0.5 TRAIN-SD on pct_change(N) of each leg, z-scored on train, per fold.
- MIN_TRAIN 60 months. Leaf/cell/type floor n = 8.
- Pull bar: WF > 67.5% AND n >= 8 -> standing rule. Conviction star: WF > 70%.
- Filter-strength gate: point-biserial R^2 >= 0.20 (train, in-fold) or discard; none clear -> ABSTAIN.
- Overlap: 3-mo windows rolled monthly -> effective independent n ~ n/3 (report LB_ovl).
- PIT publication lags: Industrial_Production, US_CPI, M2_Money = +2 months.
- Zones: Wilson LB>50 = predictive(act base); UB<50 = anti-predictive(FLIP); spans 50 = coin-toss(abstain).
- Placebo: NOT a gate (dropped). Acceptance = accuracy + Wilson-LB + n.
- Ledger: 1x flat sizing, monthly rebalance, no costs; CAGR = eq[-1]^(12/n)-1; fire-months + calendar.
- Final step: Dollar-Index overlay (declared short-USD tilt), applied LAST.

## CONTAMINATION REGISTER — resolve + anticipate (standing, all assets)
Every leak found becomes a permanent guard. Format: source · manifests as · resolve · anticipate.

- **C1 Unit/vintage splice** · giant single-month level break + full range separation (Copper 2000-08, ~2000x), corrupts z-scores/cells straddling the seam · resolve: drop pre-splice segment or the series · anticipate: Stage-0 unit-aware splice detector, BLOCK on hard splice, per-series vintage check.
- **C2 Publication-timing leak** · mid-month series (Industrial_Production, US_CPI, M2_Money) used as-of-1st-of-month → inflated acc that collapses when lagged (M2/Term_Spread 50.7%→34.0%) · resolve: PIT publication-lag (≥1mo; INDPRO/M2 realistically ~2mo at a 1st-of-month decision) · anticipate: PITlag flag in Stage 0, explicit lag calendar per series in Stage 1, never use a value before its real release date.
- **C3 Drift-capture as skill** · long-horizon (3mo) accuracy dominated by the asset's own trend; high raw OOS acc (60-68%) but ≤0 edge vs always-predict-majority · resolve: net the drift baseline, rank on EDGE (acc−drift), never raw acc · anticipate: always report drift + edge; a call only counts if it beats always-trend.
- **C4 Overlapping-window autocorrelation** · H-month horizon rolled monthly overlaps by H−1 → independence violated, Wilson-LB too tight · resolve: overlap-adjusted LB (eff n≈n/H) · anticipate: always print LB_ovl; treat nominal LB as an upper bound.
- **C5 Multiple-comparison / best-of-N** · sweeping many pairs×types, the best clears 50% by luck (lone survivor out of dozens) · resolve: judge on Wilson-LB + n (and overlap-adjusted LB_ovl) · anticipate: report N tested + LB + n. (Max-stat placebo DROPPED as a gate per operator 2026-08-12; selection-luck acknowledged via LB + n, not a placebo pass.)
- **C6 House-wide selection** · picking predictors on the full sample then scoring "OOS" (the original contamination) · resolve: ALL selection in-fold only · anticipate: fold-local everything — the ZION invariant.
- **C7 Coverage-selection leak** · months acted ≈ months the asset rose · resolve: report corr(acted, up); abstain must be direction-blind · anticipate: coverage guard in Stage 3.
- **C8 Rate/spread zero-crossing** · pct_change on near-zero/negative series explodes → false splice/outliers (Fed_Funds, Term_Spread) · resolve: unit-aware ops (absolute-point for RATE_LIKE) · anticipate: classify RATE_LIKE columns; never pct_change them.
- **C9 Reprint vs as-issued drift** · tapes silently revised → reprint acc ≫ as-issued (~85% vs ~52%) · resolve: score only frozen-at-issue calls (MIMESIS) · anticipate: never backfill from reprints.

Open guards: exact per-series publication-lag calendar (Stage 1). (C5 placebo dropped as a gate.)

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

### Predictor lookback N — RULE (canonical; see LOCKED PARAMETERS + Phase-1 step 6)
N in {3,6,9,12} (>=3, multiple of 3 = quarterly reporting), chosen by the PRE-1990
design-sample sweep then FROZEN per asset (first-40% fallback if <40 pre-1990 obs). Never
chosen from the full-sample sweep (C6). In-fold data-driven N-selection underperforms the
frozen choice (WF head-to-head). Per asset: SPY=6, Gold=6, Silver=9, WTI=3, USD=6.

### "No movement" / dead zone — DECISION D6 RESOLVED (operator: +-0.5 SD)
LOCKED: dead zone = +-0.5 TRAIN-standard-deviations on pct_change(N) of each leg
(ratio/num/den), z-scored on TRAIN only, per fold. |z| < 0.5 -> flat. (Legacy used a
mislabeled +-0.005 on .diff(6) absolute levels that rarely flagged price; superseded.)

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

---

## PHASE 2 / RED DAWN — POOL-REMOVAL + CONVICTION (operator rulings 2026-08-12)
Phase 2 analyzes MONTHS IN THE POOL, removing them as valid analyses appear.
- PULL RULE: any type with sequential-WF > 67.5% AND n >= 8 (operator floor) is PULLED from
  the pool and becomes a standing rule — that type predicts on its type alone going
  forward. Cascade hunts only the shrunken remainder pool (recursive coverage:
  accept -> remove months -> re-analyze remainder).
- CONVICTION: pulled types with WF > 70% enter the conviction-weighting system — for now
  rated ONE STAR (weighting system to be elaborated).
- STARS AT TIER LEVEL: same bar, same currency — a tier-cell earns a star ONLY via
  realized sequential-OOS track (WF>70%, n>=8).
  Tier MEMBERSHIP confers zero stars (train labels anti-predict OOS). Since >67.5% pulls
  a cell into standing rules, stars in practice attach only to STANDING RULES at any
  level. Labels inform where to look, never what to award.
- TIMING (C6 guard, operator AGREED): for BACKTESTED numbers the pull decision is IN-FOLD —
  a type locks only when its TRAILING past-only OOS record clears the bar at that month.
  Full-record pulls act only as GOING-FORWARD standing rules from today; never historical
  pool-carving.
- PULL BARS (operator-set 2026-08-12, BOTH required): WF > 67.5% AND n >= 8. Fail either ->
  stays in pool. (Bar raised from 65% by operator; conviction star bar stays 70%.)
- SPY standing snapshot (2026-08-12 FINAL @67.5): PULLED = T27* (77.1%, n=35), T5* (72.7%,
  n=11), T14 (68.8%, n=125); * = one star (>70%). Coverage 171/434 (~39%) at 70.8% blended.
  REMAINDER POOL = 263 months @ ~58.6%: T26(59, 66.1) T15(52, 59.6) T1(36) T17(31) T2(30)
  T13(21) T25(9, 66.7) T3(8) T18(7) + 10 degenerate. T26/T25 fell back in at the new bar.
- Other assets @67.5 (n>=8): WTI pulls T3 only (71.4, n=14; T18 67.4 n=46 misses by 0.1);
  Silver [provisional predictor] pulls T19 (68.0, n=25) + T5 (77.8, n=9); USD pulls T22
  (71.4, n=14, C5 lone-cell caution); Gold none.
  (Operator said "T11" — recorded as T5, whose n=11; no T11 exists in the SPY table.)
- FLIP verdicts: trailing-OOS flip TESTED AND REJECTED (flip months 23.1% vs base 76.9% —
  losing streaks mean-revert; matches ARTEMIS flip-not-learnable). Train-side under-50
  flip only, Wilson-gated. Post-dip rebound subsets are NEVER certification evidence
  (selection artifact — C5/C6 class).
- TIER verdict (first honest cascade test on SPY remainder): IS 67-71% -> WF 52.6%
  (15-19pt overfit gap; tier1 not better than tier2 OOS). Tiers = conviction labels only,
  never direction-changers. NOTE: legacy RED DAWN cascade NEVER EXECUTED on SPY/CAPE
  (missing _Z6 column code; all months Model 1 = raw CAPE direction) — the 71%/0.623
  legacy anchor was CAPE+convergence, NOT tiers; there is no legacy evidence tiers add value.
- Other assets' pulls (floor 8): WTI T18 (67.4%, n=46), T3 (71.4%, n=14); Silver T19
  (68.0%, n=25) + T3/T5 (66.7%/77.8%, n=9) [provisional — predictor unconfirmed];
  Gold none; USD T22 (71.4%, n=14) borderline-lone-cell, treat with C5 suspicion.
- Workflow: read original RED DAWN + CYCLOPS letters first (DONE), then walk the
  cascade step-by-step on SPY's remainder pool, one checkpoint per step.

### CASCADE WORKFLOW ORDER (operator, 2026-08-12)
1. RUN the cascading tier analysis on the remainder pool (in-fold, per type).
2. AFTER EACH tier run: FILTER ANALYSIS — which (predictor, threshold) the in-fold search
   chose, modal filter + selection-stability %, WITH the per-type color scatter plots
   (x = primary-filter z (train-scored), y = forward return, color = tier, o=hit x=miss).
   Scatters are part of the standing diagnostics, emitted every run.
3. Tier table format (legacy O-value format + the new OOS column):
   type | tier | n | IS% | Bayes% | AvgRet|ok | Cov | O-val | o_cov | WF sequential-OOS% | LB.
   OOS column = SEQUENTIAL 3-MONTH-FORWARD forecast (train <= t-3, predict t+3, roll monthly).
   Artifacts: reports/RD_cascade3m_months.csv + RD_cascade3m_scatter.png.

### TRUNCATION DOUBLE-CHECK (operator, 2026-08-12 — mandatory, EVERY analysis stage)
Truncation overturns verdicts (full-algo convention). Check TWICE, independently:
- CHECK 1 — PRE-RUN (machinery audit): before running, verify against the stage spec that
  NOTHING is cut down: full threshold grid (percentile, not token points), all derivative
  forms (incl. 2nd-order), full candidate pool, all cascade retries, all types included.
  Any deliberate reduction must be DECLARED in the run header (what + why), never silent.
- CHECK 2 — POST-RUN (month accounting): pool_total == emitted + abstained_with_reason,
  reconciled PER TYPE and printed. Zero silently dropped months; ABSTAIN rows carry
  reasons (type-train<floor, leaf<floor, candidate-missing). Display shows ALL types
  including degenerates — no display filtering.
- LOOP-UNTIL-CLEAN (operator): repeat the audit cycle (CHECK 1 + CHECK 2, fix anything
  found, re-run) until TWO CONSECUTIVE full audit passes discover ZERO truncations.
  One clean pass is not enough; the verdict unlocks only after the second consecutive
  clean pass. Each pass's findings (or "none") are logged in the run record.
A verdict is PROVISIONAL until the loop closes. (Audit 2026-08-12 caught v1 cascade:
12/263 months silently dropped incl. all of T18; 3-point threshold grid vs legacy
50-point percentile; 1 derivative form vs 5; 9 candidates vs 34 — verdict held open.)

### FILTER-STRENGTH DIAGNOSTIC (operator, 2026-08-12 — MANDATORY, before threshold analysis)
Measure each candidate filter's strength BEFORE any threshold is searched:
- Statistic: point-biserial R^2 = corr(candidate z, Match)^2 within the type, TRAIN-side
  in-fold — the % of Match-variance the candidate accounts for. (Match = base direction
  correct that month. Monotone with the Welch/Cohen-d screen: d 0.2/0.5/0.8 ~ R^2 1%/6%/14%.)
- Report R^2 for EVERY screened candidate per type; the chosen filter's R^2 travels with
  it into all downstream tables.
- HARD GATE (operator, 2026-08-12): a candidate must explain >= 20% of Match-variance
  (train-side, in-fold) or it is DISCARDED before threshold analysis. If NO candidate
  clears 20% for a type -> the type ABSTAINS (operator ruling — supersedes earlier
  "emit base direction": no qualifying filter = no call; dark is valid).
  (R^2 20% ~ Cohen's d ~ 1.0.) The gate kills noise-carving outright.
- CAVEAT the gate does NOT cover: small-n luck. Null R^2 ~ 1/(n-1); at n~30 the max
  across ~50 candidate-columns can clear 20% by chance (cf. T25 55.2% @ n=28). The gate
  therefore NEVER substitutes for the n-floor. gate + n-floor are the lock; small-n cells
  are judged on Wilson-LB + n (placebo dropped as a gate per operator). At n>=300, 20% is
  unreachable by chance; a large-cell pass is a genuine monster.
- SPY effect (descriptive preview): splits attemptable only in T1 (US_2Y 22.0%), T15
  (WTI 27.3%), T17 (Gold 28.7%), T25 (Gold 55.2%, small-n suspect); T2/T3/T13/T26 ABSTAIN.

### PRODUCTION BOARD — STANDARD OUTPUT INTO HAL (operator, 2026-08-12; per asset, every run)
The monthly HAL report carries this table per asset (re-printed every run; gate runs
in-fold so bucket membership can shift as evidence accumulates):
  bucket | types | months | share% | status/acc
  1. ACT — standing rules (pulled types, WF>67.5 & n>=8; stars >70%)  -> emit type direction
  2. CASCADE — split permitted (some filter R^2>=20% in-fold)          -> tier calls if survived
  3. ABSTAIN — gate-fail (no filter >=20%)                             -> dark, no forced call
  4. ABSTAIN — floor (type n<8 / degenerate)                           -> dark
SPY snapshot (3-mo horizon, FINAL): ACT 282mo/64% @~77% (T5* T14 T15 T26 T27*); remainder
CASCADE tiers = NOTHING survives (untruncated, 2 clean passes); ABSTAIN gate-fail + floor
cover the rest. Dark board = valid answer. (Earlier 1-mo snapshot superseded by the 3-mo lock.)
- Evidence (2026-08-12, SPY v1 post-mortem): cells where the selector chose near-zero
  filters collapsed hardest (T2: chosen 0.2% vs 4.7% available -> IS72/OOS31; T15: 0.7%
  vs 27.3% -> IS77/OOS33); cells where chosen = strongest (T17 28.7%, T26 8.5%) behaved
  least pathologically. Selection criterion must track variance strength (Welch-d screen).

### TARGET-CONVENTION ASYMMETRY (operator catch, 2026-08-12)
When a leaf/type flips, the t-test screen can run against the OLD (base) or NEW (flipped)
Match target. INVARIANT across the two: the primary variable chosen, its |d|/R^2 strength,
and the primary threshold VALUE (Youden-J magnitude is symmetric under label complement).
NOT INVARIANT: the pass/fail ORIENTATION inverts (positive-predictive side flips to the
other side of the same threshold). Because the cascade recurses ASYMMETRICALLY (secondary
on pass, model-3 on fail), the two conventions build DIFFERENT TREES -> different tier
membership -> per-tier OOS numbers are CONVENTION-DEPENDENT.
RULES: (a) the target convention MUST be declared in every run header; an undeclared
convention is a truncation-check finding. (b) v1 SPY per-tier figures are provisional on
this axis too. (c) Flip validity is NOT rescued by convention: forward corr(leaf train
acc, base outcome) ~ 0 (-0.107) either way; relabeling adds no forward info. (d) Under
flip-abolition, emitted direction = base everywhere -> aggregate accuracy is convention-
INVARIANT (61.8% survives); only the conviction LABEL depends on the (pinned) tree.

### PLACEBO NOT REQUIRED (operator 2026-08-12)
Max-stat placebo is DROPPED as an acceptance gate. Standard = accuracy + Wilson-LB (and
n). Do not re-insert placebo as a survival condition. (Selection-luck is acknowledged via
LB + n; operator accepts the accuracy numbers on that basis.)

### PULL HORIZON LOCKED = 3-MONTH (operator 2026-08-12)
All type-level pulls AND tier OOS computed at the 3-MONTH sequential horizon (train <= t-3,
predict t+3), consistent with the tier cascade. Earlier 1-month pulls SUPERSEDED.
SPY CAPE @3mo, TYPE LEVEL: 5 types pull (T5 90% n10 LB60, T27 80% n35 LB64, T14 77.4% n124
LB69, T26 74.6% n59 LB62, T15 73.1% n52 LB60) — ALL reliably predictive (LB>50).
COVERAGE = 280/420 scored months = 67% @ ~77% blended; remainder 140mo (T1,T2,T3,T13,T17,
T25) -> cascade closure (expected null, few months). CAPE edge is ENTIRELY type-level; no
tier required. (Horizon inconsistency caught: cascade had wrongly kept T15/T26 in remainder.)
REGIME/WAVEFORM (CAPE 3mo stream, 420mo 68.6%): NO two-simultaneous-waveform evidence
(2-sinusoid R2=0.19; the 4.3yr candidate = 2nd harmonic of 8.5yr = ONE non-sinusoidal
cycle). 3 extreme drops (2012-09, 2020-10, 2022-11; all to ~50-53% at trend->reversal
stress) = SEQUENTIAL rupture signature (CYCLOPS), not a mixture. Proper 2-regime test =
condition accuracy on a state variable (pre-registered). Charts: reports/
regime_decay_spy_cape.png, cape_waveform_decomp.png.

### FLIP DOCTRINE — CORRECTED (operator 2026-08-12; supersedes earlier "abolish flip")
The flip STAYS in the recipe permanently (it is valid method — e.g. reliably-inverse
markers in medicine). Earlier "abolish" recommendation RETRACTED. Corrected criterion —
THREE ZONES around 50% (LB may be as low as .4; a coin toss is neutral, not failure):
  - RELIABLY PREDICTIVE: Wilson LOWER bound > 50% -> act on base direction.
  - RELIABLY ANTI-PREDICTIVE: Wilson UPPER bound < 50% -> FLIP (this is the flip's job).
  - COIN-TOSS: interval spans 50% -> ABSTAIN (no reliable direction either way).
The v1 "flips destructive" finding was flipping on the WRONG TRIGGER (train acc<50%,
endogenous to the search). Correct trigger = realized-OOS anti-predictiveness (UB<50).
SPY result: ZERO reliably-anti-predictive cells (n>=8) — the sub-50 cells (T1-t4 35.3%
UB59, T2-t2 33.3% UB65) STRADDLE 50 = coin-tosses. Verdict = "n too small," NOT "flips
worthless." Flip machinery remains; on SPY it fires never.
- DOUBLE-FLIP: current rebuild = single leaf-flip (no month flips twice; predA/predB
  compositions verified correct). If the full 4-model cascade (base-flip -> model3 re-flip
  -> leaf flip) is implemented, double/triple flips CAN occur and each composition MUST be
  verified (two flips = base) — mandatory trace step.
- FLIP AS DIAGNOSTIC: even when a cell fails gates, its flipped direction + percentage
  carry information for the DECISION step (a reliably-wrong-leaning cell is a soft veto).

### O-VALUE ROLE — CORRECTED: veto/derating diagnostic, not selection, not flip-trigger
Negative O-value flags UNDERPERFORMING cells (SPY: 3 neg-O-val cells averaged ~39% OOS;
corr(O-val,OOS)=+0.92 on survivors BUT partly mechanical — AvgRet touches realized ret —
and only 5 cells). USE: soft veto / conviction-derating input to the decision step.
NEVER: selection ranking, nor a flip trigger (flip still needs UB<50 confirmation).

### PHASE-2 CANONICAL WORKFLOW (operator 2026-08-12, per predictor/asset, IN ORDER)
1. Anchor 27-type analysis -> pulls (WF>67.5 & n>=8) -> standing rules.
2. Cascade tiers on remainder (in-fold; R^2>=20% gate; gate-fail=ABSTAIN; filter-strength
   + scatter after each tier run; tiers across-all AND within-each-type).
3. If a type/tier COLLAPSES in OOS -> REGIME ANALYSIS (CYCLOPS): rolling-accuracy chart,
   when it last worked, decay trend, cyclicality (dominant period, # cycles) — see below.
4. If still no WF validity after regime analysis -> ABSTAIN.
5. MIRROR-inverse: test IN-SAMPLE first (is an inverse/error engine plausible?), THEN
   out-of-sample, scoped to that predictor's ACTED months only. Survivor = satellite.
6. SECOND PREDICTOR on the REMAINING months only: LOWER thresholds; seek a second
   threshold ideally covering ~half the prior predictor's months.
7. FINAL RECKONING: coverage + in-sample AND out-of-sample accuracy of the covered months.
8. Flip direction+percentage retained as decision-step diagnostic throughout.

### REGIME-ESTABLISHMENT / DECAY RULES (operator 2026-08-12)
Trigger: a cell/predictor no longer matches direction ~3 readings out. Then present:
- 10-yr (36-mo) ROLLING OOS-accuracy chart; shade below-50% regimes.
- WHEN it last worked (last month rolling>=50%); decay TREND (pp/yr, declining vs stable).
- CYCLICALITY: autocorrelation / FFT -> dominant period + # full cycles over span.
- Question answered: is the failure a persistent decay (act on it) or a cyclical trough
  (a working pattern that no change was enacted around)?
Built: reports/regime_decay_*.png (regime_decay_spy_cape). SPY anchor HEALTHY: 61.8%,
6/188 windows <50%, still working (2025-07), flat -0.13pp/yr, ~7.8yr mild cycle.

### TIER VERDICT (SPY, untruncated rebuild, variant B, 2026-08-12)
Across all types: tier2 n54 OOS57.4 (UB70), tier3 n3 100 (tiny), tier4 n39 51.3 (UB66);
tier1 NEVER emitted (secondary fails R^2 gate). Within each type: all real-n cells are
coin-toss; only micro-n T1-t2(n4)/T2-t4(n8) read PRED (thin, n too small). Tier best-bucket
is INCONSISTENT across types -> no stable directional info; tiers = conviction/coverage
labels only. Pool 56.2% (LB_ovl 39%) = no edge over drift. Loop closed 2 clean passes.

### FILTER METHOD (v1, stated for the record)
Per fold, per type: candidates (HYPERION registry, PIT-lagged) z-scored on TRAIN stats;
threshold grid z in {-0.5, 0, +0.5}; primary = (predictor,threshold) maximizing train
J = |acc(pass) - acc(fail)| (floor 8/side); secondary re-splits pass side (different
predictor); model-3 re-splits fail side -> 4 tiers; leaf flips only if TRAIN acc < 50%.
Modal filter + stability % reported: stable modal = candidate correspondence; churn = noise.

### MIRROR-INVERSE / ERROR-REGIME TEST (MANDATORY after predictor analysis, every asset)
Lineage: HYACINTH_10_MIRROR (inverse-predictor finder; error-month engine; fed TEARS
satellites/hedge legs). ZION rule (operator 2026-08-12): after the anchor predictor
analysis, TEST whether any candidate predicts the anchor's ERROR months — in-fold: flag
month if its candidate-state's TRAIN error-rate > train base +10pp (state n>=8); PASS iff
Wilson-LB(err|flagged) > base error rate. If PASS -> reserve as ERROR-TESTING REGIME /
future SATELLITE function (never sizes; conditioning only). If FAIL -> move on. Either
way the test runs and the result is recorded — possibility is tested, never assumed.
- SEQUENCING RULE (operator, 2026-08-12): MIRROR-INVERSE may NOT run until the prediction
  pool for the specific predictor is exactly known — i.e., AFTER the production board is
  finalized (pulls + cascade + gate/floor abstentions locked). Its input = the ACTED
  months of that predictor ONLY (standing rules + surviving cascade calls). Errors on
  would-have-abstained months are not errors; scoping to the full stream is invalid.
- SPY FINAL (2026-08-12, re-scoped to the 280 acted standing-rule months): base error
  23.2%; NO candidate reliably predicts the standing rules' errors -> NO MIRROR satellite
  for SPY. (The earlier ungated-434-mo FAIL was mis-scoped and withdrawn; this is the clean run.)
- SPY SECOND-PREDICTOR pass (152 remainder months, lower bar 60%): nothing — best is GS10
  covering 61% but only 53.8% (LB 44%, coin). No second predictor. SPY edge = type-level only.

### O-VALUE vs SEQUENTIAL OOS — MEASURED VERDICT (2026-08-12, 11 tiers n>=8)
corr(O-value, OOS3m) = +0.33 (partly mechanical — AvgRet|ok touches realized outcomes);
corr(Bayes, OOS3m) = -0.48 Pearson / -0.55 Spearman; corr(IS, OOS3m) = -0.40.
The accuracy core of O-value ANTI-predicts sequential OOS (inverted conviction gradient,
tier level — matches WF-pilot type-level finding). RULE: O-value/O-score = descriptive
payoff context ONLY; never selection. Selection ranks on realized OOS Wilson-LB.
STATUS: SPY remainder-pool cascade FAILS OOS as a whole (untruncated rebuild 55.7%,
LB_ovl ~36%); isolated bright tiers are best-of-N thin cells — judged on accuracy+LB+n
(placebo dropped per operator); none survive. SPY tier level: nothing survives (final).

### O-VALUE AS INVERSE PREDICTOR — TESTED, REJECTED (2026-08-12)
Conviction-fade rule (a-priori bar: invert months routed to leaves with TRAIN acc > 70%,
the overfit-wall signature): faded acc 54.8% (LB 44%), decaying 59.5% -> 50.0% across
halves = noise consumption, not a standing inverse edge. RULE: the IS/O-value
anti-correlation is a DIAGNOSTIC ONLY — use as VETO/derating (refuse to act on months
routed to IS>70% overfit-flagged leaves), NEVER as an inversion signal. Third flip-family
rejection (ARTEMIS, trailing-flip, conviction-fade) — flips are not learnable in this
ecosystem; the recipe stops testing new inversion variants without new evidence.

---

## STAGE 6 — LEDGER (money) + BOOK   [method locked 2026-08-13]
Converts directional predictions to P&L; reports ACCURACY and MONEY together.
- POSITION: on acted months, position = predicted direction (the 3-mo signal), realize
  the 1-MONTH forward return (monthly rebalance); 0 (cash) on abstain. Assumptions stated
  every run: 1x FLAT sizing, NO costs (both refined later by TRON sizing / a cost model).
- METRICS: CAGR = eq[-1]**(12/n) - 1 (n = MONTHS; NEVER len(r)/52 — the annualization
  defect); Sortino = mean(r)/downside-std * sqrt(12); Calmar = CAGR/|MaxDD|; MaxDD.
- TWO BASES, always both: FIRE-MONTHS (annualize over only fired months) and CALENDAR
  (all months incl cash). Report for BOTH the last-10-yr window AND the full period.
- YEAR-BY-YEAR table: calendar return, fired count, accuracy per year.
- RECONCILIATION RULE (truncation-class, mandatory): build the ledger on the VALIDATED
  positions (the pipeline's own in-fold acted-month directions). Reconcile each sleeve's
  acted-month count to the validated coverage; a MISMATCH is a truncation finding. Never
  re-derive positions a different way (caught: an inline recompute gave Gold 17 acted vs
  validated ~85 — discarded).
- SPY result (2026-08-12, type-level standing rules): FIRE-MONTHS 16.0% CAGR / 2.80 Sortino
  / -11.5% MaxDD / 84% acc (86 mo); CALENDAR 11.1% / 1.99 (121 mo, 35 cash); 8 of 10 years
  positive; down years 2018 & 2022 = the low-accuracy years. MIRROR (re-scoped, 280 acted):
  NO error engine. Second-predictor pass (152 remainder): nothing (best GS10 53.8% coin).
  SPY edge = type-level standing rules ONLY.

## STAGE 6b — SYZYGY BOOK (combine sleeves)   [status: BUILDING 2026-08-13]
Equal-weight combine the 5 monthly sleeves (SPY, Gold, Silver, WTI, USD; USD = cash, no
rules) into one book; book monthly return = mean of sleeves with data (cash sleeves = 0).
Same two-base metrics + coverage (months with >=1 sleeve firing) + all-cash %. Runs under
the truncation double-check loop (reconcile per-sleeve acted counts; loop until 2 clean).
RESULTS (2026-08-13, syzygy_book.py; all 5 sleeves reconciled exact; 2 consecutive clean):
- BOOK last-10yr: fire 9.3% CAGR / Sortino 3.88 / Calmar 2.12 / MaxDD -4.4%; cal 7.5% / 3.49.
- BOOK full 1990+: fire 6.2% / 2.47 / MaxDD -7.1%; cal 4.9% / 2.20.
- Coverage 350/440 fire (79.5%); 90 all-cash (20.5%).
- Per-sleeve fire (full): SPY 12.9%/2.29, Gold 10.7%/1.02, Silver 50.1%/3.21 [PROPOSED],
  WTI 47.1%/2.61 [PROPOSED], USD cash.
- READ: SPY-dominated (57% of fired months, effectively always-long drift). Diversification
  buys RISK not return: SPY-only cal 8.1%/1.83/-12.8% -> book 4.9%/2.20/-7.1% (Sortino up,
  MaxDD halved). Silver/WTI CAGRs not trustworthy (proposed ratios, thin). USD costs ~1.3pp.
- BOOK WEIGHTING (operator-locked 2026-08-13): SPY-ANCHORED 50/20/15/15 (SPY .5, Gold .2,
  Silver .15, WTI .15, USD 0) — highest-Sortino, lowest-DD scheme. 1x = BASE; 1.3x =
  optional "push for ~1%/mo" (Sortino invariant to leverage). Last-10yr 1x: 9.7% CAGR /
  Sortino 2.93 / -6.5% DD; full-1990 1x: 6.5% / 1.84 / -7.8% (the HONEST full-cycle read;
  last decade flattered by bull + SPY-drift). Rejected: max-gain weighting (concentrates in
  thin/PROPOSED sleeves), equal-active (22% CAGR but Sortino 1.35 / DD -22%).
- Book value = DIVERSIFICATION + DRAWDOWN CONTROL, not directional alpha (SPY always-long).
- Stage 9 overlay APPLIED -> OFF (not a hedge; all-USD book).

### FIVE-ASSET SUMMARY (type-level accuracy, 3-mo OOS, 2026-08-12)
SPY: 5 pulls ~77% (ROBUST, T14 n124 LB69) — 64% coverage. Gold: 3 pulls 71.8% (T1/T2/T25).
Silver: 3 pulls 70.5% [PROPOSED ratio + IndProd non-timely leg]. WTI: 2 pulls 73.4%
[PROPOSED, ZIRP-fragile]. USD: NONE — clean ABSTAIN. Tier level: NOTHING survives on ANY
asset. Combined monthly (5 sleeves): ~17% of months all-dark (no asset predicts; matches
legacy ~13% stand-down); max 4 assets ever fire together; USD always cash.

## STAGE 9 — DOLLAR-INDEX OVERLAY (FINAL STEP — applied LAST, after the book)  [operator 2026-08-13]
The very last step of monthly ZION, after SYZYGY combines the sleeves. The book is
USD-denominated, so a Dollar-Index overlay adjusts the whole book for dollar exposure.
- Applied as a DECLARED SHORT-USD TILT, NOT a hedge (ecosystem currency-step verdict: no
  genuine FX hedge survived for a USD-denom book; a declared tilt is the honest form,
  effect marginal, TRAIN k ~ 0.1).
- DISTINCT from the USD sleeve (which is an asset/outcome): this overlay is a book-level
  currency tilt on the combined portfolio, not a directional prediction.
- Reported as a final adjustment to book CAGR/Sortino/Calmar (with/without overlay).
- It is the LAST step; nothing runs after it.
- TIMING (fix): overlay currency return must be FORWARD-aligned (t->t+1) to the book's
  holding period. First attempt used backward pct_change -> garbage; corrected.
- RESULT (2026-08-13, corrected, k=0.10): the whole book is USD-DENOMINATED (all 5 sleeves
  USD-priced) -> there is NO foreign-currency exposure to hedge. A currency overlay is a
  fresh SPECULATIVE bet, not a hedge. Tested Dollar-Index + 5 majors (EUR/JPY/GBP/AUD/CAD):
  almost any currency nudges Sortino +0.1-0.4 in one direction, but the helpful SIGN is
  INCONSISTENT across currencies (AUD-short vs CAD-long etc.) = pure DIVERSIFICATION, not
  a hedge; best-fit (AUD-short 2.61 vs base 2.16) is best-of-N overfit. Only real dollar
  link = commodities (Gold/WTI/Silver) inversely dollar-sensitive, and that bet is weak.
- VERDICT: overlay stays OFF (k=0). A currency position for this book would need its OWN
  directional edge (JANUS-style FX predictor), not an overlay. (Reproduces ecosystem verdict.)

---

## MONTHLY ZION — STUDY CONCLUSION (wrapped 2026-08-13)
Clean-OOS monthly system COMPLETE end-to-end (Stage 0->9), entirely under sequential
one-step-ahead WF, in-fold selection, PIT lags, and the truncation loop-until-2-clean.
FINDINGS:
- SPY/CAPE = the one robust monthly anchor: 5 type-level standing rules, 3-mo directional
  accuracy ~77% (fire-months 84% last decade), 282mo/64% coverage. Its money is mostly
  BETA (always-long momentum) + drawdown-capping; not proven directional alpha.
- TIER/CASCADE: NOTHING survives on ANY asset (all coin-toss at honest n / overlap-adj LB).
  The edge is TYPE-LEVEL only. Flip family rejected 4 ways. O-value = veto diagnostic only.
  MIRROR (SPY, re-scoped): no error engine. Second-predictor pass: nothing.
- Gold (Dollar/M2, prior) 71.8% type-level, thin. Silver/WTI/USD ratios PROPOSED (not
  priors) - suggestive at best; USD a clean ABSTAIN. Currency overlay = not a hedge
  (all-USD book) -> OFF.
- BOOK: SPY-anchored 50/20/15/15, 1x base (1.3x optional). HONEST full-cycle ~Sortino 1.84,
  ~0.55-0.70%/mo, DD ~-8 to -10% levered; last-decade flattered (2.93 / ~1%/mo). Value =
  diversification + drawdown control, not alpha. ~17% of months all-dark (valid stand-down).
- Book monthly return = equal per-month blend, so book != sum of columns (1/n dilution;
  verified exact, not a bug).
OPEN (deferred, non-blocking): confirm Silver/WTI/USD real priors (need MXN in panel);
cost model; live emission (MIMESIS/HAL); MCP server to serve monthly_state (legacy pattern).
NEXT: WEEKLY ZION - same OOS methodology, single asset at a time; ~4x data so cascade/tier
may have power monthly lacked (do NOT assume it inherits 'tiers don't survive').
Deliverables: pipeline/ (oracle_stage, hyperion_build, reddawn_cascade_full, multiasset_pipeline,
syzygy_book), reports/, spec/ (this recipe + ROADMAP + HYPERION + RED_DAWN + PROGRAM_MAP).

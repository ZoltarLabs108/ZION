# ZION RED DAWN — Stage 3 (the DISCOVERY engine)

RED DAWN is ZION's discovery stage. Where ORACLE (Stage 1) rides ONE anchor ratio per
asset and reports its honest sequential-WF baseline, RED DAWN extends the analysis to
MULTIPLE predictors and searches for the HIDDEN CORRESPONDENCES — the non-obvious
predictor-cell → next-month-direction relationships a single anchor cannot see.

It KEEPS the RED DAWN machinery that works: the 27-type ternary grammar, train-majority
direction, Wilson-LB gating, and the four-model cascade (recursively partition a type's
months into four leaf-models via threshold filters, each with its own flip). It REPLACES
the machinery that leaks: every house-wide / fixed-split selection (the contaminated
50/25/25 and 0.65-tail blocks, and HYACINTH_X's full-history in-sample fit) is torn out
and rebuilt as SEQUENTIAL ONE-STEP-AHEAD WALK-FORWARD with IN-FOLD-ONLY selection — the
identical discipline as `stage1_pit_data/oracle_stage.py`.

Horizon and cadence are inherited from ORACLE: predict the asset's **next-month**
direction; retrain on all-past each month; roll one month; reset every month. No fixed
split exists anywhere. This is the ecosystem's first real purged walk-forward applied to
the four-model cascade (per PROGRAM_MAP: HYACINTH_X had none — its WF/permutation gates
were dead code, all "walk-forwards" were contaminated tail splits).

---

## 0. WHAT RED DAWN CONSUMES FROM ORACLE

RED DAWN is layered strictly on top of ORACLE — it does not re-derive the anchor, it reads
ORACLE's frozen decisions and adds a discovery layer:

- **Anchor ratio + legs** — the per-asset `(num, den, deflate, ratio_col)` from
  `oracle_stage.ASSETS`. The anchor defines the top-level 27 types exactly as ORACLE builds
  them. RED DAWN's top-level cells are byte-for-byte ORACLE's cells.
- **Frozen N** — the predictor lookback chosen by ORACLE's pre-1990 design-sample sweep
  (N ∈ {3,6,9,12}, multiple-of-3, then FROZEN). RED DAWN never re-sweeps N; a re-sweep on
  in-sample data would be C6 house-wide selection. It reads N per asset from ORACLE.
- **PIT publication lags** — `oracle_stage.PUB_LAG` (Industrial_Production, US_CPI,
  M2_Money lagged ≥2 mo at a first-of-month decision). Applied to the panel before any
  fold, identically for anchor legs and cascade candidates.
- **Leg-uniqueness registry** — the anchor legs already claimed by ORACLE
  (`check_leg_uniqueness`). RED DAWN's cascade candidate pool EXCLUDES every anchor leg so
  the discovered predictors are orthogonal to the anchor (no double-counting the anchor).
- **The single-anchor WF baseline** — ORACLE's per-type sequential-WF accuracy. RED DAWN's
  headline is not "beats a coin"; it is "beats the ORACLE anchor" (edge over ORACLE), so
  the anchor baseline is carried forward as the reference to clear.

RED DAWN re-derives the anchor type memberships IN-FOLD (train-only z-params) rather than
reading a precomputed type column, because ORACLE itself computes types fold-locally; this
keeps the whole stack PIT with zero shared-state leakage.

---

## 1. THE MULTI-PREDICTOR IDEA — where "multiple predictors" actually enters

ORACLE has exactly one predictor: the anchor ratio, whose 27 sign-types carry a
train-majority direction. RED DAWN adds a SECOND tier of predictors underneath each type:

> Within the months of a single anchor type, the four-model cascade uses ADDITIONAL
> candidate predictors (macro series distinct from the anchor legs) to partition those
> months into four leaf-models, each a purer direction cell than the type as a whole.

So "multiple predictors" is the cascade's candidate pool: the grounded macro universe
(Dollar_Index, M2_Money, Industrial_Production, GS10_Rate, Fed_Funds_Rate, US_2Y_Treasury,
WTI_Crude_Close, Gold_Close, Term_Spread_10Y_2Y, …) minus (a) the outcome, (b) the asset's
own price, (c) the anchor's own num/den legs, (d) globally-banned series (Copper_Close
2000-08 splice; Term_Spread as a ratio leg — zero-crossing). Each candidate is expanded
into a small transform menu (see §3). The cascade DISCOVERS which candidate + threshold
best splits each type — and that discovery is the "hidden correspondence".

The hard part is admitting these many candidates **without** house-wide selection. §4 is
the exact mechanism.

---

## 2. CANONICAL ORDERED STEPS (run in this order, every asset)

1. **INHERIT from ORACLE** — anchor `(num, den, deflate/ratio_col)`, frozen N, PUB_LAG,
   anchor-leg exclusions. Apply PUB_LAG to the panel once.
2. **ASSEMBLE candidate pool** — grounded universe minus (outcome, own price, anchor legs,
   banned series). This SET is fixed a-priori by economic prior; it is never data-selected
   (selecting the *set* on the full sample would be C6). What is selected in-fold is *which*
   candidate + *which* threshold, on past-only data.
3. **BUILD anchor grammar (KEPT)** — over the frozen N, ternary triple of
   (ratio change, num change, den change), ±0.5 train-SD dead zone → 27 types. z-params
   fit on TRAIN rows only, refit every fold.
4. **SEQUENTIAL ONE-STEP-AHEAD FOLD LOOP** from 1990 (§5). At each decision month t:
   a. Build the train pool (all-past, PIT — labels resolved ≤ t).
   b. Assign every train row and row t to an anchor type (train z-params).
   c. Take the type row t falls into; gather that type's TRAIN months.
   d. **Fit the four-model cascade IN-FOLD** on those train months (§3 logic, §4 selection).
   e. **Route row t** through the fitted cascade to exactly one leaf-model.
   f. **Admit or abstain**: emit the leaf's direction iff the leaf's train Wilson-LB ≥ GATE
      (0.45); else ABSTAIN. NO forced prediction, NO OOS gate at measurement.
   g. Record (t, type, leaf, chosen-predictors, pred, realized, conviction).
5. **ROLL** to t+1 and REFIT EVERYTHING (z-params, type memberships, cascade splits,
   thresholds, flips, directions). Nothing is frozen across folds.
6. **END-OF-STAGE DIAGNOSTICS** (§6) — per-asset, per-type, per-model tables, NO truncation.

---

## 3. THE FOUR-MODEL CASCADE — re-fit INSIDE each fold (KEPT logic)

The legacy `analyze_type` (HYACINTH_X ~2736–2931) recursively partitions a type's months
into four leaf-models. RED DAWN keeps that tree shape and its flip logic EXACTLY, and
re-fits it fresh on each fold's train-only rows of the current type:

```
type-train-months
├── PRIMARY split      (best candidate c1, threshold θ1, direction/flip on train)
│     ├── Primary_Pass ──► SECONDARY split (best NEW candidate c2 on the Pass subset)
│     │        ├── model1  (secondary pass)   ── leaf: dir + own flip + train Wilson-LB
│     │        └── model2  (secondary fail)   ── leaf: dir + own flip + train Wilson-LB
│     └── (Primary_Pass with no secondary ⇒ model2 = whole Pass subset)
└── Primary_Fail  ────► MODEL3 split (independent flip on the Fail subset, best NEW cand c3)
          ├── model3  (model3 pass)           ── leaf: dir + own flip + train Wilson-LB
          └── model4  (model3 fail / residual)── leaf: dir + own flip + train Wilson-LB
```

KEPT invariants (unchanged from legacy):
- **Base flip.** The type's base direction is the train-majority next-month direction; if
  the anchor rule's train raw-accuracy on the type is significantly < 0.5 (Wilson one-sided,
  `flip_is_significant`), the analysis target is flipped. Flip only on significant evidence,
  never on a bare < 50%.
- **Independent per-leaf flip.** Each of model1..4 decides its OWN flip from its OWN train
  raw-accuracy (Wilson one-sided). No cascading of flips between leaves.
- **Recursive partition, not a flat menu.** Secondary is searched only within Primary_Pass;
  model3 only within Primary_Fail. Each split excludes variables already used upstream on
  that branch (leg-uniqueness within a branch).
- **Direction = train-majority of the leaf.** Conviction = the leaf's train Wilson-LB.

REPLACED (the contamination):
- Legacy fit thresholds/flips/accuracies on the WHOLE history of the type (in-sample). RED
  DAWN fits them on TRAIN-only rows of the type, inside the fold, every month.
- Legacy `red_dawn_cascade` ranked candidates on a fixed VALIDATION block carved from a
  50/25/25 chronological split, TEST held for "OOS". Both blocks are gone. The honest
  out-of-sample is the single next month, scored across all folds. In-fold ranking uses a
  PURGED INNER-VALIDATION slice (§4), not a house-wide block.
- Legacy `analyze_type` ranked primary/secondary candidates by t-test p-value / effect
  size (best-of-N over dozens of vars ⇒ multiple-comparison inflation, C5). RED DAWN ranks
  on Wilson-LB (n-penalized), with a train-n floor and a max-stat placebo hook for Stage 5.

---

## 4. IN-FOLD MULTI-PREDICTOR ADMISSION — the exact mechanism (the hard part)

The whole risk of "multiple predictors" is that with a candidate pool of ~10 vars × a
transform menu, the best train-fit clears any bar by luck and does not generalize. The
mechanism below admits many candidates in-fold while making that luck show up as degraded
walk-forward accuracy (it can never leak, because the winner is chosen on past-only data
and scored only on the untouched next month).

### 4.1 The fold's data partition (all past-only)

At decision month t, the train pool = rows whose next-month label is resolved by t. Split
it PURGED into:
- **inner-train** = the earlier `(1 − VAL_FRAC)` of the train pool by time,
- **inner-val**   = the latest `VAL_FRAC` of the train pool by time,
- **purge**       = drop the 1 boundary month whose label straddles inner-train/inner-val
  (H=1 ⇒ drop one month), so no inner-val label leaks into inner-train.

Both slices are ≤ t. Nothing from t+1 onward is ever touched. inner-val is the fold's
own held-out ranking sample — it replaces the contaminated fixed VA block, and it moves
forward every fold (it is not a static tail).

### 4.2 Candidate generation (fixed set, in-fold transforms)

For each candidate variable v in the a-priori pool, build a small transform menu (the
"multiple predictors" concretely):
- Δ over the frozen N (`v.diff(N)`), z-scored on inner-train,
- cyclic-window level deviation for w ∈ {60, 92, 120} (`v − rolling_mean(w)`), z-scored,
- velocity / acceleration `diff(k)`, `diff(k).diff(k)` for k ∈ {3,6,9} (quarterly-aligned).

Every z-normalization uses inner-train mean/sd only. The transform MENU is fixed a-priori;
only which menu entry wins is selected in-fold.

### 4.3 Per-candidate score (Youden-J threshold with flip, KEPT)

For a leaf's target `correct∈{0,1}` (anchor rule right/wrong, after base flip), search each
candidate feature's threshold θ and direction on **inner-train**:
- J = TPR − FPR over (θ, {>, <}); flip the kept side if J < 0 so the kept region is the
  high-correct region (KEPT from `red_dawn_tier`/`find_optimal_threshold_with_flip`).
- The candidate's kept region on inner-train must clear the train-n floor (MIN_N) and a
  min-per-group floor.

### 4.4 Admission + winner selection (the two-gate rule)

Two distinct gates, straight from the roadmap (Stage 3d: "0.45 admits; winner chosen on
validation/OOS Wilson-LB"):

1. **TRAIN-ADMIT gate (GATE = 0.45).** A candidate is *eligible* only if its kept-region
   Wilson-LB on inner-train ≥ 0.45. This lets candidates through — it is a floor above
   noise, not the emit bar. Small-n or coin-flip candidates are dropped here.
2. **WINNER = max inner-VALIDATION Wilson-LB.** Among eligible candidates, apply each one's
   (θ, dir) — frozen from inner-train — to the **inner-val** rows and compute the kept
   region's Wilson-LB there. The candidate with the highest inner-val Wilson-LB wins the
   split. This is the honest selection: a candidate that only fit inner-train loses on
   inner-val and is not chosen. Ties break on larger inner-val support.

This is applied at each cascade node: PRIMARY (on the type), SECONDARY (on Primary_Pass),
MODEL3 (on Primary_Fail), each excluding variables already spent on that branch.

### 4.5 Refit, route, emit

- **Refit on full train.** Once the winning (candidate, θ, dir) is chosen per node on
  inner-train→inner-val, refit each LEAF's direction (train-majority) and independent flip
  and conviction on the FULL train pool (inner-train ∪ inner-val), so the emitted call uses
  all available past. (Selection used the purge; the final direction estimate does not need
  it because direction is a majority vote, not a ranked search.)
- **Route row t.** Apply the fold's frozen primary/secondary/model3 thresholds to row t's
  feature values → row t lands in exactly one of model1..4.
- **Emit or abstain.** Emit the routed leaf's direction iff its full-train Wilson-LB ≥ GATE.
  Otherwise ABSTAIN. There is NO OOS gate here — the sequential WF accuracy IS the
  measurement (same as ORACLE: pure measurement, gates deferred to Stage 4/5).

### 4.6 Why this is not house-wide selection (C6) and not best-of-N leak (C5)

- The candidate SET is fixed by economic prior, never chosen from the sample.
- Every θ, direction, flip, ranking, and winner is computed on rows ≤ t. The scored month
  (t+1) is never seen by selection.
- Selection ranks on a purged INNER-VAL slice, so in-fold overfit to inner-train is
  penalized before the winner is picked.
- The number of candidates searched per fold is recorded and handed to Stage 5's max-stat
  placebo (permute labels, re-run the ENTIRE in-fold selection, tail test) — the C5 guard.
- Because splits refit every month, a "correspondence" is only credible if it is chosen
  repeatedly across folds AND the acted months are accurate out-of-sample. A predictor that
  wins one fold by luck contributes one OOS month and washes out.

### 4.7 Coverage-selection guard (C7)

RED DAWN can abstain, so acted months are a selected subsample. The guard reports
`corr(acted, market-up)` over the evaluable span and the acted-month up-rate vs the
abstained-month up-rate. If acting ≈ "the months the asset rose", the edge is coverage
selection, not skill. This is a DIAGNOSTIC (reported, not a gate that peeks at the future).

---

## 5. THE FOLD LOOP (sequential one-step-ahead — identical discipline to ORACLE)

```
for t in range(len(panel)):
    if date[t] < 1990 or label[t] invalid: continue
    train = rows s in [0, t) with next-month label resolved    # PIT, all-past
    if len(train) < MIN_TRAIN: continue
    types = anchor_grammar(train z-params)                      # KEPT, refit this fold
    typ_t = types[t]
    type_train = train rows where types == typ_t
    inner_tr, inner_val = purged_split(type_train, VAL_FRAC)    # §4.1
    tree = cascade_fit(type_train, inner_tr, inner_val, pool)   # §3 shape, §4 selection
    leaf = route(row_t, tree)                                   # model1..4
    if leaf.train_wilson_lb >= GATE and label[t] != 0:
        emit(dir=leaf.direction, conv=leaf.train_wilson_lb)
    else:
        abstain()
    record(t, typ_t, leaf.id, tree.chosen_vars, pred, realized, conv)
```

Every quantity is refit from scratch each month. No state survives a fold except the
recorded OOS stream. This mirrors `oracle_stage.run` exactly (`tr = arange(0, t)`,
train-only z-params, per-type majority) with the cascade inserted between "type" and
"prediction".

---

## 6. END-OF-STAGE DIAGNOSTICS (required every run, NO truncation)

Emitted per asset, in order:

- **[provenance]** anchor ratio, frozen N (from ORACLE), PUB_LAG applied, candidate pool
  (explicit list, with the excluded anchor legs / banned series named).
- **[OVERALL]** sequential-WF accuracy, n acted, Wilson-LB (informational), abstain count,
  and the fraction of months that reached each cascade leaf.
- **[edge vs ORACLE]** RED DAWN acted-accuracy MINUS ORACLE anchor-baseline accuracy on the
  same months — the discovery must beat the single anchor, not just a coin. Report both.
- **[coverage guard]** `corr(acted, market-up)`, acted-up-rate vs abstained-up-rate (C7).
- **PER-TYPE table — ALL 27, no truncation** (including n=0 and tiny-n): T# | anchor sign
  triple | n acted | WF acc | Wilson-LB | which leaves fired | abstain count. Truncation
  hides the cells that overturn verdicts (full-algo convention); print every type.
- **PER-MODEL (leaf) table within each populated type**: model1..4 | n | WF acc | Wilson-LB
  | modal chosen predictor + selection-frequency across folds | flip-rate across folds.
  Because splits refit every fold, the "predictor for type T model m" is a DISTRIBUTION,
  not a constant — report the modal predictor and how often it was chosen. A stable modal
  predictor across folds = a real correspondence; a churning one = noise. This distribution
  is itself the primary discovery diagnostic.
- **[C5 hook]** candidates searched per fold (min/median/max) — the input to the Stage 5
  max-stat placebo. No best-of-N number is ever quoted without this.

NO-EDGE IS AN ACCEPTABLE OUTPUT. If no cascade leaf beats the ORACLE anchor out-of-sample,
RED DAWN reports the dark board and passes the ORACLE baseline forward unchanged. Edge is
never forced or fabricated to make discovery "work" (operator standing rule).

---

## 7. CONTAMINATION REGISTER — what RED DAWN specifically must not do

- **C6 house-wide selection** — never pick the candidate SET, thresholds, flips, or winner
  on the full sample. All in-fold, past-only. (The reason RED DAWN is being rebuilt.)
- **Fixed splits** — no 50/25/25, no 0.65 tail, no static VA/TE block. The only split is
  the per-fold purged inner-train/inner-val, which moves forward every month.
- **C5 best-of-N** — rank on Wilson-LB not p-value; record candidates-per-fold; hand to
  Stage 5 placebo. Never quote a lone survivor without the placebo tail test.
- **C2 publication timing** — consume ORACLE's PUB_LAG; never use a mid-month series at its
  nominal first-of-month date.
- **C7 coverage selection** — abstention must be direction-blind; report corr(acted, up).
- **C3 drift-capture** — headline is edge over the ORACLE anchor (and over always-majority),
  never raw accuracy alone.
- **NO forced prediction** — the fold ends in a gated in-regime call or ABSTAIN. No
  default-to-majority to fill an empty slot (roadmap hard rule).

---

## 8. INTERFACES / FILES

- Runner: `reddawn_stage.py` (this stage). Config-driven per asset; adding an asset = one
  `ASSETS`/pool entry, mirroring ORACLE.
- Consumes: `stage1_pit_data/oracle_stage.py` (anchor config, frozen N, PUB_LAG,
  leg-uniqueness), the master panel from HYPERION, and Stage-0's `audit_pass.flag` gate.
- Emits: per-asset OOS stream (one row per decision month: type, leaf, chosen predictors,
  pred, realized, conviction, acted/abstain) for Stage 4 (convergence) and Stage 6 (ledger).
- Downstream: RED DAWN's per-month directional signal + conviction is one lens into Stage 4
  CONVERGENCE; its conviction (leaf train Wilson-LB) feeds TRON sizing (never as a raw
  multiplier — conviction-only, per PROGRAM_MAP).
```

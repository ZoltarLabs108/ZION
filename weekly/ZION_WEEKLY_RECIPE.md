# ZION WEEKLY RECIPE — clean-OOS weekly system (S&P first)

**Status: DRAFT SPEC FOR REVIEW. Nothing built, nothing run, nothing wired. No production file touched.**
Date: 2026-08-13. Author of record: Shaun (operator). This document is the thing to review *before* any build action.

---

## 0. Quarantine principle (non-negotiable)

The **monthly ZION system works and is left completely alone.** This weekly system is a **separate section**, physically isolated:

- Lives under `~/Desktop/ZION/weekly/` only. It writes nothing outside that subtree.
- It does **not import** live monthly modules. Instead it takes a **frozen snapshot copy** of the methodology primitives it needs (grammar27, cascade, Wilson-LB, WF harness) into `weekly/zion_core_frozen/`. Reason: an `import` couples the two lineages — a weekly edit could then break monthly. A frozen copy cannot. The cost (drift between copies) is acceptable and explicit; the monthly original stays canonical.
- It touches **no AEGIS / MERCURY / CERES / HAL file**, no launchd job, no live tape. The current live weekly book keeps running untouched until *you* decide to cut over.
- Cutover to production is a **separate, later, explicitly-authorized step** — never a side effect of building this.

```
~/Desktop/ZION/weekly/
  ZION_WEEKLY_RECIPE.md        <- this spec
  zion_core_frozen/            <- frozen copies of monthly primitives (rescaled, not imported)
  stage0_audit_weekly/
  stage1_grammar_weekly/
  stage2_wf_weekly/
  stage4_convergence_weekly/
  ledger_weekly/
  reports/                     <- all weekly outputs land here, nowhere else
```

---

## 1. Scope of this pass

- **Asset: S&P 500 first** (SPY spine). Everything below is written for SPY; other assets are a later copy-with-reconfig.
- **Target/horizon: forward direction over H weeks, where H is DISCOVERED BY A SWEEP — not assumed.** On a `W-FRI` resample, `label(t) = sign(SP[t+H]/SP[t] − 1)`; decision uses only rows with a resolved label available at decision time, so train frontier ≤ `t−H` (embargo = label gap = H, satisfied by construction). **H is chosen exactly the way the monthly system chose H=3: a horizon sweep** (see §1a). The old draft fixed H=1wk; that was wrong — the monthly H=3 was *discovered*, and the weekly H must be too.
- **Honest prior, stated up front:** the most probable *honest* outcome for weekly SPY is **ABSTAIN-heavy / drift-capture**, same verdict the monthly Stage-4 SPY convergence reached (gated 68.4% but edge only +1.1pp over drift, placebo p≈.058 → ABSTAIN). Weekly direction carries *less* drift signal per bet and *more* microstructure noise than monthly. **The recipe is built to detect that truthfully, not to manufacture an edge.** If weekly SPY has no admissible edge, the correct deliverable is a clean "ABSTAIN, here's why" — which is still valuable, because it tells you to run SPY as beta/execution, not as weekly alpha.

### 1a. Horizon discovered by sweep (same process as monthly's H=3)
The monthly system did **not** assume 3-month. It swept the horizon and ranked candidates by **honest type-pull yield**: at H=1 month, 3 types cleared the pull bar; at H=3, **5 types** cleared it (coverage 67% @ ~77% blended, every pulled type Wilson-LB > 50%). H=3 won. We replicate that process at weekly:

- **Candidate grid:** H ∈ {1, 2, 3, 4, 6, 8, 13} weeks (≈ 1 week … 1 quarter). Spans the tradeable-weekly end through a ~monthly/quarterly horizon.
- **Per candidate H, run the sequential type grammar** (train frontier ≤ t−H, in-fold z-scoring) and compute per-type: WF accuracy, n, and — the key weekly upgrade — **edge over the H-week drift base rate** with an **overlap-adjusted Wilson-LB (eff n = n/H)**. The monthly recipe's own C3/C4 rules mandate ranking on *edge (acc − drift)*, not raw accuracy, and overlap-correcting the LB; at weekly this is decisive because the drift base rate is high (~54–56% at H=1wk, rising with H).
- **Ranking criterion (frozen before looking):** the horizon that maximizes **reliably-predictive EDGE structure** — count of types with `WilsonLB(edge, eff-n) > 0` at `n ≥ floor`, then coverage × blended edge as the tie-break. This is the monthly "how many types clear the pull bar" yield, expressed on edge instead of raw accuracy.
- **Freeze H, then run the full cascade at that H.** If *no* horizon yields reliably-predictive edge structure, the honest output is **ABSTAIN at every horizon** — a valid and likely result for weekly SPY.

**Overlap correction is therefore conditional on the swept H:** at H=1wk labels don't overlap (eff n = n, no penalty); at any H > 1wk the H-week horizon rolled weekly overlaps by H−1, so `eff n = n/H` applies (supersedes the old draft's blanket "no overlap penalty"). §3.2 is revised accordingly.

---

## 2. The weekly pipeline, stage by stage

Same spine as monthly ZION, every fixed count rescaled to weekly units (×4.348 = 52.1775 weeks/yr ÷ 12 months/yr). Rescaled constants are collected in §3.

### ⚠️ CRUCIAL PREPROCESSING STEPS (operator 2026-08-13) — do not skip, do not reorder
These are non-negotiable and each is a *discrete* step performed **before** the one after it:

1. **Discrete cyclical adjustment of every variable, individually, BEFORE pairing.** Each numerator and each denominator is passed through `shiller_cpi_adjust` (52-week rolling average re-expressed in current dollars) **on its own**, and only then combined into the `num/den` ratio. Order is mandatory: `adj = cyc(raw)` first, `ratio = cyc(num) / cyc(den)` second — never `cyc(num/den)`. This matches the live MERCURY `build_predictor()` and puts both legs in real, cycle-smoothed terms so the ratio compares like with like. Impact is largest at long windows and for pairs with different inflation exposure; it is a required correctness step regardless of magnitude. The three grammar legs are then `Δ(ratio)`, `Δ(cyc_num)`, `Δ(cyc_den)`.
2. **Long, honest predictor history (no artificial truncation).** A predictor is only as testable as its shortest leg. Series with short native history (e.g. the dollar via `DTWEXBGS`, 2006+) MUST be extended to real long history before judging them — the dollar is built as a **level-matched splice of `DTWEXM` (1973→2019) + `DTWEXBGS`** (documented, cf. the TED splice), or the candidate is flagged THIN and never surfaced as a winner. Never rank a predictor on a coincidentally-short recent window.
3. **Absolute-change legs, then in-fold z-score** (division-free; unit-robust for rates/spreads), matching MERCURY's `.diff()` convention — not pct-change, which divides by zero on rate series.
4. **Effective-n discipline**: overlap (eff n = n/H) always; plus a staleness cap (eff n = n/max(H, 4.348)) for any monthly-ff / forward-filled leg, so a stale predictor never gets weekly-density credit it didn't earn.

Skipping or reordering any of these overturns the verdict, so they are gated in code, not left to convention.

### Stage 0 — DATA AUDIT GATE (`stage0_audit_weekly/`)
Row-level admission on the SPY weekly spine + every predictor series, ported from monthly `stage0_audit/audit.py`. HARD-block on: non-monotonic dates, duplicate weeks, zeros in a price/level, and **basis-splice** (a `pct_change` jump > 0.60 for levels / > 3.0pp absolute for rate-like series **with complete pre/post range separation** over the separation window). WARN (not block) on stale-repeats and week-gaps. **Weekly change:** the separation window rescales 24 months → ~104 weeks; the stale-repeat detector must be tuned looser because forward-filled monthly macro *legitimately* repeats for ~4–5 weeks (see §3, staleness). Writes `audit_pass.flag`.

### Stage 1 — grammar27 + recursive cascade (`stage1_grammar_weekly/`)
The 27-type ternary grammar, unchanged in form: sign-triple of Δ(A), Δ(B), Δ(zA−zB) over a swept window k, z-scored **on TRAIN only** with a ±dead-zone. Recursive per-round refit cascade: per round, per type, direction = TRAIN-pool majority; **train-quality floor = Wilson-LB(effective-n) > GATE**; winner = max VALIDATION-pool Wilson-LB; **TEST never touched in selection**. Halts on remainder-too-small or no candidate clearing the floor.

**Weekly-specific feature choice (this is the biggest real change, see §3.4).** At monthly, SPY's predictor is CAPE. **CAPE barely moves week-to-week** — a CAPE-Δ grammar at weekly resolution is almost all dead-zone. So the weekly SPY predictor pool must lead with **natively-weekly series**: term spread (10Y−2Y, 10Y−3M), VIX, credit spreads (BAA10Y), the dollar index, short-rate level/velocity — all sampled daily→weekly and genuinely moving each week — with **CAPE retained only as a slow regime conditioner**, not as the weekly trigger. This is not optional polish; a straight monthly-predictor transpose produces a dead board.

### Stage 2 — walk-forward (`stage2_wf_weekly/`)
Expanding window, in-fold selection only, one-step-ahead. Refit weekly (the monthly WF pilot found **refit cadence irrelevant**, so weekly refit is a convenience, not a requirement). Decision weeks start once `MIN_TRAIN` is satisfied. The `[OOS-METHOD VERIFICATION]` machine-assert (frontier gap ≥ H, window strictly expands) is carried over verbatim — it is the thing that makes this the first *honest* weekly WF in the ecosystem, replacing the live engine's in-sample selection.

### Stage 4 — convergence / voting (`stage4_convergence_weekly/`)
Three independent one-step-ahead weekly streams — **RED DAWN** (grammar/type vote), **ODYSSEY** (in-fold quantile-bin analogue), **SANCTUARY** (similarity-weighted analogue) — on one SPY spine. Vote rule ported exactly: **≥2 present; UNANIMOUS → act; any dissent → FLAT ("flat on split").** Report pure-agreement (descriptive) and **GATED** (agreement *and* the agreement signal's trailing in-fold record clears the edge gate) side by side; GATED is the only deployable rule. CORE = all-3 present & unanimous.

### Stage 5 — DECISION + certification
Convergence gated on the **edge-over-drift** gate of §3.3 (not raw accuracy). Only gauntlet-certified cells are tradeable; conflict → flat; **backtest is built from the exact same certified cells so backtest == emitted tape.**

### Stage 6 — ledger (`ledger_weekly/`)
Position on acted weeks = predicted direction × next-week return, cash on abstain. **Annualize on true calendar span, never `len(r)/52`** (this defect is already fixed in the live ledger; carry the fix in). CAGR/Sortino/Calmar/MaxDD/Win/ProfitFactor. **New mandatory line vs monthly: transaction costs (§3.7).**

---

## 3. Threshold & interpretation changes forced by weekly data density

This is the section that matters most for correctness. More data is **not** simply "more power" — several monthly-calibrated thresholds become *wrong* at weekly resolution.

### 3.1 Effective-n cap (predictor-dependent) — the core correction
Weekly gives ~4.348× the rows. A fixed Wilson-LB gate (0.45) is easier to clear at bigger n, so raw weekly n would **loosen** a monthly-calibrated gate. But the right divisor is **not** uniform:

- **Monthly-published, forward-filled predictors** (CAPE, CPI, IndProd, M2, sentiment, PCE): ~4.35 consecutive weekly rows carry the *identical* predictor value. Their **effective independent n ≈ n / 4.348.** Apply the cap.
- **Natively-weekly predictors** (price ratios, VIX, yields, dollar, credit spreads — daily→weekly): each week is a genuinely new reading. **Effective n ≈ n** (no cap, or a mild cap only for return autocorrelation, which for weekly is small).

**Interpretation:** the cap is justified by *predictor staleness*, not by return autocorrelation. Tag every predictor `MONTHLY_FF` or `WEEKLY_NATIVE` and apply the divisor per-predictor. A single blanket `n/4.348` (as the old `WEEKLY_RECIPE.md` proposed) is too harsh on weekly-native signals and too generous on nothing — per-predictor is the honest version.

### 3.2 Overlap penalty — conditional on the swept H
`eff n = n / H_weeks` (the C4 correction), applied with whatever H the §1a sweep discovers. If the sweep picks H=1wk, labels don't overlap and eff n = n (a genuine gain in independent evidence). If it picks H>1wk, the `n/H` divisor applies and partly offsets the weekly density gain — the sweep sees this cost directly because it ranks on overlap-adjusted edge-LB, so it only picks a longer horizon when the edge structure genuinely justifies the independence tax.

### 3.3 Raw-accuracy gates must become **edge-over-drift** gates
This is the interpretation trap. Weekly market up-rate ≈ **54–56% per week**. A raw-accuracy Wilson-LB > 0.45 gate is **meaningless at weekly** — always-long drift clears it trivially, at enormous n, with a tight LB. So:

- The **binding gate is edge over the weekly drift base rate**, not absolute accuracy. Compute drift = in-fold marginal up-rate on the emitted weeks; admit a cell only if `WilsonLB(accuracy − drift, effective-n) > 0` with a margin. The MIRROR / always-UP baseline (already in ZION) *is* this test; at weekly it is promoted from diagnostic to **the** gate.
- The monthly **pull bar (WF > 67.5%, n ≥ 8)** does **not transfer.** 67.5% was ~+7.5pp over monthly drift (~60%). The weekly equivalent is drift(~55%) + that edge, i.e. ≈ 62%, but measured as an LB on the *edge*, effective-n capped — not as an absolute 67.5% or a naive 62%.
- Consequence you should expect: many weekly cells that look "68% accurate" will fail because their edge over drift is ~+1–3pp and the effective-n-capped LB on that edge straddles zero. **That is the ZION SPY monthly verdict reappearing at weekly, and it is the correct answer, not a bug.**

### 3.4 Feature staleness / publication lag
Monthly macro at weekly resolution is stale up to 4–5 weeks. PIT publication lag stays in **calendar** terms (IndProd/CPI/M2 ≈ +2 months ≈ +9 weeks) then forward-filled; the forward-filled flat segments must be (a) allowed by the Stage-0 stale-repeat WARN and (b) counted at their reduced effective-n (§3.1). Weekly-native series carry only their true daily→weekly lag.

### 3.5 Window / period / floor rescaling (×4.348)
| Monthly | Weekly |
|---|---|
| swept k ∈ {3,6,9} | k ∈ {13,17,22,26,30,35,39} weeks |
| lookback windows | {260, 400, 520} weeks |
| MIN_TRAIN = 60 | 260 weeks (~5 yr) |
| type-train floor = 8–15 | 35–65 weeks |
| tr_floor = 30 | 130 weeks |
| val_floor = 8 | 35 weeks |
| dead-zone ±0.20σ / ±0.5σ | unchanged (unit-free) |
| Wilson z = 1.645 | unchanged |
| GATE = 0.45 (floor) | unchanged as a floor; **binding gate = edge-over-drift, §3.3** |

### 3.6 Multiple-comparisons surface grows
More decision weeks × candidates × forms = a bigger search surface, so the overfitting risk *rises* even as n rises. Keep the **leak tripwire** (columns screened per fold ≤ 5×pool) and rescale the permutation-null draw count with the surface. **Placebo/null stays REPORT-ONLY** (operator standing rule 2026-08-13) — it is a diagnostic, never an admission gate. The admission gate is the edge-over-drift Wilson-LB (§3.3) + as-issued forward record.

### 3.7 Transaction costs — **now mandatory** (monthly ignored them)
Weekly trades ~4.35× more often than monthly. Costs the monthly recipe could ignore now bite ~4.35× harder: ~52 turnovers/yr × (spread + slippage) per leg, worst on **UNG** (roll/spread) and non-trivial on PPLT/SLV. **The weekly ledger must model costs, and the edge-over-drift gate must clear net of costs.** A weekly cell whose gross edge is +2pp but whose round-trip cost eats +1.5pp is not tradeable. This single change kills a large fraction of marginal weekly cells and is the most important weekly-specific reality check.

---

## 4. How monthly predictions intersect the weekly (and the "monthly fires / weekly abstains" question)

The two systems are **different horizons on different evidence.** Monthly ZION emits a 1–3-month direction with its own OOS admission; weekly emits a next-week direction with its own. They are combined as **two sleeves at two horizons**, by **netting exposure**, under three rules:

1. **Abstention on one horizon is NOT a veto on the other.** Weekly abstaining means "no admissible *1-week* edge this week" — a statement about 1-week predictability, silent about 1–3-month predictability. It is not evidence against a monthly call.
2. **When both fire and agree** → reinforce (size up within the gross cap). **When both fire and disagree** → net the exposures / go flat on the contested portion; the shorter horizon does not automatically win.
3. **Netting, not projection** (same principle as the JANUS two-sided sizer): combine dollar exposures, don't let one system's signal overwrite the other's.

### The specific question: weekly does NOT fire, monthly DOES — place the monthly wager?
**Yes — place it, on the monthly gate's own authority, at the monthly horizon and monthly sizing — with one asset-specific caveat.**

Reasoning:
- A monthly "fire" means the monthly cell cleared **its own** OOS edge-over-drift Wilson-LB admission. That evidence stands on its own. Weekly's silence is not disagreement; it is "the 1-week horizon has nothing to say," which is expected most weeks even when a 1–3-month edge exists. So weekly abstention should **not** cancel an admitted monthly bet.
- Mechanically it's usually a **non-event**: a monthly position is opened once and **carried** across its holding weeks. On a weekly-abstain/monthly-fire week you are simply *holding* the monthly position; the weekly system just doesn't add or trim that week. You are not placing a *new* weekly wager — you're honoring an existing monthly one.

**The caveat — and it's the important part for SPY specifically:** the honest monthly SPY verdict is **drift-capture, not alpha** (Stage-4 ABSTAIN). So a monthly SPY "fire" is, in practice, *being long the market's drift*. Placing that wager is fine **as beta**, but do not book it as skill, and do not size it as if it were an edge. For assets where the monthly system has a *real* admitted edge (Gold, Silver at monthly), the monthly wager is justified as alpha and the answer is an unqualified yes. For SPY, the answer is: yes, but recognize you're buying drift, so size it as beta and let the *cost/gross-cap* discipline govern it — don't let a drift-capture "fire" crowd out capital that a genuinely-admitted sleeve could use.

**One thing to explicitly avoid:** treating weekly-abstain + monthly-fire as a *high-conviction* signal ("the calm-week version of the monthly bet"). It isn't — the two carry independent information; absence of a weekly signal adds no conviction to the monthly one. Place the monthly wager at its normal monthly conviction, no bonus.

---

## 5. What to review before any build

1. **Horizon**: DISCOVERED BY SWEEP over {1,2,3,4,6,8,13}wk, ranked on edge-over-drift pull-yield — same process that found monthly H=3. Not assumed. §1a / §3.2.
2. **Quarantine mechanism**: frozen-copy of core vs shared import. §0. (Recommend frozen copy.)
3. **Per-predictor effective-n** (`MONTHLY_FF` ÷4.348 vs `WEEKLY_NATIVE` ×1) vs a blanket divisor. §3.1.
4. **Edge-over-drift as the binding gate** replacing raw-accuracy 67.5% pull bar. §3.3.
5. **Mandatory transaction-cost modeling** and the net-of-cost gate. §3.7.
6. **Monthly↔weekly combination = netting, abstention ≠ veto, SPY-monthly = beta not alpha.** §4.
7. **Expectation-setting**: a clean "weekly SPY ABSTAIN" is an acceptable, likely, and valuable outcome — the build must be willing to return it.

## 6. Build order
0 audit → **0.5 HORIZON SWEEP (discover & freeze H, §1a)** → 1 grammar/cascade at the frozen H with the weekly-native feature pool → 2 honest expanding WF → 4 three-lens convergence → 5 edge-over-drift certification → 6 net-of-cost ledger. Each stage runs the loop-until-2-consecutive-clean truncation audit before the next begins (truncation overturns verdicts — house rule). The sequential OOS invariant (`train frontier ≤ t−H`, in-fold-only selection, expanding window, machine-asserted at ≥5 checkpoints) holds at **every** horizon the sweep tries — the sweep never peeks past `t−H`.

---

## 7. IMPLEMENTATION AUDIT — as-built vs spec (added 2026-08-14)

### 7.1 Audit of the WTI dev build (`~/Desktop/ZION_WEEKLY_WTI/weekly/`)
The dev tree has the capabilities scattered across ~39 scripts and **multiple competing drivers**
(`zion_weekly.py`, `zion_driver.py`, `weekly_pipeline_spy.py`, `weekly_full_spy.py`, …). The file
called the **final book** — `reports/final_book_weekly_ledger.csv` (960 wks 2008–2026, CAGR 8.07%,
Sortino 1.90, maxDD −23.3%, 58% invested) — was produced by **`zion_weekly.py`, a SHORTCUT driver.**

| # | Stage (spec §6) | Recipe requires | Exists in tree | In the FINAL-BOOK driver | Verdict |
|---|---|---|---|---|---|
| pre | weekly-native pool + long history (dollar DTWEXM splice) | yes | ✓ | ✓ referenced | **PRESENT** |
| 0 | data-audit gate → `audit_pass.flag` | yes | ✓ (`weekly_pipeline_spy.py`) | ✗ not in final path | **SUBSET** |
| 0.5 | **HORIZON SWEEP {1,2,3,4,6,8,13}, freeze H** | yes | ✓ (`type_analysis.py`) | ✗ **H=3 hardcoded — "sweep omitted for speed"** | **TRUNCATED** |
| 1 | grammar27 + recursive cascade, TEST untouched | yes | ✓ | ✓ (`stream()`: train-floor+val-winner) | RAN (fixed H) |
| 2 | expanding WF, in-fold, train ≤ t−H | yes | ✓ | ✓ sequential per-week | RAN |
| 3.1 | effective-n cap ÷4.348 | yes | ✓ | ✓ (`stale=4.348`) | RAN |
| 3.3 | **edge-over-drift as binding gate** | yes | partial | ✗ ranks firing-acc×coverage, not edge | **DEVIATION** |
| 3.7 | mandatory transaction costs | yes | ✓ | ✓ (5 bps) | RAN |
| 4 | **3-lens RD+ODYSSEY+SANCTUARY convergence** | yes | ✓ (`weekly_pipeline_spy.py`) | ✗ **predictor-agreement, not the 3 engines** | **TRUNCATED/SUBSTITUTED** |
| 5 | DECISION + edge-over-drift certification | yes | ✓ | partial (MIRROR/INTERSTELLAR/CASSANDRA ✓; edge-cert ✗) | PARTIAL |
| 6 | net-of-cost ledger | yes | ✓ | ✓ | RAN |
| — | per-stage loop-until-2-clean truncation audit | yes | ✗ | ✗ | **MISSING** |

**VERDICT: there is NO non-truncated final weekly book.** The certified-looking `final_book_weekly_ledger.csv`
was built by the shortcut path with ≥4 material truncations vs spec — (1) horizon NOT swept (H=3 fixed),
(2) convergence is predictor-agreement not the mandated 3-lens, (3) edge-over-drift gate not applied,
(4) per-stage truncation audit absent (5) stage-0 gate off the final path. **Its 8.07%/1.90 numbers must
NOT be cited as the recipe-faithful result.** The full-fidelity pieces exist but were never unified into
one dutiful end-to-end run, and two dev worktrees (`weekly-oos-dev`, `weekly-wti-dev`) remain unreconciled.
The **PP sleeve is NOT wired to weekly** (monthly overlay only; Sortino-neutral even there).

### 7.2 STANDING implementation-audit protocol (now part of the recipe)
Before any weekly book may be labelled **final**, assert for EVERY stage in §6, in the SAME driver that
writes the final ledger (not a sibling script):
1. the stage's code path actually executed and wrote its artifact (non-empty);
2. its OOS invariant held (`train frontier ≤ t−H`, in-fold-only);
3. **no parameter the recipe says to SWEEP was hardcoded** (esp. H);
4. the mandated gate for that stage was the one applied (edge-over-drift, not raw accuracy).
Emit RAN / SUBSET / TRUNCATED / MISSING per stage. **Any TRUNCATED or MISSING on a mandated stage BLOCKS
the "final" label** — mirrors the monthly AUDITOR (N/N PASS or BLOCKED at source). Re-run this §7 audit as
the last step of every weekly build; a book is "final" only when §7 returns all RAN/PRESENT.

---

## 8. FINAL METHODOLOGY — the locked combined book (added 2026-08-16)

The unified driver (`weekly/unified/`, §7-audit-clean) produced the locked book. The methodology as
finally practiced, where it AMENDS the sections above:

### 8.1 Decision gate (amends §3.3)
**Drift is REMOVED as a gate (operator 2026-08-16).** The deployable rule is the trailing eff-n
**Wilson-LB > 0.50, n ≥ 12** accuracy gate on the convergence stream. Rationale: the sleeves are
drift-capture by construction; the book's job is capturing that drift with loss-limiting structure,
and edge-over-drift belongs to the *alpha* question (where the faithful answer was ABSTAIN), not to
the *book-construction* question. The LB>0.50 gate still earns ~+2pp CAGR and +0.3 Sortino vs ungated.
Component sleeves are NOT required to beat SPX on a calendar basis — that comparison is reserved for
the combined book (operator ruling).

### 8.2 Book construction (new; the structural layer that carries the performance)
1. Sleeves from the §6 pipeline (SPY H=2, QQQ H=2). Sleeves with negative/coin OOS quality are
   DROPPED (Gold: 50.8% gated-acc, Sortino −0.20).
2. **Sortino-weight** the surviving risk sleeves (by OOS sleeve Sortino) on the risk block.
3. **Pure-hedge leg, always-on, never throttled: 20% 2Y Treasury** (duration sweep monotone
   2Y>5Y>10Y>30Y; 20% = peak Sortino). Sortino-first ruling: never cut the hedge for CAGR — lever.
4. **Dual exogenous throttle** on risk sleeves only: ×0.5 at VIX trailing-pctl ≥0.70, ×0.5 again at
   Credit_BAA10Y ≥0.70. **Own-error (MIRROR-style) book throttles are REJECTED** — measured cost
   Sortino 1.10→1.00; only exogenous-stress conditioning helps (1.10→2.03).
5. **Leverage to the operator's DD cap** (10% → 1.232×), financing disclosed as unmodeled.
6. **Micro-sleeve overlays** (w≈0.05) admitted ONLY via §8.3.
Result: coverage 51.8% (risk) → **100%** (with hedge); Sortino 2.42; MaxDD −9.9% @ 1.232×. Full spec
+ the three lock-time caveats (decade concentration; gold watch-cell; all-long family):
`unified/LOCKED_BOOK_SPEC_20260816.md`.

### 8.3 Micro-sleeve admission (new; generalizes SILVER_MICRO_SLEEVE_20260816.md)
Frozen template — **N=8, H=4, episodic hold-and-extend, no persistence-carry, no sweeping** — and
four mandatory gates: **G1** acc≥65% · n≥30 · Wilson-LB≥0.55; **G2** concentration ≥3 yrs, max-year
≤45%; **G3** |corr to book| <0.30 on active weeks; **G4** +5% overlay must not reduce book Sortino.
Survivors are PROVISIONAL until the forward tape confirms. Validation run 2026-08-16
(`unified/micro_screen.py`, pre-declared 11-cell grid): 1 survivor = the silver control, 10/11 fail —
the gate set discriminates. Standing observations: the VIX/IP_Nowcast fear-bid mechanism exists
across the metal complex but only silver clears G1 (gold/platinum = exposure-timing, watch-only);
the family is 100% long — first SHORT emission = review, don't follow.

### 8.4 Reporting (amends §3)
Always report firing AND calendar bases; always report sub-period splits (the locked book is
2007–16 +0.3% / 2017–26 +17.1% — a named caveat, not a footnote); always disclose search size on any
screen; leverage/financing flagged wherever quoted.

### 8.5 Structural overlays + the ZION-universe combination (added 2026-08-16, Amendment 1)
- **Gold 7.5% always-on** (Amendment 1): structural PP inflation leg, NO signal claim — admitted on
  corr/book-Sortino criteria only. Measured law: always-on ballast beats stress-timed exposure
  (stress-only added nothing — the throttle+micro already own those windows). Amended weekly book:
  Sortino 2.56, CAGR 11.80% @1.220×, MaxDD −9.9%.
- **Cross-cadence combination** (`ZION_UNIVERSE_BOOK_20260816.md`): weekly × monthly SYZYGY at a
  deliberate naive 50/50 (zero DOF). Corr +0.20 → **Sortino 4.13, MaxDD −3.9%, 95% years positive,
  positive through 2008 AND 2022**; the monthly leg fills the weekly leg's burn-in decade
  (cross-cadence decorrelation is temporal, not just cross-sectional). Before shared capital:
  per-instrument NETTING across cadences (SYZYGY mandate) + the universe book on the forward
  as-issued tape.

### 8.6 Amendment 2 — persistence + stress-exit (added 2026-08-17)
Risk-sleeve positions **persist** from each gated decision until the next (abstain = hold) and
**flatten while the dual throttle is stressed** (thr < 1.0). Gate results: pure persistence REJECTS
(Sortino 1.89, h2 −0.67 — drift-carry into every crash); persistence+stress-exit **ADOPTED**
(2.37 → **2.82** @cap, CAGR 12.91%, both halves ≥ 0, lev re-solved 1.190×). Universe under Amendment 2:
**Sortino 4.71, CAGR 9.60%, MaxDD −4.0%**. The pair of verdicts is the doctrine: drift-carry needs an
EXOGENOUS exit; the book's own P&L is never the exit (own-error rules reject everywhere they're tested).
Same-day REJECTS (pre-declared): Ag/Au spread (always-on and micro-window), dynamic sizing V1–V3;
live-vs-ZION disagreement study (7 clean wks): ZION won directions 7–3 — live's edge was sizing, and
its transferable form is exactly this amendment. Tape: Amendment 2 governs from the next issue; prior
rows stand as-issued.

### 8.7 Amendment 3 — recovery-window leverage schedule (added 2026-08-17)
Leverage completes the world-state symmetry: **flat in stress (A2) · 1.190× calm · 2.0× (house cap)
for 4 weeks after a recovery event** (dual throttle's first calm week after ≥2 stressed weeks —
same exogenous machinery, no own-P&L input, no new data). Basis: the book's own forward-4wk return
after recovery events = +2.32% mean / 74% positive (n=23) vs +0.80% unconditional. Gates: Sortino@cap
2.82 → **3.17** (G1 ✓), DD unchanged (G2 ✓), halves +0.02/+0.49 (G3 ✓), events split 12/11 — trigger
NOT decade-concentrated. **Universe under A3: Sortino 5.20, CAGR 10.82%, MaxDD −4.0%.** Caveats:
n=23, tail-carried (median window +0.49%), PROVISIONAL on the tape. The completed doctrine: every
sizing decision in the book — exit, base, max — is keyed to the WORLD's state; the book's own P&L
is never an input. The tape emission carries `lev`/`recovery` fields; a live recovery event is
flagged by the Friday job automatically.


### 8.8 Amendment 4 — universe leverage 2.54× · universe gross cap 3.5× (added 2026-08-17)
Operator ruling: the universe book runs at **2.54×** (spends the 10% MaxDD budget exactly) and the
2.0× house gross cap — a live-5-asset-book convention — is superseded for the universe book by a
**3.5× universe cap** (levered netted gross peaks 3.49×, mean 1.21×; peaks are brief and live in the
A3 recovery windows; clipping them rejected as incoherent). **FINAL UNIVERSE: CAGR 28.66% (honest
~27% after financing), Sortino 5.20, MaxDD −10.0%, worst yr −5.8%, 2008 +8.5% / 2022 +22.3%.**
Tape stays 1×-structural (capital P&L = 2.54 × tape return; `L_universe` field on emissions).
Beyond-history events scale by 2.54; 12 resolved tape weeks before capital — leverage last of all.


### 8.9 Amendment 5 + A4 revision — dollar sleeve in-book, 3.80×, 15.7% budget (2026-08-17)
Tracked config = +19.3% structural UUP · 3.80× · cap 6.0× → backtest 45.6%/Sortino 5.89/−15.7%.
Supersedes the same-day 2.54×/10% ruling and the sleeve's paper path (adopted ahead of forward
evidence, operator authority, in-sample discovery flagged). Tape stays 1×-structural (USD bucket via
UUP); capital P&L = 3.80×. Real capital: November review unchanged.

### 8.10 Amendment 6 — India composite in-book, 2.5% hard ceiling (2026-08-17)
NIFTY-USD (Nifty/USDINR, INDA/EPI) at 2.5% universe-structural: both-up gauntlet pass (46.62%/5.96,
halves +/+); 5%+ fails on the 2008 USD-tail — 2.5% is a ceiling, not a starting point. Promoted from
paper same-day (flag recorded). Tape: INDIA bucket, resolved via the composite.

### 8.11 CUTOVER (2026-08-17) — ZION live, AEGIS shadow
Operator executes the ZION desk ticket from today; executed lev 2.5× (staged), model tape 3.80×;
November review = scale-up decision. AEGIS untouched → shadow automatically. Fills-vs-ticket log =
live record. Supersession #3 recorded.

### 8.12 Leverage ladder (2026-08-17) — 2.5→3.2 (~wk 6, clean) →4.0 (~wk 12 review, clean)
Gates = operational fidelity (fills/resolutions/caps/DD pro-rata), never performance. At 4.0×:
MaxDD ≈−16.5% accepted, cap →6.5×, model tape →4.0×. ZION_LEV in run_universe.sh is the dial.

# CYCLOPS — Final Monthly Recipe

**The authoritative, consolidated recipe for the monthly asset-prediction pipeline.**
Distilled 2026-08-10 from the working `RECIPE.md`. The recipe is **enforced code**, not prose —
`lib_pipeline.py` + an in-driver auditor. Thirteen steps, run in full and in order for every asset.
This doc is the index; **the code is the source of truth** (`lib_pipeline.py`, `recipe_check.py`).

> **Comfort verdict — yes, as a disciplined, honest framework.** Comfortable deploying it to discover,
> certify, and onboard asset classes and to emit monthly calls. It harvests **beta + rare orthogonal
> edges**, defaults to **ABSTAIN**, and is **paper-track forward** — *not* a proven alpha engine, and the
> recipe is honest about that. The caveats at the bottom are known and bounded, not blockers.

---

## Standing integrity constraints (non-negotiable)

- **No truncation.** Every asset runs every step, in order. A skipped step overturns verdicts
  (silver "abstain"→"64.8%"; gold 2-type→27-type). An ABSTAIN or a "looks done" is a red flag to
  re-check, never a stopping point. If a step is genuinely N/A, say so with the reason.
  **Probe/sandbox runs are not exempt** (USD probe 2026-08-10): a probe either runs the full
  `run_asset` or labels its output PARTIAL — no verdict may be quoted from a partial run.
- **Honest numbers.** Calendar annualization, never row-count. Backtest is labelled as backtest; the
  as-issued tapes are the only forward evidence. No test-set tuning — k's/thresholds fixed on TRAIN.
- **The machine certifies, not the builder.** No hand-picked cells. A coded gauntlet + validation gate
  admits signals. Single certified cells are traded; the multi-round cascade is fragile and is **not**.
- **Emission validity.** Cells use only data knowable at the 1st of the month. Revision-contaminated
  inputs (IndProd, TOTALSA, IPG*) are hard-excluded; publication-lagged inputs pass a carry-forward test.
- **Book-changing actions need explicit operator go** (freezes, live wiring, weight changes).

---

## The pipeline — 13 steps

Tiers: **[AUTO]** run & auditor-enforced by `run_asset` (skip → blocked verdict) · **[EXAM]**
examination scripts, run once per asset · **[ADOPT]** per-asset wiring that changes live state (operator go).

| Step | Stage | Tier | Pass criterion |
|---|---|---|---|
| 0 · 0b | Data-admission audit + lag-scan | AUTO | no in-window splice/dup/zero; new merges peak at lag 0 |
| 1 | RED DAWN 27-type recursive discovery | AUTO | ternary triple Δ(A),Δ(B),Δ(zA−zB)→27 types; rounds to vaLB-floor (first-breach) |
| 1c–1g | Tier · IS→OOS funnel · lifecycle | AUTO | wf-OOS as selection stat; every zero attributable |
| 1i | Liquidity regime (INTERSTELLAR, 3-mode) | AUTO | regime labeled; degenerate-split flagged |
| 1v | Valuation-composite family | AUTO | runs even on cascade-empty |
| 1t | Emission-validity audit | AUTO | carry-forward overlap ≥ .60 & LB > gate & n ≥ 8 |
| 2s · 2 · 3 | Analogue sweep · ODYSSEY · SANCTUARY (voice) | EXAM | conditional lift, not standalone accuracy |
| 5 · 5b | DECISION gate · STANDDOWN | AUTO | Wilson-LB > gate else ABSTAIN; recent-24 fired ≥ 50% |
| 6 | MIRROR (drift-guard + hedge leg) | AUTO | beats always-long; hedge TRAIN-frozen / TEST-verified |
| 1s | Regime-stress diagnostic | COND | fires on Δ(train−test) > 20 pts (STRONG: test ≤ .35 inversion; WEAK: Δ>20, test > .35); rescued cells re-certify within-regime |
| GAUNTLET | Single-cell certification → freeze json | ADOPT | admit (floor) + emission-valid + DECISION-LB > gate (.45 macro / .40 analogue) |
| 1e · 1h | As-issued runner + resolver · letter · refit | ADOPT | complete ticket, conflict→abstain; tape emits & resolves PIT |
| 11 · 11b | SYZYGY netting + weight caps · DD-cap 6% | AUTO | book == tape; NETTED exposure, 2.0× cap on net |
| 12 | Terminal USD overlay (SPY+Gold anchor) | CODED | `−k·(spy_dir+gold_dir)·DXY`, k TRAIN-calibrated; per-month ledger |
| 13 | Re-calibration band (4-horizon ladder) | CODED | band tightens to resolution; weekly becomes prediction in final week |
| A | In-driver auditor (all invariants) | AUTO | N/N PASS or verdict BLOCKED at the source |

---

## The book — four assets

| Asset | Weight | Basis |
|---|---|---|
| SPY | 48% | CAPE anchor (drift-beta; kept — coverage stabilizes the book) |
| Gold | 23% | CAPE-T26 + AGR |
| Silver | 17% | 2-cell (Palladium\|MXN + Copper/WTI-ratio\|TS) · paper-track |
| Brent | 12% | orthogonal energy · weight-capped |

**Book (calendar):** CAGR **3.92%** · Sortino **1.24** · MaxDD **−5.7%** · fire-months 11.58% / 3.53.

- **Platinum** — certified but book-redundant (precious-correlated) → held **watch-only**, not traded.
- **NatGas** — stale signal → **dropped**. Both were trading coin-flip tier signals at ~1%; removing
  them sharpened fire-month Sortino (3.15→3.53).
- Monthly CYCLOPS is **one of three frequency books** (daily · weekly · monthly), sharing capital —
  not the entire firm book.

---

## Step 12 — terminal USD overlay

`overlay = −k · (spy_dir + gold_dir) · DXY_return`. The SPY+Gold anchor ladder {−2..+2} sets a
symmetric USD tilt — net-long risk → short USD; net-short → long USD; 2× when both agree, 1× single,
none when offsetting. **k TRAIN-calibrated (0.3)**, never tuned to test. NOT a hedge (adds risk-on beta);
a declared macro tilt that trims USD drag. Per-month `USD_tilt` written to `book_net_exposure.csv`.

## Step 13 — re-calibration band (4-horizon ladder)

The monthly call sets the **side** of a directional confidence band; the band is re-estimated across
the month as fresher signals arrive, and in the final week the weekly system **becomes** the prediction.
Band width tightens toward resolution. PIT / append-only (`recalibration_tape.csv` + dashboard).

| Horizon | Source | Status |
|---|---|---|
| 4 wk | Monthly CYCLOPS certified call | WIRED |
| 3 wk | GREEKWATCH rolling 21-day (daily system) | **SHADOW-INGESTING** — board call + Bayes + daily state recorded per re-run (SPY + Gold covered); never moves the point. Promotes to DRIVE the slot after ≥12 resolved 21d calls w/ Wilson-LB > 0.50 |
| 2 wk | Updated band (carry-forward) | WIRED |
| 1 wk | Weekly (AEGIS) **becomes** the prediction | WIRED — falls back to band if weekly silent/stale |

Honest freshness: a re-run only moves the point if a fresher source fired; weekly silent → carries the
band (no fabricated hand-off).

---

## Onboarding a new asset class

**Turnkey:** discovery → certification is one call — `run_asset(name, col, start_year, extra_vars)`.
Every gate is invariant-enforced; truncation is blocked at the source.

**Still hands-on:** (1) data onboarding — get the asset + candidate drivers into the panel / `*_extra.csv`
(the real lift); (2) the `[EXAM]` steps are run-once scripts (`exam_asset.py <asset>`); (3) the `[ADOPT]`
wiring (`*_certified_signal`, runner, tape, resolver, launchd, `final_portfolio` branch, refit) is cloned
from the Gold/Silver/Brent pattern; (4) orthogonality + marginal-Sortino admission; (5) weight cap if high-vol.

Expect **ABSTAIN** as the honest default — most assets won't certify a real edge. Of six run, only Brent
earned an orthogonal seat; Platinum certified-but-redundant; NatGas stale. That is the recipe working.

---

## Honest caveats & open items

- **Mostly beta, not alpha.** SPY's ~71% is long-drift capture, not timing skill (skill over drift ≈ +0.8 pts).
  The book harvests beta + a few orthogonal certified cells; it is not a high-alpha machine.
- **Paper-track forward.** Headline metrics are backtest. The as-issued tapes are thin (weeks) and are the
  only genuine out-of-sample evidence. Silver/Gold certifications are near-gate and short-history.
- **[EXAM] semi-manual.** ODYSSEY / SANCTUARY / analogue-sweep are frozen-pattern scripts, not yet folded
  into the invariant-enforced driver.
- **Two external unblocks for Step 13.** GREEKWATCH must emit a 21-day directional forecast (3wk slot);
  AEGIS's weekly signal tape is stale at 2026-07-31 (HAL guard flattening it) — fix before the 1wk hand-off fires.
- **One data-robustness TODO.** Fetch ALFRED vintage M2 to verify (or downgrade) Gold's CAPE-T26 — its
  only soft-contaminated input.

---
*Authoritative source: `lib_pipeline.py` + `RECIPE.md` · GitHub ZoltarLabs108/CYCLOPS*

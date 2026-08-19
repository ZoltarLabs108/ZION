# ZION — Shadow / Forward Test Register  (as of 2026-08-18)

Every forward-gated test currently running, what it tests, the code change it would unlock,
its evidence gate, current state, and the earliest date a verdict can arrive. Nothing here
changes live code until its gate is met AND the operator authorizes.

Forward tracking clock: first as-issued forward week resolves **2026-08-21**; the standard
12-week gate therefore first completes **~2026-11-06** (the single "November review").

---

## A. ZION-core forward tests (built/verified this session)

| # | Test | What it tests | Code change it unlocks | Gate | Now | Verdict ETA |
|---|------|---------------|------------------------|------|-----|-------------|
| 1 | **ZION vs LIVE comparator** (`zion_vs_live.py`, job step 5/8) | Does the ZION universe book beat the live AEGIS book, week by week, live-side scored AS-EXECUTED | Keep ZION as the executed book vs revert / re-weight | 12 resolved weeks | **1/12** (ZION +0.02% vs LIVE −0.61%, ZION 1-0) | **~2026-11-06** |
| 2 | **Forward Sortino reconcile** (`forward_sortino.py`, step 6/8) | The real forward universe Sortino, to feed L_max = 0.9×Sortino | Confirm/deny each leverage-ladder rung | 12 weeks (Sortino needs a sample) | **1/12** (holding haircut 3.9 → 3.5×) | **~2026-11-06** |
| 3 | **Leverage ladder** (`run_universe.sh` ZION_LEV) | Whether forward evidence earns 2.5×→3.2×→4.0× | Raise ZION_LEV / UNIVERSE_LEV | 6 clean wks → 3.2×; 12 wks + fwd Sortino ≥4.44 → 4.0× | **2.5×, wk 1** | 3.2× **~2026-09-25**; 4.0× **~2026-11-06** |
| 4 | **Paper Monday-close exit** (`paper_monclose.py`, step 4/8) | Does exiting the live book at Monday close beat holding to the next mid-week print | Add a Monday-close exit rule to execution | 12 FORWARD resolved prints | **1 forward** (backfill 5, rule 4-1) | **~2026-11** (weekly prints) |
| 5 | **ZION_SANDBOX variants** (`sandbox_forward.py`, scheduled task Tue 07:05) | Do AEGIS-style axes — window(A), feature-union(B), horizon(C), thin-tier filter(D-supp50) — beat the lean SPY sleeve OOS | Adopt a variant into the SPY cascade | 12 forward weeks, beat baseline WF-LB + forward | **1 row** (08-14, all abstain) | **~2026-11-06** |
| 6 | **Silver micro resize C1** (spec candidate) | 7.5% vs live 5% silver micro on book Sortino | `W_MICRO` 0.05 → 0.075 | 12 forward weeks with silver micro ACTIVE | silver currently OFF | ⚠ **~3.2 YEARS** at 7.2% firing — underpowered on a 12-ACTIVE-week gate; needs a relaxed gate or judge on fewer active weeks |
| 7 | **Equity de-concentration C2** (`paper_deconcentration.py`, job step 5/9) | Split SPY/QQQ by inverse-vol (not Sortino) so higher-vol QQQ can't silently carry ~67% of book risk — the DEFENSIBLE kernel of the correlation-hedge idea (full mean-variance/return-target version REJECTED as error-maximization) | Change the equity risk-block split to inverse-vol | 12 forward weeks, de-conc Sortino ≥ actual, DD not worse | **0/12** (backfill: 1.598→1.639 Sortino, DD-neutral) | **~2026-11-06** |
| 8 | **AEGIS Tuesday-baseline cadence** (operational) | Tue 01:15 print + Wed catch-up guard fire reliably; no double-print | n/a (cadence already live) — revert if flaky | ~3-4 clean weekly cycles | verified once (08-18 manual) | watch Wed "catch-up SKIPPED" log through Sept |

## B. Adjacent ecosystem trackers (from memory — verify separately before acting)

| Test | What it tests | Gate / ETA | Notes |
|------|---------------|-----------|-------|
| **FED_WATCH walk-forward** (`com.zoltar.fedwatch.wf.track`, daily) | fed_funds & M2-accel 3M cells hold OOS | first row **2026-11-01** | → HAL wiring if it holds; two 3M cells cleared IS |
| **GREEKWATCH voter / STANDDOWN monitor** | SPY 3rd-lens vote; abstain-when-hit-rate-drops | paper/forward, read-only | regime-lab paper studies |
| **NOVA IPO/lockup** (`com.zoltar.nova`) | SPCX unlock fade | unlock 08-06 → 10-06 | tracking-first |
| **Daily family** (5-asset 06:00 runner) | daily tape | 0/90 reset | costs unmodeled |
| **HELIOS gold daily** | shadow-live gold daily | since 07-17 | CONCORDANCE context only |

---

## Key observations
- **Six of the seven ZION tests converge on ~2026-11-06** — by design, that is the single evidence
  review point (12 forward weeks). Expect to make several decisions at once then.
- **The leverage ladder is the one with an earlier waypoint**: 3.2× around 2026-09-25 (6 clean weeks),
  contingent on the forward tape staying clean and the Sortino tracker not deteriorating.
- **The silver resize (C1) is the outlier** — its "12 active weeks" gate is ~3 years at silver's 7%
  firing rate. **Operator decision 2026-08-18: LEAVE for the November batch** — do not relax the gate
  now; revisit the active-week question as part of the ~Nov 6 review alongside everything else.
- **Legacy paper tracks retired**: UUP and India were paper-tracked pre-live; both are now in the live
  book, so `paper_uup_*` / `paper_india_*` columns are historical, not active tests.

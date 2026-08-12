# PHASE: RECAL — RECIPE STEP 13 (re-calibration band, 4-horizon ladder)
Tier:    AUTO
Worktree: ZION_RECAL   Branch: recal-dev
Owns:    the seam where the vertical (frequency) axis collapses to one emitted number

## CONTRACT (the handoff)
IN   ← SYZYGY:    the monthly netted call (direction + book weight) = the 4wk anchor.
     ← MIMESIS:   the latest weekly AEGIS call (becomes the prediction in the final week).
     ← GreekWatch: the rolling 21-day board call + Bayes (daily system), as a SHADOW input.
OUT  → emit:      a horizon-laddered prediction whose band TIGHTENS toward resolution, PIT-taped.
GATE :  a faster-cadence input may only *narrow the band*; it may only *flip the direction* after
        it earns promotion (see below). Weekly silent → fall back to the band (no fabricated hand-off).

## ACTIONS  (the 4-horizon ladder — recalibrate.py)
1. **4wk — monthly CYCLOPS** issues the anchor (direction + band).
2. **3wk — GreekWatch 21-day** (`greekwatch_shadow()`): once the month is ~1 week in, the 21-day
   horizon lands on month-end, so it feeds this slot. TODAY: **SHADOW-tracked** — recorded beside
   the band on every re-run, **never moves the point** (`note='SHADOW-tracked — carries band until
   record earns it'`). Coverage: SPY→SPY, Gold→GLD only (GW_MAP); Silver/Brent have no board yet.
3. **2wk — updated band** narrows as data arrives.
4. **1wk — weekly AEGIS** call *BECOMES* the prediction in the final week; direction sets the side.

## DIAGNOSTICS
- pass criterion: band monotonically tightens toward resolution; direction consistent or explicitly
  re-stated with reason; PIT tape append-only (schema v2 adds `gw_*` shadow columns).
- emitted: `recalibration_tape.csv` (PIT, append-only), `recalibration_state.csv`,
  `recalibration_dashboard.html`.
- failure mode → weekly silent = fall back to the band (never fabricate a hand-off); GreekWatch
  missing/unmapped asset = 3wk slot carries the band unchanged.

## GreekWatch promotion rule (the "changes the prediction based on backtest" mechanism)
Promote GreekWatch-21d to **DRIVE** the 3wk slot once its shadow record accumulates **≥12 RESOLVED
non-overlapping 21-day calls per asset with Wilson-LB > 0.50**; then weight by its Bayes. Until then
it fills the record only. This is the standing shadow→promote pattern for every faster-cadence input
(same posture as FED_WATCH — [[fedwatch-walkforward]], [[greekwatch-tail-verdict-system]]).
**Status today: nothing promoted — GreekWatch is a band-narrowing / conviction input, NOT yet a
direction-changer.** Treating the 21d call as a decider now would jump the gate.

## CADENCE  (this phase IS the frequency seam)
- MONTHLY : issues the 4wk anchor.
- WEEKLY  : owns the 2wk band + the 1wk becomes-prediction step.
- DAILY   : ingests the GreekWatch 21d board call (shadow) + daily board state between captures.

## PROVENANCE  (verified in code, 2026-08-12 — recalibrate.py)
- `greekwatch_shadow()` lines 95–125; ladder point-selection lines 179–182 (keeps point=carry,
  tags SHADOW); promotion rule lines 99–102; GW_MAP line 93 (SPY/Gold only).
- Consistent with RECIPE STEP 13 row: "4wk monthly → 3wk GREEKWATCH rolling-21d (SHADOW-INGESTING)
  → 2wk band → 1wk weekly BECOMES prediction; band tightens; GW promotes to DRIVE 3wk after ≥12
  resolved 21d calls w/ Wilson-LB>0.50."

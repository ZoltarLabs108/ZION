# PHASE: MIRROR — RECIPE STEP 6 (drift-guard + hedge leg)
Tier:    AUTO
Worktree: ZION_MIRROR   Branch: mirror-dev
Owns:    ZION validation (reflection / self-consistency); the drift guard + hedge leg

## CONTRACT (the handoff)
IN   ← DECISION: the direction call {dir, conviction}.
OUT  → GAUNTLET: a drift-checked call + a hedge leg (TRAIN-frozen / TEST-verified, else report-only).
                 Frozen as `stage_STEP6_mirror`.
GATE :  the call must BEAT always-long (drift baseline). Hedge leg TRAIN-frozen; if it can't be
        verified on TEST, it stays report-only (never live off unverified hedge).

## ACTIONS  (in order)
1. **Drift guard** — compare the call to an always-long benchmark; a call that doesn't beat drift
   is flagged (most "edge" in this ecosystem is drift-capture — this is the honesty gate).
2. **Hedge leg** — build the loss-limiting hedge (e.g. gold/10Y satellite in STRESS), TRAIN-frozen.
3. **Verify hedge on TEST** — if verified, attach; else mark report-only.

## DIAGNOSTICS
- pass criterion: beats always-long; hedge leg TRAIN-frozen & TEST-verified to go live.
- emitted: `stage_STEP6_mirror`, drift-vs-call comparison, hedge verification result.
- failure mode → doesn't beat drift → the call is drift-capture, labelled as such (not alpha).

## CADENCE
- MONTHLY : F — drift-guard + hedge.
- WEEKLY  : s — hedge leg re-check.
- DAILY   : N/A — mirror operates on the monthly call.

## PROVENANCE / PRIOR ART
- ZION_PROGRAM_MAP marks MIRROR as validation (tentative — confirm). The ecosystem's repeated
  verdict is drift-capture: [[gold-weekly-recipe-verdict]] (+0.0 skill = pure drift-capture),
  [[spy-anchor-drift-not-skill]], [[walkforward-verdict]] (no cell beats buy-hold; Gold p=.011).
  MIRROR is where that honesty is ENFORCED per call. Hedge discipline: [[hermes-liquidity-crisis-hedge]].

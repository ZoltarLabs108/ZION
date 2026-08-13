# PHASE: REGIME — RECIPE STEP 1s (regime-stress diagnostic)
Tier:    COND   (fires conditionally; report-only, never sizes)
Worktree: ZION_REGIME   Branch: regime-dev
Owns:    the within-regime rescue-or-discard conduit + TRANSITIONAL ALERT

## CONTRACT (the handoff)
IN   ← the train/test accuracy split of a cell (from RED DAWN / DECISION).
OUT  → DECISION (conditional): either a within-regime rescued cell (re-certified) or a confirmed
       discard, plus a per-asset TRANSITIONAL ALERT for the dashboard. Frozen as
       `stage_STEP1s_regime_monitor` / `<asset>_regime_stress.json`.
GATE :  trigger = Δ(train − test) > 20 pts. STRONG form: test ≤ .35 (sign-flip/inversion).
        WEAK form: Δ>20 with test > .35 (regime-drift suspicion) — same conduit, tiered evidence bar.
        Rescued cells RE-CERTIFY within-regime (no gauntlet back door).

## ACTIONS  (in order)
1. Detect the trigger — Δ(train−test) > 20 pts on the cell's accuracy.
2. Classify STRONG (test ≤ .35) vs WEAK (test > .35).
3. Re-test on an OBSERVABLE regime axis (5 PIT axes; GENERAL signature {REALRATE, LIQ, USD}).
4. Rescue a regime-conditional cell OR confirm-discard; rescued cells re-certify within-regime.
5. Emit TRANSITIONAL ALERT — regime axes NOW vs 3 bars ago (PIT); CLEAR/WATCH/TRANSITION, upgraded
   to SIGNATURE MATCH when changed axes cover the asset's historical flip-fold signature.

## DIAGNOSTICS
- pass criterion: rescued cell must clear the within-regime certification (not the full gauntlet).
- emitted: `<asset>_regime_stress.json`, transition-alert state, fold-flip signature.
- failure mode → cannot rescue → confirm-discard (report the reason); never force-keep.

## CADENCE
- MONTHLY : F — Δ>20 stress test + within-regime re-test.
- WEEKLY  : s — transition-alert refresh.
- DAILY   : F — daily transition-state read (axes NOW vs 3 bars ago).

## PROVENANCE / PRIOR ART
- [[step1s-regime-transition-system]] (Δ>20pt trigger, 5 PIT axes, fold-flip signatures, TRANSITIONAL
  ALERT; GENERAL sig {REALRATE, LIQ, USD}; report-only, re-certify within-regime),
  [[artemis-pit-placebo-findings]] (catastrophic cell MOVED = fragile flip estimator, not per-model
  bug — regime-stress is the right lens, not per-cell patching).

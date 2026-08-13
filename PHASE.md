# PHASE: INTERSTELLAR — RECIPE STEP 1i (liquidity regime)
Tier:    AUTO
Worktree: ZION_INTERSTELLAR   Branch: interstellar-dev
Owns:    ZION gate-before-8 (act/abstain conditioning) — liquidity/regime-stress + throttle

## CONTRACT (the handoff)
IN   ← RED DAWN: the cascade signal + the liquidity/stress series.
OUT  → DECISION: a 3-mode liquidity regime label + a throttle multiplier (report-only; NEVER
                 sizes positions). Frozen as `stage_STEP1i_liquidity_regime`.
GATE :  regime labeled; degenerate-split flagged. Throttle is a conditioning gate, not a sizer.

## ACTIONS  (in order)
1. Compute the INTERSTELLAR liquidity-stress composite (v3.2 thresholds).
2. Classify into 3 modes (e.g. CALM / CAUTION / STRESS); rekey CAUTION to Liq_Throttle==0.0.
3. Emit throttle multiplier (0.5x suggested in TRANSITION/STRESS) — report-only on the dashboard.
4. Flag degenerate splits (a mode with too few obs to condition on).

## DIAGNOSTICS
- pass criterion: every month labeled; no degenerate mode used as a gate silently.
- emitted: `stage_STEP1i_liquidity_regime`, regime timeline, throttle log.
- failure mode → degenerate split → WARN + do not condition (fall back to unconditional).

## CADENCE
- MONTHLY : F — 3-mode regime label.
- WEEKLY  : F — weekly liquidity read (faster signal is legitimate here).
- DAILY   : F — daily stress state feeds the throttle / STANDDOWN dashboard.

## PROVENANCE / PRIOR ART
- [[interstellar-liquidity-integration]] (v3.2 stress thresholds → SELENE spine; throttle NEVER
  sizes; CAUTION rekeyed to Liq_Throttle==0.0), [[hermes-liquidity-crisis-hedge]] (gold's edge is
  loss-limiting in STRESS, not directional — liquidity is the conditioning lever). Validated as
  report-only throttle: forward 8/11 & 10/11 folds, ex-GFC robust ([[step1s-regime-transition-system]]).

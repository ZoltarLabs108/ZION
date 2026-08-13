# PHASE: DECISION — RECIPE STEP 5 · 5b (decision gate + STANDDOWN)
Tier:    AUTO
Worktree: ZION_DECISION   Branch: decision-dev
Owns:    ZION calc-5d/9 (emit/decision) — the convergence gate; the re-convergence point

## CONTRACT (the handoff)
IN   ← RED DAWN cascade ∩ SANCTUARY analogue (k≥n convergence) + ODYSSEY waveform voice +
       INTERSTELLAR liquidity gate + VALUATION family + EMISSION-valid cells + (cond) REGIME.
OUT  → MIRROR: a direction call {dir, conviction, tier} OR **ABSTAIN**. Frozen as `stage_STEP5_decision`.
GATE :  Wilson-LB > GATE else ABSTAIN. STANDDOWN if recent-24-fired ≥ 50% has decayed.
        ABSTAIN is the default — act only on OOS-proven convergence.

## ACTIONS  (in order)
1. **Convergence** — require k≥n engine agreement (RED DAWN ∩ SANCTUARY; ODYSSEY as a voice-lift
   vote, not a caller). Voices only *raise/confirm* conviction; they don't fire alone.
2. **DECISION gate** — Wilson-LB > GATE on the convergence accuracy (test slice); else ABSTAIN.
3. **5b STANDDOWN** — abstain when the sleeve's recent-24 fired hit-rate drops (N=20 / ≤35%).
4. Apply liquidity conditioning (INTERSTELLAR) and label-population check.

## DIAGNOSTICS
- pass criterion: Wilson-LB > GATE; label-population check passes (DECISION_P label defect guard).
- emitted: `stage_STEP5_decision`, `stage_STEP5b_standdown`, convergence table, fired/abstain log.
- failure mode → below gate → ABSTAIN (a dark board is NOT trouble; it is the honest default).

## CADENCE
- MONTHLY : F — convergence gate → call / ABSTAIN.
- WEEKLY  : F — weekly AEGIS call (feeds RECAL's 1wk becomes-prediction step).
- DAILY   : s — GreekWatch board direction, SHADOW until promoted (see RECAL).

## PROVENANCE / PRIOR ART
- [[convergence-abstention-methodology]] (abstain by default, act only on OOS-proven edge,
  convergence = edge), [[decision-p-label-defect]] (standing guard LABEL_POPULATION_CHECK.py),
  [[zion-stage4-convergence-spy]] (first real WF convergence — honest verdict was DRIFT-CAPTURE,
  edge +1.1pp, placebo failed p=.058: keep the gate HONEST, don't overclaim convergence edge),
  [[regime-lab-paper-studies]] (STANDDOWN_MONITOR N=20/≤35%), [[ticket-desktop-alert]]
  (match the severity WORD, not the "diverg" substring).

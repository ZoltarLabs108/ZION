# PHASE: GAUNTLET — single-cell certification
Tier:    ADOPT   (changes live state — explicit operator go)
Worktree: ZION_GAUNTLET   Branch: gauntlet-dev
Owns:    the machine-certifies-not-the-builder gate — single certified cells are what get traded

## CONTRACT (the handoff)
IN   ← EMISSION-valid cells + DECISION-standalone LB + (MIRROR drift-check).
OUT  → MIMESIS / SYZYGY: a frozen `<asset>_certified_signal.json`. Only certified single cells go live.
GATE :  admit (per-asset floor) + 1t emission-valid + DECISION-standalone LB > class gate.
        Class gates: macro .45 / analogue .40 (+ CERT_MARGIN). NO hand-picked cells.

## ACTIONS  (in order)
1. Admit the cell at the per-asset VA floor (default .50; short-history e.g. Silver .45).
2. Confirm 1t emission-validity (carry-forward pass).
3. Require DECISION-standalone Wilson-LB > class gate + CERT_MARGIN (macro .45 / analogue .40).
4. Freeze the certified single-cell signal to JSON (immutable).

## DIAGNOSTICS
- pass criterion: all three gates clear on a SINGLE cell (the multi-round cascade is fragile and is
  NOT traded — only single certified cells are).
- emitted: `<asset>_certified_signal.json` (frozen), certification log.
- failure mode → no cell clears → asset stays uncertified (ABSTAIN); never lower the gate to admit.

## CADENCE
- MONTHLY : F — single-cell certification on monthly evidence.
- WEEKLY  : N/A — certify on monthly evidence only (weekly is too thin to certify a live cell).
- DAILY   : N/A.

## PROVENANCE / PRIOR ART
- FINAL_MONTHLY_RECIPE: "The machine certifies, not the builder. No hand-picked cells. Single
  certified cells are traded; the multi-round cascade is fragile and is NOT."
  [[tier-retention-convergence-verdict]] (PLATINUM = real candidate edge → paper-track),
  [[gate0a-calibration-and-pt-leaveoneout]] (Gate 0a coarse-gate reform ≥90 obs/cell),
  [[full-algo-language-convention]] / [[audit-first-build-convention]] (no truncation into the gate).

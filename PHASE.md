# PHASE: VALUATION — RECIPE STEP 1v (valuation-composite family)
Tier:    AUTO
Worktree: ZION_VALUATION   Branch: valuation-dev
Owns:    the valuation-composite family — runs EVEN ON cascade-empty

## CONTRACT (the handoff)
IN   ← HYPERION panel (+ RED DAWN cascade status).
OUT  → DECISION: valuation-composite family signals (CAPE + valuation ladder). Frozen as
                 `stage_STEP1v_valuation_family`.
GATE :  runs even when RED DAWN cascade is empty (this is its point — an always-available family).

## ACTIONS  (in order)
1. Assemble the valuation composite (CAPE + related valuation series), recency-guarded.
2. Build the composite family signals (levels + changes + z-scores).
3. Emit family — available to DECISION regardless of cascade outcome.

## DIAGNOSTICS
- pass criterion: family emitted every month; CAPE input passes recency check (no stale ie_data).
- emitted: `stage_STEP1v_valuation_family`, CAPE recency stamp.
- failure mode → stale/misnamed valuation file → BLOCK with reason (do not compute on stale CAPE).

## CADENCE
- MONTHLY : F — composite family.
- WEEKLY  : s — CAPE/valuation is slow-moving; light refresh only.
- DAILY   : N/A — valuation is monthly-grained.

## PROVENANCE / PRIOR ART
- [[shiller-stale-ie-data-no-recency-check]] (2026-08-06: misnamed 2024 ie_data contaminated the
  monthly analog, CAPE 35.1 vs correct 40.12 — MUST recency-guard + real download here).
  [[spy-anchor-drift-not-skill]] (CAPE kept because COVERAGE stabilizes the book, not skill —
  do not oversell valuation as directional edge).

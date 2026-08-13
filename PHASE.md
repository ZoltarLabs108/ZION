# PHASE: HYPERION — features / panel assembly
Tier:    AUTO
Worktree: ZION_HYPERION   Branch: hyperion-dev   (pre-existing)
Owns:    ZION calc-2 (features)

## CONTRACT (the handoff)
IN   ← AUDIT: the admitted panel (`audit_pass.flag` == PASS).
OUT  → RED DAWN: the assembled feature/panel matrix — outcome column + all drivers + DERIVED_VARS
                 (ratios, either-direction, theory-gated), each PIT-lagged; the target (calc-3)
                 and cell-encoding scaffold (calc-4, ORACLE lookup) ride here.
GATE :  every derived series lag-scan peak at lag 0; drivers present per ASSET_VARS clause-(e).

## ACTIONS  (in order)
1. Register the universe — ASSET_VARS + DERIVED_VARS; fetch + lag-scan any new series.
2. Assemble the monthly panel — align all drivers to the outcome's month-first index.
3. Build the target (calc-3) — 1-month forward direction, ±dead-zone.
4. Cell-encode scaffold (calc-4 / ORACLE) — predictor lookup / rich map for RED DAWN to fit in.

## DIAGNOSTICS
- pass criterion: no misaligned merges (all peak at lag 0); panel row basis = signal tape.
- emitted: feature matrix, DERIVED_VARS manifest, lag-scan table, target column.
- failure mode → a driver that won't lag-scan to 0 is excluded with reason (never force-merged).

## CADENCE
- MONTHLY : F — panel assembly.
- WEEKLY  : s — refresh only the series that moved.
- DAILY   : N/A — the panel is monthly-grained (no daily feature build).

## PROVENANCE / PRIOR ART
- ZION_PROGRAM_MAP marks HYPERION as calc-2 (tentative — confirm). [[athena-odyssey-asof-port]]
  (merge_asof backward, row basis = signal tape). Keep PIT lagging strict; ORACLE encoding kept,
  full-history in-sample fit REPLACED by walk-forward folds downstream.

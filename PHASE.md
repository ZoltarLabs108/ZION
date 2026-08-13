# PHASE: EMISSION — RECIPE STEP 1t (emission-validity audit)
Tier:    AUTO
Worktree: ZION_EMISSION   Branch: emission-dev
Owns:    the PIT emission-validity gate — cells may use only data knowable at the 1st of the month

## CONTRACT (the handoff)
IN   ← candidate cells (from RED DAWN cascade / valuation family).
OUT  → GAUNTLET / DECISION: the emission-VALID subset of cells. Frozen as `stage_STEP1t_emission`.
GATE :  carry-forward overlap ≥ .60 AND LB > GATE AND n ≥ 8.

## ACTIONS  (in order)
1. Hard-exclude revision-contaminated inputs (IndProd, TOTALSA, IPG* — revised after the fact).
2. Carry-forward test on publication-lagged inputs — the last-known value at month-1st must
   overlap the fitted value ≥ .60 of the time.
3. Re-check LB > GATE and n ≥ 8 on the emission-valid basis (a cell that only passes on revised
   data is dropped).

## DIAGNOSTICS
- pass criterion: carry-forward overlap ≥ .60 & LB > gate & n ≥ 8.
- emitted: `stage_STEP1t_emission`, per-cell overlap + excluded-input log.
- failure mode → cell fails emission validity → excluded (cannot be certified or emitted).

## CADENCE
- MONTHLY : F — full carry-forward validity audit.
- WEEKLY  : s — re-check newly-published inputs.
- DAILY   : N/A — emission basis is the 1st-of-month.

## PROVENANCE / PRIOR ART
- [[janus-emission-basis-and-resolver]] (horizon = 1 month-first span on FIRST print; CARRY_FORWARD),
  [[monthly-as-issued-freeze]] (predictions frozen at issue; never backfill from reprints),
  [[tape-revision-corrupts-asissued]] (weekly tapes silently revise; nothing WF-testable from them).

# PHASE: AUDIT — RECIPE STEP 0 · 0b (data admission)
Tier:    AUTO   (stage 0 of every build — spine hard-gated on this)
Worktree: ZION_AUDIT   Branch: audit-dev
Owns:    ZION calc-1 (audit); backs stage0_audit/ (audit.py, audit_pass.flag)

## CONTRACT (the handoff)
IN   ← (raw): the outcome series' FULL history + all merged driver series.
OUT  → HYPERION: `audit_pass.flag` (PASS/BLOCK) + the admitted panel. No downstream phase runs
                 until this flag is PASS — a blocked audit BLOCKS the verdict at the source.
GATE :  no in-window splice / dup date / zero / non-monotonic; new merges peak |corr| at lag 0.

## ACTIONS  (in order)
1. **Row-level audit of the outcome's full history** — zeros / duplicate dates / non-monotonic
   index = HARD BLOCK.
2. **Basis-splice discriminator** — |monthly move| > 60% AND complete 24-mo range separation =
   vendor splice → BLOCK if inside the build window. A mean-reverting spike only WARNS (natgas
   must not false-block).
3. **Lag-scan (0b)** — every newly-merged driver's peak |corr| must sit at lag 0 (no look-ahead
   alignment).

## DIAGNOSTICS
- pass criterion: PASS flag written only when all checks clear; else BLOCK with the offending rows.
- emitted: `audit_pass.flag`, audit report (blocked rows + reasons), lag-scan table.
- failure mode → BLOCK (never WARN-through). Caught the ag-complex vendor splice
  (wheat/corn +136/+113% @2000-07, soy +194% @2000-09) that would otherwise contaminate discovery.

## CADENCE
- MONTHLY : F — full-history admission audit before every build.
- WEEKLY  : s — freshness/splice re-check on new rows only.
- DAILY   : s — stale-row guard (HAL: stale sleeve row → NO_SIGNAL + reason).

## PROVENANCE / PRIOR ART
- [[audit-first-build-convention]] (stage 0 = row-level audit, spine gated on audit_pass.flag),
  [[aegis-hal-freshness-guard]], [[ag-complex-panel-splice]], [[shiller-stale-ie-data-no-recency-check]]
  (add a recency guard on downloaded inputs).

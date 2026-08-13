# AUDITOR — RECIPE STEP A (cross-cutting invariant gate)
Tier:    AUTO   (wraps every AUTO phase; not a standalone worktree — lives here in COMBINED)

## ROLE
The in-driver auditor wraps each AUTO phase's OUT and checks its invariants BEFORE the handoff is
allowed. It is the enforcement that makes "no truncation" real: a phase that skips a step or emits a
malformed OUT does not silently pass — the verdict is BLOCKED at the source.

## CONTRACT
IN   ← every AUTO phase's emitted OUT + its declared invariants.
OUT  → the next phase, ONLY if N/N invariants PASS; else `verdict = BLOCKED` with the failing check.
GATE :  N/N PASS or BLOCKED. No partial pass.

## INVARIANTS (per phase — the auditor knows each phase's `stage_STEP*` contract)
- AUDIT: audit_pass.flag == PASS; no in-window splice/dup/zero.
- HYPERION: all merges lag-scan peak at 0.
- RED DAWN: cascade rounds terminate at floor; every funnel zero attributable.
- EMISSION: carry-forward ≥ .60 & LB > gate & n ≥ 8.
- DECISION: Wilson-LB > GATE or ABSTAIN; label-population check passes.
- GAUNTLET: single-cell, three gates cleared, frozen JSON immutable.
- SYZYGY: book == tape; net ledger balances.
- (every phase): OUT is frozen; no TEST-tuned threshold; calendar annualization.

## THE TRUNCATION CHECK (standing lesson)
Any run that produces a number someone might cite must show ALL its steps in its log/artifacts.
An ABSTAIN or a "looks done" is a RED FLAG to re-check for a skipped step, never a stopping point.
Probe/sandbox runs are NOT exempt — a probe either runs the full phase chain or its output is
labelled **PARTIAL — no verdict may be quoted from it**.

## PROVENANCE
- RECIPE STEP A (`_audited`, recipe_check.py). [[full-algo-language-convention]],
  [[audit-first-build-convention]]. This is the reason the recipe is CODE, not prose —
  "prose can't enforce itself."

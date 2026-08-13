# PHASE: MIMESIS — RECIPE STEP 1e · 1h (as-issued runner + resolver + letter + refit)
Tier:    ADOPT   (changes live state — explicit operator go)
Worktree: ZION_MIMESIS   Branch: mimesis-dev
Owns:    ZION calc-8 (freeze + live runner + resolve) — the as-issued ledger, the ONLY real OOS

## CONTRACT (the handoff)
IN   ← GAUNTLET: the frozen `<asset>_certified_signal.json`.
OUT  → SYZYGY: a complete as-issued ticket (dir / conv / size / hedge / context) frozen at issue,
              + the resolved ledger (scored next month, never revised). This tape is the ground truth.
GATE :  ticket complete; conflict → ABSTAIN; freshness guard (stale row → NO_SIGNAL + reason).
        Predictions frozen at issue (Phase-5 nightly); never backfilled from reprints.

## ACTIONS  (in order)
1. **As-issued runner** — emit the complete monthly ticket from the certified signal; freeze it.
2. **Freshness guard** — a stale sleeve tape row → NO_SIGNAL + reason (do not trade a stale row;
   Friday preflight legitimately trades last-Friday's row — holiday guard = SPY-bar check).
3. **Resolver** — score the prior month's frozen prediction; append to the ledger PIT.
4. **Letter / sizing / refit (1h)** — forecast block (conviction_mult; CASSANDRA magnitude);
   refit_runner over FINISHED_ASSETS + re-cert; the letter LEADS with book status.

## DIAGNOSTICS
- pass criterion: tape emits AND resolves; ticket complete; conflict resolves to ABSTAIN.
- emitted: as-issued tape row (frozen), resolved ledger row, monthly letter.
- failure mode → conflict / stale → ABSTAIN / NO_SIGNAL (loud sleeve failure, never silent).

## CADENCE
- MONTHLY : F — as-issued ticket + resolve.
- WEEKLY  : F — weekly tape emit/resolve (but weekly tapes silently REVISE — not WF-testable;
             the monthly as-issued freeze is the honest forward record).
- DAILY   : s — daily freshness stamp (HAL).

## PROVENANCE / PRIOR ART
- [[zion-live-record-conventions]], [[monthly-as-issued-freeze]] (as-issued 51.8% vs reprint ~65%;
  never backfill), [[tape-revision-corrupts-asissued]] (43% of traded signals changed, 39% sign-
  flipped — weekly tapes not WF-testable), [[aegis-hal-freshness-guard]], [[friday-preflight-spec]],
  [[red-dawn-pit-verdict]] (the live tape is the only evidence). MIMESIS = forward-OOS ground truth.

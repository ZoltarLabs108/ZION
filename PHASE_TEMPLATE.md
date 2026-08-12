# PHASE CONTRACT — template

> Every phase worktree carries ONE `PHASE.md` in this shape. A phase is a clean unit:
> it declares what it CONSUMES, what it DOES, how it PROVES itself, and the single frozen
> artifact it PASSES FORWARD as the first input of the next phase. No phase may quote a
> number from a truncated run (RECIPE standing lesson — see COMBINED/REGISTRY.md).

```
# PHASE: <NAME> — RECIPE STEP <n>
Tier:    [AUTO | EXAM | ADOPT]
Worktree: ZION_<NAME>   Branch: <name>-dev
Owns:    <ZION stage/calc it implements>

## CONTRACT (the handoff)
IN   ← <prior phase>:  <exact artifact(s) consumed, path/schema>
OUT  → <next phase> :  <exact frozen artifact(s) produced — this is the FIRST input of next>
GATE :  <the pass criterion that must hold for OUT to be valid; else BLOCKED/ABSTAIN>

## ACTIONS  (what it does, in order — no step skippable)
1. ...

## DIAGNOSTICS  (how it proves itself)
- pass criterion: ...
- emitted diagnostic artifacts: ...
- failure mode → what it does (BLOCK / WARN / ABSTAIN / rescue)

## CADENCE  (this function × frequency — the vertical axis)
- MONTHLY : <behavior at monthly cadence>
- WEEKLY  : <behavior at weekly cadence, or "N/A — reason">
- DAILY   : <behavior at daily cadence, or "N/A — reason">

## PROVENANCE / PRIOR ART  (what X and CYCLOPS did; what is new; known verdicts)
- ...
```

## Rules every contract obeys
1. **No truncation.** All ACTIONS run in full, in order. An ABSTAIN or "looks done" is a
   red flag to re-check for a skipped step, never a stopping point. Genuinely-N/A steps say
   so with a reason.
2. **The machine certifies, not the builder.** OUT is admitted by a coded GATE, not hand-pick.
3. **Honest numbers.** Calendar annualization; backtest labelled as backtest; the as-issued
   tape is the only forward evidence; k's/thresholds fixed on TRAIN, never on TEST.
4. **OUT is frozen.** Once a phase emits OUT it is immutable for that period; the next phase
   reads it, never recomputes it.

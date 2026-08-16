# ZION WEEKLY — UNIFIED DRIVER — BUILD SCOPE
### 2026-08-14. The one driver that runs every §6 stage dutifully and passes its own §7 audit.

## 0. Why this exists
The §7 audit found the "final" weekly book was built by a SHORTCUT (`zion_weekly.py`: H hardcoded,
predictor-agreement instead of 3-lens, no edge-over-drift gate). The full-fidelity pieces all EXIST
but are scattered across ~39 scripts and two unreconciled worktrees. This scope unifies them into
ONE driver so "final" means something. **Honest prior (from the recipe itself): the faithful result
is likely ABSTAIN-heavy — possibly LESS than the shortcut's 8%. That is the point; a true ABSTAIN is
a valid, valuable deliverable.**

## 1. Canonical-lineage decision (resolve the two worktrees FIRST)
- `weekly-oos-dev` (ZION_WEEKLY_WT): SPY+Gold clean path — the honest book per [[zion-weekly-build]].
- `weekly-wti-dev` (ZION_WEEKLY_WTI): multi-asset (adds Silver/WTI/10Y/Platinum) — **all of which ABSTAIN
  or fail clean PIT-OOS** (silver empty outside 2025; platinum worst-of-all 47% OOS; WTI/10Y excluded).
- **Decision: canonical = the SPY+Gold clean lineage; the WTI multi-asset assets enter only as
  abstain-confirmations.** Merge into a single new branch `weekly-unified-dev`; archive the other two.

## 2. Architecture — one driver, `weekly/zion_weekly_unified.py`
Per-asset walk (each stage = a called function from the EXISTING weekly modules, frozen-copied per §0
quarantine — NOT imported from monthly):

```
for asset in ASSETS:
    panel = build_panel(asset)                 # PIT-lagged + dollar-spliced
    assert stage0_audit(panel).passed          # HARD gate → audit_pass.flag
    H     = horizon_sweep(panel, asset)         # {1,2,3,4,6,8,13}, freeze on edge-pull yield
    cells = grammar27_cascade(panel, H)         # train-floor + val-winner, TEST untouched
    wf    = expanding_wf(cells, H)              # train ≤ t−H, machine-asserted
    vote  = three_lens(panel, H)                # RED DAWN + ODYSSEY + SANCTUARY, ≥2 unanimous
    call  = decision(wf, vote, edge_over_drift) # edge gate, not raw acc → dir or ABSTAIN
    call  = overlays(call, MIRROR, INTERSTELLAR, CASSANDRA)
    led   = ledger_net_of_cost(call)            # 5bps, non-overlapping H-blocks
    audit7(asset, stages)                        # §7 self-audit → RAN/SUBSET/TRUNCATED/MISSING
book = syzygy_combine(sleeves)                   # equal-weight, abstain-as-HOLD (persistence convention)
```

## 3. Reuse map (write the orchestration, not the physics)
| stage | reuse from | status |
|---|---|---|
| build_panel (PIT-lag, dollar splice) | `zion_driver.py` (pit_lag INDPRO/TCU/CPI+2mo, M2+1mo; DTWEXM splice) | REUSE |
| Stage-0 audit | `weekly_pipeline_spy.py` (audit_pass) | REUSE |
| **Horizon sweep** | `type_analysis.py` (H_GRID {1,2,3,4,6,8,13}, drift-free edge Wilson-LB) | **REUSE (was skipped)** |
| grammar27 + cascade + ÷4.348 eff-n | `zion_weekly.py::stream()` / `weekly_tier_cascade.py` | REUSE |
| expanding WF (train≤t−H) | `stream()` sequential loop | REUSE |
| **3-lens RD/ODYSSEY/SANCTUARY** | `weekly_reddawn_spy.py`, `weekly_pipeline_spy.py`, `weekly_full_spy.py` | **REUSE (was substituted)** |
| **edge-over-drift gate** | `type_analysis.py`, `zion_decision3.py` | **REUSE (was raw acc)** |
| MIRROR / INTERSTELLAR / CASSANDRA | `zion_weekly.py` | REUSE |
| net-of-cost ledger (5bps) | `zion_spy_final.py`, `zion_decision3.py` | REUSE |
| SYZYGY combine + abstain-as-hold | `syzygy_weekly.py` + `persistence_test.py` | REUSE + rewire |
| **§7 self-audit** | (none — WRITE) | **NEW** |

**Net new code = ~2 files:** the `zion_weekly_unified.py` orchestrator + `audit7.py` (the machine
truncation-checker). Everything else is wiring existing, tested functions in the mandated order.

## 4. Build order (each phase gated by its own §7 audit — house rule)
1. **Skeleton + §7 auditor.** Orchestrator calls stages as stubs; `audit7.py` asserts each ran in THIS
   driver and wrote a non-empty artifact. Prove the audit BLOCKS on a deliberately-skipped stage.
2. **SPY end-to-end** (the one asset with a hybrid edge). Real horizon sweep (expect H≈3 but let it
   choose), 3-lens convergence, edge-over-drift gate. §7 must return all RAN. Compare the faithful SPY
   result to the shortcut — expect it to shrink.
3. **Gold end-to-end** (the quality sleeve). Same. §7 clean.
4. **Abstainers as confirmations** (Silver/WTI/10Y/Platinum): run the same driver; expect ABSTAIN, and
   let §7 confirm the abstain came from a full run, not a truncated one.
5. **SYZYGY book** = SPY+Gold sleeves, abstain-as-HOLD, net-of-cost, both-bases monthly reporting.
   Reconcile against the shortcut book; the delta IS the cost of the truncations.
6. **Retire** `zion_weekly.py` (shortcut) and the losing worktree; tag `final_book_weekly_ledger.csv`
   as superseded.

## 5. Honest expectations & risks
- **Expect the faithful book < shortcut 8%.** The horizon sweep + edge-over-drift gate + 3-lens will
  admit FEWER weeks than firing-acc×coverage did. A drop is the truncations being paid back, not a bug.
- **SPY likely stays drift-capture** (recipe §4 prior); the honest deliverable may be "SPY = beta, Gold =
  the only quality sleeve, everything else ABSTAIN." That is a complete, valuable answer.
- **Risk: frozen-copy drift** (§0) — the weekly primitives are copies; document versions.
- **PP sleeve stays OUT** of weekly (monthly overlay, Sortino-neutral) until it earns in monthly first.

## 6. Definition of done
`zion_weekly_unified.py` produces `reports/final_book_weekly_unified_ledger.csv` AND an `audit7` table
returning **all RAN/PRESENT** across every §6 stage, in that same driver, with no swept parameter
hardcoded. Only then is the weekly book labelled **final**. Effort estimate: ~2 new files + wiring;
the hard part is reconciliation and honest acceptance of a smaller number, not new physics.

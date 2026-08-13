# ZION PHASE REGISTRY — the horizontal axis (function), worktree per RECIPE step

Each row is a phase worktree off the ZION repo (`git worktree list`). The chain is the
handoff order: every phase's **OUT** is the next phase's first **IN**. Two worktrees already
existed (`hyperion-dev`, `reddawn-dev`) — this registry extends that pattern to the full
RECIPE. Basis: `~/Desktop/ASSET_PIPELINE/FINAL_MONTHLY_RECIPE.md` (13-step canonical) +
`ZION/spec/ZION_PROGRAM_MAP.md` (calc map).

Status: ✅ built (contract written) · ✅ planned (worktree pending fan-out) · 🟢 pre-existing worktree

| # | RECIPE step | Phase / worktree | Branch | Tier | IN ← | OUT → (first input of next) | Status |
|---|---|---|---|---|---|---|---|
| 1 | 0·0b | **AUDIT** / ZION_AUDIT | audit-dev | AUTO | raw asset+driver panel | `audit_pass.flag` + admitted panel | ✅ (backs stage0_audit/) |
| 2 | calc-2 features | **HYPERION** / ZION_HYPERION | hyperion-dev | AUTO | admitted panel | feature/panel matrix | ✅ (worktree pre-existed) |
| 3 | 1 · 1c–1g | **RED DAWN** / ZION_RED_DAWN | reddawn-dev | AUTO | feature matrix | 27-type cascade + tier + IS→OOS funnel | ✅ (worktree pre-existed) |
| 4 | 1i | **INTERSTELLAR** / ZION_INTERSTELLAR | interstellar-dev | AUTO | cascade + liquidity series | 3-mode regime label + throttle (never sizes) | ✅ |
| 5 | 1v | **VALUATION** / ZION_VALUATION | valuation-dev | AUTO | panel | valuation-composite family signals | ✅ |
| 6 | 1t | **EMISSION** / ZION_EMISSION | emission-dev | AUTO | candidate cells | emission-valid cells (carry-forward ≥.60, LB>gate, n≥8) | ✅ |
| 7a | 2 | **ODYSSEY** / ZION_ODYSSEY | odyssey-dev | EXAM | certified RD signal + price waveform | waveform voice-lift verdict (+ new: composite-waveform quality score) | ✅ |
| 7b | 2s · 3 | **SANCTUARY** / ZION_SANCTUARY | sanctuary-dev | EXAM | certified RD signal + return panel | analogue voice verdict + swept window + (new) broadened catch | ✅ |
| 8 | 5 · 5b | **DECISION** / ZION_DECISION | decision-dev | AUTO | RD∩SANCTUARY convergence + ODYSSEY voice + liquidity gate | direction call or ABSTAIN (Wilson-LB>gate) + STANDDOWN | ✅ |
| 9 | 1s | **REGIME** / ZION_REGIME | regime-dev | COND | train/test acc split | transition alert / within-regime rescue-or-discard | ✅ |
| 10 | 6 | **MIRROR** / ZION_MIRROR | mirror-dev | AUTO | decision | drift-checked call + hedge leg (TRAIN-frozen) | ✅ |
| 11 | GAUNTLET | **GAUNTLET** / ZION_GAUNTLET | gauntlet-dev | ADOPT | emission-valid + decision-LB | frozen `<asset>_certified_signal.json` | ✅ |
| 12 | 1e · 1h | **MIMESIS** / ZION_MIMESIS | mimesis-dev | ADOPT | certified signal | as-issued ticket + resolved ledger (the ONLY real OOS) | ✅ |
| 13 | 11·11b·12 | **SYZYGY** / ZION_SYZYGY | syzygy-dev | AUTO | per-asset certified signals | netted book + DD-cap 6% + USD overlay | ✅ |
| 14 | 13 | **RECAL** / ZION_RECAL | recal-dev | AUTO | monthly call + weekly + GreekWatch 21d | horizon-laddered prediction (band tightens to resolution) | ✅ |
| — | A | **AUDITOR** (cross-cutting) | in COMBINED | AUTO | every phase's invariants | N/N PASS or verdict BLOCKED at source | ✅ (lib) |

## The chain (handoff order)
```
AUDIT → HYPERION → RED_DAWN ─┬─ INTERSTELLAR ─┐
                             ├─ VALUATION ─────┤
                             ├─ EMISSION ──────┤
                             ├─ ODYSSEY ───────┼→ DECISION → MIRROR → GAUNTLET → MIMESIS → SYZYGY → RECAL → emit
                             └─ SANCTUARY ─────┘        ↑REGIME (cond rescue)
AUDITOR wraps every AUTO phase (invariant gate; skip → BLOCKED verdict).
```
RED DAWN fans out to the conditioning/voice phases (INTERSTELLAR, VALUATION, EMISSION,
ODYSSEY, SANCTUARY) which run independently and re-converge at DECISION. ODYSSEY & SANCTUARY
are **secondary voices** — their value is *at DECISION*, never as a standalone caller.

## Combine rule
`ZION_COMBINED` (combined-dev) is the integration branch: it holds this registry, the
frequency×function MATRIX, the AUDITOR lib, and the orchestration driver that walks the chain,
enforcing that each phase reads only the prior phase's frozen OUT.

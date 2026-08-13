# FREQUENCY × FUNCTION MATRIX — the vertical axis on top of the horizontal

The system is computed **vertically by frequency** (monthly / weekly / daily) and
**horizontally by function** (the phases in REGISTRY.md). You already have the cadence-native
base: MONTHLY = full 13-step CYCLOPS, WEEKLY = RECIPE-study subset, DAILY = GreekWatch/board
actions. This matrix adds **each phase, by cadence** — every cell says what that phase does at
that cadence, or `N/A — reason` (never silently blank; RECIPE no-truncation rule).

Legend: **F**=full run · **s**=subset/lighter · **shadow**=records, does not drive · **N/A**=with reason

| Phase (function) → cadence ↓ | MONTHLY (4wk, CYCLOPS) | WEEKLY (RECIPE-study) | DAILY (GreekWatch/board) |
|---|---|---|---|
| AUDIT | F — full-history admission audit | s — freshness/splice re-check on new rows | s — stale-row → NO_SIGNAL guard |
| HYPERION | F — panel assembly | s — refresh moved series | N/A — panel is monthly-grained |
| RED DAWN | F — 27-type recursive discovery | s — re-score on frozen tiers (no re-discovery) | N/A — discovery is monthly |
| INTERSTELLAR | F — 3-mode regime label | F — weekly liquidity read (faster) | F — daily stress state feeds throttle |
| VALUATION | F — composite family | s — CAPE/valuation slow-moving | N/A — valuation is monthly-grained |
| EMISSION | F — carry-forward validity | s — re-check newly-published inputs | N/A |
| **ODYSSEY** | F — waveform voice + composite-quality score | s — waveform re-read on weekly bars | shadow — daily bin-state recorded |
| **SANCTUARY** | F — analogue voice (broadened catch) | s — analogue re-rank | N/A — analogue horizon ≥ monthly |
| DECISION | F — convergence gate → call/ABSTAIN | F — weekly AEGIS call | s — board direction (shadow until promoted) |
| REGIME | F — Δ(train−test)>20 stress test | s — transition-alert refresh | F — daily transition-state read |
| MIRROR | F — drift-guard + hedge | s — hedge leg re-check | N/A |
| GAUNTLET | F — single-cell certification | N/A — certify on monthly evidence only | N/A |
| MIMESIS | F — as-issued ticket + resolve | F — weekly tape emit/resolve | s — daily freshness stamp |
| SYZYGY | F — netted book + DD-cap + USD | F — weekly book update | s — daily net exposure mark |
| **RECAL** | issues the 4wk anchor | 2wk band + 1wk **becomes** prediction | 3wk **GreekWatch 21d** (shadow → promote) |

## How the two axes compose
- **Horizontal (function):** a call walks AUDIT→…→RECAL once per period; each phase reads the
  prior phase's frozen OUT (REGISTRY handoff chain).
- **Vertical (frequency):** the SAME phase runs at up to three cadences. The RECAL row is the
  seam where the vertical axis collapses back to one number: the **4wk monthly anchor** is
  progressively narrowed by the **3wk GreekWatch 21-day** shadow, the **2wk** band, and in the
  final week the **1wk weekly** call *becomes* the prediction (see ZION_RECAL/PHASE.md).
- **Not every cell is live.** DAILY has far fewer full cells than MONTHLY — that is honest to
  what each cadence can support, not an omission. Empty-looking = `N/A — reason`, always stated.

## Cross-cadence promotion (the only way a faster cadence changes a slower call)
A daily/weekly input may **drive** a monthly call only after its own forward record earns it:
e.g. GreekWatch-21d promotes to DRIVE the 3wk slot after ≥12 resolved non-overlapping calls
per asset with Wilson-LB > 0.50. Until then it is `shadow` — recorded beside the band, never
moving the point. This is the standing rule for every faster-cadence input.

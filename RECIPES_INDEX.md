# ZION RECIPES INDEX — all cadences, one honest map (2026-08-17)

| cadence | recipe | status | notes |
|---|---|---|---|
| **WEEKLY** | `weekly/ZION_WEEKLY_RECIPE.md` | **CURRENT** — §1–6 spec, §7 implementation audit, §8 final methodology incl. Amendment 1 (7.5% gold) + Amendment 2 (persistence + stress-exit) | The locked book spec: `weekly/unified/LOCKED_BOOK_SPEC_20260816.md`. Universe: `weekly/unified/ZION_UNIVERSE_BOOK_20260816.md` |
| **MONTHLY** | canonical: `~/Desktop/ASSET_PIPELINE/FINAL_MONTHLY_RECIPE.md` (13-step); frozen snapshot: `monthly/FINAL_MONTHLY_RECIPE_snapshot_20260817.md`; ZION-rebuild spec: `spec/ZION_RECIPE.md` + `spec/ZION_PROGRAM_MAP.md` | **CURRENT w/ addendum below** | ZION monthly = the clean-OOS rebuild (`multiasset_pipeline.py`): Gold/Silver/WTI/USD + **NatGas (added 2026-08-17, WATCH-ONLY — OOS 58.8%, LB .478 < .50, not in SYZYGY)**. Canonical stays in ASSET_PIPELINE per the quarantine principle; the snapshot here is a dated frozen copy, never edited |
| **DAILY** | **NOT in ZION** — daily lives in the AEGIS/GREEK_WATCH ecosystem (06:00 ET family runner, GreekWatch board, HAL) | out of ZION scope by design | `MATRIX.md` daily column documents what each ZION phase means at daily cadence (mostly s/N/A). ZION consumes daily state only via the INTERSTELLAR-style throttles (VIX/credit percentiles) |

## Cross-cadence composition
`MATRIX.md` (frequency × function) + `REGISTRY.md` (phase chain) + `ZION_UNIVERSE_BOOK_20260816.md`
(weekly × monthly 50/50, corr +0.20, netting via `weekly/unified/netting_ledger.py`).

## Operational cadence (what actually runs)
- **Friday 17:30** `com.zoltar.zion.universe` (launchd): panel refresh → netting ledger + tape issue →
  resolve matured → ZION-vs-LIVE comparison. Logs: `weekly/unified/logs/`.
- Monthly pipeline + SYZYGY: run on demand (`multiasset_pipeline.py`, `syzygy_book.py`).
- Binding gates: 12 resolved tape weeks (~mid-Nov 2026) before capital decisions.

## Monthly addendum (2026-08-17)
NatGas ported through the clean-OOS machinery (`ng_monthly_port.py`): anchor = validated
Industrial/Term_Spread with pre-declared den level-shift (+10; spread crosses zero). Verdict:
**WATCH-ONLY** (LB .478 < .50 gate; positive mirror verdict; re-applies if forward record earns
LB > 0.50). Not a SYZYGY sleeve.

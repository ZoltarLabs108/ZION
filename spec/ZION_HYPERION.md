# ZION — HYPERION (data assembly + variable registry)

HYPERION is Phase 0's data engine (legacy HYACINTH_2_HYPERION / "IMPORTA v4.1").
It declares every API/source, fetches all variables, and assembles the MASTER MONTHLY CSV
that every ZION analysis step reads — the database of record. Runs downstream of SHILLER
(which builds the Shiller equity skeleton from FRED before the official workbook releases).

## OUTPUT — master panel + analysis record
- `master_panel_MMYY.csv` — one row per month (first-of-month anchor), one column per
  variable; the single input every stage consumes. Versioned by month (as-issued; never
  backfilled from later reprints).
- `analysis_record.csv` — step-by-step provenance ledger: each stage run appends (stage,
  asset, inputs-hash, params, key outputs, timestamp) so the whole analysis is reproducible
  and auditable as a database, not scattered logs.

## APIs / SOURCES
| source | access | covers | notes |
|---|---|---|---|
| FRED | API key (`~/.config/ghsys/fred_key`) | macro: rates, M2, IndProd, CPI, dollar index | PIT loaders + TED splice (BF.py); pace/retry |
| Shiller `ie_data` | workbook (ORACLE) or FRED replica (SHILLER) | SP_Price, Dividend, Earnings, CPI, CAPE | replica used before official monthly release |
| Yahoo / market | yfinance | asset settlement prices (Gold, Silver, WTI) | throttle bulk pulls; month-end value |

## THE PLAYERS — variable registry (source · API · series id · release/PIT-lag · ROLE)
FINALIZED 2026-08-12. This table is the single source of truth; `hyperion_build.py` carries
the same registry in code (`VARIABLES`) and drives fetch + lag + splice from it.

**PIT lag** = months a reference-month value must be shifted FORWARD so that, at a
**1st-of-the-month decision**, row `M` holds only what was already published. It is
strictly larger than FRED's own reference→first-publication measure, because a series whose
value for month `m` is first published *during* `m+1` (e.g. mid-month) is NOT yet knowable at
the 1st of `m+1` — so the newest usable reference month at a 1st-of-`M` decision is `M-2`, i.e.
PIT lag = 2. FRED's ALFRED-measured reference→publication lag (the `1`s in HYPERION's
`FRED_PUBLICATION_LAG_MONTHS`) is shown in the "FRED lag" column for provenance; the "PIT lag"
column is what HYPERION actually applies. Market/observable series (daily closes, daily
constituent yields read at the prior month-end) are known same-day → PIT lag 0.

### Outcomes (the five assets — next-MONTH direction is predicted)
| variable | source | API | series id | FRED lag | PIT lag | role |
|---|---|---|---|---|---|---|
| SP_Price | Shiller / market | SHILLER replica (FRED SP500 pre-workbook) or ie_data | `SP500` (mkt) / Shiller `P` | 0 | 0 | OUTCOME: S&P 500 monthly close |
| Gold_Close | market | Yahoo (LBMA retired on FRED) | `GC=F` (Yahoo); pre-1968 backfill | 0 | 0 | OUTCOME: Gold (panel from 1968) |
| Silver_Close | market | Yahoo | `SI=F` (Yahoo) | 0 | 0 | OUTCOME: Silver (panel from 2000-08 — extend pre-2000) |
| WTI_Crude_Close | FRED / market | FRED | `DCOILWTICO` (WTI Cushing spot, daily) | 0 | 0 | OUTCOME: WTI (panel from 1986) |
| Dollar_Index | FRED / market | FRED (splice) or Yahoo ICE | `DTWEXM`→`DTWEXBGS` splice, or Yahoo `DX-Y.NYB` | 0 | 0 | OUTCOME: USD (also Gold's num) — see splice note below |

### Predictor legs currently in use (leg-uniqueness: each used once)
| variable | source | API | series id | FRED lag | PIT lag | role |
|---|---|---|---|---|---|---|
| Real_Price | Shiller (CPI-real) | ie_data / SHILLER replica | derived `Real_Price` | 0 | 0 | S&P **num** (CAPE) |
| Real_Earnings | Shiller (CPI-real, 10y smooth) | ie_data / SHILLER replica | derived `Real_Earnings` | ~2 (reported-earnings lag) | 0 applied / **2 recorded** | S&P **den** (CAPE) — the CYCLE input. Lag *recorded, not applied by default* (see note) |
| Dollar_Index | FRED / market | FRED / Yahoo | as Outcome above | 0 | 0 | Gold **num** |
| M2_Money | FRED | FRED | `M2SL` (M2, SA, monthly) | 1 | **2** | Gold **den** — LAGGED (released ~4th week for prior month) |
| Industrial_Production | FRED | FRED | `INDPRO` (Ind. Prod. Index, monthly) | 1 | **2** | Silver **num** — LAGGED (released ~15th–17th for prior month) |
| GS10_Rate | FRED | FRED | `GS10` (10Y monthly avg) / daily `DGS10` | 1 (monthly avg) | 0 | Silver **den** — read as observable yield (prior month-end) |
| US_2Y_Treasury | FRED | FRED | `GS2` (2Y monthly avg) / daily `DGS2` | 1 (monthly avg) | 0 | WTI **num** — panel from 1976-06; use `DGS2` daily for the observable read |
| Fed_Funds_Rate | FRED | FRED | `FEDFUNDS` (eff. FFR monthly avg) / daily `DFF` | 1 (monthly avg) | 0 | WTI **den** — observable overnight rate |
| Gold_Close | market | Yahoo | `GC=F` | 0 | 0 | USD **num** (dollar-FREE numerator) |
| US_CPI | FRED | FRED | `CPIAUCSL` (CPI-U All Items, SA) | 1 | **2** | USD **den** + DEFLATOR (released ~10th–15th for prior month) |

Rates note: `GS10`/`GS2`/`FEDFUNDS` are FRED *monthly-average* series (published ~1st business
day of the next month). ZION reads them as **observable yields** — the prior month-end value is
knowable at a 1st-of-month decision — so PIT lag is 0. If a build ever consumes the monthly
*average* as-of the label month, switch to the daily series (`DGS10`/`DGS2`/`DFF`, prior
month-end) rather than lagging, to avoid conflating an average with a point read.

### Deflator / cycle inputs
- **US_CPI** (`CPIAUCSL`) — deflator for all real adjustments (base-recent CPI, discrete per-leg
  pre-ratio). Same series is USD's denominator. PIT lag 2 (both roles).
- **Real_Earnings / Earnings** (Shiller) — 10-year trailing real-earnings smoothing = the cycle
  behind CAPE. Reported earnings carry a real ~2-month reporting lag. This lag is **recorded in
  the registry but NOT applied by default**, because (a) it is baked into how Shiller's ie_data
  reports earnings and (b) shifting it changes the CAPE denominator timing for every historical
  S&P verdict — a modeling change requiring operator authorization. `--apply-all-lags` opts in.
  Only S&P has a defined cycle; other assets' cycles are an OPEN modeling task.

### Applied-lag set (what HYPERION bakes in by default)
`{Industrial_Production: 2, US_CPI: 2, M2_Money: 2}` — exactly the three FRED macro legs that
`stage1_pit_data/oracle_stage.py` currently lags itself (`PUB_LAG`). HYPERION baking them here
lets ORACLE (and every downstream stage) drop its private lag and inherit clean PIT data, per
the HYGIENE requirement. Mirrors HYACINTH_2_HYPERION's own opt-in discipline
(`FRED_APPLY_PUBLICATION_LAG` default OFF): master_panel is the place the shift is made once.

### Candidate pool (not yet predictors — reserved for Stage 2/3 admission)
| variable | source | series id | note | intended future purpose |
|---|---|---|---|---|
| Term_Spread_10Y_2Y | FRED | `T10Y2Y` | zero-crossing — treat as a **rate/level** (sign of the spread), NOT a ratio leg | recession/regime lens; Stage-3 rate feature & Stage-4 convergence vote |
| Copper_Close | FRED→Yahoo | `PCOPPUSDM`→`HG=F` | **HARD SPLICE 2000-08**: $/tonne (~1800) → $/lb (~0.885), ~2000× unit break. `hyperion_build` BLOCKS/quarantines until repaired | "Dr. Copper" growth proxy — Silver/WTI cross-check; admit only after unit repair |
| Natural_Gas_Close | Yahoo / FRED | `NG=F` / `DHHNGSP` | panel from 1997 | 5th-asset candidate (VULCAN leg elsewhere); Stage-3 admission |
| Sector ETFs | Yahoo | `XLK,XLF,XLE,XLV,XLI,XLY,XLP,XLU,XLRE,XLB,XLC` | monthly closes | rotation/breadth features; Stage-4 convergence lenses |
| FX pairs | FRED | `DEXUSEU,DEXUSUK,DEXJPUS,DEXCAUS,…` | daily | short-USD tilt / cross-asset conditioning (JANUS territory) |
| Liquidity / stress | FRED | `NFCI`, `STLFSI2`, `DFII5`/`DFII10` (TIPS) | weekly/daily | INTERSTELLAR throttle & TEARS satellite underlyings |

### FRED-id verification status (2026-08-12)
Verified from live ecosystem usage (ids are actively fetched in HYACINTH_2_HYPERION / BF.py):
`INDPRO, M2SL, GS10, GS2, DGS2, FEDFUNDS, DFF, CPIAUCSL, CPILFESL, DCOILWTICO, T10Y2Y,
DTWEXBGS, DTWEXM`. **Dollar_Index splice**: `DTWEXM` = Trade-Weighted Major Currencies,
Mar-1973=100, **discontinued** (last vintage ~2020) → splice to `DTWEXBGS` (Broad, Goods &
Services, Jan-2006=100) at the overlap, OR use ICE `DX-Y.NYB` (Yahoo). Panel `Dollar_Index`
begins 1973-01, consistent with a `DTWEXM`-anchored series. **Gold/Silver** LBMA FRED series
(`GOLDAMGBD228NLBM`, `SLVPRUSD`) are **retired/broken** on FRED → Yahoo `GC=F`/`SI=F`.
NOT re-verified against a live FRED call in this offline environment (release *days* below are
from domain knowledge, not an ALFRED pull today): INDPRO ~15th–17th, CPI ~10th–15th, M2 ~4th
week — all resolve to PIT lag 2 at a strict 1st-of-month decision.

## HYGIENE (HYPERION enforces at assembly — implemented in `hyperion_build.py`)
- **Publication-lag alignment per series** (PIT-lag column above). Applied on a *complete*
  monthly grid (reindex first) so `shift(lag)` is an exact month offset even across gaps.
  Shifting forward correctly drops the last `lag` reference months off the tail (not yet
  knowable) and NaNs the head. Default applied set = {IndProd, CPI, M2}=2; ORACLE can then drop
  its own `PUB_LAG`.
- **Unit-aware splice detection**: `price`/`index`/`level` units checked on |MoM %| (default
  block > 60%, warn > 40%); `rate` units checked on |MoM Δ points| (block > 5, warn > 3).
  Registry-declared HARD splices (Copper 2000-08) are seam-tested by level ratio; an unrepaired
  hard splice **quarantines** the column (excluded from master_panel, logged) rather than
  aborting the whole build.
- **Structural checks**: datetime monotonic increasing, first-of-month normalized, dedup on
  Date (keep last), internal month-gap report. NaN rule: never fabricate — carry NaN, record
  per-column coverage (first/last/n) in the analysis_record; downstream `dropna` per asset.

## OUTPUT — analysis_record.csv (provenance ledger schema)
Append-only. One row per stage ACTION. Columns:
`run_ts, run_id, stage, asset, action, inputs, inputs_hash, params, key_outputs, rows_in, rows_out, status, note`
- `run_ts` ISO8601; `run_id` = `HYPERION_<UTCstamp>` (groups all rows of one build)
- `stage` e.g. `HYPERION`; `asset` = variable/asset or `ALL`
- `action` e.g. `load_source`, `grid_reindex`, `apply_lag`, `splice_check`, `quarantine`,
  `coverage`, `write_master`
- `inputs` human list of source paths/series; `inputs_hash` = sha256[:12] of the source file(s)
- `params` compact JSON (e.g. `{"lag":2}`); `key_outputs` compact JSON (e.g.
  `{"first":"1919-01-01","last":"2026-06-01","n":1290}`)
- `rows_in`/`rows_out` ints; `status` = `OK|WARN|BLOCK|QUARANTINE`; `note` free text

## OPEN (operator)
- Confirm Silver/WTI/USD predictor ratios (yours vs proposed) — run clean lag-corrected head-to-head.
- Decide whether to APPLY the Real_Earnings ~2mo reporting lag (`--apply-all-lags`) — changes CAPE timing.
- Extend Silver history pre-2000; add Platinum data if reinstated; repair Copper 2000-08 unit splice.
- Per-asset cycle definitions (only S&P defined).
- Wire live FRED/Yahoo fetch (needs `~/.config/ghsys/fred_key` + network); default build reads the panel.

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

## THE PLAYERS — variable registry (source · release/PIT-lag · ROLE)
Release lag = months a value must be lagged at a 1st-of-month decision to be PIT-honest.

### Outcomes (the five assets — next-MONTH direction is predicted)
| variable | source | release lag | role |
|---|---|---|---|
| SP_Price | Shiller/market | 0 (market) | OUTCOME: S&P 500 |
| Gold_Close | market | 0 | OUTCOME: Gold |
| Silver_Close | market | 0 | OUTCOME: Silver (panel starts 2000-08 — extend) |
| WTI_Crude_Close | FRED DCOILWTICO/market | 0 | OUTCOME: WTI (from 1986) |
| Dollar_Index | FRED trade-weighted/DXY | 0 | OUTCOME: USD (also a predictor-leg elsewhere) |

### Predictor legs currently in use (leg-uniqueness: each used once)
| variable | source | release lag | role |
|---|---|---|---|
| Real_Price | Shiller (CPI-real) | 0 | S&P num (CAPE) |
| Real_Earnings | Shiller (CPI-real, 10y smooth) | ~2 (earnings lag) | S&P den (CAPE) — the CYCLE input |
| Dollar_Index | FRED | 0 | Gold num |
| M2_Money | FRED M2SL | ~2 (releases ~4th wk) | Gold den — LAGGED |
| Industrial_Production | FRED INDPRO | ~2 (releases ~15th) | Silver num — LAGGED, was banned; needs lag or swap |
| GS10_Rate | FRED GS10 | 0 | Silver den |
| US_2Y_Treasury | FRED GS2/DGS2 | 0 | WTI num |
| Fed_Funds_Rate | FRED FEDFUNDS | 0 | WTI den |
| Gold_Close | market | 0 | USD num (dollar-free) |
| US_CPI | FRED CPIAUCSL | ~2 (releases ~mid-month) | USD den + DEFLATOR (real adjustment) |

### Deflator / cycle inputs
- US_CPI — deflator for all real adjustments (base-recent CPI, discrete per-leg pre-ratio).
- Earnings (Shiller) — 10-year trailing smoothing = the cycle behind CAPE. Only S&P has a
  defined cycle; other assets' cycles are an OPEN modeling task.

### Candidate pool (not yet predictors — reserved for Stage 2 admission)
Term_Spread_10Y_2Y (zero-crossing — treat as rate, not ratio leg), Copper_Close (2000-08
splice — repair before use), Natural_Gas_Close, sector ETFs, FX pairs, NFCI/liquidity.
Purpose: feature admission / multi-predictor cascade (Stage 3), convergence lenses (Stage 4).

## HYGIENE (HYPERION enforces at assembly)
- Publication-lag alignment per series (the release-lag column above) — the ORACLE module
  MUST consume already-lagged LAGGED vars (IndProd/M2/CPI ~2mo). Current gap: oracle_stage.py
  does not yet lag — fix here so all stages inherit clean PIT data.
- Unit-aware splice detection (prices pct, rates points); block on hard splice (Copper).
- Datetime monotonic + first-of-month + dedup + gap check; NaN rules (coverage, drop vs
  PIT-ffill, never fabricate).

## OPEN (operator)
- Confirm Silver/WTI/USD predictor ratios (yours vs proposed) — run clean lag-corrected head-to-head.
- Exact FRED series ids for Dollar_Index, WTI, US_2Y (verify DXY vs trade-weighted; DCOILWTICO; GS2 vs DGS2).
- Extend Silver history pre-2000; add Platinum data if reinstated.
- Per-asset cycle definitions (only S&P defined).

# Sector Method — Health Care (XLV)

Status: **COMPLETE through the recipe (steps 0–17), 2026-09-13; re-verified under the corrected earnings parser (F10, §10) — all three prior sector conclusions confirmed; Health Care's anchor label amended to Price-to-Growth** — the method is established and this document is the template for
the other eight SPDR sectors.** Every step below was run on Health Care in the order given, each with its script, criterion and
result table; operator rulings are recorded in §5; every truncation of the prior board and every non-sector-specific mistake made
while building this is listed in Addendum A. The closing step is a standing dialectic with the operator, not a one-off sign-off.
This is a sector system in its own right; it is **not** the ZION S&P chain and does not inherit the S&P's horizon, anchor or gates.

Working directory: `~/Desktop/ZION/sector_volume/`. Nothing here is wired into `refresh_reports.sh`, the Friday job, the netting
ledger, the desk ticket, the tape resolver, `LOCKED_BOOK_SPEC`, or the dashboard; wiring any of them is a production change that needs
explicit authorisation. `ASSET_PIPELINE/lib_pipeline.py`, `ZION/multiasset_pipeline.py` and `gen_cassandra_prices.py` are used
unmodified (imported); sector legs are merged in-process.

**Contents**
0. Truncation review of the standing sector board · 1. Data · 2. Where sector-specific factors plug in · 3. Sector CAPE and cyclically
adjusted PEG · 4. Results (4a volume · 4b sequential harness · 4c standing-board cells · 4d CAPE/CAPEG horizon test · 4e PE/PEG lists ·
4f rotation · 4g full driver, tailored pool · 4h horizon sweep · 4i money test · 4j interim verdict · 4k relative label · 4l anchor-only
attempt · 4m relative money test · 4n forward tape · **4o Stage-1 type analysis, four anchors** · **4p Stage 3: pulls, remainder,
pre-type tier, dead-zone sensitivity** · **4q parallel instruments** · **4r integrated instrument** · **4s engines + DECISION** ·
**4t CASSANDRA** · **4u sizing** · **4v portfolio integration**) · 5. Rulings · 6. Status · 7. The procedure, steps 0–17 · Results index ·
Change log · Addendum A (truncations A1–A15, mistakes B1–B19)

---

## 0. Why this document exists — the truncation review

The standing ZION sector board (`reports_gen/gen_board_h6.py`, 9 sectors, 6-month horizon) was reviewed
against the enforced monthly recipe (`lib_pipeline.run_asset`). It never calls that driver; it calls the
cascade directly. Truncations found, in recipe order:

| # | Stage | Recipe requires | Sector board did |
|---|---|---|---|
| 1 | Stage 0 audit | row audit (zeros, stale, splices, spikes) gates the build | not run |
| 2 | Stage 1 predictors | per-asset valuation anchor + the asset's own drivers (`ASSET_VARS` rule) | nine generic macro legs, identical for every sector; no valuation, no sector drivers |
| 3 | Stage 1 exclusions | exclude only circular legs | Copper excluded for all sectors, including Materials whose driver it is |
| 4 | Publication lags | mid-month publishers lagged or discovery-only; emission audit | Industrial Production, M2, CPI used at data month; XLV's top cell (vaLB 0.909) rests on Industrial Production, a hard-contaminated leg |
| 5 | Horizon | swept then frozen | hardcoded 6 months (board) / 1 month (13 Sep sequential run) |
| 6 | Validation | non-overlapping bets, honest bound | single 50/25/25 split with overlapping 6-month labels (82 test months ≈ 14 independent bets); headline is the fitted accuracy |
| 7 | Act gate | DECISION convergence only; "do not gate on the cascade" | gates on the cascade's own bound |
| 8 | Stage 1 diagnostics | funnel, lifecycle, regime monitor, regime stress, liquidity regime, emission audit, valuation family | none run |
| 9 | Tier level | tier walk-forward + hybrid fallback | tier number computed on the standing board only; no fallback evaluated |
| 10 | Engines | ODYSSEY + SANCTUARY on the outcome's returns, convergence vote | not run |
| 11 | Stand-down | recent-fired accuracy gate | not run |
| 12 | MIRROR | drift guard: signal Sortino vs always-long; two-sided vs long-only arbitration | not run (XLV: 137 of 137 covered months long, never tested against being long) |
| 13 | Money test / sleeve / auditor | vs buy-and-hold; TRON/TEARS; in-driver invariants | not run |
| 14 | Reporting | accuracy beside drift, edge first | board JSON leads with fitted accuracy |

Root cause: the driver was bypassed, so its auditor never ran.

## 1. Data (verified 2026-09-13)

| Series | Source | History | Point-in-time treatment |
|---|---|---|---|
| XLV monthly close (outcome) | canonical panel `US_Healthcare_Close` (row M-01 = first-trading-day close of month M) | 1998-12 → | as-is |
| XLV, SPY daily price/volume | Yahoo | 1998-12 → | volume summed by calendar month, shifted one month |
| XLV distributions | Yahoo | 1999-12 → | trailing-12m sum through prior month |
| Medical-care CPI (CPIMEDSL), headline CPI (CPIAUCSL) | FRED | 1947 → | +2 months |
| Health-care employment (CES6562000001) | FRED | 1990 → | +2 months |
| Pharmaceutical PPI (PCU325412325412) | FRED | 1981 → | +2 months |
| Constituent fundamentals (PE, fwd PE, PEG, cap) | Yahoo quote snapshot | today only | **not a history — peer-basket medians only, never a backtest input** |
| Constituent earnings and shares | SEC XBRL companyfacts, 59 current XLV names (User-Agent authorised by operator) | FY2007 → (10-Ks carry prior years) | as-issued value = earliest filing per fiscal-year end; usable from **filing date** |
| Panel per-stock CAPEs (UNH, JNJ, ABBV, PFE, LLY, MRK) | panel | — | **rejected**: built on ~3 years of EPS, not a CAPE |
| S&P sector operating EPS workbook | S&P DJI | — | download blocked (HTML returned); not used |

Generic macro legs retained from the panel: Dollar Index, M2 (+1), Industrial Production (+2), 10-year,
Fed funds, 2-year, WTI, gold, 10s–2s spread; CPI +2 inside the deflator.

## 2. Sector-specific factors — where they plug in

- **Predictor pool**: `extra_vars` at load / `ASSET_VARS` registry → enters the 27-type grammar and recursive cascade as a pair partner. Primary integration point.
- **Transform registries**: ratios and z-scores → `STATIONARY` (never CPI-deflated); first-of-month series → `TIMELY_VARS` (emission-eligible). Mid-month publishers lagged.
- **Publication lags**: applied in the sector wrapper before load (`PIT_LAG` = IndProd 2, M2 1, CPI 2; FRED legs per table above).
- **Valuation anchor**: the sector's own CAPE (section 3), replacing the S&P's CAPE which was never sector-tailored.
- **Engines** (ODYSSEY, SANCTUARY): run on XLV's own returns; nothing sector-specific needed, they simply must be called.
- **MIRROR hedge set**: gold, 10-year, dollar, SPY; SPY is the natural sector beta hedge.

Declared Health Care leg set: `XLV_DivYield`, `XLV_RelSPY`, `XLV_CAPE10`, `XLV_CAPE5`, `XLV_CAPEG`, `XLV_CAPE5G`,
`MedCPI_Rel`, `HC_Employment`, `Pharma_PPI`. Dropped: `UnitedHealth_CAPE` (§1, not a CAPE); `XLV_Vol_Log`, `XLV_Vol_Rel` (§4a, coverage not skill).

## 3. Sector CAPE and cyclically adjusted PEG (built 2026-09-13, definitions fixed before results)

`hc_cape.py` → `results/hc_cape_monthly.csv`, `results/hc_cape_companies.csv`.

- Universe: the 59 current XLV constituents (survivorship: current members only — stated, not fixed).
- Earnings: annual net income (`NetIncomeLoss`, fallback `ProfitLoss`), ~1-year 10-K durations, as-issued, usable from filing date; real = deflated by CPI at fiscal-year end. Negative years kept (Shiller convention).
- Shares: weighted-average diluted shares from the same 10-K (fallback dei shares outstanding).
- Company E10 = mean real earnings over its last 10 usable fiscal years (≥7 required); E5 likewise (≥4).
- **Sector CAPE10** = Σ real market cap / Σ E10 over companies with both (cap-weighted harmonic aggregate — the Shiller aggregate). CAPE5 likewise.
- **Trend growth g10** = log-linear slope (%/yr) of aggregate real earnings over the last 10 fiscal years, balanced within the window; a fiscal year enters once ≥60% of companies have filed it (mixed fiscal year-ends). g5 likewise.
- **CAPEG** = CAPE10 / max(g10, 0.5). CAPE5G = CAPE5 / max(g5, 0.5).
- History: CAPE10 from 2014-03 (151 months); CAPE5 from 2011-03 (187 months). 52 companies in the current aggregate.

| as of 2026-09 | value |
|---|---|
| CAPE10 | 33.6 |
| CAPE5 | 29.4 |
| g10 (real, %/yr) | 1.7 |
| g5 (real, %/yr) | −9.6 |
| CAPEG | 19.6 |
| S&P CAPEG (same construction, Shiller data) | 5.8 (25th pct since 1990) |

Reading: on a cyclically adjusted growth basis Health Care is expensive relative to the S&P, the opposite of its plain-PE discount.

## 4. Results to date

### 4a. Volume as a predictor (13 Sep)
Two declared legs (log prior-month volume; log volume vs prior 12-month mean), stationary and timely, added to the
generic pool. Sequential next-month walk-forward (§4b mechanics), XLV:

| variant | acted / 212 | acc | LB95 | acted up-rate | edge |
|---|---|---|---|---|---|
| no volume, all vars | 37 | 70.3% | 54.2% | 73.0% | −2.7 |
| + volume, all vars | 35 | 65.7% | 49.1% | 65.7% | 0.0 |
| no volume, timely | 20 | 70.0% | 48.1% | 70.0% | 0.0 |
| + volume, timely | 25 | 68.0% | 48.4% | 68.0% | 0.0 |

Verdict: volume buys coverage, not skill (same on all nine sectors).

### 4b. Sequential next-month walk-forward harness (`seq_wf.py`)
Panel truncated at t; labels recomputed on the truncation; full recursive cascade refit from scratch every month
(in-fold 50/25/25, quality floor 0.50); rounds frozen; month t classified with `classify_frozen`; scored on the
realised sign; fit discarded. OOS 2008-12 → 2026-07, 212 scored months, H=1 so bets are non-overlapping and a plain
Wilson LB95 is honest. ~0.8 s per fit. This harness is the honest instrument; the standing board's fitted 74–88%
is not comparable.

### 4c. Generic-pool cells behind the standing XLV BUY (6-month board)
Round 1 Industrial Production | Gold (vaLB 0.909, 49 months, contaminated leg); round 2 WTI | Gold (0.699, 44);
round 3 M2 | 2-year (0.504, 44). All long. Current BUY at 0.70 conviction comes from WTI | Gold. Non-overlapping
bound 60.2% vs drift 66.6% → does not clear even on its own board.

### 4d. Sector CAPE / CAPEG horizon test (`hc_horizon_test.py`)
Single-predictor cell grammar (ternary level-z × ternary 6-month change, expanding, dead zone 0.2 sd, min cell 10,
36-month warm-up), direction = expanding majority of the realised H-month sign, labels only where known at t.

| predictor | H | acted | acc | acted up-rate | edge | long | non-overlap n / acc / LB95 |
|---|---|---|---|---|---|---|---|
| CAPE10 | 1 | 70 | 71.4% | 75.7% | −4.3 | 84% | 70 / 71.4 / 59.9 |
| CAPEG | 1 | 49 | 69.4% | 65.3% | **+4.1** | 84% | 49 / 69.4 / 55.5 |
| CAPE5 | 1 | 112 | 63.4% | 67.0% | −3.6 | 73% | 112 / 63.4 / 54.2 |
| CAPE5G | 1 | 91 | 62.6% | 63.7% | −1.1 | 92% | 91 / 62.6 / 52.4 |
| CAPE10 | 3 | 66 | 60.6% | 66.7% | −6.1 | 91% | 27 / 59.3 / 40.7 |
| CAPEG | 3 | 45 | 64.4% | 64.4% | 0.0 | 100% | 18 / 72.2 / 49.1 |
| CAPE5 | 3 | 107 | 67.3% | 67.3% | 0.0 | 100% | 40 / 62.5 / 47.0 |
| CAPE5G | 3 | 78 | 66.7% | 66.7% | 0.0 | 97% | 28 / 60.7 / 42.4 |
| CAPE10 | 6 | 59 | 76.3% | 76.3% | 0.0 | 100% | 13 / 76.9 / 49.7 |
| CAPEG | 6 | 41 | 80.5% | 80.5% | 0.0 | 100% | 9 / 66.7 / 35.4 |
| CAPE5 | 6 | 95 | 67.4% | 71.6% | −4.2 | 96% | 18 / 72.2 / 49.1 |
| CAPE5G | 6 | 77 | 76.6% | 79.2% | −2.6 | 97% | 15 / 86.7 / 62.1 |

Reading: CAPEG at one month is the only Health Care predictor with positive edge over drift (+4.1, n 49). Three- and
six-month accuracies are high but equal the up-rate (96–100% long). Series is short (CAPE10 from 2014): candidate,
not a certified cell. Reference on the S&P (1990→, 434 months): CAPE 59.9% / CAPEG 63.1%, both below the 64.1% up-rate.

### 4e. Constituent PE / PEG lists
`data/fundamentals/lists/XLV_Health_Care.csv` (59 names; sector median PE 26.2, cap-weighted 30.1, fwd 16.0, PEG 1.30).
Snapshot only; usable as today's peer-basket medians (e.g. the sector-relative PEG covariate in the 10 Sep
overextension pre-registration), never as a backtest predictor.

### 4f. Rotation (RRG) — descriptive only
XLV currently "rises" on the raw series, "maintains" once smoothed (4- or 8-week EMA). Quadrant does not forecast
the next quarter (pooled hit ≈ 50%). Not a system input.

### 4g. Full enforced driver on the tailored pool (`sector_recipe.py XLV`, run 2026-09-13)
Pool = nine macro legs (IndProd +2, M2 +1, CPI +2) + XLV_DivYield, XLV_RelSPY, XLV_CAPE10/5, XLV_CAPEG/5G, MedCPI_Rel (+2), HC_Employment (+2), Pharma_PPI (+2). UnitedHealth_CAPE dropped (§1). Horizon 1 month (driver default). Log verbatim:

```
=== Health Care (US_Healthcare_Close) — 331 months, up-rate 58.6% ===  [+XLV_DivYield,XLV_RelSPY,XLV_CAPE10,XLV_CAPE5,XLV_CAPEG,XLV_CAPE5G,MedCPI_Rel,HC_Employment,Pharma_PPI]
STEP0 AUDIT: n=333/333 zeros=0 stale=1 dups=0 gaps=0 splices=none spikes=none -> PASS
STEP1 CASCADE (27-type grammar, recursive refit, vaLB-floor 0.5): 4 rounds -> 197 mo covered (60%); weakest kept vaLB 0.545; TEST 53.4% LB0.43 -> ABSTAIN (below gate). rounds: WTI_Crud/MedCPI_R·T20·LB0.70, XLV_DivY/HC_Emplo·T20·LB0.59, XLV_RelS/MedCPI_R·T6·LB0.59, Dollar_I/MedCPI_R·T20·LB0.55
STEP1 cascade weak (LB0.43<=gate) — NOT gating; continuing to engines+DECISION per gospel
STEP1f FUNNEL: 7411 cand (1849 size-ok); IS>=70%: 304 -> full-gate 155 (OOS mean 60.2% max 84.6%, <=50%: 21%); IS>=65%: 567 -> full-gate 295 (OOS mean 60.1% max 90.0%, <=50%: 22%); IS>=60%: 956 -> full-gate 454 (OOS mean 58.8% max 90.0%, <=50%: 24%); nearest miss M2_Money|WTI_Crude_Close·T20 IS 68.4% OOS 90.0%(n10)
STEP1g LIFECYCLE: R1: active, OOS n=21 acc 52% UB0.69; R2: active, OOS n=10 acc 70% UB0.87; R3: active, OOS n=19 acc 53% UB0.70; R4: active, OOS n=8 acc 38% UB0.65
STEP1r REGIME-MONITOR (report-only): R1 train -0.05 / recent60 -0.08; R2 train +0.07 / recent60 +0.01; R3 train -0.26 / recent60 -0.14; R4 train -0.07 / recent60 -0.12
STEP1s: 0 rounds trigger Δ>20-pt collapse — no regime conduit opened
STEP1i LIQUIDITY-REGIME (VOICE/THROTTLE/CONDITIONER, report-only): train-stress-share 17% vs test 2%; [A voice] next-mo up-rate by regime: deep-stress:up46%(n13); stress:up59%(n17); neutral:up54%(n142); easy:up64%(n134); very-easy:up60%(n25)
STEP1t EMISSION: R1 WTI_Crude_Close|MedC ov99% LB0.53(n41) VALID; R2 XLV_DivYield|HC_Empl ov100% LB0.39(n15) FAILS; R3 XLV_RelSPY|MedCPI_Re ov100% LB0.40(n23) FAILS; R4 Dollar_Index|MedCPI_ ov100% LB0.22(n15) FAILS
STEP1v VALUATION FAMILY: no cell clears the floors
STEP1c TIER: 147 of 197 cascade months clear the >65% historical bar; wf-OOS 51.4%; base-signal recent-36mo 50.0%; M2_Money:acc6 <0.18 eff 86% n=114; Fed_Funds_Rate:acc6 >0.11 eff 74% n=33
STEP5 DECISION: RED DAWN test 62.4% (n=85, LB0.53); convergence 60.9% (n=69, LB0.51) -> ACTS
STEP5b STANDDOWN: recent-24-fired 58.3% -> clear
STEP6 MIRROR: RED DAWN Sortino 1.55 vs always-long 1.21 -> TWO-SIDED (RED DAWN, shorts kept) (39 down calls kept)
AUDITOR: 19/19 invariants PASS -> verdict allowed
```

Rounds: 1 WTI | MedCPI_Rel (T20, long, vaLB 0.698, va_n 26); 2 XLV_DivYield | HC_Employment (T20, long, 0.589, n 8); 3 XLV_RelSPY | MedCPI_Rel (T6, long, 0.589, n 8); 4 Dollar | MedCPI_Rel (T20, **short**, 0.545, n 16).

Reading: every stage ran and the auditor passed 19/19. The sector-specific legs were selected (medical-care CPI relative to headline appears in three of four rounds; dividend yield and relative price each once), and the cascade found a short cell for the first time. **None of the CAPE legs were chosen by the pair grammar**; their single-variable test (§4d) is the record for them. Emission audit: only round 1 survives carry-forward (rounds 2–4 FAIL at LB 0.39/0.40/0.22) — so the standalone emitted cell is WTI | MedCPI_Rel. Tier walk-forward 51.4%, base signal recent-36 months 50.0% (borderline). DECISION: RED DAWN test 62.4% (n 85, LB 0.53) → ACTS; MIRROR two-sided Sortino 1.55 vs always-long 1.21 → shorts kept (39 down calls). This is the driver's single 65/35 split; the sequential horizon sweep (§4h) is the honest out-of-sample record.

### 4h. Horizon sweep on the sequential harness, tailored pool (`seq_wf_tailored.py XLV H`, 13 Sep)
Same mechanics as §4b with the §4g pool and PIT lags; refit every month; H in {1, 3, 6}. **Effective scored window is
2016-01 → 2026-07 at every horizon**: before 2016 the in-fold cascade admits no cell above the 0.50 floor (true of the
generic pool too — 0 acted months 2008-12 → 2015-12 in both), so the harness is silent, not wrong, there.

| H | acted | coverage | acc | LB95 | acted up-rate | edge | long | non-overlap n / acc / LB95 | current call (2026-08) | dominant cell |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 49 | 23% | 67.3% | 53.4% | 69.4% | −2.0 | 94% | 49 / 67.3 / 53.4 | ABSTAIN | Dollar \| Pharma_PPI (23 months) |
| 3 | 40 | 19% | 72.5% | 57.2%* | 72.5% | 0.0 | 100% | 19 / 63.2 / 41.0 | BUY, conv 0.715 (IndProd \| Gold) | IndProd \| Gold (21) |
| 6 | 47 | 23% | 63.8% | 49.5%* | 61.7% | +2.1 | 85% | 11 / 63.6 / 35.4 | ABSTAIN | IndProd \| RelSPY (20) |

\* overlapping labels; the non-overlapping column is the honest bound.

Reading: no horizon yields edge over drift with an admissible bound. H=1 is the only horizon whose bets are independent;
its cascade is 94% long and sits 2 points below the up-rate. H=3's 72.5% is 100% long. H=6's +2.1 edge rests on 11
independent bets. The sector-specific legs are used (Pharma_PPI, RelSPY, HC_Employment, DivYield all appear) but do not
change the character: the cascade on Health Care is a long-drift selector. Per-year accuracy at H=1 dips to 40–43% in
2019–2020.

### 4i. Money test (H=1 ledger, 2016-01 → 2026-07, monthly, price-only, no costs)
| strategy | CAGR | Sortino (down-months) | MaxDD |
|---|---|---|---|
| buy&hold XLV | 9.96% | 1.23 | -16.2% |
| buy&hold SPY | 15.20% | 1.26 | -23.8% |
| long/flat on call | 7.29% | 0.77 | -12.4% |
| two-sided on call | 7.49% | 0.83 | -12.4% |
| abstain=hold (persistence) | 10.62% | 1.29 | -16.2% |

### 4j. Health Care verdict after the absolute-label runs — WATCH, no certified cell (superseded by §4k–§4l reading; see §6)
- Cascade (any pool, any horizon): no cell clears Wilson LB95 > 50% with positive edge over drift.
- Single candidate with positive edge: **CAPEG, 1 month, +4.1 over drift, n 49, LB95 55.5%** (§4d). Series from 2014; candidate to carry forward, not certified.
- Operating horizon recommendation: **1 month** (the only horizon with non-overlapping bets and an honest bound; 3- and 6-month accuracies are drift).
- Live reading (2026-08 row): tailored cascade ABSTAIN at H=1 and H=6; H=3 BUY at 0.715 on an Industrial Production cell (lagged +2, PIT-valid); standing 6-month board BUY at 0.70 on WTI \| Gold. Sector CAPEG 19.6 says expensive on cyclically adjusted growth.

### 4k. RELATIVE label (sector minus SPY), horizon 1 month — driver + sequential (13 Sep, after §5 rulings)

**Full driver, relative outcome = XLV/SPY month-start price ratio (`sector_recipe.py XLV relative`), auditor 19/19:**

```
=== Health Care (US_Healthcare_Close) — 332 months, up-rate 49.7% ===  [+XLV_DivYield,XLV_RelSPY,XLV_CAPE10,XLV_CAPE5,XLV_CAPEG,XLV_CAPE5G,XLV_g10,XLV_g5,MedCPI_Rel,HC_Employment,Pharma_PPI]
STEP0 AUDIT: n=333/333 zeros=0 stale=1 dups=0 gaps=0 splices=none spikes=none -> PASS
STEP1 CASCADE (27-type grammar, recursive refit, vaLB-floor 0.5): 5 rounds -> 192 mo covered (58%); weakest kept vaLB 0.508; TEST 62.8% LB0.50 -> ACTS. rounds: Fed_Fund/WTI_Crud·T6·LB0.77, M2_Money/Fed_Fund·T3·LB0.60, Dollar_I/Gold_Clo·T20·LB0.51, M2_Money/Gold_Clo·T6·LB0.54, M2_Money/Industri·T6·LB0.62
STEP1f FUNNEL: 7407 cand (1899 size-ok); IS>=70%: 136 -> full-gate 43 (OOS mean 53.9% max 100.0%, <=50%: 46%); IS>=65%: 362 -> full-gate 131 (OOS mean 54.6% max 100.0%, <=50%: 45%); IS>=60%: 798 -> full-gate 268 (OOS mean 53.9% max 100.0%, <=50%: 47%); nearest miss Gold_Close|Term_Spread_10Y_2Y·T6 IS 70.6% OOS 100.0%(n8)
STEP1g LIFECYCLE: R1: active, OOS n=17 acc 59% UB0.76; R2: active, OOS n=2 acc 50% UB0.88; R3: DORMANT, OOS n=1 acc 100% UB1.00; R4: active, OOS n=20 acc 70% UB0.84; R5: active, OOS n=3 acc 33% UB0.75
STEP1r REGIME-MONITOR (report-only): R1 train -0.10 / recent60 -0.17; R2 train +0.07 / recent60 +0.00; R3 train +0.10 / recent60 +0.21; R4 train -0.06 / recent60 +0.17 ⚠REGIME-FLAG; R5 train -0.13 / recent60 +0.03 ⚠REGIME-FLAG
STEP1s: 0 rounds trigger Δ>20-pt collapse — no regime conduit opened
STEP1i LIQUIDITY-REGIME (VOICE/THROTTLE/CONDITIONER, report-only): train-stress-share 17% vs test 2%; [A voice] next-mo up-rate by regime: deep-stress:up54%(n13); stress:up53%(n17); neutral:up46%(n142); easy:up50%(n135); very-easy:up64%(n25)
STEP1t EMISSION: R1 Fed_Funds_Rate|WTI_C ov76% LB0.47(n20) VALID; R2 M2_Money|Fed_Funds_R[lag:M2_Mon] ov61% LB0.42(n24) FAILS; R3 Dollar_Index|Gold_Cl ov98% LB0.52(n15) VALID; R4 M2_Money|Gold_Close[lag:M2_Mon] ov88% LB0.60(n37) VALID; R5 M2_Money|Industrial_[lag:M2_Mon,Indust] ov61% LB0.17(n23) FAILS
STEP1v VALUATION FAMILY: no cell clears the floors
STEP1c TIER: 143 of 192 cascade months clear the >65% historical bar; wf-OOS 64.6%; base-signal recent-36mo 63.9%; MedCPI_Rel:lvl92 <-0.45 eff 96% n=89; M2_Money:lvl120 <1.21 eff 100% n=12; Term_Spread_10Y_2Y:acc3 >0.16 eff 80% n=33; GS10_Rate:vel7 <-0.65 eff 75% n=9
STEP5 DECISION: RED DAWN test 71.2% (n=73, LB0.62); convergence 72.2% (n=36, LB0.59) -> ACTS
STEP5b STANDDOWN: recent-24-fired 66.7% -> clear
STEP6 MIRROR: RED DAWN Sortino 2.13 vs always-long 0.42 -> TWO-SIDED (RED DAWN, shorts kept) (74 down calls kept)
AUDITOR: 19/19 invariants PASS -> verdict allowed
```

Rounds: 1 Fed funds | WTI (T6, long, vaLB 0.769); 2 M2 | Fed funds (T3, **short**, 0.601); 3 Dollar | Gold (T20, long, 0.508);
4 M2 | Gold (T6, **short**, 0.541); 5 M2 | Industrial Production (T6, long, 0.623). Tiers lean on MedCPI_Rel (level < −0.45, 96% eff, n 89).
Reading: on the relative series the label is balanced (49.7% up), the cascade is genuinely two-sided (74 down calls), DECISION
71.2% (n 73, LB 0.62) with convergence 72.2% (n 36, LB 0.59) → **ACTS by the §5 gate**; MIRROR 2.13 vs always-long-relative 0.42.
Emission audit: rounds 2 and 5 fail carry-forward; rounds 1, 3, 4 valid. Regime flags on rounds 4 and 5 (sign flip vs train).
This is the driver's single 65/35 split.

**Sequential walk-forward, relative label, tailored pool (`seq_wf_tailored.py XLV H relative`)** — edge is vs the
majority-class rate of the acted months (§5.5):

| H | acted | coverage | acc | LB95 | up-rate | majority | edge | long | window | current (2026-08) | dominant cells |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | 54 | 25% | 59.3% | 46.0% | 44.4% | 55.6% | **+3.7** | 44% | 2019–2026 | ABSTAIN | M2 \| HC_Employment 20; DivYield \| MedCPI_Rel 9; IndProd \| RelSPY 7 |
| 3* | 42 | 20% | 61.9% | 46.8% | 42.9% | 57.1% | +4.8 | 57% | 2018–2026 | LONG-rel 0.666 (WTI \| Pharma_PPI) | DivYield \| MedCPI_Rel 12; Gold \| Pharma_PPI 9 |
| 6* | 53 | 26% | 67.9% | 54.5% | 35.8% | 64.2% | +3.8 | 42% | 2014–2026 | LONG-rel 0.601 (WTI \| Gold) | DivYield \| Pharma_PPI 10; M2 \| Gold 9 |

\* overlapping labels, reference only (horizon frozen at 1).

Reading: this is the first Health Care record that looks like sector knowledge rather than market drift — the calls are two-sided
(44% long), the sector legs dominate the accepted cells (health employment, dividend yield, medical CPI, relative price, pharma
PPI), and accuracy sits above the constant-call bar at every horizon. It is **not certified**: at 1 month the Wilson LB95 is
46.0% on 54 bets, and the per-year record swings (2021 44%, 2024 86%). Evidence channel says WATCH; the §5 gate (DECISION) says
ACTS on the driver's split. The two disagree exactly as the recipe anticipates (single split optimistic; sequential honest).

### 4l. Anchor-only 27-type run (CAPE10 with g10 as the pair, nothing else) — NOT POWERED
Even with the history restarted at the anchor's first valid row (2016-03, 126 rows; first decision after 60), the recursive
cascade admits **no cell** at either label: a type needs ≥15 training members and ≥8 validation members from ~63 training rows.
The sector CAPE has 12 years of history against the S&P's 145; the 27-type anchor analysis the S&P chain did in Stage 1 cannot be
run on it yet. CAPEG's record is therefore the single-predictor test only (§4d absolute; relative below), and the CAPE legs sit in
the cascade pool where the pair grammar has not selected them.

Single-predictor test, relative label (majority-class edge): CAPEG 1-mo 57.1% vs 63.3% bar (−6.1, n 49); CAPE5 1-mo 53.6% vs 52.7%
(+0.9, n 112); every other cell negative. **On the relative label CAPEG does not beat a constant call.**

### 4m. Money test, relative label (H=1 ledger, 2019-01 → 2026-07, XLV-minus-SPY monthly excess, no costs)
| strategy | CAGR of the excess | Sortino | MaxDD |
|---|---|---|---|
| constant long XLV vs SPY (rel) | -6.93% | -0.74 | -46.9% |
| constant SHORT XLV vs SPY (rel) | 5.73% | 0.79 | -19.1% |
| calls: long/short XLV-vs-SPY, flat on abstain | 3.88% | 0.53 | -14.1% |
| calls + persistence (hold last rel call) | 8.12% | 1.13 | -10.3% |

### 4n. Forward tape opened (`results/XLV_forward_tape.csv`)
First as-issued row 2026-09-13: decision row 2026-08, horizon 1 month, absolute call ABSTAIN, relative call ABSTAIN; resolves 2026-10-01.
The tape is the evidence channel from here; the sequential bound accrues on it.

### 4o. STAGE-1 TYPE ANALYSIS — the four anchors, ORACLE discipline (`hc_oracle_types.py`, 13 Sep)

**This analysis is to be run for every sector.** For each sector: build the three discrete legs (real price, 10-year smoothed
real earnings, trend real earnings growth — each adjusted before any ratio, the S&P standard), run the four anchors below through
the ORACLE step (27 sub-types = sign triple of the N-month change of ratio / numerator / denominator, ±0.5 SD dead zone, N swept on
the design sample and frozen, sequential walk-forward, all 27 sub-types printed), on both labels, at the frozen horizon, and
**select the sector's anchor = the most accurate one** by the rule: highest edge over the majority-class rate, with Wilson LB95
above 50%, n ≥ 60, both directions discriminating, no single year carrying it. The selected anchor is the sector's Stage-1
predictor; the others are recorded, not discarded.

Mechanics as the S&P, with three declared adaptations: design sample = first 40% of the series (no pre-1990 history); the
walk-forward starts after the design sample (kept disjoint, as the S&P's 1990 start is from its pre-1990 design); the design
sweep floor is 24 months instead of 40 (short series). Horizon 1 month. Ungated (global fallback, as in the S&P Stage 1) —
every month is called; abstention is deferred to later stages.

| anchor | label | N | rows | n WF | acc | LB95 | up-rate | majority | edge | long | N sweep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PE | absolute | 3 | 151 | 87 | 74.7% | 65% | 58.6% | 58.6% | +16.1 | 68% | peaked |
| PE_G | absolute | 3 | 127 | 63 | 77.8% | 66% | 60.3% | 60.3% | +17.5 | 60% | peaked |
| P_G | absolute | 3 | 127 | 63 | 73.0% | 61% | 60.3% | 60.3% | +12.7 | 52% | peaked |
| E_G | absolute | 6 | 127 | 60 | 55.0% | 42% | 58.3% | 58.3% | -3.3 | 67% | peaked |
| PE | relative | 3 | 151 | 87 | 58.6% | 48% | 41.4% | 58.6% | -0.0 | 46% | peaked |
| PE_G | relative | 3 | 127 | 63 | 58.7% | 46% | 41.3% | 58.7% | +0.0 | 41% | peaked |
| P_G | relative | 3 | 127 | 63 | 52.4% | 40% | 41.3% | 58.7% | -6.3 | 48% | peaked |
| E_G | relative | 9 | 127 | 57 | 45.6% | 33% | 42.1% | 57.9% | -12.3 | 30% | peaked |

Per-direction and per-year, absolute label (the leaders):

| anchor | n | acc | long calls | months up vs unconditional | short calls | months down vs unconditional | by year |
|---|---|---|---|---|---|---|---|
| PE against Growth | 63 | 77.8% | 38 | 81.6% vs 60.3% | 25 | 72.0% vs 39.7% | 2021 100%/7, 2022 67%/12, 2023 75%/12, 2024 75%/12, 2025 75%/12, 2026 88%/8 |
| Price to Earnings | 87 | 74.7% | 59 | 74.6% vs 58.6% | 28 | 75.0% vs 41.4% | 2019 57%/7, 2020 75%/12, 2021 75%/12, 2022 67%/12, 2023 75%/12, 2024 75%/12, 2025 83%/12, 2026 88%/8 |
| Price to Growth | 63 | 73.0% | 33 | 81.8% vs 60.3% | 30 | 63.3% vs 39.7% | 2021 86%/7, 2022 67%/12, 2023 75%/12, 2024 67%/12, 2025 67%/12, 2026 88%/8 |

**Reading.** On the absolute label three of the four anchors are two-sided and beat the constant-call bar by 13–18 points with lower
bounds above 60%: the short calls land in months that fell 63–75% of the time against a 40% base, so this is not long-drift
capture. Earnings-to-Growth alone is noise. On the relative label every anchor collapses to the majority class (edge 0 or
negative): the type structure is in the sector's own direction, not in its performance against the market — consistent with §5.5.
The pending September 2026 call is **UP** on all three leaders (type T14, ratio flat / numerator flat / denominator flat, 21–30
up vs 10–12 down in same-type history).

**Health Care's most accurate anchor: PE against Growth (CAPE10 / trend growth = CAPEG), absolute label, N = 3 months.**
77.8% on 63 walk-forward months (LB95 66%), +17.5 over the majority class, 60% long, short calls right 72%, every year 67–100%.
Price to Earnings (plain sector CAPE) is the runner-up at 74.7% on the longer 87-month window (LB 65%, +16.1) and is the
fallback if growth data is unavailable for a sector. Caveats that stay attached: walk-forward window 2021-03 → 2026-08 (5½
years); N chosen on 2016–2020; the earnings leg steps annually (filings) so N = 3 mostly reads price and growth moves; ungated.
Certification, as for the S&P, comes from the type-level pulls at Stage 3 and the forward tape, not from this table.

### 4p. STAGE 3 on the selected anchor — PE against Growth (`hc_stage3.py`, 13 Sep)

**Process (this is the process to run for every sector once its anchor is selected in §4o).** The sector is run through the
S&P's own Phase 1/2 machinery (`ZION/multiasset_pipeline.py`, unmodified, imported): (1) anchor 27-type table by sequential
majority-vote walk-forward with Wilson zones; (2) **type-level PULLS** — a type becomes a standing ACT rule iff its walk-forward
accuracy > 67.5% with n ≥ 8; pulled months are removed from the pool; (3) **untruncated tier cascade on the non-pulled
remainder** — per type, candidate features from the pool (five derivative forms), Welch screen, hard gate R² ≥ 0.20, Youden
thresholds, four tiers, Wilson-gated flip, floors of 8; every type printed, pool months reconcile to emitted + abstained with
reason; (4) MIRROR test on acted months (opposite signal and always-up as the two benchmarks); (5) production board; (6) audit
invariants (expanding window, frontier gap, partition, pull membership). Sector adaptations declared in the script header:
H = 1 month (the printed "3-MONTH" header text is the S&P run's label — the verification block shows frontier gap 1 row, i.e.
H = 1 was used); scoring START = end of the design sample (2020-05); sector legs added as extra candidates (splice-scanned);
PUB_LAG applied as in the pipeline's own main().

**"No change" criterion (verbatim mechanics).** For each leg — ratio, numerator, denominator — take the N-month percentage
change (N = 3, frozen from the design sweep), z-score it on the TRAIN rows only (all months before the decision month, expanding,
PIT), and classify: |z| ≤ 0.5 train-SD → **flat (no change)**; z > +0.5 → UP; z < −0.5 → DN. Type = 9·(ratio+1) + 3·(num+1) + (den+1).
Because the growth leg updates only when filings land, the denominator reads "flat" in most months: 47 of the 62 scored months sit
in a type with at least one flat leg, and all three pulled types contain one.

**27-type table (n = months scored in the walk-forward, 2021-03 → 2026-07; 10 of 27 types populated, 17 empty):**

| T | ratio/num/den | n | WF % | LB | UB | zone | |
|---|---|---|---|---|---|---|---|
| T1 | DN/DN/DN | 0 | — | — | — | empty |  |
| T2 | DN/DN/flat | 11 | 90.9 | 62.3 | 98.4 | PREDICTIVE | PULLED |
| T3 | DN/DN/UP | 5 | 60.0 | 23.1 | 88.2 | COIN-TOSS |  |
| T4 | DN/flat/DN | 0 | — | — | — | empty |  |
| T5 | DN/flat/flat | 0 | — | — | — | empty |  |
| T6 | DN/flat/UP | 1 | 100.0 | 20.7 | 100.0 | COIN-TOSS |  |
| T7 | DN/UP/DN | 0 | — | — | — | empty |  |
| T8 | DN/UP/flat | 0 | — | — | — | empty |  |
| T9 | DN/UP/UP | 1 | 100.0 | 20.7 | 100.0 | COIN-TOSS |  |
| T10 | flat/DN/DN | 0 | — | — | — | empty |  |
| T11 | flat/DN/flat | 4 | 50.0 | 15.0 | 85.0 | COIN-TOSS |  |
| T12 | flat/DN/UP | 0 | — | — | — | empty |  |
| T13 | flat/flat/DN | 0 | — | — | — | empty |  |
| T14 | flat/flat/flat | 14 | 85.7 | 60.1 | 96.0 | PREDICTIVE | PULLED |
| T15 | flat/flat/UP | 0 | — | — | — | empty |  |
| T16 | flat/UP/DN | 0 | — | — | — | empty |  |
| T17 | flat/UP/flat | 16 | 87.5 | 64.0 | 96.5 | PREDICTIVE | PULLED |
| T18 | flat/UP/UP | 1 | 100.0 | 20.7 | 100.0 | COIN-TOSS |  |
| T19 | UP/DN/DN | 7 | 57.1 | 25.0 | 84.2 | COIN-TOSS |  |
| T20 | UP/DN/flat | 0 | — | — | — | empty |  |
| T21 | UP/DN/UP | 0 | — | — | — | empty |  |
| T22 | UP/flat/DN | 0 | — | — | — | empty |  |
| T23 | UP/flat/flat | 0 | — | — | — | empty |  |
| T24 | UP/flat/UP | 0 | — | — | — | empty |  |
| T25 | UP/UP/DN | 2 | 0.0 | 0.0 | 65.8 | COIN-TOSS |  |
| T26 | UP/UP/flat | 0 | — | — | — | empty |  |
| T27 | UP/UP/UP | 0 | — | — | — | empty |  |

Overall ungated: 77.4% on 62 (LB 65.6%). **Pulled: T2 (DN/DN/flat) 90.9% n 11; T14 (flat/flat/flat) 85.7% n 14; T17 (flat/UP/flat)
87.5% n 16 → 41 of 62 months (66%), blended 87.8%.** Remainder pool 35 months: 2 emitted by the tier cascade (T11 tier 4, both
right), 33 abstain (type thinner than 8, or untypeable in warm-up). MIRROR on 43 acted months: OOS 88.4% (LB 75.5%) vs opposite
signal 11.6% vs always-up 62.8% → EDGE, with the pipeline's own caveat printed: pull-set membership is chosen on the full-sample
walk-forward record, so the acted-months figure is an upper bound; per-month routing is walk-forward. Audit: clean.

**Current call.** Latest decision row in the panel is 2026-08: type T18 (flat/UP/UP), one prior month → thinner than the floor →
**ABSTAIN**. The Yahoo-priced September row (§4o) lands in T14, a pulled type, which would emit **UP** once the panel carries it.


**Remainder accounting and the tier layer (operator questions, 13 Sep).** 76 decision months; 41 pulled; 35 left in the pool, of which
13 are warm-up months with no type (train < 60 rows) → 22 typed remainder months (21 scored). Tier cascade on the remainder: 2 emitted
(T11, tier 4, both right), 20 abstain because their type had < 8 training months. The tier cascade does **not** remove months from the
pool — removal happens only at the pull step in this machinery (the recursive remove-and-refit belongs to the library's pair cascade,
a different object). **Whole-group check** (`hc_stage3_nopull.py`, pulls switched off, tiers on all 76): 20 emitted at 85.0% (LB 64%)
against an 80% up-rate on those months, from tiers inside T14 (tier 2, 10 months at 90%; tier 4, 4), T17 (tier 2, 4) and T11 (tier 4, 2).
Month-by-month overlap: **all 20 no-pull emissions lie inside the 43 months the pulls-on run acted on** — 18 are pulled months, the
other 2 are the same T11 months the remainder cascade emitted; 0 outside. Direction agreement on the 20: 95% (tiers 85%,
pulls 90% on those months). 23 of the 41 pulled months are not reached by any tier. So the tier layer, run on everything,
is a strict subset of the pull layer for Health Care: it selects the same types, fewer months, one less accurately. The pulls are the
system; the tiers confirm them and add nothing outside them.

**Pre-type, type-agnostic tier screen (operator correction, 13 Sep; `hc_stage3_pretype.py`).** The earlier "whole-group" run was still
type-conditioned. This run gives the pipeline a constant anchor so every month is one type: one universe-wide tier cascade on all months
BEFORE any type analysis, with the CAPE legs available as ordinary candidates. Result: every month emitted (75 scored), variant B 70.7%
(LB 59.6%) vs 60.0% always-up; inside it **one tier-2 rule — 6-month velocity of XLV_CAPE10 above its threshold → UP — 35 months at 91.4%
OOS (LB 77.6%)**, and a tier-4 remainder of 40 months at 52.5% (coin). Month-level overlap with the type pulls: 22 of the 35 tier-2 months
are pulled months (direction agreement 91%); 13 are outside every month the pulled run acted on, at 92% — but 7 of those 13 fall in
the anchored run's warm-up (train < 60 rows: 2020-07-01, 2020-08-01, 2020-09-01, 2020-11-01, 2020-12-01, 2021-03-01, 2021-04-01), where it could not act by construction; the **genuinely new months are
6** (2021-10-01, 2022-03-01, 2022-05-01, 2024-03-01, 2026-06-01, 2026-07-01), 100% right, all UP. 19 of the 41 pulled months are reached by no tier (pulls 84% on them).
So the pre-type layer is NOT fully consumed by the pulls: it is one long-only rule on the anchor's own velocity that overlaps the pulls
on 22 months and adds 6 outside them. A union (pulls + remainder cascade + pre-type tier-2 on the pulled run's abstained months) would
act on 49 of 62 scored months at 89.8%. This union is a CANDIDATE architecture (pre-type tier → type pulls → post-type tier), not adopted:
the tier rule's per-month routing is in-fold, but its existence was noticed on the full record.

**No-change dead zone — definition and sensitivity (`hc_stage3_sd.py`, pulls on).** Flat = |z| ≤ SD where z = (3-month % change − train
mean) / train SD, train-only, expanding. SD = 0.5 is the locked S&P constant; the sweep is a sensitivity reading, not a re-tune:

| SD (dead zone) | types populated | pulled types | pull coverage | pull accuracy | overall ungated | acted OOS (pulls + remainder) | mirror |
|---|---|---|---|---|---|---|---|
| 0.25 | 14 | 1 | 13 / 62 (21%) | 69.2% | 69.4% | 70.6% (n 17) | 29.4% |
| 0.35 | 13 | 2 | 27 / 62 (44%) | 81.5% | 72.6% | 82.8% (n 29) | 17.2% |
| **0.50** | 10 | 3 | 41 / 62 (66%) | **87.8%** | **77.4%** | **88.4% (n 43)** | 11.6% |
| 0.75 | 8 | 3 | 47 / 62 (76%) | 76.6% | 67.7% | 76.6% (n 47) | 23.4% |
| 1.00 | 7 | 3 | 51 / 62 (82%) | 74.5% | 71.0% | 74.5% (n 51) | 25.5% |

Reading: tightening the dead zone fragments the months into more, thinner types (fewer pulls, −6 to −19 points of pull accuracy);
widening it merges types (more coverage, +10 to +16 points, at −11 to −13 points of accuracy). The locked 0.5 sits at the peak on every
metric — a confirmation of a pre-set constant, not a fit — and the sensitivity on a 62-month window is itself a reason to keep 0.5 fixed
for every sector rather than tune it per sector.

**Caveats.** 62 scored months, 5½ years; pull membership in-sample by construction (same as the S&P's, "full-record = going-forward
only"); the earnings leg steps annually. Certification remains the forward tape.

### 4q. PARALLEL INSTRUMENTS — type pulls (system) vs pre-type CAPE-velocity tier: overlap, convergence, divergence, and what each state predicts (`hc_convergence.py`, 13 Sep)

**Ruling (operator):** the type-level analysis stays as the system. The pre-type tier runs in parallel as a second instrument; the joint
state of the two is measured month by month, and each state is scored against the outcome on the standard sequential next-month OOS
with the Wilson LB95 > 50% threshold. Both records are one-step-ahead sequential at H = 1 (§4p runs); window = the 62 scored months
2021-03 → 2026-07 (the type run's warm-up months are "type silent"). Tier instrument = its predictive tier only (tier 2, the CAPE10
6-month-velocity rule); tier 4 is a coin (52.5%) and treated as abstain — a definition made after seeing tier 4's OOS, stated as such.

| joint state | n | up-rate of those months | type call acc | tier call acc | acted call acc | LB95 | clears |
|---|---|---|---|---|---|---|---|
| CONVERGE (both act, agree) | 20 | 95% | 95.0% | 95.0% | **95.0%** | 76% | YES |
| DIVERGE (both act, disagree) | 2 | 50% | 50.0% | 50.0% | 50.0% | 9% | no |
| TYPE only | 21 | 33% | **85.7%** | — | 85.7% | 65% | YES |
| TIER only | 13 | 92% | — | **92.3%** | 92.3% | 67% | YES |
| NEITHER | 19 | 32% | — | — | — | — | — |

Overlap: the type acts on 43 months, the tier on 35; both act on 22, and when both act they agree 91% (the two divergent months,
2022-09 and 2025-06, split 1–1). Unconditional up-rate over the window 60%.

**Reading.** (i) Convergence months are almost all up-months (95%) and both instruments are long there: the convergence call is right 95%
against a 60% unconditional up-rate — the selection has timing content, but it is one-sided. (ii) TYPE-only months are where the system's
two-sidedness lives: the up-rate is 33% and the type calls (mostly shorts from T2) are right 85.7% — this is the part the tier cannot see.
(iii) TIER-only months (13, 92%, all long) are the new coverage found in §4p, 7 of them in the type run's warm-up. (iv) The two disagree on
only 2 months and are right once each; divergence = abstain. (v) NEITHER months run 32% up — the silence itself is informative (both
instruments go quiet in down-months), which is the same abstain-as-information pattern seen elsewhere in the house.

**Divergence months (operator question).** Tier-2 definition: **2 divergent months** — 2022-09 (type SHORT via T2, tier UP; outcome DOWN → type right)
and 2025-06 (type SHORT, tier UP; outcome UP → tier right). Accuracy on them 50% each; both calls were made one-step-ahead in the
sequential walk-forward, so the record is out of sample but n = 2 says nothing (LB 9%). Under the broader definition (every tier emission
including the coin tier 4): 11 divergent months, type right 72.7% (LB 43%), tier right 27.3% — the type wins the disagreements, which is
why the type keeps authority on divergence in §4r. Both instruments are long-biased in the same direction; divergence arises only where the
type finds a short cell (T2) that the velocity rule cannot see.

**Abstentions vs exclusions (operator question).** The integrated ledger has 75 rows = 49 acted + **13 genuine abstentions** (system ran,
no instrument spoke: thin types T19/T3/T11/T25, tier silent) + **13 exclusions by rule** (warm-up, train < 60 rows, 2020-05 → 2021-02,
where the type system could not run) — plus the unscored current row (2026-08) which is a genuine abstention pending resolution.

**Combined instruments (candidates, not adopted):** act on CONVERGE + TYPE-only + TIER-only, abstain on DIVERGE / NEITHER → **54 of 62
months at 90.7%, LB95 80.1%** (up-rate of acted months 70%); convergence-only → 20 of 62 at 95.0%, LB95 76.4%. Caveats: the two
instruments are NOT independent predictors — both read the sector CAPE10 (types on Δratio/Δnum/Δden, tier on the numerator's velocity),
so "convergence" is partly the same information twice; pull membership and the tier-2 designation are full-record choices; 62 months,
one sector. The forward tape carries all three states (type, tier, joint) from the September row; certification comes from there.

**Current state (2026-08 decision row):** type ABSTAIN (T18, thin), tier-2 silent (tier 4) → joint NEITHER → ABSTAIN. The Yahoo-priced
September row lands in pulled type T14 → the system would read UP once the panel carries it; the tier's read on that row is pending.

### 4r. INTEGRATED INSTRUMENT (operator ruling 13 Sep): type pulls + post-type cascade + pre-type tier on silent months (`hc_integrated.py`)

**Ruling.** Integrate the 2 post-type remainder-cascade months and the 6 genuinely new pre-type tier-2 months into the system.
**Precedence:** (1) type pull; (2) if the type is silent, the post-type remainder cascade; (3) if both are silent and the type system was
able to run (warm-up excluded), the pre-type tier-2 (CAPE10 6-month velocity > threshold → UP). Divergence (type acts, tier-2 disagrees):
the type call stands — the type analysis is the system. Variant with abstain-on-divergence reported for reference.

| instrument | acted / 62 | acc | LB95 | acted up-rate | long share | long calls: months up | short calls: months down |
|---|---|---|---|---|---|---|---|
| type-only (pulls + remainder) | 43 (69%) | 88.4% | 75.5% | 63% | 70% | — | — |
| **INTEGRATED** | **49 (79%)** | **89.8%** | **78.2%** | 67% | 73% | 36 → 89% | 13 → 92% |
| variant: abstain on divergence | 47 (76%) | 91.5% | 80.1% | 68% | 77% | 36 → 89% | 11 → 100% |

By source (integrated): type pulls 41 @ 88%; post-type cascade 2 @ 100%; pre-type tier-2 6 @ 100%. By year: 2021 100%/5, 2022 82%/11,
2023 90%/10, 2024 90%/10, 2025 89%/9, 2026 100%/4. Unconditional up-rate 60%.

Money test, 2021-03 → 2026-07, XLV next-month returns, no costs: buy-and-hold XLV 10.19% CAGR / Sortino 1.67 / MaxDD −15.0%; SPY 18.72% /
2.40 / −22.4%; type-only two-sided on call 20.92% / 6.30 / −3.5%; **integrated two-sided 25.38% / 7.51 / −3.5%**; integrated long-flat
18.23% / 8.82 / −3.5%; integrated + persistence 17.46% / 3.04 / −14.0% (persistence HURTS here — the shorts and the abstentions are
where the sector falls, so holding through them gives the drawdown back; opposite of the S&P book's finding).

Caveats carried forward: 62 months; pull membership and the tier-2 designation are full-record; the 8 added months are 100% right, which
is exactly what a full-record selection would show — their forward record starts now; the two instruments share the anchor.

**Remaining abstentions (operator question).** After integration, 13 of the 62 scored months still have no call (plus the 13 warm-up
months before 2021-03 where the type system could not run — excluded by rule, not abstentions). The 13: T19 (UP/DN/DN) ×7, T3 (DN/DN/UP)
×3, T11 ×2 (degenerate screen / thin leaf), T25 ×1 — every one a type too thin to pull (< 8 training months) and outside the tier-2
rule. They are not neutral months: **9 of 13 went DOWN, mean next-month return −2.12% against +0.69% for the window** (2021-09, 2021-11,
2022-04, 2024-04, 2025-03/04/05, 2026-03/04 all fell 1.7–6.4%). T19 = ratio UP with both price and growth DOWN, i.e. CAPEG rising because
growth is falling faster than price — a de-rating-in-progress signature that has no pull yet because it has only 7 months of history.
The abstentions therefore carry information (silence ≈ down-month), which is the same abstain-as-information pattern seen at the book
level; nothing is done with it here — a "T19 → short" rule would be a full-record selection on 7 months and is NOT adopted. It is logged
as the first candidate to watch on the forward tape: T19 clears the pull bar at n = 8 if its next occurrence resolves down.

**Current month.** August decision row (outcome September): type T18 thin → abstain, tier-4 → silent → **integrated ABSTAIN**.
September decision row (outcome October, Yahoo-priced): type **T14, a pulled type → UP**; tier feature: CAPE10 6-month-change velocity
z = +1.66 vs threshold 0.22 → **tier-2 UP**; integrated call **UP** (both instruments agree). Written to the forward tape.

### 4s. ENGINES + DECISION on the integrated signal (`hc_decision.py`, 13 Sep) — recipe steps 2–3 and 5, `lib_pipeline.engines` / `decision` unmodified

**Which engines.** The DECISION vote uses the two directional engines: **ODYSSEY** (binned pattern analogue) and **SANCTUARY**
(similarity-weighted analogue with permutation scoring), both run on XLV's own monthly returns, point-in-time. **TRON** (payoff /
conviction sizing), **TEARS** (freeze / portfolio) and **CASSANDRA** (direction-gated price band) are downstream layers that consume
a decided direction; they do not vote and were not run here. MIRROR was run in §4p.

| item | result |
|---|---|
| integrated signal in the DECISION test block (last 35% of labelled months, from 2016-12) | all 49 acted months inside |
| integrated, test block | 89.8% (n 49), Wilson-LB (z 1.645) 0.80 |
| convergence = integrated kept only where SANCTUARY agrees | 88.2% (n 34), LB 0.76 |
| **DECISION (GATE 0.45)** | **ACTS** — on both the raw signal and the convergence subset |
| SANCTUARY standalone, whole test block | 56.0% (n 116) vs 61% up-rate — drift-level |
| ODYSSEY standalone | emits 10 months in the test block, 30% — sparse and wrong |
| SANCTUARY vs integrated on the 49 acted months | agree 34 (88.2%); **disagree 15: integrated 93.3%, SANCTUARY 6.7%** (up-rate 20% — these are the short months) |
| ODYSSEY vs integrated | agree 2, disagree 3 (integrated 100%, ODYSSEY 0%), silent 44 |

Three-engine tally (integrated + ODYSSEY + SANCTUARY): unanimous 2 (100%); 2-of-3 32 (87.5%, LB95 72%); integrated alone vs opposition 15
(93.3%, LB95 70%, up-rate 20%); ≥ 2 agree (the house Stage-4 gate) 34 at 88.2%, LB95 73%.

**Reading.** The §5 act gate is met: DECISION ACTS. But gating the CALLS on SANCTUARY convergence would discard the 15 months where the
integrated signal is opposed — the shorts, where it scores 93% and the analogue engine 7%. That is the recipe's own arbitration case
("prefer the raw signal if it beats drift two-sided; convergence is a long-biased subset and must never silently drop the short edge"):
the two-sided integrated signal stands as the call; the engines confirm the long side (2-of-3 on 32 months) and contribute nothing on
the short side. Both engines are silent on the current (2026-08) row.

### 4t. CASSANDRA — price at the outcome date (`hc_cassandra.py`, 13 Sep)
Decision row 2026-09-01, XLV spot $171.67, integrated call **UP** (both instruments agree), outcome date **2026-10-01**, horizon 1 month.
The production band builder (`gen_cassandra_prices.analogue_returns`, unmodified) found **no analogue** for XLV's recent 3–5-month shape
above the 0.55 similarity floor → the analogue leg **VETOES** and the builder falls back to its statistical band (n 333: p10 $163.14 /
p50 $172.67 / p90 $182.75, reference only). The recipe's answer when the analogue leg vetoes is the cell-conditioned range — the band
hung on what is actually acting:

| band (next-month XLV, 2026-10-01) | n | up | p10 | p50 | p90 | price p10 / p50 / p90 |
|---|---|---|---|---|---|---|
| statistical, all months (reference) | 333 | 59% | −4.10% | +0.76% | +6.19% | $164.62 / $172.98 / $182.30 |
| statistical, conditional on UP | 195 | 100% | +0.62% | +2.91% | +6.97% | $172.73 / $176.67 / $183.64 |
| **TYPE-conditioned: T14 same-type past months** | 31 | 68% | −1.98% | +1.45% | +6.51% | $168.28 / **$174.16** / $182.85 |
| **CALL-conditioned: the integrated instrument's past UP calls** | 36 | 89% | −0.50% | +2.39% | +7.31% | $170.81 / **$175.77** / $184.21 |
| type-conditioned, up-months only (the called sign) | 21 | 100% | +0.37% | +2.45% | +6.93% | $172.31 / $175.87 / $183.56 |

**Emitted price (direction-conditional, per the house rule): p50 ≈ $175 to $176 for 2026-10-01 (+2.4% to +2.9%), band $171 to $184.**
The call-conditioned band is the system-native one (36 months, 89% up). Divergence gate: the unconditional p50 (+0.8%) does not oppose
the call → price not withheld. Caveat: the analogue engine has nothing to say about this row; the emitted range rests on the instrument's
own 36-call history, which is full-record for the 8 integrated months.

### 4u. SIZING — recommendation (`results/stage3_hc/sizing.json`, 13 Sep)
House sizing doctrine applied: **static, risk-based, no per-call conviction multiplier** (every dynamic-conviction rule ever tested in the
house — conv-TRON, record-sizing, tier conviction — rejected; Sortino-weighted static sleeves + caps + exogenous throttle are the
architecture). Admission is by DECORRELATION (Phase −1), not accuracy. Sleeve stream = integrated two-sided call on XLV, flat on abstain
(persistence HURTS on XLV, §4r), 2021-06 → 2026-07 (62 months overlap with the book).

| | value |
|---|---|
| corr(sleeve, ZION book 1x) | **-0.06** (in book down-months -0.05) |
| corr(sleeve, SPY) | +0.11 |
| sleeve alone | CAGR 31.5%, Sortino 9.08, MaxDD -3.5%, vol 9.8% |
| book 1x, same window | CAGR 21.1%, Sortino 7.30, MaxDD -3.6%, vol 8.6% |

| XLV sleeve overlay weight | book CAGR | book Sortino | book MaxDD |
|---|---|---|---|
| 0.0% | 21.09% | 7.30 | -3.56% |
| 2.5% | 21.93% | 7.57 | -3.40% |
| 5.0% | 22.78% | 8.03 | -3.25% |
| 7.5% | 23.63% | 8.30 | -3.16% |
| 10.0% | 24.48% | 8.59 | -3.08% |
| 15.0% | 26.21% | 9.28 | -2.91% |
| 20.0% | 27.96% | 9.50 | -2.74% |

Risk parity: a 5% risk share of the book ≈ **4.5%** notional; 10% ≈ 9.0%. Leverage rule on the sleeve's own stream
(0.9 × Sortino × 25% haircut) would allow ~6× — irrelevant, the book's gross cap governs. Admission gates as used for the silver micro:
G1 accuracy/LB (passes on the record), G2 concentration (62 months, no single year carries it — passes on the record), G3 |corr| < 0.30
(**−0.06, passes**), G4 book-Sortino lift (+0.27 at 2.5%, +0.73 at 5%, +1.29 at 10% — passes).

**Recommendation.** (1) **Admit as a 5% notional overlay sleeve** (the silver-micro precedent; ≈ 5% risk share; +0.73 book Sortino,
MaxDD improves) — two-sided, flat on abstain, inside the book's existing gross cap, no dynamic multiplier, no persistence. (2) **Real capital
0% until the forward tape resolves** — the house onboarding rule (as-issued tape before capital); the sleeve's 62-month record carries
full-record membership for 8 of its 49 calls and its Sortino is in-sample-tier. If the operator adopts ahead of evidence, as with UUP/India,
that is flagged on the record and 2.5% is the "homeopathic dose" precedent. (3) Scale to 10% only on a resolved tape (≥ 12 months) with the
book-Sortino lift holding forward. (4) Shorts kept at full size: they are the sleeve's strongest part (13 calls, 92%) — but 13 is the
evidence; a short-side haircut is the operator's call. Numbers here are a 62-month, one-sector, in-sample-selected sleeve; the tape decides.

### 4v. PORTFOLIO INTEGRATION — shadow, no live file touched (`hc_portfolio.py`, 13 Sep)

**Form (the silver-micro precedent):** HEALTH sleeve = 5% notional × position (integrated call, two-sided, flat on abstain) × weekly-book
lev, in its **own netting bucket** (XLV is a distinct instrument; it does not net against SPY), **FLAT while the dual throttle is stressed**
(Amendment 2 stress-exit applies to every risk sleeve). Position for month M applies to the weeks of month M. Universe gross = netted
gross × UNIVERSE_LEV 3.80 against the 6.0× cap; executed 2.5×.

| item | result |
|---|---|
| sleeve active weeks | 215 of 998 (2021-06 →); throttle stressed in 19% of them (book-wide 41%) |
| netted gross with HEALTH bucket | max 1.59× / mean 0.71× (unchanged max — the peak week predates the sleeve); house cap 2.0× never breached |
| universe gross @ 3.80× | max 6.05× — the pre-existing peak (1.59 × 3.8), not caused by the sleeve, which adds ≤ 0.06× in its active weeks |
| HEALTH vs US_EQ block, active weeks | same-side 142, opposing 45; max \|US_EQ + HEALTH\| 0.51 vs 0.41 without |
| universe 2020-05 → 2026-07 (75 mo), 1× | no sleeve: CAGR 22.42%, Sortino 7.68, MaxDD -3.56% |
| + HEALTH 5% **throttled** (adopted form) | CAGR 23.73%, Sortino **8.37**, MaxDD -3.22% |
| + HEALTH 5% unthrottled | CAGR 24.10%, Sortino 8.39, MaxDD -3.22% |
| at executed 2.5× | CAGR 62.9% → 67.2%, MaxDD −8.8% → −8.0% |
| throttle cost | 11 of 49 active months flattened, ≈ 0.4 pp CAGR — the price of the exogenous exit rule, kept |
| corr(sleeve, universe) | −0.09 |

**Shadow desk-ticket line (week 2026-09-11, thr 1.00, lev 1.19, $100k @ 2.5×):** HEALTH bucket XLV exposure +0.0595 → notional
$14,875 → **90 shares XLV LONG @ $165.36**; book netted gross 0.858× → 0.917×, executed 2.29×. Written to
`results/stage3_hc/shadow_netting_ledger_with_health.csv`; the live `netting_ledger.py`, desk ticket, tape resolver and LOCKED_BOOK_SPEC
are untouched — wiring them is a production change that needs explicit authorisation.

**Amendment draft (candidate A7 — NOT appended to LOCKED_BOOK_SPEC):** "HEALTH sleeve: 5% notional × integrated Health Care call
(type pulls > post-type cascade > pre-type tier-2; type authority on divergence) × lev; own bucket; two-sided; flat on abstain (no
persistence — persistence hurts XLV); flat while throttle < 1.0; no conviction multiplier. Real capital 0% until 12 resolved tape months;
2.5% if adopted ahead of evidence (flagged); 10% only on a resolved tape with the Sortino lift holding. Instrument XLV. Enters the universe
gross; cap unchanged."

## 5. Rulings (operator, 2026-09-13)

1. **Horizon: frozen at 1 month** for the sector system (3- and 6-month accuracies were drift; 1 month is the only horizon with independent bets).
2. **Act gate: DECISION convergence** (driver mandate). The sequential walk-forward bound is the **evidence channel**, reported beside it, never the gate.
3. **Anchor leg: CAPE10 and CAPE5 both stay in the pool**; the machinery chooses; both records reported.
4. **Survivorship: current-constituent universe accepted** for the sector CAPE (stated in §3); historical-membership rebuild deferred.
5. **Relative tag added**: every run carries two labels — absolute (sector direction) and **relative** (sign of sector return minus SPY return over the horizon). The relative label is the sector system's primary evidence of sector knowledge; the absolute label stays for the live call.

### 5.5 Why the relative label (recorded from the 13 Sep exchange)
Monthly 2016–2026: XLV–SPY correlation 0.72, beta 0.67, same-sign months 81%, XLV up 82% of SPY-up months and 19% of SPY-down months; XLV-minus-SPY up-rate 44%. The tailored cascade's 49 absolute calls re-scored: 67% right on XLV, 61% on SPY, **53% on XLV-versus-SPY**. Four fifths of an absolute sector call is a market call; once the market is stripped the call is a coin. Absolute-label accuracy is therefore judged against the sector's own up-rate; relative-label accuracy is judged against the **majority-class rate** of the acted months (a constant relative call's score), since the relative label is two-sided and can drift below 50%.

## 6. Status and what remains for Health Care

Done (all in this document): truncation review; data; sector CAPE/CAPEG; volume verdict; generic-pool sequential; full driver on the
tailored pool (absolute and relative); sequential sweep (absolute and relative) at 1/3/6; money test (absolute); anchor-only attempt;
rulings §5.

**Health Care state under the §5 rules (horizon 1 month, DECISION gate, both labels):**
- Absolute label: driver ACTS (62.4% test), sequential 67.3% vs 69.4% up-rate — drift; live call ABSTAIN. Money test: calls cost return vs holding.
- Relative label: driver ACTS (71.2% test, two-sided), sequential 59.3% vs 55.6% majority bar, LB95 46.0% (n 54) — WATCH; live call ABSTAIN.
- CAPEG: not selected by the Stage-3 pair cascade; single-predictor +4.1 absolute at 1 mo. **Stage-1 ORACLE typing (§4o): PE-against-Growth = the sector's most accurate anchor, 77.8% / LB 66% / +17.5 vs majority, two-sided; pending Sept-2026 call UP.**

Remaining before this sector is "done":
1. ~~Money test on the relative label~~ done (§4m).
2. ~~Forward tape~~ opened (§4n); Stage-1 type call added to the tape; monthly emission not yet scheduled (no launchd job — needs explicit authorisation per jobs inventory).
3. ~~Stage-1 type analysis~~ done (§4o); anchor selected = PE against Growth.
4. ~~Stage 3 on the selected anchor~~ done (§4p): pulls T2/T14/T17 (66% coverage, 87.8%), remainder cascade thin, MIRROR edge (upper bound), audit clean.
5. ~~Parallel-instrument convergence~~ done (§4q). ~~Integration~~ done (§4r): INTEGRATED instrument adopted by operator ruling — 49/62 @ 89.8%, LB 78.2%; September call UP.
6. ~~Engines + DECISION on the integrated signal~~ done (§4s): ACTS (LB 0.80 raw / 0.76 converged); shorts kept per arbitration rule.
7. ~~Operator verdict~~ → Health Care stands as solved (operator 13 Sep); the closing step is a standing dialectic with the operator, not a one-off sign-off.
8. ~~CASSANDRA~~ done (§4t): p50 ≈ $175–176 for 2026-10-01. ~~Sizing~~ done (§4u): 5% overlay recommended, 0% real capital until tape.
9. ~~Portfolio integration~~ done as SHADOW (§4v): own bucket, throttled, caps hold, universe Sortino 7.68 → 8.37; A7 draft; shadow ticket 90 XLV. Live wiring needs authorisation.
10. Next: the other eight sectors through §7; then the report graph; then the dashboard.
Then: apply the same runner to the other eight sectors, redraw the report graph, and only after that touch the dashboard.

## 7. THE SECTOR PROCEDURE — every step, in order, as run on Health Care (template for all sectors)

Run every step in this order; a sector is complete only when each step's table exists in its document. Constants are fixed across
sectors and never tuned per sector: horizon 1 month; dead zone 0.5 SD; pull bar WF > 67.5% & n ≥ 8; floors of 8; MIN_TRAIN 60;
design sample = first 40% of the anchor frame; DECISION gate 0.45; sizing static; admission by decorrelation.

| # | step | script | criterion / output | Health Care result |
|---|---|---|---|---|
| 0 | Truncation review of any prior board against `run_asset`; open the sector document | — | Addendum A checklist | 15 truncations + 18 mistakes logged |
| 1 | Data: outcome (panel month-start close), ETF price / volume / dividends, FRED drivers with publication lags, S&P 500 constituents | `sector_recipe.py`, `data/` | §1 table; every lag stated | §1 |
| 2 | Constituent PE / PEG snapshot (peer-basket medians only, never a backtest input) | `build_pe_lists.py` | sector medians | §4e |
| 3 | Sector earnings from SEC XBRL (as-issued, filing-date PIT); discrete legs RealPrice / E10 / g10; sector CAPE10, CAPE5, CAPEG | `hc_cape.py` | §3 definitions | CAPE10 33.6, g10 1.7%, CAPEG 19.6 |
| 4 | Stage-1 TYPE analysis: four anchors (P/E, PE/G, P/G, E/G) × two labels, ORACLE discipline, all 27 sub-types printed | `hc_oracle_types.py` | pick anchor: max edge vs majority, LB > 50%, n ≥ 60, two-sided, no single year | PE-vs-Growth 77.8% / LB 66% |
| 5 | Stage 3 on the anchor via `multiasset_pipeline`: 27-type table with zones → PULLS → tier cascade on the remainder → mirror → board → audit | `hc_stage3.py` | pulled iff WF > 67.5% & n ≥ 8 | T2/T14/T17 = 41/62 @ 87.8%; remainder 2 emits; audit clean |
| 6 | Pre-type, type-agnostic tier screen on all months (constant anchor) = second instrument | `hc_stage3_pretype.py` | its predictive tier only | CAPE10 velocity tier-2, 35 @ 91.4% |
| 7 | Dead-zone sensitivity (report only) | `hc_stage3_sd.py` | 0.25 … 1.0 | 0.5 at the peak |
| 8 | Parallel instruments: overlap / convergence / divergence, per-state next-month OOS with LB95 > 50% | `hc_convergence.py` | five joint states | §4q |
| 9 | Integration: type pull > post-type cascade > pre-type tier-2 on silent months; type authority on divergence; money test | `hc_integrated.py` | acted / acc / LB / by source / by year | 49/62 @ 89.8%, LB 78.2% |
| 10 | Abstention accounting: genuine abstentions vs exclusions by rule; what the silent months did | (in 9) | list every abstain month | 13 genuine (9 down), 13 warm-up |
| 10s | **SEQUENTIAL RE-DERIVATION (as in ZION; R7)**: refit steps 4–9 on the panel truncated at every decision month t (data ≤ t, outcome of t unknown) and take the call the runner would have issued at t — the pull set, the cascade folds, the tier admission (R3) and, in strict mode, the anchor (R1) all recomputed from data ≤ t; two modes side by side (fixed = anchor held as the one-time design choice; strict = anchor re-chosen monthly); variants `--embargo 3` (ZION training frontier t−3) and `--horizon 3` (reported only). The sequential record, not the ledger, is the evidence for steps 11 and 15 | `sector_sequential.py <TK> --mode fixed\|strict [--embargo 3] [--horizon 3]` → `results/sequential/<TK>_<mode>_tape.csv`; `portfolio_integration_seq.py` → `results/sequential/integration_compare.md` | acted / acc / LB95 / majority / edge per instrument, backtest v sequential; universe with the block, both | §14 |
| 11 | Engines (ODYSSEY, SANCTUARY) + DECISION on the integrated signal; arbitration keeps the two-sided call if it beats drift | `hc_decision.py` | ACTS iff LB > 0.45 | ACTS, LB 0.80; shorts kept |
| 12 | Relative-label tag: steps 4–5 rerun on sector-minus-SPY, reported beside absolute | `… relative` | majority-class benchmark | collapses to majority class |
| 13 | Current-month read on both instruments; forward tape row (as-issued) | `results/*_forward_tape.csv` | tape = evidence channel | Sept row: UP, both agree |
| 14 | CASSANDRA price at the outcome date: production band builder; if the analogue leg vetoes, cell-conditioned range (type / call) | `hc_cassandra.py` | direction-conditional; divergence gate withholds price only | p50 ≈ $175–176, band $171–184 |
| 15 | Sizing vs the book: corr, Sortino-lift grid, risk-parity weight, admission gates G1–G4; static, no conviction multiplier | `results/stage3_hc/sizing.json` | admit on decorrelation | 5% overlay; 0% capital until tape |
| 16 | Portfolio integration (shadow): own netting bucket, throttle stress-exit, gross caps at house / universe / executed leverage, universe with and without, shadow ticket, amendment draft | `hc_portfolio.py` | caps hold; Sortino lift | 7.68 → 8.37; 90 sh XLV shadow |
| 17 | Standing dialectic with the operator; document; next sector | this document | — | complete; next: XLK … XLU |

Not wired (needs authorisation): monthly tape emission job; netting-ledger / desk-ticket / tape-resolver / LOCKED_BOOK_SPEC changes.

## 8. MULTI-SECTOR RULES (declared 2026-09-13, before any second sector was run) and the parameterized runner

`sector_runner.py <TK>` executes steps 1–16 in order for one sector, each step asserting its output before the next starts, and writes
`results/<TK>/REPORT.md` with every table. Constants are fixed across sectors (§7). FRED drivers for all nine sectors were verified on
2026-09-13 (history, frequency, lag); one dead series (IPG2211A2S, utilities electric output) was replaced by IPUTIL.

- **R1 Anchor selection (step 4) — AMENDED 13 Sep after the Energy run (operator):** among the four anchors on EITHER label (absolute or
  relative), the highest edge over the majority-class rate, subject
  to LB95 > 50%, n ≥ 60, two-sided (long share 15–90%), and no calendar year with **≥ 8 calls** below 50% (**amended 14 Sep, operator, after
  Consumer Discretionary:** a year needs 8 calls to count, at either end of the walk-forward — the same sample floor the type-pull rule uses;
  the original ≥ 4 disqualified an 87-month anchor on a 7-call partial first year. Impact checked across the six sectors run: changes
  admission for Consumer Discretionary only; every other selected anchor unchanged). **Ill-conditioned growth:** an anchor
  whose denominator is the growth leg is ineligible if g10 sits at the 0.5%/yr floor in more than 20% of the anchor frame. No eligible
  anchor → the sector is TYPE-INELIGIBLE: reported, no Stage-3 verdict, no sizing. **A relative-label anchor makes the sector a LONG/SHORT
  PAIR sleeve (sector vs SPY):** every downstream step runs on the sector/SPY price ratio, the sleeve return is sector-minus-SPY, the SPY leg
  nets into the US_EQ bucket, and the ticket carries two legs.
- **R2 No-pull branch (step 5):** no type clears the pull bar → the type system is SILENT for that sector; the integrated instrument is the
  second instrument alone; the sector is flagged TYPE-SILENT, WATCH only, cannot be sized.
- **R3 Second instrument (step 6):** the tier(s) of the type-agnostic run whose sequential OOS accuracy has Wilson LB95 > 50% with n ≥ 8 —
  chosen by the rule, never by inspection. None qualifying → no second instrument.
- **R4 Selection caveat:** nine sectors × four anchors × full-record pull membership is many chances; the controls are the majority-class
  benchmark and the forward tape. Every sector result is a candidate until its tape resolves.
- **R5 Portfolio:** all sector sleeves share a 15% total GROSS cap and net per bucket; a sleeve failing |corr| < 0.30 against the book
  or adding no Sortino is NOT admitted (reported). Health Care's 5% counts against the cap.
- **R5p Pair rule (13 Sep, after Energy):** a relative-label sleeve is a long/short pair and costs two legs of gross. Every sector sleeve
  spends the same 5% of gross: single-leg = 5% notional; pair = **2.5% per leg** (2.5% sector, 2.5% SPY netted into US_EQ). The 15% cap
  counts gross legs. No universe-cap allowance: in any week where adding the sleeve would push universe gross above the 6.0× cap the
  sleeve is clipped to zero for that week, counted and reported. (Weeks where the base book itself already exceeds the cap are the
  book's, not the sleeve's — reported separately.)
- **R5s Short-only overlay rule (declared 14 Sep, operator, after Technology):** a sector instrument that ACTS but fails the R5 correlation
  gate **on its long side** (long-only stream corr ≥ +0.30 with the book, short-only stream corr ≤ +0.30) enters the book as a
  **SHORT-ONLY OVERLAY**: act on its short calls only, single leg, 5% notional × lev, own bucket, counted against the 15% sector cap.
  Overlay admission: ≥ 15 short calls on the record; short-call accuracy above the window's down-rate; no calendar year holding > 50% of
  the short calls; a Sortino lift on the universe. The overlay is hedge-class and therefore **unthrottled** (as the 2Y hedge and gold
  ballast are — a position that pays in stress is not flattened in stress); the throttled variant is reported beside it. 0% real capital
  until the tape resolves. A sector admitted as a full sleeve under R5 is unaffected; the rule fires only on an R5 correlation failure.
- **R6 Foreign / IFRS filers** (no us-gaap net income) are dropped from the sector CAPE and LISTED in the report — never silently.
- **R7 Sequential evidence (declared 14 Sep, operator: "as in ZION"):** the full-record ledger (`results/<TK>/integrated_ledger.csv`: pull
  set WF > 67.5% & n ≥ 8 measured over the whole record; anchor chosen by R1 on the whole post-design record) is the **backtest**. It is
  not admission evidence and its figures are labelled backtest wherever quoted. Admission (R1 anchor, DECISION, R5 sizing) and every
  number quoted for the block are taken from the **sequential re-derivation** (§7 step 10s, §14): each month's call refit on data ≤ t —
  the pull set, the cascade folds, the tier admission and, in strict mode, the anchor. This is ZION's own convention (pull membership
  in-fold trailing for backtests; full-record membership going-forward only). Modes reported side by side: **fixed** (anchor held as the
  one-time design choice) and **strict** (anchor re-chosen monthly by R1). Variants: `--embargo 3` (training frontier t−3, ZION's locked
  mechanic; the method's frontier is t−1 at horizon 1 — which frontier the sectors adopt is an open ruling) and `--horizon 3` (reported;
  the method's horizon stays 1 month). The forward tape is sequential by construction; the re-derivation is its historical counterpart.
- **Bearish leans:** the machinery is two-sided by construction (type direction = majority of same-type history; relative label = versus
  market). Each sector report states its up-rate and its long/short call mix, so a bearish lean is visible, not assumed.

- **R8 Integration priority (declared 2026-09-28, after the call-source study):** on the integrated instrument the priority is
  **pull > TIER > cascade**, not the original pull > cascade > tier. A genuine type-pull leads; on months with no pull the
  second-instrument tier (pre-type CAPE-velocity, sequential 76.2% / LB95 61.5%) takes precedence over a post-type cascade emission
  (sequential 55.0% / LB95 42.5%, below the 50 admission bar every other source must clear). The cascade survives only as the
  last-resort fallback on months neither the pull nor the tier covers. Chosen over deletion: the reorder (block Sortino 4.56 → 7.83
  at 2.5×, pull>tier>cascade) dominates deleting the cascade (5.79), because the cascade's marginal 55% still beats abstaining on the
  few months only it covers. Replay across the six admitted sectors: 22 call-months change source, pooled sequential accuracy
  64.9% → 70.9% (LB95 58.6 → 64.6). In-sample on 62 months, principled by the source LB95 ordering; the forward tape is the arbiter.
  **SHADOW SECTOR SYSTEM ONLY.** The live ZION book (weekly + monthly legs) is untouched: its sleeves use different machinery (weekly
  = 3-lens convergence; monthly = pull + one cascade cell, no pre-type tier) and were not swept — there is no tier in them to promote.

Order of sector runs: Energy first (the hard case — cyclical negative earnings), then the rest.

## 9. SECTOR RESULTS LOG (runner)

### 9.1 Energy (XLE) — 2026-09-13 — `sector_runner.py XLE` — verdict: **TYPE-INELIGIBLE, no instrument → WATCH-NONE, ABSTAIN**

Data: 21 constituents, all with earnings + shares after the predecessor-registrant merge (XOM ← CIK 34088, APA ← CIK 6769 — the SEC
ticker map points at successor registrants holding only recent filings; R6b below). Sector CAPE10 from 2014-03, 15 of 21 companies in the
aggregate (the rest have ten-year mean real earnings ≤ 0 — the loss years 2015–16 and 2020). Latest CAPE10 29.9, CAPE5 18.8. **Growth leg
ill-conditioned:** the log-linear trend is undefined in most months (a window year with aggregate losses), the declared block-mean fallback
(v2) is used in 84% of months and reads +42%/yr off a near-zero 2015–19 base; g10 is at the floor or undefined in 68% of the frame → the
three growth anchors are ineligible by R1.

| anchor | label | N | n | acc | LB95 | majority | edge | long | R1 outcome |
|---|---|---|---|---|---|---|---|---|---|
| PE | absolute | 9 | 81 | 56.8% | 46% | 55.6% | +1.2 | 79% | bad year |
| PE_G | absolute | 6 | 72 | 54.2% | 43% | 58.3% | -4.2 | 79% | ill-conditioned growth |
| P_G | absolute | 3 | 75 | 60.0% | 49% | 56.0% | +4.0 | 77% | ill-conditioned growth |
| E_G | absolute | 6 | 72 | 52.8% | 41% | 58.3% | -5.6 | 86% | ill-conditioned growth |
| PE | relative | 3 | 87 | 69.0% | 59% | 59.8% | +9.2 | 23% | edge<=0 |
| PE_G | relative | 12 | 66 | 48.5% | 37% | 59.1% | -10.6 | 26% | ill-conditioned growth |
| P_G | relative | 12 | 66 | 53.0% | 41% | 59.1% | -6.1 | 21% | ill-conditioned growth |
| E_G | relative | 12 | 66 | 53.0% | 41% | 59.1% | -6.1 | 30% | ill-conditioned growth |

Price-to-Earnings, the only conditioned anchor on the absolute label, scores 56.8% on 81 months against a 55.6% majority bar — a 1-point
edge, lower bound 46%, calendar years 2020 and 2024 at or below 50%. Not admitted. Stage 3 was run on the best-edge anchor (P/G) for the
record only: 7 of 27 types populated; **one type, T17 (flat/UP/flat), clears the pull bar on that record-only run (78.6%, n 14, LB 52%) —
NOT admitted under R1** (the runner first printed "PULLED NONE" because the branch blanks the admitted list; corrected to report the record);
the type-agnostic pre-type run emits nothing; second instrument none.

**Finding the rules did not anticipate — a bearish-relative anchor.** On the RELATIVE label (Energy minus SPY), Price-to-Earnings scores
**69.0% on 87 months, LB95 59%, majority-class 59.8%, edge +9.2, long share 23%** (i.e. mostly SHORT-relative calls), no calendar year
below 50% (2019 57% … 2026 88%). It clears every numeric threshold in R1; it is not admitted only because R1 was declared for the absolute
label. This is precisely the bearish lean the operator asked about: Energy's valuation anchor says nothing reliable about the sector's own
direction and something consistent about its under-performance versus the market. **Rule question for the operator (not decided here):**
extend R1 to admit a relative-label anchor, which would make Energy a long/short-versus-SPY sleeve rather than a directional one.
Integrated instrument: 0 acted of 74 scored (up-rate 55%, mean next-month +2.1% on the silent months — Energy's silence is not a down-month
signal, unlike Health Care's). Relative-label driver: ABSTAIN. DECISION: nothing to decide. CASSANDRA: statistical band only (one analogue),
reference p50 $65.64 for 2026-10-01 vs spot $64.77 — not an emitted price (no call). Not sized. Dead-zone sensitivity (report-only) shows a
pull appearing at SD 0.35 (10 months at 90%) and vanishing at 0.5 — exactly the per-sector tuning R1/§8 forbids.

**What Energy taught the template:** (1) successor-registrant CIKs silently truncate history — R6b predecessor map + the < 8-row listing;
(2) the growth leg needs a declared fallback for loss years, and even then can be ill-conditioned — R1's 20% rule did its job; (3) a sector
can be honestly empty at every layer; the runner reports it without inventing a call. Energy stays on the board as ABSTAIN with its tape open.

### 9.2 Energy (XLE) — re-run under the amended R1 (both labels) — 2026-09-13 — verdict: **ACTS as a LONG/SHORT PAIR (Energy vs SPY), 5% overlay recommended, 0% real capital until tape; current call ABSTAIN**

Anchor: **Price-to-Earnings on the RELATIVE label** (69.0% n 87, LB 59%, +9.2 vs majority, 23% long, no bad year) — the only eligible anchor.
Stage 3 on the sector/SPY ratio from 2019-10: 12 of 27 types populated; **pulled T2 (DN/DN/flat) and T14 (flat/flat/flat)** = 44 of 82 months at 75%;
remainder cascade 1 emission; audit clean. Pre-type run: no tier clears R3 → no second instrument. Integrated instrument = type only:

| item | Energy pair (sector − SPY), 2019-10 → 2026-07 |
|---|---|
| acted / scored | 45 / 82 (55%) |
| accuracy, LB95 | **75.6%, 61.3%** |
| calls | 1 long-relative, **44 short-relative** (short calls right 75%) |
| window up-rate / acted-months up-rate | 40% / 27% → majority-class bar on acted months **73.3%** → edge **+2.3** |
| by year | 2019 100%/3 · 2020 57%/7 · 2021 100%/3 · 2022 50%/4 · 2023 71%/7 · 2024 89%/9 · 2025 80%/10 · 2026 50%/2 |
| abstentions | 37 (21 up / 16 down; mean next-month excess +3.1% — Energy out-performs when the system is silent) |
| DECISION | integrated test 75.6% (n 45, LB 0.64) → **ACTS**; SANCTUARY agrees 17 / opposes 28 (integrated 75% where opposed); ODYSSEY 1 emission |
| money test (pair, no costs) | constant long pair −0.1% CAGR / Sortino 0.25 / MaxDD −48%; **integrated two-sided pair 13.2% / 1.06 / −17.2%**; SPY 16.6% / 1.30 / −23.8% |
| current (2026-08 row) | type T26 not pulled → **ABSTAIN**; tape row written (label = relative) |
| CASSANDRA | one analogue → reference only: statistical p50 ≈ −0.2% excess; no emitted price (no call) |

**Reading.** Energy's edge is one-sided and relative: the anchor says *when Energy will lag the market*, and almost never when it will lead.
Against the acted-months majority (a constant short-relative call on the same months) the lift is only +2.3 points; the value is in choosing
the months (acted months lag 73% of the time vs 60% for the window), not in beating a standing short. Sleeve Sortino 1.06 is far below Health
Care's 9.1; what carries it into the book is a correlation of +0.03 with the universe.

**Sizing (same tables as Health Care, §4u/§4v):**

| XLE overlay | book CAGR | book Sortino | book MaxDD |
|---|---|---|---|
| 0% | 22.17% | 7.60 | −3.56% |
| 2.5% | 22.57% | 8.00 | −3.49% |
| 5% | 22.98% | 8.52 | −3.42% |
| 10% | 23.79% | 8.98 | −3.42% |

| universe, 1x | CAGR | Sortino | MaxDD |
|---|---|---|---|
| no sleeve | 22.17% | 7.60 | −3.56% |
| + Energy 5%, throttled | 22.78% | 8.06 | −3.42% |
| + Energy 5%, unthrottled | 23.12% | 8.66 | −3.42% |

Admission: corr +0.03 (passes), Sortino lift passes → under **R5p the pair is sized at 2.5% per leg (5% gross)**: **0% real capital
until the tape resolves** (the same R4 caveat: pull membership full-record; 82-month window; one-sided).

**Tables at the R5p pair weight (final):**

| XLE pair overlay (per leg / gross) | book CAGR | book Sortino | book MaxDD |
|---|---|---|---|
| 0% | 22.17% | 7.60 | −3.56% |
| 1.25% / 2.5% | 22.36% | 7.72 | −3.52% |
| **2.5% / 5%** | 22.57% | **8.00** | −3.49% |
| 5% / 10% | 22.98% | 8.52 | −3.42% |

| universe, 1x | CAGR | Sortino | MaxDD |
|---|---|---|---|
| no sleeve | 22.17% | 7.60 | −3.56% |
| + Energy 2.5%/leg pair, throttled | 22.47% | 7.81 | −3.47% |
| + Energy 2.5%/leg pair, unthrottled | 22.64% | 8.08 | −3.47% |

**Portfolio finding — a pair sleeve costs two legs of gross.** At 5% per leg the universe gross peaked at 6.81× (above the 6.0× cap at
3.80×); at the R5p 2.5% per leg it peaks at 6.43× — still above, because the base book itself already touches 6.05× in its peak weeks.
With the sleeve on, universe gross exceeds the cap in 5 active weeks; one of them (2020-11-27) is the base book's own cap-touching week, so the R5p clip zeroes the sleeve in the **4 weeks it causes** (2021-12-10 to 2021-12-31); the base book's own 2 cap-touching weeks (2020-11-27, 2021-04-02) are the book's. House 2.0× cap holds (1.69×). Executed 2.5× → 4.2×, inside. Shadow ticket this week: zero (ABSTAIN).

### 9.2a Fixes that were required to run Energy (all applied to the runner, all sectors)
| # | defect found on the Energy run | consequence if unfixed | fix (where) |
|---|---|---|---|
| F1 | ticker→CIK map was never cached to disk (the Health Care pull held it in memory) | runner crashed at step 3 | fetch and cache `data/xbrl/ticker_cik.json` on first use (`s3_cape`) |
| F2 | SEC ticker map points XOM at a NEW registrant CIK (2115436) holding only 2026 filings; APA likewise (successor of Apache, CIK 6769) | Exxon (largest weight) and Apache silently absent from the sector CAPE | R6b `PREDECESSOR` map (XOM ← 34088, APA ← 6769), facts merged per period end, earliest filing wins; every constituent with < 8 annual rows is listed before a run; XBRL fetch validated with retry |
| F3 | FRED series IPG2211A2S (utilities electric output) returns 404 | Utilities run would have failed at step 1 | replaced by IPUTIL (`sector_recipe.FRED`); all other 20 sector series verified with history, frequency and lag |
| F4 | log-linear trend growth undefined when a window year's aggregate real earnings ≤ 0 (Energy 2015–16, 2020) | g10 NaN in 94% of months; three anchors blocked with no diagnosis | growth v2 block-mean fallback, version recorded per month; R1's ill-conditioned test counts floor + undefined months |
| F5 | type-ineligible sector aborted the run with no Stage-3 record, no second instrument, no tape | a "no" with no evidence table | continuation: Stage 3 on the best-edge anchor for the record (pulls not admitted), type marked silent, run continues to tape and CASSANDRA reference |
| F6 | report builder assumed attributes a blocked run never sets; pre-type month-level has no `tier` column when nothing emits; groupby crashed | runner crashed after the block | `getattr` defaults in `report`; column guards in steps 6, 8, 13; decision/sizing skip when nothing acted |
| F7 | `pd.to_datetime(Series).strftime` in the sizing step (needed `.dt.strftime`) | crash at step 15 on the first sector that reached sizing | one-line fix (`s15_s16_portfolio`) |
| F8 | the record-only branch blanked the admitted pull list, so the log printed "PULLED NONE" although T17 cleared the bar on the record | reader told no type cleared | log now prints the record-only pulls beside the (empty) admitted list |
| F9 | R1 admitted absolute-label anchors only; Energy's only edge is relative | a real bearish-relative edge would have been discarded | R1 amended to both labels (operator); relative anchors run the whole chain on the sector/SPY ratio as a pair sleeve |
| F10 | **Income-tag truncation (found on Consumer Discretionary, 13 Sep):** the parser took annual rows from the FIRST non-empty income tag (`NetIncomeLoss`, else `ProfitLoss`); many filers carry most of their history under the other tag or under `NetIncomeLossAvailableToCommonStockholdersBasic` (Booking: 3 rows vs 20+). Consistency check on the cached facts: **13 Health Care companies (e.g. Agilent 6→19 years, Cigna 3→10, Waters 4→13), 4 Energy (Apache 7→19) and 12 Financials (Mastercard 7→19, Interactive Brokers 7→18, Aon 11→19)** had truncated earnings in their sector CAPE | every sector CAPE built before the fix rests on partial earnings for those names; Health Care's own results (§3–§4v) are affected and must be re-verified | union of the three income tags per period end (`annual_union`); third tag added to the pull; **re-verification runs of XLV, XLE, XLF launched under the corrected parser; their §9 entries and §3–§4 are provisional until the re-runs are compared** |
| F11 | Stage 3 read the sector's CAPE legs from the ORIGINAL Health Care file name for XLV rather than the runner's own output (path routing) | a re-run of Health Care would have typed on the old CAPE | the runner's CAPE file is routed to the legs builder on every run, not only exclusion runs |
| F12 | R5 admission tested the Sortino lift on the unthrottled book grid; Consumer Discretionary passed there (+0.13) while the THROTTLED universe — the adopted form — fell (−0.03) | a sleeve admitted that lowers the book as actually run | R5 amended: admission requires a Sortino lift on the throttled universe |

### 9.2b Relative anchor detail — Energy, Price-to-Earnings on the sector-minus-SPY label
ORACLE record (§4o mechanics, both legs cycle/CPI-adjusted discretely, ratio = RealPrice / E10, sub-types = sign triple of the N-month change):
N chosen **3** (design sweep N3: 60%, N6: 54%, N9: 55%, N12: 46%); walk-forward n **87**, accuracy **69.0%**, LB95 **59%**, up-rate of acted months 40.2%
→ majority-class **59.8%**, edge **+9.2**, long share **23%** (i.e. 77% of calls are short-relative); by year 2019 57%/7 · 2020 58%/12 · 2021 58%/12 · 2022 67%/12 · 2023 75%/12 · 2024 75%/12 · 2025 75%/12 · 2026 88%/8; no calendar year below 50%; ill-conditioned no.
On the absolute label the same anchor reads 56.8% (n 81, LB 46%, two bad years) — Energy's P/E has relative content only.

Stage 3 on the relative outcome (`multiasset_pipeline`, H = 1, scoring from 2019-10), all 27 types:

| T | ratio/num/den | n | WF % | LB | UB | zone | |
|---|---|---|---|---|---|---|---|
| T1 | DN/DN/DN | 2 | 50.0 | 9.5 | 90.5 | COIN-TOSS |  |
| T2 | DN/DN/flat | 18 | 72.2 | 49.1 | 87.5 | COIN-TOSS | PULLED |
| T3 | DN/DN/UP | 0 | — | — | — | empty |  |
| T4 | DN/flat/DN | 0 | — | — | — | empty |  |
| T5 | DN/flat/flat | 2 | 100.0 | 34.2 | 100.0 | COIN-TOSS |  |
| T6 | DN/flat/UP | 1 | 100.0 | 20.7 | 100.0 | COIN-TOSS |  |
| T7 | DN/UP/DN | 0 | — | — | — | empty |  |
| T8 | DN/UP/flat | 0 | — | — | — | empty |  |
| T9 | DN/UP/UP | 0 | — | — | — | empty |  |
| T10 | flat/DN/DN | 0 | — | — | — | empty |  |
| T11 | flat/DN/flat | 0 | — | — | — | empty |  |
| T12 | flat/DN/UP | 0 | — | — | — | empty |  |
| T13 | flat/flat/DN | 0 | — | — | — | empty |  |
| T14 | flat/flat/flat | 26 | 76.9 | 57.9 | 89.0 | PREDICTIVE | PULLED |
| T15 | flat/flat/UP | 6 | 66.7 | 30.0 | 90.3 | COIN-TOSS |  |
| T16 | flat/UP/DN | 0 | — | — | — | empty |  |
| T17 | flat/UP/flat | 5 | 60.0 | 23.1 | 88.2 | COIN-TOSS |  |
| T18 | flat/UP/UP | 1 | 100.0 | 20.7 | 100.0 | COIN-TOSS |  |
| T19 | UP/DN/DN | 0 | — | — | — | empty |  |
| T20 | UP/DN/flat | 0 | — | — | — | empty |  |
| T21 | UP/DN/UP | 0 | — | — | — | empty |  |
| T22 | UP/flat/DN | 1 | 0.0 | 0.0 | 79.3 | COIN-TOSS |  |
| T23 | UP/flat/flat | 0 | — | — | — | empty |  |
| T24 | UP/flat/UP | 0 | — | — | — | empty |  |
| T25 | UP/UP/DN | 5 | 60.0 | 23.1 | 88.2 | COIN-TOSS |  |
| T26 | UP/UP/flat | 14 | 64.3 | 38.8 | 83.7 | COIN-TOSS |  |
| T27 | UP/UP/UP | 1 | 100.0 | 20.7 | 100.0 | COIN-TOSS |  |

Pulled: T2 (DN/DN/flat) and T14 (flat/flat/flat). Both are "no change" or "falling" configurations of the sector's own valuation — the
sector lags the market when its P/E is flat or falling with real price and smoothed earnings flat or falling, i.e. a de-rating that the
market does not share. The two divergence-free states (no second instrument) mean the integrated instrument is the type system alone.

### 9.3 Financials (XLF) — 2026-09-13 — `sector_runner.py XLF` — verdict: **ACTS (long-drift character), 5% overlay recommended, 0% real capital until tape; current call UP**

**Data and pre-run review.** 76 constituents; two successor registrants caught by the thin-history listing and mapped before acceptance
(BlackRock ← CIK 1364742, BlackRock Finance 2009–2023; Apollo ← CIK 1411494, Apollo Asset Management 2011–2022); Erie Indemnity dropped
and listed (no annual share count in its XBRL: diluted/basic/dei all absent — 0.5% of the sector). Sector CAPE10 from 2014-03, 73 of 75
companies in the aggregate; latest CAPE10 18.5, CAPE5 16.4, g10 4.3%/yr (v1), CAPEG 4.3; growth v2 fallback in 32% of months (2008-era losses
inside early windows), at floor/undefined 8% → growth anchors conditioned but not selected.

**Anchor (R1, both labels): Price-to-Earnings, ABSOLUTE label** — 65.9% on 85 months, LB95 55%, +8.2 over the 57.6% majority bar, 85% long,
no bad year (2019 80% … 2026 75%). Every other anchor fails (growth anchors: negative or sub-threshold edge, bad years; every relative-label
anchor ≤ 52%). Financials has no relative-label content: its P/E says something about its own direction, nothing about it versus the market
— the mirror image of Energy.

**Stage 3 (H = 1, from 2019-10):** 12 of 27 types populated; **pulled T25 (UP/UP/DN, 76.9%, n 13) and T26 (UP/UP/flat, 83.3%, n 18)** = 32
months; remainder cascade 15 emissions; audit clean. Pre-type run: tier 2 qualifies (R3: 22 months, 73%, LB 52%) → second instrument.
Dead-zone sensitivity: pulls present at every SD (report-only).

| integrated instrument (type > cascade > tier-2) | value |
|---|---|
| acted / scored | 55 / 82 (67%) |
| accuracy, LB95 | 69.1%, 56.0% |
| by source | type pulls 31 @ 80.6% · post-type cascade 15 @ 53.3% · second instrument 9 @ 55.6% |
| calls | 51 long (months up 70.6%), 4 short (50%) → **93% long** |
| **acted-months up-rate** | **69.1% = the accuracy** → zero edge over being long in those months; window up-rate 58.5% → the selection content is +10.6 points |
| by year | 2019 100%/2 · 2020 75%/8 · 2021 70%/10 · 2022 62%/8 · 2023 83%/6 · 2024 62%/8 · **2025 44%/9** · 2026 100%/4 |
| abstentions | 27 (10 up / 17 down, mean next-month −2.5%) — silence is a down signal, as for Health Care |
| DECISION | integrated test 69.1% (n 55, LB 0.58); SANCTUARY-converged 72.7% (n 33, LB 0.59) → **ACTS**; SANCTUARY opposes 22 (integrated 64% there); ODYSSEY 6 emissions |
| current (2026-08 row) | **UP** — T25, a pulled type; second instrument silent |
| CASSANDRA (2026-10-01) | one analogue → cell-conditioned: call-conditioned p50 **$59.61 (+4.2%)** vs spot $57.20; statistical reference $57.86 |

**Reading.** Financials is the S&P pattern inside a sector: the anchor is real (65.9% vs 57.6% on the type table, two-sided enough to pass R1)
but the Stage-3 instrument it produces is long in 93% of its calls and its accuracy equals the up-rate of the months it chose. What it earns
is selection — it is long in months that rise 69% of the time against 59% for the window, and silent in months that fall — not direction.
2025 is the weak year (44% of 9). The pulled types T25/T26 are "valuation and price both rising" configurations: momentum in the sector's own
P/E. The post-type cascade (53%) and the second instrument (56%) add coverage at near-coin accuracy; under R4 the two extra layers are the
part most likely to be noise here.

**Sizing (§4u tables):** corr(sleeve, book) **+0.22** (passes the 0.30 gate, but the closest yet — a long-biased sector sleeve correlates with
the SPY/QQQ block, as anticipated in §8), sleeve Sortino 4.44.

| XLF overlay | book CAGR | book Sortino | book MaxDD |
|---|---|---|---|
| 0.0% | 22.17% | 7.60 | -3.56% |
| 2.5% | 22.93% | 7.74 | -3.60% |
| 5.0% | 23.70% | 7.95 | -3.65% |
| 10.0% | 25.25% | 8.40 | -3.74% |

| universe, 1x | CAGR | Sortino | MaxDD |
|---|---|---|---|
| no sleeve | 22.17% | 7.60 | −3.56% |
| + Financials 5%, throttled | 23.35% | 7.98 | −3.66% |
| + Financials 5%, unthrottled | 24.07% | 8.07 | −3.66% |

Sortino lift +0.38 at 5% with MaxDD slightly worse (−3.56 → −3.66) — admitted under R5, **5% overlay recommended, 0% real capital until the
tape resolves**; house gross 1.69× holds; universe 6.43× at 3.80× = the base book's own peak weeks. Shadow ticket this week: **260 sh XLF long**
($14,875 at $100k @ 2.5×). **Berkshire sensitivity:** §9.3a.

### 9.3a Berkshire sensitivity (`sector_runner.py XLF --exclude BRK-B`, report-only; the standard run is the system)

| | standard (with BRK) | ex-Berkshire |
|---|---|---|
| sector CAPE10 / CAPE5 / g10 / CAPEG (latest) | 18.5 / 16.4 / 4.3% / 4.3 | 21.9 / 19.5 / 3.9% / 5.7 |
| anchor selected | P/E absolute | P/E absolute (same) |
| anchor record | 65.9% n 85, LB 55%, +8.2 | 64.7% n 85, LB 54%, +7.1 |
| pulled types | T25, T26 (32 months) | T25, T26 (33 months) |
| second instrument | tier 2 (22 @ 73%) | tier 2 (29 @ 69%) |
| integrated | 55/82, 69.1%, LB 56.0%, acted up-rate 69.1%, 93% long | 59/82, 72.9%, LB 60.4%, acted up-rate 67.8%, 88% long |
| DECISION | ACTS (LB 0.58) | ACTS (LB 0.63) |
| current call | UP (T25) | UP (T26) |
| corr with book / sleeve Sortino / book Sortino at 5% | +0.22 / 4.44 / 7.95 | +0.27 / 4.56 / 7.88 |
| universe MaxDD at 5% throttled | −3.66% | −3.94% |

**Reading.** Berkshire's mark-to-market earnings depress the sector CAPE by about 3 points (18.5 vs 21.9) but change nothing structural:
the same anchor, the same two pulled types, the same second instrument, the same call, the same verdict. Ex-Berkshire the instrument acts
on four more months and its accuracy rises above its acted up-rate by 5 points (72.9 vs 67.8) — the only place a two-sided reading appears —
at the cost of a higher correlation with the book (+0.27, nearer the gate) and a worse drawdown. Verdict: **keep Berkshire in** (the sector
as the index defines it; the accounting noise is absorbed by the ten-year average); log the sensitivity; no rule change.

### 9.4 Consumer Discretionary (XLY) — 2026-09-13 — `sector_runner.py XLY` (corrected parser, F10) — verdict: **TYPE-INELIGIBLE → WATCH-NONE, ABSTAIN**

Predicted beforehand (from the up-rate table) as the likeliest remaining sector to produce shorts and the surest to fall with the market
(fell in 90% of SPY-down months, 100% of SPY < −3% months). Data: 47 constituents, all with earnings and shares, no predecessor issue
(Booking's history was the F10 case — 3 rows under one tag, 20+ under another — now unioned). Sector CAPE10 from 2014-03, 42 of 47 in the
aggregate; latest CAPE10 **46.2**, CAPE5 36.3, g10 9.2%/yr (v1), CAPEG 5.0 — the richest sector CAPE on the board so far.

Anchors: Price-to-Earnings on the absolute label scores **65.5% on 87 months, LB 55%, +12.6 over the 52.9% majority bar, 64% long** — the
strongest raw edge of any anchor yet — but fails R1 on the calendar-year test (2019 43%/7, 2020 67%/12, 2021 75%/12, 2022 75%/12, 2023 67%/12, 2024 67%/12, 2025 67%/12, 2026 50%/8). On the first pass (truncated earnings for
Booking and others) the same anchor had passed; the corrected earnings moved one year below 50%. Every relative-label anchor fails by a
wide margin: Discretionary lags SPY 61–62% of months, so the majority-class bar is 61–62% and no anchor beats a standing short-relative.

Stage 3, record only (PE): 14 of 27 types populated; **three types clear the pull bar on the record — T2 (DN/DN/flat), T14 (flat/flat/flat)
and T22 (UP/flat/DN)** — not admitted (R1). T2 is the same falling-valuation configuration that gave Health Care its shorts, so the
short content the up-rate table pointed to does exist in the type grammar; it is not admitted because the anchor as a whole fails the year
test. No pre-type tier qualifies; nothing acts; DECISION has nothing to decide; CASSANDRA reference only (statistical p50 $115.84 vs spot
$114.59, no analogue, no call). Not sized. Silent months: 39 up / 36 down, mean +1.3% — silence carries no down signal here.

**Reading.** Consumer Discretionary is the clearest R4 case so far: a 12.6-point anchor edge that does not survive the year test, a short
type that exists but cannot be admitted, and a relative record that no anchor can beat. It stays on the board as ABSTAIN with its tape
open. If the tape shows T2 firing and resolving down over the next year, that is the evidence the rules require before anything changes.
The forecast of a "mostly short" sector was directionally right about the grammar and wrong about admission.

### 9.4a Consumer Discretionary under the amended R1 (eight-call years) — 2026-09-14 — verdict: **ACTS, two-sided, ADMITTED as a 5% sleeve; current call ABSTAIN**

Anchor: **Price-to-Earnings, absolute** — 65.5% on 87 months, LB 55%, +12.6 over the 52.9% majority bar, 64% long; the seven-call 2019 year no
longer counts (§8 R1 as amended). Same data as §9.4 (corrected parser; CAPE10 46.2).

**Stage 3 (H = 1, from 2020-05):** 14 of 27 types populated; **pulled T2 (DN/DN/flat, 85.7%, n 14 — all 14 calls SHORT), T14 (flat/flat/flat,
78.6%, n 14 — all long), T22 (UP/flat/DN, 87.5%, n 8 — all long)** = 36 months; no remainder emissions; no second instrument (R3); audit clean.

| integrated instrument (type pulls only) | value |
|---|---|
| acted / scored | 36 / 75 (48%) |
| accuracy, LB95 | **83.3%, 68.1%** |
| calls | 22 long (right 81.8%), **14 short (right 85.7%)** — 61% long |
| acted-months up-rate → majority bar | 55.6% → **edge +27.8** (the largest two-sided edge on the board; window up-rate 52%) |
| by year | 2020 75%/4 · 2021 100%/6 · 2022 86%/7 · 2023 100%/3 · 2024 78%/9 · 2025 80%/5 · 2026 50%/2 |
| abstentions | 39 (19 up / 20 down, mean +1.9%) — silence is neutral here |
| DECISION | 83.3% (n 36, LB 0.71); SANCTUARY-converged 89.5% (n 19, LB 0.73) → **ACTS**; SANCTUARY opposes 17 (integrated 76% there); ODYSSEY 6 |
| current (2026-08 row) | **ABSTAIN** — T1 (DN/DN/DN), not a pulled type |
| CASSANDRA | no analogue (VETO); no call → statistical reference only ($115.84 vs spot $114.59) |

**Sizing:** corr(sleeve, book) **+0.01**, sleeve Sortino 2.82 (CAGR 25.1%, MaxDD −6.2%), throttled-universe lift **+0.47** → **admitted, 5% notional,
0% real capital until the tape**. Cap-clip 3 weeks.

| XLY overlay | book CAGR | book Sortino | book MaxDD |
|---|---|---|---|
| 0% | 22.42% | 7.68 | −3.56% |
| 2.5% | 23.12% | 7.95 | −3.33% |
| 5% | 23.83% | 8.13 | −3.18% |
| 10% | 25.25% | 8.56 | −2.94% |

| universe, 1x | CAGR | Sortino | MaxDD |
|---|---|---|---|
| no sleeve | 22.42% | 7.68 | −3.56% |
| + Consumer Disc 5%, throttled | 23.64% | 8.15 | −3.13% |
| + Consumer Disc 5%, unthrottled | 24.23% | 8.32 | −3.13% |

**Reading.** This is the second genuinely two-sided sector after Health Care, and its short cell is the same configuration (T2: valuation
and price falling, growth flat) — the de-rating signature — right 12 of 14 times. Coverage is lower than Health Care's (48% vs 82%) and the
window is 36 acted months, so the bound is wider; the edge over the acted-months majority (+27.8) is the largest on the board because the
acted months are nearly balanced (56% up) rather than drift-dominated. Its correlation with the book is zero: the sector's beta to the market
(it fell in 90% of SPY-down months) is exactly what the short calls neutralise. **Supersedes §9.4's verdict.** Shadow ticket this week: none.

### 9.5 Technology (XLK) — 2026-09-14 — `sector_runner.py XLK` — verdict: **ACTS, two-sided, NOT ADMITTED to the book (R5 correlation gate); current call DOWN**

**Data.** 73 constituents, all with earnings and shares; no predecessor issue; Qnity (3y) and Sandisk (4y) excluded by the seven-year rule
and listed (2025 spin-offs). Sector CAPE10 from 2014-03, 67 of 73 in the aggregate; latest **CAPE10 72.7**, CAPE5 59.4, g10 4.7%/yr (v1),
CAPEG 15.4 — by far the richest sector CAPE (Health Care 32.5, Consumer Discretionary 46.2, Financials 18.0, Energy 30.3).

**Anchor (R1, both labels): Price-to-Earnings, absolute** — 74.7% on 87 months, LB95 65%, +10.3 over the 64.4% majority bar, 71% long, no
year below 50% (2019 86% … 2025 58%, 2026 50% of 8). The growth anchors fail (PE-vs-Growth −1.9; Price-to-Growth +3.2 with a bad year);
the relative label carries a near-miss (PE-vs-Growth relative 60.3%, +9.5, LB 48%).

**Stage 3 (H = 1, from 2020-05):** only **5 of 27 types populated** — the smoothed-earnings leg reads "flat" in every populated type
(a ten-year mean steps once a year; its 3-month change rarely leaves the dead zone), so Technology's grammar runs on the ratio and price
legs alone. **Four pulled: T2 (DN/DN/flat, 71.4%, n 21), T14 (flat/flat/flat, 68.0%, n 25), T23 (UP/flat/flat, 100%, n 10), T26
(UP/UP/flat, 80.0%, n 15)** = 72 of 75 months. Second instrument: tier 2 (45 @ 80%, LB 66%).

| integrated instrument | value |
|---|---|
| acted / scored | **74 / 75** (the sector is almost never silent) |
| accuracy, LB95 | 75.7%, 64.8% |
| calls | 53 long (right 77.4%), **21 short (right 71.4%)** |
| acted-months up-rate → majority bar | 63.5% → **edge +12.2** (genuinely two-sided) |
| by year | 2020 88% · 2021 92% · 2022 67% · 2023 82% · 2024 75% · **2025 58%** · 2026 71% |
| DECISION | 75.7% (n 74, LB 0.67); SANCTUARY-converged 78.4% (n 51, LB 0.68) → **ACTS**; SANCTUARY opposes 23 (integrated 70% there); ODYSSEY 8 |
| current (2026-08 row) | **DOWN** — T2 (DN/DN/flat), a pulled type; second instrument says UP → divergence → type authority (§4r) → **DOWN**; shadow −79 sh XLK |
| CASSANDRA (2026-10-01) | first sector with an analogue band: 16 analogues, pool p50 +3.0% ($189.22); call-conditioned DOWN p50 **$176.41 (−3.9%)**; the pool's lean (up) contradicts the call by > 4%/mo → **divergence gate: price withheld, reference only; the call stands** |
| sizing (R5) | corr(sleeve, book) **+0.52 → NOT ADMITTED**; sleeve Sortino 4.77; the book would have gained (+0.68 throttled universe) but the decorrelation gate is the rule |

**Reading.** Technology is the first sector where the type system is both two-sided and nearly always on: 21 shorts at 71%, ten of them in
2022. Its 2025 weakness (58%) is the AI-melt-up year, when the "valuation falling" cells misread a sector that kept rising. It fails
admission for exactly the reason §8 anticipated — its long side is the book's own SPY/QQQ block (long-only stream corr +0.71).

**Short-only decomposition (report-only, candidate for a rule):** the short-only stream has corr **−0.32** with the book (hedge-shaped),
earns +2.47%/mo in the book's 21 down-months, and lifts the book more than any admitted sleeve (5% → Sortino 7.68 → **8.13**, MaxDD −3.56 →
−3.32); the long-only stream does the opposite (corr +0.71, book Sortino falls). A two-sided sector instrument whose long side duplicates
the book and whose short side hedges it argues for a **short-only overlay rule** (act on the sector's short calls only, sized as a sleeve).
Not adopted here: it is a decomposition noticed on the record; it needs a declared rule and a tape. Logged as an open R5 question.

### 9.5a Technology under R5s — SHORT-ONLY OVERLAY ADMITTED (`sector_runner.py XLK`, 14 Sep)
Trigger: long-only stream corr **+0.71**, short-only stream corr **−0.32**. Admission: 21 short calls at **71.4%** against a window down-rate of
36%; largest year holds 48% of them (2022: 10) ≤ 50%; universe lift +0.57.

| XLK short-only overlay | book CAGR | book Sortino | book MaxDD |
|---|---|---|---|
| 0% | 22.42% | 7.68 | −3.56% |
| 2.5% | — | 8.06 | −3.44% |
| **5%** | — | **8.13** | **−3.32%** |
| 10% | — | 8.21 | −3.08% |

| universe, 1x | CAGR | Sortino | MaxDD |
|---|---|---|---|
| no overlay | 22.42% | 7.68 | −3.56% |
| + Technology short-only 5%, **unthrottled (declared form)** | 23.32% | **8.26** | −3.28% |
| + Technology short-only 5%, throttled (reported) | 23.09% | 8.19 | −3.28% |

Overlay stream alone: CAGR 10.6%, Sortino 1.11, MaxDD −10.7% — a hedge, not a return engine; its value is the −0.32 correlation and
+2.5%/mo in the book's down-months. **Recommendation: admit as a 5% short-only overlay, unthrottled, 0% real capital until the tape.**
Current call DOWN (T2) → the overlay is ON this week: shadow **−79 sh XLK** ($14,875 short at $100k @ 2.5×). The full two-sided sleeve
(§9.5) stays not admitted; its long calls are informational.

### 9.6 Utilities (XLU) — 2026-09-14 — `sector_runner.py XLU` — verdict: **TYPE-INELIGIBLE → WATCH-NONE, ABSTAIN** — with a rule finding

**Data.** 31 constituents, all with earnings and shares; Constellation (6y, 2022 spin-off) excluded and listed. Sector CAPE10 from 2014-03,
28 of 31 in the aggregate; latest CAPE10 25.1, CAPE5 24.4, g10 6.9%/yr, CAPEG 3.6. No loss years, no growth fallback used.

**Anchors.** Price-to-Growth absolute scores **62.5% on 72 months, LB 51%, +9.7 over the majority bar, 68% long, no bad year** and
PE-vs-Growth absolute 61.1%, +8.3, LB 49.6% — both are ruled **ill-conditioned by R1** because g10 sits at or below the 0.5%/yr floor in
40% of the frame (8% undefined). Price-to-Earnings absolute 58.1%, LB 47.6% (fails the bound). Relative anchors: Price-to-Growth
61.1%, +9.7 but ill-conditioned; nothing else clears.

**The rule finding — CORRECTED before the ink dried.** A first draft of this paragraph claimed Utilities' growth was "defined and positive"
and that the 0.5%/yr floor was clipping a low-growth sector; the numbers computed in the same step say otherwise. **g10 is ≤ 0 in 40% of the
frame** (year medians: 2015 −3.3%, 2016 −5.9%, 2017 −9.4%, 2018 −4.1%, 2019 −1.0%; positive only from 2020: 1.2 → 6.9%); 0% of months
sit in the low-positive band (0, 0.5]. Utilities' real ten-year earnings trend was genuinely negative for five years (windows spanning the
2008–2019 earnings decline), which is exactly the pathology R1's ill-conditioned test exists to catch. **The floor amendment is withdrawn;
R1 stands as declared.** For comparison: Health Care, Technology, Financials 0% of months at or below the floor; Consumer Discretionary 7%;
Energy 56% (the other genuine case). Mistake logged as B19 in Addendum A.

**Stage 3, record only (P_G):** 7 of 27 types; **T11 (flat/DN/flat) clears the pull bar on the record — 72.7% on 22 months, LB 52%, and every
one of its 22 calls is SHORT** (ratio flat, real price falling, growth flat → the sector keeps falling) — not admitted (R1). No second instrument; nothing acts; relative driver STANDDOWN; CASSANDRA 11 analogues, reference p50 $42.55 vs spot
$42.56 (no call). Not sized. Silent months 35 up / 36 down (up-rate 49%: Utilities is the one sector with no drift to capture).

**Reading.** Utilities is a coin on its own direction (49% up-months), and its growth leg is ill-conditioned for the same reason Energy's is:
a multi-year decline in real earnings inside the ten-year windows. The 62.5% anchor and the 73% short type on the record are real, but they
rest on a CAPEG that was undefined or clipped for two fifths of the history; under the rules they stay on the record. ABSTAIN on the board,
tape open. The forward tape is the only thing that can promote T11.

### 9.7 Materials (XLB) — 2026-09-14 — `sector_runner.py XLB` — verdict: **ACTS, mostly SHORT, NOT ADMITTED (throttled-universe lift ≤ 0); current call ABSTAIN**

**Data.** 25 constituents (copper re-admitted to the pool for this sector); Smurfit Westrock (4y) and CRH (5y) excluded by the seven-year rule
and listed. Sector CAPE10 from 2014-03, 21 of 25 in the aggregate; latest CAPE10 29.0, CAPE5 23.9, g10 6.6%/yr, CAPEG 4.4 — but the growth leg is
ill-conditioned in 57% of the frame (v2 fallback 40%, undefined 16%; cyclical earnings), so all three growth anchors are ruled out.

**Anchor (R1, both labels): Price-to-Earnings, absolute** — 61.6% on 86 months, LB 51%, +7.0 over the 54.7% majority bar, 67% long, no bad year.
Relative label: nothing clears (P/E relative 51.9%, +1.2).

**Stage 3 (H = 1, from 2020-05):** 14 of 27 types populated; **one pulled — T2 (DN/DN/flat, 68.8%, n 16, all SHORT)**, the de-rating cell again;
remainder cascade 9 emissions (77.8%); no second instrument. Integrated:

| integrated instrument | value |
|---|---|
| acted / scored | 25 / 75 (33%) |
| accuracy, LB95 | 72.0%, 52.4% |
| calls | 6 long (right 83%), **19 short (right 68%)** → **76% short — the first mostly-short sector on the absolute label** |
| acted-months up-rate → majority bar | 44% → 56% → edge **+16.0** |
| by year | 2021 67%/3 · 2022 67%/6 · 2023 100%/1 · 2024 75%/4 · 2025 62%/8 · 2026 100%/3 |
| abstentions | 50 (31 up / 19 down, mean +2.2%) — the sector rises when the system is silent |
| DECISION | 72.0% (n 25, LB 0.56); SANCTUARY-converged 88.9% (n 9, LB 0.62) → **ACTS** |
| current (2026-08 row) | **ABSTAIN** (T14, not pulled) |
| CASSANDRA | no analogue; no call; statistical reference $52.47 vs spot $52.07 |
| sizing | corr(sleeve, book) **−0.12** (passes); sleeve Sortino 1.24; throttled-universe lift **−0.05 → NOT admitted (R5)**; unthrottled +0.03 |

**Precious-metals overlap (operator question).** Structurally, Materials' monthly returns correlate 0.21 with gold, 0.33 with silver, 0.41 with
gold miners and **0.72 with copper miners**; net of SPY beta the residual correlates +0.25 gold, +0.38 miners, +0.43 copper — an industrial-metals
sector with a mild gold-miner tilt (Newmont, Freeport), not a precious-metals proxy. Against the metals calls already made: the monthly Gold
sleeve acts in 11 of the 75 months (all long) and agrees with Materials in **1 of the 7** months both act; the Silver sleeve acts in 18, agrees in
2 of 4; the book's silver micro agrees in 3 of 10. Return-stream correlations 0.00 (gold) and +0.01 (silver); Materials' calls carry no
information about the next month's gold or silver return (+0.03, +0.04). **No correlation with the precious-metals guesses** — the Materials
instrument is independent of them, and mostly opposed in sign (it is short when they are long). The book's 7.5% gold ballast is always on and is
not a guess.

**Rule observation (not applied).** Materials passes the correlation gate and fails only the throttled lift: its short calls pay in stress, and
the throttle flattens risk sleeves in stress, so the throttled form loses what the instrument is for (unthrottled lift +0.03). R5s treats
short-only *overlays* as hedge-class and unthrottled, but it triggers only on a correlation failure. A mostly-short sleeve that passes
correlation falls between the rules. Logged as an open question; the lift is marginal either way, so Materials stays not admitted.

**Reading.** Materials is a thin, mostly-short instrument: one short cell on 16 months at 69%, a cascade adding 9, and 50 silent months in which
the sector rose. It is on the board as ABSTAIN with its tape open; the T2 cell is the same de-rating configuration that carries Health Care's,
Consumer Discretionary's and Technology's shorts.

### 9.8 Industrials (XLI) — 2026-09-14 — `sector_runner.py XLI` — verdict: **ACTS, two-sided, ADMITTED as a 5% sleeve; current call UP (thin source, flagged)**

**Data.** 83 constituents; Honeywell Aerospace (HONA, 2025 spin-off, no annual filing yet) dropped and listed; Ferguson, GE Vernova, Veralto and
FedEx Freight (3–5 years) excluded by the seven-year rule and listed. Sector CAPE10 from 2014-03, 75 of 82 in the aggregate; latest CAPE10 31.9,
CAPE5 31.8, g10 2.7%/yr, CAPEG 12.0; growth leg ill-conditioned in 43% of the frame → the three growth anchors ruled out.

**Anchor (R1, both labels): Price-to-Earnings, absolute** — **69.8% on 86 months, LB 59%, +14.0** over the 55.8% majority bar, 77% long, no bad year.
Relative label: nothing (P/E relative 40.5%, anti-predictive).

**Stage 3 (H = 1, from 2020-05):** 7 of 27 types populated; **pulled T2 (DN/DN/flat, 76.9%, n 13 — the short cell) and T23 (UP/flat/flat, 86.7%,
n 15, long)** = 28 months; remainder cascade 3 emissions (2 scored, 50%); no second instrument.

| integrated instrument | value |
|---|---|
| acted / scored | 30 / 75 (40%) |
| accuracy, LB95 | **80.0%, 62.7%** |
| calls | 17 long (right 82%), **13 short (right 77%)** → 57% long |
| acted-months up-rate → majority bar | 56.7% → **edge +23.3** |
| by year | 2020 67%/6 · 2021 67%/3 · 2022 80%/5 · 2023 86%/7 · 2024 100%/4 · 2025 75%/4 · 2026 100%/1 |
| abstentions | 45 (26 up / 19 down, mean +1.9%) |
| DECISION | 80.0% (n 30, LB 0.66); SANCTUARY-converged 78.6% (n 14, LB 0.57) → **ACTS**; SANCTUARY opposes 16 (integrated 81% there) |
| current (2026-08 row) | **UP — from the post-type cascade on T14, not from a pulled type**; the cascade layer's own record is 2 scored months at 50% → **flagged thin**; shadow 86 sh XLI |
| CASSANDRA (2026-10-01) | 2 analogues; call-conditioned UP p50 **$179.78 (+4.1%)** vs spot $172.73; statistical $174.72 |
| sizing | corr(sleeve, book) **−0.06**; sleeve Sortino 1.28; throttled-universe lift **+0.61** → **admitted, 5% notional, 0% real capital until tape** |

| universe, 1x | CAGR | Sortino | MaxDD |
|---|---|---|---|
| no sleeve | 22.42% | 7.68 | −3.56% |
| + Industrials 5%, throttled | 23.21% | **8.29** | −3.14% |
| + Industrials 5%, unthrottled | 23.50% | 8.23 | −3.14% |

**Metals correspondence (operator question).** Structurally Industrials is a *different metal* from Materials and a weaker one: raw monthly
correlations silver 0.22, gold 0.07, gold miners 0.19, **copper miners 0.61, base-metals basket 0.51**, platinum 0.34; net of SPY beta the silver
and gold residuals vanish (−0.02, 0.00) and what remains is a mild base-metals tilt (copper +0.20, base metals +0.19, palladium +0.17 from the
auto/aerospace names). No lead-lag in either direction (all within ±0.09). Against the metals calls already made: agrees with the monthly Silver
sleeve in **5 of 8** months both act and with the silver micro in **7 of 10**; with the monthly Gold sleeve 2 of 3. Return-stream correlations
+0.03 (silver), −0.09 (gold); Industrials' calls carry +0.08 information about next month's silver return. So a mild same-direction tendency with
the silver calls when both fire, but no shared return stream — not a duplicated bet, and the structural link runs through copper, not silver.

**Reading.** Industrials is the third two-sided sector, its short cell again T2 (13 months at 77%), its long cell T23; the anchor is the second-
strongest on the board (+14.0). The current UP is the weakest kind of call the system makes — a cascade emission on a non-pulled type with a
two-month record — and is on the tape with that flag; the pulled types are silent this month.

### 8b. Runner amendments made during the Energy run (declared, applied to all sectors)
- **R6b Predecessor registrants:** `PREDECESSOR = {XOM: [34088], APA: [6769]}`; facts merged per period end, earliest filing wins; every
  constituent with < 8 annual rows after the merge is listed so the map is extended BEFORE a sector runs. XBRL fetch validated with retry.
- **Growth v2 fallback:** when any window year's aggregate real earnings ≤ 0, g = annualised log ratio of the later-half block mean to the
  earlier-half block mean (NaN if either ≤ 0); the version is recorded per month; the R1 ill-conditioned test counts floor + undefined months.
- **Type-ineligible continuation:** with no admitted anchor, Stage 3 still runs on the best-edge anchor for the record (pulls not admitted),
  the type system is marked silent, and the run continues to the second instrument, tape, and CASSANDRA reference.

## 10. RE-VERIFICATION UNDER THE CORRECTED EARNINGS PARSER (F10) — 2026-09-13

All three sectors run before the fix were re-run end to end with `sector_runner.py` (income tags unioned, third tag pulled, CAPE routed).
The question for each: does the recorded conclusion survive complete earnings histories? **Yes for all three; details move, structure does not.**

### 10.1 Health Care (XLV) — CONFIRMED with one change of anchor label
| item | recorded (§3–§4v, hand scripts, truncated earnings) | re-verified (runner, full earnings) |
|---|---|---|
| companies with < 7 years (excluded, listed) | — | SOLV 4y, GEHC 5y (spin-offs, correct) |
| CAPE10 / CAPE5 / g10 / CAPEG (latest) | 33.6 / 29.4 / 1.7% / 19.6 | **32.5 / 28.6 / 2.4% / 13.7** |
| eligible anchors (R1) | PE-vs-Growth | **PE-vs-Growth (76.2%, +15.9) and Price-to-Growth (82.5%, LB 71%, +22.2), both absolute; Price-to-Growth relative (63.5%, +4.8)** |
| selected anchor (max edge) | PE-vs-Growth (CAPE10 / g10) | **Price-to-Growth (RealPrice / g10)** — the rule's choice; PE-vs-Growth remains eligible and second |
| pulled types | T2, T14, T17 (41 months) | **T2 (87.5%, n 16), T14 (81.8%, n 11), T17 (93.8%, n 16) — the same three, 44 months** |
| second instrument (R3) | CAPE10-velocity tier 2, 35 @ 91% | tier 2, **38 @ 84%, LB 70%** |
| integrated | 49/62 @ 89.8%, LB 78.2%, 73% long | **51/62 @ 88.2%, LB 76.6%, 69% long**; long calls right 88.6%, **16 short calls right 87.5%** |
| by year | 100/82/90/90/89/100 | 86/91/90/89/80/100 |
| abstentions | 13 (9 down, −2.1%) | 11 (7 down, −1.7%) |
| DECISION | ACTS (LB 0.80 / converged 0.76) | **ACTS (LB 0.79 / converged 0.76)**; SANCTUARY opposes 18, integrated 89% there |
| current (2026-08 row) | ABSTAIN (T18 thin); Sept row UP (T14) | **UP (T17, pulled)** — the corrected earnings re-type the August row |
| CASSANDRA 2026-10-01 | call-conditioned p50 $175.77 | **call-conditioned p50 $176.01** (+2.5%, n 35); statistical $173.19 |
| sizing | corr −0.06, sleeve Sortino 9.08, book 7.30 → 8.03 at 5% | **corr −0.09, sleeve Sortino 7.03, book 7.30 → 7.72 at 5%**; universe throttled 7.30 → 7.99 (+0.69), MaxDD −3.56 → −3.22 |
| shadow ticket | 90 sh XLV | 90 sh XLV |

Reading: the truncated earnings had flattered the sleeve's own Sortino (9.1 → 7.0) and tilted the anchor choice; the three pulled types, the
two-sidedness (16 shorts at 87.5%), the DECISION verdict, the admission and the ticket all stand. The template's anchor statement is amended:
**Health Care's most accurate anchor is Price-to-Growth (RealPrice / g10) on the absolute label; PE-against-Growth is the eligible runner-up.**
§4o–§4v remain as the worked example of the method with their numbers superseded by this table; the runner's `results/XLV/` is now the record.

### 10.2 Energy (XLE) — CONFIRMED
CAPE10 30.3 (29.9); anchor unchanged (P/E relative, pair); pulls T2 + T14 = 43 months (44); integrated **43/82 @ 74.4%, LB 59.8%, 100% short-relative**
(45 @ 75.6%); DECISION ACTS (LB 0.62); current ABSTAIN; sizing 2.5%/leg pair, corr −0.03, book 7.60 → 7.98, universe throttled 7.79. Same verdict.

### 10.3 Financials (XLF) — CONFIRMED
CAPE10 18.0 (18.5); anchor unchanged (P/E absolute); pulls T25 + T26 = 32 months; integrated **56/82 @ 69.6%, LB 56.7%, 95% long** (55 @ 69.1%);
DECISION ACTS (LB 0.59); current UP, 260 sh XLF; corr +0.23; universe throttled 7.91 (7.98), MaxDD −3.94 (−3.66). Same verdict, same character.

**Status after re-verification:** provisional flags lifted. The runner's `results/<TK>/` directories are the record for all sectors from here;
the hand-script results under `results/stage3_hc/` are the worked example only. Board: Health Care two-sided ACTS (UP), Financials
long-selection ACTS (UP), Energy relative pair ACTS (ABSTAIN this month), Consumer Discretionary WATCH-NONE (ABSTAIN). Five sectors remain.

### 9.9 Consumer Staples (XLP) — 2026-09-14 — verdict: **TYPE-INELIGIBLE; second instrument qualifies → WATCH (R2), not sized; current ABSTAIN**
34 constituents; Constellation Brands dropped (no annual share count, listed); Bunge and Kenvue (5y) excluded and listed. CAPE10 28.9; the
growth leg is ill-conditioned in 78% of the frame (real earnings flat-to-falling: g10 0.08%/yr now) → growth anchors out; Price-to-Earnings
absolute 62.1% (+6.9, LB 52%) fails on a bad year. Record-only T17 clears the pull bar (not admitted). **The type-agnostic tier qualifies (R3):
tier 2 on CAPE10/CAPE5 velocity, 38 @ 79%, LB 64%** → integrated = second instrument alone: 30/62 @ 80.0%, LB 62.7%, **100% long**, acted up-rate
80% (= accuracy; window 52% → selection +28), abstentions 32 with 24 down (mean −1.6% — silence is a down signal); DECISION ACTS (LB 0.66).
Under R2 a tier-only sector is WATCH and cannot be sized. On the board as ABSTAIN with its tape open.

## 11. THE SECTOR BOARD AND THE INTEGRATED PORTFOLIO (all nine sectors run, 2026-09-14)

Page: **ZION Sector Board** (artifact; `build_board_page.py` → `sector_board.html`). Integration: `portfolio_integration_all.py` →
`results/portfolio_integration_all.{json,csv}`.

| sector | anchor · label | pulled | integrated (acted/scored, acc, LB95) | long/short | edge vs majority | DECISION | instrument | status | call now |
|---|---|---|---|---|---|---|---|---|---|
| Health Care | P/G · abs | T2,T14,T17 | 51/62, 88.2%, 77% | 35/16 (shorts 87.5%) | +23.5 | ACTS | sleeve 5% | ADMITTED | UP |
| Consumer Disc | P/E · abs | T2,T14,T22 | 36/75, 83.3%, 68% | 22/14 (shorts 85.7%) | +27.8 | ACTS | sleeve 5% | ADMITTED | ABSTAIN |
| Industrials | P/E · abs | T2,T23 | 30/75, 80.0%, 63% | 17/13 (shorts 77%) | +23.3 | ACTS | sleeve 5% | ADMITTED | UP (thin source) |
| Financials | P/E · abs | T25,T26 | 56/82, 69.6%, 57% | 53/3 | +0.1 (selection +10.7) | ACTS | sleeve 5% | ADMITTED | UP |
| Technology | P/E · abs | T2,T14,T23,T26 | 74/75, 75.7%, 65% | 53/21 (shorts 71%) | +12.2 | ACTS | short-only overlay 5% (R5s) | ADMITTED | DOWN (overlay ON) |
| Energy | P/E · rel | T2,T14 | 43/82, 74.4%, 60% | 0/43 short-rel | +1.1 (selection +13) | ACTS | pair 2.5%/leg (R5p) | ADMITTED | ABSTAIN |
| Materials | P/E · abs | T2 | 25/75, 72.0%, 52% | 6/19 (shorts 68%) | +16.0 | ACTS | — | not admitted (throttled lift −0.05) | ABSTAIN |
| Cons Staples | none (R1) | — | 30/62, 80.0%, 63% (tier only) | 30/0 | 0 (selection +28) | ACTS | — | WATCH (R2) | ABSTAIN |
| Utilities | none (R1) | — | 0/71 | — | — | — | — | WATCH-NONE | ABSTAIN |

**The admitted block (six instruments; as admitted = 30% gross, twice the 15% cap → allocated; Sortino-weighted variant carried):**
weights XLV 5.21%, XLF 0.96%, XLY 2.65%, XLE 0.11%, XLK 0.75%, XLI 5.21%. Instrument correlations with the universe: XLV −0.17, XLF +0.21, XLY −0.09,
XLE +0.15, XLK −0.32, XLI −0.25; among instruments the only pairs ≥ 0.30 are XLY–XLK +0.47, XLY–XLI +0.41, XLK–XLI +0.32 (the shared T2 cell).

| universe / leg (monthly basis, 2021-06 → 2026-07) | CAGR | Sortino | MaxDD | with block: CAGR | Sortino | MaxDD |
|---|---|---|---|---|---|---|
| universe 1× (tape basis) | 21.09% | 7.30 | -3.56% | 24.76% | **8.79** | -2.75% |
| universe 2.5× (executed) | 58.5% | 7.30 | -8.78% | 70.6% | 8.79 | -6.84% |
| universe 3.8× (model) | 97.2% | 7.30 | -13.20% | 120.2% | 8.79 | -10.38% |
| universe 4.0× (ladder destination) | 103.69% | 7.30 | -13.87% | 128.79% | 8.79 | -10.92% |
| weekly leg alone 1× | 26.37% | 4.26 | -9.59% | 30.20% | 4.86 | -8.55% |
| monthly leg alone 1× | 7.02% | 1.47 | -4.40% | 10.27% | 2.36 | -3.88% |
| weekly book × lev, week-by-week, aggregated to months | 24.15% | 4.07 | −9.81% | 27.72% | **5.01** | −8.85% |
| (weekly basis, reference only) | 24.12% | 3.47 | −9.93% | 27.68% | 3.99 | −8.85% |

Allocation variants at 1×: as admitted (30% gross, over cap) 27.21% / 8.80 / -2.66%; 15% equal 24.12% / 8.71;
15% Sortino-weighted 24.76% / 8.79; 15% inverse-vol 24.09% / 8.71. Gross with the block at the cap: netted max 1.63× (house
2.0× holds), 6.21× at 3.8× (base 5.67×; R5p clip applies in the excess weeks), 4.09× at the executed 2.5×.

**How CAGR and Sortino land.** Sortino is the sizing number and is leverage-invariant: +1.49 on the universe (7.30 → 8.79) at every multiple;
the weekly leg +0.60, the monthly leg +0.89, the week-by-week book +0.94 (monthly-aggregated). CAGR scales with leverage: +3.7 pts at 1×, +12.1 at
the executed 2.5×, +23 at 3.8×. Drawdown improves at every multiple because the block is negatively correlated with the universe in its
down-months (the shorts and the pair). All of it is backtest with full-record pull membership and in-sample joint weights (R4); the tapes opened
2026-09-13 are the evidence; real capital 0% until 12 resolved months per instrument.

**Dashboard integration (proposal, not wired):** a "Sectors" section fed by the nine forward tapes and a `gen_sector_board.py` in
`reports_gen/` (board table, as-issued call, instrument kind, status, LB95 as conviction, thin-source flag); a "universe + sector block" row
beside the universe row in the integrated view (1× and 2.5× CAGR / Sortino / MaxDD); a SHADOW sector line on the desk ticket (this month
XLV +90, XLF +260, XLI +86, XLK −79 shares; Energy/Discretionary abstain). Monthly tape emission needs a scheduled job — explicit authorisation
per the jobs inventory, as does any edit to `refresh_reports.sh`, the netting ledger, the desk ticket or the locked book spec.

## 12. OPERATING PROCEDURE — how to repeat this every month and every week

All commands run from `~/Desktop/ZION/sector_volume/` with the HYACINTH venv python (`/Users/castaglia/Desktop/HYACINTH/venv/bin/python`).
Nothing here is scheduled; scheduling is a production change that needs explicit authorisation (jobs inventory). Until then the steps are manual.

### 12.1 MONTHLY — on the first trading day of the month (after the panel's new M-01 row exists)
1. **Refresh prices** (Yahoo daily → the scratchpad CSVs the runner reads; SPY, the nine sectors, GLD/SLV/COPX for the overlap checks).
   The fetch block at the top of this thread (`yf.download(tks, start="1998-01-01")` into `<TK>_daily.csv`) is the reference; make it a
   `refresh_prices.py` before the first scheduled run.
2. **Refresh the panel** — the runner reads `HYACINTH_X/combined_macro_<MMDD>.csv` via `lib_pipeline.PANEL`; the panel job is the house's (not
   this system's). Confirm the M-01 row is present; macro columns will lag one month (carry-forward convention, §4b).
3. **Refresh FRED legs** — delete `data/fred_*.csv` (they are cached) so the runner re-pulls; the publication lags are in `sector_recipe.FRED`.
4. **Refresh earnings** — delete `data/xbrl/<tk>_companyfacts.json` for any sector whose constituents filed a 10-K in the month (or simply all
   nine, ~5 minutes total); the runner re-pulls with the predecessor map and lists every thin-history name. **Review that listing before
   accepting the run** (F2, F10): a new successor CIK goes into `PREDECESSOR`; a new spin-off is expected to be listed and excluded.
5. **Refresh constituents once a quarter** (`build_pe_lists.py`): S&P 500 membership and the PE/PEG snapshot. The universe is current-
   constituent by ruling (§5.4).
6. **Run each sector**: `python sector_runner.py XLV` … for all nine (≈ 5–10 minutes each; sequentially to respect SEC rate limits). Each run
   appends an as-issued row to `results/<TK>/<TK>_forward_tape.csv` (decision row, call, cell, label, price, resolution date) and rewrites
   `results/<TK>/REPORT.md`. **Never edit a past tape row**; the resolver (step 9) fills outcomes.
6b. **Run the sequential re-derivation** (R7) for each sector — `python sector_sequential.py <TK> --mode fixed` and `--mode strict`
   (≈ 5 minutes per sector per mode; nine sectors × two modes in six parallel processes ≈ 20 minutes) — then
   `python portfolio_integration_seq.py` → `results/sequential/integration_compare.{md,json}`. The per-sector record columns on the board
   and every figure quoted for the block are the sequential ones; the ledger figures are shown beside them, labelled backtest. The
   harness's call for the last decision row is the same call the runner writes to the tape (verified 14 Sep on Health Care).
7. **Run the integration**: `python portfolio_integration_all.py` → `results/portfolio_integration_all.{json,csv}` (admitted block, weights,
   universe and leg tables, weekly-level table, gross check). Then `python build_board_page.py` and republish **ZION Sector Board**.
8. **Read the board** (§11 table): per sector the call (UP / DOWN / LONG-REL / SHORT-REL / ABSTAIN; overlay ON/OFF), the instrument, the status,
   and the shadow shares at `$100k × 2.5×`. A call sourced from the post-type cascade rather than a pulled type carries the thin-source flag.
9. **Resolve last month's tape rows** (each sector's previous row: outcome = sign of the M-01 → next M-01 move, relative for pairs) and
   recompute the **forward record** per instrument (acted, accuracy, Wilson LB95, edge vs the acted-months majority). This is the evidence
   channel; the resolver is `resolve_sector_tapes.py` (to be written from the XLV tape schema before the first resolution on 2026-10-01).
10. **Gates** (unchanged): an instrument leaves shadow only after 12 resolved months with LB95 > 50% and its edge > 0; the block's Sortino lift
    must hold on the tape; the 15% cap and the R5p clip are enforced; the leverage ladder is untouched. Real capital: 0% until then.
11. **Re-verification triggers** (rerun the affected sectors from step 4): a parser or rule change; a predecessor-map addition; a constituent
    list refresh that adds or removes names with > 5% of a sector's cap.

### 12.2 WEEKLY — Friday, after the ZION Friday job (netting ledger current)
The sector instruments are monthly; the weekly work is positioning and bookkeeping, not re-deciding.
1. **Carry the month's calls into the week**: for each admitted instrument, position = this month's call × its notional weight × the weekly
   book's `lev`, in its own bucket; pairs carry the SPY leg into US_EQ; the Technology overlay carries only when the call is DOWN.
2. **Apply the throttle** from the netting ledger's `thr`: sleeves and pairs FLAT while `thr < 1.0`; the overlay is hedge-class and stays on.
3. **Apply the caps**: sector gross ≤ 15%; if universe gross (netted × 3.80) would exceed 6.0× in the week, clip the sector block (R5p).
4. **Write the SHADOW line** to the desk ticket (shares at capital × 2.5× / last close, per instrument) — this is what
   `results/<TK>/shadow_netting_ledger.csv` computes per sector and what `gen_sector_board.py` would feed to the dashboard once wired.
5. **Do not re-run the sectors mid-month**: the decision row is the M-01 row; a mid-month re-run changes nothing except the price used for shares.
6. **Weekly performance**: the sector block's week-by-week contribution = Σ position × sector weekly return (pairs: minus SPY); report it
   monthly-aggregated beside the weekly book (§11 table), never on the √52 basis as the headline.

### 12.3 What repeats, what is fixed
- **Fixed for every run and every sector** (never tuned): horizon 1 month; dead zone 0.5 SD; pull bar WF > 67.5% & n ≥ 8; floors 8; MIN_TRAIN 60;
  design sample 40%; DECISION gate 0.45; the eight-call year test; sleeve 5% / pair 2.5% per leg / overlay 5%; 15% sector cap; R1–R6 as written.
- **Refit monthly by construction — going forward**: from the first tape row on, every call is issued by the full machinery refit on the
  data available at the decision month, so the tape is sequential and there is no frozen cell to maintain. The historical ledger is
  NOT sequential (its pull set and anchor were chosen on the whole record — B20); its sequential counterpart is the re-derivation of
  §7 step 10s / §14, and that, not the ledger, is the backtest figure that counts as evidence (R7). What accrues is the tape.
- **Amend only by declared rule** (as R1, R5p, R5s were): write the rule into §8 and the runner header, state its impact across sectors,
  then re-run. Every change so far is dated in the change log.

## 13. FINDINGS — consolidated (2026-09-14), and the current suggestion

### 13.1 What the nine runs established
1. **One method runs every sector.** The same procedure (§7), constants and rules (§8) produced a verdict for all nine without per-sector tuning;
   every deviation was a declared rule change with its cross-sector impact stated (R1 both labels; R1 eight-call years; R5p pair; R5s overlay;
   R5 throttled lift; R6b predecessors; growth v2 fallback; income-tag union).
2. **The short side is one cell.** Every two-sided sector's shorts come from T2 — sector valuation and real price falling with smoothed-earnings
   growth flat, a de-rating in progress: Health Care 16 @ 87.5%, Consumer Discretionary 14 @ 85.7%, Industrials 13 @ 77%, Technology 21 @ 71%,
   Materials 19 @ 68%. Energy's shorts are relative (short Energy / long SPY, 43 @ 74%); Utilities' record-only T11 is all-short (22 @ 73%).
3. **Long sides split into two kinds.** Selection-longs whose accuracy equals the acted-months up-rate (Financials, Staples' tier) earn by
   choosing months, not direction; two-sided longs (Health Care T14/T17, Discretionary T14/T22, Industrials T23) sit beside a working short cell.
4. **Sector CAPEs (latest):** Technology 72.7, Consumer Discretionary 46.2, Health Care 32.5, Industrials 31.9, Energy 30.3, Materials 29.0,
   Staples 28.9, Utilities 25.1, Financials 18.0. Growth legs are ill-conditioned wherever real earnings fell for years inside the windows
   (Energy 60%, Staples 78%, Materials 57%, Utilities 40%, Industrials 43% of months) — those sectors' growth anchors are out by rule.
5. **Data defects found and fixed on the way** (§9.2a F1–F12, Addendum A B16–B19): successor-registrant CIKs (Exxon, Apache, BlackRock,
   Apollo), income-tag truncation (Booking; 29 companies across three sectors), missing share tags (Erie, Constellation), a dead FRED series,
   undefined growth trends. Each is now a listed check the runner performs before a sector's numbers are accepted.
6. **Admission (R5):** six instruments admitted, three not. Correlation with the book: Health Care −0.09, Consumer Discretionary +0.01,
   Industrials −0.06, Financials +0.23, Energy pair −0.03, Technology overlay −0.32 (full Technology +0.52, failed); Materials −0.12 but no
   throttled lift; Staples tier-only; Utilities nothing.
7. **Precious metals:** no sector's calls correlate with the gold or silver calls (return-stream correlations within ±0.09); Materials is
   copper-shaped (0.72), Industrials base-metals-shaped (0.61 copper) with zero silver residual.

### 13.2 What the block does to the portfolio (15% cap, Sortino-weighted; 2021-06 → 2026-07)
Universe Sortino 7.30 → 8.79 at every leverage (leverage-invariant); CAGR 21.1 → 24.8% (1×), 58.5 → 70.6% (2.5× executed), 97.2 → 120.2% (3.8×),
**103.7 → 128.8% at 4.0×** (the ladder destination), with MaxDD −13.87 → −10.92% at 4.0×; weekly leg 4.26 → 4.86, monthly leg 1.47 → 2.36,
week-by-week book 4.07 → 5.01 (monthly-aggregated). Gross max 1.63× netted; 6.21× at 3.8× (clip applies in the excess weeks).

**Weighting observation (rule question, not decided):** Sortino-weighting the cap concentrates it in Health Care 5.2% and Industrials 5.2% and
starves the hedge-shaped instruments (Financials 0.96%, Technology overlay 0.75%, Energy pair 0.11%). Equal-gross weighting lands within 0.08 of
the same Sortino (8.71 vs 8.79) while keeping every admitted instrument at 2.5%; on diversification grounds equal gross is the better carried
variant. Operator to rule; the tables for both are in §11 and on the board page.

### 13.3 The current suggestion (decision row 2026-08, outcome September → October; week ending 2026-09-11; throttle 1.00, lev 1.19)
Shadow only — 0% real capital; nothing on the executed ticket. $100k at 2.5×, 15% cap, Sortino-weighted:

| instrument | call | weight | exposure | shares (last close) |
|---|---|---|---|---|
| Health Care sleeve | **UP** (T17 pulled) | 5.21% | +0.062 | **+94 XLV** @ $165.36 |
| Industrials sleeve | **UP** (cascade emission on T14 — thin source) | 5.21% | +0.062 | **+90 XLI** @ $172.37 |
| Financials sleeve | **UP** (T25 pulled) | 0.96% | +0.011 | +50 XLF @ $57.25 |
| Technology overlay | **DOWN** (T2 pulled → overlay ON) | 0.75% | −0.009 | −12 XLK @ $187.67 |
| Consumer Discretionary sleeve | ABSTAIN (T1) | 2.65% | 0 | — |
| Energy pair | ABSTAIN (T26) | 0.11%/leg | 0 | — |
| Materials / Staples / Utilities | ABSTAIN | not admitted | — | — |

Sector block gross 0.144× of capital (0.36× executed); book netted gross 0.858× → 1.002×. **Month:** long Health Care, Industrials and
Financials, short Technology; abstain elsewhere. **Week:** carry those positions; the throttle is on so the sleeves are live; no re-decision
until the 2026-09-01 row is the decision row (the runner reads the panel's latest row; the September row will re-type once the panel carries it —
Health Care's Yahoo-priced September row already reads T14 UP with the tier agreeing, §4r).

### 13.4 Hand-offs sent (14 Sep)
- **THE INTRUDER thread** (session "The Intruder"): the T2 short-cell findings and three questions — whether the count of sectors' T2 cells
  firing belongs in its signal-count crash logic; whether it wants the sector shorts as inputs to its alert state or as a cited board; anything
  in its as-issued short record that contradicts the T2 reading. Delivered; reply pending in that thread.
- **GREEK_WATCH thread** (session "Extend GREEK_WATCH monitoring + health routine"): the board, the admitted block and its effect, the current
  calls, and three questions — where monthly sector calls fit (context row / gate on 5-day calls / separate with cross-reference); whether it
  wants the T2 flags as inputs and in what format; anything in its XLK/tech record contradicting the Technology DOWN. Delivered; reply pending.

## 14. BACKTEST v OOS-VALIDATED — the sequential re-derivation (R7, "as in ZION"), 2026-09-14

### 14.1 Why, and what was run
The operator asked whether the sector block should go live rather than shadow. The figures on the table (§11, §13.2) were the ledger's:
pull membership decided on the whole record, anchor chosen on the whole record (R4). A 2020 month in that ledger "knew" how its type
would do through 2026. That is not what the tape will see. So every instrument was re-derived **sequentially**: at each decision month t
the panel is truncated at t (outcome of t unknown), the whole chain is refit on it — the N sweep on the first 40% of the truncated frame,
the 27-type table and the pull set (WF > 67.5% & n ≥ 8 on scored months < t), the cascade folds on the remainder, the type-agnostic
tier admission (R3, LB95 > 50% & n ≥ 8 on months < t) — and the call for t is read off the last decision row exactly as `s13_tape`
reads it today. Verified on Health Care's last four months: the harness's call equals the runner's tape call in every month.

Two modes, both reported: **fixed** — the anchor and label are held at the admitted ones (a one-time design choice, the R4 exposure that
remains is 4 anchors × 2 labels per sector); **strict** — the anchor is re-chosen by R1 each month on the truncated record (R1 needs
n ≥ 60 post-design calls, so strict mode has no anchor for the first ~5 years of a 12-year CAPE frame and acts through the tier instrument
until R1 can admit one). A third layer, **sequential admission**, keeps an instrument out of the book until its own sequential record has
twelve resolved months clearing the DECISION bound (LB z=1.645 > 0.45), a positive edge against its majority class, |corr| < 0.30 with the
universe and a throttled Sortino lift — the R1 / DECISION / R5 gates applied the way the tape will apply them.

Runtime: ≈ 3 s per decision month per sector (Stage 3 ≈ 1 s, pre-type ≈ 2 s); nine sectors × two modes in six parallel processes ≈ 20 min.
Scripts: `sector_sequential.py <TK> --mode fixed|strict [--embargo 3] [--horizon 3] [--last N --out DIR]` → `results/sequential/<TK>_<mode>_tape.csv`
+ `_summary.json`; `portfolio_integration_seq.py` → `results/sequential/integration_compare.{md,json}`. Nothing under `results/<TK>/` is touched.
Production modules are not edited: the embargo / horizon variants load `multiasset_pipeline.py` and `sector_runner.py` from source with
three exact-text substitutions (training frontier `t − H + 1` → `t − FRONT + 1`; `MP.H = 1` → the horizon; the ORACLE label and frontier).
Early months with no scored phase-1 decision on the truncated frame raise the pipeline's diagnostics printer (division by zero) — classified
warm-up (B22).

### 14.2 Per-instrument record — backtest (ledger) v sequential
Acted months / accuracy / Wilson LB95 / majority-class rate of the acted months / edge (points) / long–short split. Windows 2019-10 or
2020-05 → 2026-07. Shaded = admitted instruments.

| sector | instrument | **backtest** acted · acc · LB95 · maj · edge · L/S | **sequential, anchor held** | **sequential, strict (R1 monthly)** |
|---|---|---|---|---|
| XLV Health Care | sleeve | 51 · 88.2 · 76.6 · 64.7 · **+23.5** · 35/16 | 37 · 81.1 · 65.8 · 81.1 · **0.0** · 35/2 | 42 · 88.1 · 75.0 · 73.8 · **+14.3** · 34/8 |
| XLF Financials | sleeve | 56 · 69.6 · 56.7 · 67.9 · +1.8 · 53/3 | 47 · 63.8 · 49.5 · 61.7 · +2.1 · 44/3 | 38 · 65.8 · 49.9 · 63.2 · +2.6 · 35/3 |
| XLY Cons Disc | sleeve | 36 · 83.3 · 68.1 · 55.6 · **+27.8** · 22/14 | 15 · 80.0 · 54.8 · 53.3 · **+26.7** · 8/7 | 8 · 75.0 · 40.9 · 50.0 · +25.0 · 6/2 |
| XLE Energy | pair (rel) | 43 · 74.4 · 59.8 · 74.4 · 0.0 · 0/43 | 23 · 78.3 · 58.1 · 73.9 · +4.3 · 1/22 | 14 · 78.6 · 52.4 · 78.6 · 0.0 · 0/14 |
| XLK Technology | short-only overlay | 21 shorts · 71.4 · 50.0 · (down-rate 37) | 18 shorts · 55.6 · 33.7 · (down-rate 37) | 6 shorts · 50.0 · 18.8 · (down-rate 37) |
| XLI Industrials | sleeve | 30 · 80.0 · 62.7 · 56.7 · **+23.3** · 17/13 | 33 · 69.7 · 52.7 · 54.5 · **+15.2** · 20/13 | 8 · 75.0 · 40.9 · 75.0 · 0.0 · 6/2 |
| XLB Materials | not admitted | 25 · 72.0 · 52.4 · 56.0 · +16.0 · 6/19 | 28 · 64.3 · 45.8 · 53.6 · +10.7 · 19/9 | 0 (R1 never admits an anchor) |
| XLP Cons Staples | WATCH (tier only) | 30 · 80.0 · 62.7 · 80.0 · 0.0 · 30/0 | 46 · 71.7 · 57.5 · 60.9 · +10.9 · 29/17 | 52 · 73.1 · 59.7 · 63.5 · +9.6 · 35/17 |
| XLU Utilities | WATCH-NONE | 0 | 0 | 34 · 82.4 · 66.5 · 61.8 · +20.6 · 27/7 (tier only; flickers in and out of R3) |

Sources of the sequential calls (anchor held): XLV type-pull 15 / cascade 8 / tier 14 / abstain 22 / warm-up 17; XLF 14 / 14 / 19 / 34 / 2;
XLY 13 / 2 / 0 / 61; XLE 19 / 4 / 0 / 60; XLK 38 / 18 / 9 / 11; XLI 19 / 14 / 0 / 43; XLB 8 / 20 / 0 / 48; XLP 0 / 0 / 46 / 13 / 17.
Strict mode anchors: XLV none 53 · PE 20 · P/G 3 of 76 months; every other sector none ≈ 50–58 · PE 25–27 — R1's n ≥ 60 admits an anchor
only from about 2024 on this frame. Cascade emissions sequentially: XLI 14 at 43%, XLF 14 at 43%, XLK 18 at 50%, XLV 8 at 88%, XLB 20 at 70% —
the post-type cascade is the weakest source once it is honest, as ZION found for its own tiers.

Per calendar year, sequential (anchor held), accuracy (n): XLV 2021 100 (2) · 2022 83 (6) · 2023 78 (9) · 2024 67 (6) · 2025 78 (9) · 2026 100 (5);
XLF 75 (8) · 75 (4) · 62 (8) · 50 (6) · 57 (7) · 56 (9) · 80 (5) from 2020; XLY 2022 100 (1) · 2023 100 (3) · 2024 83 (6) · 2025 67 (3) · 2026 50 (2);
XLE 2021 100 (1) · 100 (2) · 50 (4) · 89 (9) · 83 (6) · 0 (1); XLK 2020 100 (5) · 75 (8) · 42 (12) · 67 (9) · 82 (11) · 58 (12) · 50 (8);
XLI 2020 100 (1) · 50 (4) · 50 (12) · 100 (6) · 100 (4) · 75 (4) · 50 (2). Long / short against the window base rates (anchor held):
XLV longs 35 at 83% v up-rate 61%; XLF longs 44 at 64% v 58%; XLY longs 8 at 75% v 53%, shorts 7 at 86% v down-rate 47%; XLE shorts 22 at
77% v 59%; XLK shorts 18 at 56% v 37%; XLI longs 20 at 70% v 57%, shorts 13 at 69% v 43%; XLP longs 29 at 76% v 53%, shorts 17 at 65% v 47%.

### 14.3 What the sequential test changed, instrument by instrument
- **Health Care**: the +23.5-point edge is a full-record artefact. Sequentially (anchor held) it acts 37 months at 81% — and 81% is the
  up-rate of the months it chose. Its shorts vanish (2, at 50%). It is a long-drift capturer on the honest record. Strict mode does better
  (+14.3) because for 53 months it has no anchor and acts through the CAPE-velocity tier (29 months at 86%), and 8 shorts at 88%: the
  second instrument, not the type system, carries Health Care sequentially.
- **Consumer Discretionary** keeps its edge (+26.7) but on 15 months, 8 long / 7 short; strict mode has 8. The lower bound (54.8) barely
  clears 50. Real, thin.
- **Industrials** keeps a smaller edge (+15.2 on 33; pulls 19 at 89%, cascade 14 at 43%); strict mode has 8 months. The 2022 year is 50% on 12 calls.
- **Financials** never had an edge (+1.8 → +2.1 → +2.6): its accuracy is the up-rate of the months it selects. Sequential LB95 is 49.5.
- **Energy pair**: shorts-only in every version; 77–79% against a 59–74% majority-down rate; the edge is 0–4 points. Not evidence of skill
  beyond "Energy lags the market most months on this window".
- **Technology overlay**: 18 sequential shorts at 56% against a 37% down-rate (n too small for R5s's ≥ 15 at LB > down-rate: LB95 33.7);
  strict mode 6 shorts at 50%. The overlay's backtest bar (21 shorts, 71%) does not survive.
- **Materials / Staples / Utilities**: Materials' sequential LB95 is 45.8; Staples' tier-only instrument is the surprise — 46 months at
  71.7% / LB95 57.5 against a 61% majority, both modes — it was WATCH under R2 (a tier alone cannot be sized) and stays WATCH; Utilities
  in strict mode acts 34 months at 82% through a tier that qualifies and un-qualifies under R3 month to month (31 "seq-only" months):
  a rule finding on R3's stability, recorded, not acted on.

### 14.4 The universe with the block — backtest v OOS-validated
Same six instruments, same weights, the calls from each source. Equal gross under the 15% cap (B: sleeves 2.5%, pair 1.25%/leg, overlay
2.5%; nothing fitted on the sequential streams) and the published Sortino weights (C, fitted on the backtest streams, applied unchanged).
Universe = ZION universe monthly 1×, class-throttled block, Sortino on down-months, leverage-invariant.

Published window 2021-06 → 2026-07 (62 months), universe alone: CAGR 21.1% (1×) · 58.5% (2.5×) · 103.7% (4.0×), Sortino 7.30, MaxDD −3.6 / −8.8 / −13.9%.

| block source | weights | CAGR 1× | Sortino | MaxDD 1× | CAGR 2.5× | MaxDD 2.5× | CAGR 4.0× | MaxDD 4.0× | Δ Sortino |
|---|---|---|---|---|---|---|---|---|---|
| backtest (ledger) | B equal | 24.1% | 8.71 | −3.0% | 68.5% | −7.5% | 124.2% | −12.0% | +1.41 |
| backtest (ledger) | C Sortino | 24.8% | 8.79 | −2.7% | 70.6% | −6.8% | 128.8% | −10.9% | +1.48 |
| sequential, anchor held | B equal | 22.7% | 8.65 | −3.1% | 63.8% | −7.8% | 114.4% | −12.3% | +1.35 |
| sequential, anchor held | C Sortino | 23.2% | 8.98 | −3.0% | 65.3% | −7.5% | 117.5% | −11.9% | +1.67 |
| sequential, strict | B equal | 21.9% | 7.85 | −3.6% | 61.0% | −8.8% | 108.8% | −13.9% | +0.55 |
| sequential, strict | C Sortino | 22.3% | 8.03 | −3.6% | 62.4% | −8.8% | 111.5% | −13.9% | +0.72 |
| sequential, strict + sequential admission | B equal | 21.1% | 7.29 | −3.6% | 58.6% | −8.8% | 103.9% | −13.9% | −0.02 |

Extended window 2019-10 → 2026-07 (82 months), universe alone CAGR 22.2% / 62.2% / 111.6%, Sortino 7.60, MaxDD −3.6 / −8.8 / −13.9%:
backtest B +1.28 (8.88) · C +1.22; sequential held B +1.18 (8.78) · C +1.43 (9.02); strict B +0.55 (8.14) · C +0.68; strict + admission −0.01 (7.58).

Block only, 2.5× on $100k, equal gross, extended window (82 months):

| source | active mo | up / down | mean $/mo | total $ | worst month | block MaxDD | block Sortino | down when universe down (of 21) |
|---|---|---|---|---|---|---|---|---|
| backtest (ledger) | 62 | 55 / 7 | +450 | +36,886 | −847 (2022-12) | −0.66% | 5.77 | 2 |
| sequential, anchor held | 52 | 39 / 13 | +239 | +19,559 | −1,198 (2022-12) | −0.58% | 2.29 | 3 |
| sequential, strict | 33 | 28 / 5 | +139 | +11,366 | −847 (2022-12) | −0.54% | 1.54 | 1 |
| strict + sequential admission | 3 | 3 / 0 | +3 | +270 | 0 | 0 | — | 0 |

First month each instrument clears the sequential admission gates on its own record: **Health Care 2025-12; no other instrument, ever, on this
frame.** The book the rules would actually have built holds one sleeve for eight months.

### 14.5 Reading
1. **The dollar edge halves and the block's own Sortino drops from 5.8 to 2.3** when the pull set is honest (anchor held), and halves again
   (1.5) when the anchor choice is honest too. Mean +$450/month becomes +$239 and +$139; the worst month gets worse (−$847 → −$1,198).
2. **The universe Sortino lift mostly survives the anchor-held test (+1.35 / +1.67) and halves under strict (+0.55 / +0.72).** It is not
   the block's return that lifts the universe — it is *when* the block pays: in the universe's 21 down-months the block is itself down in
   2 (backtest), 3 (held), 1 (strict). The de-rating short cell T2 fires in market down-months, and T2 is pulled sequentially as well as on
   the full record. That is the part of the story that is real; the accuracy figures on the board were not.
3. **Under sequential admission the lift is zero** because on a 76–83-month record no instrument reaches twelve resolved months clearing the
   house gates until Health Care in 2025-12. "Go live now" would therefore mean acting on the backtest, which R7 now forbids; on the rules
   as written the block is not admissible on its history at all — it becomes admissible only through the tape, one instrument at a time.
4. **Health Care's edge was the full-record pull set.** Sequentially it is a long-drift capturer (81% = its up-rate). The instrument that
   carries it honestly is the CAPE-velocity tier (second instrument), which is exactly what the parallel-instrument ruling (§4q–§4r) kept.
5. **Consumer Discretionary and Industrials keep a real but thin two-sided edge** (15 and 33 months); Financials and the Energy pair have
   none beyond drift; the Technology overlay does not clear its own admission bar sequentially.
6. **The 3.8× / 4.0× ladder numbers quoted in §11 / §13.2 (97 → 120%, 104 → 129%) are backtest.** Their sequential counterparts (anchor
   held, equal gross) are 114% at 4.0× on the published window, 109% strict, 104% (no lift) with sequential admission.

**Consequence for the shadow / live question:** unchanged from the assessment given before this section was written, now with the reason
quantified — the tape is the only admissible evidence, the machinery to score it does not yet exist, and the honest history admits one
instrument for eight months. Live-small after the resolver and price-refresh exist, with the ramp gated on the tape, is the most that the
record supports; full live would be a ruling against R7 and the twelve-month rule together.

### 14.6 Embargo-3 (ZION training frontier t − 3) and 3-month horizon — reported, not the method
Both variants run through the same harness (27 + 9 jobs; the first strict variants ran as fixed through a wrong-branch bug — B23 — and were rerun).

**Embargo 3 (training frontier t − 3, horizon 1).** Per instrument, acted · acc · LB95 · majority · edge · L/S:

| sector | anchor held, embargo 3 | strict, embargo 3 | (for reference: anchor held, frontier t − 1) |
|---|---|---|---|
| XLV | 38 · 78.9 · 63.7 · 78.9 · 0.0 · 36/2 | 47 · 87.2 · 74.8 · 74.5 · +12.8 · 39/8 | 37 · 81.1 · 65.8 · 81.1 · 0.0 |
| XLF | 48 · 58.3 · 44.3 · 58.3 · 0.0 · 44/4 | 24 · 62.5 · 42.7 · 62.5 · 0.0 · 22/2 | 47 · 63.8 · 49.5 · 61.7 · +2.1 |
| XLY | 12 · 75.0 · 46.8 · 66.7 · +8.3 · 5/7 | 6 · 66.7 · 30.0 · 66.7 · 0.0 · 4/2 | 15 · 80.0 · 54.8 · 53.3 · +26.7 |
| XLE | 22 · 77.3 · 56.6 · 72.7 · +4.5 · 1/21 | 12 · 75.0 · 46.8 · 75.0 · 0.0 · 0/12 | 23 · 78.3 · 58.1 · 73.9 · +4.3 |
| XLK (shorts) | 17 · 58.8 · 36.0 · (down-rate 37) | 5 · 40.0 · 11.8 | 18 · 55.6 · 33.7 |
| XLI | 33 · 78.8 · 62.2 · 54.5 · **+24.2** · 21/12 | 7 · 85.7 · 48.7 · 85.7 · 0.0 · 5/2 | 33 · 69.7 · 52.7 · 54.5 · +15.2 |
| XLB | 29 · 65.5 · 47.3 · 51.7 · +13.8 · 20/9 | 0 | 28 · 64.3 · 45.8 · 53.6 · +10.7 |
| XLP (tier only) | 46 · 73.9 · 59.7 · 63.0 · +10.9 · 35/11 | 46 · 73.9 · 59.7 · 63.0 · +10.9 | 46 · 71.7 · 57.5 · 60.9 · +10.9 |
| XLU (tier only) | 45 · 73.3 · 59.0 · 66.7 · +6.7 · 36/9 | 33 · 69.7 · 52.7 · 66.7 · +3.0 | 0 |

The embargo costs little and changes little: Industrials improves (+24.2 on 33; its cascade emissions go from 43% to 76%), Consumer
Discretionary loses most of its edge (+8.3 on 12, LB95 46.8), Health Care and Financials stay at their majority rates, the Energy pair and
the Technology overlay stay where they were. Universe with the block (published 62-mo, 1×): anchor held +1.28 (B) / +1.37 (C); strict +0.58 /
+0.73; strict + sequential admission −0.02 (XLV from 2025-12 again the only admission). Extended window: +1.03 / +1.18; +0.55 / +0.67; −0.01.
Block only, 2.5× on $100k, equal gross, extended: anchor held 51 active, 36 up / 15 down, mean +$207, worst −$548, block Sortino 4.2, down in
4 of the universe's 21 down-months; strict 34 active, mean +$134, worst −$390, down in 2 of 21.

**3-month horizon (label = sign of the 3-month forward move; P&L as an overlapping 1/3-notional ladder).** The Stage-1 anchor step admits
no anchor for any sector at this horizon under R1 (Health Care's P/G at H = 3: every populated type is COIN-TOSS, T2 52.9% on 17, T17 61.5% on 13 —
nothing clears the pull bar). Anchor held (the H = 1 choice forced through): XLV 11 at 63.6% = majority; XLF 15 at 86.7% v 73.3 (+13.3, n 15);
XLY 18 at 55.6% = majority; XLE 28 at 60.7% = majority; XLK 3 shorts, 0 of 3; XLI 25 at 68.0% v 72.0 (−4.0); XLB 21 at 47.6% v 52.4; XLP and XLU
silent. Strict: no sector acts (Financials 2 months). Universe with the block, published window: anchor held +0.15 (B) / +0.10 (C); strict 0.00;
block down in 11 of 21 universe down-months (ladder P&L mean +$45/month, worst −$1,515). **Verdict: the 3-month horizon has no instrument;
the one-month ruling (§5.1) stands, now on the full machinery rather than on the anchor-only sweep of §4h.**

### 14.7 Open rulings raised by this section
- **Admission mode**: fixed (anchor as a one-time design choice, R4 exposure 4 × 2 per sector) or strict (anchor by R1 monthly; blind for
  ~5 years on this frame). The document reports both; the board's evidence columns use both; nothing is admitted on either until the tape.
- **Training frontier**: t − 1 (method, horizon 1) or t − 3 (ZION's locked mechanic). §14.6 quantifies the cost.
- **R3 stability**: a tier that qualifies and un-qualifies month to month (Utilities strict, 31 seq-only months) — whether R3 needs a
  hysteresis (e.g., remain admitted for k months once admitted) is an open rule question; no change made.
- **The 12-month gate on a 7-year record**: as written, no sector instrument can be admitted on history; only the tape admits. That is the
  rule working as intended, stated here so it is not mistaken for a defect.

## 15. THE BASE ITSELF — sequential re-derivation of the ZION universe's two legs (2026-09-14, operator request)

### 15.1 Why
The block's "Δ Sortino" is measured against the ZION universe, whose Sortino on the sector window is 7.30 (house definition; 8.76 on the
textbook definition) — a series with a worst 1× month of −2.4% across 2022 and 18 down-months in 62. The house's own backtest note
(`weekly/unified/reports/UNIVERSE_BACKTEST_20260817.md`) states that every component is walk-forward and only the assembly (sleeve
weights, hedge weight, gold and micro weights, leverage 2.54×) is in-sample. Two of the components are not: the **monthly leg** takes its
positions from `status == "pulled"` rows whose pulled TYPE SETS were validated on the whole record (`syzygy_book.py`, RECONCILE TARGETS),
and the **weekly sleeves** fit the horizon sweep, the RED DAWN cascade, ODYSSEY and SANCTUARY on the whole panel (base 1995 → today),
with only the Wilson-LB gate trailing (`combined_book.py::sleeve`). Before any of the Sortino levels in §11 / §14 are used for sizing or
leverage, both legs were re-derived sequentially in the sandbox (nothing under `ZION/reports`, `ZION_RED_DAWN` or `weekly/unified/reports`
was written).

### 15.2 How far back each component can go (data, not algorithm)
| component | earliest honest decision | binding input |
|---|---|---|
| monthly S&P sleeve | 1870s (run from 1970 here) | Shiller panel from 1871 |
| monthly gold sleeve | ≈ 1980 | gold 1968, M2 1959, MIN_TRAIN 60 |
| monthly WTI / silver / dollar | 1993 / 2007 / 1980 | WTI 1986, silver 2000-08, dollar index 1973 |
| weekly SPY / QQQ sleeves | **2007-08** | the engines (`weekly_full_spy.py`) carry a fixed scoring start of 2007-08 on any frame; the horizon sweep needs VIX (1990) plus a design window (first returns an H in 2000–2001 on a 1990 base); QQQ prices 1999 |
| sector CAPE (all nine) | 2014 (2011 on E5) | SEC XBRL from 2009; no pre-XBRL sector earnings in-house |

### 15.3 Harnesses (sandbox)
- `universe_sequential_monthly.py <asset> --start 1970-01-01 [--N6]` — `multiasset_pipeline.run_asset` (unmodified) on the panel truncated
  at every month; position = the last decision row's pulled-type direction or 0 (the book's rule); production emits from the LAST COMPLETE
  row (Shiller earnings lag price by months) so the last row's call is carried into t with the staleness recorded. SPY runs through the
  same grammar (Real_Price / Real_Earnings) with the design-sample N sweep, and with N frozen at 6 as the production cascade froze it.
  ≈ 1 s per refit; 679 months × 5 runs ≈ 45 min in 5 processes.
- `universe_sequential_weekly.py <SPY|QQQ> --from --to --base 1990-01-01` — for every decision week, the horizon sweep, `red_dawn`,
  `odyssey`, `sanctuary` re-run on the panel truncated at t; the convergence for t gated by the trailing record of weeks whose H-week label
  is known at t; positions laid out as production (hold H weeks, non-overlapping, 5 bps). Base 1990 rather than production's 1995 (VIX
  starts 1990; the sweep then first returns an H in 2001; decisions exist only from 2007-08 by the engines' fixed start). ≈ 5–20 s per
  refit; ≈ 3,000 refits in 13 parallel chunks ≈ 1.5 h.
- `universe_sequential_book.py` — assembly: dual throttle (expanding percentiles, PIT as production); sleeve weights = trailing Sortino of the
  throttled sleeves (expanding, ≥ 104 weeks, else equal; production froze full-record Sortinos); 20% 2Y hedge and 7.5% gold as declared
  rules; leverage = min(3, 0.10 / |trailing MaxDD|) expanding (production: 1.232 on the full record; also reported at 1.232 fixed); 5% silver
  micro carried from `locked_book.csv` (screened on the full record — flagged); monthly leg = equal weight of the five sleeves (USD cash);
  universe = 0.5 weekly (monthly-aggregated) + 0.5 monthly. Output `results/sequential_universe/universe_compare.{md,json}` and the
  sequential universe series `universe_sequential_monthly.csv`.

### 15.4 Monthly leg — backtest v sequential
| monthly leg | window | CAGR | Sortino (house) | Sortino (std) | MaxDD | worst month | down-months |
|---|---|---|---|---|---|---|---|
| backtest (`book_ledger.csv`, validated pull sets) | 2007-08 → 2026-07 | 6.14% | 1.79 | 2.52 | −6.4% | −4.4% | 28% |
| sequential, N swept in the design sample | 2007-08 → 2026-07 | **2.26%** | **0.51** | 0.84 | −8.9% | −6.1% | 21% |
| sequential, N frozen 6 (as the SPY cascade) | 2007-08 → 2026-07 | 1.73% | 0.40 | 0.69 | −9.1% | −5.9% | 16% |
| backtest | 1990-01 → 2026-07 | 4.89% | 1.55 | 2.20 | −7.1% | −4.4% | 28% |
| sequential | 1970-01 → 2026-07 | 1.01% | 0.27 | 0.60 | −8.9% | −6.1% | 13% |

Per sleeve, sequential pulls 1970 → 2026 (acted months · 1-month hit): SPY 167 · 62.9% (N frozen 6: 77 · 62.3%); WTI 59 · 62.7%; silver
27 · 59.3%; gold **13 · 46.2%** against 85 validated pulled months in the backtest. The gold sleeve's pull set does not exist point-in-time;
the monthly leg keeps roughly a third of its backtest return and a quarter of its Sortino once the pull sets are honest.

### 15.5 Weekly leg and the universe — backtest v sequential
Weekly decisions, sequential: SPY 482 acted weeks in 257 non-overlapping blocks (first acted 2013 — the gate needs a trailing record that
only begins with the engines' 2007-08 scoring start and does not clear LB > 0.50 until 2013); QQQ 347 acted in 180 blocks (first 2015).
The horizon re-swept each week is not stable: SPY H ∈ {1: 493, 2: 347, 4: 317, 3: 98, 8: 85, 6: 53} weeks; QQQ {1: 718, 2: 442, 8: 94, 6: 58};
production froze H = 2 on the full record. Trailing leverage (min 3, 0.10 / |trailing MaxDD|, from week 104) starts at the 3.0 cap while the
drawdown history is short and ends at 1.09 (production 1.232 fixed) — a rule finding: a trailing DD-cap leverage needs a minimum history or a
prior; the fixed-1.232 variant is reported beside it. Last trailing weights SPY 0.47 / QQQ 0.53 (production ≈ 0.375 / 0.625).

| series | window | CAGR | Sortino (house) | Sortino (std) | MaxDD | worst month |
|---|---|---|---|---|---|---|
| **sector window 2021-06 → 2026-07** | | | | | | |
| universe backtest `uni_1x` (the base used in §11 / §14) | 62 mo | 21.1% | **7.30** | 8.76 | −3.6% | −2.4% |
| universe backtest `zion_universe_book` (50/50 construction) | 62 mo | 16.6% | 5.68 | 5.96 | −3.8% | −2.9% |
| **universe sequential** (both legs re-derived; trailing lev) | 62 mo | **12.2%** | **4.80** | 5.11 | −4.0% | −2.7% |
| universe sequential, SPY N frozen 6 | 62 mo | 11.9% | 4.55 | 5.22 | −4.0% | −2.7% |
| weekly leg backtest | 62 mo | 26.4% | 4.26 | 4.45 | −9.6% | −5.7% |
| weekly leg sequential (trailing lev) | 62 mo | 22.2% | 4.14 | 4.85 | −7.8% | −5.3% |
| weekly leg sequential (lev 1.232 fixed) | 62 mo | 25.2% | 4.12 | 4.79 | −8.8% | −6.0% |
| monthly leg backtest | 62 mo | 7.0% | 1.47 | 3.36 | −4.4% | −4.4% |
| monthly leg sequential | 62 mo | 2.6% | 0.49 | 1.30 | −4.4% | −4.4% |
| SPY buy & hold (price) | 62 mo | 11.8% | 1.15 | 1.27 | −24.8% | −11.6% |
| **universe window 2007-08 → 2026-07** | | | | | | |
| universe backtest `uni_1x` (charted 5.20 std) | 228 mo | 10.7% | 4.02 | 5.13 | −4.0% | −3.5% |
| universe backtest `zion_universe_book` | 228 mo | 9.0% | 3.38 | 4.11 | −3.9% | −3.2% |
| **universe sequential** | 228 mo | **7.2%** | **1.83** | 2.43 | −7.0% | −5.8% |
| weekly leg backtest | 228 mo | 11.8% | 2.35 | 3.16 | −9.6% | −5.7% |
| weekly leg sequential (trailing lev) | 228 mo | 12.1% | 1.58 | 2.26 | −11.9% | −11.5% |
| weekly leg sequential (lev 1.232 fixed) | 228 mo | 11.1% | 2.10 | 2.86 | −8.8% | −7.3% |
| monthly leg backtest | 228 mo | 6.1% | 1.79 | 2.52 | −6.4% | −4.4% |
| monthly leg sequential | 228 mo | 2.3% | 0.51 | 0.84 | −8.9% | −6.1% |
| SPY buy & hold (price) | 228 mo | 9.0% | 0.77 | 0.89 | −52.1% | −20.2% |
| **extended** | | | | | | |
| universe sequential 1993-01 → 2026-07 (weekly leg = hedge + gold + micro before 2013) | 403 mo | 4.9% | 1.47 | 2.20 | −7.0% | −5.8% |
| universe sequential 1970-01 → 2026-07 (monthly S&P + gold only before the 1990s) | 679 mo | 3.0% | 0.97 | 1.73 | −7.0% | −5.8% |

**The sector block on the sequential base** (`portfolio_integration_seq.py --base sequential`; 15% cap, equal gross, published window, 1×):

| block source | base Sortino | with block | Δ Sortino | base CAGR | with block |
|---|---|---|---|---|---|
| backtest block on backtest base (§11) | 7.30 | 8.71 | +1.41 | 21.1% | 24.1% |
| sequential-held block on backtest base (§14) | 7.30 | 8.65 | +1.35 | 21.1% | 22.7% |
| backtest block on **sequential base** | 4.80 | 7.19 | +2.39 | 12.2% | 15.0% |
| sequential-held block on **sequential base** | 4.80 | 6.34 | **+1.54** | 12.2% | 13.7% |
| sequential-strict block on sequential base | 4.80 | 4.95 | +0.15 | 12.2% | 12.9% |
| strict + sequential admission on sequential base | 4.80 | 4.81 | 0.00 | 12.2% | 12.2% |

### 15.6 Reading
1. **The base was inflated the same way the block was.** On the sector window the universe's house Sortino goes 7.30 → 4.80 and its CAGR
   21.1% → 12.2% when both legs are re-derived point-in-time; on the full 2007 → 2026 window 4.02 → 1.83 (5.13 → 2.43 on the textbook
   definition that the charted 5.20 uses) and 10.7% → 7.2%. Worst months roughly double (−3.5% → −5.8% at 1×).
2. **The weekly leg mostly holds; the monthly leg does not.** Weekly: Sortino 4.26 → 4.14 on the sector window, 2.35 → 2.10 (fixed lev)
   on the long window, with CAGR within a few points either way — the trailing gate was already doing most of the work, and the re-swept
   horizon converges on H = 2 once the record is long. Monthly: 1.79 → 0.51, CAGR 6.1% → 2.3%; the gold sleeve's pull set (85 months
   validated) is 13 months point-in-time at 46%. The universe's smoothness came from averaging a strong weekly leg with a monthly leg
   whose calm was full-record membership.
3. **The block's lift is larger on the honest base, not smaller** (+1.54 sequential-on-sequential against +1.35 sequential-on-backtest),
   because the base has more downside to diversify; the ordering across sources is unchanged (backtest > held > strict > admission = 0).
4. **What the leverage rule should read.** The rule is 0.9 × forward Sortino with the charted 5.20 as the backtest anchor and a 25% haircut
   (3.9) as the conservative end (`forward_sortino.py`). The sequential 2007 → 2026 figure is 2.43 on the same definition — below the
   haircut — and 5.11 on the sector window. Neither is a tape number; the tape is still the arbiter (1/12 weeks resolved at the note's date).
   Recommendation: until the tape matures, the leverage rule's backtest anchor should be the sequential 2.43, not 5.20 or 3.9.
5. **Extended history** adds no comfort: the universe sequential from 1993 is 1.47 / 4.9% and from 1970 (effectively the monthly S&P sleeve
   plus gold) 0.97 / 3.0%; the weekly leg cannot be taken before 2007-08 without changing the engines' scoring start, and the sectors not
   before 2014 without pre-XBRL fundamentals.

### 15.7 Findings and open rulings from the base re-derivation
- **B24 (house-level, recorded here because this thread found it):** `UNIVERSE_BACKTEST_20260817.md` states every component is walk-forward;
  the monthly leg's pull sets and the weekly sleeves' fits are full-record. The forward tape was already declared binding, so the operating
  conclusion is unchanged; the backtest levels quoted for the universe are not.
- **Trailing leverage rule:** a DD-cap leverage computed on a trailing record needs a minimum history (it sits at the 3.0 cap for the first
  years); the fixed 1.232 is itself full-record. Open ruling: minimum history (e.g., 5 years) or a prior; reported both ways.
- **Horizon instability:** the weekly sweep's H changes week to week for a decade before settling at 2; production's frozen H = 2 was chosen
  with the whole record. Open ruling: freeze H on a declared design window sequentially (as the N sweep does) rather than re-sweep.
- **Sandbox → promotion:** every script in this section is read-only on production. Promotion of any of it (the leverage anchor, the
  sequential universe series as the sizing base, the monthly leg's role) is an edit to `LOCKED_BOOK_SPEC_20260816.md` and needs the
  operator's authorization; the recommended path is quarterly sequential re-derivation as a job (≈ 2 h compute) with its series stored
  beside the backtest series and labelled.

## Results index (all under `~/Desktop/ZION/sector_volume/`)
- `data/xbrl/xlv_companyfacts.json`, `data/xbrl/xlv_constituent_monthly_close.csv`, `data/fundamentals/lists/*.csv`, `data/fred_*.csv`
- `results/hc_cape_monthly.csv`, `results/hc_cape_companies.csv` — sector CAPE, CAPE5, g10, g5, CAPEG, RealPrice, E10
- `results/hc_oracle_types.json`, `results/hc_oracle_breakdown.json` — Stage-1 four anchors, 27 sub-types, per-direction breakdown
- `results/stage3_hc/` — `HealthCare_type_table.csv`, `HealthCare_cascade_tier.csv`, `HealthCare_month_level.csv`, `HealthCare_run.txt`, `convergence_type_vs_tier.csv`, `integrated_ledger.csv`, `decision.json`, `cassandra*.json`, `sizing.json`, `portfolio_integration.json`, `shadow_netting_ledger_with_health.csv`; `stage3_hc_pretype/`, `stage3_hc_nopull/`, `stage3_hc_sd*/`
- `results/XLV_*.json` (generic-pool and tailored sequential runs, both labels), `results/XLV_money_test*.json`, `results/XLV_recipe*.json` (full driver logs)
- `results/XLV_forward_tape.csv` — the as-issued tape (opened 2026-09-13)
- Report page (volume, sequential board, rotation): https://claude.ai/code/artifact/8c1a6c0a-8954-447a-8a02-44211a5fad76 · PE/PEG lists: https://claude.ai/code/artifact/ce00ea94-239f-4c85-83dd-993e41b8f6e3

## Change log
- 2026-09-28: **R8 AMENDED to PRUNE the cascade** (operator: remove cascade from all sector analyses). integ = pull > tier > abstain; cascade removed (fails LB95>50: 52-57%). Kept-as-last-resort scored higher in-sample Sortino (7.83 vs 5.79 pruned @2.5x) via diversification-of-noise -> pruned on principle. NaN-classification BUG found+fixed in the sandbox flip study (NaN calls mislabeled as flips; the 'flip2=10.5% contrarian / Health-Care-concentration / down-90%' findings were ARTIFACTS and are RETRACTED; corrected clean pull+tier: straight 76.4%, flip1 76.5%, flip2 57.1% n7 = no signal). R9 flip-filter stays OFF (diagnostic only; hurt every sector).
- 2026-09-28: STANDING CASCADE DIAGNOSTIC added — call-stability vs next-month OOS accuracy (straight / flip-once / flip-twice), wired into s8_s10 (historical) and s13 (current-call flip2 caution). Finding (pooled 6 admitted, sequential): straight 70.9% (n175, LB63.7), flip-once 69.0% (n29, LB50.8), FLIP-TWICE 50.0% (n10, LB23.7 — a whipsaw is a coin flip, fails the 50 bar). flip-twice = the call reversed and the prior call had also reversed; it is the rotation-reversal shape that missed in Sept. Candidate rule (held pending n): abstain/halve on flip-twice.
- 2026-09-28: R8 integration reorder (pull > TIER > cascade) wired into the SHADOW sector runner (sector_runner.py s8_s10_integrate + s13_tape); live book untouched; §8 + change log; memory [[zion-move-ovx-throttle-rejected]] chain.
- 2026-09-14: §15 universe re-derivation complete (both legs, universe, block on the sequential base; B24); harnesses `universe_sequential_{monthly,weekly,book}.py`.
- 2026-09-14: §14 backtest v OOS-validated written (fixed / strict / embargo-3 / horizon-3, 63 sequential runs; B23 wrong-branch bug caught and rerun); board page republished with A2 and the sequential universe tables. R7 (sequential evidence, "as in ZION") declared; §7 step 10s; §12.1 step 6b; §12.3 corrected (B20); Addendum B20–B22;
  `sector_sequential.py` (modes fixed / strict; `--embargo 3`; `--horizon 3`) and `portfolio_integration_seq.py` built; §14 results.
- 2026-09-13: document opened after the truncation review; §1–§4 recorded from the session's runs.
- 2026-09-13: §4g full driver run recorded; UnitedHealth_CAPE removed from the pool.
- 2026-09-13: §4h horizon sweep, §4i money test, §4j interim verdict recorded. Steps 1–4 of §6 complete; step 5 (operator verdict + agreement) open.
- 2026-09-13: Addendum A (truncations + non-sector-specific mistakes) added at operator request.
- 2026-09-13: §5 rulings recorded (horizon 1 mo; DECISION gate; CAPE10+CAPE5; current universe; relative tag); §5.5 relative-label rationale.
- 2026-09-13: §4k relative driver + sequential, §4l anchor-only (not powered), §6 rewritten as status.
- 2026-09-13: §4m relative money test; §4n forward tape opened.
- 2026-09-13: §4o Stage-1 ORACLE type analysis, four anchors, both labels; Health Care anchor = PE against Growth; B15 added to Addendum A.
- 2026-09-13: §4p Stage 3 via the S&P's multiasset_pipeline on the selected anchor; pulls, remainder, mirror, current call recorded.
- 2026-09-13: §4p remainder accounting + whole-group (no-pull) tier comparison + month-level overlap check added.
- 2026-09-13: §4p pre-type type-agnostic tier screen (6 genuinely new months) + dead-zone sensitivity table added.
- 2026-09-13: §4q parallel instruments (type pulls vs pre-type tier): overlap / convergence / divergence and per-state OOS scoring; ruling recorded.
- 2026-09-13: §4r integrated instrument adopted (type pulls + post-type cascade + pre-type tier-2 on silent months); money test; current-month read; remaining-abstention accounting (13, 9 down, T19 watch).
- 2026-09-13: §4q divergence detail + abstention-vs-exclusion accounting; §7 the full sector procedure (13 steps) as the template.
- 2026-09-13: §4s engines (ODYSSEY, SANCTUARY) + DECISION on the integrated signal: ACTS; step 14 added to §7.
- 2026-09-13: §4t CASSANDRA (analogue veto → cell-conditioned range, p50 ≈ $175–176 for 2026-10-01); §4u sizing (5% overlay, 0% capital until tape); steps 15–16 added; step 13 reframed as standing dialectic.
- 2026-09-13: §4v shadow portfolio integration (own bucket, throttled, caps hold, universe Sortino +0.69); A7 draft; step 17 added. Health Care complete through the recipe; live wiring pending authorisation.
- 2026-09-13: document committed as the complete record — status header, contents, §7 re-sequenced 0–17, results index, Addendum A B16–B18.
- 2026-09-13: §8 multi-sector rules R1–R6 declared; FRED drivers verified (IPG2211A2S → IPUTIL); `sector_runner.py` built.
- 2026-09-13: §9.1 Energy run: TYPE-INELIGIBLE → WATCH-NONE; §8b runner amendments (R6b predecessor merge, growth v2 fallback, type-ineligible continuation); Energy relative-label P/E anchor (69%, LB 59, short-relative) recorded as an open rule question.
- 2026-09-13: R1 AMENDED to both labels (operator); §9.2 Energy re-run: ACTS as a long/short pair, 5% overlay recommended, current ABSTAIN; pair-sleeve gross finding (6.81× > 6.0× universe cap) logged for R5.
- 2026-09-13: §9.2a fixes F1–F9 required to run Energy; §9.2b relative-anchor detail with the full 27-type table.
- 2026-09-13: R5p pair rule declared (2.5%/leg, both legs count, cap-clip); Energy tables re-issued at the pair weight.
- 2026-09-14: §12 operating procedure (monthly / weekly) written.
- 2026-09-14: §13 consolidated findings, 4.0× row, current suggestion at capped weights, weighting observation, hand-offs to THE INTRUDER and GREEK_WATCH threads.
- 2026-09-14: §9.9 Consumer Staples (tier-only → WATCH); §11 the sector board (all nine) and the integrated portfolio at monthly and weekly level; dashboard proposal; board page published.
- 2026-09-14: §9.8 Industrials: P/E absolute anchor (+14.0); pulls T2 (short) + T23 = 28 months; integrated 30/75 @ 80% LB 63, two-sided (13 shorts @ 77%), ACTS, admitted 5% (universe 7.68 → 8.29); current UP from a thin cascade emission (flagged); metals: copper-shaped, silver-call agreement 5/8 and 7/10 with no shared return stream.
- 2026-09-14: §9.7 Materials: P/E absolute anchor; one pull (T2, all-short); integrated 25/75 @ 72% (76% short), ACTS, NOT admitted (throttled lift −0.05); no overlap with the gold/silver calls; current ABSTAIN.
- 2026-09-14: R1 amended (operator): bad-year test counts years with ≥ 8 calls (was ≥ 4); §9.4a Consumer Discretionary re-run: ACTS two-sided (T2 all-short 85.7%, T14, T22; 36/75 @ 83.3% LB 68, +27.8 vs majority), admitted 5% sleeve (corr +0.01, universe 7.68 → 8.15), current ABSTAIN.
- 2026-09-14: §9.6 Utilities: TYPE-INELIGIBLE — P/G anchor 62.5% +9.7 LB 51 ruled ill-conditioned; g10 ≤ 0 in 40% of months (real earnings decline 2015–19) — the test fired correctly; a floor amendment drafted in error was withdrawn in the same step (B19); T11 (all-short, 72.7% n22) on the record.
- 2026-09-14: R5s short-only overlay rule declared; §9.5a Technology overlay admitted (5%, unthrottled, universe Sortino 7.68 → 8.26; current DOWN → −79 sh XLK shadow).
- 2026-09-14: §9.5 Technology: P/E absolute anchor, 4 pulls (72/75 months), integrated 74/75 @ 75.7% two-sided (21 shorts @ 71%), ACTS, current DOWN; NOT admitted (corr +0.52); short-only overlay logged as an open R5 question.
- 2026-09-13: §10 re-verification (XLV/XLE/XLF) under the corrected parser: all confirmed; HC anchor = Price-to-Growth by the rule; provisional flags lifted.
- 2026-09-13: §9.4 Consumer Discretionary (corrected parser): TYPE-INELIGIBLE (PE anchor +12.6 but fails the year test; T2/T14/T22 on the record, not admitted) → WATCH-NONE.
- 2026-09-13: F10 income-tag truncation found (Booking); parser unioned; XLV/XLE/XLF re-verification launched — all three sector entries and Health Care §3–§4 PROVISIONAL pending comparison; F11 CAPE routing; F12 R5 throttled-lift amendment.
- 2026-09-13: §9.3a Berkshire sensitivity: no structural change (same anchor, pulls, call); keep BRK in.
- 2026-09-13: §9.3 Financials: P/E absolute anchor, pulls T25/T26, integrated 55/82 @ 69.1% = acted up-rate (long-drift character), ACTS, 5% overlay, current UP; BLK/APO predecessors mapped; ERIE dropped (no share count); basic-shares fallback added to the parser; exclusion option (--exclude) for constituent sensitivities.

---

## Addendum A — Truncations and non-sector-specific mistakes in the initial runs (this thread, 2026-09-13)

Kept as a standing checklist. A: recipe truncations inherited from the standing sector board (detail in §0).
B: mistakes that were generic to the method, not to Health Care, made in this thread's first runs before the review.

### A. Recipe truncations (inherited by the first runs)
| # | What was skipped or wrong | Status |
|---|---|---|
| A1 | Enforced driver (`run_asset`) bypassed → auditor never ran | fixed: driver run §4g, 19/19 |
| A2 | Stage 0 data audit not run | fixed (§4g PASS; 1 stale row noted) |
| A3 | Generic 9-leg macro pool, no valuation anchor, no sector drivers | fixed for XLV (§2, §3) |
| A4 | Copper excluded for every sector incl. Materials | fixed in config (re-admitted for XLB only) |
| A5 | No publication lags (IndProd, M2, CPI at data month); emission audit not run | fixed: PIT_LAG + emission audit (§4g) |
| A6 | Horizon hardcoded (6 mo board / 1 mo first sequential run) | fixed: swept {1,3,6} (§4h); freeze pending ruling |
| A7 | Single 50/25/25 split with overlapping 6-month labels reported as accuracy | replaced by sequential harness; non-overlap column added |
| A8 | Act gate = cascade bound ("do not gate on the cascade") | driver DECISION now run; sequential gate ruling open (§5) |
| A9 | Funnel, lifecycle, regime monitor/stress, liquidity regime, valuation family not run | run in §4g |
| A10 | Tier fallback / hybrid never evaluated | tier run in §4g (wf 51.4%); hybrid not evaluated — open |
| A11 | ODYSSEY / SANCTUARY engines and convergence vote not run | run in §4g |
| A12 | Stand-down gate not run | run in §4g (clear) |
| A13 | MIRROR drift guard not run (all-long signal never tested vs always-long) | run in §4g (two-sided 1.55 vs 1.21) |
| A14 | Money test vs buy-and-hold not run | run §4i |
| A15 | Board JSON / dashboard star lead with fitted accuracy and the cascade bound | reporting rule: edge beside drift; dashboard untouched until agreed |

### B. Non-sector-specific mistakes made while building this (B1–B15 first runs; B16–B18 later in the thread)
| # | Mistake | Consequence | Correction |
|---|---|---|---|
| B1 | Built the first sequential harness on the board's generic pool instead of on the driver | every A-item inherited into "the honest test" | driver + tailored pool (§4g–§4h) |
| B2 | Took "volume" as the first sector factor — it is a generic factor with no Stage-1 rationale | a coverage-only leg tested before the sector's own drivers | volume dropped from the leg set (§4a verdict stands) |
| B3 | "All variables" variant left IndProd/M2/CPI unlagged; the "timely" variant *dropped* them instead of lagging | leak carried in one variant, information thrown away in the other | PIT_LAG shifts them; both kept in pool |
| B4 | Hardcoded H=1 in the first sequential run with no sweep (while criticising the board for hardcoding H=6) | horizon never chosen from history | §4h sweep; per-sector horizon rule (§5.1) |
| B5 | Reported the first sequential board as "2008-12 → 2026-07, 212 scored months" | implied acted months across the window; there were none before 2016 | §4h states the effective window 2016-01 → |
| B6 | Sequential harness ran cascade only: no emission audit, engines, DECISION, stand-down, MIRROR, auditor | half the recipe absent from the "honest instrument" | driver run §4g; sequential harness still cascade-only — noted, gate ruling open |
| B7 | Answered "is Health Care the best sector?" from the dashboard conviction star (valb) | valb is the cascade's validation bound, i.e. the gate the recipe says not to use | answer restated on edge-vs-drift; star not used for ranking |
| B8 | Rotation graph momentum unsmoothed; smoothing added after seeing the raw picture | post-hoc parameter (declared at the time) | both shown side by side; neither forecasts (§4f) |
| B9 | Considered the panel's per-stock CAPEs as legs before checking their basis | they rest on ~3 years of EPS | rejected (§1); sector CAPE built from SEC filings (§3) |
| B10 | Sector CAPE first build: growth trend NaN (mixed fiscal year-ends) and real earnings shown in CPI-index dollars | unreadable output | 60%-filed window rule; today's-dollar units |
| B11 | Horizon test §4d uses a single-variable 9-cell grammar, not the 27-type cascade | comparable across predictors, not to the cascade | declared; cascade result in §4h |
| B12 | Survivorship: sector CAPE universe = current members | valuation history biased toward survivors | declared (§3, §5.4); historical membership rebuild deferred |
| B13 | Compared standing 6-month board accuracies with sequential 1-month accuracies in the first report | different tests read as one | incomparability stated in report and here |
| B14 | Early answer on "any prediction right now" mixed three instruments (standing board, cross-sectional screen, rotation) | reader could take a description (rotation) as a call | instruments separated; rotation marked descriptive (§4f) |
| B15 | Stage-1 TYPE analysis not run the ORACLE way: the anchor was fed to the Stage-3 pair grammar as a finished ratio (CAPE10, g10), and the CAPEG single-predictor test used a level×change grid — neither is the S&P's 27 sub-type triple of (ratio, num, den) N-month changes with a frozen N | the sector never had a Stage-1 type table | `hc_oracle_types.py`: faithful ORACLE port on the four operator-specified anchors (§4o) |
| B16 | Claimed the tier layer "run on everything adds nothing the pulls had not captured" before the type-agnostic run existed (the "whole-group" run was still type-conditioned) | a wrong conclusion stated as settled | operator challenge → pre-type run (§4p) found 6 new months; corrected in §4p/§4q |
| B17 | First abstention count read 26 by including the 13 warm-up exclusions as abstentions | abstentions and exclusions-by-rule conflated | separated (§4q, §4r): 13 genuine + 13 warm-up |
| B18 | Pipeline output headers say "3-MONTH" although H = 1 was run (label text inherited from the S&P run) | reader could take the wrong horizon | stated in §4p with the verification-block evidence (frontier gap 1 row) |
| B19 | Wrote that Utilities' growth was "defined and positive" and proposed lowering the CAPEG floor, in the same step that computed g10 ≤ 0 in 40% of months | a rule amendment proposed on a claim the data refuted | paragraph replaced with the numbers; amendment withdrawn; R1 stands |

| B20 | §12.3 said "the sequential machinery re-fits everything from scratch each month inside the runner; there is no frozen cell", as if the ledger were sequential | the ledger's pull set (WF > 67.5% & n ≥ 8 over the whole record) and its anchor (R1 on the whole post-design record) were chosen with the months they then score; a 2020 month "knew" its type's 2026 record | corrected 14 Sep; sequential re-derivation built (§7 step 10s, §14); R7 declared |
| B21 | The block's portfolio figures (§11, §13.2: Sortino 7.30 → 8.79; CAGR at 2.5× / 3.8× / 4.0×) travelled to the shadow-versus-live question without their sequential counterpart | R4 was written down but the numbers were quoted alone | §14: backtest v OOS-validated side by side; the live/shadow ruling waits on the sequential table |
| B24 | The house backtest note for the universe (`UNIVERSE_BACKTEST_20260817.md`) claims all components walk-forward; the monthly leg's validated pull sets and the weekly sleeves' full-panel fits are not | the base every Δ Sortino in this document was measured against was itself full-record | §15: both legs re-derived; universe 7.30 → 4.80 on the sector window, 4.02 → 1.83 on 2007 → 2026 |
| B23 | The harness appended the variant suffix to the mode name before the branch that re-chooses the anchor compared it to "strict", so the first embargo-3 / horizon-3 strict runs silently ran as fixed (identical tapes for XLV and XLY exposed it) | a wrong-branch bug that produced plausible output | caught by comparing the two tapes; fixed (base_mode); the affected 27 jobs rerun |
| B22 | The sequential harness first logged its early months as "error" (ZeroDivisionError in the pipeline's diagnostics printer when no phase-1 decision is scored yet on the truncated frame) | warm-up months mislabelled as failures | classified warm-up in harness and comparison (call 0 either way) |

Rule going forward: a sector run is complete only when every A-item shows RAN in the same driver that wrote the ledger,
and every B-item has a line in the sector's document saying how it was avoided.

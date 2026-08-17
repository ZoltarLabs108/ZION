# ZION UNIVERSE — proper backtest, month by month (2026-08-17)
**229 months, 2007-08 .. 2026-08, monthly basis. Both leverage approaches + SPY buy-and-hold.**

## Final results

| approach | final multiple | CAGR | Sortino | Calmar | MaxDD | worst yr |
|---|---|---|---|---|---|---|
| **ZION universe 2.54× (ADOPTED)** | **123.3×** | 28.70% | 5.20 | 2.87 | −10.0% | −5.8% |
| ZION universe 4.0× (declined) | 1,560.0× | 47.00% | 5.20 | 2.99 | −15.7% | −9.1% |
| SPY buy & hold (price-only) | 5.3× | 9.17% | 0.91 | 0.18 | **−52.1%** | −38% class |

Chart: `universe_vs_buyhold.png` · full monthly series: `universe_monthly_backtest.csv`

## OOS DIAGNOSTICS — what these numbers are and are not

**What is honestly walk-forward (one-step-ahead, train ≤ t−H) in this backtest:**
- Every sleeve signal (SPY/QQQ 3-lens convergence, LB-gated decisions), the monthly SYZYGY calls,
  the silver micro emissions, the throttle/recovery states — all sequential, PIT, no test reuse.

**What is in-sample ASSEMBLY on top of those components (documented selection surfaces):**
- Sortino sleeve weights (frozen from full-record sleeve Sortinos); hedge weight (20%, 10-cell
  sweep); gold overlay (7.5%, 6-cell grid); silver micro weight (5%, 7-variant); Amendment 2/3
  adoption via gates measured on the full record (A3: n=23 events); universe split (50/50 —
  deliberately naive, zero DOF); leverage 2.54× solved on full-record MaxDD.
- Consequence: the CONSTRUCTION is backtest-fitted even though the COMPONENTS are walk-forward.
  This is why the tape is binding.

**Component-level OOS reality (no directional-alpha claims anywhere):**
- SPY convergence 63.3% vs its own drift 62.3% (+1.0pp); QQQ +0.7pp → both sleeves are
  DRIFT-CAPTURE with loss-limiting structure, not alpha. Monthly leg likewise (SPY anchor =
  drift-capture per standing verdict). Silver micro 81%/LB .69 — PROVISIONAL, forward-gated.
  Gold as signal: dropped (coin). NatGas: watch-only (LB .478).
- Search discipline behind the book: 32 declared micro cells lifetime → 1 admission; every
  rejected overlay (MIRROR, conv-TRON, dynamic sizing V1–V3, spreads, GW-5D) is on the record.

**Sub-period honesty (the decade split):** weekly leg flat-lev CAGR 2007–16 ≈ +1.2% (gate burn-in)
vs 2017–26 ≈ +26%. The universe's monthly leg fills that first decade (see the 2007–2015 rows
below — small positive years), but the big compounding is 2017+. Discount forward accordingly.

**Basis disclosures:** SPY B&H shown PRICE-ONLY (with dividends ≈ 7–8×, CAGR ~11% — the honest
benchmark gap is smaller than the chart shows); universe equity legs are also price-only
(symmetric, but the B&H comparison line specifically understates the benchmark). Financing
unmodeled: −~1.5pp/yr at 2.54× (honest ≈ 27%), −~4.5pp/yr at 4×. Monthly leg 1×-flat, uncosted.
**The only true OOS of the assembled book = the forward tape: 1/12 weeks resolved (+0.02%).
Every number above is PROVISIONAL until ~mid-November 2026.**

## Month-by-month — universe @ 2.54× (ADOPTED) (%, monthly basis)

| year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **YEAR** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2007 | — | — | — | — | — | — | — | +1.1 | +7.7 | +1.8 | +0.5 | +3.1 | **+14.7** |
| 2008 | +3.0 | +3.2 | -3.0 | -1.9 | +4.6 | +4.6 | -3.8 | -0.9 | +1.0 | -6.4 | +1.9 | +6.6 | **+8.5** |
| 2009 | +2.8 | +1.5 | -0.3 | -1.1 | +0.9 | -0.5 | +0.2 | -0.3 | +2.2 | +2.5 | -1.4 | +1.3 | **+7.9** |
| 2010 | -1.0 | +0.1 | +2.8 | -2.0 | -0.5 | +0.4 | -0.4 | +1.3 | +1.7 | +1.2 | +1.6 | +3.6 | **+9.0** |
| 2011 | -1.4 | +5.9 | +5.7 | +2.5 | -4.7 | -0.4 | +1.1 | +2.2 | -3.5 | +0.9 | +1.8 | +1.1 | **+11.2** |
| 2012 | +2.2 | +0.9 | -0.7 | -0.8 | -1.0 | +1.0 | +1.0 | +1.2 | +0.5 | -1.4 | +0.7 | +0.6 | **+4.1** |
| 2013 | +0.2 | +0.1 | +0.5 | -1.6 | -0.8 | +0.2 | +4.0 | +0.8 | -1.9 | +0.2 | -0.8 | -0.2 | **+0.3** |
| 2014 | +0.5 | +3.0 | -1.5 | +0.4 | -0.0 | +4.2 | -1.2 | -1.3 | -2.0 | +1.1 | +0.1 | -0.3 | **+2.8** |
| 2015 | +1.6 | -0.7 | +0.1 | -0.2 | -0.0 | -0.3 | -1.4 | -0.8 | +0.2 | +0.7 | -3.6 | -1.5 | **-5.8** |
| 2016 | +0.6 | +1.8 | +1.2 | +5.0 | -0.7 | +8.3 | +1.8 | -2.5 | -0.2 | -1.2 | +2.4 | -0.3 | **+16.8** |
| 2017 | +1.0 | +1.1 | -0.2 | +0.6 | +0.5 | -0.0 | +1.5 | +1.7 | -0.5 | +1.3 | +4.6 | +4.3 | **+16.9** |
| 2018 | +10.8 | +3.5 | +2.6 | +1.8 | +4.8 | +1.8 | +5.2 | +7.6 | -1.9 | -8.1 | +1.5 | +2.1 | **+35.2** |
| 2019 | +16.7 | +6.6 | +4.4 | +5.8 | -8.8 | -1.3 | +6.4 | +1.9 | -2.3 | +6.7 | +3.6 | +6.7 | **+54.5** |
| 2020 | +2.4 | +5.6 | +0.9 | +0.7 | +6.8 | -0.6 | +13.3 | +4.0 | -4.4 | -0.1 | +11.0 | +10.2 | **+60.7** |
| 2021 | +6.7 | +5.7 | +9.0 | +9.0 | +0.8 | +6.0 | +5.8 | +4.9 | +0.3 | +6.4 | -1.2 | +12.5 | **+88.6** |
| 2022 | -1.8 | +4.6 | +4.2 | -4.9 | -0.1 | -0.4 | +9.3 | +3.1 | +0.1 | -0.6 | +6.7 | +0.9 | **+22.3** |
| 2023 | +17.8 | -3.9 | +16.0 | +1.3 | +7.1 | +7.0 | +4.3 | -6.1 | -2.6 | -0.4 | +17.2 | +7.6 | **+82.7** |
| 2024 | +4.6 | +5.0 | +3.6 | -2.4 | +6.0 | +7.1 | -1.1 | +8.8 | +10.9 | +2.7 | +4.1 | +3.0 | **+65.7** |
| 2025 | +1.8 | -2.3 | -5.3 | +0.9 | +19.1 | +7.4 | +4.9 | +4.4 | +12.4 | +7.5 | +3.4 | +2.5 | **+70.3** |
| 2026 | +0.4 | -1.7 | -0.7 | +25.3 | +11.6 | -5.7 | -1.5 | +7.9 | — | — | — | — | **+37.2** |

## Month-by-month — universe @ 4.0× (examined, declined) (%, monthly basis)

| year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **YEAR** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2007 | — | — | — | — | — | — | — | +1.7 | +12.1 | +2.9 | +0.7 | +4.8 | **+23.8** |
| 2008 | +4.8 | +5.0 | -4.7 | -3.0 | +7.2 | +7.3 | -5.9 | -1.4 | +1.6 | -10.0 | +2.9 | +10.5 | **+12.9** |
| 2009 | +4.5 | +2.4 | -0.5 | -1.7 | +1.4 | -0.8 | +0.3 | -0.5 | +3.5 | +3.9 | -2.3 | +2.0 | **+12.6** |
| 2010 | -1.6 | +0.2 | +4.4 | -3.1 | -0.8 | +0.6 | -0.7 | +2.1 | +2.7 | +1.9 | +2.5 | +5.6 | **+14.4** |
| 2011 | -2.2 | +9.3 | +9.0 | +3.9 | -7.4 | -0.6 | +1.8 | +3.4 | -5.5 | +1.4 | +2.9 | +1.7 | **+17.6** |
| 2012 | +3.5 | +1.5 | -1.2 | -1.3 | -1.6 | +1.5 | +1.5 | +1.9 | +0.8 | -2.2 | +1.0 | +1.0 | **+6.5** |
| 2013 | +0.3 | +0.1 | +0.8 | -2.6 | -1.3 | +0.3 | +6.3 | +1.2 | -3.1 | +0.2 | -1.3 | -0.3 | **+0.3** |
| 2014 | +0.8 | +4.7 | -2.4 | +0.7 | -0.1 | +6.6 | -1.9 | -2.0 | -3.1 | +1.7 | +0.1 | -0.4 | **+4.3** |
| 2015 | +2.6 | -1.1 | +0.2 | -0.3 | -0.0 | -0.4 | -2.2 | -1.3 | +0.3 | +1.0 | -5.7 | -2.3 | **-9.1** |
| 2016 | +0.9 | +2.8 | +1.9 | +7.8 | -1.2 | +13.1 | +2.8 | -3.9 | -0.3 | -1.9 | +3.7 | -0.4 | **+27.1** |
| 2017 | +1.6 | +1.8 | -0.3 | +0.9 | +0.7 | -0.1 | +2.3 | +2.6 | -0.7 | +2.1 | +7.2 | +6.8 | **+27.7** |
| 2018 | +17.1 | +5.6 | +4.1 | +2.8 | +7.6 | +2.8 | +8.1 | +12.0 | -3.0 | -12.8 | +2.4 | +3.3 | **+58.6** |
| 2019 | +26.3 | +10.4 | +6.9 | +9.2 | -13.8 | -2.1 | +10.1 | +3.0 | -3.7 | +10.5 | +5.6 | +10.5 | **+93.6** |
| 2020 | +3.8 | +8.9 | +1.4 | +1.1 | +10.7 | -1.0 | +21.0 | +6.3 | -6.9 | -0.1 | +17.3 | +16.0 | **+106.9** |
| 2021 | +10.6 | +9.0 | +14.1 | +14.1 | +1.3 | +9.5 | +9.1 | +7.7 | +0.5 | +10.1 | -1.8 | +19.7 | **+166.1** |
| 2022 | -2.8 | +7.2 | +6.6 | -7.7 | -0.2 | -0.6 | +14.7 | +4.9 | +0.1 | -0.9 | +10.5 | +1.5 | **+36.2** |
| 2023 | +28.0 | -6.1 | +25.2 | +2.0 | +11.2 | +11.0 | +6.7 | -9.6 | -4.1 | -0.6 | +27.1 | +11.9 | **+148.1** |
| 2024 | +7.3 | +7.9 | +5.7 | -3.8 | +9.5 | +11.2 | -1.7 | +13.9 | +17.2 | +4.2 | +6.4 | +4.7 | **+118.2** |
| 2025 | +2.8 | -3.7 | -8.4 | +1.4 | +30.1 | +11.6 | +7.6 | +6.9 | +19.6 | +11.8 | +5.4 | +3.9 | **+125.2** |
| 2026 | +0.6 | -2.6 | -1.1 | +39.8 | +18.2 | -9.0 | -2.4 | +12.4 | — | — | — | — | **+59.9** |
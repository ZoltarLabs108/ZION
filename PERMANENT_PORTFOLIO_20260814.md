# Permanent Portfolio sleeve — structural, non-predictive (2026-08-14)
Window: 1986-02..2026-07 (n=486 months; starts when WTI leg begins).

## Configurations (monthly-rebalanced; ann=CAGR, dd=max drawdown, posyr=fraction of years positive)
| config | CAGR | vol | maxDD | +years | Sharpe | Sortino | worst year |
|---|---|---|---|---|---|---|---|
| Classic-4 EW (Browne) | 6.5% | 4.9% | -14.1% | 83% | 0.64 | 1.01 | -7% (2022) |
| Classic-4 EW + throttle | 6.7% | 4.7% | -10.4% | 85% | 0.71 | 1.26 | -7% (2022) |
| 5-leg EW | 6.9% | 8.6% | -25.6% | 78% | 0.41 | 0.64 | -14% (2008) |
| 5-leg EW + throttle | 7.2% | 8.1% | -21.1% | 78% | 0.47 | 0.80 | -10% (2015) |
| 5-leg risk-parity | 3.6% | 1.2% | -1.2% | 100% | 0.22 | 0.10 | 0% (1986) |
| 5-leg risk-parity + throttle | 3.6% | 1.2% | -0.6% | 100% | 0.23 | 0.10 | 0% (1986) |

## Blind-month behaviour (the 268 months the ZION book has NO signal)
- 5-leg EW+throttle in blind months: mean **+0.43%**/mo, **58%** positive (n=268).
- vs signal months: mean +0.82%/mo, 65% positive.
- Read: the structural sleeve earns through the blind months WITHOUT predicting them — the whole point.

## 2022 stress (the year the "always positive" claim breaks)
- 5-leg EW+throttle 2022 return: **-0.2%**
| leg | 2022 return |
|---|---|
| Equities | -16.3% |
| LongBonds | -13.6% |
| Gold | +1.1% |
| Commodities | +23.9% |
| Cash | +1.7% |

Confirms the honest caveat: in a synchronized rate/inflation shock (2022) equities, bonds AND gold fall together — only cash (and sometimes commodities) win. PP is high-hit-rate risk reduction, NOT a guarantee.

## Honest caveats (do not skip)
- Equities = SP_Price PRICE-ONLY (no dividends) → understates the equity leg ~2%/yr; real PP CAGRs are higher.
- Long bonds = 10Y constant-maturity TR PROXY (carry + dur8·−Δyield), not an actual bond index.
- Cash = Fed funds accrual. Monthly rebalancing (Browne rebalances annually/at bands → slightly different).
- Throttle uses NFCI fixed thresholds (documented); swap for ZION v3.2 composite to match production.
- Window starts at the WTI leg; classic-4 could extend earlier (gold 1970s) — reported on the common window for comparability.
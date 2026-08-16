# SYZYGY × PP abstain-fallback — full-record effect (2026-08-14)
Book months: 440 (1990-01..2026-08). PP deployed ONLY on all-cash (n_fired==0) months; acted months unchanged.

## BASE (rules only)
- all-cash months converted to PP: **90** of 440 (20%); PP mean there **+0.26%/mo**, 60% positive.
| metric | book (cash on abstain) | book + PP-fallback | Δ |
|---|---|---|---|
| CAGR | 4.88% | 5.54% | **+0.66pp** |
| Sortino | 2.20 | 2.16 | **-0.04** |
| MaxDD | -7.1% | -8.4% | -1.3pp |
| Calmar | 0.69 | 0.66 | -0.03 |

## BASE + commodity-tail PP
- all-cash months converted to PP: **90** of 440 (20%); PP mean there **+0.12%/mo**, 54% positive.
| metric | book (cash on abstain) | book + PP-fallback | Δ |
|---|---|---|---|
| CAGR | 4.88% | 5.17% | **+0.29pp** |
| Sortino | 2.20 | 1.83 | **-0.37** |
| MaxDD | -7.1% | -9.8% | -2.7pp |
| Calmar | 0.69 | 0.53 | -0.16 |

## CELLS variant
- all-cash months converted to PP: **82** of 440 (19%); PP mean there **+0.27%/mo**, 59% positive.
| metric | book (cash on abstain) | book + PP-fallback | Δ |
|---|---|---|---|
| CAGR | 5.31% | 5.92% | **+0.61pp** |
| Sortino | 2.25 | 2.21 | **-0.04** |
| MaxDD | -7.1% | -8.4% | -1.3pp |
| Calmar | 0.75 | 0.70 | -0.05 |

## Permanent integration (one change in `syzygy_book.assemble_book`)
In assemble_book, after computing `book_r`, on all-cash months substitute the PP return:
```python
# abstain-fallback: hold PP structure instead of cash when no sleeve fires
if fired == 0 and np.isfinite(pp_r.get(d, np.nan)):
    book_r = float(pp_r[d])            # pp_r = precomputed Browne-4+throttle monthly series
```
PP is non-predictive; judge on Sortino/MaxDD above, never on directional accuracy.

## Caveats (carried from the PP build)
- Equities price-only (no dividends) → understates ~2%/yr; real uplift larger.
- 10Y-TR proxy + Fed-funds cash; throttle = NFCI fixed thresholds (swap for v3.2 composite).
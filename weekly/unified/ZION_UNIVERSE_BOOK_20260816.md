# ZION UNIVERSE BOOK — weekly × monthly combined (ADOPTED 2026-08-16)
**Operator ruling: combine the two ZION cadences, 50/50. The naive split is deliberate — zero
selection degrees of freedom. Per-instrument netting = the remaining production step.**

## 1. Components (each separately validated, near-orthogonal)

- **Weekly leg:** the LOCKED unified book + Amendment 1 (Sortino-wt SPY/QQQ, 20% 2Y hedge, dual
  VIX/credit throttle, 1.220×, 5% silver micro, 7.5% gold overlay). `LOCKED_BOOK_SPEC_20260816.md`.
- **Monthly leg:** SYZYGY base (5-sleeve monthly: SP/Gold/Silver/WTI/USD certified rules, 1× flat,
  cash on abstain). `syzygy_book.py` / `reports/book_ledger.csv`.
- **Measured correlation: +0.20** (monthly basis, 229 overlapping months 2007–2026). Different
  cadences, different acted periods, different sleeves — the books make money in different months.

## 2. The numbers (monthly basis, 229 months)

| book | CAGR | Sortino | MaxDD |
|---|---|---|---|
| weekly leg (monthly agg) | 11.80% | 3.18 | −9.6% |
| monthly SYZYGY base | 6.12% | 2.52 | −6.4% |
| **UNIVERSE 50/50** | **9.05%** | **4.13** | **−3.9%** |

**95% of years positive; worst year −2.3% (2015). Positive through BOTH crises: 2008 +3.5%,
2022 +4.5%.** The Permanent-Portfolio ambition — something is always up — achieved via structure.

## 3. The finding that makes this more than diversification arithmetic

**The monthly leg fills the weekly leg's dead decade.** The weekly book alone made ~0% 2007–16
(gate burn-in); the universe book's 2007–15 years are +5.1/+3.5/+3.1/+3.5/+4.4/+1.7/+0.3/+1.1/−2.3
— carried by the monthly sleeves. Cross-cadence decorrelation is **temporal**, not just
cross-sectional: the two systems' evidence windows are complementary, which also softens (not
removes) the weekly leg's decade-concentration caveat at the universe level.

## 4. Production requirements before shared capital

1. **Per-instrument NETTING** (SYZYGY's standing mandate): both legs can hold SPY/gold
   simultaneously; net exposures per instrument across cadences, cap the netted gross. Corr +0.20
   says practical overlap is small, but the netting ledger must prove it week by week.
2. **Both-bases reporting** stays law: weekly-basis Sortino for the weekly leg (2.56), monthly-basis
   for comparisons (this doc). Never quote the monthly-agg 3.18 as the weekly leg's own number.
3. Costs asymmetry disclosed: weekly leg 5bps modeled; monthly SYZYGY is uncosted 1×-flat.
   Financing on the weekly leg's 1.22× unmodeled (~−0.6%/yr at the 50% share).
4. **Forward tape binding** for: silver micro (its 12-Friday window), the gold overlay, and the
   universe combination itself — the 50/50 book goes on the as-issued tape before capital treats
   the 4.13 as real.

## 5. Honesty box
Both legs are structure/drift-capture, not directional alpha (weekly: conv≈drift; monthly: SPY
anchor = drift-capture, per standing verdicts). The universe Sortino 4.13 is earned by
decorrelation across cadence — the same second-moment edge as everything else that survived this
build. Ledger: `reports/zion_universe_book.csv`.

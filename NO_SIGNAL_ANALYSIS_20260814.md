# No-signal months — regime, tradability, and the inverse-layer question (2026-08-14)

Blind (no-signal) months: **268** · signal months: **171**

## (2) What regime are the blind months? (descriptive, exogenous — zero overfit risk)
| regime var | blind mean | signal mean | Δ |
|---|---|---|---|
| VIX level | 20.41 | 18.08 | +2.33 |
| NFCI (fin. conditions, +=tight) | -0.33 | -0.51 | +0.18 |
| Dollar 12-mo % | 0.69 | -0.22 | +0.91 |
| Real 10Y rate | 1.76 | 1.20 | +0.55 |
| Term spread 10Y-2Y | 1.00 | 1.00 | -0.01 |
| Fed funds | 3.25 | 2.33 | +0.92 |

Read: if blind months don't differ much from signal months on these, the book's blindness is NOT a clean exogenous regime — it's idiosyncratic, and no regime risk-rule cleanly separates it.

## (3) Is there anything real to trade in the blind months?
- SPY next-month up-rate IN blind months: **65%** (n=268) vs all-months ~64%.
- So even a naive 'always long SPY' in blind months would be ~65% — that's the drift floor any 'blind-month signal' must beat to be real, not just re-captured drift.

## (4) NUCLEAR SWEEP — INTEL ONLY (this is a multiplicity demo, NOT a result)
Brute-forced **215** `*_Return_6M` predictors vs SPY direction in blind months (best of sign/−sign each).
- **0 predictors ≥70%**, **2 ≥65%** — out of 215 searched.
- Under pure noise you EXPECT ~17+ to clear 70% by chance on this n; a big hit-count is the winner's-curse signature, not discovery.

Top 12 "matches" (INTEL — presumed noise until independently re-discovered out-of-search):

| predictor (6-mo change) | acc in blind mo | n | Wilson-LB |
|---|---|---|---|
| Visa | 66% | 110 | 0.57 |
| Cisco | 65% | 261 | 0.59 |
| LT | 64% | 149 | 0.56 |
| Axis_Bank | 63% | 188 | 0.56 |
| France_ETF | 62% | 203 | 0.55 |
| Google | 61% | 135 | 0.53 |
| AEX_25 | 61% | 236 | 0.55 |
| Meta | 61% | 88 | 0.51 |
| Royal_Bank_CA | 61% | 211 | 0.54 |
| Bajaj_Finance | 61% | 149 | 0.53 |
| Netflix | 61% | 151 | 0.53 |
| Morgan_Stanley | 61% | 232 | 0.54 |

Even the TOP match's Wilson-LB is 0.57 — and it's the MAX over 215 tries, so its honest search-corrected LB is far lower. Treat all of the above as noise-shaped-like-signal.

## (5) Verdict: worth adding as an inverse layer?
- The blind months are NOT a clean exogenous regime (see §2).
- SPY drifts ~65% in blind months, so any 'edge' there must clear that drift floor.
- The nuclear sweep produces 2 high matches from noise — exactly the residual-fishing trap.
- **Conclusion:** a *directional* inverse layer is NOT justified — you'd be trading the residual, and the sweep shows that residual yields confident noise. The only defensible use of the blind-month structure is a **risk/abstention overlay** IF §2 shows a clean regime (size down / stay flat when the book is structurally blind), never a directional bet. Decision gates on §2, not on the sweep.
# DECISION review — voice agreement + no-signal months (2026-08-14)

## SPY monthly — RED DAWN / ODYSSEY / SANCTUARY  (n=439 decision-months, 1990-01..2026-07)

- **RED DAWN** present 435/439 months · standalone dir acc 63.4%
- **ODYSSEY** present 94/439 months · standalone dir acc 57.4%
- **SANCTUARY** present 397/439 months · standalone dir acc 59.2%

| convergence state | months | share | next-month acc |
|---|---|---|---|
| **UNANIMOUS (≥2 present, agree)** → ACT | 282 | 64% | **66.0%** (LB 60%) |
| SPLIT (≥2 present, disagree) → ABSTAIN | 118 | 27% | — (no call) |
| THIN (<2 engines present) → ABSTAIN | 39 | 9% | — (no call) |

- **CORE (all 3 present & unanimous):** n=54 · acc 66.7% · LB 53%

- pairwise agree RD~OD (both present, n=93): 71%
- pairwise agree RD~SC (both present, n=394): 75%
- pairwise agree OD~SC (both present, n=87): 69%

---

## Book-level NO-DECENT-SIGNAL months (integrated 5-asset ledger, n=439)
Months where **no asset** (SP500/Gold/Silver/WTI/USD) clears its DECISION gate — `n_acting==0`.

- **268 of 439 months (61%)** have zero acting assets.
- by decade:
    - 1990s: 87/120 months no-signal
    - 2000s: 82/120 months no-signal
    - 2010s: 51/120 months no-signal
    - 2020s: 48/79 months no-signal

First 24 no-signal months (full list in decision_review_nosignal.csv):

| Date | SP500 | Gold | Silver | WTI | USD |
|---|---|---|---|---|---|
| 1990-01 | ↑ | ↑ | — | — | ↓ |
| 1990-02 | ↓ | ↓ | — | — | ↓ |
| 1990-03 | ↓ | ↑ | — | — | ↓ |
| 1990-04 | ↓ | ↑ | — | — | ↓ |
| 1990-05 | ↑ | ↓ | — | — | ↓ |
| 1990-06 | ↑ | ↓ | — | — | ↓ |
| 1990-07 | ↑ | ↓ | — | — | ↓ |
| 1990-08 | ↑ | ↑ | — | — | ↓ |
| 1990-09 | ↑ | ↓ | — | — | ↑ |
| 1990-10 | ↑ | ↓ | — | — | ↑ |
| 1990-11 | ↑ | ↓ | — | — | ↑ |
| 1990-12 | ↑ | ↓ | — | — | ↓ |
| 1991-01 | ↑ | ↓ | — | — | ↓ |
| 1991-02 | ↓ | ↓ | — | — | ↓ |
| 1991-03 | ↑ | ↑ | — | — | ↓ |
| 1991-04 | ↑ | ↓ | — | — | ↓ |
| 1991-05 | ↑ | ↑ | — | ↓ | ↑ |
| 1991-06 | ↑ | ↑ | — | ↓ | ↑ |
| 1991-07 | ↑ | ↑ | — | ↓ | ↓ |
| 1991-08 | ↑ | ↑ | — | ↑ | ↑ |
| 1991-09 | ↑ | ↑ | — | ↓ | ↑ |
| 1991-10 | ↑ | ↓ | — | ↓ | ↑ |
| 1991-11 | ↑ | ↑ | — | ↑ | ↓ |
| 1992-03 | ↑ | ↑ | — | ↑ | ↓ |

---

## What is NOT built (stated, not faked)
- **Gold / Silver three-VOICE ledgers**: do not exist. Only their RED DAWN cascades are computed (`reports/Gold_*`, `reports/Silver_*`). The ODYSSEY/SANCTUARY voices are SPY-wired in `engines.py` (`load_spine()` = SP). Running them per-asset needs gold/silver spines built to the engine schema — a real build, not a read.
- **Weekly convergence (any asset)**: not computed. `weekly/` holds only `ZION_WEEKLY_RECIPE.md` (a spec). No weekly voice ledger exists, so weekly agree/disagree cannot be shown without building the weekly pipeline.
- The book-level no-signal months above use the integrated 5-asset **final** DECISION (real), which is the right input for the "match an asset to the missing months" step.
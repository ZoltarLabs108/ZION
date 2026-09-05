# Cascade Separator Method — first-level predictor discovery (ARION→ZION, 2026-09-05)

A clean, reusable procedure for finding what predicts a **binary outcome** (e.g. "horse finishes 4th",
"pick_hit", "month up") and recursively tiering it — the front end that feeds ZION's gated cascade
(`reddawn_cascade_full.py` / ARION `arion_cascade.py`). Written up at operator request after it correctly
found a 4th-place predictor ARION's coarse ranking had missed.

## Stage 0 — the separator (find the level-1 predictor)
**The critical design choice is the comparison POOL.** To learn "what makes the 4th-place horse," do NOT
compare 4th vs the whole field (the top-3 winners drown it — it looks average). **Restrict to the relevant
pool** (here: horses that did NOT make the top 3) and ask what separates the target (4th) from the rest of
that pool (5th+). Getting the pool wrong is why a naive mean-rank test wrongly reported "no signal."

1. Join outcome (real result) to **point-in-time** features (no look-ahead — ARION uses bet_time_snapshot).
2. Restrict to the comparison pool; require a minimum pool size.
3. **Within-pool z-score** each candidate factor (subtract pool mean, ÷ pool SD) so races/cells pool cleanly.
4. Label target=1, rest=0. For each factor: **Welch t-test + Cohen's d** (effect size).
5. **Translate d → strength, and gate on STRENGTH not significance.** r = d/√(d²+4); R² = r². This is the
   ZION currency. A large-n t-test gives tiny p on a useless signal — e.g. d=0.49 → r≈0.24 → **R²≈0.06**,
   which fails even the explore gate (0.10). **Significance ≠ strength; ZION gates on R²/Wilson-LB precisely
   to reject "significant but weak."**

## Stage 1..N — recursive tiering (break the predictor down)
Greedy recursive split, keep the predictive branch, up to N tiers (we used 4). **Do NOT pre-partition into
many regime sub-types (e.g. the 27-type split) when data is thin — it starves every cell.** Recurse on the
whole pool instead.

At each node: search factors × thresholds; pick the split maximizing **point-biserial R²** with the target
(subject to min-n). Keep the elevated-hit branch, drop that factor, recurse. Report each tier:
`rule (conjunction) | n | hit% | Wilson-LB | R² | zone`.

Worked example (4th-place target, one day, n=390 pool, base 20%):
```
tier1 favored(odds z≥+0.3)                         n176 30%  R2 .049
tier2 + best-speed-at-dist≥+0.9                    n36  47%  R2 .036
tier3 + class≥+0.8                                 n24  58%  R2 .099
tier4 + late-pace≥+0.5                             n18  72%  WilsonLB 49%  R2 .238  <-- clears confirm-R2
```
The conjunction (favored + fast + classy + closing) isolates a 72%-hit subgroup a flat separator (R²~0.06)
could never see. **This is what recursion buys: thresholded conjunctions expose structure linear correlation
hides.**

## Gates — EXPLORE vs CONFIRM (the honesty line)
- **EXPLORE** (discovery): R²≥0.10, min-n≥5, Wilson dropped, composites allowed. Surfaces candidates.
- **CONFIRM** (promotable): R²≥0.20, **Wilson-LB above base**, n≥8, **WALK-FORWARD out-of-sample**.
- **Greedy in-sample search manufactures R².** Searching factors×thresholds×tiers guarantees *some* high
  in-sample R² (the tier-4 .238 above is a fit, n=18, one day). It is EXPLORE-grade until it survives
  **walk-forward** — that is the whole reason ZION's confirm gate is OOS, not in-sample R². Never promote a
  greedy-fit tier without it. Sign-flip anti-predictive factors; build a correlation-weighted composite only
  when no single factor clears.

## One-line takeaway
Restrict the pool → within-pool z → t/d but **gate on R² (strength), not p** → recurse into thresholded
conjunctions for hidden tiers → **confirm only on walk-forward OOS + Wilson-LB.** Significance is cheap;
strength and out-of-sample survival are the product.

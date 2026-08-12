# HYACINTH_X program → ZION calculation map (extractor-verified)

Calc steps referenced: 1 audit · 2 features · 3 target · 4 cell-encode · 5 fold-loop(a select→b fit→c conviction→d emit) · 6 OOS stream · 7 OOS acc · 8 coverage guard · 9 convergence · 10 null/placebo · 11 money · 12 annualize · 13 risk · 14 magnitude · 15 rupture.

| HYACINTH_X program | ZION calc / stage | Role | Keep / Replace |
|---|---|---|---|
| **1 ORACLE** | 4 (cell encode) | Builds predictor lookup / rich map | Keep encoding |
| **2 HYPERION** *(tentative)* | 2 (features) | Panel/feature assembly | Confirm |
| **3 RED DAWN** | 5b–5c (fit, tier) | Four-model cascade WITHIN each of 27 CAPE-types: `classify_cape_type` (27-type sign grammar, ±0.5% dead zone) + `analyze_type` (primary/secondary/model-3/model-4 threshold partition, each with Wilson one-sided flip). **Core model.** | KEEP: 27-type grammar + train-majority-direction + Wilson-LB gate (`grammar27`/`_tern_train`, lib_pipeline 399–442). REPLACE: full-history in-sample fit (HYACINTH_X) and 50/25/25 blocks (port) → walk-forward folds |
| **4 ODYSSEY** | 9 (convergence) | 6-bin pattern-analogue **direction vote + confidence**; one vote in k≥2 agreement gate. NOT a multiplier (size=1.0). PIT fix = Oligon merge_asof backward-93d | KEEP as one convergence vote; re-fit bins in-fold. Do not treat as conviction scaler |
| **5 SANCTUARY** | 14 (magnitude) | Generates historical analogue list (`SANCTUARY_ALL_MATCHES.csv`) | Keep analogue engine; feed CASSANDRA |
| — **CASSANDRA** | 14 (magnitude) | Direction-conditional magnitude: filter analogues to DECISION-matched M+1 direction, top-3 by similarity, similarity-weighted forward return → range. Fallback 10y same-dir mean. **Publish tier-conditioned RANGE only; VETO if it can't beat drift/zero** | Keep direction-conditional machinery + range-only + veto. Its OOS must also be walk-forward |
| **6 INTERSTELLAR** | gate before 8 (act/abstain) | Liquidity/regime-stress conditioning + throttle (throttle never sizes) | Keep as conditioning gate |
| **7 TRON** | 11–12 (money/sizing) | Per-asset payoff layer: direction+conviction → position/payoff | Keep per-asset; re-derive under WF |
| **8 CONVERGENCE** | 9 (convergence) | Multi-engine agreement + forward scoring | Keep; this is the Stage 4 host |
| **DECISION** | 5d/9 (emit/decision) | Direction decision under k≥n convergence gate (`decision()`) | Keep gate logic; re-fit in-fold |
| **9 ARTEMIS** | 10 (placebo) — SEPARATE HORIZON | 1-**year** equity cross-section selector + placebo method. NOT in the 1-month spine | Borrow placebo discipline only |
| **10 MIRROR** *(tentative)* | validation | Reflection/self-consistency check | Confirm |
| **SYZYGY** *(tentative)* | assembly | Sits DECISION→CASSANDRA→**SYZYGY**→LEDGER; likely aligns direction+magnitude into emitted call | Confirm |
| **11 TEARS IN RAIN** | 8b (freeze) | Freeze architecture — satellites frozen, as-issued emission freeze | Keep freeze discipline |
| **12 HAL** | 8a (live runner) | Live emission + freshness guard (stale row → NO_SIGNAL) | Keep freshness guard |
| **13 MIMESIS** | 8b–8c (freeze+resolve) | **The as-issued ledger — the ONLY genuine OOS today.** score_prior_month / archive_current_predictions / _update_ledger; frozen at issue, scored next month, never revised | Keep as forward-OOS ground truth |

## Load-bearing finding
No true purged walk-forward exists in HYACINTH_X. Discovery is full-history in-sample; WF/permutation gates are disabled dead code (RED_DAWN 2482–2488). All port "walk-forwards" are single contiguous tail splits (50/25/25, split=0.65) = the contaminated family. The as-issued ledger (MIMESIS) is the only real OOS. **ZION Stage 3 is the ecosystem's first real walk-forward.**

## Contamination boundary (what NOT to reproduce)
- HYACINTH_X full-history fit of thresholds/flips/accuracies (`analyze_type`, `cape_type_accuracy`).
- Port fixed blocks: `U[:50]/[50:75]/[75:]` (discovery/cascade/tier), `split=0.65` tail (lib_spy).
- Any floor/threshold tuned after seeing TEST.

## Still tentative (need one quick read)
HYPERION (calc 2?), MIRROR (validation?), SYZYGY (assembly?), and ORACLE's exact build role.

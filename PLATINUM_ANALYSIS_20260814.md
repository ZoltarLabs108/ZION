# Platinum monthly — ANALYSIS & VERDICT (post stress-test)
### 2026-08-14. Supersedes the integration plan in `PLATINUM_INTEGRATION_20260814.md`.

## VERDICT: ABSTAIN — do not integrate, not even at shadow. The "confirmed" edge failed the multiplicity stress test.

Earlier today I called a **CONFIRMED regime break in platinum** (pre-2011 industrial cells at
80–94% out-of-selection, dead post-2011) and drafted a ZION shadow integration around it. A
multiplicity stress test (`platinum_recheck.py`) **refutes that confirmation.** Reverting to
abstain, consistent with silver and the session's overfit-wall theme.

## The stress test (what broke the claim)

Re-ran the *same* out-of-selection de-bias across the **entire emission-legal universe** (15
TIMELY, non-CONTAM variables), not just the 4 hand-picked cells:

| finding | result | meaning |
|---|---|---|
| **(1) Emission-legal cells surviving out-of-selection** | **719** survive, **381 "CONFIRMED" (LB>0.50)** | not 4 special cells — hundreds "confirm" |
| **signature** | nearly all post **pre→100% on n=12–15** | 100% on tiny n across hundreds = search-multiplicity noise, not edge |
| **(4) break dates** | only **288/719 (40%) in 2010–2012; median 2013** | the "clean 2011 break" was cherry-picked from the top cells |
| **(2) flag contamination** | copper 12-mo vs WTI 12-mo corr **+0.44** | the copper flag partly proxies WTI — the signal in the one live cell |
| **(3) episode clustering** | 175 flag-ON months = **~16 independent episodes** | arming-test n's (n53, n63) rest on ~16 episodes → effective n tiny |

## The methodological lesson (why I was wrong)

The de-bias split (set direction on early-pre, test on late-pre) corrects the **within-cell
direction** degree of freedom. It does **NOT** correct the **cross-cell search** — choosing these
pairs/k/w/types out of thousands. Run the same "confirmation" across the whole search and it
rubber-stamps 381 cells at 100%/n13. **An out-of-selection test that isn't out-of-*search* is not
a real confirmation.** The `regime_vs_latency` "CONFIRMED" verdict must be read this way from now on:
it rules out one DOF, not the search. This is the in-sample→OOS overfit wall wearing a
"regime-break" costume.

## What about 2011 — is anything real there?

Two levels, kept separate:

- **Macro history: yes, real.** The 2000s commodity super-cycle peaked ~2011; platinum's diesel
  auto-catalyst thesis genuinely deteriorated (dieselgate 2015, EV pivot). Copper is **+49.3%** over
  12 months *right now*, so the complex is arguably re-engaged. These are real facts.
- **Cell-level tradable edge: no.** We **cannot** extract a multiplicity-survived monthly directional
  cell from that history. The break dates are diffuse (median 2013), and the "pre-edge" cells are
  indistinguishable from selection noise. Real macro story ≠ a signal you can trade.

So 2011 stands as **context**, not as a certified break in a specific predictor. The honest
statement is "platinum's industrial regime shifted around 2011–2013," full stop — no cell rides it.

## What survives (the tools, and one live fact)

- **The tools are keepers**, now correctly understood: `funnel_miner.py` (rank by coherence, seals
  TEST), `regime_vs_latency.py` (latency vs regime vs noise — with the de-bias caveat above),
  `build_supercycle_flag.py` (watch-only copper flag). Reusable across assets.
- **The flag is currently ARMED** (copper 12-mo +49.3%) — a real macro reading — but its gating power
  is **unproven** (in-sample separation +6/−0/+8/+0%, on ~16 episodes) and **contaminated** (+0.44 vs
  WTI). It is a curiosity to watch, not a gate to act on.

## What a real confirmation would require (and the expected outcome)

To claim any platinum cell, the test must be out-of-**search**, not just out-of-direction:

1. **Independent re-discovery.** Re-run discovery on a disjoint sub-window; require the *same* cell to
   re-emerge on its own. A cell that only appears when you search the whole space is search noise.
2. **Multiplicity-corrected selection** (a family-wise bar over the search), or
3. **Pure forward tape** — data the search never touched (2026-08-14 →).

Expected outcome, honestly: **abstain.** Given 381 cells "confirm" equally and the breaks are diffuse,
the base rate that any specific cell is real is low. The forward tape can be opened as **pure
observation** (costs nothing), but with **no promotion expectation** and **no shadow sizing**.

## Disposition

- **No ZION integration** — the shadow plan is withdrawn; `PLATINUM_INTEGRATION_20260814.md` is
  superseded by this file.
- **SYZYGY holds zero platinum** (unchanged; nothing was ever sized).
- **Optional, harmless:** open a forward observation log for the emission-legal `US_2Y/WTI T20` under
  flag-armed months — labelled observation-only, not a pre-registered promotion path, since its
  in-sample basis is now void.
- **Standing correction:** treat `regime_vs_latency`'s "CONFIRMED" as *direction-de-biased*, never
  *search-corrected*. Add an independent-re-discovery step before any future "confirmed" claim.

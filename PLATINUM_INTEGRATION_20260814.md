> ⚠️ **SUPERSEDED 2026-08-14 by `PLATINUM_ANALYSIS_20260814.md`.** A multiplicity stress test
> (`platinum_recheck.py`) refuted this doc's premise: 381 emission-legal cells "confirm" equally
> (100%/n13 — search noise), so the 4 cells below are NOT special. Verdict reverted to ABSTAIN.
> Kept as the as-issued record of the plan the stress test overturned; do not act on it.

# Platinum → ZION (monthly) — integration design + forward-DECISION pre-registration
### LOCKED 2026-08-14. Watch/shadow only. No live sleeve is authorized by this document.

## 0. Verdict up front (so nothing here reads as a green light)

Platinum enters ZION at the **SHADOW / MIMESIS** level — its calls are recorded as as-issued
tickets and resolved forward, **not** sized into the SYZYGY book. It does **not** become a
certified sleeve now, and it may never. Two hard reasons, both from the 2026-08-14 diagnostic
work (`~/Desktop/ASSET_PIPELINE/funnel_miner.py`, `regime_vs_latency.py`, `build_supercycle_flag.py`):

1. **3 of 4 confirmed cells are emission-illegal.** They predict from `Industrial_Production`
   (`CONTAM_HARD`: mid-month publish + heavy revision). ZION **EMISSION** excludes it — they can
   never fire on the 1st. Narrative/discovery only, permanently.
2. **The one emission-legal cell shows zero flag lift.** `US_2Y/WTI T20` is TIMELY-clean, but the
   super-cycle flag's in-sample separation on it is **+0%** (67% ON vs 67% OFF). The arming logic
   is unproven for the only cell that could go live.

So this is an honest **watch** integration: wire the shadow, start the forward tape, pre-register
the exact bar that would (or would not) promote it. The flag is currently **ARMED** (copper 12-mo
+49.3%), which is *why* we bother to watch — not a reason to trade.

## 1. The candidate cells and their emission status

Confirmed out-of-selection by the diagnostic (pre-edge holds on held-out pre-break data, then
collapses post-break — a real, drift-robust regime break):

| cell | k·w·type | break | out-of-sel pre-edge | post | EMISSION | flag sep |
|---|---|---|---|---|---|---|
| M2_Money / **Industrial_Production** | 4·60·6 | 2011-02 | 94% (LB .73) | 49% | ❌ CONTAM_HARD | +6% |
| M2_Money / **Industrial_Production** | 5·60·6 | 2013-05 | 83% (LB .61) | 42% | ❌ CONTAM_HARD | −0% |
| M2_Money / **Industrial_Production** | 7·60·6 | 2011-02 | 80% (LB .55) | 40% | ❌ CONTAM_HARD | +8% |
| **US_2Y_Treasury / WTI_Crude_Close** | 9·60·20 | 2012-09 | 93% (LB .69) | 44% | ✅ TIMELY | **+0%** |

Only the last row is emission-legal. The first three are kept **narrative-only** — real economic
history (auto-catalyst/diesel super-cycle, died ~2011–2013), never a live caller.

## 2. Phase-by-phase wiring (how platinum walks the ZION chain)

| Phase | What it does for platinum |
|---|---|
| **AUDIT** | full-history admission on Platinum_Futures_Close (1997+) + drivers. Standard. |
| **HYPERION** | panel assembly. Standard. |
| **RED DAWN** | **frozen tiers, NO re-discovery.** The 4 confirmed cells are loaded as fixed definitions (pair, k, w, type, direction, z-constants) — not re-mined. |
| **INTERSTELLAR** | liquidity throttle (never sizes). Unchanged. |
| **VALUATION / ODYSSEY / SANCTUARY** | secondary voices; no platinum-specific change. |
| **EMISSION** | **the gate that matters.** Drops the 3 IndProd cells (CONTAM_HARD). Passes `US_2Y/WTI T20` (carry-forward ≥.60, LB>gate, n≥8) — the only live-eligible caller. |
| **REGIME** (step 1s, COND) | **home of the 2011 break + the super-cycle flag.** Records the confirmed break; hosts the copper arming label (§3). Its verdict for the current regime: **within-regime = discard** (post-2011 cells are dead) — the flag is the *rescue* condition, watch-only. |
| **DECISION** | in the current regime the platinum cells **ABSTAIN** (post-break dead). When flag=ARMED **and** `US_2Y/WTI T20` fires, DECISION emits a **SHADOW** call (recorded, not live) + STANDDOWN monitor. |
| **MIRROR** | drift-guard + TRAIN-frozen USD hedge leg — applied only if/when promoted. |
| **GAUNTLET** | **withholds `platinum_certified_signal.json`** until the forward bar (§4) clears. No cert → no live sleeve. |
| **MIMESIS** | **the actual test surface.** Emits the shadow ticket as-issued each armed-and-fired month; resolves it forward. This is the only real OOS. |
| **SYZYGY** | holds **zero platinum** until GAUNTLET certifies. Book is unchanged by this document. |
| **RECAL** | n/a until promoted. |

## 3. The super-cycle flag as a REGIME arming label (never sizes)

Follows the INTERSTELLAR contract: a regime **label**, never a size.

- **Primary:** copper 12-month change > 0 (standard annual trend — **not swept**). Exogenous to the
  signal axis (M2/IndProd/rates), TIMELY (market price, never revised, fresh on the 1st).
- **Arming rule (pre-registered):** a dormant cell is ARMED in month `t` iff FLAG(`t`)=ON. Armed +
  fires → **WATCH candidate** (shadow ticket via MIMESIS). Never a trade, never a size.
- **Honest caveat:** in-sample flag separation on the confirmed cells is weak (+6/−0/+8/+0%) and the
  pre/post-2011 ON-fraction gap is soft (61% vs 50%). The flag *coincides* with the break; it is not
  proven to *gate* the edge. The forward record is the only test. (`supercycle_flag.csv`, WATCH-ONLY.)

## 4. FORWARD-DECISION PRE-REGISTRATION (locked)

**Premise correction (critical):** the sealed TEST block is **already peeked** for these cells — the
regime diagnostic read post-2011 (which includes the TEST era) to establish the break. So TEST is
**NOT** a clean confirmation surface here; it is descriptive-only. The **forward tape (2026-08-14 →)**
is the sole honest OOS. We are **not** re-testing the dead post-2011 edge (known dead). We are testing
one thing:

> **H1.** With the super-cycle flag ARMED, do `US_2Y/WTI T20`'s flag-armed, emission-legal calls, on
> the **forward as-issued tape**, beat ABSTENTION and beat platinum drift — by a margin, over enough
> resolved calls to matter?

- **Caller:** `US_2Y_Treasury/WTI_Crude_Close`, k9 w60 type20, D=+1 (frozen). Emission-legal.
- **Gate:** fire only when FLAG=ARMED (copper 12-mo > 0). Otherwise ABSTAIN. Default is abstain.
- **Surfaces:** forward MIMESIS tape (confirmatory). Sealed-TEST replay is reported **descriptive-only,
  non-confirmatory** (peeked). Pre-2011 numbers are historical context, never evidence of forward skill.
- **Promotion bar (ZION standing rule):** GAUNTLET certifies platinum to a live sleeve **iff** the
  forward tape shows **Wilson-LB > 0.50 over ≥ 12 resolved, non-overlapping armed calls**, AND the
  call beats drift (long-only platinum) on the same months, AND STANDDOWN has not tripped.
- **Objective:** Sortino-LB (shared module), accuracy secondary. Consistent with Sortino-first.
- **Go / No-Go:** clears the bar → GAUNTLET certifies, SYZYGY sizes at base sleeve weight under the
  2.0× gross cap. Fails, or STANDDOWN trips → stays SHADOW; **null is final**, no re-spec at a lower bar.
- **Time to verdict:** armed-and-fired months are sparse; expect **years**, not months. That is honest,
  not a defect — the flag just re-armed; the tape starts now.

## 5. Trap ledger

| # | trap | control |
|---|---|---|
| 1 | Trading a dead edge | post-2011 cells ABSTAIN; only forward-armed calls shadow-recorded |
| 2 | Emission look-ahead | IndProd cells HARD-excluded; only TIMELY US_2Y/WTI can emit |
| 3 | TEST re-use after peeking | TEST is descriptive-only; forward tape is the sole confirmation |
| 4 | Flag = signal in disguise | copper is exogenous to the signal axis (note: copper~WTI mild for the WTI cell) |
| 5 | Flag DOF | trend = 12-mo change > 0, pre-registered, not swept |
| 6 | Drift-capture | promotion requires beating long-only drift, not just >50% |
| 7 | Silent promotion | GAUNTLET withholds cert until the forward bar clears; SYZYGY holds 0 until then |

## 6. Next executable step

Stand up the shadow: freeze the 4 cell definitions into `platinum_cells_frozen.json`, wire the copper
FLAG into ZION_REGIME as the arming label, and open a MIMESIS shadow tape for `US_2Y/WTI T20`
gated on FLAG=ARMED. First armed ticket emits at the next 1st-of-month while copper 12-mo stays > 0.
No SYZYGY change. Re-read the promotion bar only when ≥12 resolved armed calls exist.

# ZION WEEKLY — COMBINED BOOK SPEC (LOCKED 2026-08-16)
**Status: LOCKED, operator-authorized. Built by the unified driver (§7-audited); replicated on a
fresh model pass (Fable, 2026-08-16) before lock. Distinct from the weekly-oos-dev persistence book
(Sortino 1.24) — do not pool or compare their records.**

---

## 1. Configuration (frozen)

| component | rule |
|---|---|
| **SPY sleeve** | unified pipeline: swept H=2wk · val-winner VIX/Dollar cascade · 3-lens (RD/ODY/SANC) ≥2-unanimous convergence · decision = trailing eff-n Wilson-LB > **0.50**, n≥12 (**drift gate REMOVED — operator 2026-08-16**) |
| **QQQ sleeve** | same pipeline on QQQ (fresh weeks; H=2wk) |
| **Gold sleeve** | **DROPPED** — gated-acc 50.8% (coin), Sortino −0.20; gold survives only via the micro-sleeve + watch-cell below |
| **Risk weights** | Sortino-weighted SPY/QQQ on the 80% risk block: OOS Sortino 0.86/1.41 → **SPY ≈30% / QQQ ≈50%** of book |
| **Hedge** | **20% 2Y Treasury** (DGS2 carry − 1.9·Δy), **always-on, never throttled**. Duration sweep was monotone 2Y>5Y>10Y>30Y; hedge weight 20% = peak Sortino. Sortino-first ruling: keep the hedge and lever — never cut the hedge for CAGR |
| **Dual throttle** | risk sleeves ×0.5 when VIX trailing-pctl ≥0.70; ×0.5 again when Credit_BAA10Y trailing-pctl ≥0.70 (multiplicative, PIT, exogenous only — own-error/book-MIRROR throttle is REJECTED, it cost Sortino 1.10→1.00) |
| **Leverage** | **1.232×** — levers the 20%-hedge book to the operator's 10% MaxDD cap (historical-worst calibrated) |
| **Silver micro overlay** | **w=0.05**, VIX/IP_Nowcast N8 H4 episodic (SILVER_MICRO_SLEEVE_20260816.md): hold 4wks, extend on re-fire, else flat; ~8% active; corr to this book **−0.01** |

## 2. Locked numbers (weekly full-calendar, 2007–2026, 5bps costs)

| book | coverage | Sortino | Calmar | CAGR | MaxDD |
|---|---|---|---|---|---|
| unlevered, no micro | 100% | 2.36 | 1.04 | 8.45% | −8.1% |
| **FINAL: 1.232× + 5% silver micro** | **100%** | **2.42** | **1.08** | **10.73%** | **−9.9%** |

Financing at 1.23× unmodeled ≈ −1.1%/yr → honest forward ≈ **9.6%**. Silver micro contributes
+0.29pp CAGR and **+0.06 Sortino** here (a true diversifier in this book: it fires long-metal in the
exact VIX windows where the throttle has de-risked the sleeves — counter-phased by construction;
peak gross in those windows ≈0.8×, so the all-fire case is self-limiting under the cap).

## 3. The three lock-time additions (Fable pass, 2026-08-16)

1. **Decade concentration (named risk).** 2007–16: **+0.31% CAGR / Sortino 1.92** (gate burn-in +
   throttle-heavy). 2017–26: **+17.09% / 3.27**. The armed system has ~one decade of evidence and it
   was a strong equity decade. Forward expectation in a flat regime: materially below 10%. **Trust
   the structure (DD control, Sortino profile), not the CAGR level.**
2. **Gold VIX/IP_Nowcast = WATCH-ONLY, no weight.** n=106, acc 57.5%, LB 0.48 (inadmissible signal)
   yet +0.055 book Sortino at a hypothetical 5% — the lift is **exposure timing** (long-metal while
   throttled), not direction. Report-only; admissible only if a future forward record earns G1.
3. **All-long family caveat.** Every fire in the entire micro family (silver 54, gold 106, platinum
   47) is LONG — it is a fear-bid long-metal mechanism. A first SHORT emission anywhere in the
   family is out-of-character → **review, don't follow.**

## 4. Honesty box

- **This book is structure, not alpha.** SPY/QQQ convergence ≈ their drift (+1.0/+0.7pp). All gains
  over buy-and-hold come from: decorrelation, exogenous-stress throttling, the 2Y hedge, sizing,
  and the one admitted micro cell. The edge is second-moment (loss-limiting), not first-moment.
- −9.9% MaxDD is calibrated to the historical worst; a worse-than-2008/2022 concurrent draw breaches
  the cap. Equity legs are price-only (no dividends). 2Y hedge is a TR proxy.
- **Forward tape is the binding gate** for the silver micro (12-Friday window, per its own doc) and
  for any future addition.

## 5. Admission rule for ANY future addition (validated 2026-08-16)

Frozen template (N=8, H=4, episodic, no sweeping) + four gates, all mandatory:
**G1** signal: acc ≥65%, n ≥30, Wilson-LB ≥0.55 · **G2** concentration: ≥3 calendar years, max-year
≤45% · **G3** decorrelation: |corr to book| <0.30 on active weeks · **G4** book: +5% overlay must not
reduce book Sortino. Then PROVISIONAL until the forward tape confirms.
Validated on a pre-declared 11-cell grid (`micro_screen.py`): **1 survivor = the silver control;
10/11 fail.** The pipeline discriminates — silver is unique, not the first of an easy family.

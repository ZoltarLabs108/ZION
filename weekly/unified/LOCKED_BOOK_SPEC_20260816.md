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

---

## AMENDMENT 1 (2026-08-16, operator) — 7.5% always-on GOLD structural overlay

Gold re-enters **not as a signal sleeve** (that stays dead: 50.8% acc, Sortino −0.20) but as the
**Permanent-Portfolio inflation leg** — always-on ballast, no prediction claim, judged only on
G3/G4-style criteria. Disclosed 6-cell grid (2.5/5/10% × always/stress): always-on monotone-helps
(2.49/2.53/2.57), **stress-only adds nothing** (the throttle+micro already own those windows) — the
simple version wins, the clever version fails. Operator weight **w=0.075** (inside the grid).

| book (weekly basis) | Sortino | CAGR | MaxDD |
|---|---|---|---|
| locked + micro (pre-amendment) | 2.43 | 10.79% @1.232× | −9.9% |
| **AMENDED: + 7.5% gold, @1.220×** | **2.56** | **11.80%** | **−9.9%** |

Gross accounting: overlays are additive → 1.125 unlevered gross, ~1.37× effective at the cap;
financing (~−1.2%/yr) unmodeled → honest forward ≈ **10.6%**. Gold corr to book +0.10, to silver
micro −0.04 (near-orthogonal to both). Full run: `universe_book.py` / `gold_overlay_run.log`.

---

## AMENDMENT 2 (2026-08-17, operator) — PERSISTENCE + STRESS-EXIT on the risk sleeves

**Rule:** each risk-sleeve position PERSISTS from its gated decision until the NEXT gated decision
(abstain = hold, no H-block expiry) — and FLATTENS while the dual throttle is stressed (thr < 1.0):
the exit is the *world's* stress state, never the book's own P&L. Transferred from the live-ticket
forensic + the sister lineage's abstain-as-hold finding; passed the pre-declared gates:

| variant | Sortino@cap | CAGR@cap | h1 ΔS | h2 ΔS | verdict |
|---|---|---|---|---|---|
| baseline (blocks, this harness) | 2.37 | 11.20% | — | — | reference |
| B1 pure persistence (no exit) | 1.89 | 6.45% | +0.00 | −0.67 | **REJECT** — rides drift into every crash |
| **B2 persistence + stress-exit** | **2.82** | **12.91%** | +0.00 | **+0.66** | **[G1 G2 G3] ADOPTED** |

Leverage re-solved: **1.190×** to the 10% DD cap (unlev DD −8.4%). The B1/B2 split is the lesson:
persistence supplies the drift-carry, the exogenous stress-exit supplies the crash-sidestep — each
alone fails, together they clear every gate. (Harness note: this baseline carries sleeve costs and
reads 2.37 vs Amendment 1's 2.56 construction; the +0.45 delta is the claim, measured like-for-like.)

**Universe book under Amendment 2:** weekly leg (monthly agg) CAGR 12.93% / Sortino 3.75 →
**UNIVERSE 50/50: CAGR 9.60%, Sortino 4.71, MaxDD −4.0%, 95% years positive** (was 9.05 / 4.13 / −3.9).

**Same-day companion verdicts (pre-declared, all REJECT):** long-Ag/short-Au spread always-on
(2.31/2.24 — the ratio bleeds) and micro-window (2.38/2.39, fails the +0.05 bar); dynamic sizing V1–V3
(sized_variant_test). The spread's live-book work is real but window-specific; not transferable as a
standing component. PROVISIONAL: Amendment 2 governs tape emissions from the next issue; prior tape
rows stand as-issued under Amendment-1 rules (never rewritten).

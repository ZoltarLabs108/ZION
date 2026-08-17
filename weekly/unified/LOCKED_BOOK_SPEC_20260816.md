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

---

## AMENDMENT 3 (2026-08-17, operator) — RECOVERY-WINDOW LEVERAGE SCHEDULE

**Rule:** the weekly book's leverage is a WORLD-STATE SCHEDULE, completing the throttle's symmetry:
sleeves flat in stress (Amendment 2) · **base 1.190× in calm** · **2.0× (the house gross cap) for the
4 weeks after a recovery event** — a recovery event = the dual throttle's first calm week after ≥2
consecutive stressed weeks. No own-P&L input anywhere; the trigger is the same exogenous machinery
as the throttle. Motivated a priori by the mirror-phase screen's co-phasing finding (the book's own
forward-4wk return after recovery events: +2.32% mean, 74% positive, n=23 — ~3× unconditional).

| gate check | flat 1.19× | **scheduled** | Δ |
|---|---|---|---|
| FULL Sortino@cap | 2.82 | **3.17** | **+0.34** ✓ G1 |
| FULL CAGR / MaxDD | 12.91% / −10.0% | **15.33% / −10.0%** | DD unchanged ✓ G2 |
| h1 (2007–16) ΔSortino | — | +0.02 | ≥0 ✓ G3 |
| h2 (2017–26) ΔSortino | — | +0.49 | ≥0 ✓ G3 |

**Trigger is NOT decade-concentrated:** 12 events in h1, 11 in h2 (~1.2/yr, windows ≈9–10% of weeks
in both halves) — unlike the book's returns, the rule's opportunities are evenly spread.

**Universe under Amendment 3: CAGR 10.82%, Sortino 5.20, MaxDD −4.0%, 95% years positive**
(was 9.60 / 4.71 / −4.0). Caveats: n=23 events; the mean is tail-carried (median window +0.49% —
the rule earns on the big rebounds, which is the point); financing at 2.0× unmodeled (~−1%/yr on
window weeks ≈ −0.1%/yr book-level); PROVISIONAL on the forward tape like everything else. The tape
emission now carries a `lev` field; the first live recovery event will be flagged by the Friday job.

---

## AMENDMENT 4 (2026-08-17, operator) — UNIVERSE LEVERAGE 2.54× · UNIVERSE GROSS CAP 3.5×

**Ruling:** the universe book is levered **2.54×** — the multiple that spends the operator's 10%
MaxDD budget exactly — and the **2.0× house gross cap is superseded FOR THE UNIVERSE BOOK by a
universe-specific cap of 3.5×** (the 2.0× convention was written for the live 5-asset book; at
2.54× the universe's netted gross peaks at 3.49×, mean 1.21× — the peaks are brief and occur
precisely in the Amendment-3 recovery windows, the highest-expectancy weeks; clipping them was
rejected as incoherent).

| universe book | CAGR | Sortino | MaxDD | worst yr | 2008 | 2022 |
|---|---|---|---|---|---|---|
| 1× (structural) | 10.82% | 5.20 | −4.0% | −2.3% | + | + |
| **2.54× (FINAL)** | **28.66%** | **5.20** | **−10.0%** | −5.8% | **+8.5%** | **+22.3%** |

**Honest ≈ 27% after financing** (~−1 to −1.5%/yr; mean borrow modest, recovery bursts heavy).
Tape semantics unchanged: rows record **1× structural exposures** (as-issued continuity); capital
P&L = 2.54 × tape return. Caveats, amplified with the leverage: the −10% is calibrated to the
HISTORICAL worst (a beyond-history event scales by 2.54); decade concentration scales too (the
burn-in decade levered still earned ~nothing); **12 resolved tape weeks before any real capital
runs at this multiple — leverage last of all.**

**Same-day companion verdicts (pre-declared, all REJECT):** long-Ag/short-Au spread always-on
(2.31/2.24 — the ratio bleeds) and micro-window (2.38/2.39, fails the +0.05 bar); dynamic sizing V1–V3
(sized_variant_test). The spread's live-book work is real but window-specific; not transferable as a
standing component. PROVISIONAL: Amendment 2 governs tape emissions from the next issue; prior tape
rows stand as-issued under Amendment-1 rules (never rewritten).

---

## AMENDMENT 5 (2026-08-17, operator) — RE-LOCK UNIVERSE LEVERAGE 4.0× · DD BUDGET 10% → 16%

**Ruling:** the operator raises the universe MaxDD budget from **10% to 16%** and re-locks the
universe leverage to **4.0×** (the multiple that spends the 16% budget), **superseding Amendment 4's
2.54×**. Numbers are the already-computed 4.0× series (`universe_monthly_backtest.csv`, col `uni_400`;
the "examined, declined" row of `UNIVERSE_BACKTEST_20260817.md`), not an extrapolation.

| universe book | final mult | CAGR | Sortino | Calmar | MaxDD | worst yr | 2008 | 2022 |
|---|---|---|---|---|---|---|---|---|
| 2.54× (was FINAL, Amdt 4) | 123.3× | 28.70% | 5.20 | 2.87 | −10.0% | −5.8% | +8.5% | +22.3% |
| **4.0× (RE-LOCKED FINAL)** | **1,560×** | **47.00%** | **5.20** | **2.99** | **−15.7%** | −9.1% | **+12.9%** | **+36.2%** |

**Honest ≈ 42.5% after financing** (~−4.5pp/yr at 4×; recovery bursts heavy). Sortino is
leverage-invariant (5.20 unchanged) — this buys return by spending drawdown budget, not by adding
risk-adjusted quality. Tape semantics unchanged: rows record **1× structural exposures**; capital
P&L = 4.0 × tape return.

**The binding gate is NOT waived.** The Amendment-4 rule still stands verbatim: **"12 resolved tape
weeks before any real capital runs at this multiple — leverage last of all."** Forward tape is at
**1 / 12 resolved** (clears ~mid-November 2026).

**Go-live 2026-08-17 = FORWARD RUN LIVE IN TRACKING MODE ONLY** (`com.zoltar.zion.universe`, Fri
17:30). Real capital deploys at **12/12**, not before. Risk note amplified with the leverage: the
−16% is calibrated to the HISTORICAL worst — a beyond-history concurrent draw scales by 4.0×
(→ ~−25%+ off-model); decade concentration scales too. This amendment records the target spec and
the tracking go-live; it authorizes **no capital** ahead of the gate.


---

## AMENDMENT 5 + AMENDMENT 4 REVISION (2026-08-17, operator) — DOLLAR SLEEVE IN-BOOK · 3.80× · 15.7% DD BUDGET

**Ruling:** the tracked ZION configuration becomes the characterized aggressive tier:
**+19.3% structural UUP (dollar sleeve, always-on) · leverage 3.80× · DD budget 15.7% · universe
gross cap 6.0×** (levered structural gross peaks ≈5.98×).

| tracked config | CAGR | Sortino | MaxDD |
|---|---|---|---|
| prior (2.54×, no sleeve) | 28.4% | 5.11 | −10.0% |
| **CURRENT: 3.80× + dollar sleeve** | **45.6%** (honest ≈41% after financing) | **5.89** | **−15.7%** |

**Recorded flags (integrity):** this supersedes two same-day rulings — the 2.54×/10%-DD "wait for
the tape" and the sleeve's paper-track admission path. The sleeve is adopted AHEAD of forward
evidence, on operator authority, with its in-sample discovery (found on the book's own down months,
weight tuned on the same history) explicitly on the record. The tape remains the arbiter: 1×
structural rows, capital P&L = 3.80 × tape return, USD bucket resolved via UUP. Governs from the
next issue (wk ending 2026-08-21); prior rows stand as-issued. REAL capital still waits for the
12-week November review per the standing gate; this amendment changes what is TRACKED, not what is
traded.


---

## AMENDMENT 6 (2026-08-17, operator) — INDIA COMPOSITE IN-BOOK at 2.5%

**Ruling:** the NIFTY-USD composite (Nifty50 / USDINR; tradeable INDA/EPI) enters the tracked book
at **2.5% universe-structural** — the only weight that passed the both-up gauntlet (CAGR 45.57 →
**46.62%**, Sortino 5.89 → **5.96**, halves +/+, leverage re-solve allows 3.82×; UNIVERSE_LEV held
at 3.80× for headroom). Corr to book **+0.05** — the most orthogonal component ever admitted.
**Flags:** promoted from paper the same day it was declared paper (second same-day supersession
after UUP); the 2.5% optimum sits at the grid edge and 5% FAILS (2008 USD-tail) — the weight is a
hard ceiling, never to be raised without a fresh gauntlet. Governs from the next issue; capital
P&L = 3.80 × tape return; REAL trading remains operator-executed and November-gated.


---

## CUTOVER (2026-08-17, operator) — ZION IS THE LIVE-EXECUTED BOOK

**Ruling:** effective immediately, the operator executes the ZION desk ticket (manual, Schwab) and
the AEGIS ticket becomes the SHADOW side of the weekly comparison. **Executed leverage = 2.5×
(staged)** while the tracked model tape remains 3.80× — the gap is deliberate: the model record
runs at full spec, real capital runs reduced until the November 12-week review, which now decides
the SCALE-UP (2.5× → 3.80×) rather than the go-live. Supersession #3 of the original staging
(go-live was planned mid-November) — on the record. Operational law: the Friday job prints the
ticket (step 5/5, ZION_LEV=2.5 in the runner); operator places orders; a fills-vs-ticket log is
the true live record; AEGIS files remain untouched (quarantine holds — shadow by default, not by
modification). Switch-back = execute the AEGIS ticket again; nothing else changes.


---

## LEVERAGE LADDER (2026-08-17, operator) — 2.5× → 4.0× within ~90 days, evidence-gated

**Target: executed leverage 4.0× by ~2026-11-15.** The path is a ladder with gates, not dates alone:

| step | when | executed lev | gate to advance |
|---|---|---|---|
| 1 (now) | 2026-08-17 | **2.5×** | — |
| 2 | ~week 6 (early Oct) | **3.2×** | 6 resolved tape weeks clean: fills track ticket, resolutions match market, caps unbreached, DD within pro-rata budget |
| 3 | ~week 12 (mid-Nov = the review) | **4.0×** | 12-week review clean; same criteria |

"Clean" = operational fidelity, not performance: the ladder advances on the machine keeping its
word, never on a hot streak (and it PAUSES, not reverses, on a cold one unless a gate criterion
fails). At 4.0× with the full book: backtest MaxDD ≈ **−16.5%** (slightly past the 15.7% budget —
accepted by this ruling) and peak levered gross ≈6.3× → **universe cap moves 6.0× → 6.5× at step 3**.
Model tape moves 3.80× → 4.0× at step 3 so model and execution converge. Financing at 4.0× ≈
−4.5pp/yr (honest CAGR ~42%). Operator advances each step by changing ZION_LEV in run_universe.sh.

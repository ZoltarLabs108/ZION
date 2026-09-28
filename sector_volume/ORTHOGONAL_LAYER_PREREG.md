# PRE-REGISTRATION — the orthogonal sector layer

**Written 2026-09-28, BEFORE any conditional-return test is run. Nothing in this file was chosen by looking at what would have worked.**
The purpose is to commit the weakness definition, the sector map, the eligibility gate, the benchmark, and the decision rule in advance,
so the eventual test cannot be a story fitted to September or to the 62-month history. If the pre-registered design does not beat the
benchmark out of sample, it is dropped — no post-hoc redefinition, no sector added to the map to rescue it, no threshold tuned to the outcome.

---

## 0. The claim being tested (one sentence)
Deploying **specific sectors at specific times, to fill a weakness ZION cannot cover itself**, beats running the sector block always-on —
and does so because the sectors are orthogonal to ZION exactly in the regime ZION is blind to.

## 1. ZION's weakness — defined objectively, in advance
Established earlier this session (documented, not fitted): ZION's stress gauge is VIX × credit, and it is **structurally blind to a
rate-and-commodity-and-rotation regime**. This session's live proof: VIX 15.9 while MOVE +26.6 to 96, OVX +11.9 to 55, oil to $105,
2Y +70 bp, cross-sector dispersion at the 85th percentile — a real stress event the throttle read as calm (thr = 1.0, sleeves fully on).

The weakness state is therefore, per month t, defined by pre-committed gauges at the **same 0.70 expanding-percentile rule the existing
throttle already uses** (no new free parameter):

- **W1 — rate/commodity shock the throttle misses:** ( MOVE pctl ≥ 0.70 OR OVX pctl ≥ 0.70 OR 2Y 3-month change ≥ +0.50 pp ) **AND**
  VIX pctl < 0.70. The `AND VIX calm` clause is the definition of "blind spot": stress present in bonds/oil while the equity gauge is asleep.
- **W2 — rotation/dispersion the throttle misses:** cross-sector return dispersion pctl ≥ 0.70 **AND** VIX pctl < 0.70.

When neither W1 nor W2 holds, there is no ZION weakness for the sectors to fill, and the orthogonal layer contributes nothing that month.
(When VIX itself is stressed, the existing throttle already handles it; the orthogonal layer is not for that case.)

## 2. The sector map — by MECHANISM, committed in advance
Each mapping is an economic exposure statement, not a backtest ranking. Locked here before returns:

| ZION weakness | sectors eligible to fill it | mechanism (why this is orthogonal to ZION's book) |
|---|---|---|
| W1 rate/commodity shock | **Energy long** (XLE); **Technology SHORT** via the overlay (XLK) | Energy is long the oil/rate factor that is hurting ZION's equity beta; short long-duration growth offsets the book's growth tilt. |
| W1 or W2 with equity-drawdown risk | **Health Care long** (XLV), **Consumer Staples long** (XLP) | Defensives are the drawdown hedge ZION's 2Y leg only partially provides; low beta into a rotation the book cannot rotate with. |
| W2 rotation only (no rate shock) | **the sector with the straight, admitted call whose corr to the book is lowest** | rotation is idiosyncratic; fill it with the most orthogonal available sector, not a fixed name. |

Sectors NOT in the map for a given weakness are not deployed for it, however good their standalone call looks. Financials, Industrials,
Consumer Discretionary are deliberately excluded from W1 (they are pro-cyclical / rate-ambiguous — Financials fell while yields rose in Sept,
so the "banks like higher rates" reflex is not reliable and is not committed).

## 3. Eligibility gate — which sector calls may fill a weakness
A sector call is eligible to fill a weakness only if ALL hold at month t:
1. **Straight** (call-stability diagnostic, 28 Sep): not flip-once, not flip-twice. Whipsaws are coin flips (flip-twice LB95 23.7%) and are ineligible.
2. **Admitted source:** the call comes from a type-pull or the second-instrument tier (R8), never a cascade emission.
3. **Correlation:** the sector's stream |corr| with the ZION universe < 0.30 over the trailing window (the existing R5 gate, measured trailing).

## 4. Benchmark — what the layer must beat
The **always-on 15% sector block** (equal-gross, R8 integration, the current shadow construction). The orthogonal layer is the same six
instruments, but each contributes ONLY in months where (a) a ZION weakness (W1/W2) is present, (b) the sector is in the map for that weakness,
and (c) it passes the eligibility gate. Otherwise it is flat that month.

## 5. Decision rule — pre-committed, pass/fail
On the ZION universe (sequential base, §15), 2007-08 → present where data allows, the orthogonal layer **passes** iff BOTH:
- **P1:** universe Sortino with the orthogonal layer > universe Sortino with the always-on block, on the sequential base, by ≥ +0.10; AND
- **P2:** it does not cost more than 25% of the always-on block's CAGR contribution (it may earn less, but must not gut return to buy the Sortino).
Plus a discipline check, **P3:** the layer must also beat always-on on a **placebo weakness** (weakness flags shuffled in time) by a margin
larger than the shuffled version achieves — i.e., the edge must come from the weakness *timing*, not from merely trading less. If P3 fails,
the "orthogonal" story is really just "trade fewer months," and we say so.

If P1–P3 pass on the sequential record, the layer graduates to **shadow forward-tracking**, gated to the same 12 resolved tape months as
everything else before any real capital. If they do not pass, the orthogonal layer is **rejected** and we keep the always-on block (or nothing).

## 6. What is explicitly forbidden (the anti-overfitting commitments)
- No redefining W1/W2 after seeing returns. The gauges and the 0.70 threshold are locked above.
- No adding a sector to the map, or moving one between weaknesses, to improve the result.
- No tuning the +0.10 / 25% / placebo margins after the fact.
- No dropping the placebo check (P3) if it is the one that fails.
- The whole layer is 0% real capital until 12 resolved tape months, identical to the block's own gate.

## 7. Order of operations (per operator, 28 Sep)
1. This pre-registration (done, this file).
2. Monthly-sleeve cascade-quality test — does the reorder principle generalize past the sectors? (separate, does not touch this design.)
3. Only then: build the layer to this spec, test P1–P3 against always-on, report the verdict.

Signed into the record before returns: this file's git/mtime timestamp is the pre-registration date.

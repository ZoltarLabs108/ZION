"""
forward_sortino.py — reconcile the ZION universe Sortino against the as-issued forward tape.

WHY: the leverage rule L_max = 0.9 x Sortino needs a Sortino it can trust. The BACKTEST number
is NOT robust — it ranges ~2.8 (independent reconstruction, current +UUP/India book) to ~4.1
(pipeline locked-book calc) to 5.2-5.96 (model configs), a 2x spread from reconstruction /
config / weekly:monthly blend-leverage differences. So the forward tape is the arbiter — but a
Sortino needs a sample; this tracker reports it only once >=12 resolved weeks exist (house rule),
and until then holds the CONSERVATIVE backtest end.

Each run: read the weekly forward tape's resolved returns since go-live, compute the running
forward Sortino when mature, and print what leverage 0.9 x {conservative backtest | forward}
permits, floored by the 20% DD backstop. READ-ONLY; writes only reports/forward_sortino_log.csv.
"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
TAPE = os.path.join(REP, 'universe_forward_tape.csv')
LOG = os.path.join(REP, 'forward_sortino_log.csv')
K_RULE = 0.90                 # leverage multiplier (operator 2026-08-18)
DD_BACKSTOP = 0.20            # hard DD backstop (operator 2026-08-18)
MIN_WK = 12                   # house rule: no Sortino verdict before 12 resolved weeks
BT_CHARTED = 5.20            # authoritative charted backtest (universe_monthly_backtest.csv, lev-invariant, -15.7% DD @4x)
BT_CONSERVATIVE = 3.9        # 25% haircut of the charted 5.20 (house doctrine: backtest inflates OOS)
BT_OPTIMISTIC = BT_CHARTED  # (my earlier 2.79 reconstruction was a data-proxy ARTIFACT — understated; discarded)


def sortino_ann(r):
    r = np.asarray(r, float)
    if len(r) < 2: return np.nan
    dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
    return float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else np.nan


def main():
    if not os.path.exists(TAPE):
        print('no forward tape yet.'); return
    t = pd.read_csv(TAPE)
    res = t[t['status'] == 'RESOLVED'].copy()
    rr = pd.to_numeric(res.get('realized_ret'), errors='coerce').dropna().to_numpy()
    n = len(rr)
    print("FORWARD SORTINO RECONCILIATION (weekly universe leg)")
    print(f"  backtest is NON-ROBUST: conservative {BT_CONSERVATIVE} .. pipeline ~4.1 .. optimistic {BT_OPTIMISTIC}")
    print(f"  resolved forward weeks: {n}/{MIN_WK} needed for a Sortino")
    if n >= MIN_WK:
        fs = sortino_ann(rr)
        permit_rule = K_RULE * fs
        print(f"  FORWARD Sortino (annualized, {n} wks): {fs:.2f}")
        print(f"  0.9 x forward Sortino permits: {permit_rule:.2f}x  (then floor by 20% DD backstop)")
        basis = f"forward({fs:.2f})"; permit = permit_rule
    else:
        cum = (np.prod(1 + rr) - 1) * 100 if n else 0.0
        print(f"  forward Sortino NOT YET MEANINGFUL ({n} pts). Running cum return {cum:+.2f}%.")
        permit = K_RULE * BT_CONSERVATIVE
        print(f"  HOLD conservative: 0.9 x {BT_CONSERVATIVE} = {permit:.2f}x until forward matures.")
        print(f"  (optimistic backtest would allow 0.9 x {BT_OPTIMISTIC} = {K_RULE*BT_OPTIMISTIC:.2f}x — NOT yet earned.)")
        basis = f"conservative-backtest({BT_CONSERVATIVE})"
    print(f"  => leverage the rule supports NOW: ~{permit:.1f}x  (live ladder is 2.5x; 4x needs forward >= {4.0/K_RULE:.2f} Sortino)")
    row = pd.DataFrame([{'resolved_wks': n, 'basis': basis, 'permitted_lev': round(permit, 2),
                         'need_sortino_for_4x': round(4.0 / K_RULE, 2)}])
    hdr = not os.path.exists(LOG)
    row.to_csv(LOG, mode='a', header=hdr, index=False)


if __name__ == '__main__':
    main()

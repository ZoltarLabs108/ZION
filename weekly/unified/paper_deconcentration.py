"""
paper_deconcentration.py — FORWARD SHADOW (pre-registered CANDIDATE C2, NOT LIVE).

Compares, week by week on the as-issued tape, the ACTUAL book return vs what it WOULD have
returned had the equity block (US_EQ + NASDAQ) been split by INVERSE 26-week volatility instead
of by Sortino. This is the defensible kernel of the correlation-hedge idea: it only rebalances
SPY vs QQQ by RISK (a stable, descriptive statistic — no forecast, no return target, no optimizer,
no corner solutions), leaving the total equity weight and every structural hedge untouched.

Rationale: SPY/QQQ are ~0.94 correlated (one bet), yet Sortino-weighting silently lets the
higher-vol leg (QQQ) carry ~67% of book risk. Inverse-vol splitting balances the two.
Backfill backtest: book Sortino 1.598 -> 1.639 (+0.041), MaxDD −10.4% -> −10.2%.

Each run: for every RESOLVED forward-tape week, recompute the equity contribution both ways and
accrue the difference; report cumulative and forward Sortino once >=12 forward weeks resolve.
READ-ONLY; writes only reports/paper_deconcentration_log.csv. Append-only in spirit (recomputed
from immutable tape + market closes each run). Changes NO live weight.
"""
import os
import numpy as np, pandas as pd
import yfinance as yf
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
TAPE = os.path.join(REP, 'universe_forward_tape.csv')
LOG = os.path.join(REP, 'paper_deconcentration_log.csv')
FWD_START = pd.Timestamp('2026-08-14')
VOL_WIN = 26

_px = {}
def wkser(tk):
    if tk not in _px:
        h = yf.Ticker(tk).history(period='max', interval='1wk')['Close'].dropna()
        h.index = h.index.tz_localize(None)
        _px[tk] = h
    return _px[tk]


def trade_ret(tk, w0, w1):
    s = wkser(tk); a = s[s.index <= w0]; b = s[s.index <= w1]
    if not len(a) or not len(b) or b.index[-1] <= a.index[-1]: return np.nan
    return float(b.iloc[-1] / a.iloc[-1] - 1.0)


def trail_vol(tk, w0):
    s = wkser(tk); s = s[s.index <= w0]
    if len(s) < VOL_WIN + 1: return np.nan
    return float(s.pct_change().dropna().tail(VOL_WIN).std())


def main():
    if not os.path.exists(TAPE):
        print('no forward tape yet.'); return
    t = pd.read_csv(TAPE); t['week_ending'] = pd.to_datetime(t['week_ending'])
    res = t[t['status'] == 'RESOLVED'].copy()
    rows = []
    for _, r in res.iterrows():
        w0 = r['week_ending']; w1 = w0 + pd.Timedelta(days=7)
        eS, eQ = float(r.get('US_EQ', 0) or 0), float(r.get('NASDAQ', 0) or 0)
        rr = float(r.get('realized_ret'))
        eq = eS + eQ
        rS, rQ = trade_ret('^GSPC', w0, w1), trade_ret('QQQ', w0, w1)
        vS, vQ = trail_vol('^GSPC', w0), trail_vol('QQQ', w0)
        if any(np.isnan(x) for x in (rr, rS, rQ, vS, vQ)) or abs(eq) < 1e-12:
            continue
        iv_s = (1 / vS) / ((1 / vS) + (1 / vQ)); iv_q = 1 - iv_s
        actual_eq = eS * rS + eQ * rQ
        deconc_eq = eq * (iv_s * rS + iv_q * rQ)
        delta = deconc_eq - actual_eq
        rows.append({'week': str(w0.date()), 'forward': int(w0 >= FWD_START),
                     'book_actual': round(rr, 6), 'book_deconc': round(rr + delta, 6),
                     'delta_bps': round(delta * 1e4, 2),
                     'split_cur': f"{eS/eq:.2f}/{eQ/eq:.2f}" if eq else '-',
                     'split_ivol': f"{iv_s:.2f}/{iv_q:.2f}"})
    df = pd.DataFrame(rows)
    if len(df): df.to_csv(LOG, index=False)
    print("PAPER DE-CONCENTRATION (Candidate C2) — actual book vs inverse-vol equity split")
    print("  backfill backtest: Sortino 1.598 -> 1.639 (+0.041), MaxDD -10.4% -> -10.2%")
    if not len(df):
        print("  no jointly-resolved weeks yet — opens as the tape matures."); return
    fwd = df[df['forward'] == 1]
    print(f"{'week':>12} {'actual':>9} {'deconc':>9} {'Δbps':>7}  split cur->ivol")
    for _, r in df.iterrows():
        print(f"{r['week']:>12} {r['book_actual']*100:>+8.2f}% {r['book_deconc']*100:>+8.2f}% "
              f"{r['delta_bps']:>+7.1f}  {r['split_cur']}->{r['split_ivol']}")
    def sortino(x): x = np.asarray(x, float); dn = np.sqrt(np.mean(np.minimum(x, 0)**2)); return np.mean(x)/dn*np.sqrt(52) if dn > 0 else np.nan
    n = len(fwd)
    if n >= 12:
        sa, sd = sortino(fwd['book_actual']), sortino(fwd['book_deconc'])
        print(f"\nFORWARD ({n} wks): actual Sortino {sa:.2f} vs de-conc {sd:.2f}  (Δ {sd-sa:+.2f})")
    print(f"forward evidence window: {n}/12 — no adoption verdict before 12 (pre-registered). NOT LIVE.")


if __name__ == '__main__':
    main()

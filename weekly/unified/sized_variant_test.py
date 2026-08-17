"""
sized_variant_test.py — PRE-DECLARED test: dynamic (conviction/payoff) SIZING variants of the locked
ZION book, through the gates. The live-book hypothesis: direction ~coin-flip, edge lives in sizing
(Van Tharp / per-asset payoff split). Prior expectation is REJECTION (conviction inverted OOS in the
tier cascade; conv-TRON overlays rejected on the persistence book) — testing honestly anyway.

FROZEN GRID (3 variants, no sweeping, declared before results):
  V1 RECORD-SIZED : block size x1.25 when the issuing trailing eff-n Wilson-LB >= 0.55, else x1.0.
                    (Conviction axis = the decision gate's own trailing record; strength can't be
                    used — the 3-lens book acts only on 3/3 unanimity, so strength never varies.)
  V2 PAYOFF-TILT  : weekly SPY/QQQ risk weights proportional to trailing-52wk realized sleeve
                    Sortino (floor 0, bounds 20-60% each of the 0.80 risk block), renormalized. PIT.
  V3 = V1 + V2.
Everything else identical to the locked book (20% 2Y hedge, dual throttle, 5% micro, 7.5% gold,
lev re-solved to the 10% DD cap).
GATES (all required to ADOPT): dSortino >= +0.05 at the DD cap AND unlev MaxDD not worse by >1pp
AND both sub-period halves (2007-16 / 2017-26) dSortino >= 0. Anything else = REJECT (null is final).
"""
import os, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
H = 2; DD_CAP = 0.10; SCORE0 = pd.Timestamp('2007-08-01')


def _l(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py'); wf = _l('wf', 'weekly_full_spy.py'); eng = _l('eng', 'weekly_reddawn_spy.py')
wlb_eff = eng.wlb_eff
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('1995-01-01')].reset_index(drop=True)


def yser(t):
    s = zw.yahoo_weekly(t)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


def sleeve(price):
    """returns (ret_arr, hiconv_arr): weekly sleeve return + 1 if the issuing block's trailing LB>=0.55."""
    panel = base.copy(); panel['SP_Price'] = price
    sp = np.asarray(price, float); dts = base['Date'].to_numpy(); cpi = base['US_CPI'].to_numpy(float)
    wf.H = H
    rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, panel); od = wf.odyssey(sp, dts, ret, lab); sc, _ = wf.sanctuary(sp, dts, ret, lab)
    weeks = sorted(set(rd) & set(od) & set(sc))
    dec = {}
    for t in weeks:
        pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
        dec[t] = pres[0] if (len(pres) >= 2 and len(set(pres)) == 1) else 0
    acted = []; k = n = 0
    for t in weeks:
        c = dec[t]
        if c != 0 and np.isfinite(lab[t]) and lab[t] != 0:
            if n >= 12 and wlb_eff(k, n, H) > 0.50:
                acted.append((t, c, 1 if wlb_eff(k, n, H) >= 0.55 else 0))
            k += int(c == lab[t]); n += 1
    wret = np.full(len(sp), np.nan); wret[1:] = sp[1:] / sp[:-1] - 1.0
    arr = np.zeros(len(base)); hic = np.zeros(len(base)); last = -10**9
    for t, c, hi in sorted(acted):
        if t - last >= H:
            for j in range(1, H + 1):
                if t + j < len(base):
                    hic[t + j] = hi
                    if np.isfinite(wret[t + j]): arr[t + j] += c * wret[t + j]
            arr[min(t + 1, len(base) - 1)] -= 5 / 1e4
            last = t
    return arr, hic


def diag(r):
    r = np.asarray(r, float); e = np.cumprod(1 + r)
    cagr = e[-1] ** (52 / len(r)) - 1
    dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2)); so = float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else np.nan
    dd = float((e / np.maximum.accumulate(e) - 1).min())
    return cagr, so, dd


def trailing_sortino_w(a0, a1, win=52):
    """PIT weekly weights for the 0.80 risk block from trailing-52wk realized sleeve Sortino."""
    n = len(a0); w0 = np.full(n, 0.4); w1 = np.full(n, 0.4)
    for i in range(win, n):
        s = []
        for a in (a0, a1):
            x = a[i - win:i]; dn = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
            s.append(max((np.mean(x) / dn * np.sqrt(52)) if dn > 0 else 0.0, 0.0))
        tot = s[0] + s[1]
        f0 = 0.5 if tot == 0 else s[0] / tot
        f0 = min(max(f0, 0.25), 0.75)                       # bounds 20-60% of book => 0.25-0.75 of block
        w0[i], w1[i] = 0.80 * f0, 0.80 * (1 - f0)
    return w0, w1


def main():
    print('building sleeves ...')
    a_spy, hi_spy = sleeve(base['SP_Price'].to_numpy(float))
    a_qqq, hi_qqq = sleeve(yser('QQQ'))
    gold_px = yser('GC=F'); gr = np.zeros(len(base)); gp = np.asarray(gold_px, float)
    gr[1:] = np.nan_to_num(gp[1:] / gp[:-1] - 1.0)
    mask = (base['Date'] >= SCORE0).to_numpy()
    vix = base['VIX_Close'].to_numpy(float); cred = base['Credit_BAA10Y'].to_numpy(float)
    def pctl_thr(series):
        t = np.ones(len(series))
        for w in range(len(series)):
            pri = series[:w]; pri = pri[np.isfinite(pri)]
            if len(pri) >= 50 and np.isfinite(series[w]) and (pri <= series[w]).mean() >= 0.70: t[w] = 0.5
        return t
    thr = (pctl_thr(vix) * pctl_thr(cred))
    # 2Y + micro
    import io
    raw = zw.fetch('https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2')
    dd2 = pd.read_csv(io.BytesIO(raw)); dd2.columns = ['date', 'val']; dd2['date'] = pd.to_datetime(dd2['date'])
    dd2['val'] = pd.to_numeric(dd2['val'], errors='coerce')
    y2 = dd2.set_index('date')['val'].reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('7D')).ffill().values
    t2 = np.nan_to_num(y2 / 100 / 52.0 - 1.9 * np.concatenate([[0.0], np.diff(y2)]) / 100.0)
    _mst = importlib.util.spec_from_file_location('mst', os.path.join(WT, 'silver_micro_test.py'))
    mst = importlib.util.module_from_spec(_mst); _mst.loader.exec_module(mst)
    ag = mst.silver_micro().reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()

    # baseline sleeve Sortino weights (frozen, as locked)
    def srt(x):
        dn = np.sqrt(np.mean(np.minimum(x[mask], 0.0) ** 2)); return float(np.mean(x[mask]) / dn * np.sqrt(52)) if dn > 0 else 0.0
    sS, sQ = srt(a_spy), srt(a_qqq)
    wsp, wqq = 0.80 * sS / (sS + sQ), 0.80 * sQ / (sS + sQ)
    w0_dyn, w1_dyn = trailing_sortino_w(a_spy, a_qqq)

    def book(mult_spy, mult_qqq, w0, w1):
        risk = (w0 * mult_spy * a_spy + w1 * mult_qqq * a_qqq) * thr
        bk = 0.20 * t2 + risk + 0.05 * ag + 0.075 * gr
        return bk[mask]

    ones = np.ones(len(base))
    variants = {
        'LOCKED (baseline)': book(ones, ones, np.full(len(base), wsp), np.full(len(base), wqq)),
        'V1 record-sized (LB>=.55 x1.25)': book(1 + 0.25 * hi_spy, 1 + 0.25 * hi_qqq,
                                                np.full(len(base), wsp), np.full(len(base), wqq)),
        'V2 payoff-tilt (trail-52wk Sortino)': book(ones, ones, w0_dyn, w1_dyn),
        'V3 = V1 + V2': book(1 + 0.25 * hi_spy, 1 + 0.25 * hi_qqq, w0_dyn, w1_dyn),
    }
    half = (base['Date'][mask] < pd.Timestamp('2017-01-01')).to_numpy()
    res = {}
    print(f"\n{'variant':38s} {'Sortino@cap':>11} {'CAGR@cap':>9} {'unlevDD':>8} {'h1 dSort':>9} {'h2 dSort':>9}  verdict")
    base_key = 'LOCKED (baseline)'
    c0, s0, d0 = diag(variants[base_key]); lev0 = DD_CAP / abs(d0)
    s0h1 = diag(variants[base_key][half])[1]; s0h2 = diag(variants[base_key][~half])[1]
    for nm, bk in variants.items():
        c, s, d = diag(bk); lev = DD_CAP / abs(d)
        cl, sl_, dl = diag(lev * bk)
        sh1, sh2 = diag(bk[half])[1], diag(bk[~half])[1]
        if nm == base_key:
            print(f"{nm:38s} {sl_:>11.2f} {cl*100:>8.2f}% {d*100:>7.1f}% {'—':>9} {'—':>9}  (reference)")
            continue
        g1 = (sl_ - s0) >= 0.05; g2 = (d - d0) >= -0.01; g3 = (sh1 - s0h1) >= 0 and (sh2 - s0h2) >= 0
        verdict = 'ADOPT-candidate' if (g1 and g2 and g3) else 'REJECT'
        res[nm] = verdict
        print(f"{nm:38s} {sl_:>11.2f} {cl*100:>8.2f}% {d*100:>7.1f}% {sh1-s0h1:>+9.2f} {sh2-s0h2:>+9.2f}  [{ 'G1' if g1 else '--'}{'G2' if g2 else '--'}{'G3' if g3 else '--'}] {verdict}")
    print("\nGates: G1 dSortino@cap>=+0.05, G2 unlev MaxDD not worse by >1pp, G3 both halves dSortino>=0. Null is final.")


if __name__ == '__main__':
    main()

"""
spread_persist_gates.py — PRE-DECLARED gate tests for the two live-ticket transfers (operator
2026-08-17): #1 long-Ag/short-Au SPREAD component, #4 PERSISTENCE-carry on the locked book.

FROZEN GRID (declared before results; no sweeping beyond it):
  A0 ratio-signal : SI=F/GC=F ratio run through the unified pipeline (sweep -> 3-lens -> LB>.50
                    decision). PRIOR: ABSTAIN (WTI:Silver precedent — ratio targets have no drift).
  A1 spread always-on   w in {2.5%, 5%}: +w silver / -w gold, permanent.
                    PRIOR: REJECT — Ag/Au ratio DECLINED most of 2011-2020; always-on likely loses.
  A2 spread micro-window w in {2.5%, 5%}: the spread ONLY while the silver micro is active
                    (vol episodes, ~8% of weeks) — i.e. a hedged version of the micro's metal beta.
                    PRIOR: the live-book evidence lives here (silver outruns gold in those windows).
  B1 persistence  : sleeve position HOLDS after each acted block until the NEXT acted decision
                    (abstain = hold; no expiry). Validated in the sister lineage.
  B2 persistence + stress-exit : as B1 but position flattens while the dual throttle is stressed
                    (thr < 1.0) — persistence with the existing risk machinery as the exit.
GATES vs LOCKED baseline (same harness as sized_variant_test — baseline Sortino ~2.37 with costs):
  G1 dSortino@10%DD-cap >= +0.05  ·  G2 unlev MaxDD not worse by >1pp  ·  G3 both halves dSort >= 0.
  ADOPT-candidate requires all three; anything else REJECT; null is final. Adoption would still be
  PROVISIONAL (forward tape) per standing rule.
Weight accounting: 1 unit spread = +w Ag / -w Au (adds 2w to gross; disclosed).
"""
import os, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
H = 2; DD_CAP = 0.10; SCORE0 = pd.Timestamp('2007-08-01')


def _l(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py'); wf = _l('wf', 'weekly_full_spy.py'); eng = _l('eng', 'weekly_reddawn_spy.py')
wlb_eff = eng.wlb_eff
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('1995-01-01')].reset_index(drop=True)


def yser(t):
    s = zw.yahoo_weekly(t)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


def sleeve_both(price):
    """One engine pass -> (block_arr, persist_arr, persist_pos): H-block returns AND persistence-carry
    returns (hold last acted dir until next acted decision)."""
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
            if n >= 12 and wlb_eff(k, n, H) > 0.50: acted.append((t, c))
            k += int(c == lab[t]); n += 1
    wret = np.full(len(sp), np.nan); wret[1:] = sp[1:] / sp[:-1] - 1.0
    blk = np.zeros(len(base)); last = -10**9
    for t, c in sorted(acted):
        if t - last >= H:
            for j in range(1, H + 1):
                if t + j < len(base) and np.isfinite(wret[t + j]): blk[t + j] += c * wret[t + j]
            blk[min(t + 1, len(base) - 1)] -= 5 / 1e4
            last = t
    # persistence: pos holds from each acted decision until the next acted decision
    pos = np.zeros(len(base)); cur = 0.0; ai = {t: c for t, c in acted}
    for t in range(len(base)):
        if t in ai: cur = float(ai[t])
        pos[t] = cur
    per = np.zeros(len(base)); prev = 0.0
    for t in range(1, len(base)):
        p = pos[t - 1]                                     # position entering week t
        if np.isfinite(wret[t]): per[t] = p * wret[t] - 5 / 1e4 * abs(p - prev)
        prev = p
    return blk, per, pos


def diag(r):
    r = np.asarray(r, float); e = np.cumprod(1 + r)
    cagr = e[-1] ** (52 / len(r)) - 1
    dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2)); so = float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else np.nan
    dd = float((e / np.maximum.accumulate(e) - 1).min())
    return cagr, so, dd


def main():
    print('building sleeves (block + persistence in one pass) ...')
    b_spy, p_spy, pos_spy = sleeve_both(base['SP_Price'].to_numpy(float))
    b_qqq, p_qqq, pos_qqq = sleeve_both(yser('QQQ'))
    gold = yser('GC=F'); silver = yser('SI=F')
    def wr(px):
        px = np.asarray(px, float); r = np.zeros(len(px)); r[1:] = np.nan_to_num(px[1:] / px[:-1] - 1.0); return r
    au_r, ag_r = wr(gold), wr(silver)
    mask = (base['Date'] >= SCORE0).to_numpy()
    vix = base['VIX_Close'].to_numpy(float); cred = base['Credit_BAA10Y'].to_numpy(float)
    def pctl_thr(series):
        t = np.ones(len(series))
        for w in range(len(series)):
            pri = series[:w]; pri = pri[np.isfinite(pri)]
            if len(pri) >= 50 and np.isfinite(series[w]) and (pri <= series[w]).mean() >= 0.70: t[w] = 0.5
        return t
    thr = pctl_thr(vix) * pctl_thr(cred)
    import io
    raw = zw.fetch('https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2')
    d2 = pd.read_csv(io.BytesIO(raw)); d2.columns = ['date', 'val']; d2['date'] = pd.to_datetime(d2['date'])
    d2['val'] = pd.to_numeric(d2['val'], errors='coerce')
    y2 = d2.set_index('date')['val'].reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('7D')).ffill().values
    t2 = np.nan_to_num(y2 / 100 / 52.0 - 1.9 * np.concatenate([[0.0], np.diff(y2)]) / 100.0)
    mst = _l('mst', 'silver_micro_test.py')
    ag_ser = mst.silver_micro()
    ag_al = ag_ser.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()
    micro_on = (np.abs(ag_al) > 1e-9).astype(float)

    def srt(x):
        dn = np.sqrt(np.mean(np.minimum(x[mask], 0.0) ** 2)); return float(np.mean(x[mask]) / dn * np.sqrt(52)) if dn > 0 else 0.0
    sS, sQ = srt(b_spy), srt(b_qqq)
    wsp, wqq = 0.80 * sS / (sS + sQ), 0.80 * sQ / (sS + sQ)
    spread = ag_r - au_r                                     # 1 unit = +1 Ag / -1 Au

    def book(risk_spy, risk_qqq, extra=None):
        risk = (wsp * risk_spy + wqq * risk_qqq) * thr
        bk = 0.20 * t2 + risk + 0.05 * ag_al + 0.075 * au_r * 0 + 0.075 * wr(gold)  # gold overlay
        if extra is not None: bk = bk + extra
        return bk[mask]

    variants = {
        'LOCKED (baseline)': book(b_spy, b_qqq),
        'A1a spread always 2.5%': book(b_spy, b_qqq, 0.025 * spread),
        'A1b spread always 5%': book(b_spy, b_qqq, 0.05 * spread),
        'A2a spread micro-window 2.5%': book(b_spy, b_qqq, 0.025 * spread * micro_on),
        'A2b spread micro-window 5%': book(b_spy, b_qqq, 0.05 * spread * micro_on),
        'B1 persistence (abstain=hold)': book(p_spy, p_qqq),
        'B2 persistence + stress-exit': book(p_spy * (thr >= 1.0), p_qqq * (thr >= 1.0)),
    }
    half = (base['Date'][mask] < pd.Timestamp('2017-01-01')).to_numpy()
    key0 = 'LOCKED (baseline)'
    c0, s0, d0 = diag(variants[key0]); s0h1 = diag(variants[key0][half])[1]; s0h2 = diag(variants[key0][~half])[1]
    print(f"\n{'variant':34s} {'Sortino@cap':>11} {'CAGR@cap':>9} {'unlevDD':>8} {'h1 dS':>7} {'h2 dS':>7}  verdict")
    for nm, bk in variants.items():
        c, s, d = diag(bk); lev = DD_CAP / abs(d)
        cl, sl_, dl = diag(lev * bk)
        sh1, sh2 = diag(bk[half])[1], diag(bk[~half])[1]
        if nm == key0:
            print(f"{nm:34s} {sl_:>11.2f} {cl*100:>8.2f}% {d*100:>7.1f}% {'—':>7} {'—':>7}  (reference)")
            continue
        g1 = (sl_ - s0) >= 0.05; g2 = (d - d0) >= -0.01; g3 = (sh1 - s0h1) >= 0 and (sh2 - s0h2) >= 0
        verdict = 'ADOPT-candidate' if (g1 and g2 and g3) else 'REJECT'
        gates = ('G1' if g1 else '--') + ('G2' if g2 else '--') + ('G3' if g3 else '--')
        print(f"{nm:34s} {sl_:>11.2f} {cl*100:>8.2f}% {d*100:>7.1f}% {sh1-s0h1:>+7.2f} {sh2-s0h2:>+7.2f}  [{gates}] {verdict}")
    # in-market lift from persistence (context)
    im_b = float(((np.abs(b_spy) + np.abs(b_qqq))[mask] > 0).mean())
    im_p = float(((np.abs(p_spy) + np.abs(p_qqq))[mask] > 0).mean())
    print(f"\ncontext: risk-sleeve in-market {im_b*100:.0f}% (blocks) -> {im_p*100:.0f}% (persistence)")
    # dump B2 + baseline series for Amendment 2 (exact lev + universe re-quote)
    b2 = variants['B2 persistence + stress-exit']; c2, s2, d2 = diag(b2)
    print(f"B2 exact: unlev DD {d2*100:.2f}% -> lev-to-cap {DD_CAP/abs(d2):.3f}x")
    pd.DataFrame({'Date': base['Date'][mask].to_numpy(), 'locked': variants[key0], 'b2': b2}).to_csv(
        os.path.join(REP, 'b2_series.csv'), index=False)
    print('[dumped] reports/b2_series.csv')
    # A0: ratio through the pipeline (predictive test)
    print('\nA0 — SI/GC ratio through the unified pipeline (predictive):')
    far = _l('far', 'fresh_asset_run.py', HERE)
    try:
        ratio_px = np.asarray(silver, float) / np.asarray(gold, float)
        far.run('AG_AU_RATIO', pd.Series(ratio_px, index=far.spy['Date']).reindex(far.spy['Date']).values, '2000-09-01')
    except Exception as e:
        print(f'  A0 failed: {repr(e)[:140]}')


if __name__ == '__main__':
    main()

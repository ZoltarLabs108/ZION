"""
fresh_asset_run.py — run the unified weekly system on FRESH assets (different covered weeks than SPY).
No drift gate (operator): decision = trailing eff-n Wilson-LB > 0.50. Components need NOT beat SPX on
calendar (operator: that analysis is for the combined book only). Reports predictors + per-stage acc +
coverage + firing/calendar numbers. Assets: QQQ (Yahoo), WTI:Silver (panel WTI / Yahoo silver).
"""
import os, importlib.util
import numpy as np, pandas as pd
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')


def _load(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _load('zw', 'zion_weekly.py'); wf = _load('wf', 'weekly_full_spy.py')
ps = _load('ps', 'predictor_search.py'); HS = _load('hs', 'stage_hsweep.py', HERE)
eng = _load('eng', 'weekly_reddawn_spy.py'); wlb_eff = eng.wlb_eff
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])


def yser(ticker):
    s = zw.yahoo_weekly(ticker)
    if isinstance(s, pd.DataFrame):
        s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index); return s


def align(s):
    return s.reindex(spy['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


def run(name, price, start):
    panel = spy.copy(); panel['SP_Price'] = price
    panel = panel[(panel['Date'] >= pd.Timestamp(start)) & np.isfinite(panel['SP_Price'])].reset_index(drop=True)
    qpath = os.path.join(REP, f'{name}_panel.csv'); panel.to_csv(qpath, index=False)
    sp = panel['SP_Price'].to_numpy(float); dts = panel['Date'].to_numpy(); cpi = panel['US_CPI'].to_numpy(float)
    fh, _, _ = HS.sweep(qpath, os.path.join(REP, f'{name}_hsweep.csv'))
    NATIVE = [('VIX/Dollar', 'VIX_Close', 'Dollar_Index'), ('VIX/SP', 'VIX_Close', 'SP_Price'),
              ('Gold/Dollar', 'Gold_Close', 'Dollar_Index'), ('Copper/Dollar', 'Copper_Close', 'Dollar_Index'),
              ('FedFunds/GS10', 'Fed_Funds_Rate', 'GS10_Rate')]
    cres = [ps.evaluate(panel, sp, dts, nm, nc, dc, set(), cpi) for nm, nc, dc in NATIVE]
    okc = [r for r in cres if r.get('status') == 'ok']
    qual = sorted([r for r in okc if r.get('qualified')], key=lambda r: (r['n_reliable'], r['coverage']*r['blended_acc']), reverse=True)
    winner = qual[0] if qual else None
    wf.H = int(fh)
    rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, panel); od = wf.odyssey(sp, dts, ret, lab); sc, band = wf.sanctuary(sp, dts, ret, lab)
    weeks = sorted(set(rd) & set(od) & set(sc))
    def acc(dm):
        s = [(t, dm[t]) for t in weeks if dm[t] != 0 and np.isfinite(lab[t]) and lab[t] != 0]
        return (len(s), (float(np.mean([int(dr == lab[t]) for t, dr in s])) if s else float('nan')))
    ea = {nm: acc(dm) for nm, dm in [('RED DAWN', rd), ('ODYSSEY', od), ('SANCTUARY', sc)]}
    dec = {}
    for t in weeks:
        pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
        dec[t] = (pres[0], len(pres)) if (len(pres) >= 2 and len(set(pres)) == 1) else (0, len(pres))
    conv = [(t, dec[t][0]) for t in weeks if dec[t][0] != 0 and np.isfinite(lab[t]) and lab[t] != 0]
    conv_n = len(conv); conv_acc = float(np.mean([int(d == lab[t]) for t, d in conv])) if conv else float('nan')
    drift = float(np.mean([lab[t] > 0 for t in weeks if np.isfinite(lab[t]) and lab[t] != 0]))
    H = int(fh); retH = np.full(len(sp), np.nan); retH[:len(sp)-H] = sp[H:]/sp[:len(sp)-H]-1
    acted = []; k = n = 0
    for t in weeks:
        c = dec[t][0]
        if c != 0 and np.isfinite(lab[t]) and lab[t] != 0:
            if n >= 12 and wlb_eff(k, n, H) > 0.50: acted.append((t, c))
            k += int(c == lab[t]); n += 1
    cov = len(acted)/conv_n if conv_n else 0.0
    blocks = []; bd = []; last = -10**9
    for t, c in sorted(acted):
        if t - last >= H and np.isfinite(retH[t]): blocks.append(c*retH[t]-5/1e4); last = t; bd.append(dts[t])
    x = np.array(blocks); eqv = float(np.cumprod(1+x)[-1]) if len(x) else 1.0
    fy = len(x)*H/52.0; cy = ((pd.Timestamp(bd[-1])-pd.Timestamp(bd[0])).days/365.25) if len(bd) > 1 else fy
    dd = np.sqrt(np.mean(np.minimum(x, 0.0)**2)) if len(x) else np.nan
    sor = float(np.mean(x)/dd*np.sqrt(52.0/H)) if (len(x) and dd > 0) else float('nan')
    print("=" * 74)
    print(f"{name} — unified weekly (winner={winner['name'] if winner else None}, H={fh}wk, NO drift gate) "
          f"| {panel['Date'].min():%Y-%m}..{panel['Date'].max():%Y-%m} scored={len(weeks)}")
    print(f"  Stage1 predictors: evaluated {len(NATIVE)}, qualified {len(qual)}  " +
          " | ".join(f"{r['name']} {r['blended_acc']*100:.0f}%/{r['coverage']*100:.0f}%cov{'*' if r.get('qualified') else ''}" for r in sorted(okc, key=lambda r:(r['n_reliable'], r['coverage']*r['blended_acc']), reverse=True)))
    print(f"  Stage4 engines: RD {ea['RED DAWN'][1]*100:.1f}%  ODY {ea['ODYSSEY'][1]*100:.1f}%  "
          f"SANC {ea['SANCTUARY'][1]*100:.1f}%  | DRIFT {drift*100:.1f}%  CONV {conv_acc*100:.1f}% (n={conv_n})")
    print(f"  Stage5 decision (LB>0.50): acted {len(acted)}/{conv_n} -> COVERAGE {cov*100:.1f}%")
    print(f"  Stage6 ledger: {len(x)} blocks {eqv:.2f}x | FIRING CAGR {eqv**(1/fy)-1 if fy>0 else float('nan'):.2%} Sortino {sor:.2f}"
          f" | CALENDAR({cy:.0f}y) CAGR {eqv**(1/cy)-1 if cy>0 else float('nan'):.2%}")


if __name__ == '__main__':
    try:
        run('QQQ', align(yser('QQQ')), '1999-03-12')
    except Exception as e:
        print(f"QQQ failed: {repr(e)[:160]}")
    try:
        sil = align(yser('SI=F'))
        ratio = spy['WTI_Crude_Close'].to_numpy(float) / sil
        run('WTI_SILVER', ratio, '2000-06-01')
    except Exception as e:
        print(f"WTI:Silver failed: {repr(e)[:160]}")

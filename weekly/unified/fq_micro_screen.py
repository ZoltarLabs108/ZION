"""
fq_micro_screen.py — PRE-DECLARED flight-to-quality micro screen (operator 2026-08-17).
The metal micro family = ONE mechanism (fear-bid metal, all-long, same vol windows). This screen
tests the OPPOSITE-response family, never screened: duration (long bonds on fear) and risk-off JPY.
Targets: TLT (2002+), IEF (2002+), JPY (=X, 1996+). Pairs (frozen, from the panel's native legs):
(VIX,Dollar), (Credit_BAA10Y,Dollar), (VIX,GS10). Template frozen N=8 H=4 episodic. Gates G1-G4
identical to micro_screen. 9 cells, declared, null is final.
"""
import os, math, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
COST = 5 / 1e4; N_TPL, H_TPL = 8, 4


def _l(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py')


def wilson_lb(k, n, z=1.96):
    if n <= 0: return 0.0
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return (c - m) / d


def sortino(r):
    r = np.asarray(r, float); dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
    return float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else float('nan')


spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('1996-01-01')].reset_index(drop=True)
lk = pd.read_csv(os.path.join(REP, 'locked_book.csv')); lk['Date'] = pd.to_datetime(lk['Date'])
cal = pd.DatetimeIndex(lk['Date']); locked = lk['locked'].to_numpy(float); s0 = sortino(locked)


def yser(t):
    s = zw.yahoo_weekly(t)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


PAIRS = [('VIX/Dollar', 'VIX_Close', 'Dollar_Index'),
         ('Credit/Dollar', 'Credit_BAA10Y', 'Dollar_Index'),
         ('VIX/GS10', 'VIX_Close', 'GS10_Rate')]
TARGETS = [('TLT', 'TLT'), ('IEF', 'IEF'), ('JPY', 'JPY%3DX')]
print(f"FLIGHT-TO-QUALITY MICRO SCREEN — frozen N={N_TPL}/H={H_TPL}, 9 declared cells, gates G1-G4")
print(f"{'cell':26s} {'n':>4} {'acc':>6} {'LB':>5} {'yrs':>4} {'maxYr':>6} {'%long':>6} {'corr':>6} {'dSort':>7}  gates")
survivors = []
for tname, tk in TARGETS:
    P = base[['Date', 'VIX_Close', 'Dollar_Index', 'Credit_BAA10Y', 'GS10_Rate', 'US_CPI']].copy()
    try:
        P['TARGET'] = yser(tk)
    except Exception as e:
        print(f"{tname}: fetch failed {repr(e)[:60]}"); continue
    P = P[np.isfinite(P['TARGET'])].reset_index(drop=True)
    for pname, num, den in PAIRS:
        nm = f"{tname}: {pname}"
        de = P['Date'].iloc[0] + (P['Date'].iloc[-1] - P['Date'].iloc[0]) * 0.4
        try:
            s, ret, lab = zw.stream(P, num, den, N_TPL, H_TPL, set(), de)
        except Exception as e:
            print(f"{nm:26s} stream failed: {repr(e)[:56]}"); continue
        tgt = P['TARGET'].to_numpy(float); calP = pd.to_datetime(P['Date'])
        r1 = np.full(len(tgt), np.nan); r1[:-1] = tgt[1:] / tgt[:-1] - 1.0
        pos = np.zeros(len(tgt)); hold = 0; cur = 0.0
        for t in range(len(tgt)):
            d = s.get(t); d = d if d not in (0, None) else 0
            if d != 0: cur = float(d); hold = H_TPL
            elif hold > 0: hold -= 1
            else: cur = 0.0
            pos[t] = cur if hold > 0 or d != 0 else 0.0
        rows = {}; prev = 0.0
        for t in range(len(tgt)):
            if not np.isfinite(r1[t]): continue
            rows[calP.iloc[t]] = r1[t] * pos[t] - COST * abs(pos[t] - prev); prev = pos[t]
        ser = pd.Series(rows)
        fires = [(t, s[t]) for t in sorted(s) if s[t] not in (0, None) and np.isfinite(lab[t]) and lab[t] != 0]
        hits = [int(d == lab[t]) for t, d in fires]
        years = pd.Series([calP.iloc[t].year for t, _ in fires])
        acc = float(np.mean(hits)) if hits else float('nan')
        lb = wilson_lb(int(np.sum(hits)), len(hits))
        nyr = years.nunique(); maxyr = float(years.value_counts(normalize=True).max()) if len(years) else float('nan')
        plong = float(np.mean([d > 0 for _, d in fires])) if fires else float('nan')
        a = ser.reindex(cal, method='nearest', tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()
        act = np.abs(a) > 1e-9
        corr = float(np.corrcoef(a[act], locked[act])[0, 1]) if act.sum() > 10 else float('nan')
        ds = sortino(locked + 0.05 * a) - s0
        g1 = (len(fires) >= 30) and (acc >= 0.65) and (lb >= 0.55)
        g2 = (nyr >= 3) and (maxyr <= 0.45)
        g3 = np.isfinite(corr) and abs(corr) < 0.30
        g4 = ds >= -0.01
        gates = ''.join(c if okg else '-' for c, okg in zip('1234', (g1, g2, g3, g4)))
        verdict = 'PASS' if all((g1, g2, g3, g4)) else ''
        if verdict: survivors.append(nm)
        print(f"{nm:26s} {len(fires):>4} {acc*100:>5.1f}% {lb:>5.2f} {nyr:>4} "
              f"{maxyr*100 if np.isfinite(maxyr) else float('nan'):>5.0f}% "
              f"{plong*100 if np.isfinite(plong) else float('nan'):>5.0f}% {corr:>+6.2f} {ds:>+7.3f}  [{gates}] {verdict}")
print(f"\nSurvivors: {len(survivors)} {survivors if survivors else '— honest null'}  (null final; survivors = PROVISIONAL, forward tape)")

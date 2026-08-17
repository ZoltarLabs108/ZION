"""
ng_micro_screen.py — PRE-DECLARED micro-sleeve screen for NATGAS (operator 2026-08-17).
NG was NOT a target in the 2026-08-16 11-cell screen; this is its first micro test.

Theory cell: the silver micro is "fear + soft industry -> monetary-metal bid"; the NG analog is
"fear + TIGHT STORAGE -> squeeze bid" (2014 polar vortex, 2021 winter, 2022 Freeport).
FROZEN silver template (N=8, H=4, episodic hold-and-extend, no sweeping). Declared grid (3 cells):
  1. (VIX_Close, NG_Storage_Level)      — fear x storage tightness (the theory cell)
  2. (NG_Storage_Level, Dollar_Index)   — storage momentum vs USD
  3. (VIX_Close, Dollar_Index)          — control (no storage)
GATES (identical to micro_screen): G1 acc>=65%, n>=30, WLB>=0.55 · G2 >=3 yrs, max-yr<=45% ·
G3 |corr to locked book|<0.30 on active weeks · G4 +5% overlay must not cut book Sortino.
Caveat: storage feature valid ~2011+ -> short window; G1's n>=30 is a real hurdle; null is final.
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


# ---- panel: NG target + storage pseudo-level + macro legs ----
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('2005-01-01')].reset_index(drop=True)
sto = pd.read_csv(os.path.join(REP, 'hyperion_ng_storage.csv')); sto['Date'] = pd.to_datetime(sto['Date'])
P = base[['Date', 'VIX_Close', 'Dollar_Index', 'US_CPI']].copy()
P['NG_Storage_Level'] = sto.set_index('Date')['storage_level_idx'].reindex(P['Date']).values
ng = zw.yahoo_weekly('NG%3DF')
if isinstance(ng, pd.DataFrame): ng = ng['Close'] if 'Close' in ng.columns else ng.iloc[:, 0]
ng.index = pd.to_datetime(ng.index)
P['TARGET'] = ng.reindex(P['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values
P = P[np.isfinite(P['TARGET'])].reset_index(drop=True)

lk = pd.read_csv(os.path.join(REP, 'locked_book.csv')); lk['Date'] = pd.to_datetime(lk['Date'])
cal = pd.DatetimeIndex(lk['Date']); locked = lk['locked'].to_numpy(float)
s0 = sortino(locked)

CELLS = [('VIX/StorageIdx (theory)', 'VIX_Close', 'NG_Storage_Level'),
         ('StorageIdx/Dollar', 'NG_Storage_Level', 'Dollar_Index'),
         ('VIX/Dollar (control)', 'VIX_Close', 'Dollar_Index')]
print(f"NG MICRO SCREEN — frozen N={N_TPL}/H={H_TPL}, 3 declared cells, gates G1-G4 (silver-template)")
print(f"{'cell':28s} {'n':>4} {'acc':>6} {'LB':>5} {'yrs':>4} {'maxYr':>6} {'%long':>6} {'corr':>6} {'dSort':>7}  gates")
for nm, num, den in CELLS:
    de = P['Date'].iloc[0] + (P['Date'].iloc[-1] - P['Date'].iloc[0]) * 0.4
    try:
        s, ret, lab = zw.stream(P, num, den, N_TPL, H_TPL, set(), de)
    except Exception as e:
        print(f"{nm:28s} stream failed: {repr(e)[:70]}"); continue
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
    gates = ''.join(c if ok else '-' for c, ok in zip('1234', (g1, g2, g3, g4)))
    verdict = 'PASS' if all((g1, g2, g3, g4)) else ''
    print(f"{nm:28s} {len(fires):>4} {acc*100:>5.1f}% {lb:>5.2f} {nyr:>4} "
          f"{maxyr*100 if np.isfinite(maxyr) else float('nan'):>5.0f}% "
          f"{plong*100 if np.isfinite(plong) else float('nan'):>5.0f}% {corr:>+6.2f} {ds:>+7.3f}  [{gates}] {verdict}")
print("\nnull is final: no re-run at lower bars, no added cells. Survivors would be PROVISIONAL (forward tape).")

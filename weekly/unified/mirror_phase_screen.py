"""
mirror_phase_screen.py — PRE-DECLARED recovery-cell (mirror-phase) screen (operator 2026-08-17).

MECHANISM (new class — every prior cell was stress-ENTRY; this is the exit side): when the book's
dual throttle returns to CALM after a real stress spell, buy rebound-character assets for the
recovery window.

FROZEN RULE (declared before results, nothing swept):
  trigger : thr==1.0 first week after >=2 consecutive stressed weeks (thr<1.0). Exogenous
            (VIX/credit percentile state — the book's standing regime machinery), PIT.
  action  : LONG target for H=4 wks (silver-template hold), extend on re-trigger. 5bps on changes.
  targets : SPY(^GSPC), QQQ, Silver(SI=F), GDX, WTI(CL=F), HYG  — 6 declared rebound candidates.
GATES (identical to every micro screen): G1 n>=30, acc>=65%, WLB>=0.55 · G2 >=3yrs, max-yr<=45%
· G3 |corr to locked book|<0.30 active-weeks · G4 +5% overlay must not cut book Sortino.
HONEST RISK: recovery weeks are when the persistence book RE-ENTERS -> co-phased exposure is the
expected failure mode (G3). Null is final.
"""
import os, math, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
COST = 5 / 1e4; H = 4; SPELL = 2


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
base = spy[spy['Date'] >= pd.Timestamp('1995-01-01')].reset_index(drop=True)
vix = base['VIX_Close'].to_numpy(float); cred = base['Credit_BAA10Y'].to_numpy(float)


def pctl_thr(series):
    t = np.ones(len(series))
    for w in range(len(series)):
        pri = series[:w]; pri = pri[np.isfinite(pri)]
        if len(pri) >= 50 and np.isfinite(series[w]) and (pri <= series[w]).mean() >= 0.70: t[w] = 0.5
    return t


thr = pctl_thr(vix) * pctl_thr(cred)
stressed = thr < 1.0
events = []
run = 0
for i in range(len(base)):
    if stressed[i]: run += 1
    else:
        if run >= SPELL: events.append(i)          # first calm week after a real spell
        run = 0
print(f"recovery events: {len(events)} over {base['Date'].iloc[0].date()}..{base['Date'].iloc[-1].date()} "
      f"(stress spells >= {SPELL} wks); years: {sorted(set(base['Date'].iloc[i].year for i in events))}")

lk = pd.read_csv(os.path.join(REP, 'locked_book.csv')); lk['Date'] = pd.to_datetime(lk['Date'])
cal = pd.DatetimeIndex(lk['Date']); locked = lk['locked'].to_numpy(float); s0 = sortino(locked)


def yser(t):
    s = zw.yahoo_weekly(t)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


TARGETS = [('SPY', '%5EGSPC'), ('QQQ', 'QQQ'), ('Silver', 'SI%3DF'),
           ('GDX', 'GDX'), ('WTI', 'CL%3DF'), ('HYG', 'HYG')]
print(f"\n{'target':8s} {'ev':>4} {'acc':>6} {'LB':>5} {'yrs':>4} {'maxYr':>6} {'medRet':>7} {'corr':>6} {'dSort':>7}  gates")
survivors = []
for nm, tk in TARGETS:
    px = yser(tk)
    r1 = np.full(len(px), np.nan); r1[1:] = np.asarray(px, float)[1:] / np.asarray(px, float)[:-1] - 1.0
    retH = np.full(len(px), np.nan); retH[:len(px) - H] = np.asarray(px, float)[H:] / np.asarray(px, float)[:len(px) - H] - 1.0
    ev_ok = [i for i in events if np.isfinite(retH[i]) and np.isfinite(px[i])]
    hits = [int(retH[i] > 0) for i in ev_ok]
    rets = [retH[i] for i in ev_ok]
    years = pd.Series([base['Date'].iloc[i].year for i in ev_ok])
    acc = float(np.mean(hits)) if hits else float('nan')
    lb = wilson_lb(int(np.sum(hits)), len(hits))
    nyr = years.nunique(); maxyr = float(years.value_counts(normalize=True).max()) if len(years) else float('nan')
    med = float(np.median(rets)) if rets else float('nan')
    pos = np.zeros(len(base)); hold = 0
    for i in range(len(base)):
        if i in ev_ok: hold = H
        if hold > 0: pos[i] = 1.0; hold -= 1
    ser = {}; prev = 0.0
    for i in range(len(base)):
        if not np.isfinite(r1[i]): continue
        p_in = pos[i - 1] if i > 0 else 0.0
        ser[base['Date'].iloc[i]] = p_in * r1[i] - COST * abs(p_in - prev); prev = p_in
    a = pd.Series(ser).reindex(cal, method='nearest', tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()
    act = np.abs(a) > 1e-9
    corr = float(np.corrcoef(a[act], locked[act])[0, 1]) if act.sum() > 10 else float('nan')
    ds = sortino(locked + 0.05 * a) - s0
    g1 = (len(ev_ok) >= 30) and (acc >= 0.65) and (lb >= 0.55)
    g2 = (nyr >= 3) and (maxyr <= 0.45)
    g3 = np.isfinite(corr) and abs(corr) < 0.30
    g4 = ds >= -0.01
    gates = ''.join(c if okg else '-' for c, okg in zip('1234', (g1, g2, g3, g4)))
    verdict = 'PASS' if all((g1, g2, g3, g4)) else ''
    if verdict: survivors.append(nm)
    print(f"{nm:8s} {len(ev_ok):>4} {acc*100:>5.1f}% {lb:>5.2f} {nyr:>4} "
          f"{maxyr*100 if np.isfinite(maxyr) else float('nan'):>5.0f}% {med*100:>+6.1f}% {corr:>+6.2f} {ds:>+7.3f}  [{gates}] {verdict}")
print(f"\nSurvivors: {len(survivors)} {survivors if survivors else '— honest null'}  (null final; PASS = PROVISIONAL, forward tape)")

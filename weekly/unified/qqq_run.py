"""
qqq_run.py — run the unified weekly system on QQQ (fresh asset, DIFFERENT up/down weeks than SPY).
No drift gate (operator): decision = trailing eff-n Wilson-LB > 0.50. Reports predictor count,
per-stage/per-engine accuracy, coverage, and firing + calendar numbers. Redundancy w/ SPY is fine.

QQQ (Nasdaq-100 ETF) weekly from Yahoo (1999+), merged with the SAME market-wide predictors as the
SPY panel (VIX, Dollar, Gold, Copper, CPI). CAPE/Real_Earnings are SP-specific and unused by the
VIX/Dollar + price engines, so they don't matter here.
"""
import os, importlib.util
import numpy as np, pandas as pd

WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')


def _load(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _load('zw', 'zion_weekly.py')
wf = _load('wf', 'weekly_full_spy.py')
ps = _load('ps', 'predictor_search.py')
HS = _load('hs', 'stage_hsweep.py', HERE)
eng = _load('eng', 'weekly_reddawn_spy.py'); wlb_eff = eng.wlb_eff

# ---- build QQQ weekly panel (QQQ price into 'SP_Price', same predictors) ----
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
qraw = zw.yahoo_weekly('QQQ')                              # DatetimeIndex weekly closes
qser = qraw['Close'] if 'Close' in getattr(qraw, 'columns', []) else qraw.iloc[:, 0]
qser.index = pd.to_datetime(qser.index)
cal = spy['Date']
qaligned = qser.reindex(cal, method='nearest', tolerance=pd.Timedelta('4D')).ffill().values
panel = spy.copy(); panel['SP_Price'] = qaligned                 # engines read 'SP_Price' = QQQ now
panel = panel[panel['Date'] >= pd.Timestamp('1999-03-12')].reset_index(drop=True)
qpath = os.path.join(REP, 'qqq_panel.csv'); panel.to_csv(qpath, index=False)

sp = panel['SP_Price'].to_numpy(float); dts = panel['Date'].to_numpy(); cpi = panel['US_CPI'].to_numpy(float)

# ---- Stage 0.5: horizon sweep (reuse; sweep() takes a panel path) ----
HS.CANDIDATES = [('VIX/Dollar', 'VIX_Close', 'Dollar_Index'), ('VIX/SP', 'VIX_Close', 'SP_Price'),
                 ('Gold/Dollar', 'Gold_Close', 'Dollar_Index')]
fh, sres, sagg = HS.sweep(qpath, os.path.join(REP, 'QQQ_hsweep.csv'))

# ---- Stage 1: val-winner over candidates ----
NATIVE = [('VIX/Dollar', 'VIX_Close', 'Dollar_Index'), ('VIX/SP', 'VIX_Close', 'SP_Price'),
          ('Gold/Dollar', 'Gold_Close', 'Dollar_Index'), ('Copper/Dollar', 'Copper_Close', 'Dollar_Index')]
cres = [ps.evaluate(panel, sp, dts, nm, nc, dc, set(), cpi) for nm, nc, dc in NATIVE]
okc = [r for r in cres if r.get('status') == 'ok']
qual = sorted([r for r in okc if r.get('qualified')], key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True)
winner = qual[0] if qual else None

# ---- Stage 4: 3-lens convergence at frozen H ----
wf.H = int(fh)
rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, panel)
od = wf.odyssey(sp, dts, ret, lab)
sc, band = wf.sanctuary(sp, dts, ret, lab)
weeks = sorted(set(rd) & set(od) & set(sc))
def acc(dm):
    s = [(t, dm[t]) for t in weeks if dm[t] != 0 and np.isfinite(lab[t]) and lab[t] != 0]
    return (len(s), (float(np.mean([int(dr == lab[t]) for t, dr in s])) if s else float('nan')))
eacc = {nm: acc(dm) for nm, dm in [('RED DAWN', rd), ('ODYSSEY', od), ('SANCTUARY', sc)]}
dec = {}
for t in weeks:
    pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
    dec[t] = (pres[0], len(pres)) if (len(pres) >= 2 and len(set(pres)) == 1) else (0, len(pres))
conv = [(t, dec[t][0]) for t in weeks if dec[t][0] != 0 and np.isfinite(lab[t]) and lab[t] != 0]
conv_n = len(conv); conv_acc = float(np.mean([int(d == lab[t]) for t, d in conv])) if conv else float('nan')
drift = float(np.mean([lab[t] > 0 for t in weeks if np.isfinite(lab[t]) and lab[t] != 0]))

# ---- Stage 5: decision LB>0.50 (NO drift gate) + Stage 6 ledger ----
H = int(fh); retH = np.full(len(sp), np.nan); retH[:len(sp) - H] = sp[H:] / sp[:len(sp) - H] - 1.0
acted = []; k = n = 0
for t in weeks:
    c = dec[t][0]
    if c != 0 and np.isfinite(lab[t]) and lab[t] != 0:
        if n >= 12 and wlb_eff(k, n, H) > 0.50: acted.append((t, c))
        k += int(c == lab[t]); n += 1
total = conv_n; coverage = len(acted) / total if total else 0.0
blocks = []; bdates = []; last = -10**9
for t, c in sorted(acted):
    if t - last >= H and np.isfinite(retH[t]):
        blocks.append(c * retH[t] - 5/1e4); last = t; bdates.append(dts[t])
x = np.array(blocks); eqv = np.cumprod(1 + x) if len(x) else np.array([1.0])
firing_years = len(x) * H / 52.0
cal_years = ((pd.Timestamp(bdates[-1]) - pd.Timestamp(bdates[0])).days / 365.25) if len(bdates) > 1 else firing_years
dd = np.sqrt(np.mean(np.minimum(x, 0.0)**2)) if len(x) else np.nan
sortino_f = float(np.mean(x)/dd*np.sqrt(52.0/H)) if (len(x) and dd > 0) else float('nan')

print("=" * 74)
print(f"QQQ — unified weekly system (val-winner={winner['name'] if winner else None}, frozen H={fh}wk, NO drift gate)")
print(f"QQQ weekly {panel['Date'].min():%Y-%m}..{panel['Date'].max():%Y-%m}  scored weeks (2007+)={len(weeks)}")
print("=" * 74)
print("\nStage 1 — val-winner candidates (blended acc on reliable types):")
for r in sorted(okc, key=lambda r: (r['n_reliable'], r['coverage']*r['blended_acc']), reverse=True):
    print(f"  {r['name']:14s} N={r['N']:>2} H={r['H']:>2} n_rel={r['n_reliable']} cov={r['coverage']*100:4.1f}% "
          f"bacc={r['blended_acc']*100:4.1f}% qualified={r.get('qualified')}")
print(f"  -> predictors evaluated={len(NATIVE)}, qualified={len(qual)}, WINNER={winner['name'] if winner else None}")
print("\nStage 4 — engine accuracy (full-week):")
for nm in ['RED DAWN', 'ODYSSEY', 'SANCTUARY']:
    nn, aa = eacc[nm]; print(f"  {nm:10s} n={nn:4d} acc={aa*100:4.1f}%")
print(f"  DRIFT up-rate = {drift*100:.1f}%   CONVERGENCE (>=2 unanimous) n={conv_n} acc={conv_acc*100:.1f}%")
print(f"\nStage 5 — decision LB>0.50 (no drift): acted {len(acted)}/{total}  ->  COVERAGE = {coverage*100:.1f}%")
print(f"Stage 6 — ledger (net 5bps, non-overlap H={H}): {len(x)} blocks, total {eqv[-1]:.2f}x")
print(f"   FIRING  ({firing_years:4.1f} in-market yrs): CAGR {eqv[-1]**(1/firing_years)-1 if firing_years>0 else float('nan'):6.2%}  Sortino {sortino_f:.2f}")
print(f"   CALENDAR({cal_years:4.1f} yrs)            : CAGR {eqv[-1]**(1/cal_years)-1 if cal_years>0 else float('nan'):6.2%}")

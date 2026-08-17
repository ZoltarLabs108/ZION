"""
hyperion_ng.py — HYPERION leg: EIA weekly natgas STORAGE as a real driver for weekly NG.

Storage: ir.eia.gov/ngs/ngshistory.xls (no API key), weekly Total Lower 48, 2010+.
PIT: the report for week-ending W is released the following Thursday -> at a Friday decision the
latest known week is W-1: series shifted +1 week on the W-FRI grid. Feature = seasonal deviation
z (level vs trailing same-week-of-year mean/std, past-only), embedded as a pseudo-level
NG_Storage_Level = 100 + cumsum(z_clipped) — the exact IP_Nowcast construction the silver micro
validated — so the cascade's dabs(N) recovers N-week storage-tightness momentum.

PRE-DECLARED candidates (frozen, no additions): ('VIX_Close','NG_Storage_Level'),
('NG_Storage_Level','Dollar_Index'), control ('Fed_Funds_Rate','GS10_Rate'). Stage-1 val-winner
becomes the RED DAWN lens (wf.NUM/DEN), then the standard 3-lens -> LB>0.50 decision -> 5bps ledger.
Honest caveats: storage history 2010+ (feature valid ~2013+ with seasonal warm-up); short-history
Wilson is harsh; a null here = "no storage edge through THIS machinery", not "no NG edge ever".
"""
import os, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
XLS = '/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/30282cd4-7b33-4f1b-a96e-f4101c00d0e5/scratchpad/ngshistory.xls'


def _l(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py'); wf = _l('wf', 'weekly_full_spy.py')
ps = _l('ps', 'predictor_search.py'); eng = _l('eng', 'weekly_reddawn_spy.py'); wlb_eff = eng.wlb_eff
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('2005-01-01')].reset_index(drop=True)

# ---- storage series ----
raw = pd.read_excel(XLS, header=5)
raw = raw.rename(columns={raw.columns[0]: 'week', raw.columns[-1]: 'total'})
raw['week'] = pd.to_datetime(raw['week'], errors='coerce')
raw = raw.dropna(subset=['week']); raw['total'] = pd.to_numeric(raw['total'], errors='coerce')
sto = raw.set_index('week')['total'].dropna().sort_index()
print(f'storage: {len(sto)} wks {sto.index.min().date()}..{sto.index.max().date()}  latest {sto.iloc[-1]:.0f} Bcf')
# seasonal z, past-only: for each week use same-week-of-year values from PRIOR years
woy = sto.index.isocalendar().week.astype(int).to_numpy(); vals = sto.to_numpy(float)
z = np.full(len(sto), np.nan)
for i in range(len(sto)):
    past = [vals[j] for j in range(i) if abs(int(woy[j]) - int(woy[i])) <= 1 and (sto.index[i] - sto.index[j]).days > 90]
    if len(past) >= 8:
        m, s = np.mean(past), np.std(past)
        if s > 0: z[i] = (vals[i] - m) / s
zc = pd.Series(np.clip(z, -3, 3), index=sto.index)
lvl = 100.0 + zc.fillna(0).cumsum()
lvl_pit = lvl.copy(); lvl_pit.index = lvl_pit.index + pd.Timedelta(days=7)     # released next Thursday -> known at W+1 Friday
panel = base.copy()
panel['NG_Storage_Level'] = lvl_pit.reindex(panel['Date'], method='nearest', tolerance=pd.Timedelta('4D')).values
ngpx = zw.yahoo_weekly('NG%3DF')
if isinstance(ngpx, pd.DataFrame): ngpx = ngpx['Close'] if 'Close' in ngpx.columns else ngpx.iloc[:, 0]
ngpx.index = pd.to_datetime(ngpx.index)
panel['SP_Price'] = ngpx.reindex(panel['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values
panel = panel[np.isfinite(panel['SP_Price'])].reset_index(drop=True)
pd.DataFrame({'Date': panel['Date'], 'storage_level_idx': panel['NG_Storage_Level']}).to_csv(
    os.path.join(REP, 'hyperion_ng_storage.csv'), index=False)

sp = panel['SP_Price'].to_numpy(float); dts = panel['Date'].to_numpy(); cpi = panel['US_CPI'].to_numpy(float)
CANDS = [('VIX/StorageIdx', 'VIX_Close', 'NG_Storage_Level'),
         ('StorageIdx/Dollar', 'NG_Storage_Level', 'Dollar_Index'),
         ('FedFunds/GS10 (control)', 'Fed_Funds_Rate', 'GS10_Rate')]
res = [ps.evaluate(panel, sp, dts, nm, nc, dc, set(), cpi) for nm, nc, dc in CANDS]
ok = [r for r in res if r.get('status') == 'ok']
print('\nStage 1 — declared candidates:')
for r in sorted(ok, key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True):
    print(f"  {r['name']:24s} N={r['N']:>2} H={r['H']:>2} n_rel={r['n_reliable']} cov={r['coverage']*100:4.1f}% "
          f"bacc={r['blended_acc']*100:4.1f}% qualified={r.get('qualified')}")
qual = sorted([r for r in ok if r.get('qualified')], key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True)
winner = qual[0] if qual else (sorted(ok, key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True)[0] if ok else None)
if winner is None:
    print('\nno evaluable candidate — ABSTAIN'); raise SystemExit
wnm = winner['name']; wpair = next((nc, dc) for nm, nc, dc in CANDS if nm == wnm)
H = int(winner['H'])
wf.NUM, wf.DEN, wf.H = wpair[0], wpair[1], H
rd, ret, lab, okm = wf.red_dawn(sp, dts, cpi, panel)
od = wf.odyssey(sp, dts, ret, lab); sc, _ = wf.sanctuary(sp, dts, ret, lab)
weeks = sorted(set(rd) & set(od) & set(sc))
dec = {}
for t in weeks:
    pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
    dec[t] = pres[0] if (len(pres) >= 2 and len(set(pres)) == 1) else 0
conv = [(t, dec[t]) for t in weeks if dec[t] != 0 and np.isfinite(lab[t]) and lab[t] != 0]
drift = float(np.mean([lab[t] > 0 for t in weeks if np.isfinite(lab[t]) and lab[t] != 0])) if weeks else float('nan')
cacc = float(np.mean([int(d == lab[t]) for t, d in conv])) if conv else float('nan')
acted = []; k = n = 0
for t in weeks:
    c = dec[t]
    if c != 0 and np.isfinite(lab[t]) and lab[t] != 0:
        if n >= 12 and wlb_eff(k, n, H) > 0.50: acted.append((t, c))
        k += int(c == lab[t]); n += 1
retH = np.full(len(sp), np.nan); retH[:len(sp) - H] = sp[H:] / sp[:len(sp) - H] - 1.0
blocks = []; last = -10**9
for t, c in sorted(acted):
    if t - last >= H and np.isfinite(retH[t]): blocks.append(c * retH[t] - 5 / 1e4); last = t
x = np.array(blocks)
print(f"\nStage 4/5 — RD lens = {wnm} @ H={H}wk: scored {len(weeks)} wks  DRIFT {drift*100:.1f}%  "
      f"CONV {cacc*100:.1f}% (n={len(conv)})")
print(f"decision LB>0.50: acted {len(acted)}/{len(conv)} -> COVERAGE {len(acted)/max(len(conv),1)*100:.1f}%")
if len(x):
    eqv = float(np.cumprod(1 + x)[-1]); fy = len(x) * H / 52.0
    dn = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
    print(f"ledger: {len(x)} blocks {eqv:.2f}x | FIRING CAGR {eqv**(1/fy)-1 if fy>0 else float('nan'):.2%} "
          f"Sortino {float(np.mean(x)/dn*np.sqrt(52/H)) if dn>0 else float('nan'):.2f}")
else:
    print('ledger: 0 blocks — ABSTAIN (honest null: no storage edge through this machinery)')

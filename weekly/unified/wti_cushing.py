"""
wti_cushing.py — WTI x Cushing storage: the petroleum analog of the HYPERION NG build (operator
2026-08-17). No-key EIA route (dnav hist_xls W_EPC0_SAX_YCUOK_MBBLw), weekly 2004+.

HONEST PRIOR (stated before results): the WTI monthly prereg verdict (2026-08-09) found
backwardation+Cushing REJECTED/NULL as monthly predictors — expectation here is REJECT/ABSTAIN.
The episodic (micro) form is a different question than monthly direction; that's why we test.

Construction IDENTICAL to the NG build (template fidelity, nothing tuned): seasonal same-week z
(past-only, +/-1 week, >=8 prior obs), clipped +/-3, pseudo-level 100+cumsum(z) (IP_Nowcast style);
PIT: WPSR releases Wednesday for week-ending prior Friday -> series shifted +7d on the W-FRI grid.

Tests (both pre-declared):
  A. Pipeline: Stage-1 evaluate over {(VIX,CushIdx),(CushIdx,Dollar),(FedFunds/GS10 control)};
     winner -> RD lens -> 3-lens conv -> LB>0.50 decision -> 5bps ledger.
  B. Micro screen: same 3 pairs on the frozen N8/H4 episodic template, gates G1-G4 vs locked book.
Null is final on both.
"""
import os, math, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
XLS = '/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/30282cd4-7b33-4f1b-a96e-f4101c00d0e5/scratchpad/cushing.xls'
COST = 5 / 1e4; N_TPL, H_TPL = 8, 4


def _l(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py'); wf = _l('wf', 'weekly_full_spy.py')
ps = _l('ps', 'predictor_search.py'); eng = _l('eng', 'weekly_reddawn_spy.py'); wlb_eff = eng.wlb_eff


def wilson_lb(k, n, z=1.96):
    if n <= 0: return 0.0
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return (c - m) / d


def sortino(r):
    r = np.asarray(r, float); dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
    return float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else float('nan')


spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('2004-01-01')].reset_index(drop=True)

# ---- Cushing feature (identical construction to NG) ----
raw = pd.read_excel(XLS, sheet_name='Data 1', header=2)
raw.columns = ['week', 'stocks']; raw['week'] = pd.to_datetime(raw['week'])
sto = raw.set_index('week')['stocks'].dropna().sort_index()
print(f'Cushing: {len(sto)} wks {sto.index.min().date()}..{sto.index.max().date()}  latest {sto.iloc[-1]/1000:.1f} MMbbl')
woy = sto.index.isocalendar().week.astype(int).to_numpy(); vals = sto.to_numpy(float)
z = np.full(len(sto), np.nan)
for i in range(len(sto)):
    past = [vals[j] for j in range(i) if abs(int(woy[j]) - int(woy[i])) <= 1 and (sto.index[i] - sto.index[j]).days > 90]
    if len(past) >= 8:
        m, s = np.mean(past), np.std(past)
        if s > 0: z[i] = (vals[i] - m) / s
zc = pd.Series(np.clip(z, -3, 3), index=sto.index)
lvl = 100.0 + zc.fillna(0).cumsum(); lvl.index = lvl.index + pd.Timedelta(days=7)   # PIT shift
P = base[['Date', 'VIX_Close', 'Dollar_Index', 'Fed_Funds_Rate', 'GS10_Rate', 'US_CPI']].copy()
P['Cushing_Level'] = lvl.reindex(P['Date'], method='nearest', tolerance=pd.Timedelta('4D')).values
wti = zw.yahoo_weekly('CL%3DF')
if isinstance(wti, pd.DataFrame): wti = wti['Close'] if 'Close' in wti.columns else wti.iloc[:, 0]
wti.index = pd.to_datetime(wti.index)
P['SP_Price'] = wti.reindex(P['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values
P['TARGET'] = P['SP_Price']
P = P[np.isfinite(P['SP_Price'])].reset_index(drop=True)
pd.DataFrame({'Date': P['Date'], 'cushing_level_idx': P['Cushing_Level']}).to_csv(
    os.path.join(REP, 'wti_cushing_storage.csv'), index=False)

sp = P['SP_Price'].to_numpy(float); dts = P['Date'].to_numpy(); cpi = P['US_CPI'].to_numpy(float)
CANDS = [('VIX/CushingIdx', 'VIX_Close', 'Cushing_Level'),
         ('CushingIdx/Dollar', 'Cushing_Level', 'Dollar_Index'),
         ('FedFunds/GS10 (control)', 'Fed_Funds_Rate', 'GS10_Rate')]

# ---- A. pipeline ----
res = [ps.evaluate(P, sp, dts, nm, nc, dc, set(), cpi) for nm, nc, dc in CANDS]
ok = [r for r in res if r.get('status') == 'ok']
print('\nA. Stage 1 — declared candidates:')
for r in sorted(ok, key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True):
    print(f"  {r['name']:24s} N={r['N']:>2} H={r['H']:>2} n_rel={r['n_reliable']} cov={r['coverage']*100:4.1f}% "
          f"bacc={r['blended_acc']*100:4.1f}% qualified={r.get('qualified')}")
qual = sorted([r for r in ok if r.get('qualified')], key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True)
winner = qual[0] if qual else (sorted(ok, key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True)[0] if ok else None)
if winner is not None:
    wnm = winner['name']; wpair = next((nc, dc) for nm, nc, dc in CANDS if nm == wnm)
    H = int(winner['H']); wf.NUM, wf.DEN, wf.H = wpair[0], wpair[1], H
    rd, ret, lab, okm = wf.red_dawn(sp, dts, cpi, P)
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
    print(f"   RD lens={wnm} H={H}: scored {len(weeks)}  DRIFT {drift*100:.1f}%  CONV {cacc*100:.1f}% (n={len(conv)})  "
          f"gate acted {len(acted)}/{len(conv)} -> COVERAGE {len(acted)/max(len(conv),1)*100:.1f}%")

# ---- B. micro screen ----
lk = pd.read_csv(os.path.join(REP, 'locked_book.csv')); lk['Date'] = pd.to_datetime(lk['Date'])
cal = pd.DatetimeIndex(lk['Date']); locked = lk['locked'].to_numpy(float); s0 = sortino(locked)
print(f"\nB. MICRO SCREEN — frozen N={N_TPL}/H={H_TPL}, gates G1-G4:")
print(f"{'cell':26s} {'n':>4} {'acc':>6} {'LB':>5} {'yrs':>4} {'maxYr':>6} {'%long':>6} {'corr':>6} {'dSort':>7}  gates")
for nm, num, den in CANDS:
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
    print(f"{nm:26s} {len(fires):>4} {acc*100:>5.1f}% {lb:>5.2f} {nyr:>4} "
          f"{maxyr*100 if np.isfinite(maxyr) else float('nan'):>5.0f}% "
          f"{plong*100 if np.isfinite(plong) else float('nan'):>5.0f}% {corr:>+6.2f} {ds:>+7.3f}  [{gates}] {verdict}")
print("\nnull is final on both tests. Any PASS = PROVISIONAL (forward tape).")

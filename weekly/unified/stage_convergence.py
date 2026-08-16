"""
stage_convergence.py — REAL Stage 1 (RED DAWN type-vote) + Stage 4 (3-lens convergence) for SPY,
run AT THE SWEPT HORIZON (not the hardcoded H=3). Reuses weekly_full_spy.py's engines.

HONEST NOTE surfaced here and by the auditor: weekly_full_spy's RED DAWN is a SINGLE-PREDICTOR
(VIX/Dollar) 27-type majority vote — a SUBSET of the mandated recursive cascade (train-floor +
val-winner, multi-round refit). Stage 4 (the 3-lens ≥2-unanimous convergence) IS faithful. So this
step makes the convergence real and gives the honest OOS number, while the audit flags that the full
recursive Stage-1 cascade is still to build at weekly.
"""
import os, importlib.util
import numpy as np, pandas as pd

WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'


def _load(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


wf = _load('wf', 'weekly_full_spy.py')


def run(frozen_H, repdir):
    wf.H = int(frozen_H)                       # <-- run engines at the SWEPT horizon
    df = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); df['Date'] = pd.to_datetime(df['Date'])
    sp = df['SP_Price'].to_numpy(float); dts = df['Date'].to_numpy(); cpi = df['US_CPI'].to_numpy(float)
    rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, df)
    od = wf.odyssey(sp, dts, ret, lab)
    sc, band = wf.sanctuary(sp, dts, ret, lab)
    weeks = sorted(set(rd) & set(od) & set(sc))

    def acc(dm):
        s = [(t, dm[t]) for t in weeks if dm[t] != 0 and np.isfinite(lab[t]) and lab[t] != 0]
        return (len(s), (float(np.mean([int(dr == lab[t]) for t, dr in s])) if s else float('nan')))

    stats = {nm: acc(dm) for nm, dm in [('RED DAWN', rd), ('ODYSSEY', od), ('SANCTUARY', sc)]}
    dec = {}
    for t in weeks:
        pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
        dec[t] = (pres[0], len(pres)) if (len(pres) >= 2 and len(set(pres)) == 1) else (0, len(pres))

    def dacc(kfilter=None):
        s = [(t, dec[t][0]) for t in weeks if dec[t][0] != 0 and (kfilter is None or dec[t][1] == kfilter)
             and np.isfinite(lab[t]) and lab[t] != 0]
        return (len(s), (float(np.mean([int(d == lab[t]) for t, d in s])) if s else float('nan')))

    stats['CONV_unanimous'] = dacc(); stats['CONV_strength3'] = dacc(3); stats['CONV_strength2'] = dacc(2)
    # drift baseline on the same scored weeks (what convergence must beat)
    lb = np.array([lab[t] for t in weeks if np.isfinite(lab[t]) and lab[t] != 0])
    stats['DRIFT_uprate'] = (len(lb), float((lb > 0).mean()) if len(lb) else float('nan'))

    rd_art = os.path.join(repdir, 'SPY_rd_stream.csv')
    pd.DataFrame([dict(t=t, date=str(dts[t])[:10], rd=rd[t]) for t in weeks]).to_csv(rd_art, index=False)
    conv_art = os.path.join(repdir, 'SPY_conv_stream.csv')
    pd.DataFrame([dict(t=t, date=str(dts[t])[:10], rd=rd[t], od=od[t], sc=sc[t],
                       conv=dec[t][0], strength=dec[t][1],
                       lab=(int(lab[t]) if np.isfinite(lab[t]) else 0)) for t in weeks]).to_csv(conv_art, index=False)
    return dict(stats=stats, weeks=len(weeks), rd_art=rd_art, conv_art=conv_art, H=int(frozen_H))


if __name__ == '__main__':
    rep = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports'); os.makedirs(rep, exist_ok=True)
    r = run(2, rep)
    print(f"SPY 3-lens convergence @ H={r['H']}wk — scored weeks={r['weeks']}\n")
    for k in ['RED DAWN', 'ODYSSEY', 'SANCTUARY', 'DRIFT_uprate', 'CONV_unanimous', 'CONV_strength3', 'CONV_strength2']:
        n, a = r['stats'][k]
        print(f"  {k:16s}  n={n:5d}  acc/rate={a*100:5.1f}%" if not np.isnan(a) else f"  {k:16s}  n={n:5d}  --")

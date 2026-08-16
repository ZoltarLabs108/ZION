"""
stage_cascade.py — REAL Stage 1: val-winner predictor selection (upgrades the single-hardcoded
VIX/Dollar type-vote to the mandated 'train-floor + val-winner'). Reuses predictor_search.evaluate:
freeze N on the design split, sweep H, accept on validation Wilson-LB (overlap+staleness eff-n),
rank qualified by (n_reliable, coverage*blended_acc); winner = top of the validation ranking.
"""
import os, importlib.util, json
import numpy as np, pandas as pd

WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'


def _load(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


ps = _load('ps2', 'predictor_search.py')
NATIVE = [('VIX/Dollar', 'VIX_Close', 'Dollar_Index'),
          ('VIX/SP', 'VIX_Close', 'SP_Price'),
          ('Gold/Dollar', 'Gold_Close', 'Dollar_Index'),
          ('Copper/Dollar', 'Copper_Close', 'Dollar_Index')]


def run(repdir):
    df = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); df['Date'] = pd.to_datetime(df['Date'])
    sp = df['SP_Price'].to_numpy(float); dts = df['Date'].to_numpy(); cpi = df['US_CPI'].to_numpy(float)
    monthly_ff = set()                                       # NATIVE candidates are all weekly-native (stale=1.0)
    res = []
    for name, nc, dc in NATIVE:
        r = ps.evaluate(df, sp, dts, name, nc, dc, monthly_ff, cpi)
        if r.get('status') == 'ok':
            res.append(r)
    qual = [r for r in res if r.get('qualified')]
    qual.sort(key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True)
    winner = qual[0] if qual else (sorted(res, key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']),
                                          reverse=True)[0] if res else None)
    art = os.path.join(repdir, 'SPY_cascade_valwinner.csv')
    pd.DataFrame(res).to_csv(art, index=False)
    return winner, res, art


if __name__ == '__main__':
    rep = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports'); os.makedirs(rep, exist_ok=True)
    w, res, art = run(rep)
    print("VAL-WINNER SELECTION (Stage 1) — qualified ranking:")
    for r in sorted(res, key=lambda r: (r['n_reliable'], r['coverage'] * r['blended_acc']), reverse=True):
        print(f"  {r['name']:14s} N={r['N']:>2} H={r['H']:>2} n_rel={r['n_reliable']} "
              f"cov={r['coverage']*100:4.1f}% bacc={r['blended_acc']*100:4.1f}% n={r['n_scored']} "
              f"qualified={r.get('qualified')}")
    print(f"\nWINNER = {w['name'] if w else None}  (H={w['H'] if w else '-'})")

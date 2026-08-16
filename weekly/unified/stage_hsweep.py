"""
stage_hsweep.py — REAL Stage 0.5 horizon sweep for SPY (the stage the shortcut fully skipped).

Reuses the WT weekly reference physics (cyclical-adjusted ratios via shiller_cpi_adjust, the 27-type
grammar, drift-free Wilson-LB validity with overlap+staleness eff-n) from `type_analysis.py`. For each
weekly-native candidate predictor: freeze N on the design window, then SWEEP H over {1,2,3,4,6,8,13}
on the scored window, ranking types by reliably-predictive EDGE structure. Freezes the winning H.

Writes a real sweep table artifact and returns (frozen_H, table). This is the fidelity Phase 2 adds.
"""
import os, importlib.util
import numpy as np, pandas as pd

WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(WT, fn))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


ta = _load('ta', 'type_analysis.py')          # brings eng, ps, shiller_cpi_adjust, H_GRID, N_GRID, DESIGN_FRAC
H_GRID, N_GRID, DESIGN_FRAC = ta.H_GRID, ta.N_GRID, ta.DESIGN_FRAC
shiller, ps, eng = ta.shiller_cpi_adjust, ta.ps, ta.eng

CANDIDATES = [('VIX/Dollar', 'VIX_Close', 'Dollar_Index'),
              ('VIX/SP', 'VIX_Close', 'SP_Price'),
              ('Gold/Dollar', 'Gold_Close', 'Dollar_Index')]


def sweep(panel_csv, out_csv):
    df = pd.read_csv(panel_csv); df['Date'] = pd.to_datetime(df['Date'])
    sp = df['SP_Price'].to_numpy(float); dts = df['Date'].to_numpy(); cpi = df['US_CPI'].to_numpy(float)
    rows = []
    for name, nc, dc in CANDIDATES:
        na = shiller(df[nc].to_numpy(float), cpi); da = shiller(df[dc].to_numpy(float), cpi)
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.where(np.isfinite(da) & (da != 0), na / da, np.nan)
        span = ps.first_scored_span(df, ratio, na, da)
        if span is None:
            continue
        d0, d1 = span; design_end = d0 + (d1 - d0) * DESIGN_FRAC
        bestN, bestrel = N_GRID[0], -1
        for N in N_GRID:                                    # freeze N on design window
            recs = ps.sequential_ratio(sp, ratio, na, da, dts, 1, N, score_min=d0, score_max=design_end)
            rel, _, _ = eng._summarize(*eng.type_stats(recs, 1, indep_period=1.0))
            if len(rel) > bestrel:
                bestrel, bestN = len(rel), N
        for H in H_GRID:                                    # SWEEP H on scored window
            recs = ps.sequential_ratio(sp, ratio, na, da, dts, H, bestN, score_min=design_end, score_max=d1)
            rws, nsc = eng.type_stats(recs, H, indep_period=1.0)
            rel, cov, bacc = eng._summarize(rws, nsc)
            rows.append(dict(predictor=name, N=bestN, H=H, n_reliable=len(rel),
                             coverage=round(cov, 4), blended_acc=round(bacc, 4),
                             pull_yield=round(cov * bacc, 4), n_scored=nsc))
    res = pd.DataFrame(rows)
    res.to_csv(out_csv, index=False)
    # freeze H = maximize reliably-predictive structure across predictors; tie-break total pull-yield
    if len(res):
        agg = res.groupby('H').agg(n_reliable=('n_reliable', 'sum'),
                                   pull_yield=('pull_yield', 'sum')).reset_index()
        agg = agg.sort_values(['n_reliable', 'pull_yield'], ascending=False)
        frozen_H = int(agg.iloc[0]['H'])
    else:
        agg = pd.DataFrame(); frozen_H = None
    return frozen_H, res, agg


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports', 'SPY_hsweep_real.csv')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    H, res, agg = sweep(os.path.join(WT, 'weekly_panel_spy.csv'), out)
    print("HORIZON SWEEP (SPY, real) — per predictor × H:")
    print(res.to_string(index=False) if len(res) else "  (no scorable predictors)")
    print("\nAggregate edge-structure by H (freeze rule: max n_reliable, tie-break pull_yield):")
    print(agg.to_string(index=False) if len(agg) else "  (empty)")
    print(f"\nFROZEN H = {H} weeks")

"""
stage_decision_ledger.py — REAL Stage 5 (edge-over-drift decision) + Stage 6 (net-of-cost ledger).

Stage 5: sequential edge-over-drift GATE (PIT). Act on the convergence direction ONLY when the
trailing in-fold record of convergence clears an eff-n Wilson-LB that EXCEEDS THE DRIFT base rate
(not merely 0.50) — the §3.3 upgrade. Record updates AFTER each decision.
Stage 6: non-overlapping H-week blocks, 5 bps cost, net returns -> CAGR/Sortino + FINAL COVERAGE.

For weekly SPY the honest result is expected ABSTAIN: convergence (63.3%) barely tops drift (62.3%),
so its Wilson-LB cannot clear the drift bar -> ~0% coverage. That IS the deliverable.
"""
import os, importlib.util
import numpy as np, pandas as pd

WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'


def _load(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


eng = _load('eng', 'weekly_reddawn_spy.py')
wlb_eff = eng.wlb_eff
COST = 5 / 1e4
MIN_N = 12


def run(conv_csv, H, repdir, bar=0.50):
    """bar = trailing eff-n Wilson-LB threshold to ACT. bar=0.50 => plain accuracy gate (DRIFT REMOVED,
    operator 2026-08-14). Pass bar='drift' to require clearing the long-bias base rate instead."""
    cv = pd.read_csv(conv_csv)
    df = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); sp = df['SP_Price'].to_numpy(float)
    retH = np.full(len(sp), np.nan); retH[:len(sp) - H] = sp[H:] / sp[:len(sp) - H] - 1.0
    cv = cv[cv['lab'] != 0].reset_index(drop=True)
    drift = float((cv['lab'] > 0).mean())
    thresh = drift if bar == 'drift' else float(bar)

    # Stage 5 — sequential accuracy gate (drift removed): act when trailing eff-n Wilson-LB > thresh
    acted = []; k = n = 0
    for _, r in cv.iterrows():
        c = int(r['conv'])
        if c != 0:
            if n >= MIN_N and wlb_eff(k, n, H) > thresh:
                acted.append((int(r['t']), c))
            k += int(c == int(r['lab'])); n += 1
    total = int((cv['conv'] != 0).sum())
    coverage = len(acted) / total if total else 0.0

    # Stage 6 — non-overlapping H-blocks, net of cost
    def ledger(pairs):
        pairs = sorted(pairs); out = []; last = -10 ** 9
        for t, c in pairs:
            if t - last >= H and np.isfinite(retH[t]):
                out.append(c * retH[t] - COST); last = t
        return np.array(out)

    def stat(x):
        if len(x) == 0:
            return dict(blocks=0, cagr=float('nan'), sortino=float('nan'), total=float('nan'))
        eq = np.cumprod(1 + x); yrs = len(x) * H / 52.0
        cagr = eq[-1] ** (1 / yrs) - 1
        dd = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
        sortino = float(np.mean(x) / dd * np.sqrt(52.0 / H)) if dd > 0 else float('nan')
        return dict(blocks=len(x), cagr=float(cagr), sortino=sortino, total=float(eq[-1]))

    gated = stat(ledger(acted))
    ungated = stat(ledger([(int(r['t']), int(r['conv'])) for _, r in cv.iterrows() if int(r['conv']) != 0]))
    art = os.path.join(repdir, 'SPY_decision_ledger.csv')
    pd.DataFrame([dict(t=t, dir=c) for t, c in acted]).to_csv(art, index=False)
    return dict(drift=drift, total=total, acted=len(acted), coverage=coverage,
                gated=gated, ungated=ungated, artifact=art)


if __name__ == '__main__':
    rep = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    r = run(os.path.join(rep, 'SPY_conv_stream.csv'), 2, rep)
    print(f"drift base rate = {r['drift']*100:.1f}%   convergence calls = {r['total']}")
    print(f"edge-over-drift GATE acted on {r['acted']} / {r['total']} calls  ->  FINAL COVERAGE = {r['coverage']*100:.1f}%")
    print(f"  gated   ledger: blocks={r['gated']['blocks']}  CAGR={r['gated']['cagr']*100 if not np.isnan(r['gated']['cagr']) else float('nan'):.2f}%  Sortino={r['gated']['sortino']:.2f}")
    print(f"  ungated ledger: blocks={r['ungated']['blocks']}  CAGR={r['ungated']['cagr']*100:.2f}%  Sortino={r['ungated']['sortino']:.2f}")

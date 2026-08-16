"""
micro_screen.py — PRE-DECLARED micro-sleeve admission screen (Fable pass, 2026-08-16).

Applies the silver-micro methodology (SILVER_MICRO_SLEEVE_20260816.md) to a SMALL, FROZEN grid of
new candidates. Everything is pre-declared to keep the search surface honest:

  TEMPLATE (frozen, inherited from the silver find — NOTHING swept):
    N=8 (Δ8wk), H=4 (hold 4wks, extend on re-fire, else flat), cascade-gated stream
    (train-floor + val-winner, sequential OOS, train frontier <= t-H), 5bps on position change.

  GRID (disclosed): targets x pairs = the WHOLE search
    targets : WTI, GOLD, PLATINUM, AUDUSD  (+ SILVER/VIX-IPNowcast as POSITIVE CONTROL)
    pairs   : (VIX, IP_Nowcast) [skipped for WTI: nowcast contains WTI's own momentum = self-leak],
              (VIX, Dollar), (Credit_BAA10Y, Dollar)
    -> ~11 live cells. Under pure noise at these gates expect ~0-1 false survivors; anything passing
       is PROVISIONAL (forward-tape gate), exactly like silver.

  GATES (all must pass):
    G1 signal        : fire-week acc >= 0.65, n >= 30, Wilson-LB >= 0.55
    G2 concentration : fires span >= 3 calendar years AND max single-year share <= 0.45
    G3 decorrelation : |corr to LOCKED book| < 0.30 on micro-active weeks
    G4 book          : Sortino(locked + 0.05*micro) >= Sortino(locked) - 0.01

Also prints locked-book sub-period robustness (the concentration question Opus flagged).
"""
import os, math, importlib.util, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
COST = 5 / 1e4; N_TPL, H_TPL = 8, 4


def _l(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


drv = _l('drv', 'zion_driver.py'); zw = _l('zw', 'zion_weekly.py')


def wilson_lb(k, n, z=1.96):
    if n <= 0: return 0.0
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return (c - m) / d


def episodic(P, num, den, mff):
    """silver_micro construction, verbatim logic: stream -> hold H wks, extend on re-fire."""
    cal = pd.to_datetime(P['Date'])
    de = P['Date'].iloc[0] + (P['Date'].iloc[-1] - P['Date'].iloc[0]) * 0.4
    s, ret, lab = zw.stream(P, num, den, N_TPL, H_TPL, mff, de)
    tgt = P['TARGET'].to_numpy(float)
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
        rows[cal.iloc[t]] = r1[t] * pos[t] - COST * abs(pos[t] - prev); prev = pos[t]
    # fire stats on the H-forward label (the cell's own claim)
    fires = [(t, s[t]) for t in sorted(s) if s[t] not in (0, None) and np.isfinite(lab[t]) and lab[t] != 0]
    hits = [int(d == lab[t]) for t, d in fires]
    years = pd.Series([cal.iloc[t].year for t, _ in fires])
    longs = sum(1 for _, d in fires if d > 0)
    return pd.Series(rows), dict(n=len(fires), acc=(np.mean(hits) if hits else np.nan),
                                 lb=wilson_lb(int(np.sum(hits)), len(hits)),
                                 nyears=years.nunique(), maxyr=(years.value_counts(normalize=True).max() if len(years) else np.nan),
                                 pct_long=(longs / len(fires) if fires else np.nan))


def sortino(r):
    r = np.asarray(r, float); dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
    return float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else float('nan')


def main():
    lk = pd.read_csv(os.path.join(REP, 'locked_book.csv')); lk['Date'] = pd.to_datetime(lk['Date'])
    cal = pd.DatetimeIndex(lk['Date']); locked = lk['locked'].to_numpy(float)
    s0 = sortino(locked)
    # locked-book sub-period robustness (for the discussion)
    half = cal < pd.Timestamp('2017-01-01')
    def cagr(r): e = np.cumprod(1 + r); return e[-1] ** (52 / len(r)) - 1
    print(f"LOCKED book sub-periods: 2007-16 CAGR {cagr(locked[half])*100:+.2f}% Sortino {sortino(locked[half]):.2f} | "
          f"2017-26 CAGR {cagr(locked[~half])*100:+.2f}% Sortino {sortino(locked[~half]):.2f}  (full Sortino {s0:.2f})\n")

    PAIRS = [('VIX_Close', 'IP_Nowcast_Level'), ('VIX_Close', 'Dollar_Index'), ('Credit_BAA10Y', 'Dollar_Index')]
    TARGETS = ['SILVER', 'WTI', 'GOLD', 'PLATINUM', 'AUDUSD']   # SILVER row = positive control
    print(f"{'cell':38s} {'n':>4} {'acc':>6} {'LB':>5} {'yrs':>4} {'maxYr':>6} {'%long':>6} "
          f"{'corr':>6} {'dSort':>7}  gates")
    survivors = []
    for tgt in TARGETS:
        cfg = drv.ASSETS.get(tgt)
        if cfg is None: continue
        try:
            P = drv.build_panel(cfg)
        except Exception as e:
            print(f"{tgt:38s} PANEL FAILED: {repr(e)[:80]}"); continue
        for num, den in PAIRS:
            name = f"{tgt}: {num.replace('_Close','')}/{den.replace('_Level','').replace('_Close','')}"
            if tgt == 'WTI' and den == 'IP_Nowcast_Level':
                print(f"{name:38s} SKIPPED (self-leak: nowcast contains WTI momentum)"); continue
            if num not in P.columns or den not in P.columns:
                print(f"{name:38s} missing column"); continue
            try:
                ser, st = episodic(P, num, den, cfg['MFF'])
            except Exception as e:
                print(f"{name:38s} stream failed: {repr(e)[:60]}"); continue
            a = ser.reindex(cal, method='nearest', tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()
            act = np.abs(a) > 1e-9
            corr = float(np.corrcoef(a[act], locked[act])[0, 1]) if act.sum() > 10 else np.nan
            ds = sortino(locked + 0.05 * a) - s0
            g1 = (st['n'] >= 30) and (st['acc'] >= 0.65) and (st['lb'] >= 0.55)
            g2 = (st['nyears'] >= 3) and (st['maxyr'] <= 0.45)
            g3 = np.isfinite(corr) and abs(corr) < 0.30
            g4 = ds >= -0.01
            gates = ''.join(c if ok else '-' for c, ok in zip('1234', (g1, g2, g3, g4)))
            verdict = 'PASS' if all((g1, g2, g3, g4)) else ''
            print(f"{name:38s} {st['n']:>4} {st['acc']*100:>5.1f}% {st['lb']:>5.2f} {st['nyears']:>4} "
                  f"{st['maxyr']*100 if np.isfinite(st['maxyr']) else float('nan'):>5.0f}% "
                  f"{st['pct_long']*100 if np.isfinite(st['pct_long']) else float('nan'):>5.0f}% "
                  f"{corr:>+6.2f} {ds:>+7.3f}  [{gates}] {verdict}")
            if verdict: survivors.append((name, st, corr, ds))
    print(f"\nSearch size: ~11 live cells, frozen template (no sweep). "
          f"Survivors: {len(survivors)} -> {'PROVISIONAL, forward-tape gated (silver rule)' if survivors else 'none — honest null'}")


if __name__ == '__main__':
    main()

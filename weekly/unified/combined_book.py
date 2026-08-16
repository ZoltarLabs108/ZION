"""
combined_book.py — SPY + QQQ + Gold into ONE weekly book; report combined coverage/Sortino/Calmar.
Each sleeve: unified weekly system (sweep -> 3-lens convergence -> LB>0.50 decision, NO drift gate),
turned into a WEEKLY-CALENDAR return series (position held over the non-overlapping H-block, 0 in cash
weeks), 5bps cost. Book = equal-weight mean of the 3 sleeves each week (flat sleeve contributes 0).
Calendar basis on 2007+ (the combined-book analysis the operator reserves for the end).
"""
import os, importlib.util
import numpy as np, pandas as pd
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')


def _load(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _load('zw', 'zion_weekly.py'); wf = _load('wf', 'weekly_full_spy.py')
HS = _load('hs', 'stage_hsweep.py', HERE); eng = _load('eng', 'weekly_reddawn_spy.py'); wlb_eff = eng.wlb_eff
spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('1995-01-01')].reset_index(drop=True)   # bound runtime; ample pre-2007 train
SCORE0 = pd.Timestamp('2007-08-01')


def yser(t):
    s = zw.yahoo_weekly(t)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index); return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


def sleeve(name, price):
    """Return weekly-calendar return array (len=len(base)); position held across each non-overlapping
    H-block, 0 in cash weeks. Also returns coverage of scored weeks."""
    panel = base.copy(); panel['SP_Price'] = price
    qpath = os.path.join(REP, f'{name}_bpanel.csv'); panel.to_csv(qpath, index=False)
    sp = np.asarray(price, float); dts = base['Date'].to_numpy(); cpi = base['US_CPI'].to_numpy(float)
    fh, _, _ = HS.sweep(qpath, os.path.join(REP, f'{name}_bsweep.csv')); H = int(fh)
    wf.H = H
    rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, panel); od = wf.odyssey(sp, dts, ret, lab); sc, bnd = wf.sanctuary(sp, dts, ret, lab)
    weeks = sorted(set(rd) & set(od) & set(sc))
    dec = {}
    for t in weeks:
        pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
        dec[t] = pres[0] if (len(pres) >= 2 and len(set(pres)) == 1) else 0
    # decision: trailing eff-n Wilson-LB > 0.50 (no drift)
    acted = []; k = n = 0
    for t in weeks:
        c = dec[t]
        if c != 0 and np.isfinite(lab[t]) and lab[t] != 0:
            if n >= 12 and wlb_eff(k, n, H) > 0.50: acted.append((t, c))
            k += int(c == lab[t]); n += 1
    conv_n = sum(1 for t in weeks if dec[t] != 0 and np.isfinite(lab[t]) and lab[t] != 0)
    # weekly-calendar series: hold each block H weeks
    wret = np.full(len(sp), np.nan); wret[1:] = sp[1:] / sp[:-1] - 1.0
    arr = np.zeros(len(base)); last = -10**9
    for t, c in sorted(acted):
        if t - last >= H:
            for j in range(1, H + 1):
                if t + j < len(base) and np.isfinite(wret[t + j]): arr[t + j] += c * wret[t + j]
            if t + 1 < len(base): arr[t + 1] -= 5 / 1e4
            last = t
    cov = len(acted) / conv_n if conv_n else 0.0
    acc_acted = float(np.mean([int(c == lab[t]) for t, c in acted])) if acted else float('nan')
    return arr, cov, H, len(acted), conv_n, acc_acted


def diag(r, label):
    r = np.asarray(r, float)
    eq = np.cumprod(1 + r); n = len(r)
    cagr = eq[-1] ** (52.0 / n) - 1
    mdd = float((eq / np.maximum.accumulate(eq) - 1).min())
    dd = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2)); sortino = float(np.mean(r) / dd * np.sqrt(52)) if dd > 0 else float('nan')
    calmar = float(cagr / abs(mdd)) if mdd < 0 else float('nan')
    inmkt = float((r != 0).mean())
    return dict(label=label, cagr=cagr, sortino=sortino, calmar=calmar, maxdd=mdd, cov=inmkt, n=n)


# FIX GOLD: real Yahoo weekly (GC=F futures ~2000+) instead of the sparse panel Gold_Close
try:
    gold_px = yser('GC=F'); gold_src = 'GC=F'
    if np.isfinite(gold_px).sum() < 400: raise ValueError('thin')
except Exception:
    gold_px = yser('GLD'); gold_src = 'GLD'

sl = {}; accs = {}
for name, price in [('SPY', base['SP_Price'].to_numpy(float)), ('QQQ', yser('QQQ')), ('Gold', gold_px)]:
    arr, cov, H, na, cn, acc = sleeve(name, price); sl[name] = arr; accs[name] = acc
    print(f"[{name:4s}] H={H}wk  acted {na}/{cn}  decision-coverage {cov*100:.1f}%  gated-acc {acc*100:.1f}%")
print(f"(gold source = {gold_src})")

mask = (base['Date'] >= SCORE0).to_numpy()
S = {k: v[mask] for k, v in sl.items()}
vix = base['VIX_Close'].to_numpy(float)[mask]
M = np.vstack([S['SPY'], S['QQQ'], S['Gold']])
book = np.mean(M, axis=0)
anyact = float((M != 0).any(axis=0).mean())

# ---- DUAL throttle (applied to RISK sleeves only; hedge stays on) ----
import io
def fred(sid):
    raw = zw.fetch(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}')
    d = pd.read_csv(io.BytesIO(raw)); d.columns = ['date', 'val']; d['date'] = pd.to_datetime(d['date'])
    d['val'] = pd.to_numeric(d['val'], errors='coerce'); s = d.set_index('date')['val']
    return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('7D')).ffill().values

def pctl_throttle(series):
    t = np.ones(len(series))
    for w in range(len(series)):
        pri = series[:w]; pri = pri[np.isfinite(pri)]
        if len(pri) >= 50 and np.isfinite(series[w]) and (pri <= series[w]).mean() >= 0.70: t[w] = 0.5
    return t

thr_vix = pctl_throttle(vix)
credit = base['Credit_BAA10Y'].to_numpy(float)[mask]
thr_liq = pctl_throttle(credit)                                   # liquidity/credit-spread stress
thr = thr_vix * thr_liq                                           # BOTH throttles (either stressed -> de-risk)
risk = M * thr                                                    # throttle the 3 risk sleeves

# ---- Treasury pure-hedge leg: sweep 2/5/10/30y (always-on, NOT throttled) ----
DUR = {'2Y': ('DGS2', 1.9), '5Y': ('DGS5', 4.6), '10Y': ('DGS10', 8.0), '30Y': ('DGS30', 18.0)}
tsy = {}
for nm, (sid, dur) in DUR.items():
    try:
        y = fred(sid); carry = y / 100 / 52.0; dy = np.concatenate([[0.0], np.diff(y)]) / 100.0
        tr = carry - dur * dy; tr = np.nan_to_num(tr[mask]); tsy[nm] = tr
    except Exception as e:
        print(f"  {nm} fetch failed: {repr(e)[:80]}")

print("\n" + "=" * 74)
print("SLEEVE diagnostics (weekly-calendar, 2007+):")
for k in ['SPY', 'QQQ', 'Gold']:
    d = diag(S[k], k); print(f"  {k:4s} cov {d['cov']*100:4.1f}% CAGR {d['cagr']*100:5.2f}% Sortino {d['sortino']:.2f} Calmar {d['calmar']:.2f} MaxDD {d['maxdd']*100:.1f}%")
print("=" * 74)


def row(r, label):
    d = diag(r, label)
    inm = float((r != 0).mean())
    return f"  {label:34s} cov {inm*100:5.1f}%  Sortino {d['sortino']:5.2f}  Calmar {d['calmar']:5.2f}  CAGR {d['cagr']*100:5.2f}%  MaxDD {d['maxdd']*100:6.1f}%"


print(f"3-LEG (SPY+QQQ+Gold), risk-sleeve coverage {anyact*100:.1f}%:")
print(row(book, 'no throttle'))
print(row(np.mean(risk, axis=0), 'both throttles (VIX x liquidity)'))
print(f"\n4-LEG (+ Treasury pure hedge, always-on; both throttles on risk sleeves):")
for nm in ['2Y', '5Y', '10Y', '30Y']:
    if nm in tsy:
        book4 = np.mean(np.vstack([risk, tsy[nm]]), axis=0)
        print(row(book4, f'+ {nm} Treasury hedge'))

# ---- WEIGHT SWEEP: hedge weight (2Y) vs risk sleeves sharing remainder ----
t2 = tsy.get('2Y'); rsum = np.sum(risk, axis=0)      # sum of 3 throttled risk sleeves per week
if t2 is not None:
    print(f"\nHEDGE-WEIGHT SWEEP (2Y hedge weight w_h; 3 risk sleeves share (1-w_h)/3 each):")
    best = None
    for wh in [0.0, 0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.70, 0.80]:
        bk = wh * t2 + ((1 - wh) / 3.0) * rsum
        d = diag(bk, f'{wh:.0%}')
        print(row(bk, f'hedge {wh*100:>3.0f}%'))
        if best is None or d['calmar'] > best[1]:
            best = (wh, d['calmar'], d['sortino'])
    print(f"  -> best Calmar at hedge weight {best[0]*100:.0f}%  (Calmar {best[1]:.2f}, Sortino {best[2]:.2f})")
    # risk-parity (inverse 36wk vol) across the 4 legs
    legs = np.vstack([risk, t2]); W = np.zeros_like(legs)
    for w in range(legs.shape[1]):
        lo = max(0, w - 36); v = np.nanstd(legs[:, lo:w + 1], axis=1); v = np.where(v > 0, v, np.nan)
        iv = 1.0 / v; iv[~np.isfinite(iv)] = 0.0
        W[:, w] = iv / iv.sum() if iv.sum() > 0 else np.ones(legs.shape[0]) / legs.shape[0]
    rp = np.sum(W * legs, axis=0)
    print("\nRISK-PARITY (inverse-vol, 4 legs; approx — risk sleeves' cash weeks understate vol):")
    print(row(rp, 'risk-parity 4-leg'))

    # ---- which sleeve is most accurate / best OOS-gated ----
    print("\nSLEEVE OOS-GATED QUALITY (accuracy on acted weeks + risk-adjusted):")
    for k in ['SPY', 'QQQ', 'Gold']:
        d = diag(S[k], k)
        print(f"  {k:4s} gated-acc {accs[k]*100:4.1f}%  Sortino {d['sortino']:5.2f}  Calmar {d['calmar']:5.2f}  CAGR {d['cagr']*100:5.2f}%")

    # ---- CALENDAR YEAR-BY-YEAR for the 20% hedge book (the recommended config) ----
    book20 = 0.20 * t2 + (0.80 / 3.0) * rsum
    dts_s = pd.DatetimeIndex(base['Date'].to_numpy()[mask])
    sr = pd.Series(book20, index=dts_s); yr = sr.groupby(sr.index.year).apply(lambda x: (1 + x).prod() - 1)
    d20 = diag(book20, '20%')
    print(f"\nCALENDAR YEAR-BY-YEAR — 20% hedge book (calendar CAGR {d20['cagr']*100:.2f}%, {(yr>0).mean()*100:.0f}% of years positive):")
    print("  " + "  ".join(f"{y}:{v*100:+.1f}%" for y, v in yr.items()))

    # ---- PREDICTION-SIZING: drop the negative Gold sleeve + Sortino-weight SPY/QQQ ----
    sSPY = diag(S['SPY'], 'x')['sortino']; sQQQ = diag(S['QQQ'], 'x')['sortino']
    book_dropgold = 0.20 * t2 + 0.40 * (risk[0] + risk[1])                 # SPY+QQQ 40/40, no Gold
    wsp, wqq = max(sSPY, 0), max(sQQQ, 0); tot = wsp + wqq
    book_sortw = 0.20 * t2 + 0.80 * ((wsp * risk[0] + wqq * risk[1]) / tot if tot > 0 else 0)
    print("\nPREDICTION-SIZED books (size sleeves by OOS quality; both throttles + 20% 2Y hedge):")
    print(row(book20, 'baseline (EW risk incl Gold)'))
    print(row(book_dropgold, 'drop Gold (SPY+QQQ 40/40)'))
    print(row(book_sortw, 'Sortino-weighted SPY/QQQ'))

    # ---- 10% DRAWDOWN CAP: push CAGR via weighting (Sortino-first) ----
    rw = (wsp * risk[0] + wqq * risk[1]) / tot if tot > 0 else np.zeros(len(t2))   # Sortino-wt SPY/QQQ, no Gold
    print("\n10% DD-CAP PUSH (drop Gold; Sortino-wt SPY/QQQ; sweep hedge DOWN; Sortino-first):")
    cap_best = None
    for wh in [0.20, 0.15, 0.10, 0.07, 0.05, 0.03, 0.0]:
        bk = wh * t2 + (1 - wh) * rw; d = diag(bk, 'x'); ok = d['maxdd'] >= -0.10
        print(f"  hedge {wh*100:>4.1f}%  CAGR {d['cagr']*100:5.2f}%  Sortino {d['sortino']:.2f}  Calmar {d['calmar']:.2f}  MaxDD {d['maxdd']*100:5.1f}%  [{'OK' if ok else 'DD>10%'}]")
        if ok and (cap_best is None or d['cagr'] > cap_best[1]): cap_best = (wh, d['cagr'], d['sortino'], d['maxdd'])
    if cap_best:
        print(f"  -> MAX CAGR under 10% DD via WEIGHTING: {cap_best[1]*100:.2f}%  at hedge {cap_best[0]*100:.0f}%  (Sortino {cap_best[2]:.2f}, DD {cap_best[3]*100:.1f}%)")
    for wh in [0.15, 0.20]:
        bk = wh * t2 + (1 - wh) * rw; db = diag(bk, 'x')
        lev = min(3.0, 0.10 / abs(db['maxdd'])) if db['maxdd'] < 0 else 1.0
        dl = diag(lev * bk, 'x')
        print(f"  +LEVERAGE: {wh*100:.0f}%-hedge book @ {lev:.2f}x -> CAGR {dl['cagr']*100:.2f}%  Sortino {dl['sortino']:.2f}  DD {dl['maxdd']*100:.1f}%  (financing unmodeled)")

    # ---- LOCKED book + SILVER MICRO-SLEEVE overlay (from the other thread) ----
    locked = 0.20 * t2 + 0.80 * rw
    lev = 0.10 / abs(diag(locked, 'x')['maxdd'])
    try:
        smt = _load('smt', 'silver_micro_test.py')
        ag = smt.silver_micro()
        ag_al = ag.reindex(pd.DatetimeIndex(base['Date'].to_numpy()[mask]), method='nearest',
                           tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()
        act = np.abs(ag_al) > 1e-9
        cg = np.corrcoef(ag_al[act], locked[act])[0, 1] if act.sum() > 10 else float('nan')
        print(f"\nLOCKED BOOK (20% 2Y hedge, Sortino-wt SPY/QQQ, drop Gold, dual throttle) + 5% SILVER MICRO:")
        print(f"  silver micro: active {act.mean()*100:.0f}% of weeks, corr to locked book {cg:+.2f}")
        print(row(locked, 'LOCKED (unlevered)'))
        print(row(locked + 0.05 * ag_al, 'LOCKED + 5% silver micro'))
        print(row(lev * locked, f'LOCKED @ {lev:.2f}x (10% DD cap)'))
        print(row(lev * locked + 0.05 * ag_al, f'LOCKED @ {lev:.2f}x + 5% silver micro'))
        # dump the locked book series for downstream screens (micro-sleeve admission gate)
        pd.DataFrame({'Date': base['Date'].to_numpy()[mask], 'locked': locked, 'lev': lev,
                      'silver_micro': ag_al}).to_csv(os.path.join(REP, 'locked_book.csv'), index=False)
        print(f"  [dumped] reports/locked_book.csv (lev={lev:.3f})")

        # ---- GOLD STRUCTURAL OVERLAY (no signal claim — hedge-style, like the 2Y leg) ----
        # Disclosed 6-cell grid: w in {2.5,5,10}% x {always-on, stress-only(throttle active)}.
        # Judged G3/G4-style: corr + book Sortino under the 10% DD cap. 5bps on weight changes.
        gr_full = np.full(len(base), np.nan); gp = np.asarray(gold_px, float)
        gr_full[1:] = gp[1:] / gp[:-1] - 1.0
        gr = np.nan_to_num(gr_full[mask]); stress = (thr < 1.0)
        print(f"\nGOLD STRUCTURAL OVERLAY on LOCKED book (stress weeks = {stress.mean()*100:.0f}% of calendar):")
        cg_b = np.corrcoef(gr, locked)[0, 1]
        cg_m = np.corrcoef(gr[np.abs(ag_al) > 1e-9], ag_al[np.abs(ag_al) > 1e-9])[0, 1]
        print(f"  gold corr: to locked book {cg_b:+.2f} (all wks) | to silver micro {cg_m:+.2f} (micro-active wks)")
        base_final = locked + 0.05 * ag_al                       # locked + micro (unlevered)
        d0f = diag(base_final, 'x')
        for tag, wser in [('always', None), ('stress', stress)]:
            for w in (0.025, 0.05, 0.10):
                wt = np.full(len(gr), w) if wser is None else w * wser.astype(float)
                leg = wt * gr - 5 / 1e4 * np.abs(np.diff(np.concatenate([[0.0], wt])))
                bk = base_final + leg
                d = diag(bk, 'x')
                lev2 = min(3.0, 0.10 / abs(d['maxdd'])) if d['maxdd'] < 0 else 1.0
                dl2 = diag(lev2 * bk, 'x')
                print(f"  +gold {tag:6s} w={w*100:4.1f}%:  unlev Sortino {d['sortino']:5.2f} (Δ{d['sortino']-d0f['sortino']:+.2f}) "
                      f"DD {d['maxdd']*100:5.1f}%  | @cap {lev2:.2f}x -> CAGR {dl2['cagr']*100:5.2f}%  Sortino {dl2['sortino']:5.2f}")
        print(f"  reference (locked+micro, no gold): unlev Sortino {d0f['sortino']:.2f}, "
              f"@1.232x CAGR {diag(1.232*base_final,'x')['cagr']*100:.2f}% Sortino {diag(1.232*base_final,'x')['sortino']:.2f}")
    except Exception as e:
        print(f"\nsilver micro integration failed: {repr(e)[:180]}")

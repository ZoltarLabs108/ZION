"""
netting_ledger.py — per-instrument NET exposure across the two ZION cadences (SYZYGY netting
mandate, applied to the UNIVERSE book) + as-issued forward-tape emission.

Weekly leg (Amendment-1 locked book, frozen params — H=2, lev=1.220, weights per spec):
  SPY sleeve  w=0.80*sSPY/(sSPY+sQQQ) x thr x lev   (pos +/-1 during non-overlap H-blocks, LB>0.50 gate)
  QQQ sleeve  w=0.80*sQQQ/(sSPY+sQQQ) x thr x lev
  2Y hedge    0.20 x lev (always-on, unthrottled)
  gold        0.075 x lev (always-on)                silver micro 0.05 x pos x lev (episodic)
Monthly leg (SYZYGY base): per_sleeve_ledger without_cells positions x (1/n_data) sleeve weight.
UNIVERSE exposure per bucket = 0.5*weekly + 0.5*monthly. Buckets:
  US_EQ (SPY+SP500) | NASDAQ (QQQ) | GOLD (overlay+Gold sleeve) | SILVER (micro+Silver sleeve)
  | WTI (monthly only) | UST2Y (weekly only).
Outputs: reports/netting_ledger.csv (weekly rows), summary (max/mean netted gross vs 2.0x house cap,
opposing-vs-stacking weeks), and seeds/updates reports/universe_forward_tape.csv (as-issued).
"""
import os, importlib.util, math, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
H = 2; LEV = 1.190; LEV_RECOVERY = 2.0; RECOVERY_WKS = 4; SPELL = 2
W_RISK, W_2Y, W_GOLD, W_MICRO = 0.80, 0.20, 0.075, 0.05
SCORE0 = pd.Timestamp('2007-08-01'); GROSS_CAP = 2.0            # legacy/live-book cap (reported)
UNIVERSE_LEV = 2.54; UNIVERSE_GROSS_CAP = 3.5                    # AMENDMENT 4 (operator 2026-08-17)
# AMENDMENT 2 (2026-08-17): risk-sleeve positions PERSIST from each gated decision until the next
# (abstain = hold), and FLATTEN while the dual throttle is stressed (thr < 1.0). Passed G1-G3
# (Sortino@cap 2.37 -> 2.82, both halves non-negative); pure persistence w/o stress-exit REJECTED.
# AMENDMENT 3 (2026-08-17): leverage is a WORLD-STATE SCHEDULE — base 1.190x calm; 2.0x (house cap)
# for RECOVERY_WKS after a recovery event (first calm week after >= SPELL stressed weeks). Gates:
# Sortino@cap 2.82 -> 3.17, DD unchanged, both halves >= 0; events evenly split 12/11 across halves.


def _l(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py'); wf = _l('wf', 'weekly_full_spy.py')
eng = _l('eng', 'weekly_reddawn_spy.py'); drv = _l('drv', 'zion_driver.py')
wlb_eff = eng.wlb_eff

spy = pd.read_csv(os.path.join(WT, 'weekly_panel_spy.csv')); spy['Date'] = pd.to_datetime(spy['Date'])
base = spy[spy['Date'] >= pd.Timestamp('1995-01-01')].reset_index(drop=True)


def yser(t):
    s = zw.yahoo_weekly(t)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).ffill().values


def sleeve_pos(price):
    """Rebuild a risk sleeve's POSITION series + block return series. AMENDMENT 2: the position
    PERSISTS from each gated decision until the next gated decision (abstain = hold); the
    stress-exit (flatten while thr < 1.0) is applied downstream where the throttle is known."""
    panel = base.copy(); panel['SP_Price'] = price
    sp = np.asarray(price, float); dts = base['Date'].to_numpy(); cpi = base['US_CPI'].to_numpy(float)
    wf.H = H
    rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, panel); od = wf.odyssey(sp, dts, ret, lab); sc, _ = wf.sanctuary(sp, dts, ret, lab)
    weeks = sorted(set(rd) & set(od) & set(sc))
    dec = {}
    for t in weeks:
        pres = [v for v in (rd[t], od[t], sc[t]) if v != 0]
        dec[t] = pres[0] if (len(pres) >= 2 and len(set(pres)) == 1) else 0
    acted = []; k = n = 0
    for t in weeks:
        c = dec[t]
        if c != 0 and np.isfinite(lab[t]) and lab[t] != 0:
            if n >= 12 and wlb_eff(k, n, H) > 0.50: acted.append((t, c))
            k += int(c == lab[t]); n += 1
    wret = np.full(len(sp), np.nan); wret[1:] = sp[1:] / sp[:-1] - 1.0
    arr = np.zeros(len(base)); last = -10**9
    for t, c in sorted(acted):
        if t - last >= H:
            for j in range(1, H + 1):
                if t + j < len(base) and np.isfinite(wret[t + j]): arr[t + j] += c * wret[t + j]
            last = t
    ai = {t: c for t, c in acted}                       # persistence: hold last gated direction
    pos = np.zeros(len(base)); cur = 0.0
    for t in range(len(base)):
        if t in ai: cur = float(ai[t])
        pos[t] = cur
    return pos, arr


def micro_pos():
    """silver micro POSITION series (VIX/IP_Nowcast N8 H4 episodic), on the drv SILVER calendar."""
    P = drv.build_panel(drv.ASSETS['SILVER']); cal = pd.to_datetime(P['Date'])
    de = P['Date'].iloc[0] + (P['Date'].iloc[-1] - P['Date'].iloc[0]) * 0.4
    s, ret, lab = zw.stream(P, 'VIX_Close', 'IP_Nowcast_Level', 8, 4, drv.ASSETS['SILVER']['MFF'], de)
    pos = np.zeros(len(P)); hold = 0; cur = 0.0
    for t in range(len(P)):
        d = s.get(t); d = d if d not in (0, None) else 0
        if d != 0: cur = float(d); hold = 4
        elif hold > 0: hold -= 1
        else: cur = 0.0
        pos[t] = cur if hold > 0 or d != 0 else 0.0
    return pd.Series(pos, index=cal).reindex(base['Date'], method='nearest', tolerance=pd.Timedelta('4D')).fillna(0.0).to_numpy()


def _sortino(r):
    dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2)); return float(np.mean(r) / dn * np.sqrt(52)) if dn > 0 else np.nan


def main():
    print('[1/4] rebuilding weekly sleeve positions (frozen H=2) ...')
    spy_pos, spy_arr = sleeve_pos(base['SP_Price'].to_numpy(float))
    qqq_pos, qqq_arr = sleeve_pos(yser('QQQ'))
    mask = (base['Date'] >= SCORE0).to_numpy()
    sS, sQ = _sortino(spy_arr[mask]), _sortino(qqq_arr[mask])
    wsp, wqq = W_RISK * sS / (sS + sQ), W_RISK * sQ / (sS + sQ)
    print(f'      sleeve Sortinos {sS:.2f}/{sQ:.2f} -> weights SPY {wsp:.3f} QQQ {wqq:.3f} (of book)')
    print('[2/4] throttle + silver micro positions ...')
    vix = base['VIX_Close'].to_numpy(float); cred = base['Credit_BAA10Y'].to_numpy(float)
    def pctl_thr(series):
        t = np.ones(len(series))
        for w in range(len(series)):
            pri = series[:w]; pri = pri[np.isfinite(pri)]
            if len(pri) >= 50 and np.isfinite(series[w]) and (pri <= series[w]).mean() >= 0.70: t[w] = 0.5
        return t
    thr = pctl_thr(vix) * pctl_thr(cred)
    # Amendment 3: recovery windows (first calm week after >= SPELL stressed weeks -> RECOVERY_WKS at cap)
    recovery = np.zeros(len(base), bool); run = 0
    for i in range(len(base)):
        if thr[i] < 1.0: run += 1
        else:
            if run >= SPELL: recovery[i:i + RECOVERY_WKS] = True
            run = 0
    mpos = micro_pos()
    print('[3/4] monthly leg positions (SYZYGY base) ...')
    ps = pd.read_csv('/Users/castaglia/Desktop/ZION/reports/per_sleeve_ledger.csv')
    ps = ps[ps['variant'] == 'without_cells']; ps['date'] = pd.to_datetime(ps['date'])
    bl = pd.read_csv('/Users/castaglia/Desktop/ZION/reports/book_ledger.csv'); bl['date'] = pd.to_datetime(bl['date'])
    ndata = bl.set_index(bl['date'].dt.to_period('M'))['n_data']
    mon = {}
    for slv in ['SPY', 'Gold', 'Silver', 'WTI']:
        d = ps[ps['sleeve'] == slv].set_index(ps[ps['sleeve'] == slv]['date'].dt.to_period('M'))['position']
        mon[slv] = d
    rows = []
    dts = pd.DatetimeIndex(base['Date'])
    for i in np.where(mask)[0]:
        wdt = dts[i]; mper = wdt.to_period('M')
        nd = float(ndata.get(mper, 5)) or 5
        mw = 0.5 / nd                                             # universe share x sleeve weight
        m_spy = mw * float(mon['SPY'].get(mper, 0)); m_gld = mw * float(mon['Gold'].get(mper, 0))
        m_slv = mw * float(mon['Silver'].get(mper, 0)); m_wti = mw * float(mon['WTI'].get(mper, 0))
        lev_i = LEV_RECOVERY if recovery[i] else LEV               # Amendment 3 schedule
        wl = 0.5 * lev_i                                           # universe share x weekly leverage
        onoff = 1.0 if thr[i] >= 1.0 else 0.0                     # AMENDMENT 2 stress-exit: flat, not scaled
        w_spy = wl * wsp * onoff * spy_pos[i]; w_qqq = wl * wqq * onoff * qqq_pos[i]
        w_gld = wl * W_GOLD; w_slv = wl * W_MICRO * mpos[i]; w_t2 = wl * W_2Y
        rows.append(dict(week=str(wdt.date()), lev=lev_i,
                         US_EQ=w_spy + m_spy, NASDAQ=w_qqq, GOLD=w_gld + m_gld, SILVER=w_slv + m_slv,
                         WTI=m_wti, UST2Y=w_t2,
                         w_spy=w_spy, m_spy=m_spy, w_gold=w_gld, m_gold=m_gld, w_silver=w_slv,
                         m_silver=m_slv, thr=thr[i],
                         gross=sum(abs(x) for x in (w_spy + m_spy, w_qqq, w_gld + m_gld, w_slv + m_slv, m_wti, w_t2)),
                         gross_stacked=sum(abs(x) for x in (w_spy, m_spy, w_qqq, w_gld, m_gld, w_slv, m_slv, m_wti, w_t2))))
    L = pd.DataFrame(rows)
    L.to_csv(os.path.join(REP, 'netting_ledger.csv'), index=False)
    print('[4/4] summary + forward-tape emission ...\n')
    opp_eq = ((L.w_spy * L.m_spy) < 0).sum(); stk_eq = ((L.w_spy * L.m_spy) > 0).sum()
    opp_au = ((L.w_gold * L.m_gold) < 0).sum(); stk_au = ((L.w_gold * L.m_gold) > 0).sum()
    opp_ag = ((L.w_silver * L.m_silver) < 0).sum(); stk_ag = ((L.w_silver * L.m_silver) > 0).sum()
    print(f"NETTING LEDGER — {len(L)} weeks ({L.week.iloc[0]}..{L.week.iloc[-1]}) -> reports/netting_ledger.csv")
    print(f"  netted gross : max {L.gross.max():.2f}x  mean {L.gross.mean():.2f}x   (house cap {GROSS_CAP:.1f}x -> "
          f"{'NEVER breached' if L.gross.max() <= GROSS_CAP else 'BREACHED — investigate'})")
    print(f"  vs stacked   : max {L.gross_stacked.max():.2f}x  (netting saves up to "
          f"{(L.gross_stacked - L.gross).max():.2f}x in the worst week)")
    print(f"  per-bucket max |net|: " + "  ".join(f"{c} {L[c].abs().max():.2f}" for c in
          ['US_EQ', 'NASDAQ', 'GOLD', 'SILVER', 'WTI', 'UST2Y']))
    print(f"  US_EQ  legs: opposing {opp_eq} wks / stacking {stk_eq} wks")
    print(f"  GOLD   legs: opposing {opp_au} wks / stacking {stk_au} wks")
    print(f"  SILVER legs: opposing {opp_ag} wks / stacking {stk_ag} wks")
    # ---- forward tape: append this week's as-issued emission if not already present ----
    tape_p = os.path.join(REP, 'universe_forward_tape.csv')
    cur = L.iloc[-1]
    row = dict(issued=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'), week_ending=cur.week, status='ISSUED',
               lev=float(cur.lev), recovery=bool(cur.lev > LEV), L_universe=UNIVERSE_LEV,
               US_EQ=round(cur.US_EQ, 4), NASDAQ=round(cur.NASDAQ, 4), GOLD=round(cur.GOLD, 4),
               SILVER=round(cur.SILVER, 4), WTI=round(cur.WTI, 4), UST2Y=round(cur.UST2Y, 4),
               thr=cur.thr, gross=round(cur.gross, 4), realized_ret='', resolved='')
    if os.path.exists(tape_p):
        tape = pd.read_csv(tape_p)
        if str(cur.week) in set(tape['week_ending'].astype(str)):
            print(f"\nFORWARD TAPE: week {cur.week} already issued — no duplicate append.")
        else:
            tape = pd.concat([tape, pd.DataFrame([row])], ignore_index=True); tape.to_csv(tape_p, index=False)
            print(f"\nFORWARD TAPE: issued week {cur.week} appended.")
    else:
        pd.DataFrame([row]).to_csv(tape_p, index=False)
        print(f"\nFORWARD TAPE OPENED: {tape_p}")
    print(f"  as-issued exposures ({cur.week}): US_EQ {cur.US_EQ:+.3f}  NASDAQ {cur.NASDAQ:+.3f}  "
          f"GOLD {cur.GOLD:+.3f}  SILVER {cur.SILVER:+.3f}  WTI {cur.WTI:+.3f}  UST2Y {cur.UST2Y:+.3f}  "
          f"(thr {cur.thr:.2f}, gross {cur.gross:.2f}x)")


if __name__ == '__main__':
    main()

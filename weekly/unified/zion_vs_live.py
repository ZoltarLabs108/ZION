"""
zion_vs_live.py — standing weekly comparison: ZION UNIVERSE ticket vs the LIVE AEGIS ticket.

READ-ONLY on AEGIS (observe, never re-run). Alignment: both tickets are normalized to the
TRADE WEEK they govern — AEGIS labels week_ending = the coming Friday (issued before the week);
the ZION tape labels the issue week W, which trades W -> W+1wk. So ZION row W <-> AEGIS row W+7d.

Each run (wired as step [4/4] of the Friday job):
  1) appends any new comparable trade week to reports/zion_vs_live_ledger.csv (idempotent),
  2) resolves matured weeks: ZION return from the universe tape's realized_ret; LIVE return
     recomputed as sum(signed notional/capital x instrument return) over the trade week
     (SP=^GSPC, Gold=GC=F, Silver=SI=F, Pt=PL=F, NG=NG=F),
  3) prints the running comparison (exposures, direction agreement, cumulative record).

This is a COMPARISON ledger, not a verdict engine: per the house rule, 12+ resolved weeks before
reading anything into it. The live ticket's own official scoring stays in AEGIS — this recompute
uses Yahoo weekly closes and may differ slightly from settlement-based sleeve tapes (disclosed).
"""
import os, importlib.util
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
AEGIS = '/Users/castaglia/Desktop/AEGIS/AEGIS_OUTPUT/AEGIS_TICKET_HISTORY.csv'
TAPE = os.path.join(REP, 'universe_forward_tape.csv')
LEDGER = os.path.join(REP, 'zion_vs_live_ledger.csv')
START = pd.Timestamp('2026-08-14')            # first comparable trade week (forward-only, operator)

_utr = importlib.util.spec_from_file_location('utr', os.path.join(HERE, 'universe_tape_resolve.py'))
utr = importlib.util.module_from_spec(_utr); _utr.loader.exec_module(utr)


def live_rows():
    a = pd.read_csv(AEGIS); a['Week_Ending'] = pd.to_datetime(a['Week_Ending'])
    cap = a['Capital'].replace(0, np.nan)
    out = pd.DataFrame({'trade_week': a['Week_Ending'],
                        'live_SP': a['SP_Notional_Lev'].fillna(0) / cap,
                        'live_GOLD': a['Gold_Notional_Lev'].fillna(0) / cap,
                        'live_SILVER': a.get('Silver_Notional_Lev', pd.Series(0, index=a.index)).fillna(0) / cap,
                        'live_PT': a.get('Pt_Notional_Lev', pd.Series(0, index=a.index)).fillna(0) / cap,
                        'live_NG': a.get('NG_Notional_Lev', pd.Series(0, index=a.index)).fillna(0) / cap})
    out['live_gross'] = out[[c for c in out.columns if c.startswith('live_') and c != 'live_gross']].abs().sum(axis=1)
    return out.drop_duplicates('trade_week', keep='last')


def zion_rows():
    t = pd.read_csv(TAPE); t['week_ending'] = pd.to_datetime(t['week_ending'])
    t['trade_week'] = t['week_ending'] + pd.Timedelta(days=7)     # issue week W trades to W+7
    keep = ['trade_week', 'US_EQ', 'NASDAQ', 'GOLD', 'SILVER', 'WTI', 'UST2Y', 'gross', 'realized_ret', 'status']
    if 'USD' in t.columns: keep.insert(7, 'USD')
    z = t[keep].rename(columns={c: f'zion_{c}' for c in keep if c != 'trade_week'})
    return z.drop_duplicates('trade_week', keep='last')


def live_realized(row, w1):
    w0 = w1 - pd.Timedelta(days=7)
    legs = [('live_SP', '%5EGSPC'), ('live_GOLD', 'GC%3DF'), ('live_SILVER', 'SI%3DF'),
            ('live_PT', 'PL%3DF'), ('live_NG', 'NG%3DF')]
    tot = 0.0
    for col, tk in legs:
        e = float(row[col])
        if abs(e) < 1e-9: continue
        r = utr.wk_ret(tk, w0, w1)
        if np.isnan(r): return np.nan
        tot += e * r
    return tot


def main():
    lv = live_rows(); zn = zion_rows()
    led = pd.read_csv(LEDGER) if os.path.exists(LEDGER) else pd.DataFrame()
    if len(led): led['trade_week'] = pd.to_datetime(led['trade_week'])
    have = set(led['trade_week']) if len(led) else set()
    m = lv.merge(zn, on='trade_week', how='outer').sort_values('trade_week')
    m = m[m['trade_week'] >= START]
    new = m[~m['trade_week'].isin(have)].copy()
    if len(new):
        new['zion_ret'] = np.nan; new['live_ret'] = np.nan; new['resolved'] = ''
        led = pd.concat([led, new], ignore_index=True)
    # refresh exposure columns on still-OPEN rows (a ticket side may publish after the row was created)
    exp_cols = [c for c in m.columns if c != 'trade_week']
    mi = m.set_index('trade_week')
    for i, r in led.iterrows():
        tw = pd.Timestamp(r['trade_week'])
        if str(r.get('resolved', '')) in ('', 'nan') and tw in mi.index:
            for c in exp_cols:
                if c in led.columns: led.at[i, c] = mi.at[tw, c]
    # resolve matured trade weeks
    now = pd.Timestamp.now()
    for i, r in led.iterrows():
        tw = pd.Timestamp(r['trade_week'])
        if str(r.get('resolved', '')) not in ('', 'nan') or now < tw + pd.Timedelta(days=1): continue
        zr = r.get('zion_realized_ret')
        if pd.isna(zr):                                       # fall back to tape re-read
            zt = zion_rows(); hit = zt[zt['trade_week'] == tw]
            zr = hit['zion_realized_ret'].iloc[0] if len(hit) else np.nan
        lr = live_realized(r, tw) if not pd.isna(r.get('live_SP', np.nan)) else np.nan
        if not (pd.isna(zr) or pd.isna(lr)):
            led.at[i, 'zion_ret'] = float(zr); led.at[i, 'live_ret'] = float(lr)
            led.at[i, 'resolved'] = now.strftime('%Y-%m-%d')
    led.to_csv(LEDGER, index=False)
    # ---- report ----
    print(f"ZION vs LIVE — standing weekly comparison ({len(led)} trade weeks tracked)")
    print(f"{'trade wk':>10} | {'ZION: eq':>8} {'gold':>6} {'slv':>6} {'2y':>5} {'gross':>6} | "
          f"{'LIVE: sp':>8} {'gold':>6} {'slv':>6} {'pt':>6} {'ng':>6} {'gross':>6} | {'agree':>6} | {'z_ret':>7} {'l_ret':>7}")
    for _, r in led.sort_values('trade_week').iterrows():
        agr = []
        for zc, lc in [('zion_US_EQ', 'live_SP'), ('zion_GOLD', 'live_GOLD'), ('zion_SILVER', 'live_SILVER')]:
            z, l = r.get(zc, np.nan), r.get(lc, np.nan)
            if pd.notna(z) and pd.notna(l) and abs(z) > 1e-9 and abs(l) > 1e-9:
                agr.append('=' if np.sign(z) == np.sign(l) else 'X')
        f = lambda v: f"{v:+.2f}" if pd.notna(v) else '  --'
        zret = f"{r['zion_ret']*100:+.2f}%" if pd.notna(r.get('zion_ret')) else 'open'
        lret = f"{r['live_ret']*100:+.2f}%" if pd.notna(r.get('live_ret')) else 'open'
        print(f"{pd.Timestamp(r['trade_week']).date()} | {f(r.get('zion_US_EQ'))} {f(r.get('zion_GOLD'))} "
              f"{f(r.get('zion_SILVER'))} {f(r.get('zion_UST2Y'))} {f(r.get('zion_gross'))} | "
              f"{f(r.get('live_SP'))} {f(r.get('live_GOLD'))} {f(r.get('live_SILVER'))} {f(r.get('live_PT'))} "
              f"{f(r.get('live_NG'))} {f(r.get('live_gross'))} | {''.join(agr) or '--':>6} | {zret:>7} {lret:>7}")
    res = led.dropna(subset=['zion_ret', 'live_ret'])
    if len(res):
        zc = (1 + res['zion_ret']).prod() - 1; lc = (1 + res['live_ret']).prod() - 1
        print(f"\ncumulative ({len(res)} resolved wks): ZION {zc*100:+.2f}%  vs LIVE {lc*100:+.2f}%  "
              f"| ZION wins {int((res['zion_ret'] > res['live_ret']).sum())}/{len(res)} wks")
        print(f"evidence window: {len(res)}/12 — no verdicts before 12 resolved weeks (house rule).")
    else:
        print("\nno jointly-resolved weeks yet — comparison record opens as weeks mature.")


if __name__ == '__main__':
    main()

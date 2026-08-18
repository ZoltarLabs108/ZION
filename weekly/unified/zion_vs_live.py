"""
zion_vs_live.py — standing weekly comparison: ZION UNIVERSE ticket vs the LIVE (AEGIS) book.

READ-ONLY on AEGIS (observe, never re-run).

LIVE-SIDE BASIS (re-scored 2026-08-18, operator): the live book is NOT the Fri-labeled
Week_Ending row — it is whatever MID-WEEK PRINT (Tuesday 01:15 baseline; Wed catch-up;
historically Wednesday) was last entered, held print-to-print. Scoring the official rows
Fri->Fri mis-stated the record (e.g. a Monday abstain row read as "flat" while the operator
held the prior Wednesday print). The live side is therefore scored AS-EXECUTED:

  * print snapshots come from reports/paper_monclose_ledger.csv (append-only, snapshotted
    the moment each print appears — immune to the ticket-history row overwrite),
  * for each ZION trade week (issue Fri W -> Fri W+1wk), the live return is computed
    PIECEWISE close-to-close: each day's contribution uses the exposures of the print
    actually held that day (latest print with entry_day <= day),
  * live_* display columns show the book held at the START of the trade week; if a new
    print lands mid-week the scoring follows it — the display is the week-open book.

live_ret is derived data (immutable snapshots x market closes), so it is recomputed on
every run; zion_ret always comes from the as-issued universe tape. Per the house rule,
12+ resolved weeks before reading anything into the comparison.
"""
import os, importlib.util
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
TAPE = os.path.join(REP, 'universe_forward_tape.csv')
LEDGER = os.path.join(REP, 'zion_vs_live_ledger.csv')
START = pd.Timestamp('2026-08-14')            # first comparable trade week (forward-only, operator)

_pm = importlib.util.spec_from_file_location('pm', os.path.join(HERE, 'paper_monclose.py'))
pm = importlib.util.module_from_spec(_pm); _pm.loader.exec_module(pm)

LEGMAP = {'e_SP': ('live_SP', '^GSPC'), 'e_GOLD': ('live_GOLD', 'GC=F'),
          'e_SILVER': ('live_SILVER', 'SI=F'), 'e_PT': ('live_PT', 'PL=F'),
          'e_NG': ('live_NG', 'NG=F')}

_PR = None
def prints():
    global _PR
    if _PR is None:
        led = pd.read_csv(pm.LEDGER)
        led = led[(led['midweek_print'] == 1) & led['entry_day'].astype(str).str.len().ge(8)].copy()
        led['entry_day'] = pd.to_datetime(led['entry_day'])
        _PR = led.sort_values('entry_day').reset_index(drop=True)
    return _PR


def held_print(day):
    p = prints(); p = p[p['entry_day'] <= day]
    return p.iloc[-1] if len(p) else None


def live_realized_asexec(w0, w1):
    """As-executed live return over (w0, w1]: piecewise over the prints actually held."""
    spine = pm.closes('^GSPC')
    if spine.index.max() < w1: return np.nan                  # week not complete yet
    days = spine.loc[w0:w1].index
    if len(days) < 2: return np.nan
    tot = 0.0
    for d0, d1 in zip(days[:-1], days[1:]):
        hp = held_print(d0)
        if hp is None: return np.nan
        for ecol, (_, tk) in LEGMAP.items():
            e = float(hp[ecol])
            if abs(e) < 1e-9: continue
            s = pm.closes(tk)
            if d0 not in s.index or d1 not in s.index: return np.nan
            tot += e * (float(s.loc[d1]) / float(s.loc[d0]) - 1.0)
    return tot


def zion_rows():
    t = pd.read_csv(TAPE); t['week_ending'] = pd.to_datetime(t['week_ending'])
    t['trade_week'] = t['week_ending'] + pd.Timedelta(days=7)     # issue week W trades to W+7
    keep = ['trade_week', 'US_EQ', 'NASDAQ', 'GOLD', 'SILVER', 'WTI', 'UST2Y', 'gross', 'realized_ret', 'status']
    if 'USD' in t.columns: keep.insert(7, 'USD')
    if 'INDIA' in t.columns: keep.insert(8, 'INDIA')
    z = t[keep].rename(columns={c: f'zion_{c}' for c in keep if c != 'trade_week'})
    return z.drop_duplicates('trade_week', keep='last')


def main():
    zn = zion_rows()
    led = pd.read_csv(LEDGER) if os.path.exists(LEDGER) else pd.DataFrame()
    if len(led): led['trade_week'] = pd.to_datetime(led['trade_week'])
    have = set(led['trade_week']) if len(led) else set()
    m = zn[zn['trade_week'] >= START].sort_values('trade_week')
    new = m[~m['trade_week'].isin(have)].copy()
    if len(new):
        new['zion_ret'] = np.nan; new['live_ret'] = np.nan; new['resolved'] = ''
        led = pd.concat([led, new], ignore_index=True)
    # refresh ZION exposure columns on still-OPEN rows
    zcols = [c for c in m.columns if c != 'trade_week']
    mi = m.set_index('trade_week')
    for i, r in led.iterrows():
        tw = pd.Timestamp(r['trade_week'])
        if str(r.get('resolved', '')) in ('', 'nan') and tw in mi.index:
            for c in zcols:
                if c not in led.columns: led[c] = np.nan
                led.at[i, c] = mi.at[tw, c]
    # live display columns = book held at the START of each trade week (as-executed)
    for i, r in led.iterrows():
        w0 = pd.Timestamp(r['trade_week']) - pd.Timedelta(days=7)
        hp = held_print(w0)
        g = 0.0
        for ecol, (lcol, _) in LEGMAP.items():
            v = float(hp[ecol]) if hp is not None else np.nan
            if lcol not in led.columns: led[lcol] = np.nan
            led.at[i, lcol] = v
            if np.isfinite(v): g += abs(v)
        if 'live_gross' not in led.columns: led['live_gross'] = np.nan
        led.at[i, 'live_gross'] = g if hp is not None else np.nan
    # score: zion from tape (as-issued), live recomputed AS-EXECUTED every run (derived data)
    for i, r in led.iterrows():
        tw = pd.Timestamp(r['trade_week']); w0 = tw - pd.Timedelta(days=7)
        lr = live_realized_asexec(w0, tw)
        if not pd.isna(lr): led.at[i, 'live_ret'] = float(lr)
        zr = r.get('zion_realized_ret')
        if pd.isna(zr):
            hit = zn[zn['trade_week'] == tw]
            zr = hit['zion_realized_ret'].iloc[0] if len(hit) else np.nan
        if not pd.isna(zr): led.at[i, 'zion_ret'] = float(zr)
        if pd.notna(led.at[i, 'zion_ret']) and pd.notna(led.at[i, 'live_ret']) and str(r.get('resolved','')) in ('', 'nan'):
            led.at[i, 'resolved'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    led.to_csv(LEDGER, index=False)
    # ---- report ----
    print(f"ZION vs LIVE — standing weekly comparison ({len(led)} trade weeks tracked)")
    print("live side = AS-EXECUTED print-hold (Tue-baseline mid-week prints, scored piecewise); "
          "live_* columns = book at week open")
    print(f"{'trade wk':>10} | {'ZION: eq':>8} {'gold':>6} {'2y':>5} {'usd':>6} {'gross':>6} | "
          f"{'LIVE: sp':>8} {'gold':>6} {'slv':>6} {'pt':>6} {'ng':>6} {'gross':>6} | {'z_ret':>7} {'l_ret':>7}")
    for _, r in led.sort_values('trade_week').iterrows():
        f = lambda v: f"{v:+.2f}" if pd.notna(v) else '  --'
        zret = f"{r['zion_ret']*100:+.2f}%" if pd.notna(r.get('zion_ret')) else 'open'
        lret = f"{r['live_ret']*100:+.2f}%" if pd.notna(r.get('live_ret')) else 'open'
        print(f"{pd.Timestamp(r['trade_week']).date()} | {f(r.get('zion_US_EQ'))} {f(r.get('zion_GOLD'))} "
              f"{f(r.get('zion_UST2Y'))} {f(r.get('zion_USD'))} {f(r.get('zion_gross'))} | "
              f"{f(r.get('live_SP'))} {f(r.get('live_GOLD'))} {f(r.get('live_SILVER'))} {f(r.get('live_PT'))} "
              f"{f(r.get('live_NG'))} {f(r.get('live_gross'))} | {zret:>7} {lret:>7}")
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

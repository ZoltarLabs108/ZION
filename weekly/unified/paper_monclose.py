"""
paper_monclose.py — PAPER-TRACK of the Monday-close exit rule on the live (AEGIS) book.

Hypothesis (operator, 2026-08-18): the live book's profit concentrates between the Wednesday
print and Monday's close; the Tue + Wed-morning tail gives it back (5-period intel:
Wed->Mon +2.25% vs tail -2.34%). Calendar timing is EXOGENOUS (world-state-legal), so the
rule may be paper-tracked — but 22 trading days with a hindsight-chosen split adopts nothing.
House rule: 12 forward resolved weeks before any verdict; this script builds that record.

Mechanics:
  * READ-ONLY on AEGIS. The live cadence is Wednesday-hold: com.zoltar.weekly.wed (Wed 01:15)
    regenerates the AEGIS ticket row with Mon+Tue closes; the operator holds each mid-week
    print until the next one. Monday 06:00 prints are NOT traded.
  * AEGIS_TICKET_HISTORY keeps only the LAST print per Week_Ending (Mon row overwritten Wed),
    so this script SNAPSHOTS every new mid-week print into an append-only ledger the moment
    it is seen — the paper record can never be revised after the fact.
  * A print counts as MID-WEEK (traded) if Generated falls Tue..Thu (guard delays can push
    the Wednesday run to Thursday, e.g. 2026-08-06). Mon/Fri generations are logged but
    skipped — the previous mid-week print stays the held book, matching live practice.
  * Both arms priced close-to-close from the print's Generated-day close:
      FULL HOLD : entry close -> next mid-week print's entry close   (what the operator does)
      MON-CLOSE : entry close -> first Monday close after entry, then flat  (the paper rule)
  * Rows seen only at backfill (before 2026-08-18) are flagged backfill=1: legitimate
    as-issued for completed weeks (rows are final once their week passes) but the 0/12
    forward evidence window counts non-backfill rows only.

Wired as a step of run_universe.sh (Fri 17:30) — Friday always sees the week's mid-week
print before the next Monday overwrite. Paper only: sizes nothing, changes no execution.
"""
import os
import numpy as np, pandas as pd
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
AEGIS = '/Users/castaglia/Desktop/AEGIS/AEGIS_OUTPUT/AEGIS_TICKET_HISTORY.csv'
LEDGER = os.path.join(REP, 'paper_monclose_ledger.csv')
FORWARD_START = pd.Timestamp('2026-08-18')     # rows snapshotted before this are backfill
LEGS = {'SP': ('SP_Notional_Lev', '^GSPC'), 'GOLD': ('Gold_Notional_Lev', 'GC=F'),
        'SILVER': ('Silver_Notional_Lev', 'SI=F'), 'PT': ('Pt_Notional_Lev', 'PL=F'),
        'NG': ('NG_Notional_Lev', 'NG=F')}

_px = {}
def closes(tk):
    if tk not in _px:
        h = yf.Ticker(tk).history(start='2026-07-01')['Close'].dropna()
        h.index = h.index.tz_localize(None).normalize()
        _px[tk] = h
    return _px[tk]


def close_on_or_after(tk, day):
    s = closes(tk); s = s[s.index >= day]
    return (s.index[0], float(s.iloc[0])) if len(s) else (None, np.nan)


def next_monday_close(day):
    """First Monday trading close strictly after `day` (spine = ^GSPC calendar)."""
    s = closes('^GSPC'); s = s[(s.index > day)]
    mons = s[s.index.dayofweek == 0]
    return mons.index[0] if len(mons) else None


def leg_ret(tk, d0, d1):
    s = closes(tk)
    if d0 not in s.index: return np.nan
    p0 = float(s.loc[d0])
    s2 = s[s.index <= d1]
    if not len(s2) or s2.index[-1] < d0: return np.nan
    return float(s2.iloc[-1]) / p0 - 1.0


def book_ret(row, d0, d1):
    tot = 0.0
    for k, (col, tk) in LEGS.items():
        e = float(row[f'e_{k}'])
        if abs(e) < 1e-9: continue
        r = leg_ret(tk, d0, d1)
        if np.isnan(r): return np.nan
        tot += e * r
    return tot


def snapshot_new_prints(led):
    a = pd.read_csv(AEGIS); a['Generated'] = pd.to_datetime(a['Generated'])
    a = a.sort_values('Generated')
    seen = set(led['generated'].astype(str)) if len(led) else set()
    new = []
    for _, r in a.iterrows():
        g = r['Generated']
        if str(g) in seen or pd.isna(g): continue
        wd = g.dayofweek                                   # 0=Mon
        midweek = wd in (1, 2, 3)                          # Tue..Thu = traded print
        entry_day, _ = close_on_or_after('^GSPC', g.normalize())
        row = {'generated': str(g), 'week_ending': str(pd.Timestamp(r['Week_Ending']).date()),
               'gen_weekday': g.day_name(), 'midweek_print': int(midweek),
               'backfill': int(pd.Timestamp.now() < FORWARD_START or g < FORWARD_START - pd.Timedelta(days=2)),
               'entry_day': str(entry_day.date()) if entry_day is not None else '',
               'ret_fullhold': np.nan, 'ret_monclose': np.nan, 'status': 'OPEN' if midweek else 'SKIP(non-midweek)'}
        cap = float(r['Capital']) or 1e5
        for k, (col, tk) in LEGS.items():
            row[f'e_{k}'] = round(float(r.get(col, 0) or 0) / cap, 5)
        new.append(row)
    if new:
        led = pd.concat([led, pd.DataFrame(new)], ignore_index=True)
    return led, len(new)


def resolve(led):
    mid = led[led['midweek_print'] == 1].sort_values('generated').reset_index()
    n_res = 0
    for j in range(len(mid)):
        i = mid.loc[j, 'index']; r = mid.loc[j]
        if r['status'] == 'RESOLVED' or not r['entry_day']: continue
        d0 = pd.Timestamp(r['entry_day'])
        # MON-CLOSE arm
        dm = next_monday_close(d0)
        if dm is not None and pd.isna(led.at[i, 'ret_monclose']):
            rm = book_ret(r, d0, dm)
            if not np.isnan(rm):
                led.at[i, 'ret_monclose'] = round(rm, 6); led.at[i, 'mon_exit'] = str(dm.date())
        # FULL-HOLD arm (needs the NEXT mid-week print's entry day)
        if j + 1 < len(mid) and mid.loc[j+1, 'entry_day']:
            d1 = pd.Timestamp(mid.loc[j+1, 'entry_day'])
            rf = book_ret(r, d0, d1)
            if not np.isnan(rf):
                led.at[i, 'ret_fullhold'] = round(rf, 6); led.at[i, 'full_exit'] = str(d1.date())
        if pd.notna(led.at[i, 'ret_monclose']) and pd.notna(led.at[i, 'ret_fullhold']):
            led.at[i, 'status'] = 'RESOLVED'; n_res += 1
    return led, n_res


def report(led):
    mid = led[led['midweek_print'] == 1].sort_values('generated')
    print('PAPER-TRACK — Monday-close exit vs full Wednesday-hold (live AEGIS book, paper only)')
    print(f"{'print':>12} {'wd':>4} {'entry':>11} {'bf':>3} {'full-hold':>10} {'mon-close':>10} {'edge':>8}  status")
    for _, r in mid.iterrows():
        f = lambda v: f"{v*100:+.2f}%" if pd.notna(v) else 'open'
        edge = (r['ret_monclose'] - r['ret_fullhold']) if pd.notna(r['ret_monclose']) and pd.notna(r['ret_fullhold']) else np.nan
        print(f"{r['generated'][:10]:>12} {r['gen_weekday'][:3]:>4} {str(r['entry_day']):>11} {int(r['backfill']):>3} "
              f"{f(r['ret_fullhold']):>10} {f(r['ret_monclose']):>10} {f(edge) if pd.notna(edge) else '  --':>8}  {r['status']}")
    res = mid[mid['status'] == 'RESOLVED']
    if len(res):
        cf = (1 + res['ret_fullhold']).prod() - 1; cm = (1 + res['ret_monclose']).prod() - 1
        wins = int((res['ret_monclose'] > res['ret_fullhold']).sum())
        print(f"\nall resolved ({len(res)}, incl backfill): full-hold {cf*100:+.2f}%  mon-close {cm*100:+.2f}%  "
              f"| rule wins {wins}/{len(res)}")
    fwd = mid[(mid['status'] == 'RESOLVED') & (mid['backfill'] == 0)]
    print(f"FORWARD evidence window: {len(fwd)}/12 resolved — no adoption verdict before 12 "
          f"(backfill rows are context only; hindsight-chosen split, see funnel-miner doctrine).")
    # ---- LIVE BOOK TIMING BOARD (suggestion only; the mon-close arm is PAPER at 0/12) ----
    if len(mid):
        cur = mid.iloc[-1]
        entry = pd.Timestamp(cur['entry_day']) if cur['entry_day'] else None
        if entry is not None:
            we = pd.Timestamp(cur['week_ending'])
            horizon_end = we                               # signal targets issue-Fri -> week_ending Fri
            today = pd.Timestamp.now().normalize()
            dm = entry + pd.Timedelta(days=((7 - entry.dayofweek) % 7) or 7)   # calendar next Monday
            print(f"\nLIVE BOOK TIMING — held print {cur['generated'][:10]} ({cur['gen_weekday']}), entered {entry.date()}")
            print(f"  forecast horizon ends Fri {horizon_end.date()}"
                  f"  ->  today is {'INSIDE' if today <= horizon_end else 'OUTSIDE'} the horizon"
                  f" ({(today - horizon_end).days:+d}d vs horizon end)")
            print(f"  FULL-HOLD exit (live practice)      : next mid-week print (Tue 01:15 baseline; Wed = catch-up only)")
            print(f"  MON-CLOSE exit (paper rule, {len(fwd)}/12) : Monday {dm.date() if dm is not None else '--'} at the close")


def main():
    led = pd.read_csv(LEDGER) if os.path.exists(LEDGER) else pd.DataFrame()
    led, n_new = snapshot_new_prints(led)
    led, n_res = resolve(led)
    os.makedirs(REP, exist_ok=True)
    led.to_csv(LEDGER, index=False)
    print(f"snapshotted {n_new} new print(s), resolved {n_res} period(s) -> {os.path.basename(LEDGER)}\n")
    report(led)


if __name__ == '__main__':
    main()

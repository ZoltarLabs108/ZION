"""
universe_tape_resolve.py — resolve matured rows of the UNIVERSE forward tape (as-issued, append-only).

Weekly operation (each Friday, after the close):
  1) python3 netting_ledger.py          -> appends this week's ISSUED exposures (no duplicates)
  2) python3 universe_tape_resolve.py   -> fills realized returns for matured issues

A row issued for week_ending W resolves over the FOLLOWING week (W -> W+1wk):
  realized = sum_i exposure_i x ret_i   with US_EQ=^GSPC, NASDAQ=QQQ, GOLD=GC=F, SILVER=SI=F,
  WTI=CL=F, UST2Y = DGS2 carry/52 - 1.9*(delta-yield). Exposures are NEVER rewritten — only the
  realized/resolved fields are filled (tape-revision discipline: as-issued means as-issued).

The tape is the BINDING gate: no capital treats the universe Sortino 4.13 as real until this tape
accumulates its evidence window (>=12 resolved non-overlapping weeks, per the standing rule).
"""
import os, importlib.util, io
import numpy as np, pandas as pd
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
TAPE = os.path.join(REP, 'universe_forward_tape.csv')


def _l(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


zw = _l('zw', 'zion_weekly.py')


def wk_ret(ticker, w0, w1):
    s = zw.yahoo_weekly(ticker)
    if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    a = s.asof(w0); b = s.asof(w1)
    return float(b / a - 1.0) if (np.isfinite(a) and np.isfinite(b) and a > 0) else np.nan


def t2_ret(w0, w1):
    raw = zw.fetch('https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2')
    d = pd.read_csv(io.BytesIO(raw)); d.columns = ['date', 'val']; d['date'] = pd.to_datetime(d['date'])
    d['val'] = pd.to_numeric(d['val'], errors='coerce'); s = d.set_index('date')['val'].dropna()
    y0, y1 = s.asof(w0), s.asof(w1)
    return float(y0 / 100 / 52.0 - 1.9 * (y1 - y0) / 100.0) if np.isfinite(y0) and np.isfinite(y1) else np.nan


def main():
    if not os.path.exists(TAPE):
        print('no tape yet — run netting_ledger.py first'); return
    tape = pd.read_csv(TAPE)
    now = pd.Timestamp.now()
    n_res = 0
    for i, r in tape.iterrows():
        if str(r['status']) != 'ISSUED': continue
        w0 = pd.Timestamp(r['week_ending']); w1 = w0 + pd.Timedelta(days=7)
        if now < w1 + pd.Timedelta(days=1): continue          # not matured yet
        rets = dict(US_EQ=wk_ret('%5EGSPC', w0, w1), NASDAQ=wk_ret('QQQ', w0, w1),
                    GOLD=wk_ret('GC%3DF', w0, w1), SILVER=wk_ret('SI%3DF', w0, w1),
                    WTI=wk_ret('CL%3DF', w0, w1), UST2Y=t2_ret(w0, w1))
        if any(np.isnan(v) for k, v in rets.items() if abs(float(r[k])) > 1e-9):
            print(f'  {r["week_ending"]}: instrument data not ready — left ISSUED'); continue
        realized = sum(float(r[k]) * (0.0 if np.isnan(v) else v) for k, v in rets.items())
        tape.at[i, 'realized_ret'] = round(realized, 6)
        tape.at[i, 'status'] = 'RESOLVED'
        tape.at[i, 'resolved'] = now.strftime('%Y-%m-%d %H:%M')
        n_res += 1
        print(f'  RESOLVED {r["week_ending"]} -> {realized*100:+.2f}%')
    tape.to_csv(TAPE, index=False)
    res = tape[tape['status'] == 'RESOLVED']
    print(f'\ntape: {len(tape)} rows, {len(res)} resolved, {n_res} newly resolved.')
    if len(res):
        rr = pd.to_numeric(res['realized_ret'], errors='coerce').dropna().to_numpy()
        hit = (rr > 0).mean()
        print(f'forward record: {len(rr)} wks, {hit*100:.0f}% positive, cum {(np.prod(1+rr)-1)*100:+.2f}%'
              f'   (evidence window: {len(rr)}/12 weeks)')


if __name__ == '__main__':
    main()

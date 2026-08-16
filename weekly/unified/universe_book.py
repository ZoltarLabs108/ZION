"""
universe_book.py — AMENDMENT 1 (7.5% always-on gold overlay) + the ZION-UNIVERSE combined book
(weekly locked book x monthly SYZYGY base, 50/50, both-bases reporting).

Operator rulings 2026-08-16: gold w=0.075 always-on (structural PP inflation leg, no signal claim;
inside the declared 2.5-10% grid); cross-cadence combination adopted at the naive 50/50 (zero
selection DOF). Per-instrument netting flagged as the remaining production step before shared capital.
"""
import os, importlib.util
import numpy as np, pandas as pd
WT = '/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
W_GOLD, W_MICRO, DD_CAP = 0.075, 0.05, 0.10


def _l(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(WT, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def stats(r, per):
    r = np.asarray(r, float); e = np.cumprod(1 + r)
    cagr = e[-1] ** (per / len(r)) - 1
    dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2)); so = float(np.mean(r) / dn * np.sqrt(per)) if dn > 0 else np.nan
    dd = float((e / np.maximum.accumulate(e) - 1).min())
    return cagr, so, dd


zw = _l('zw', 'zion_weekly.py')
lk = pd.read_csv(os.path.join(REP, 'locked_book.csv')); lk['Date'] = pd.to_datetime(lk['Date'])
cal = pd.DatetimeIndex(lk['Date'])
locked = lk['locked'].to_numpy(float); micro = lk['silver_micro'].to_numpy(float)

g = zw.yahoo_weekly('GC=F')
if isinstance(g, pd.DataFrame): g = g['Close'] if 'Close' in g.columns else g.iloc[:, 0]
g.index = pd.to_datetime(g.index)
gp = g.reindex(cal, method='nearest', tolerance=pd.Timedelta('4D')).ffill().to_numpy(float)
gr = np.zeros(len(gp)); gr[1:] = np.nan_to_num(gp[1:] / gp[:-1] - 1.0)

# AMENDMENT 1 weekly book: locked + 5% silver micro + 7.5% gold always-on
wk = locked + W_MICRO * micro + W_GOLD * gr
c0, s0, d0 = stats(wk, 52)
lev = min(3.0, DD_CAP / abs(d0))
cl, sl_, dl = stats(lev * wk, 52)
print(f"AMENDMENT 1 — weekly book + 7.5% gold (weekly basis):")
print(f"  unlev : CAGR {c0*100:5.2f}%  Sortino {s0:.2f}  MaxDD {d0*100:5.1f}%")
print(f"  @cap  : {lev:.3f}x -> CAGR {cl*100:5.2f}%  Sortino {sl_:.2f}  MaxDD {dl*100:5.1f}%")

# ZION-UNIVERSE: aggregate weekly to monthly, combine 50/50 with monthly SYZYGY base
wser = pd.Series(lev * wk, index=cal)
wmon = (1 + wser).groupby(wser.index.to_period('M')).prod() - 1
m = pd.read_csv('/Users/castaglia/Desktop/ZION/reports/book_ledger.csv'); m['date'] = pd.to_datetime(m['date'])
mmon = m.set_index('date')['book_r_base']; mmon.index = mmon.index.to_period('M')
idx = wmon.index.intersection(mmon.index)
a = wmon.reindex(idx).to_numpy(float); b = mmon.reindex(idx).to_numpy(float)
ok = np.isfinite(a) & np.isfinite(b); a, b = a[ok], b[ok]
uni = 0.5 * a + 0.5 * b
print(f"\nZION-UNIVERSE BOOK (50/50 weekly x monthly, {len(a)} months, monthly basis):")
print(f"  corr(weekly, monthly) = {np.corrcoef(a, b)[0,1]:+.2f}")
for nm, r in [('weekly (amended, monthly agg)', a), ('monthly SYZYGY base', b), ('UNIVERSE 50/50', uni)]:
    c, s, d = stats(r, 12)
    print(f"  {nm:30s} CAGR {c*100:5.2f}%  Sortino {s:5.2f}  MaxDD {d*100:6.1f}%")
yr = pd.Series(uni, index=idx[ok].to_timestamp())
ya = (1 + yr).groupby(yr.index.year).prod() - 1
print(f"  universe years positive: {(ya>0).mean()*100:.0f}%  worst {ya.min()*100:+.1f}% ({ya.idxmin()})")
print("  " + "  ".join(f"{y}:{v*100:+.1f}%" for y, v in ya.items()))
pd.DataFrame({'month': idx[ok].astype(str), 'weekly': a, 'monthly': b, 'universe': uni}).to_csv(
    os.path.join(REP, 'zion_universe_book.csv'), index=False)
print(f"\n[dumped] reports/zion_universe_book.csv")

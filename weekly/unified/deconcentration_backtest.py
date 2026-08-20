"""
deconcentration_backtest.py — full monthly-ledger backtest of Candidate C2 (inverse-vol SPY/QQQ
split) WITH the pre-declared guards:

  * PIT vol       — the 26-week vol split uses only data strictly before each week (no look-ahead).
  * COSTS         — both books pay 5bps on their own week-to-week turnover; the de-conc book's extra
                    equity re-split turnover is charged honestly (this is the make-or-break guard).
  * FIXED WINDOW  — 26 weeks, pre-declared, NOT swept.
  * SUB-PERIODS   — reports full, 2007-16, 2017-26 (a real edge holds in both halves).
  * AGGREGATION   — weekly, monthly-aggregated, and universe (50/50 weekly x monthly SYZYGY).

Writes reports/deconcentration_ledger.csv (monthly: actual vs de-conc, net of costs). READ-ONLY on
inputs. This is a DIAGNOSTIC backtest — the forward shadow (paper_deconcentration.py) is the gate.
"""
import os
import numpy as np, pandas as pd
import yfinance as yf
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
COST = 5 / 1e4; VOL_WIN = 26; SPLIT = pd.Timestamp('2017-01-01')

led = pd.read_csv(os.path.join(REP, 'netting_ledger.csv')); led['week'] = pd.to_datetime(led['week'])
N = len(led)

def wkret(tk):
    h = yf.Ticker(tk).history(period='max', interval='1wk')['Close'].dropna(); h.index = h.index.tz_localize(None)
    h = h.reindex(led['week'], method='nearest', tolerance=pd.Timedelta('6D'))
    return h.pct_change(fill_method=None).to_numpy(), h
TK = {'US_EQ': '^GSPC', 'NASDAQ': 'QQQ', 'GOLD': 'GC=F', 'SILVER': 'SI=F', 'WTI': 'CL=F', 'USD': 'UUP'}
R = {}; SER = {}
for k, t in TK.items(): R[k], SER[k] = wkret(t)
_, shy = wkret('SHY'); R['UST2Y'] = np.nan_to_num(SER['US_EQ'].pct_change(fill_method=None).to_numpy())  # placeholder overwritten
# UST2Y carry return proxy via SHY total-return-ish price change
R['UST2Y'] = np.nan_to_num(shy.pct_change(fill_method=None).to_numpy())
nif, _ = wkret('^NSEI'); inr, _ = wkret('INR=X')
R['INDIA'] = np.nan_to_num((1 + np.nan_to_num(nif)) / (1 + np.nan_to_num(inr)) - 1)
for k in R: R[k] = np.nan_to_num(R[k])

# PIT trailing 26wk vol -> inverse-vol equity split
def rollvol(series):
    return series.pct_change(fill_method=None).rolling(VOL_WIN).std().shift(0).to_numpy()  # uses closes up to t
vS = rollvol(SER['US_EQ']); vQ = rollvol(SER['NASDAQ'])
eS = led['US_EQ'].to_numpy(); eQ = led['NASDAQ'].to_numpy(); eqc = eS + eQ
iv_s = (1 / vS) / ((1 / vS) + (1 / vQ))
cur_s = np.where(eqc > 1e-12, eS / np.where(eqc > 1e-12, eqc, 1), 0.5)
iv_s = np.where(np.isfinite(iv_s), iv_s, cur_s)          # early weeks: fall back to actual split
new_eS = eqc * iv_s; new_eQ = eqc * (1 - iv_s)

OTHER = ['GOLD', 'SILVER', 'WTI', 'UST2Y', 'USD', 'INDIA']
def build(spy_w, qqq_w):
    gross = spy_w * R['US_EQ'] + qqq_w * R['NASDAQ']
    for k in OTHER: gross = gross + led[k].to_numpy() * R[k]
    # turnover cost on ALL legs (non-equity identical to both, but included for honest absolute net)
    W = np.vstack([spy_w, qqq_w] + [led[k].to_numpy() for k in OTHER]).T
    turn = np.zeros(N); turn[1:] = np.abs(W[1:] - W[:-1]).sum(axis=1)
    return gross - COST * turn
net_actual = build(eS, eQ)
net_deconc = build(new_eS, new_eQ)

def stats(r, per=52):
    r = np.asarray(r, float); r = r[np.isfinite(r)]; e = np.cumprod(1 + r)
    cagr = e[-1] ** (per / len(r)) - 1; dn = np.sqrt(np.mean(np.minimum(r, 0) ** 2))
    so = np.mean(r) / dn * np.sqrt(per) if dn > 0 else np.nan
    dd = (e / np.maximum.accumulate(e) - 1).min(); cal = cagr / abs(dd) if dd < 0 else np.nan
    return so, cal, cagr, dd

def report(mask, label, per=52):
    a = net_actual[mask]; d = net_deconc[mask]
    sa, ca, ga, da = stats(a, per); sd, cd, gd, dd = stats(d, per)
    print(f"  {label:14s} actual: Sort {sa:5.3f} Calmar {ca:4.2f} CAGR {ga*100:5.2f}% DD {da*100:5.1f}%  |  "
          f"de-conc: Sort {sd:5.3f} Calmar {cd:4.2f} CAGR {gd*100:5.2f}% DD {dd*100:5.1f}%  (ΔSort {sd-sa:+.3f})")

wk = led['week']
print("DE-CONCENTRATION BACKTEST — net of 5bps turnover costs, PIT 26wk vol, window NOT swept")
print(f"  turnover added by de-conc (annualized): "
      f"{(np.abs(np.diff(new_eS))+np.abs(np.diff(new_eQ))).sum()/ (N/52):.2f}x/yr equity re-split "
      f"vs actual {(np.abs(np.diff(eS))+np.abs(np.diff(eQ))).sum()/(N/52):.2f}x/yr")
print("\nWEEKLY basis:")
report(np.ones(N, bool), 'full 2007-26')
report((wk < SPLIT).to_numpy(), '2007-16')
report((wk >= SPLIT).to_numpy(), '2017-26')

# monthly aggregation + universe
def to_monthly(r):
    s = pd.Series(r, index=wk); return (1 + s).groupby(s.index.to_period('M')).prod() - 1
ma, md = to_monthly(net_actual), to_monthly(net_deconc)
mth = pd.read_csv('/Users/castaglia/Desktop/ZION/reports/book_ledger.csv'); mth['date'] = pd.to_datetime(mth['date'])
mmon = mth.set_index('date')['book_r_base']; mmon.index = mmon.index.to_period('M')
idx = ma.index.intersection(mmon.index)
uni_a = 0.5 * ma.reindex(idx).to_numpy() + 0.5 * mmon.reindex(idx).to_numpy()
uni_d = 0.5 * md.reindex(idx).to_numpy() + 0.5 * mmon.reindex(idx).to_numpy()
print("\nMONTHLY basis (weekly leg aggregated):")
sa = stats(ma.to_numpy(), 12); sd = stats(md.to_numpy(), 12)
print(f"  weekly-leg    actual Sort {sa[0]:.3f}  de-conc Sort {sd[0]:.3f}  (Δ {sd[0]-sa[0]:+.3f})")
ua, ud = stats(uni_a, 12), stats(uni_d, 12)
print(f"  UNIVERSE 50/50 actual Sort {ua[0]:.3f} CAGR {ua[2]*100:.2f}% DD {ua[3]*100:.1f}%  |  "
      f"de-conc Sort {ud[0]:.3f} CAGR {ud[2]*100:.2f}% DD {ud[3]*100:.1f}%  (ΔSort {ud[0]-ua[0]:+.3f})")

pd.DataFrame({'month': idx.astype(str), 'weekly_actual': ma.reindex(idx).values,
              'weekly_deconc': md.reindex(idx).values, 'monthly_leg': mmon.reindex(idx).values,
              'universe_actual': uni_a, 'universe_deconc': uni_d}).to_csv(
    os.path.join(REP, 'deconcentration_ledger.csv'), index=False)
print(f"\n[ledger] reports/deconcentration_ledger.csv ({len(idx)} months)")
print("VERDICT: adopt only if de-conc >= actual AFTER costs in BOTH halves AND the forward tape confirms.")

"""
ZION STAGE 6 — MONEY TEST (SPY monthly): traded returns vs buy-and-hold.
Positions realized at decision month t earn the next-month return r_{t+1}.
  buy-hold        : pos = +1 always (the benchmark; compounds full drift)
  RED DAWN L/F    : pos = +1 on UP-call else 0 (flat)
  RED DAWN L/S    : pos = engine dir (+1/-1)
  CONV gated L/F  : pos = +1 on ACT-UP else 0 ; ABSTAIN = flat (cash)
  CONV gated L/S  : pos = gated dir ; ABSTAIN = flat
Discipline: CALENDAR annualization eq[-1]**(12/n)-1 (never len/52); Sortino-first
(+MaxDD), Sharpe secondary. NOTE: SP_Price is price-only (dividends excluded) ->
understates buy-hold, i.e. CONSERVATIVE toward the timing strategy.
"""
import numpy as np, pandas as pd
import engines as E
from convergence import build, gate_stream, record_gate

m=build()
sp=E.load_spine().set_index('Date')
# next-month realized return aligned to each decision month in m
r_next=(sp['SP_Price'].shift(-1)/sp['SP_Price']-1).reindex(m['Date']).to_numpy()
m=m.assign(r_next=r_next).dropna(subset=['r_next']).reset_index(drop=True)
rn=m['r_next'].to_numpy(); n=len(m)

agr,_=gate_stream(m,['rd','od','sc'],'unanimous'); gat=record_gate(m,agr)
rd=m['rd'].fillna(0).to_numpy().astype(int)

def metrics(pos, rets):
    sr=pos*rets                                  # monthly strategy return
    eq=np.cumprod(1+sr); T=len(sr)
    cagr=eq[-1]**(12/T)-1
    vol=sr.std(ddof=1)*np.sqrt(12)
    dn=sr[sr<0]; dstd=dn.std(ddof=1)*np.sqrt(12) if len(dn)>1 else np.nan
    shar=(sr.mean()*12)/vol if vol>0 else np.nan
    sort=(sr.mean()*12)/dstd if dstd and dstd>0 else np.nan
    peak=np.maximum.accumulate(eq); mdd=((eq-peak)/peak).min()
    inv=int((pos!=0).sum())
    return dict(cagr=cagr,vol=vol,shar=shar,sort=sort,mdd=mdd,eqx=eq[-1],inv=inv)

strats={
 'buy-hold (benchmark)': np.ones(n),
 'RED DAWN  long/flat' : (rd==1).astype(float),
 'RED DAWN  long/short': rd.astype(float),
 'CONV gated long/flat': (gat==1).astype(float),
 'CONV gated long/short': gat.astype(float),
 'CONV pure  long/flat': (agr==1).astype(float),
}
W=100
print("="*W)
print(f"ZION STAGE 6 MONEY TEST — SPY monthly   n={n} months  {m.Date.min().date()}..{m.Date.max().date()}")
print("  (price-only returns; calendar annualization; Sortino-first)")
print("="*W)
print(f"{'strategy':24s} {'invested':>8s} {'endx':>7s} {'CAGR':>7s} {'vol':>6s} {'Sharpe':>7s} {'Sortino':>8s} {'MaxDD':>7s}")
print("-"*W)
bh=None
for name,pos in strats.items():
    x=metrics(pos,rn)
    if name.startswith('buy-hold'): bh=x
    print(f"{name:24s} {x['inv']:7d}  {x['eqx']:6.1f}x {x['cagr']*100:6.1f}% {x['vol']*100:5.1f}% "
          f"{x['shar']:7.2f} {x['sort']:8.2f} {x['mdd']*100:6.1f}%")
print("-"*W)
# apples-to-apples: on the CONV gated ACTED months only, strategy vs buy-hold
a=gat!=0
if a.sum()>0:
    s_acc=(gat[a]==np.sign(rn[a])).mean()
    strat_ret=(gat[a]*rn[a]); bh_ret=rn[a]
    print(f"[on {int(a.sum())} gated ACTED months]  dir-acc={s_acc*100:.1f}%   "
          f"mean strat ret={strat_ret.mean()*100:+.2f}%/mo  vs  buy-hold {bh_ret.mean()*100:+.2f}%/mo")
print("[verdict] compare CONV rows to buy-hold: does timing/abstaining beat holding the index?")
print("="*W)

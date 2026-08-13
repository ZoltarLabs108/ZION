"""
ZION book — SPY-anchored 50/20/15/15 weighting, base (1x) and 2.5x leverage.
Honest metrics from the per-sleeve monthly-return ledger (type-level 'without_cells' base
system). Sortino is leverage-invariant; CAGR/MaxDD computed on the actual compounded path
(so variance drag + drawdown scaling at 2.5x are real, not hand-waved).
"""
import pandas as pd, numpy as np
L=pd.read_csv("/Users/castaglia/Desktop/ZION_MULTIASSET/reports/per_sleeve_ledger.csv")
L["date"]=pd.to_datetime(L["date"])
base=L[L["variant"]=="without_cells"].copy()          # type-level base system (honest)
W={"SPY":0.50,"Gold":0.20,"Silver":0.15,"WTI":0.15,"USD":0.0}
# normalize sleeve names
base["sleeve"]=base["sleeve"].str.replace("SP500","SPY").str.replace("S&P500","SPY")
piv=base.pivot_table(index="date",columns="sleeve",values="monthly_return",aggfunc="sum").fillna(0.0)
for s in W:
    if s not in piv.columns: piv[s]=0.0
book=sum(piv[s]*w for s,w in W.items())               # weighted monthly book return (abstain=cash=0)
book=book.sort_index()

def metrics(r):
    r=np.asarray(r,float); n=len(r)
    eq=np.cumprod(1+r); cagr=eq[-1]**(12/n)-1
    ddN=np.sqrt((np.minimum(r,0)**2).mean())            # canonical: target-downside-dev / total N
    sortino=r.mean()/ddN*np.sqrt(12) if ddN>0 else float('nan')
    dn=r[r<0]; ddK=np.sqrt((dn**2).mean()) if len(dn) else 1e-9  # alt: over down-months only
    sortino_alt=r.mean()/ddK*np.sqrt(12)
    peak=np.maximum.accumulate(eq); mdd=((eq-peak)/peak).min()
    calmar=cagr/abs(mdd) if mdd<0 else float('nan')
    return dict(n=n,cagr=cagr,permo=r.mean(),sortino=sortino,sortino_alt=sortino_alt,mdd=mdd,calmar=calmar)

def show(label,r):
    for L_ in (1.0,2.5):
        m=metrics(r*L_)
        print(f"  {label:12s} {L_:>3.1f}x | CAGR {m['cagr']*100:6.2f}%  {m['permo']*100:+5.2f}%/mo"
              f"  Sortino {m['sortino']:5.2f} (alt {m['sortino_alt']:4.2f})  MaxDD {m['mdd']*100:6.1f}%  Calmar {m['calmar']:4.2f}  n={m['n']}")

print("="*94)
print("ZION BOOK — SPY-anchored 50/20/15/15 (base type-level system)   base 1x  vs  2.5x leverage")
print("="*94)
last10=book[book.index>=book.index.max()-pd.DateOffset(years=10)]
print("FULL (1990->):")
show("full-1990",book.values)
print("LAST 10 YEARS:")
show("last-10yr",last10.values)
print("-"*94)
print(f"months: full={len(book)}  last10={len(last10)}   Sortino is leverage-invariant (by construction).")
print("NOTE: last-10yr is in-sample & bull-flattered; Silver/WTI legs ride PROPOSED ratios.")

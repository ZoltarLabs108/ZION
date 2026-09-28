"""Integrated Health Care instrument (operator 13 Sep): type pulls (system, precedence 1) + post-type remainder cascade
(precedence 2) + pre-type tier-2 on months where the type system ran but was silent (precedence 3; warm-up months excluded).
Divergence (type acts, tier-2 disagrees): the type call stands (system authority); variant with abstain-on-divergence reported."""
import pandas as pd, numpy as np, json
J=pd.read_csv("results/stage3_hc/convergence_type_vs_tier.csv"); A=pd.read_csv("results/stage3_hc/HealthCare_month_level.csv")
def wlb(p,n,z=1.96): return (p+z*z/(2*n)-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n) if n else 0
J=J.merge(A[["date","reason"]],on="date",how="left")
def integrate(r, abstain_on_diverge=False):
    if r.type_call!=0:
        if abstain_on_diverge and r.tier_call2!=0 and r.tier_call2!=r.type_call: return 0, "diverge-abstain"
        return r.type_call, "type-pull" if r.type_state=="pull" else "post-type-cascade"
    if r.tier_call2!=0 and r.type_state!="warm-up": return r.tier_call2, "pre-type-tier2"
    return 0, "abstain"
for var,flag in (("INTEGRATED (type authority on divergence)",False),("variant: abstain on divergence",True)):
    J[["call","source"]]=J.apply(lambda r: pd.Series(integrate(r,flag)),axis=1)
    a=J[J.call!=0]; acc=(a.call==a.lab).mean(); n=len(a)
    print(f"\n{var}: acted {n}/62 ({n/62:.0%}) acc {acc:.1%} LB95 {wlb(acc,n):.1%} | up-rate acted {(a.lab>0).mean():.0%} (unconditional 60%) | long share {(a.call>0).mean():.0%}")
    L=a[a.call>0]; S=a[a.call<0]; print(f"   LONG {len(L)}: months up {(L.lab>0).mean():.0%} | SHORT {len(S)}: months down {(S.lab<0).mean():.0%}")
    print("   by source:", {s:(len(g), f"{(g.call==g.lab).mean():.0%}") for s,g in a.groupby("source")})
    print("   by year:", {int(y):f"{(g.call==g.lab).mean():.0%}/{len(g)}" for y,g in a.groupby(pd.to_datetime(a.date).dt.year)})
    if not flag: I=J.copy()
t=J[J.type_call!=0]; print(f"\nTYPE-ONLY system for comparison: acted {len(t)}/62 acc {(t.type_call==t.lab).mean():.1%} LB95 {wlb((t.type_call==t.lab).mean(),len(t)):.1%}")
# money test on the integrated ledger (2021-03 -> 2026-07): XLV next-month returns
S="/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/"
px=pd.read_csv(S+"XLV_daily.csv",index_col=0,parse_dates=True)["Adj Close"].resample("MS").first(); spy=pd.read_csv(S+"SPY_daily.csv",index_col=0,parse_dates=True)["Adj Close"].resample("MS").first()
d=pd.to_datetime(I.date); r=px.pct_change().shift(-1).reindex(d).values; rs=spy.pct_change().shift(-1).reindex(d).values
def stats(x):
    x=np.asarray(x,float); x=x[~np.isnan(x)]; n=len(x); c=np.prod(1+x)**(12/n)-1; dn=x[x<0]; so=(x.mean()*12)/(dn.std(ddof=1)*np.sqrt(12)) if len(dn)>1 else np.nan; eq=np.cumprod(1+x); dd=(eq/np.maximum.accumulate(eq)-1).min(); return c,so,dd
calls=I.call.values; tcalls=I.type_call.values
pers=[];pos=0
for c,x in zip(calls,r):
    if c!=0: pos=c
    pers.append(pos*x)
print("\nMONEY TEST 2021-03 -> 2026-07 (XLV next-month returns, no costs)")
for nm,x in (("buy&hold XLV",r),("buy&hold SPY",rs),("type-only: two-sided on call, flat else",tcalls*r),("INTEGRATED: two-sided on call, flat else",calls*r),("INTEGRATED long/flat (shorts -> flat)",np.where(calls>0,1,0)*r),("INTEGRATED + persistence (hold last call)",np.array(pers))):
    c,so,dd=stats(x); print(f"   {nm:44s} CAGR {c*100:6.2f}%  Sortino {so:5.2f}  MaxDD {dd*100:6.1f}%")
I.to_csv("results/stage3_hc/integrated_ledger.csv",index=False)
print("\ncurrent (2026-08 row):", I.tail(1)[["date","type_state","tier","call","source"]].values.tolist())

"""Type pulls (system) vs pre-type CAPE10-velocity tier (parallel instrument): overlap / convergence / divergence, and what each
joint state predicts for next-month direction. Both records are sequential one-step-ahead OOS at H=1 (Stage 3 runs)."""
import pandas as pd, numpy as np, json
A=pd.read_csv("results/stage3_hc/HealthCare_month_level.csv"); P=pd.read_csv("results/stage3_hc_pretype/HealthCare_month_level.csv")
def wlb(p,n,z=1.96): return (p+z*z/(2*n)-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n) if n else 0
A["type_call"]=np.where(A.status=="pulled",A.base_dir,np.where(A.status=="emitted",A.predB,0)).astype(float)
A["type_state"]=np.where(A.status=="pulled","pull",np.where(A.status=="emitted","remainder-cascade",np.where(A.reason=="train<MIN_TRAIN","warm-up","abstain")))
P["tier_call2"]=np.where((P.status=="emitted")&(P.tier=="tier2"),P.predB,0).astype(float)      # predictive tier only
P["tier_callall"]=np.where(P.status=="emitted",P.predB,0).astype(float)                         # every emission (tier4 = coin)
J=A[["date","lab","scored","type_call","type_state"]].merge(P[["date","tier_call2","tier_callall","tier"]],on="date",how="outer").sort_values("date")
J=J[J.scored==True].copy(); J["lab"]=J.lab.astype(int)
def state(r,tc):
    t=r.type_call; s=r[tc]
    if t!=0 and s!=0: return "CONVERGE (agree)" if t==s else "DIVERGE (disagree)"
    if t!=0: return "TYPE only"
    if s!=0: return "TIER only"
    return "NEITHER"
out={}
for tc,label in (("tier_call2","tier-2 only (predictive tier)"),("tier_callall","all tier emissions (incl. tier-4)")):
    J["state"]=J.apply(lambda r: state(r,tc),axis=1)
    print(f"\n=== tier instrument = {label} ===  (62 scored months, 2021-03 -> 2026-07)")
    print(f"{'state':20s} {'n':>3s} {'up%':>6s} | {'type acc':>8s} {'LB95':>6s} | {'tier acc':>8s} {'LB95':>6s} | {'agreed/act call acc':>19s} {'LB95':>6s} | clears LB>50")
    rows=[]
    for st in ["CONVERGE (agree)","DIVERGE (disagree)","TYPE only","TIER only","NEITHER"]:
        g=J[J.state==st]; n=len(g)
        if n==0: print(f"{st:20s}   0"); rows.append(dict(state=st,n=0)); continue
        up=(g.lab>0).mean()
        ta=(g.type_call==g.lab).mean() if (g.type_call!=0).any() else np.nan; tn=int((g.type_call!=0).sum())
        sa=(g[tc]==g.lab).mean() if (g[tc]!=0).any() else np.nan; sn=int((g[tc]!=0).sum())
        act=np.where(g.type_call!=0,g.type_call,g[tc]); aa=(act==g.lab).mean() if st!="NEITHER" else np.nan; an=n if st!="NEITHER" else 0
        lb=wlb(aa,an) if an else np.nan
        print(f"{st:20s} {n:3d} {up*100:5.0f}% | {ta*100 if tn else float('nan'):7.1f}% {wlb(ta,tn)*100 if tn else 0:5.0f}% | {sa*100 if sn else float('nan'):7.1f}% {wlb(sa,sn)*100 if sn else 0:5.0f}% | {aa*100 if an else float('nan'):18.1f}% {lb*100 if an else 0:5.0f}% | {'YES' if an and lb>0.5 else ('no' if an else '—')}")
        rows.append(dict(state=st,n=n,up=up,type_acc=ta if tn else None,tier_acc=sa if sn else None,act_acc=aa if an else None,act_lb=lb if an else None))
    both=J[J.state.str.startswith(("CONVERGE","DIVERGE"))]
    print(f"overlap: both act on {len(both)} months; of the type's {int((J.type_call!=0).sum())} acted months the tier also acts on {int(((J.type_call!=0)&(J[tc]!=0)).sum())}; of the tier's {int((J[tc]!=0).sum())} acted months the type also acts on {int(((J.type_call!=0)&(J[tc]!=0)).sum())}")
    if len(both): print(f"agreement rate when both act: {(both.state=='CONVERGE (agree)').mean():.0%}")
    out[label]=rows
    if tc=="tier_call2": J2=J.copy()
# combined instrument: act on CONVERGE + TYPE only + TIER only (union), abstain on DIVERGE / NEITHER
u=J2[J2.state.isin(["CONVERGE (agree)","TYPE only","TIER only"])]; act=np.where(u.type_call!=0,u.type_call,u.tier_call2); ua=(act==u.lab).mean()
c=J2[J2.state=="CONVERGE (agree)"]; ca=(c.type_call==c.lab).mean()
print(f"\nUNION instrument (act unless diverge/neither): {len(u)}/62 months, acc {ua:.1%}, LB95 {wlb(ua,len(u)):.1%}, up-rate {(u.lab>0).mean():.0%}")
print(f"CONVERGENCE-ONLY instrument: {len(c)}/62 months, acc {ca:.1%}, LB95 {wlb(ca,len(c)):.1%}, up-rate {(c.lab>0).mean():.0%}")
print("\ndivergent months:", [(r.date, int(r.type_call), int(r.tier_call2), r.lab) for r in J2[J2.state=="DIVERGE (disagree)"].itertuples()])
print("current rows:", A[["date","type_state","type_call"]].tail(1).values.tolist(), P[["date","tier","tier_call2"]].tail(1).values.tolist())
J2.to_csv("results/stage3_hc/convergence_type_vs_tier.csv",index=False); json.dump(out,open("results/stage3_hc/convergence_summary.json","w"),indent=1,default=float)

"""
ZION Stage 3 — full in-fold walk-forward DISCOVERY SWEEP over GROUNDED Gold pairs.
Same clean discipline as the prototype:
  1-mo direction target, t-3 embargo, expanding window, 27-type grammar fit
  INSIDE each fold only, Wilson-LB>=0.45 admit, abstain-by-default, NO house-wide pick.
HONESTY UPGRADE vs prototype: revision-heavy mid-month series (Industrial_Production,
  M2_Money) are lagged 1 month (PIT publication-lag) so a 1st-of-month decision only
  uses data actually public by then. This is exactly why IndProd was 'banned' before.
Ranks every pair by OOS Wilson lower bound. Flags the contaminated kept-set.
"""
import pandas as pd, numpy as np
from itertools import combinations

PANEL = "/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
GATE, MIN_N, FLAT, MIN_TRAIN, Z = 0.45, 8, 0.5, 120, 1.96
GROUNDED = ['Dollar_Index','M2_Money','Industrial_Production','GS10_Rate','Fed_Funds_Rate',
            'US_2Y_Treasury','Copper_Close','WTI_Crude_Close','Gold_Close','Term_Spread_10Y_2Y']
LAGGED = {'Industrial_Production','M2_Money'}          # publish mid-month -> lag 1 (PIT)
KEPT = {frozenset(('Industrial_Production','GS10_Rate')),
        frozenset(('Industrial_Production','Fed_Funds_Rate')),
        frozenset(('M2_Money','Term_Spread_10Y_2Y'))}  # contaminated kept-set (frozen)
MIN_ACTED = 30

def wilson_lb(k, n, z=Z):
    if n == 0: return 0.0
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); m=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (c-m)/d

def tern(x, mu, sd):
    if sd==0 or np.isnan(sd): return np.zeros_like(x,dtype=int)
    z=(x-mu)/sd; o=np.zeros_like(z,dtype=int); o[z>FLAT]=1; o[z<-FLAT]=-1; return o

def run_pair(A,B,G):
    m=np.isfinite(A)&np.isfinite(B)&np.isfinite(G)
    A,B,G=A[m],B[m],G[m]; n=len(G)
    if n < MIN_TRAIN+10: return None
    ret=np.full(n,np.nan); ret[:-1]=G[1:]/G[:-1]-1.0; y=np.sign(ret)
    dA=np.diff(A,prepend=A[0]); dB=np.diff(B,prepend=B[0])
    preds=[]
    for t in range(MIN_TRAIN+3, n-1):
        tr=np.arange(0,t-2); tr=tr[np.isfinite(y[tr])]
        if len(tr)<MIN_TRAIN: continue
        sdA=A[tr].std(); sdB=B[tr].std()
        if sdA==0 or sdB==0: continue
        s1,s2,s3=dA,dB,dA/sdA-dB/sdB
        c1=tern(s1,s1[tr].mean(),s1[tr].std()); c2=tern(s2,s2[tr].mean(),s2[tr].std()); c3=tern(s3,s3[tr].mean(),s3[tr].std())
        cell=c1*9+c2*3+c3
        adm={}
        for c in np.unique(cell[tr]):
            idx=tr[cell[tr]==c]; yy=y[idx]; yy=yy[yy!=0]
            if len(yy)<MIN_N: continue
            up=(yy>0).sum(); dn=(yy<0).sum(); k=max(up,dn); nn=up+dn
            if wilson_lb(k,nn)>=GATE: adm[c]=1 if up>=dn else -1
        d=adm.get(cell[t])
        if d is not None and y[t]!=0: preds.append((d,int(y[t]),ret[t]))
    if len(preds)<MIN_ACTED: return dict(n=len(preds),under=True)
    P=np.array([p[0] for p in preds]); R=np.array([p[1] for p in preds]); gr=np.array([p[2] for p in preds])
    corr=(P==R).sum(); nact=len(P); acc=corr/nact; lb=wilson_lb(corr,nact)
    sr=P*gr; eq=np.cumprod(1+sr); cagr=eq[-1]**(12/nact)-1
    downs=sr[sr<0]; sortino=(sr.mean()/downs.std()*np.sqrt(12)) if len(downs) and downs.std()>0 else float('nan')
    peak=np.maximum.accumulate(eq); maxdd=((eq-peak)/peak).min()
    bh_up=(R>0).mean()
    return dict(n=nact,acc=acc,lb=lb,edge=acc-bh_up,cagr=cagr,sortino=sortino,maxdd=maxdd,under=False)

df=pd.read_csv(PANEL); df["Date"]=pd.to_datetime(df["Date"])
for c in LAGGED:
    df[c]=df[c].shift(1)                     # PIT publication lag
G=df["Gold_Close"].to_numpy(float)

rows=[]
for a,b in combinations(GROUNDED,2):
    if a=='Gold_Close' or b=='Gold_Close':
        pass  # gold-as-feature pairs allowed
    r=run_pair(df[a].to_numpy(float), df[b].to_numpy(float), G)
    if r is None: continue
    kept = frozenset((a,b)) in KEPT
    r.update(pair=f"{a} / {b}", kept=kept)
    rows.append(r)

good=[r for r in rows if not r.get('under')]
good.sort(key=lambda r:-r['lb'])
print(f"{'pair':40s} {'':2s} {'n':>4s} {'OOSacc':>7s} {'WilsonLB':>9s} {'edge':>7s} {'CAGR':>7s} {'Sortino':>8s} {'MaxDD':>7s}")
print("-"*100)
for r in good:
    flag='*' if r['kept'] else (' >' if r['lb']>=0.50 else '  ')
    print(f"{r['pair']:40s} {flag:2s} {r['n']:4d} {r['acc']*100:6.1f}% {r['lb']*100:8.1f}% {r['edge']*100:+6.1f}% {r['cagr']*100:6.1f}% {r['sortino']:8.2f} {r['maxdd']*100:6.1f}%")
print("-"*100)
und=[r for r in rows if r.get('under')]
print(f"pairs evaluated: {len(rows)}   ranked(acted>={MIN_ACTED}): {len(good)}   too-few-acted/abstain: {len(und)}")
print(f"survivors WilsonLB>=50%: {sum(1 for r in good if r['lb']>=0.50)}   ('*'=contaminated kept-set, '>'=clears LB50)")
print("Discipline: t-3 embargo, in-fold 27-type fit, Wilson-LB>=0.45 admit, abstain-by-default; IndProd & M2 PIT-lagged 1mo.")

"""
ZION STAGE 3 DIAGNOSTIC — 3-month-forward directional OOS (CORRECTED target).
target = sign(Gold[t+3]/Gold[t]-1); train rows s<=t-3 (labels resolve s+3<=t);
expanding window, roll monthly; 27-type grammar fit IN-FOLD; Wilson-LB>=0.45 admit;
abstain-by-default. Reports, per the operator diagnostic spec:
  (A) pair sweep ranked by 3-mo OOS Wilson-LB (+ overlap-adjusted LB, eff n=n/3)
  (B) for the top pair: % accuracy BY TYPE, O-value, O-score
  (C) accuracy + OOS BY TIER (types grouped by train-conviction quartile)
  (D) correlation between O-value and OOS accuracy across types
"""
import pandas as pd, numpy as np
from itertools import combinations

PANEL="/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
GATE,MIN_N,FLAT,MIN_TRAIN,Z,H=0.45,8,0.5,120,1.96,3     # H=3-month horizon
START=np.datetime64('1990-01-01')                        # predictions begin 1990 (fixed OOS window)
GROUNDED=['Dollar_Index','M2_Money','Industrial_Production','GS10_Rate','Fed_Funds_Rate',
          'US_2Y_Treasury','WTI_Crude_Close','Gold_Close','Term_Spread_10Y_2Y']  # Copper dropped (2000-08 splice)
LAGGED={'Industrial_Production','M2_Money'}
MIN_ACTED=30

def wlb(k,n,z=Z):
    if n<=0: return 0.0
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); m=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)); return (c-m)/d
def tern(x,mu,sd):
    if sd==0 or np.isnan(sd): return np.zeros_like(x,int)
    z=(x-mu)/sd; o=np.zeros_like(z,int); o[z>FLAT]=1; o[z<-FLAT]=-1; return o

df=pd.read_csv(PANEL); df["Date"]=pd.to_datetime(df["Date"])
for c in LAGGED: df[c]=df[c].shift(1)
G=df["Gold_Close"].to_numpy(float)

DATES=df["Date"].to_numpy()
def prep(A,B):
    m=np.isfinite(A)&np.isfinite(B)&np.isfinite(G)
    return A[m],B[m],G[m],DATES[m]

def walk(A,B,g,dts,collect=False):
    n=len(g); ret3=np.full(n,np.nan)
    ret3[:-H]=g[H:]/g[:-H]-1.0; y=np.sign(ret3)      # 3-MONTH forward direction
    dA=np.diff(A,prepend=A[0]); dB=np.diff(B,prepend=B[0])
    rows=[]
    for t in range(MIN_TRAIN+H, n-H):
        if dts[t]<START: continue                          # predictions start 1990
        tr=np.arange(0,t-H+1); tr=tr[np.isfinite(y[tr])]   # labels resolve s+H<=t
        if len(tr)<MIN_TRAIN: continue
        sdA=A[tr].std(); sdB=B[tr].std()
        if sdA==0 or sdB==0: continue
        s1,s2,s3=dA,dB,dA/sdA-dB/sdB
        c1=tern(s1,s1[tr].mean(),s1[tr].std());c2=tern(s2,s2[tr].mean(),s2[tr].std());c3=tern(s3,s3[tr].mean(),s3[tr].std())
        cell=c1*9+c2*3+c3; adm={}; convn={}
        for c in np.unique(cell[tr]):
            idx=tr[cell[tr]==c]; yy=y[idx]; yy=yy[yy!=0]
            if len(yy)<MIN_N: continue
            up=(yy>0).sum();dn=(yy<0).sum();k=max(up,dn);nn=up+dn
            lb=wlb(k,nn)
            if lb>=GATE: adm[c]=1 if up>=dn else -1; convn[c]=lb
        d=adm.get(cell[t])
        if d is not None and y[t]!=0:
            rows.append((int(cell[t]),d,int(y[t]),abs(ret3[t]),convn[cell[t]]))
    return rows

# ---- (A) sweep ----
res=[]
for a,b in combinations(GROUNDED,2):
    A,B,g,dts=prep(df[a].to_numpy(float),df[b].to_numpy(float))
    if len(g)<MIN_TRAIN+2*H: continue
    r=walk(A,B,g,dts)
    if len(r)<MIN_ACTED: continue
    P=np.array([x[1] for x in r]);Y=np.array([x[2] for x in r])
    k=(P==Y).sum();n=len(P)
    up=(Y>0).mean(); base=max(up,1-up)                     # drift baseline: always-predict-majority
    edge=k/n-base                                          # skill above drift
    res.append((f"{a} / {b}",n,k/n,wlb(k,n),wlb(int(round(k/3)),int(round(n/3))),base,edge,a,b))
res.sort(key=lambda x:-x[6])                               # rank by EDGE over drift, not raw acc
print("="*112); print("ZION STAGE 3 DIAGNOSTIC — 3-MONTH-FORWARD OOS (Gold)  |  target=sign(Gold[t+3]/Gold[t]-1)"); print("="*112)
print("(A) PAIR SWEEP — ranked by EDGE over drift baseline (skill, not drift-capture)");
print(f"{'pair':40s} {'nOOS':>5s} {'OOS_acc':>8s} {'drift':>6s} {'EDGE':>6s} {'WilsonLB':>9s} {'LB_ovl':>7s}"); print("-"*112)
for nm,n,acc,lb,lbo,base,edge,a,b in res:
    flag='>' if (edge>0 and lbo>=0.50) else ' '
    print(f"{nm:40s} {n:5d} {acc*100:7.1f}% {base*100:5.1f}% {edge*100:+5.1f}% {lb*100:8.1f}% {lbo*100:6.1f}% {flag}")
print("-"*112)
print(f"pairs with EDGE>0 AND overlap-adj LB>=50%: {sum(1 for r in res if r[6]>0 and r[4]>=0.5)} / {len(res)}   (drift=always-predict-majority; EDGE=acc-drift)")

# ---- (B)(C)(D) top pair type/tier/o-score diagnostic ----
top=res[0]; a,b=top[7],top[8]
A,B,g,dts=prep(df[a].to_numpy(float),df[b].to_numpy(float)); rows=walk(A,B,g,dts,collect=True)
print("\n"+"="*104); print(f"(B) BY-TYPE + O-SCORE  |  top pair: {a} / {b}"); print("="*104)
by={}
for cell,d,y,aret,lb in rows: by.setdefault(cell,[]).append((d,y,aret,lb))
tot=len(rows); typerows=[]
for cell,v in by.items():
    n=len(v); k=sum(1 for d,y,ar,lb in v if d==y)
    if n<10: continue
    oos=k/n; bayes=(k+2)/(n+4); cov=n/tot
    aret_c=np.mean([ar for d,y,ar,lb in v if d==y]) if k>0 else 0.0
    ov=bayes*2*aret_c; osc=ov*cov; trlb=np.mean([lb for *_,lb in v])
    typerows.append((cell,n,oos,cov,aret_c,ov,osc,trlb))
typerows.sort(key=lambda r:-r[6])
print(f"{'type':>5s} {'nOOS':>5s} {'OOS_acc':>8s} {'cov':>6s} {'avgRet|ok':>9s} {'O-value':>8s} {'O-score':>8s} {'trainLB':>7s}"); print("-"*104)
for cell,n,oos,cov,ar,ov,osc,trlb in typerows:
    print(f"{cell:5d} {n:5d} {oos*100:7.1f}% {cov*100:5.1f}% {ar*100:8.1f}% {ov:8.3f} {osc:8.3f} {trlb*100:6.1f}%")
print("-"*104); print(f"TOTAL O-SCORE = {sum(r[6] for r in typerows):.3f}   (types with nOOS>=10)")

print("\n(C) BY-TIER — types grouped into 4 tiers by TRAIN conviction (Wilson-LB quartile)")
allc=sorted(rows,key=lambda x:-x[4])   # sort acted months by train conviction
q=len(allc)//4 if len(allc)>=4 else len(allc)
print(f"{'tier':>4s} {'nOOS':>5s} {'train_conv':>10s} {'OOS_acc':>8s} {'coverage':>8s}"); print("-"*104)
for ti in range(4):
    seg=allc[ti*q:(ti+1)*q] if ti<3 else allc[ti*q:]
    if not seg: continue
    k=sum(1 for d,y,ar,lb in [(x[1],x[2],x[3],x[4]) for x in seg] if d==y)
    n=len(seg); tc=np.mean([x[4] for x in seg])
    print(f"{ti+1:4d} {n:5d} {tc*100:9.1f}% {k/n*100:7.1f}% {n/tot*100:7.1f}%")
print("-"*104)

print("\n(D) O-VALUE vs OOS-ACCURACY across types")
if len(typerows)>=3:
    ov=np.array([r[5] for r in typerows]); oa=np.array([r[2] for r in typerows])
    r=np.corrcoef(ov,oa)[0,1]
    print(f"  Pearson corr(O-value, OOS_acc) = {r:+.3f}  over {len(typerows)} types")
    print("  interpretation: O-value blends accuracy x payoff-magnitude; if corr is weak/moderate,")
    print("  O-value/O-score is a PAYOFF-biased proxy for directional skill -> rank on Wilson-LB, not O-score.")
else:
    print("  too few types (nOOS>=10) to correlate.")
print("="*104)

"""
ZION — MIRROR-INVERSE / error-regime test (SPY).
Scoped (recipe): run ONLY on the ACTED months of the predictor. Here the predictor
is the Stage-4 convergence (pure-agreement acted set). Question: can any PIT candidate
flag, IN ADVANCE, which acted calls will be WRONG?
In-fold sequential: for each acted month t, using only PAST acted months (<t):
  - bucket the candidate (above/below trailing median = 2 states);
  - base_err = train error rate; state_err = train error rate within month t's bucket (n>=8);
  - FLAG month t if state_err > base_err + 0.10 .
PASS iff Wilson-LB(err | flagged over the whole stream) > overall base error rate.
If PASS -> reserve as error-testing regime / satellite (never sizes). Else FAIL.
"""
import numpy as np, pandas as pd
import engines as E
from convergence import build, gate_stream

Z=1.96
def wlb(k,n):
    if n<=0: return 0.0
    p=k/n; d=1+Z*Z/n; c=p+Z*Z/(2*n); mrg=Z*np.sqrt(p*(1-p)/n+Z*Z/(4*n*n)); return (c-mrg)/d

m=build()
# candidates (PIT): assemble from panel + derived
raw=pd.read_csv(E.PANEL); raw['Date']=pd.to_datetime(raw['Date'])
raw=raw[['Date','SP_Price','CAPE','GS10_Rate']].drop_duplicates('Date').sort_values('Date')
raw['gs10_chg6']=raw['GS10_Rate']-raw['GS10_Rate'].shift(6)
r=raw['SP_Price'].pct_change()
raw['vol12']=r.rolling(12).std()                      # trailing realized vol (causal)
m=m.merge(raw[['Date','CAPE','GS10_Rate','gs10_chg6','vol12']],on='Date',how='left',suffixes=('','_c'))

# acted set = 3-engine unanimous pure agreement
agr,_=gate_stream(m,['rd','od','sc'],'unanimous')
acted_mask=agr!=0
A=m[acted_mask].reset_index(drop=True); adir=agr[acted_mask]
y=A['y'].to_numpy(); err=(adir!=np.sign(y)).astype(int)   # 1 = call was WRONG
base_err=err.mean()
cands={'CAPE':A['CAPE_c'].to_numpy() if 'CAPE_c' in A else A['CAPE'].to_numpy(),
       'GS10_Rate':A['GS10_Rate'].to_numpy(),'gs10_chg6':A['gs10_chg6'].to_numpy(),
       'vol12':A['vol12'].to_numpy(),'SANC_conf':A['sc_c'].to_numpy(),'RD_conf':A['rd_c'].to_numpy()}

W=92
print("="*W)
print(f"MIRROR-INVERSE error-regime test — SPY  |  acted set = 3-eng unanimous pure ({len(A)} months)")
print(f"  overall base ERROR rate on acted set = {base_err*100:.1f}%   (target: flag a subset with HIGHER error)")
print("="*W)
print(f"{'candidate':12s} {'flagged':>7s} {'err|flag':>9s} {'LB(err)':>8s} {'base_err':>8s} {'verdict':>10s}")
print("-"*W)
MINSTATE=8
any_pass=False
for name,c in cands.items():
    flagged=np.zeros(len(A),bool)
    for t in range(len(A)):
        past=np.arange(t)
        past=past[~np.isnan(c[past])]
        if len(past)<20 or np.isnan(c[t]): continue
        med=np.median(c[past]); hi=c[past]>med
        be=err[past].mean()
        state_hi=c[t]>med
        sel=past[hi==state_hi]
        if len(sel)<MINSTATE: continue
        se=err[sel].mean()
        if se>be+0.10: flagged[t]=True
    nf=int(flagged.sum())
    if nf==0:
        print(f"{name:12s} {nf:7d} {'--':>9s} {'--':>8s} {base_err*100:7.1f}% {'no flags':>10s}"); continue
    ef=err[flagged].mean(); lb=wlb(int(err[flagged].sum()),nf)
    ok = lb>base_err
    any_pass=any_pass or ok
    print(f"{name:12s} {nf:7d} {ef*100:8.1f}% {lb*100:7.0f}% {base_err*100:7.1f}% {('PASS' if ok else 'FAIL'):>10s}")
print("-"*W)
print(f"[MIRROR VERDICT]  {'PASS — reserve flagged candidate as error-regime satellite' if any_pass else 'FAIL — no PIT candidate predicts the acted-call errors above base (LB) -> no error regime; move on'}")
print("="*W)

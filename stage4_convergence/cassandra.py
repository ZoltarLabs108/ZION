"""
ZION STAGE 14 — CASSANDRA (direction-conditional magnitude / PRICE range) + LIVE emission.
Produces the CURRENT-month call for SPY: each engine's live directional lean (trained on
all past, predicting next month), the convergence decision, and a 1-month-ahead PRICE band
from similarity-weighted historical analogues.

Recipe discipline (roadmap NO-FORCED-PREDICTION + CASSANDRA spec):
  - CASSANDRA is DIRECTION-CONDITIONAL: it hangs a range on the decided direction.
  - Publish a tier-conditioned RANGE only; VETO if it can't beat drift/zero.
  - The 10y same-dir fallback is NEVER emitted as a call.
  - Since SPY Stage-4 direction = ABSTAIN (no validated edge; placebo fails), the emitted
    call is ABSTAIN and the range below is DESCRIPTIVE CONTEXT, not a validated forecast.
"""
import numpy as np, pandas as pd
import engines as E

sp=E.load_spine()
p=sp['SP_Price'].to_numpy(float); dts=sp['Date'].to_numpy()
L=len(sp)-1                                   # live decision month (last row, nxt unknown)
spot=p[L]; live_date=pd.Timestamp(dts[L])
pct=np.concatenate([[np.nan],(p[1:]/p[:-1]-1)*100.0])   # pct[i]=return of month i

# ---- live directional leans (reuse engines' in-fold logic, terminal row) ----
def rd_live(N=6):
    ratio=sp['CAPE'].to_numpy(float); num=sp['Real_Price'].to_numpy(float); den=sp['Real_Earnings'].to_numpy(float)
    nxt=sp['nxt'].to_numpy(float)
    gr,gn,gd=E._pc(ratio,N),E._pc(num,N),E._pc(den,N)
    tr=np.arange(0,L); tr=tr[(~np.isnan(gr[tr]))&(~np.isnan(gn[tr]))&(~np.isnan(gd[tr]))&(~np.isnan(nxt[tr]))&(nxt[tr]!=0)]
    def tern(a):
        mu=a[tr].mean(); sd=a[tr].std(); zz=(a-mu)/sd if sd>0 else a*0
        r=np.zeros(len(a),int); r[zz>E.SD]=1; r[zz<-E.SD]=-1; return r
    cc,cp,ce=tern(gr),tern(gn),tern(gd); typ=(cc+1)*9+(cp+1)*3+(ce+1)
    same=tr[typ[tr]==typ[L]]; seg=same if len(same)>0 else tr
    up=(nxt[seg]>0).sum(); dn=(nxt[seg]<0).sum()
    return (1 if up>=dn else -1), int(typ[L])+1, len(same), up/max(len(seg),1)

rd_dir,rd_type,rd_n,rd_up=rd_live()

# ---- CASSANDRA magnitude: similarity-weighted analogue forward returns ----
# reuse SANCTUARY matching at the live month; collect each analogue's realized
# next-month % return (pct[j+1]) + its similarity weight.
def sanctuary_live(sd_w=E.SANC_SD_W, min_sim=E.SANC_MIN_SIM, lbs=E.SANC_LBS):
    sd=np.full(len(p),np.nan)
    for i in range(len(p)):
        w=pct[max(0,i-sd_w+1):i+1]; w=w[~np.isnan(w)]
        if len(w)>=12: sd[i]=w.std(ddof=1)
    zc=np.where((sd>0)&(~np.isnan(sd)),pct/sd,np.nan)
    pastz=zc[(np.arange(len(zc))<L)&(~np.isnan(zc))]
    small,big=np.quantile(np.abs(pastz),[0.15,0.85])
    fwd=[]                                    # (fwd_ret%, similarity)
    for Lk in lbs:
        a=L-(Lk-1)
        if a<1 or np.isnan(pct[a:L+1]).any() or np.isnan(zc[a:L+1]).any(): continue
        rec=pct[a:L+1]; recb=E._bins_adaptive(zc[a:L+1],small,big); rn=np.linalg.norm(rec)
        for j in range((Lk-1),L):
            b0=j-(Lk-1)
            if b0<0 or j+1>L or np.isnan(pct[j+1]): continue   # need realized next-month return
            if np.isnan(pct[b0:j+1]).any() or np.isnan(zc[b0:j+1]).any(): continue
            if E._bins_adaptive(zc[b0:j+1],small,big)!=recb: continue
            win=pct[b0:j+1]; wn=np.linalg.norm(win)
            if rn==0 or wn==0: continue
            cos=float(np.dot(rec,win)/(rn*wn))
            cr=np.corrcoef(rec,win)[0,1] if Lk-1>=2 else cos; cr=0.0 if np.isnan(cr) else cr
            sim=(abs(cr)+cos)/2.0
            if sim<min_sim: continue
            fwd.append((pct[j+1],sim))
    return fwd

fwd=sanctuary_live()
sc_dir=None; band=None
if fwd:
    rets=np.array([r for r,_ in fwd]); wts=np.array([s for _,s in fwd]); wts=wts/wts.sum()
    up_pct=(rets>0).mean(); sc_dir=1 if up_pct>0.5 else -1
    wmean=float((wts*rets).sum())
    lo,md,hi=np.percentile(rets,[10,50,90])
    band=dict(n=len(rets),up_pct=up_pct,wmean=wmean,p10=lo,p50=md,p90=hi)

# ---- convergence decision (live) ----
leans=[('RED DAWN',rd_dir),('SANCTUARY',sc_dir)]
present=[d for _,d in leans if d in (1,-1)]
if len(present)>=2 and len(set(present))==1: decision=('CONVERGE',present[0])
elif len(present)>=2: decision=('SPLIT->ABSTAIN',0)
else: decision=('INSUFFICIENT->ABSTAIN',0)

# ---- report ----
W=88; f=lambda r: spot*(1+r/100)
print("="*W)
print(f"ZION SPY — LIVE MONTHLY CALL   decision month {live_date.date()}  ->  target month +1 (Sep 2026)")
print("="*W)
print(f"[anchor]    SP_Price spot = ${spot:,.2f}   CAPE = {sp['CAPE'].iloc[L]:.2f}")
print(f"[RED DAWN ] lean={'UP' if rd_dir>0 else 'DOWN'}  (CAPE type T{rd_type}, {rd_n} past same-type, up_pct={rd_up*100:.0f}%)")
print(f"[SANCTUARY] lean={'UP' if sc_dir==1 else ('DOWN' if sc_dir==-1 else 'n/a')}  "
      + (f"({band['n']} analogues, up_pct={band['up_pct']*100:.0f}%)" if band else "(no analogues cleared sim floor)"))
print(f"[CONVERGENCE DECISION]  {decision[0]}"
      + (f"  direction={'UP' if decision[1]>0 else 'DOWN'}" if decision[1] else ""))
print("-"*W)
if band:
    print("[CASSANDRA magnitude] 1-month-ahead analogue return distribution (similarity-weighted):")
    print(f"   n={band['n']}  up_pct={band['up_pct']*100:.0f}%  wmean={band['wmean']:+.2f}%")
    print(f"   PRICE band  p10 ${f(band['p10']):,.0f}  |  p50 ${f(band['p50']):,.0f}  |  p90 ${f(band['p90']):,.0f}")
    print(f"   (spot ${spot:,.0f}; range = {band['p10']:+.1f}% .. {band['p90']:+.1f}%)")
print("-"*W)
print("[EMITTED CALL]  ABSTAIN (VETO).  SPY Stage-4 direction shows no validated edge over")
print("   buy-hold (placebo p=0.06-0.10; EDGE ~+1pp; emit-UP ~97%). Per NO-FORCED-PREDICTION,")
print("   the price band above is DESCRIPTIVE CONTEXT, NOT an emitted forecast.")
print("="*W)

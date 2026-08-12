"""
ZION STAGE 4 (first cut) — INTEGRATED FIVE-ASSET LEDGER.
Puts the five ORACLE streams on ONE monthly spine and answers:
  (1) how they assemble, (2) how conflicts resolve, (3) coverage (>=1 asset acts).

Method (recipe-faithful, PIT/in-fold):
  - Re-run each asset's sequential one-step-ahead WF (identical to oracle_stage).
  - For each month t, assign the 27-type and predict via same-type past-majority.
  - ACT GATE (Phase-2 STANDING RULE, in-fold trailing, operator bars):
        a month ACTS iff its type's TRAILING record (same-type acted months < t)
        has n>=8 AND acc>0.675 at that month. Else ABSTAIN. No forced call.
    This is the C6-honest, going-forward pull: a type only "turns on" once its
    own past-only sequential record has cleared the bar.
  - Emit per-asset per-month rows; merge on Date; report union coverage.
Assets do NOT compete for the same slot (each predicts its OWN next-month
direction) -> no directional "conflict" between assets. Conflict resolution
lives (a) WITHIN an asset across engines (Stage 4 convergence, deferred) and
(b) at the BOOK level (Stage 9 sleeve sizing / gross cap, deferred).
"""
import pandas as pd, numpy as np
PANEL="/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
SD=0.5; Z=1.96; START=np.datetime64('1990-01-01'); MIN_TRAIN=60
PULL_ACC=0.675; PULL_N=8                       # Phase-2 standing-rule bars (operator)
PUB_LAG={'Industrial_Production':2,'US_CPI':2,'M2_Money':2}
ASSETS={
 'SP500':  dict(outcome='SP_Price',    ratio_col='CAPE', num='Real_Price', den='Real_Earnings', deflate=False),
 'Gold':   dict(outcome='Gold_Close',  num='Dollar_Index', den='M2_Money', deflate=True),
 'Silver': dict(outcome='Silver_Close',num='Industrial_Production', den='GS10_Rate', deflate=False),
 'WTI':    dict(outcome='WTI_Crude_Close', num='US_2Y_Treasury', den='Fed_Funds_Rate', deflate=False),
 'USD':    dict(outcome='Dollar_Index', num='Gold_Close', den='US_CPI', deflate=False),
}
def pc(x,N):
    r=np.full(len(x),np.nan); r[N:]=x[N:]/x[:-N]-1; return r
def wlb(k,n):
    if n<=0: return 0.0
    p=k/n; d=1+Z*Z/n; c=p+Z*Z/(2*n); m=Z*np.sqrt(p*(1-p)/n+Z*Z/(4*n*n)); return (c-m)/d

def stream(name, df):
    """Return per-month DataFrame: Date, type, pred, actual, match, acted."""
    cfg=ASSETS[name]
    cols=list(dict.fromkeys(['Date',cfg['outcome'],cfg['num'],cfg['den']]
              +([cfg['ratio_col']] if cfg.get('ratio_col') else [])+(['US_CPI'] if cfg['deflate'] else [])))
    d=df[cols].dropna().reset_index(drop=True)
    out=d[cfg['outcome']].to_numpy(float)
    num=d[cfg['num']].to_numpy(float); den=d[cfg['den']].to_numpy(float)
    if cfg['deflate']:
        cpi=d['US_CPI'].to_numpy(float); num=num/cpi; den=den/cpi
    ratio=d[cfg['ratio_col']].to_numpy(float) if cfg.get('ratio_col') else num/den
    dts=d['Date'].to_numpy(); yr=d['Date'].dt.year.to_numpy()
    nxt=np.sign(np.concatenate([out[1:]/out[:-1]-1,[np.nan]]))
    pre=yr<1990
    if (pre & ~np.isnan(ratio)).sum()<40:
        cut=int(len(d)*0.4); pre=np.arange(len(d))<cut
    best=3; ba=-1
    for N in range(3,13,3):
        rd=np.sign(pc(ratio,N)); m=pre&(~np.isnan(rd))&(~np.isnan(nxt))&(rd!=0)&(nxt!=0)
        if m.sum()<40: continue
        a=(rd[m]==nxt[m]).mean()
        if a>ba: ba=a; best=N
    N=best; gr,gn,gd=pc(ratio,N),pc(num,N),pc(den,N)
    rows=[]; trail={}                              # trail[type]=(k,n) of PAST same-type WF months
    for t in range(len(d)):
        if dts[t]<START or nxt[t]==0 or np.isnan(nxt[t]) or np.isnan(gr[t]): continue
        tr=np.arange(0,t); tr=tr[(~np.isnan(gr[tr]))&(~np.isnan(gn[tr]))&(~np.isnan(gd[tr]))&(~np.isnan(nxt[tr]))&(nxt[tr]!=0)]
        if len(tr)<MIN_TRAIN: continue
        def tern(a):
            mu=a[tr].mean(); sd=a[tr].std(); zz=(a-mu)/sd if sd>0 else a*0
            r=np.zeros(len(a),int); r[zz>SD]=1; r[zz<-SD]=-1; return r
        cc,cp,ce=tern(gr),tern(gn),tern(gd); typ=(cc+1)*9+(cp+1)*3+(ce+1)
        ti=int(typ[t])
        same=tr[typ[tr]==typ[t]]; seg=same if len(same)>0 else tr
        up=(nxt[seg]>0).sum(); dn=(nxt[seg]<0).sum(); pred=1 if up>=dn else -1
        k,n=trail.get(ti,(0,0))                    # trailing PAST record for this type (in-fold)
        acted = (n>=PULL_N) and (k/n>PULL_ACC) if n>0 else False
        match=int(pred==nxt[t])
        rows.append(dict(Date=pd.Timestamp(dts[t]), type=ti+1, pred=int(pred),
                         actual=int(nxt[t]), match=match, acted=bool(acted)))
        trail[ti]=(k+match, n+1)                    # update AFTER decision (PIT)
    r=pd.DataFrame(rows)
    return r

df=pd.read_csv(PANEL); df['Date']=pd.to_datetime(df['Date'])
for col,lag in PUB_LAG.items():
    if col in df.columns: df[col]=df[col].shift(lag)

streams={nm:stream(nm,df) for nm in ASSETS}

# ---- per-asset summary ----
print("="*96)
print("ZION INTEGRATED FIVE-ASSET LEDGER (first cut) — monthly, sequential one-step-ahead")
print("="*96)
print(f"{'asset':7s} {'WF span':23s} {'months':>6s} {'ungated_acc':>11s} {'ACTED':>6s} {'act_acc':>7s} {'act_LB':>6s}")
for nm,r in streams.items():
    a=r[r.acted]
    ug=r.match.mean()*100
    aa=a.match.mean()*100 if len(a) else float('nan')
    lb=wlb(int(a.match.sum()),len(a))*100 if len(a) else 0
    span=f"{r.Date.min().date()}..{r.Date.max().date()}"
    print(f"{nm:7s} {span:23s} {len(r):6d} {ug:10.1f}% {len(a):6d} {aa:6.1f}% {lb:5.0f}%")

# ---- integrated month spine + coverage ----
alld=sorted(set().union(*[set(r.Date) for r in streams.values()]))
spine=pd.DataFrame({'Date':alld}).sort_values('Date').reset_index(drop=True)
for nm,r in streams.items():
    m=r.set_index('Date')
    spine[nm+'_pred']=spine.Date.map(m.pred).astype('Int64')
    spine[nm+'_act']=(spine.Date.map(m.acted)==True)
    spine[nm+'_match']=spine.Date.map(m.match).astype('Int64')
act_cols=[nm+'_act' for nm in ASSETS]
spine['n_acting']=spine[act_cols].sum(axis=1)
spine['any_act']=spine.n_acting>0

tot=len(spine); anymo=int(spine.any_act.sum())
print("-"*96)
print(f"[SPINE]     union months (any asset present) = {tot}   {spine.Date.min().date()}..{spine.Date.max().date()}")
print(f"[COVERAGE]  months with >=1 asset ACTING = {anymo}/{tot} = {anymo/tot*100:.1f}%")
for k in range(0,6):
    c=int((spine.n_acting==k).sum())
    print(f"   exactly {k} asset(s) acting: {c:4d} months ({c/tot*100:4.1f}%)")
# restrict to the fully-overlapping window (all five have data)
allpresent=spine[[nm+'_match' for nm in ASSETS]].notna().all(axis=1)
ov=spine[allpresent]
if len(ov):
    aov=int(ov.any_act.sum())
    print(f"[OVERLAP]   all-five-present window {ov.Date.min().date()}..{ov.Date.max().date()}  months={len(ov)}")
    print(f"            >=1 acting in that window = {aov}/{len(ov)} = {aov/len(ov)*100:.1f}%")

spine.to_csv("/Users/castaglia/Desktop/ZION/stage4_ledger/integrated_five_asset_ledger.csv",index=False)
print("-"*96)
print("wrote stage4_ledger/integrated_five_asset_ledger.csv")

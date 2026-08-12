"""
ZION ORACLE stage — reusable, config-driven. Runs the identical clean step on ANY asset.
Discipline: cyclically/real-adjust constituents DISCRETELY before forming the ratio;
N chosen by pre-1990 (design-sample) sweep then FROZEN; +-0.5 SD dead zone on pct_change(N);
sequential ONE-STEP-AHEAD walk-forward from 1990 (retrain all-past each month); NO LB/OOS
gates at this stage (pure measurement); prints full provenance every run.
Add an asset = add one ASSETS entry.
"""
import pandas as pd, numpy as np, sys
PANEL="/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
SD=0.5; Z=1.96; START=np.datetime64('1990-01-01'); MIN_TRAIN=60
PUB_LAG={'Industrial_Production':2,'US_CPI':2,'M2_Money':2}  # mid-month/late releases: lag at 1st-of-mo decision

# ratio_col: use a precomputed cyclically-adjusted column directly (e.g. CAPE). Else ratio=num/den.
# num/den: the two legs for the 27-type decomposition. deflate: CPI-real each leg discretely.
ASSETS={
 'SP500':  dict(outcome='SP_Price',    ratio_col='CAPE', num='Real_Price', den='Real_Earnings', deflate=False,
                note='CAPE = CPI-real + 10y earnings smoothing (adjusted before ratio)'),
 'Gold':   dict(outcome='Gold_Close',  num='Dollar_Index', den='M2_Money', deflate=True,
                note='Dollar/M2 (gold NOT in numerator); CPI-real legs'),
 'Silver': dict(outcome='Silver_Close',num='Industrial_Production', den='GS10_Rate', deflate=False,
                note='PROPOSED IndProd/GS10 (distinct legs per uniqueness rule); confirm'),
 'WTI':    dict(outcome='WTI_Crude_Close', num='US_2Y_Treasury', den='Fed_Funds_Rate', deflate=False,
                note='PROPOSED US2Y/FedFunds (distinct legs); confirm'),
 'USD':    dict(outcome='Dollar_Index', num='Gold_Close', den='US_CPI', deflate=False,
                note='PROPOSED Gold/CPI — dollar-FREE, distinct legs; confirm'),
}

def pc(x,N):
    r=np.full(len(x),np.nan); r[N:]=x[N:]/x[:-N]-1; return r
def wlb(k,n):
    if n<=0: return 0.0
    p=k/n; d=1+Z*Z/n; c=p+Z*Z/(2*n); m=Z*np.sqrt(p*(1-p)/n+Z*Z/(4*n*n)); return (c-m)/d

def run(name, df):
    cfg=ASSETS[name]
    cols=list(dict.fromkeys(['Date',cfg['outcome'],cfg['num'],cfg['den']]
              +([cfg['ratio_col']] if cfg.get('ratio_col') else [])+(['US_CPI'] if cfg['deflate'] else [])))
    d=df[cols].dropna().reset_index(drop=True)
    if len(d)<MIN_TRAIN+24:
        print(f"[{name}] INSUFFICIENT DATA ({len(d)} rows) — BLOCK"); return
    out=d[cfg['outcome']].to_numpy(float)
    num=d[cfg['num']].to_numpy(float); den=d[cfg['den']].to_numpy(float)
    infl='none (nominal)'
    if cfg['deflate']:
        cpi=d['US_CPI'].to_numpy(float); num=num/cpi; den=den/cpi; infl='US_CPI'   # discrete real adj
    ratio=d[cfg['ratio_col']].to_numpy(float) if cfg.get('ratio_col') else num/den
    ratio_name=cfg.get('ratio_col') or f"{cfg['num']}/{cfg['den']}"
    dts=d['Date'].to_numpy(); yr=d['Date'].dt.year.to_numpy()
    nxt=np.sign(np.concatenate([out[1:]/out[:-1]-1,[np.nan]]))
    # design sample for N-sweep: pre-1990 if enough, else first 40% (hygiene fallback)
    pre=yr<1990
    dsrc='pre-1990'
    if (pre & ~np.isnan(ratio)).sum()<40:
        cut=int(len(d)*0.4); pre=np.arange(len(d))<cut; dsrc=f'first 40% (<{d.Date.iloc[cut].date()})'
    best=3; ba=-1; sweep={}
    for N in range(3,13,3):                              # N >= 3, multiple of 3 (quarterly reporting)
        rd=np.sign(pc(ratio,N)); m=pre&(~np.isnan(rd))&(~np.isnan(nxt))&(rd!=0)&(nxt!=0)
        if m.sum()<40: continue
        a=(rd[m]==nxt[m]).mean(); sweep[N]=a
        if a>ba: ba=a; best=N
    N=best; gr,gn,gd=pc(ratio,N),pc(num,N),pc(den,N)
    k=n=0; by={}
    for t in range(len(d)):
        if dts[t]<START or nxt[t]==0 or np.isnan(nxt[t]) or np.isnan(gr[t]): continue
        tr=np.arange(0,t); tr=tr[(~np.isnan(gr[tr]))&(~np.isnan(gn[tr]))&(~np.isnan(gd[tr]))&(~np.isnan(nxt[tr]))&(nxt[tr]!=0)]
        if len(tr)<MIN_TRAIN: continue
        def tern(a):
            mu=a[tr].mean(); sd=a[tr].std(); zz=(a-mu)/sd if sd>0 else a*0
            r=np.zeros(len(a),int); r[zz>SD]=1; r[zz<-SD]=-1; return r
        cc,cp,ce=tern(gr),tern(gn),tern(gd); typ=(cc+1)*9+(cp+1)*3+(ce+1)
        same=tr[typ[tr]==typ[t]]; seg=same if len(same)>0 else tr    # NO LB/OOS gate; global fallback
        up=(nxt[seg]>0).sum(); dn=(nxt[seg]<0).sum(); pred=1 if up>=dn else -1
        c=int(pred==nxt[t]); k+=c; n+=1; by.setdefault(int(typ[t]),[]).append(c)
    flat="FLAT (no-signal)" if (sweep and max(sweep.values())-0.5<0.03) else "peaked"
    print("="*92); print(f"### ORACLE — {name} ###   {cfg['note']}")
    print(f"[provenance] predictor RATIO = {ratio_name} | inflation adj (discrete, pre-ratio) = {infl}")
    print(f"[N chosen]   {N} mo  design={dsrc}  sweep {flat}: "+", ".join(f'{a}:{b*100:.0f}%' for a,b in sorted(sweep.items())))
    print(f"[data]       rows {len(d)}  {d.Date.min().date()}..{d.Date.max().date()}")
    print(f"[OVERALL]    ungated 1-step-ahead WF from 1990: {k/n*100:.1f}%   n={n}   (LB {wlb(k,n)*100:.0f}%, informational)")
    sym={1:'UP',0:'flat',-1:'DN'}
    print(" ALL 27 SUB-TYPES (last step) | T | CAPE/num/den | n | sequential-WF acc | LB:")
    for cs in (1,0,-1):
      for ps in (1,0,-1):
        for es in (1,0,-1):
          ti=(cs+1)*9+(ps+1)*3+(es+1); v=by.get(ti,[])
          if v:
            kk=sum(v); nn=len(v)
            print(f"   T{ti+1:<2} {sym[cs]:>4}/{sym[ps]:>4}/{sym[es]:>4}  n={nn:<4} {kk/nn*100:5.1f}%   LB={wlb(kk,nn)*100:.0f}%")
          else:
            print(f"   T{ti+1:<2} {sym[cs]:>4}/{sym[ps]:>4}/{sym[es]:>4}  n=0     --")

def check_leg_uniqueness():
    """RULE: every numerator/denominator may be chosen ONCE across all assets."""
    legs={}
    for nm,c in ASSETS.items():
        for role in ('num','den'):
            legs.setdefault(c[role],[]).append(f"{nm}.{role}")
    bad={v:u for v,u in legs.items() if len(u)>1}
    print("="*70+"\n[LEG-UNIQUENESS RULE] every num/den used once across the five")
    if bad:
        for v,u in bad.items(): print(f"  VIOLATION: '{v}' reused by {', '.join(u)}")
        print("  RESULT: FAIL — reassign so no leg repeats.")
    else:
        print("  RESULT: PASS")
    return not bad

if __name__=='__main__':
    df=pd.read_csv(PANEL); df['Date']=pd.to_datetime(df['Date'])
    for col,lag in PUB_LAG.items():                     # PIT publication lag (mid-month releases)
        if col in df.columns: df[col]=df[col].shift(lag)
    print("[PIT LAGS] "+", ".join(f"{c}:{l}mo" for c,l in PUB_LAG.items()))
    ok=check_leg_uniqueness()
    names=sys.argv[1:] or list(ASSETS)
    if '--run' in names or ok:
        for nm in [n for n in names if n!='--run']: run(nm, df)

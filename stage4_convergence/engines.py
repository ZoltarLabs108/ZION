"""
ZION STAGE 4 — engine harness + directional engines (SPY monthly).
Each engine is a pure sequential one-step-ahead WALK-FORWARD producer:
    engine(spine) -> DataFrame[Date, dir, conf, <engine extras>]
where for each decision month t (>= START), the engine is trained on ALL PAST
rows (< t) ONLY and emits:
    dir  in {+1,-1}   the engine's directional lean for SP_Price at t+1
    conf in [0,1]     an engine-specific confidence scalar
No engine abstains internally; abstention/agreement is decided by the CONVERGENCE
host (convergence.py). Discipline: in-fold only, expanding window, PIT lags,
+-0.5 train-SD dead zone where a ternary is formed, N frozen a-priori.

Shared spine: SP_Price outcome; next-month realized direction nxt = sign(pct_change.shift(-1)).
"""
import pandas as pd, numpy as np

PANEL="/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
START=np.datetime64('1990-01-01'); MIN_TRAIN=60; Z=1.96; SD=0.5
PUB_LAG={'Industrial_Production':2,'US_CPI':2,'M2_Money':2}

def wlb(k,n):
    if n<=0: return 0.0
    p=k/n; d=1+Z*Z/n; c=p+Z*Z/(2*n); m=Z*np.sqrt(p*(1-p)/n+Z*Z/(4*n*n)); return (c-m)/d

def load_spine():
    """SPY monthly spine: Date + everything the engines need, PIT-lagged, sorted, deduped."""
    df=pd.read_csv(PANEL); df['Date']=pd.to_datetime(df['Date'])
    for col,lag in PUB_LAG.items():
        if col in df.columns: df[col]=df[col].shift(lag)
    need=['Date','SP_Price','CAPE','Real_Price','Real_Earnings']
    df=df[need].dropna(subset=['SP_Price']).drop_duplicates('Date').sort_values('Date').reset_index(drop=True)
    df['nxt']=np.sign(df['SP_Price'].shift(-1)/df['SP_Price']-1)   # realized next-month dir
    return df

def _pc(x,N):
    r=np.full(len(x),np.nan); r[N:]=x[N:]/x[:-N]-1; return r

# ============================================================================
# ENGINE 1 — RED DAWN  (CAPE 27-type valuation lens)
# ============================================================================
def red_dawn(spine, N=6):
    """dir = same-type past-majority next-month direction (in-fold).
       conf = trailing in-fold accuracy of that type (k/n over past same-type months).
       Also emits: type (1..27), tn (trailing n of the type)."""
    d=spine.dropna(subset=['CAPE','Real_Price','Real_Earnings']).reset_index(drop=True)
    ratio=d['CAPE'].to_numpy(float); num=d['Real_Price'].to_numpy(float); den=d['Real_Earnings'].to_numpy(float)
    nxt=d['nxt'].to_numpy(float); dts=d['Date'].to_numpy()
    gr,gn,gd=_pc(ratio,N),_pc(num,N),_pc(den,N)
    rows=[]; trail={}
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
        up=(nxt[seg]>0).sum(); dn=(nxt[seg]<0).sum(); dir_=1 if up>=dn else -1
        k,n=trail.get(ti,(0,0)); conf=(k/n) if n>0 else 0.5
        rows.append(dict(Date=pd.Timestamp(dts[t]),dir=int(dir_),conf=float(conf),
                         type=ti+1,tn=int(n)))
        trail[ti]=(k+int(dir_==np.sign(nxt[t])), n+1)
    return pd.DataFrame(rows)

# ============================================================================
# ENGINE 2 — ODYSSEY  (binned pattern-analogue, monthly port of TrendaEngine)
# ----------------------------------------------------------------------------
# Faithful monthly adaptation of HYACINTH_4_ODYSSEY:
#   - native engine is DAILY (window=21d, sd=756d); monthly port uses w=1 month,
#     trailing-SD lookback SD_L months, lookback=4-symbol trajectory (t..t-3).
#   - 6 EQUI-PROBABLE z-bins; edges = quantiles [1/6..5/6] of PAST z only
#     (EXPANDING/in-fold) -> fixes the documented full-sample leak (lines 509-524).
#   - analogue = past month whose 4-bin trajectory EXACTLY equals current's.
#   - HORIZON ALIGNED TO 1 MONTH: an analogue's outcome = its own next-month
#     realized direction nxt[j] (so it votes on the SAME target as RED DAWN),
#     not the native 6-period forward. up_pct = fraction of analogues up.
# ============================================================================
ODY_LB=4; ODY_SD_L=36; ODY_MIN_MATCH=3

def odyssey(spine, lookback=ODY_LB, sd_l=ODY_SD_L, min_match=ODY_MIN_MATCH):
    d=spine.reset_index(drop=True)
    p=d['SP_Price'].to_numpy(float); nxt=d['nxt'].to_numpy(float); dts=d['Date'].to_numpy()
    r=np.concatenate([[np.nan], p[1:]/p[:-1]-1])                 # monthly return (w=1), causal
    sd=np.full(len(p),np.nan)
    for i in range(len(p)):
        w=r[max(0,i-sd_l+1):i+1]; w=w[~np.isnan(w)]
        if len(w)>=20: sd[i]=w.std(ddof=1)
    z=np.where((sd>0)&(~np.isnan(sd)), r/sd, np.nan)
    rows=[]
    for t in range(len(d)):
        if dts[t]<START or nxt[t]==0 or np.isnan(nxt[t]): continue
        if t<lookback or np.isnan(z[t-lookback+1:t+1]).any(): continue
        past=np.where((np.arange(len(z))<t)&(~np.isnan(z)))[0]   # in-fold z pool (< t)
        if len(past)<60: continue
        edges=np.quantile(z[past],[1/6,2/6,3/6,4/6,5/6])         # EXPANDING equi-prob edges
        b=lambda v: int(np.digitize(v,edges))                   # 0..5
        cur=tuple(b(z[t-k]) for k in range(lookback))           # newest..oldest
        outs=[]
        for j in range(lookback-1, t):                          # analogue end-month j (< t)
            if nxt[j]==0 or np.isnan(nxt[j]) or np.isnan(z[j-lookback+1:j+1]).any(): continue
            if tuple(b(z[j-k]) for k in range(lookback))==cur: outs.append(nxt[j])
        outs=np.array(outs,float)
        if len(outs)<min_match: continue                        # too few analogues -> no vote
        up=(outs>0).mean(); dir_=1 if up>=0.5 else -1
        rows.append(dict(Date=pd.Timestamp(dts[t]),dir=int(dir_),conf=float(up),n_match=len(outs)))
    return pd.DataFrame(rows)

# ============================================================================
# ENGINE 3 — SANCTUARY  (continuous similarity-weighted analogue, monthly)
# ----------------------------------------------------------------------------
# Faithful port of HYACINTH_5_SANCTUARY PatternEngine (already monthly):
#   - recent state = last (L-1) monthly % changes, L in ensemble {3,4,5}.
#   - Stage 1 exact SD-bin filter: 6 bins, ADAPTIVE edges = |z| quantiles
#     0.15/0.85 computed IN-FOLD (past-only) -> matches the cutoff_idx path,
#     avoids the full-sample bin leak.
#   - Stage 2 similarity = (|corr|+cosine)/2 over raw pct-change vectors; keep
#     sim >= MIN_SIM. (regime factor + time-decay omitted from the directional
#     COUNT; they scale magnitude, not the vote -- documented simplification.)
#   - HORIZON ALIGNED TO 1 MONTH: each match outcome = its own nxt[j].
#   - Ensemble pools matches over L in {3,4,5}. up_pct = fraction up;
#     dir_ratio = max(up,down)/n (unweighted, per source). dir = up>down.
# ============================================================================
SANC_SD_W=60; SANC_MIN_SIM=0.55; SANC_MIN_MATCH=3; SANC_LBS=(3,4,5)

def _bins_adaptive(zvec, small, big):
    out=[]
    for zz in zvec:
        m=1 if abs(zz)<small else (3 if abs(zz)>=big else 2)
        s=1 if zz>=0 else -1
        out.append(s*m)
    return tuple(out)

def sanctuary(spine, sd_w=SANC_SD_W, min_sim=SANC_MIN_SIM, min_match=SANC_MIN_MATCH, lbs=SANC_LBS):
    d=spine.reset_index(drop=True)
    p=d['SP_Price'].to_numpy(float); nxt=d['nxt'].to_numpy(float); dts=d['Date'].to_numpy()
    pct=np.concatenate([[np.nan], (p[1:]/p[:-1]-1)*100.0])       # monthly % change, pct[i]=month i
    sd=np.full(len(p),np.nan)
    for i in range(len(p)):
        w=pct[max(0,i-sd_w+1):i+1]; w=w[~np.isnan(w)]
        if len(w)>=12: sd[i]=w.std(ddof=1)
    zc=np.where((sd>0)&(~np.isnan(sd)), pct/sd, np.nan)          # z of each monthly change
    rows=[]
    for t in range(len(d)):
        if dts[t]<START or nxt[t]==0 or np.isnan(nxt[t]): continue
        pastz=zc[(np.arange(len(zc))<t)&(~np.isnan(zc))]         # in-fold |z| pool
        if len(pastz)<60: continue
        small,big=np.quantile(np.abs(pastz),[0.15,0.85])
        pooled=[]                                                # (outcome, weight) across ensemble
        for L in lbs:
            a=t-(L-1)                                            # recent changes pct[a..t]
            if a<1 or np.isnan(pct[a:t+1]).any() or np.isnan(zc[a:t+1]).any(): continue
            rec=pct[a:t+1]; recb=_bins_adaptive(zc[a:t+1],small,big)
            rn=np.linalg.norm(rec)
            for j in range((L-1), t):                            # window end month j (< t)
                b0=j-(L-1)
                if b0<0 or nxt[j]==0 or np.isnan(nxt[j]): continue
                if np.isnan(pct[b0:j+1]).any() or np.isnan(zc[b0:j+1]).any(): continue
                if _bins_adaptive(zc[b0:j+1],small,big)!=recb: continue     # Stage-1 bin filter
                win=pct[b0:j+1]
                wn=np.linalg.norm(win)
                if rn==0 or wn==0: continue
                cos=float(np.dot(rec,win)/(rn*wn))
                if L-1>=2:
                    cr=np.corrcoef(rec,win)[0,1]; cr=0.0 if np.isnan(cr) else cr
                else: cr=cos
                sim=(abs(cr)+cos)/2.0
                if sim<min_sim: continue                                    # Stage-2 sim floor
                pooled.append((nxt[j],sim))
        if len(pooled)<min_match: continue
        outs=np.array([o for o,_ in pooled]);
        up=(outs>0).mean(); n=len(outs)
        dir_=1 if up>0.5 else (-1 if up<0.5 else 1)
        dir_ratio=max((outs>0).sum(),(outs<0).sum())/n
        rows.append(dict(Date=pd.Timestamp(dts[t]),dir=int(dir_),conf=float(up),
                         dir_ratio=float(dir_ratio),n_match=int(n)))
    return pd.DataFrame(rows)

def _acc(eng, spine):
    m=spine.set_index('Date')['nxt']
    y=np.sign(m.loc[eng.Date].to_numpy()); return (eng.dir.to_numpy()==y).mean()

if __name__=='__main__':
    sp=load_spine()
    print(f"[spine] rows={len(sp)}  {sp.Date.min().date()}..{sp.Date.max().date()}")
    rd=red_dawn(sp);  print(f"[RED DAWN ] months={len(rd):4d}  ungated dir acc={_acc(rd,sp)*100:.1f}%")
    od=odyssey(sp);   print(f"[ODYSSEY  ] months={len(od):4d}  ungated dir acc={_acc(od,sp)*100:.1f}%  (min_match={ODY_MIN_MATCH})")
    sc=sanctuary(sp); print(f"[SANCTUARY] months={len(sc):4d}  ungated dir acc={_acc(sc,sp)*100:.1f}%  (min_match={SANC_MIN_MATCH})")

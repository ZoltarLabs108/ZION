"""
ZION STAGE 4 — CONVERGENCE host (SPY monthly).
Puts the independent directional engines on one spine and applies the
agreement gate. Two engine SETS (operator ruling 2026-08-12: build both):
  - 2-engine: RED DAWN + ODYSSEY            (ZION program-map / legacy CONVERGENCE)
  - 3-engine: RED DAWN + ODYSSEY + SANCTUARY (Convergence-Abstention methodology)

Two GATE flavors, reported side by side (no truncation):
  A. PURE AGREEMENT (descriptive lift): act on the agreed direction whenever the
     required engines converge; ABSTAIN on split. No record gate.
  B. GATED (deployable Stage-4 4d): agreement AND the convergence signal's TRAILING
     in-fold record clears Wilson-LB > LB_BAR with n >= N_FLOOR (past-only, sequential).
     -> a proper going-forward standing rule; ABSTAIN while still accumulating.

Convergence semantics:
  - UNANIMOUS: every PRESENT engine (>=2) agrees -> act; any dissent -> ABSTAIN ("flat on split").
  - For the 2-engine set, unanimity == both-agree.
  - For the 3-engine set we also report MAJORITY (>=2 of the present engines agree).

Everything is sequential one-step-ahead already (each engine trains on <t only), so the
acted stream IS the walk-forward / CONVERGENCE_TRACK. Reports coverage-selection guard
corr(acted, market-up) and compares to RED DAWN standalone.
"""
import pandas as pd, numpy as np
import engines as E

LB_BAR=0.50; N_FLOOR=8

def build():
    sp=E.load_spine()
    rd=E.red_dawn(sp).rename(columns={'dir':'rd','conf':'rd_c'})[['Date','rd','rd_c']]
    od=E.odyssey(sp).rename(columns={'dir':'od','conf':'od_c'})[['Date','od','od_c']]
    sc=E.sanctuary(sp).rename(columns={'dir':'sc','conf':'sc_c'})[['Date','sc','sc_c']]
    m=sp[['Date','nxt']].copy()
    m['y']=np.sign(m['nxt'])
    for e in (rd,od,sc): m=m.merge(e,on='Date',how='left')
    m=m[(m.Date>=pd.Timestamp(E.START))&(m.y!=0)&m.y.notna()].reset_index(drop=True)
    return m

def agree(votes):
    """votes: list of +1/-1/nan. Return (present, up, dn)."""
    v=[x for x in votes if x==1 or x==-1]
    return len(v), sum(1 for x in v if x==1), sum(1 for x in v if x==-1)

def gate_stream(m, cols, mode='unanimous'):
    """Emit per-month agreed direction (or 0=abstain). Pure agreement, no record gate."""
    out=np.zeros(len(m),int); present=np.zeros(len(m),int)
    for i in range(len(m)):
        votes=[m[c].iloc[i] for c in cols]
        p,u,dn=agree(votes); present[i]=p
        if p<2: continue                              # need >=2 present to "converge"
        if mode=='unanimous':
            if u>0 and dn==0: out[i]=1
            elif dn>0 and u==0: out[i]=-1
        else:                                          # majority (>=2 agree)
            if u>=2 and u>dn: out[i]=1
            elif dn>=2 and dn>u: out[i]=-1
    return out, present

def record_gate(m, agreed):
    """Layer B: act only once the TRAILING in-fold record of the agreement signal
    clears Wilson-LB>LB_BAR & n>=N_FLOOR (past-only). Returns acted-dir stream."""
    y=m.y.to_numpy(); acted=np.zeros(len(m),int); k=n=0
    for i in range(len(m)):
        if agreed[i]!=0 and n>=N_FLOOR and E.wlb(k,n)>LB_BAR:
            acted[i]=agreed[i]
        if agreed[i]!=0:                               # update trailing record AFTER decision (PIT)
            k+=int(agreed[i]==y[i]); n+=1
    return acted

def summ(m, stream, label):
    y=m.y.to_numpy(); acted=stream!=0
    n=int(acted.sum())
    if n==0:
        print(f"  {label:34s} acted=0"); return dict(label=label,acted=0)
    corr_pred=(stream[acted]==y[acted]); acc=corr_pred.mean()
    lb=E.wlb(int(corr_pred.sum()),n)
    up_mkt=(y[acted]>0)                                 # coverage-selection guard
    cov_corr=np.corrcoef(stream[acted]>0, up_mkt)[0,1] if len(set(up_mkt))>1 else float('nan')
    print(f"  {label:34s} acted={n:4d}  acc={acc*100:5.1f}%  LB={lb*100:4.0f}%  corr(acted_dir,mkt_up)={cov_corr:+.2f}")
    return dict(label=label,acted=n,acc=acc,lb=lb,cov_corr=cov_corr)

if __name__=='__main__':
    m=build()
    N=len(m)
    print("="*100)
    print(f"ZION STAGE 4 — CONVERGENCE (SPY monthly)   spine decision-months={N}  {m.Date.min().date()}..{m.Date.max().date()}")
    print("="*100)
    # engine presence / standalone
    for c,nm in [('rd','RED DAWN'),('od','ODYSSEY'),('sc','SANCTUARY')]:
        pr=m[c].notna(); acc=(m.loc[pr,c].to_numpy()==m.loc[pr,'y'].to_numpy()).mean()
        print(f"  [{nm:9s}] present={int(pr.sum()):4d}  standalone dir acc={acc*100:.1f}%")
    print("-"*100)
    print("BASELINE:  RED DAWN standalone (all present months) is the number to beat.\n")

    sets={'2-engine (RD+ODY)':['rd','od'], '3-engine (RD+ODY+SANC)':['rd','od','sc']}
    rows=[]
    for sname,cols in sets.items():
        print(f"[SET] {sname}")
        for mode in (['unanimous'] if len(cols)==2 else ['unanimous','majority']):
            agreed,present=gate_stream(m,cols,mode)
            both=int((present>=2).sum())
            print(f"  -- gate={mode}  (months with >=2 engines present = {both})")
            rows.append(summ(m,agreed,f"A. pure agreement [{mode}]"))
            acted_b=record_gate(m,agreed)
            rows.append(summ(m,acted_b,f"B. gated LB>{LB_BAR:.2f} n>={N_FLOOR} [{mode}]"))
        print()
    # high-conviction core: all three present AND unanimous
    allp=m[['rd','od','sc']].notna().all(axis=1)
    core=allp & (m['rd']==m['od']) & (m['od']==m['sc'])
    if core.sum()>0:
        y=m.y.to_numpy(); cc=core.to_numpy()
        acc=(m['rd'].to_numpy()[cc]==y[cc]).mean(); lb=E.wlb(int((m['rd'].to_numpy()[cc]==y[cc]).sum()),int(cc.sum()))
        print(f"[CORE] all-3-present & unanimous: n={int(cc.sum())}  acc={acc*100:.1f}%  LB={lb*100:.0f}%")

    # write integrated convergence ledger
    m.to_csv("/Users/castaglia/Desktop/ZION/stage4_convergence/spy_convergence_ledger.csv",index=False)
    print("-"*100); print("wrote spy_convergence_ledger.csv")

"""Sequential PIT direction test of Health Care CAPE / CAPEG on XLV at horizons 1, 3, 6 months.
Cell grammar per predictor: ternary level-z (expanding mean/sd, dead zone 0.2 sd) x ternary k=6 change (expanding sd);
direction = expanding majority of realised H-month sign in that cell (labels only where t+H <= now-of-decision), min cell n=10;
warm-up 36 months. Overlapping H>1 labels -> also report the non-overlapping (H-spaced) subset and its Wilson LB95."""
import pandas as pd, numpy as np, sys
S = pd.read_csv("results/hc_cape_monthly.csv", parse_dates=["Date"]).set_index("Date")
px = pd.read_csv("/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/XLV_daily.csv", index_col=0, parse_dates=True)["Adj Close"].resample("MS").first()
S["px"] = px.reindex(S.index)
spy = pd.read_csv("/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/SPY_daily.csv", index_col=0, parse_dates=True)["Adj Close"].resample("MS").first()
S["spy"] = spy.reindex(S.index)
REL = len(sys.argv) > 1 and sys.argv[1] == "relative"
def wlb(p,n,z=1.96): return (p+z*z/(2*n)-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n) if n else 0
def test(col, H, k=6, dz=0.2, minn=10, warm=36):
    x = S[col].values; P = S.px.values; T=len(x)
    Q = S.spy.values
    m = (P[H:]/P[:-H]-1) - ((Q[H:]/Q[:-H]-1) if REL else 0); m = np.sign(m); m = np.append(m, [np.nan]*H)   # label: H-month direction, relative to SPY if REL
    dx = pd.Series(x).diff(k).values; res=[]
    for t in range(T):
        if np.isnan(x[t]) or np.isnan(dx[t]) or np.isnan(m[t]) or m[t]==0: continue
        hist_idx = [i for i in range(t) if not np.isnan(x[i]) and not np.isnan(dx[i])]
        if len(hist_idx) < warm: continue
        hx = x[hist_idx]; hd = dx[hist_idx]
        zl=(x[t]-hx.mean())/hx.std(); zc=dx[t]/hd.std()
        tl=1 if zl>dz else (-1 if zl<-dz else 0); tc=1 if zc>dz else (-1 if zc<-dz else 0)
        # cells from months whose H-month label was KNOWN at t: i + H <= t
        known=[i for i in hist_idx if i+H<=t and not np.isnan(m[i]) and m[i]!=0]
        if not known: continue
        zL=(x[known]-hx.mean())/hx.std(); zC=dx[known]/hd.std()
        TL=np.where(zL>dz,1,np.where(zL<-dz,-1,0)); TC=np.where(zC>dz,1,np.where(zC<-dz,-1,0))
        sel=(TL==tl)&(TC==tc)
        if sel.sum()<minn: continue
        up=(m[np.array(known)][sel]>0).mean(); D=1 if up>=0.5 else -1
        res.append((t,D,m[t]))
    if not res: return None
    n=len(res); acc=np.mean([D==mm for _,D,mm in res]); drift=np.mean([mm>0 for _,_,mm in res]); ls=np.mean([D>0 for _,D,_ in res])
    # non-overlapping subset
    pick=[]; last=-10**9
    for t,D,mm in res:
        if t-last>=H: pick.append((D,mm)); last=t
    nn=len(pick); nacc=np.mean([D==mm for D,mm in pick]); ndrift=np.mean([mm>0 for _,mm in pick])
    scored=[i for i in range(T) if not np.isnan(m[i]) and m[i]!=0 and not np.isnan(x[i])]
    maj=max(drift,1-drift)
    return dict(n=n, acc=acc, drift=drift, edge=acc-drift, maj=maj, edge2=acc-maj, long=ls, nn=nn, nacc=nacc, nlb=wlb(nacc,nn), ndrift=ndrift, cov=n/len(scored))
print("Health Care (XLV) — sequential PIT —", "RELATIVE label (XLV minus SPY)" if REL else "absolute label", "— CAPE10 from 2014-03, CAPE5 from 2011-03")
print(f"{'predictor':8s} {'H':>2s} {'acted':>5s} {'cov':>5s} {'acc':>6s} {'up%':>6s} {'major':>6s} {'edge':>6s} {'long':>5s} | non-overlap n  acc   LB95  up%")
for col in ["CAPE10","CAPEG","CAPE5","CAPE5G"]:
    for H in (1,3,6):
        r=test(col,H)
        if r is None: print(f"{col:8s} {H:2d}  (no cells)"); continue
        print(f"{col:8s} {H:2d} {r['n']:5d} {r['cov']:5.0%} {r['acc']:6.1%} {r['drift']:6.1%} {r['maj']:6.1%} {r['edge2']:+6.1%} {r['long']:5.0%} | {r['nn']:3d}  {r['nacc']:5.1%} {r['nlb']:5.1%} {r['ndrift']:5.1%}")

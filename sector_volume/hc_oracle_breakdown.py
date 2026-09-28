import importlib.util, numpy as np, pandas as pd, json
spec=importlib.util.spec_from_file_location("ot","hc_oracle_types.py"); ot=importlib.util.module_from_spec(spec); spec.loader.exec_module(ot)
S=pd.read_csv("results/hc_cape_monthly.csv",parse_dates=["Date"])
xlv=pd.read_csv(ot.SCR+"/XLV_daily.csv",index_col=0,parse_dates=True)["Close"].resample("MS").first(); spy=pd.read_csv(ot.SCR+"/SPY_daily.csv",index_col=0,parse_dates=True)["Close"].resample("MS").first()
S["abs"]=xlv.reindex(S.Date).values; S["rel"]=(xlv/spy).reindex(S.Date).values
def calls(name,label,N):
    cfg=ot.ANCHORS[name]; S["out"]=S["abs"] if label=="absolute" else S["rel"]
    cols=["Date","out",cfg["num"],cfg["den"]]+([cfg["ratio"]] if cfg["ratio"] else []); d=S[cols].dropna().reset_index(drop=True)
    out=d.out.to_numpy(float); num=d[cfg["num"]].to_numpy(float); den=d[cfg["den"]].to_numpy(float); ratio=d[cfg["ratio"]].to_numpy(float) if cfg["ratio"] else num/den
    nxt=np.sign(np.concatenate([out[1:]/out[:-1]-1,[np.nan]])); cut=int(len(d)*0.4); gr,gn,gd=ot.pc(ratio,N),ot.pc(num,N),ot.pc(den,N); res=[]
    for t in range(cut,len(d)):
        if np.isnan(gr[t]): continue
        tr=np.arange(0,t); tr=tr[(~np.isnan(gr[tr]))&(~np.isnan(gn[tr]))&(~np.isnan(gd[tr]))&(~np.isnan(nxt[tr]))&(nxt[tr]!=0)]
        if len(tr)<ot.MIN_TRAIN: continue
        def tern(a):
            mu=a[tr].mean(); sd=a[tr].std(); zz=(a-mu)/sd if sd>0 else a*0; r=np.zeros(len(a),int); r[zz>ot.SD]=1; r[zz<-ot.SD]=-1; return r
        cc,cp,ce=tern(gr),tern(gn),tern(gd); typ=(cc+1)*9+(cp+1)*3+(ce+1); same=tr[typ[tr]==typ[t]]; seg=same if len(same)>0 else tr
        up=(nxt[seg]>0).sum(); dn=(nxt[seg]<0).sum(); pred=1 if up>=dn else -1
        res.append((d.Date[t],pred,nxt[t],int(typ[t])+1,len(same),up,dn))
    return pd.DataFrame(res,columns=["Date","pred","mkt","typ","n_same","up","dn"])
out={}
for name,N in (("PE_G",3),("PE",3),("P_G",3)):
    c=calls(name,"absolute",N); scored=c.dropna(subset=["mkt"]); scored=scored[scored.mkt!=0].copy(); scored["hit"]=scored.pred==scored.mkt
    L=scored[scored.pred>0]; Sh=scored[scored.pred<0]
    print(f"\n{name} absolute N={N}: n={len(scored)} acc {scored.hit.mean():.1%} | LONG {len(L)} calls: months up {(L.mkt>0).mean():.1%} vs unconditional up-rate {(scored.mkt>0).mean():.1%} | SHORT {len(Sh)} calls: months down {(Sh.mkt<0).mean():.1%} vs unconditional down-rate {(scored.mkt<0).mean():.1%}")
    print("   by year:", {int(y):f"{g.hit.mean():.0%}/{len(g)}" for y,g in scored.groupby(scored.Date.dt.year)})
    print("   fallback months (no same-type history):", int((scored.n_same==0).sum()), "| types used:", scored.typ.value_counts().head(6).to_dict())
    pend=c[c.mkt.isna()]
    print("   last 4 scored:", [(str(r.Date.date()), int(r.pred), int(r.mkt)) for r in scored.tail(4).itertuples()], "| PENDING current call:", [(str(r.Date.date()), int(r.pred), f"type T{r.typ} same-type hist {r.n_same} (up {r.up}/dn {r.dn})") for r in pend.itertuples()])
    out[name]=dict(n=len(scored), acc=float(scored.hit.mean()), long_n=len(L), long_up=float((L.mkt>0).mean()), short_n=len(Sh), short_down=float((Sh.mkt<0).mean()), up_rate=float((scored.mkt>0).mean()),
                   by_year={int(y):[round(float(g.hit.mean()),3),len(g)] for y,g in scored.groupby(scored.Date.dt.year)}, fallback=int((scored.n_same==0).sum()),
                   pending=[dict(date=str(r.Date.date()), call=int(r.pred), typ=int(r.typ), n_same=int(r.n_same), up=int(r.up), dn=int(r.dn)) for r in pend.itertuples()])
json.dump(out, open("results/hc_oracle_breakdown.json","w"), indent=1)

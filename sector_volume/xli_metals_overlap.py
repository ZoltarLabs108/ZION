"""Materials (XLI) integrated calls vs the precious-metals calls already in the ecosystem:
 (a) monthly SYZYGY Gold and Silver directional positions (ZION_MULTIASSET per_sleeve_ledger, variant without_cells = base type-level);
 (b) the book's silver micro (netting ledger SILVER bucket) and gold ballast (always-on, not a guess).
Overlap = months both act; agreement = same sign; plus correlation of the return streams."""
import pandas as pd, numpy as np
SCR="/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/"
J=pd.read_csv("results/XLI/integrated_ledger.csv"); J=J[J.type_state!="warm-up"].copy(); J["m"]=pd.to_datetime(J.date).dt.strftime("%Y-%m")
P=pd.read_csv("/Users/castaglia/Desktop/ZION_MULTIASSET/reports/per_sleeve_ledger.csv"); P["m"]=pd.to_datetime(P.date).dt.strftime("%Y-%m")
base=P[P.variant=="without_cells"]
gold=base[base.sleeve=="Gold"].set_index("m").position; silver=base[base.sleeve=="Silver"].set_index("m").position
x=J.set_index("m").call
m=lambda t: pd.read_csv(SCR+f"{t}_daily.csv",index_col=0,parse_dates=True)["Adj Close"].resample("MS").first().pct_change().shift(-1)
rx=m("XLI"); rg=m("GLD"); rs=m("SLV"); idx=pd.to_datetime(x.index+"-01")
for nm,pos,r in (("Gold monthly call",gold,rg),("Silver monthly call",silver,rs)):
    p=pos.reindex(x.index).fillna(0); both=(x!=0)&(p!=0)
    print(f"{nm}: metal acts in {int((p!=0).sum())}/{len(p)} months (long {int((p>0).sum())}, short {int((p<0).sum())}); XLI acts {int((x!=0).sum())}; BOTH act {int(both.sum())}; agree when both {((np.sign(x)==np.sign(p))[both]).mean() if both.any() else float('nan'):.0%}")
    sx=pd.Series(x.values*rx.reindex(idx).values,index=x.index); sp=pd.Series(p.values*r.reindex(idx).values,index=x.index); ok=sx.notna()&sp.notna()
    print(f"   return-stream corr (XLI sleeve vs {nm.split()[0]} sleeve): {np.corrcoef(sx[ok],sp[ok])[0,1]:+.2f}; XLI call vs {nm.split()[0]} NEXT-month return corr: {np.corrcoef(x[ok],r.reindex(idx)[ok.values])[0,1]:+.2f}")
L=pd.read_csv("/Users/castaglia/Desktop/ZION/weekly/unified/reports/netting_ledger.csv",parse_dates=["week"]); L["m"]=L.week.dt.strftime("%Y-%m"); mic=L.groupby("m").SILVER.first().reindex(x.index).fillna(0)
both=(x!=0)&(mic!=0); print(f"Silver micro (book) active in {int((mic!=0).sum())} months; both act {int(both.sum())}; agree {((np.sign(x)==np.sign(mic))[both]).mean() if both.any() else float('nan'):.0%}")
print(f"XLI integrated call: long {int((x>0).sum())} short {int((x<0).sum())} abstain {int((x==0).sum())}")

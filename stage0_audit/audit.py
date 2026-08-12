"""
ZION STAGE 0 — DATA AUDIT GATE (Gold).
Row-level audit of the monthly core dataset BEFORE any modeling.
Writes audit_pass.flag; the spine is hard-gated on it.
Checks: identity, anchor integrity, target alignment, per-feature PIT/quality,
        basis-splice detection. Emits a structured diagnostic report.
"""
import pandas as pd, numpy as np, json, sys

PANEL="/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
OUTCOME="Gold_Close"
GROUNDED=['Dollar_Index','M2_Money','Industrial_Production','GS10_Rate','Fed_Funds_Rate',
          'US_2Y_Treasury','Copper_Close','WTI_Crude_Close','Gold_Close','Term_Spread_10Y_2Y']
ALWAYS=['US_CPI']
LAGGED={'Industrial_Production','US_CPI','M2_Money'}           # mid-month publish -> PIT lag
RATE_LIKE={'GS10_Rate','Fed_Funds_Rate','US_2Y_Treasury','Term_Spread_10Y_2Y'}  # can be ~0/neg
SPLICE_JUMP=0.60; SPLICE_PP=3.0; SEP_WIN=24                    # pct for prices; pp for rates
cols=sorted(set(GROUNDED)|set(ALWAYS))

df=pd.read_csv(PANEL); df["Date"]=pd.to_datetime(df["Date"])
n_rows=len(df)

def splice_scan(s, rate_like=False):
    v=s.dropna()
    if len(v)<2*SEP_WIN: return "n/a",0
    # unit-aware jump: absolute points for rates/spreads (zero-safe), pct for price levels
    j_metric=(v.diff().abs() if rate_like else v.pct_change().abs()).to_numpy()
    thr=SPLICE_PP if rate_like else SPLICE_JUMP
    jumps=np.where(j_metric>thr)[0]
    splices=0
    for j in jumps:
        if j<SEP_WIN or j>len(v)-SEP_WIN: continue
        pre=v.iloc[j-SEP_WIN:j]; post=v.iloc[j:j+SEP_WIN]
        if pre.max()<post.min() or post.max()<pre.min(): splices+=1   # full level separation
    return ("SPLICE" if splices else ("spike" if len(jumps) else "clean")), splices

# ---- anchor integrity ----
mono=bool(df["Date"].is_monotonic_increasing)
dups=int(df["Date"].duplicated().sum())
gaps=int((df["Date"].diff().dt.days>35).sum())

# ---- target alignment ----
g=df[OUTCOME]
ret=g.pct_change().shift(-1); ydir=np.sign(ret)
usable=ret.notna()&(ydir!=0)&g.notna()
n_t=int(usable.sum()); up=int((ydir[usable]>0).sum()); dn=int((ydir[usable]<0).sum())
tstart=df.loc[g.notna(),"Date"].min()

# ---- per-feature audit ----
feat=[]
hard_block=[]
for c in cols:
    s=df[c]; nn=int(s.notna().sum()); cov=nn/n_rows
    rng=(df.loc[s.notna(),"Date"].min(), df.loc[s.notna(),"Date"].max()) if nn else (None,None)
    zeros=int((s==0).sum())
    v=s.dropna(); stale=int((v.diff()==0).sum())
    kind,ns=splice_scan(s, rate_like=(c in RATE_LIKE))
    lag="LAG" if c in LAGGED else "-"
    if kind=="SPLICE": hard_block.append(c)
    feat.append(dict(col=c,nn=nn,cov=cov,start=str(rng[0].date()) if rng[0] is not None else "-",
                     zeros=zeros,stale=stale,splice=kind,lag=lag))

ok = mono and dups==0 and not hard_block
verdict="PASS" if ok else "BLOCK"

# ---- report ----
W=100
print("="*W); print("ZION STAGE 0 — DATA AUDIT  |  outcome: Gold_Close  |  panel: combined_macro_0826.csv"); print("="*W)
print(f"[identity]   rows={n_rows}   feature cols audited={len(cols)}   panel range {df['Date'].min().date()} -> {df['Date'].max().date()}")
print(f"[anchor]     monotonic={mono}   duplicate_dates={dups}   month_gaps(>35d)={gaps}")
print(f"[target]     def=sign(Gold_Close.pct_change().shift(-1)) [1-mo dir]   usable={n_t}   up={up} ({up/n_t*100:.1f}%)  down={dn} ({dn/n_t*100:.1f}%)   first Gold row {tstart.date()}")
print("-"*W)
print(f"{'feature':22s} {'nonnull':>7s} {'cov%':>6s} {'start':>11s} {'zeros':>6s} {'stale':>6s} {'splice':>7s} {'PITlag':>6s}")
print("-"*W)
for f in feat:
    print(f"{f['col']:22s} {f['nn']:7d} {f['cov']*100:5.1f}% {f['start']:>11s} {f['zeros']:6d} {f['stale']:6d} {f['splice']:>7s} {f['lag']:>6s}")
print("-"*W)
print(f"[gate]  Date monotonic: {'OK' if mono else 'FAIL'}   dup dates: {'OK' if dups==0 else 'FAIL'}   hard splices: {'none' if not hard_block else ','.join(hard_block)}")
print(f"[VERDICT]  {verdict}")
print("="*W)

flag={"verdict":verdict,"ok":ok,"n_rows":n_rows,"target_usable":n_t,"up_rate":up/n_t,
      "anchor":{"monotonic":mono,"dups":dups,"gaps":gaps},"hard_splices":hard_block,
      "features":feat}
open("/Users/castaglia/Desktop/ZION/stage0_audit/audit_pass.flag","w").write(json.dumps(flag,indent=2))
print(f"wrote audit_pass.flag  (verdict={verdict})")
sys.exit(0 if ok else 1)

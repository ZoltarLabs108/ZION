"""Sequential walk-forward (seq_wf mechanics) with the TAILORED sector pool + PIT lags, at horizon H. Usage: TK H"""
import sys, os, json, time, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sector_recipe as SR, seq_wf as W
import lib_pipeline as L
tk, H = sys.argv[1], int(sys.argv[2]); REL = len(sys.argv) > 3 and sys.argv[3] == "relative"
ANCHOR = len(sys.argv) > 4 and sys.argv[4] == "anchor"   # anchor-only: 27 types of (CAPE10, g10) alone, no other legs
names = SR.install(tk); col = SR.SECTORS[tk][0]
exclude = [] if tk == "XLB" else ["Copper_Close"]
if ANCHOR:
    names = [f"{tk}_CAPE10", f"{tk}_g10"]; exclude = list(L.GROUNDED)      # only the anchor pair survives into the grammar
d = L.load_asset(col, 1998, extra_vars=names, exclude_vars=exclude, h_label=H)
if ANCHOR:
    d.attrs["extra_vars"] = names
    first = int(d[names].dropna().index.min()); attrs = dict(d.attrs)
    d = d.iloc[first:].reset_index(drop=True); d.attrs.update(attrs)      # history starts where the anchor starts
    W.T0 = 60                                                              # first decision after 60 rows (in-fold train >= 30)
price = d[col].values.astype(float); T = len(d)
spy = pd.read_csv(os.path.join(SR.SCR, "SPY_daily.csv"), index_col=0, parse_dates=True)["Close"].resample("MS").first()
d["_spy"] = spy.reindex(pd.to_datetime(d["Date"])).values
def label(frame):
    """H-month direction; RELATIVE = sign(sector H-return minus SPY H-return) — market drift stripped."""
    r = frame[col].pct_change(H).shift(-H)
    if REL: r = r - frame["_spy"].pct_change(H).shift(-H)
    return np.sign(r)
mkt_true = label(d).values
dates = d["Date"].dt.strftime("%Y-%m").values; floor = L.PER_ASSET_VA_FLOOR.get(tk, L.VA_LB_FLOOR)
ledger = []; t0 = time.time()
for t in range(W.T0, T):
    dft = d.iloc[:t+1].copy(); dft.attrs.update(d.attrs)
    dft["mkt"] = label(dft)
    try: rd, used, ncov, te, lb = L.red_dawn_cascade(dft, va_lb_floor=floor)
    except Exception: rd = None
    if rd is None or not dft.attrs.get("rd_meta"):
        ledger.append(dict(i=t, date=dates[t], call=0, conv=0.0, known=True, pair="", vol_leg=False, mkt=None if np.isnan(mkt_true[t]) else int(mkt_true[t]), rounds=0)); continue
    frz = {"rounds": dft.attrs["rd_meta"]}; sig, conv, rnd, known = L.classify_frozen(dft, frz); r = int(rnd[t])
    pair = "|".join(frz["rounds"][r-1]["pair"]) if r > 0 else ""
    ledger.append(dict(i=t, date=dates[t], call=int(sig[t]), conv=round(float(conv[t]),3), known=bool(known[t]), pair=pair, vol_leg=False,
                       mkt=None if np.isnan(mkt_true[t]) else int(mkt_true[t]), rounds=len(frz["rounds"])))
summ = W.summarize(tk, f"{'anchor' if ANCHOR else 'tailored'}_{'rel' if REL else 'abs'}_H{H}", ledger, time.time()-t0)
# non-overlapping subset for H>1
acted = [r for r in ledger if r["call"] != 0 and r["mkt"] not in (None, 0)]; pick=[]; last=-10**9
for r in acted:
    if r["i"]-last >= H: pick.append(r); last = r["i"]
if pick:
    nacc = float(np.mean([r["call"]==r["mkt"] for r in pick])); summ["nonoverlap"] = dict(n=len(pick), acc=round(nacc,4), lb95=round(W.wilson_lb_95(nacc, len(pick)),4), drift=round(float(np.mean([r["mkt"]>0 for r in pick])),4))
from collections import Counter
summ["pairs_at_acted"] = Counter(r["pair"] for r in acted).most_common(8)
json.dump(dict(summary=summ, ledger=ledger), open(os.path.join(W.OUT_DIR, f"{tk}_{'anchor' if ANCHOR else 'tailored'}_{'rel' if REL else 'abs'}_H{H}.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != "by_year"}))

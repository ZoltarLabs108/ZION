"""
portfolio_integration_seq.py — backtest vs OOS-validated (sequential) integration of the sector block.

Sources compared, same instruments (the six admitted: XLV/XLF/XLY/XLI sleeves, XLE pair, XLK short-only overlay), same weights:
  backtest        results/<TK>/integrated_ledger.csv  (pull set + anchor chosen on the whole record; the published numbers)
  seq-fixed       results/sequential/<TK>_fixed_tape.csv   anchor held; pulls / cascade / tier admission refit on data <= t
  seq-strict      results/sequential/<TK>_strict_tape.csv  as above, and the anchor itself re-chosen by R1 on data <= t
  seq-*_e3        training frontier t-3 (the ZION 3-month embargo), horizon 1
  seq-*_h3        3-month outcome horizon; P&L as an overlapping ladder (each call = 1/3 notional held three months)
  seq-strict + admission : an instrument contributes at t only if on its OWN sequential record <= t-1 it had >= 12 resolved months,
                  DECISION LB (z=1.645) > 0.45, edge > 0 vs its majority class, |corr| < 0.30 with the universe and a throttled
                  Sortino lift > 0 at 5% (the R1 / DECISION / R5 gates applied as the tape would apply them).
Window: extended to the first decision month of any instrument (zero before an instrument's first call), plus the published 62-month
window.  Weights: B equal-gross under the 15% cap (primary; nothing is fitted on the sequential streams) and the published Sortino
weights C (fitted on the backtest streams, applied unchanged).  Leverage 1x / 2.5x / 4.0x.
Writes results/sequential/integration_compare.{json,md}.  Touches nothing under results/<TK>/ or the live reports.
"""
import os, sys, json, glob, re
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); SEQ = os.path.join(HERE, "results", "sequential")
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"
REP = "/Users/castaglia/Desktop/ZION/weekly/unified/reports"
SECTOR_CAP = 0.15; EXEC_LEV = 2.5; CAPITAL = 100000
KIND = {"XLV": "sleeve", "XLF": "sleeve", "XLY": "sleeve", "XLI": "sleeve", "XLE": "pair", "XLK": "overlay"}
ALL = ["XLV", "XLF", "XLY", "XLE", "XLK", "XLI", "XLB", "XLP", "XLU"]
W_ADM = {"sleeve": 0.05, "pair": 0.025, "overlay": 0.05}; GROSS = {"sleeve": 0.05, "pair": 0.05, "overlay": 0.05}
PUB_C = json.load(open(os.path.join(HERE, "results", "portfolio_integration_all.json")))["variants"]["C"]["weights"]


def wlb(p, n, z=1.96): return (p + z*z/(2*n) - z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)))/(1 + z*z/n) if n else 0.0
def st(x, per=12):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n == 0: return (np.nan, np.nan, np.nan)
    cg = np.prod(1 + x) ** (per / n) - 1; dn = x[x < 0]; so = (x.mean() * per) / (dn.std(ddof=1) * np.sqrt(per)) if len(dn) > 1 else np.nan; eq = np.cumprod(1 + x)
    return float(cg), float(so), float((eq / np.maximum.accumulate(eq) - 1).min())
def monthly(t): return pd.read_csv(os.path.join(SCR, f"{t}_daily.csv"), index_col=0, parse_dates=True)["Adj Close"].resample("MS").first().pct_change().shift(-1)
def mkey(idx): return pd.Index(pd.to_datetime(idx)).strftime("%Y-%m")

L = pd.read_csv(os.path.join(REP, "netting_ledger.csv"), parse_dates=["week"]); L["m"] = L.week.dt.strftime("%Y-%m"); F = L.groupby("m").first()
U = pd.read_csv(os.path.join(REP, "universe_monthly_backtest.csv")).set_index("month"); spy_m = monthly("SPY"); _PX = {}
if "--base" in sys.argv and sys.argv[sys.argv.index("--base") + 1] == "sequential":      # base = the sequentially re-derived universe (universe_sequential_book.py)
    _S = pd.read_csv(os.path.join(HERE, "results", "sequential_universe", "universe_sequential_monthly.csv"), index_col=0)
    U = U.copy(); U["uni_1x"] = _S["universe_seq"].reindex(U.index).values; SEQ_TAG = "_seqbase"
else: SEQ_TAG = ""
def per_unit(tk, rel):
    if tk not in _PX: _PX[tk] = monthly(tk)
    r = _PX[tk]; r = (r - spy_m.reindex(r.index)) if rel else r; return pd.Series(r.values, index=mkey(r.index))


def load_backtest(tk, kind):
    J = pd.read_csv(os.path.join(HERE, "results", tk, "integrated_ledger.csv")); J = J[J.type_state != "warm-up"].copy(); J["m"] = mkey(J.date)
    tape = pd.read_csv(os.path.join(HERE, "results", tk, f"{tk}_forward_tape.csv")); rel = str(tape.iloc[-1].get("label", "absolute")) == "relative"
    calls = J.set_index("m").call.astype(float); lab = J.set_index("m").lab.astype(float)
    if kind == "overlay": calls = calls.where(calls < 0, 0.0)
    ret = (calls * per_unit(tk, rel).reindex(calls.index)).fillna(0.0)
    return dict(calls=calls, lab=lab, ret=ret, pos=calls)


def load_seq(tk, mode, kind):
    p = os.path.join(SEQ, f"{tk}_{mode}_tape.csv")
    if not os.path.exists(p): return None
    T = pd.read_csv(p); T["m"] = mkey(T.date); T = T.set_index("m")
    if "note" not in T.columns: T["note"] = ""
    zd = (T.source == "error") & T.note.astype(str).str.contains("ZeroDivisionError")      # MP diagnostics with no scored phase-1 decision = warm-up
    T.loc[zd, "source"] = "warm-up"; T.loc[zd, "type_state"] = "warm-up"
    calls = T.call.astype(float); lab = T.lab.astype(float)
    if kind == "overlay": calls = calls.where(calls < 0, 0.0)
    H = int(re.search(r"_h(\d+)", mode).group(1)) if re.search(r"_h(\d+)", mode) else 1
    relcol = (T.label.fillna("absolute") == "relative")
    if H == 1:
        ret = pd.Series([calls[m] * (per_unit(tk, bool(relcol[m])).get(m, np.nan)) for m in calls.index], index=calls.index).fillna(0.0); pos = calls
    else:   # overlapping ladder: a call issued at i is 1/H notional held over months i .. i+H-1
        months = list(calls.index); ret = pd.Series(0.0, index=months); pos = pd.Series(0.0, index=months); allm = sorted(set(months) | set(per_unit(tk, False).index))
        for m in months:
            if calls[m] == 0: continue
            pu = per_unit(tk, bool(relcol[m])); j = allm.index(m)
            for k in range(H):
                if j + k < len(allm) and allm[j + k] in ret.index:
                    r_ = pu.get(allm[j + k], np.nan); ret[allm[j + k]] += calls[m] / H * (0.0 if r_ != r_ else r_); pos[allm[j + k]] += calls[m] / H
    return dict(calls=calls, lab=lab, ret=ret.fillna(0.0), pos=pos, T=T)


def record(calls, lab):
    a = calls[(calls != 0) & lab.notna() & (lab != 0)]; n = len(a)
    if not n: return dict(acted=0, acc=None, lb95=None, majority=None, edge=None, long_n=0, short_n=0, dec_lb=None)
    hit = (a == lab[a.index]).astype(float); acc = float(hit.mean()); up = float((lab[a.index] > 0).mean()); maj = max(up, 1 - up)
    return dict(acted=int(n), acc=acc, lb95=float(wlb(acc, n)), majority=maj, edge=acc - maj, long_n=int((a > 0).sum()), short_n=int((a < 0).sum()), dec_lb=float(wlb(acc, n, 1.645)))


def streams(src, months):
    """unit-notional monthly return per instrument, lev-scaled and class-throttled, over `months` (zero where inactive)."""
    out = {}
    for tk, kind in KIND.items():
        d = src.get(tk)
        if d is None: continue
        s = pd.Series([d["ret"].get(m, 0.0) * F.loc[m, "lev"] * (1.0 if (kind == "overlay" or F.loc[m, "thr"] >= 1.0) else 0.0) for m in months], index=months)
        out[tk] = s.fillna(0.0)
    return pd.DataFrame(out)


def weights(variant, S):
    g = {tk: GROSS[KIND[tk]] for tk in S}; tot = sum(g.values())
    if variant == "B": return {tk: W_ADM[KIND[tk]] * SECTOR_CAP / tot for tk in S}
    return {tk: PUB_C.get(tk, 0.0) for tk in S}


def seq_admission(S, src, base, months):
    """instrument on at t only if its own record through t-1 clears the gates (>=12 resolved, DECISION LB>0.45, edge>0, |corr|<0.30, lift>0)."""
    on = pd.DataFrame(0.0, index=months, columns=S.columns); first = {}
    for tk in S.columns:
        s = S[tk]; pos = src[tk]["pos"]
        for i, m in enumerate(months):
            h = s.iloc[:i]; act = h[h != 0]
            if len(act) < 12: continue
            sgn = np.sign(pos.reindex(act.index).fillna(0.0).values); hits = (np.sign(act.values) > 0).astype(float)      # call x return > 0 = hit
            acc = float(hits.mean()); n = len(act); lab = np.sign(act.values) * sgn; maj = max(float((lab > 0).mean()), float((lab < 0).mean()))
            corr = float(np.corrcoef(h, base.iloc[:i])[0, 1]) if h.std() > 0 else 0.0
            lift = st(base.iloc[:i] + 0.05 * h)[1] - st(base.iloc[:i])[1]
            if wlb(acc, n, 1.645) > 0.45 and acc > maj and abs(corr) < 0.30 and lift > 0:
                on.loc[m, tk] = 1.0; first.setdefault(tk, m)
    return on, first


def main():
    modes = sorted({re.sub(r"^[A-Z]+_", "", os.path.basename(p)[:-9]) for p in glob.glob(os.path.join(SEQ, "*_tape.csv"))})
    modes = [m for m in modes if all(os.path.exists(os.path.join(SEQ, f"{tk}_{m}_tape.csv")) for tk in KIND)]
    order = ["fixed", "strict", "fixed_e3", "strict_e3", "fixed_h3", "strict_h3"]; modes = [m for m in order if m in modes] + [m for m in modes if m not in order]
    sources = {"backtest": {tk: load_backtest(tk, k) for tk, k in KIND.items()}}
    for m in modes: sources[f"seq-{m}"] = {tk: load_seq(tk, m, k) for tk, k in KIND.items()}
    print("sources:", list(sources))
    rec_rows = []
    for tk in ALL:
        row = dict(sector=tk, kind=KIND.get(tk, "not admitted"))
        try: b = load_backtest(tk, KIND.get(tk, "sleeve")); r = record(b["calls"], b["lab"]); row.update({f"backtest_{k}": v for k, v in r.items()})
        except Exception as e: row["backtest_note"] = str(e)[:40]
        for m in modes:
            d = load_seq(tk, m, KIND.get(tk, "sleeve"))
            if d is None: continue
            r = record(d["calls"], d["lab"]); row.update({f"{m}_{k}": v for k, v in r.items()})
            T = d["T"]; row[f"{m}_anchors"] = ",".join(f"{k}:{v}" for k, v in T.anchor.fillna("NONE").value_counts().items()); row[f"{m}_sources"] = ",".join(f"{k}:{v}" for k, v in T.source.value_counts().items())
        rec_rows.append(row)
    REC = pd.DataFrame(rec_rows)
    starts = [min(d["calls"].index) for src in sources.values() for d in src.values() if d is not None]
    ext = sorted(m for m in U.index if m in F.index and m >= min(starts) and m <= "2026-07"); pub = [m for m in ext if m >= "2021-06"]
    port_rows = []; block_rows = []; adm_info = {}; unit_rows = []
    for wlab, win in (("extended", ext), ("published 62-mo", pub)):
        base = U.loc[win, "uni_1x"]
        for sname, src in sources.items():
            S = streams(src, win)
            if wlab == "extended":
                for tk in S: c_, s_, d_ = st(S[tk]); unit_rows.append(dict(source=sname, sector=tk, active=int((S[tk] != 0).sum()), CAGR=c_, Sortino=s_, MaxDD=d_, corr_universe=float(np.corrcoef(S[tk], base)[0, 1]) if S[tk].std() > 0 else np.nan))
            variants = [("B equal-gross", weights("B", S), None), ("C published Sortino wts", weights("C", S), None)]
            if sname.startswith("seq-strict"):
                on, first = seq_admission(S, src, base, win); adm_info[f"{wlab}|{sname}"] = first; variants.append(("B equal-gross + sequential admission", weights("B", S), on))
            for vlab, w, on in variants:
                ov = sum(w[tk] * (S[tk] * (on[tk] if on is not None else 1.0)) for tk in S)
                for lev_lab, lv in (("1x", 1.0), ("2.5x", EXEC_LEV), ("4.0x", 4.0)):
                    b = st(base * lv); u = st((base + ov) * lv)
                    port_rows.append(dict(window=wlab, source=sname, variant=vlab, lev=lev_lab, base_CAGR=b[0], base_Sortino=b[1], base_MaxDD=b[2], CAGR=u[0], Sortino=u[1], MaxDD=u[2], dSortino=u[1] - b[1]))
                d = ov * EXEC_LEV * CAPITAL; act = (sum((S[tk] != 0).astype(int) for tk in S) > 0)
                block_rows.append(dict(window=wlab, source=sname, variant=vlab, months=len(win), active=int(act.sum()), up=int((d > 0).sum()), down=int((d < 0).sum()), mean_usd=float(d.mean()), total_usd=float(d.sum()),
                                       worst_usd=float(d.min()), worst_m=str(d.idxmin()), best_usd=float(d.max()), block_MaxDD=st(ov)[2], block_Sortino=st(ov)[1],
                                       uni_down=int((base < 0).sum()), block_down_when_uni_down=int(((base < 0) & (d < 0)).sum())))
    PORT = pd.DataFrame(port_rows); BLK = pd.DataFrame(block_rows); UNIT = pd.DataFrame(unit_rows)
    json.dump(dict(records=REC.to_dict("records"), portfolio=PORT.to_dict("records"), block=BLK.to_dict("records"), unit=UNIT.to_dict("records"), windows=dict(extended=[ext[0], ext[-1], len(ext)], published=[pub[0], pub[-1], len(pub)]), first_admission=adm_info, modes=modes),
              open(os.path.join(SEQ, f"integration_compare{SEQ_TAG}.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 300)
    with open(os.path.join(SEQ, f"integration_compare{SEQ_TAG}.md"), "w") as f:
        def P(s=""): print(s); f.write(s + "\n")
        P(f"# Backtest vs OOS-validated — sector block\nwindows: extended {ext[0]}..{ext[-1]} ({len(ext)} mo); published {pub[0]}..{pub[-1]} ({len(pub)} mo); sources {list(sources)}\n")
        P("## Per-instrument record (acted / acc% / LB95% / majority% / edge pts)")
        for src in ["backtest"] + modes:
            cols = ["sector", "kind"] + [f"{src}_{k}" for k in ("acted", "acc", "lb95", "majority", "edge", "long_n", "short_n") if f"{src}_{k}" in REC.columns]
            R2 = REC[cols].copy()
            for c in R2.columns:
                if c.endswith(("_acc", "_lb95", "_majority", "_edge")): R2[c] = (R2[c].astype(float) * 100).round(1)
            P(f"### {src}"); P(R2.to_string(index=False)); P()
        P("## Sequential anchors used / call sources"); P(REC[["sector"] + [c for c in REC.columns if c.endswith(("_anchors", "_sources"))]].to_string(index=False)); P()
        P("## Unit streams (extended window, lev-scaled, class-throttled)"); P(UNIT.round(3).to_string(index=False)); P()
        P("## Universe with the block"); P2 = PORT.copy()
        for c in ("base_CAGR", "base_MaxDD", "CAGR", "MaxDD"): P2[c] = (P2[c] * 100).round(1)
        P(P2.round(2).to_string(index=False)); P()
        P("## Block only, 2.5x on $100k"); B2 = BLK.copy()
        for c in ("mean_usd", "total_usd", "worst_usd", "best_usd"): B2[c] = B2[c].round(0)
        B2["block_MaxDD"] = (B2.block_MaxDD * 100).round(2); P(B2.round(2).to_string(index=False)); P()
        P(f"first month each instrument would have been admitted on its own sequential record: {adm_info}")


if __name__ == "__main__":
    main()

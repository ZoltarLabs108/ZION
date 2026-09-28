#!/usr/bin/env python3
"""
hc_oracle_types.py — Stage-1 TYPE analysis for Health Care, a faithful port of ZION/stage1_pit_data/oracle_stage.py
(the S&P's Stage 1) to the sector's discretely adjusted legs. Operator spec 2026-09-13: four anchors —
  PE       Price to Earnings:   ratio CAPE10        num RealPrice  den E10      (each leg adjusted the S&P way, pre-ratio)
  PE_G     PE against Growth:   ratio CAPE10/g10    num CAPE10     den g10
  P_G      Price to Growth:     ratio RealPrice/g10 num RealPrice  den g10
  E_G      Earnings to Growth:  ratio E10/g10       num E10        den g10
Legs (from hc_cape.py, all cycle/CPI-adjusted discretely BEFORE any ratio): RealPrice = real market cap of the CAPE10 set;
E10 = its 10-yr smoothed real earnings; g10 = 10-yr log-linear trend of aggregate real earnings (%/yr, always > 0 here).
ORACLE discipline kept verbatim: 27 sub-types = sign triple of pct_change(N) of (ratio, num, den); ±0.5 SD dead zone with
train-only mean/sd; N in {3,6,9,12} swept on the DESIGN sample then FROZEN; sequential one-step-ahead walk-forward with
expanding train (>= 60 rows); prediction = majority next-month sign of the same sub-type (global fallback, NO LB gate —
abstention is deferred to later stages, as in the S&P run); ALL 27 sub-types printed, no truncation.
Sector adaptations (declared): no pre-1990 history -> design sample = first 40% of rows (the recipe's own hygiene fallback),
and the walk-forward starts AFTER the design sample (the S&P's 1990 start is disjoint from its pre-1990 design; keeping
them disjoint here avoids scoring the rows that chose N). Horizon 1 month (operator ruling). Two labels: ABSOLUTE
(XLV next-month sign) and RELATIVE (sign of XLV/SPY next-month change). Annual filings make E10 step yearly, so the
earnings leg's N-month change is zero inside a fiscal year unless N spans a filing — visible in the type counts.
"""
import os, sys, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"
SD = 0.5; Z = 1.96; MIN_TRAIN = 60
ANCHORS = {
    "PE":   dict(num="RealPrice", den="E10", ratio="CAPE10", note="Price to Earnings — real price / 10y smoothed real earnings (sector CAPE)"),
    "PE_G": dict(num="CAPE10", den="g10", ratio=None, note="PE against Growth — CAPE10 / trend real earnings growth (CAPEG)"),
    "P_G":  dict(num="RealPrice", den="g10", ratio=None, note="Price to Growth — real price / trend real earnings growth"),
    "E_G":  dict(num="E10", den="g10", ratio=None, note="Earnings to Growth — smoothed real earnings / trend growth"),
}


def pc(x, N):
    r = np.full(len(x), np.nan); r[N:] = x[N:] / x[:-N] - 1; return r


def wlb(k, n):
    if n <= 0: return 0.0
    p = k / n; d = 1 + Z * Z / n; c = p + Z * Z / (2 * n); m = Z * np.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)); return (c - m) / d


def run(name, S, label):
    cfg = ANCHORS[name]
    cols = ["Date", "out", cfg["num"], cfg["den"]] + ([cfg["ratio"]] if cfg["ratio"] else [])
    d = S[cols].dropna().reset_index(drop=True)
    if len(d) < MIN_TRAIN + 24:
        print(f"[{name}/{label}] INSUFFICIENT DATA ({len(d)} rows) — BLOCK"); return None
    out = d["out"].to_numpy(float); num = d[cfg["num"]].to_numpy(float); den = d[cfg["den"]].to_numpy(float)
    ratio = d[cfg["ratio"]].to_numpy(float) if cfg["ratio"] else num / den
    ratio_name = cfg["ratio"] or f"{cfg['num']}/{cfg['den']}"
    nxt = np.sign(np.concatenate([out[1:] / out[:-1] - 1, [np.nan]]))
    cut = int(len(d) * 0.4); pre = np.arange(len(d)) < cut; dsrc = f"first 40% (< {d.Date.iloc[cut].date()})"
    best = 3; ba = -1; sweep = {}
    for N in range(3, 13, 3):
        rd = np.sign(pc(ratio, N)); m = pre & (~np.isnan(rd)) & (~np.isnan(nxt)) & (rd != 0) & (nxt != 0)
        if m.sum() < 24: continue                       # design sample is short; 24 instead of the S&P's 40 (declared)
        a = (rd[m] == nxt[m]).mean(); sweep[N] = a
        if a > ba: ba = a; best = N
    N = best; gr, gn, gd = pc(ratio, N), pc(num, N), pc(den, N)
    k = n = 0; by = {}; calls = []
    for t in range(cut, len(d)):
        if nxt[t] == 0 or np.isnan(nxt[t]) or np.isnan(gr[t]): continue
        tr = np.arange(0, t); tr = tr[(~np.isnan(gr[tr])) & (~np.isnan(gn[tr])) & (~np.isnan(gd[tr])) & (~np.isnan(nxt[tr])) & (nxt[tr] != 0)]
        if len(tr) < MIN_TRAIN: continue
        def tern(a):
            mu = a[tr].mean(); sd = a[tr].std(); zz = (a - mu) / sd if sd > 0 else a * 0
            r = np.zeros(len(a), int); r[zz > SD] = 1; r[zz < -SD] = -1; return r
        cc, cp, ce = tern(gr), tern(gn), tern(gd); typ = (cc + 1) * 9 + (cp + 1) * 3 + (ce + 1)
        same = tr[typ[tr] == typ[t]]; seg = same if len(same) > 0 else tr
        up = (nxt[seg] > 0).sum(); dn = (nxt[seg] < 0).sum(); pred = 1 if up >= dn else -1
        c = int(pred == nxt[t]); k += c; n += 1; by.setdefault(int(typ[t]), []).append(c); calls.append((pred, nxt[t]))
    flat = "FLAT (no-signal)" if (sweep and max(sweep.values()) - 0.5 < 0.03) else "peaked"
    uprate = np.mean([m > 0 for _, m in calls]) if calls else np.nan; maj = max(uprate, 1 - uprate) if calls else np.nan
    longsh = np.mean([p > 0 for p, _ in calls]) if calls else np.nan
    print("=" * 96); print(f"### ORACLE TYPES — Health Care — {name} — {label} label ###   {cfg['note']}")
    print(f"[provenance] ratio = {ratio_name} | num = {cfg['num']} | den = {cfg['den']} | legs adjusted discretely pre-ratio (CPI-real; 10y smoothing on earnings; trend growth)")
    print(f"[N chosen]   {N} mo  design={dsrc}  sweep {flat}: " + ", ".join(f"{a}:{b*100:.0f}%" for a, b in sorted(sweep.items())))
    print(f"[data]       rows {len(d)}  {d.Date.min().date()}..{d.Date.max().date()}  | walk-forward from {d.Date.iloc[cut].date()} (after design), train >= {MIN_TRAIN}")
    if n:
        print(f"[OVERALL]    ungated 1-step WF: {k/n*100:.1f}%  n={n}  LB {wlb(k,n)*100:.0f}%  | up-rate {uprate*100:.1f}%  majority-class {maj*100:.1f}%  edge vs majority {(k/n-maj)*100:+.1f}  long-share {longsh*100:.0f}%")
    sym = {1: "UP", 0: "flat", -1: "DN"}
    print(" ALL 27 SUB-TYPES | T | ratio/num/den | n | sequential-WF acc | LB:")
    rows = []
    for cs in (1, 0, -1):
        for ps in (1, 0, -1):
            for es in (1, 0, -1):
                ti = (cs + 1) * 9 + (ps + 1) * 3 + (es + 1); v = by.get(ti, [])
                if v:
                    kk = sum(v); nn = len(v); print(f"   T{ti+1:<2} {sym[cs]:>4}/{sym[ps]:>4}/{sym[es]:>4}  n={nn:<4} {kk/nn*100:5.1f}%   LB={wlb(kk,nn)*100:.0f}%")
                    rows.append(dict(T=ti + 1, ratio=sym[cs], num=sym[ps], den=sym[es], n=nn, acc=kk / nn, lb=wlb(kk, nn)))
                else:
                    print(f"   T{ti+1:<2} {sym[cs]:>4}/{sym[ps]:>4}/{sym[es]:>4}  n=0     --")
                    rows.append(dict(T=ti + 1, ratio=sym[cs], num=sym[ps], den=sym[es], n=0, acc=None, lb=None))
    return dict(anchor=name, label=label, N=N, design=dsrc, sweep=sweep, flat=flat, n=n, acc=k / n if n else None, lb=wlb(k, n) if n else None,
                uprate=uprate, majority=maj, long_share=longsh, rows=len(d), types=rows)


def main():
    S = pd.read_csv(os.path.join(HERE, "results", "hc_cape_monthly.csv"), parse_dates=["Date"])
    xlv = pd.read_csv(os.path.join(SCR, "XLV_daily.csv"), index_col=0, parse_dates=True)["Close"].resample("MS").first()
    spy = pd.read_csv(os.path.join(SCR, "SPY_daily.csv"), index_col=0, parse_dates=True)["Close"].resample("MS").first()
    S["abs"] = xlv.reindex(S.Date).values; S["rel"] = (xlv / spy).reindex(S.Date).values
    res = []
    for label in ("absolute", "relative"):
        S["out"] = S["abs"] if label == "absolute" else S["rel"]
        for name in ANCHORS:
            r = run(name, S, label)
            if r: res.append(r)
    json.dump(res, open(os.path.join(HERE, "results", "hc_oracle_types.json"), "w"), indent=1)
    print("\nSUMMARY (ungated sequential WF, horizon 1 month)")
    print(f"{'anchor':6s} {'label':9s} {'N':>2s} {'rows':>4s} {'n':>3s} {'acc':>6s} {'LB':>5s} {'up%':>6s} {'major':>6s} {'edge':>6s} {'long':>5s}  sweep")
    for r in res:
        print(f"{r['anchor']:6s} {r['label']:9s} {r['N']:2d} {r['rows']:4d} {r['n']:3d} {r['acc']*100:5.1f}% {r['lb']*100:4.0f}% {r['uprate']*100:5.1f}% {r['majority']*100:5.1f}% {(r['acc']-r['majority'])*100:+5.1f} {r['long_share']*100:4.0f}%  {r['flat']} " + ", ".join(f"{a}:{b*100:.0f}" for a, b in sorted(r['sweep'].items())))


if __name__ == "__main__":
    main()

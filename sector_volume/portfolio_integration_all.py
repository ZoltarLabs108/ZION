#!/usr/bin/env python3
"""
portfolio_integration_all.py — every ADMITTED sector instrument together, integrated into the ZION universe under the R5 rules,
measured at the MONTHLY level (universe = 0.5 weekly leg + 0.5 monthly leg, the 1x tape basis) and at the WEEKLY level (locked
weekly book x lev, positions held across the weeks of each decision month). Shadow only — no live file touched.

Instruments (from results/<TK>/portfolio.json): full sleeve (absolute or pair) if sizing.admit; short-only overlay if overlay.admit.
Class: sleeves are risk sleeves -> FLAT while the dual throttle is stressed (thr < 1 at the month's first week); overlays are hedge-class
-> unthrottled. Pair sleeves: 2.5% per leg (R5p). Sector total gross cap 15% (R5): allocation variants
  A  as admitted (5% each; pair 2.5%/leg) — for reference, EXCEEDS the cap when > 3 sleeves are admitted
  B  15% cap, equal gross per instrument
  C  15% cap, Sortino-weighted (each instrument's own monthly Sortino over the common window)
  D  15% cap, inverse-vol-weighted
Sortino convention: down-months only, monthly basis (house rule; weekly x sqrt(52) inflates — the weekly ledger is aggregated to months
for the headline and the weekly-basis figure is shown as reference only).
"""
import os, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/"
REP = "/Users/castaglia/Desktop/ZION/weekly/unified/reports"
UNIVERSE_LEV = 3.80; EXEC_LEV = 2.5; SECTOR_CAP = 0.15; W_SLEEVE = 0.05; W_PAIR = 0.025
NAMES = {"XLV": "Health Care", "XLF": "Financials", "XLY": "Consumer Disc", "XLE": "Energy", "XLK": "Technology", "XLI": "Industrials", "XLP": "Cons Staples", "XLB": "Materials", "XLU": "Utilities"}


def st(x, per=12):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); cg = np.prod(1 + x) ** (per / n) - 1; dn = x[x < 0]
    so = (x.mean() * per) / (dn.std(ddof=1) * np.sqrt(per)) if len(dn) > 1 else np.nan; eq = np.cumprod(1 + x); return float(cg), float(so), float((eq / np.maximum.accumulate(eq) - 1).min())


def monthly(t, adj=True): return pd.read_csv(os.path.join(SCR, f"{t}_daily.csv"), index_col=0, parse_dates=True)["Adj Close" if adj else "Close"].resample("MS").first().pct_change().shift(-1)


def weekly_px(t): return pd.read_csv(os.path.join(SCR, f"{t}_daily.csv"), index_col=0, parse_dates=True)["Adj Close"].resample("W-FRI").last()


# ---------------- instruments
L = pd.read_csv(os.path.join(REP, "netting_ledger.csv"), parse_dates=["week"]); L["m"] = L.week.dt.strftime("%Y-%m"); F = L.groupby("m").first()
U = pd.read_csv(os.path.join(REP, "universe_monthly_backtest.csv")).set_index("month"); UB = pd.read_csv(os.path.join(REP, "zion_universe_book.csv")).set_index("month")
spy_m = monthly("SPY"); inst = {}
for tk in NAMES:
    pj = os.path.join(HERE, "results", tk, "portfolio.json"); lj = os.path.join(HERE, "results", tk, "integrated_ledger.csv")
    if not (os.path.exists(pj) and os.path.exists(lj)): continue
    P = json.load(open(pj)); J = pd.read_csv(lj); J = J[J.type_state != "warm-up"].copy(); J["m"] = pd.to_datetime(J.date).dt.strftime("%Y-%m")
    tape = pd.read_csv(os.path.join(HERE, "results", tk, f"{tk}_forward_tape.csv")); rel = str(tape.iloc[-1].get("label", "absolute")) == "relative"
    r = monthly(tk); rs = spy_m.reindex(r.index); per_unit = (r - rs) if rel else r
    kind = None; calls = J.set_index("m").call
    if P.get("sizing") and P["sizing"].get("admit"): kind = "pair" if rel else "sleeve"
    elif P.get("overlay") and P["overlay"].get("admit"): kind = "overlay"; calls = calls.where(calls < 0, 0.0)
    if kind is None: continue
    ret = pd.Series(calls.values * per_unit.reindex(pd.to_datetime(calls.index + "-01")).values, index=calls.index)
    inst[tk] = dict(kind=kind, rel=rel, calls=calls, ret=ret.fillna(0.0), w=(W_PAIR if kind == "pair" else W_SLEEVE), gross=(2 * W_PAIR if kind == "pair" else W_SLEEVE))
print("ADMITTED INSTRUMENTS:", {k: v["kind"] for k, v in inst.items()})
if not inst: raise SystemExit("nothing admitted")
common = sorted(set.intersection(*[set(v["ret"].index) for v in inst.values()]) & set(U.index) & set(F.index)); common = [m for m in common if m >= "2021-06"]
print(f"common window {common[0]}..{common[-1]} ({len(common)} months)")
# throttle per class
thr_on = pd.Series([1.0 if F.loc[m, "thr"] >= 1.0 else 0.0 for m in common], index=common); lev_m = pd.Series([F.loc[m, "lev"] for m in common], index=common)
stream = {}
for tk, v in inst.items():
    s = v["ret"].reindex(common).fillna(0.0) * lev_m * (thr_on if v["kind"] != "overlay" else 1.0)
    stream[tk] = s
S = pd.DataFrame(stream); base = U.loc[common, "uni_1x"]; wk = UB.loc[common, "weekly"]; mo = UB.loc[common, "monthly"]
print("\nunit-weight instrument streams (lev-scaled, class-throttled):"); print(pd.DataFrame({tk: dict(zip(("CAGR", "Sortino", "MaxDD"), st(S[tk]))) for tk in S}).T.round(3).to_string())
C = S.assign(universe=base, weekly_leg=wk, monthly_leg=mo).corr().round(2); print("\ncorrelations:"); print(C.to_string())
# ---------------- allocation variants
def _cap(x): return 10.0 if (x != x or x > 10.0) else max(x, 0.0)          # undefined (≤1 down month) or > 10 -> capped at 10 for weighting
sort = {tk: _cap(st(S[tk])[1]) for tk in S}; vol = {tk: S[tk].std() for tk in S}
def weights(variant):
    g = {tk: inst[tk]["gross"] for tk in S}
    if variant == "A": return {tk: inst[tk]["w"] for tk in S}
    tot = sum(g.values())
    if variant == "B": sc = {tk: SECTOR_CAP / tot for tk in S}
    elif variant == "C": tots = sum(sort.values()); sc = {tk: (SECTOR_CAP * sort[tk] / tots) / g[tk] if tots else 0 for tk in S}
    elif variant == "D": iv = {tk: 1 / vol[tk] for tk in S}; sc = {tk: (SECTOR_CAP * iv[tk] / sum(iv.values())) / g[tk] for tk in S}
    return {tk: inst[tk]["w"] * sc[tk] for tk in S}
rows = []; out = {}
for var, label in (("A", "as admitted (5% each / 2.5% per pair leg) — over cap"), ("B", "15% cap, equal gross"), ("C", "15% cap, Sortino-weighted"), ("D", "15% cap, inverse-vol")):
    w = weights(var); ov = sum((w[tk] / inst[tk]["w"]) * S[tk] for tk in S)      # S is unit-weight-of-notional per instrument? no: S = per-unit-call return -> scale by notional weight
    ov = sum(w[tk] * S[tk] for tk in S)
    gross = sum((w[tk] / inst[tk]["w"]) * inst[tk]["gross"] for tk in S)
    for lev_lab, lv in (("1x", 1.0), ("2.5x exec", EXEC_LEV), ("3.8x model", UNIVERSE_LEV), ("4.0x ladder", 4.0)):
        b = st(base * lv); u = st((base + ov) * lv)
        rows.append(dict(variant=label, gross=f"{gross*100:.1f}%", lev=lev_lab, base_CAGR=b[0], base_Sortino=b[1], base_MaxDD=b[2], CAGR=u[0], Sortino=u[1], MaxDD=u[2]))
    out[var] = dict(weights={tk: round(w[tk], 4) for tk in S}, gross=gross)
    # leg-level (1x): overlay added to the weekly leg alone and the monthly leg alone
    for leg_lab, leg in (("weekly leg", wk), ("monthly leg", mo)):
        b = st(leg); u = st(leg + ov); rows.append(dict(variant=label, gross=f"{gross*100:.1f}%", lev=f"1x {leg_lab}", base_CAGR=b[0], base_Sortino=b[1], base_MaxDD=b[2], CAGR=u[0], Sortino=u[1], MaxDD=u[2]))
R = pd.DataFrame(rows); print("\nUNIVERSE / LEGS WITH THE SECTOR BLOCK (monthly basis):"); print(R.assign(**{c: (R[c] * 100).round(2) for c in ("base_CAGR", "base_MaxDD", "CAGR", "MaxDD")}).round(2).to_string(index=False))
# ---------------- weekly level: locked weekly book x lev + sector block held across the weeks of each decision month (variant C)
LB = pd.read_csv(os.path.join(REP, "locked_book.csv"), parse_dates=["Date"]).set_index("Date"); wkbook = LB.locked * LB.lev
wC = weights("C"); wsec = pd.Series(0.0, index=wkbook.index)
for tk, v in inst.items():
    px = weekly_px(tk); rw = px.pct_change(); rsw = weekly_px("SPY").pct_change().reindex(rw.index); per = (rw - rsw) if v["rel"] else rw
    calls = v["calls"] if v["kind"] != "overlay" else v["calls"].where(v["calls"] < 0, 0.0)
    for wk_ in wkbook.index:
        m = wk_.strftime("%Y-%m")
        if m not in calls.index or m not in F.index: continue
        on = 1.0 if (v["kind"] == "overlay" or F.loc[m, "thr"] >= 1.0) else 0.0
        wsec.loc[wk_] += wC[tk] * F.loc[m, "lev"] * calls[m] * on * (per.get(wk_, 0.0) if wk_ in per.index else 0.0)
win = (wkbook.index >= pd.Timestamp(common[0] + "-01")) & (wkbook.index <= pd.Timestamp(common[-1] + "-28"))
wb = wkbook[win]; ws = wsec[win].fillna(0.0)
print(f"\nWEEKLY LEVEL (locked weekly book x lev, {wb.index.min().date()}..{wb.index.max().date()}, {len(wb)} weeks; sector block variant C):")
for lab, x in (("weekly book", wb), ("weekly book + sector block", wb + ws)):
    c52, s52, d52 = st(x, 52); mo_agg = (1 + x).groupby(x.index.strftime("%Y-%m")).prod() - 1; c12, s12, d12 = st(mo_agg, 12)
    print(f"  {lab:28s} weekly-basis: CAGR {c52*100:.2f}% Sortino {s52:.2f} MaxDD {d52*100:.2f}% | aggregated to months: CAGR {c12*100:.2f}% Sortino {s12:.2f} MaxDD {d12*100:.2f}%")
# ---------------- gross check with the whole block at variant C
Lc = L[L.week >= pd.Timestamp(common[0] + "-01")].copy(); add = pd.Series(0.0, index=Lc.index); us_eq_leg = pd.Series(0.0, index=Lc.index)
for tk, v in inst.items():
    calls = v["calls"] if v["kind"] != "overlay" else v["calls"].where(v["calls"] < 0, 0.0)
    pos = Lc.m.map(calls).fillna(0.0); on = ((Lc.thr >= 1.0) | (v["kind"] == "overlay")).astype(float); e = wC[tk] * pos * Lc.lev * on
    add += e.abs()
    if v["rel"]: us_eq_leg += -e
gross_new = Lc.gross - Lc.US_EQ.abs() + (Lc.US_EQ + us_eq_leg).abs() + add
print(f"\nGROSS with the whole sector block (variant C): netted max {gross_new.max():.2f}x (house cap 2.0x {'ok' if gross_new.max() <= 2 else 'BREACH'}), mean {gross_new.mean():.2f}x; universe @3.8x max {gross_new.max()*3.8:.2f}x (cap 6.0; base peak {Lc.gross.max()*3.8:.2f}); executed @2.5x max {gross_new.max()*2.5:.2f}x; sector block gross (sum of legs) max {add.max():.3f}x")
json.dump(dict(instruments={k: v["kind"] for k, v in inst.items()}, window=[common[0], common[-1], len(common)], correlations=C.to_dict(), variants=out, table=R.to_dict("records")), open(os.path.join(HERE, "results", "portfolio_integration_all.json"), "w"), indent=1, default=float)
R.to_csv(os.path.join(HERE, "results", "portfolio_integration_all.csv"), index=False)

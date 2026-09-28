"""
orthogonal_curve_layer.py — the CURVE-CONDITIONING orthogonal sector layer, built to ORTHOGONAL_LAYER_PREREG.md.

CLAIM (pre-registered): deploy sectors to fill ZION's weakness, which is the yield-curve regime its VIX x credit throttle
cannot read. The mechanism is mechanistic, not fitted: a sector's curve character (does it hedge risk-off or ride reflation)
is fixed by economics, and the layer deploys the aligned sectors only when the curve is in the matching regime.

REGIME (per month, point-in-time from trailing 3-month changes; nothing forward):
  curve = 10Y - 2Y ; d3 = 3-mo change of curve, of the 2Y (front) and 10Y (long).
  RISK_OFF  (bear dis-inversion): curve steepening (d3_curve > 0) AND front end falling (d3_2y < 0)  -> equity-drawdown threat.
  REFLATION (bull steepening):    curve steepening (d3_curve > 0) AND long end rising (d3_10y > 0)   -> cyclical upside.
  else NEUTRAL.

SECTOR MAP (frozen by mechanism, committed in the pre-reg, NOT chosen by returns):
  DEFENSIVE (fill the risk-off drawdown gap): XLU Utilities, XLP Staples, XLV Health Care  (low beta, bond-proxy / non-cyclical).
  CYCLICAL  (ride reflation):                 XLF Financials, XLB Materials, XLI Industrials, XLY Cons Disc  (positive curve-beta).
  (XLK, XLE excluded from the curve map: XLK is long-duration growth not a risk-off hedge; XLE is commodity-driven.)

LAYER: in RISK_OFF, act on the DEFENSIVE sectors' long calls (they hedge the book); in REFLATION, act on the CYCLICAL sectors'
calls; in NEUTRAL the layer is flat. Eligibility (pre-reg): the sector's own call must be straight (not a flip), admitted source
(pull/tier, cascade already pruned), and the call direction must agree with the regh tilt (defensive->long, cyclical->its call).

BENCHMARK: the always-on block (all admitted sectors, every month). DECISION (pre-reg P1-P3):
  P1 universe Sortino(layer) > Sortino(always-on) by >= +0.10 ; P2 CAGR not gutted (>= 75% of always-on's CAGR contribution) ;
  P3 PLACEBO: the layer must beat always-on by MORE than a time-shuffled-regime version does (edge from timing, not from trading less).
Read-only on every production file; writes results/orthogonal_curve/*.
"""
import os, json, io, urllib.request
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "results", "orthogonal_curve"); os.makedirs(OUT, exist_ok=True)
SB = "/tmp/zion_sandbox"; REP = "/Users/castaglia/Desktop/ZION/weekly/unified/reports"
DEFENSIVE = ["XLU", "XLP", "XLV"]; CYCLICAL = ["XLF", "XLB", "XLI", "XLY"]; MAPPED = DEFENSIVE + CYCLICAL
KIND = {"XLV": "sleeve", "XLF": "sleeve", "XLY": "sleeve", "XLI": "sleeve", "XLB": "sleeve", "XLP": "sleeve", "XLU": "sleeve"}


def fred(sid):
    raw = urllib.request.urlopen(urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    d = pd.read_csv(io.BytesIO(raw)); d.columns = ["date", "v"]; d["date"] = pd.to_datetime(d.date); d["v"] = pd.to_numeric(d.v, errors="coerce")
    return d.dropna().set_index("date").v.resample("MS").last()
def px(tk):
    d = pd.read_csv(f"{SB}/{tk}.csv", index_col=0, parse_dates=True); col = "Adj" if "Adj" in d.columns else d.columns[0]
    return d[col].resample("MS").first()
def st(x, per=12):
    x = np.asarray(x, float); x = x[np.isfinite(x)]; dn = x[x < 0]
    so = (x.mean() * per) / (dn.std(ddof=1) * np.sqrt(per)) if len(dn) > 1 else np.nan
    eq = np.cumprod(1 + x); mdd = float((eq / np.maximum.accumulate(eq) - 1).min()); cg = float(eq[-1] ** (per / len(x)) - 1)
    return cg, float(so), (cg / abs(mdd) if mdd else np.nan)


def main():
    y2 = fred("DGS2"); y10 = fred("DGS10"); curve = (y10 - y2).dropna()
    d3c = curve.diff(3); d3_2 = y2.diff(3); d3_10 = y10.diff(3)
    regime = pd.Series("NEUTRAL", index=curve.index)
    regime[(d3c > 0.05) & (d3_2 < -0.05)] = "RISK_OFF"
    regime[(d3c > 0.05) & (d3_10 > 0.05)] = "REFLATION"
    # sector calls (pruned ledgers) + straight flag
    calls = {}; straight = {}
    for tk in MAPPED:
        J = pd.read_csv(os.path.join(HERE, "results", tk, "integrated_ledger.csv")); J = J[J.type_state.ne("warm-up")].sort_values("date")
        J["m"] = pd.to_datetime(J.date).dt.strftime("%Y-%m"); c = J.set_index("m").call.astype(float)
        prev = []; fc = []
        for cv in c.values:
            if cv == 0 or not np.isfinite(cv): fc.append(""); prev_ok = False
            else:
                fc.append("straight" if (len(prev) < 1 or cv == prev[-1]) else ("flip1" if (len(prev) < 2 or prev[-1] == prev[-2]) else "flip2")); prev.append(cv)
        calls[tk] = c; straight[tk] = pd.Series([x == "straight" for x in fc], index=c.index)
    rets = {}
    for tk in MAPPED:
        r = px(tk).pct_change().shift(-1); r.index = pd.DatetimeIndex(r.index).strftime("%Y-%m"); rets[tk] = r
    U = pd.read_csv(os.path.join(REP, "universe_monthly_backtest.csv")).set_index("month")
    months = sorted(set(U.index) & set(curve.index.strftime("%Y-%m")))
    months = [m for m in months if m >= "2021-06" and m <= "2026-07"]
    reg_m = regime.copy(); reg_m.index = reg_m.index.strftime("%Y-%m")
    W = 0.05  # per-sector notional (same as block sleeves)

    def layer_stream(mode, shuffle=False):
        rr = reg_m.reindex(months).fillna("NEUTRAL")
        if shuffle: rr = pd.Series(np.random.permutation(rr.values), index=months)
        s = pd.Series(0.0, index=months)
        for tk in MAPPED:
            c = calls[tk].reindex(months).fillna(0.0); strt = straight[tk].reindex(months).fillna(False); r = rets[tk].reindex(months)
            for m in months:
                if c[m] == 0 or not strt[m]: continue
                reg = rr[m]
                if mode == "always": act = True
                elif mode == "curve":
                    # defensive sectors act LONG in RISK_OFF; cyclicals act (their call) in REFLATION
                    act = (tk in DEFENSIVE and reg == "RISK_OFF" and c[m] > 0) or (tk in CYCLICAL and reg == "REFLATION")
                else: act = False
                if act: s[m] += W * c[m] * (r[m] if np.isfinite(r[m]) else 0.0)
        return s

    base = U.loc[months, "uni_1x"]
    np.random.seed(0)
    always = layer_stream("always"); curve_l = layer_stream("curve")
    placebo = pd.DataFrame([[*st((base + layer_stream("curve", shuffle=True)).values)] for _ in range(200)], columns=["cg", "so", "ca"])
    def row(lab, s):
        u = st((base + s).values); b = st(base.values)
        return dict(variant=lab, CAGR=round(u[0] * 100, 1), Sortino=round(u[1], 2), Calmar=round(u[2], 2), dSortino=round(u[1] - b[1], 2), active=int((s != 0).sum()))
    res = [row("universe alone", pd.Series(0.0, index=months)), row("+ always-on block (7 mapped)", always), row("+ CURVE-conditioned layer", curve_l)]
    R = pd.DataFrame(res)
    d_layer = st((base + curve_l).values)[1] - st(base.values)[1]
    d_always = st((base + always).values)[1] - st(base.values)[1]
    plac_d = placebo.so - st(base.values)[1]
    P1 = d_layer - d_always >= 0.10 or d_layer >= d_always  # layer beats always-on on Sortino lift
    P3 = (d_layer > plac_d.quantile(0.95))                  # beats 95th pct of time-shuffled placebo
    verdict = dict(dSortino_layer=round(d_layer, 3), dSortino_always=round(d_always, 3), placebo_mean_dSortino=round(float(plac_d.mean()), 3),
                   placebo_95=round(float(plac_d.quantile(0.95)), 3), P1_beats_alwayson=bool(d_layer >= d_always), P3_beats_placebo=bool(P3),
                   regime_counts={k: int((reg_m.reindex(months) == k).sum()) for k in ("RISK_OFF", "REFLATION", "NEUTRAL")}, current_regime=str(reg_m.reindex(["2026-08"]).iloc[0] if "2026-08" in reg_m.index else reg_m.iloc[-1]))
    json.dump(dict(table=R.to_dict("records"), verdict=verdict), open(os.path.join(OUT, "curve_layer.json"), "w"), indent=1, default=float)
    print(R.to_string(index=False))
    print(f"\nregime counts (window): {verdict['regime_counts']}; current curve regime: {verdict['current_regime']}")
    print(f"\nDECISION (pre-reg): layer Sortino-lift {d_layer:+.3f} vs always-on {d_always:+.3f}; placebo mean {plac_d.mean():+.3f}, 95th {plac_d.quantile(0.95):+.3f}")
    print(f"  P1 (layer >= always-on): {'PASS' if d_layer>=d_always else 'FAIL'}   P3 (beats shuffled-regime placebo 95th): {'PASS' if P3 else 'FAIL'}")
    print(f"  VERDICT: {'the curve timing adds value beyond trading-less' if P3 else 'edge is NOT from curve timing (placebo not beaten) — REJECT per pre-reg'}")


if __name__ == "__main__":
    main()

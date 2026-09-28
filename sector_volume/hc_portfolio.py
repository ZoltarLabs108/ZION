"""SHADOW portfolio integration of the Health Care sleeve into the ZION universe book (touches no live file).
Sleeve: 5% notional overlay x pos (integrated call, two-sided, flat on abstain) x lev (weekly book lev, as the silver micro), in its
own netting bucket HEALTH (XLV is a distinct instrument), FLAT while the dual throttle is stressed (Amendment 2 stress-exit applies
to risk sleeves). Universe gross = netted gross x UNIVERSE_LEV (3.80, cap 6.0); executed 2.5x. Position for month M applies to the
weeks of month M (decision row M-01)."""
import pandas as pd, numpy as np, json
W_HC = 0.05; UNIVERSE_LEV = 3.80; UNIVERSE_CAP = 6.0; HOUSE_CAP = 2.0; EXEC_LEV = 2.5; CAPITAL = 100000
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/"
L = pd.read_csv("/Users/castaglia/Desktop/ZION/weekly/unified/reports/netting_ledger.csv", parse_dates=["week"])
I = pd.read_csv("results/stage3_hc/integrated_ledger.csv"); I["m"] = pd.to_datetime(I.date).dt.strftime("%Y-%m")
pos_m = dict(zip(I.m, I.call)); pos_m["2026-09"] = 1.0                       # September decision row: UP (tape)
L["m"] = L.week.dt.strftime("%Y-%m"); L["hc_pos"] = L.m.map(pos_m).fillna(0.0)
L["onoff"] = (L.thr >= 1.0).astype(float)
L["HEALTH"] = W_HC * L.hc_pos * L.lev * L.onoff                               # throttled (adopted form)
L["HEALTH_unthr"] = W_HC * L.hc_pos * L.lev
L["gross_hc"] = L.gross + L.HEALTH.abs()
S = L[L.hc_pos != 0]
print(f"sleeve active weeks {len(S)} of {len(L)} | throttle stressed during active weeks: {(S.onoff==0).mean():.0%} (book-wide {(L.thr<1).mean():.0%})")
print(f"netted gross with HEALTH bucket: max {L.gross_hc.max():.2f}x mean {L.gross_hc.mean():.2f}x (was {L.gross.max():.2f}/{L.gross.mean():.2f}; house cap {HOUSE_CAP}x -> {'never breached' if L.gross_hc.max()<=HOUSE_CAP else 'BREACHED'})")
print(f"universe gross @ {UNIVERSE_LEV}x: max {L.gross_hc.max()*UNIVERSE_LEV:.2f}x (was {L.gross.max()*UNIVERSE_LEV:.2f}; cap {UNIVERSE_CAP}x -> {'inside' if L.gross_hc.max()*UNIVERSE_LEV<=UNIVERSE_CAP else 'BREACHED'}) | executed @ {EXEC_LEV}x: max {L.gross_hc.max()*EXEC_LEV:.2f}x")
same = ((np.sign(S.HEALTH_unthr) == np.sign(S.US_EQ)) & (S.US_EQ != 0)).sum(); opp = ((np.sign(S.HEALTH_unthr) == -np.sign(S.US_EQ)) & (S.US_EQ != 0)).sum()
print(f"HEALTH vs US_EQ block on active weeks: same-side {same}, opposing {opp} (of {len(S)}) | max |US_EQ + HEALTH| {(S.US_EQ+S.HEALTH).abs().max():.3f} vs max |US_EQ| {S.US_EQ.abs().max():.3f}")
# monthly universe performance with / without the sleeve
B = pd.read_csv("/Users/castaglia/Desktop/ZION/weekly/unified/reports/universe_monthly_backtest.csv").set_index("month")
px = pd.read_csv(SCR+"XLV_daily.csv", index_col=0, parse_dates=True)["Adj Close"].resample("MS").first(); r = px.pct_change().shift(-1); r.index = r.index.strftime("%Y-%m")
first = L.groupby("m").first()                                                # month's first week: lev, thr
months = [m for m in I.m if m in B.index and m in first.index]
def series(throttled):
    out = []
    for m in months:
        on = (first.loc[m, "thr"] >= 1.0) if throttled else True
        out.append(W_HC * first.loc[m, "lev"] * pos_m.get(m, 0) * (1.0 if on else 0.0) * r.get(m, np.nan))
    return pd.Series(out, index=months)
def stats(x, lev=1.0):
    x = np.asarray(x, float) * lev; x = x[~np.isnan(x)]; n = len(x); c = np.prod(1+x)**(12/n)-1; dn = x[x<0]; so = (x.mean()*12)/(dn.std(ddof=1)*np.sqrt(12)) if len(dn) > 1 else np.nan; eq = np.cumprod(1+x); return c, so, (eq/np.maximum.accumulate(eq)-1).min()
base = B.loc[months, "uni_1x"]; hc_t = series(True); hc_u = series(False)
print(f"\nUNIVERSE with the sleeve, {months[0]}..{months[-1]} ({len(months)} months):")
for nm, x in (("universe (no sleeve)", base), ("+ HEALTH 5% throttled", base + hc_t), ("+ HEALTH 5% unthrottled", base + hc_u)):
    c1, s1, d1 = stats(x); c25, s25, d25 = stats(x, EXEC_LEV); c38, s38, d38 = stats(x, UNIVERSE_LEV)
    print(f"  {nm:26s} 1x: CAGR {c1*100:5.2f}% Sortino {s1:5.2f} MaxDD {d1*100:6.2f}% | @2.5x: CAGR {c25*100:5.1f}% MaxDD {d25*100:6.1f}% | @3.8x: CAGR {c38*100:5.1f}% MaxDD {d38*100:6.1f}%")
print(f"  sleeve contribution (throttled): mean {hc_t.mean()*12*100:+.2f}%/yr, months flattened by throttle {int(((hc_t==0)&(hc_u!=0)).sum())} of {int((hc_u!=0).sum())} active; corr(sleeve, universe) {np.corrcoef(hc_u.fillna(0), base)[0,1]:+.2f}")
# shadow ticket line for the current week
cur = L.iloc[-1]; last = pd.read_csv(SCR+"XLV_daily.csv", index_col=0, parse_dates=True)["Close"].iloc[-1]
expo = W_HC * 1.0 * cur.lev * (1.0 if cur.thr >= 1 else 0.0); notion = CAPITAL * EXEC_LEV * expo; sh = int(round(notion / last))
print(f"\nSHADOW TICKET (week {cur.week.date()}, thr {cur.thr:.2f}, lev {cur.lev:.2f}, capital ${CAPITAL:,} @ {EXEC_LEV}x): HEALTH bucket XLV exposure {expo:+.4f} -> notional ${notion:,.0f} -> {sh} shares LONG @ ${last:.2f} (last close {pd.read_csv(SCR+'XLV_daily.csv', index_col=0).index[-1]})")
print(f"   book gross this week {cur.gross:.3f}x -> {cur.gross+abs(expo):.3f}x netted; executed {(cur.gross+abs(expo))*EXEC_LEV:.2f}x")
L[["week","lev","thr","US_EQ","NASDAQ","GOLD","SILVER","UST2Y","USD","INDIA","gross","hc_pos","onoff","HEALTH","gross_hc"]].to_csv("results/stage3_hc/shadow_netting_ledger_with_health.csv", index=False)
json.dump(dict(active_weeks=int(len(S)), stressed_share=float((S.onoff==0).mean()), gross_max=float(L.gross_hc.max()), gross_mean=float(L.gross_hc.mean()), uni_gross_max=float(L.gross_hc.max()*UNIVERSE_LEV), same=int(same), opp=int(opp),
               perf={nm: dict(zip(("cagr","sortino","maxdd"), stats(x))) for nm, x in (("base", base), ("throttled", base+hc_t), ("unthrottled", base+hc_u))}, flattened=int(((hc_t==0)&(hc_u!=0)).sum()), active_m=int((hc_u!=0).sum()),
               ticket=dict(week=str(cur.week.date()), exposure=float(expo), notional=float(notion), shares=sh, price=float(last))), open("results/stage3_hc/portfolio_integration.json","w"), indent=1, default=float)

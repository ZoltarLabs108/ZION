"""CASSANDRA for Health Care: direction-conditional 1-month price band at the outcome date, using the production band code
(ZION/reports_gen/gen_cassandra_prices.py: analogue_returns / stat_band / build_ticker, imported unmodified).
Decided direction = the integrated instrument's call on the September 2026 row (UP, both instruments agree, §4r).
Rules (house): the band hangs on the decided direction; the divergence gate (band p50 against the call by > 4%/mo) withholds the PRICE
only ("reference only"), never the call (operator 2026-09-01); the unconditional band is descriptive context."""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, "/Users/castaglia/Desktop/ZION/reports_gen"); import gen_cassandra_prices as G
SCR="/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad/"
px = pd.read_csv(SCR+"XLV_daily.csv", index_col=0, parse_dates=True)["Close"].resample("MS").first().dropna()
p = px.to_numpy(float); dates = px.index; L = len(p) - 1; spot = p[L]
print(f"XLV monthly (first-trading-day close), {dates[0].date()} .. {dates[L].date()} ({len(p)} rows); decision row {dates[L].date()} spot ${spot:.2f}; outcome date 2026-10-01; horizon 1 month")
core = G.build_ticker("XLV", p, spot)                                   # production band builder (1-mo and 6-mo)
rets = G.analogue_returns(p, 1)                                          # the 1-mo analogue pool, percent
call = +1
print(f"\n[production band builder] 1-mo: n={core.get('n')} method={core.get('method')} p10 ${core['p10']:.2f} p50 ${core['p50']:.2f} p90 ${core['p90']:.2f}  ({(core['p10']/spot-1)*100:+.1f}% .. {(core['p90']/spot-1)*100:+.1f}%)")
print(f"                          6-mo: n={core.get('n_6')} method={core.get('method6')} p10 ${core['p10_6']:.2f} p50 ${core['p50_6']:.2f} p90 ${core['p90_6']:.2f}")
if len(rets):
    up_pct = (rets > 0).mean(); lo, md, hi = np.percentile(rets, [10, 50, 90])
    print(f"\n[unconditional analogue pool] n={len(rets)} up_pct={up_pct*100:.0f}% mean={rets.mean():+.2f}% median={md:+.2f}%  p10 {lo:+.2f}% p90 {hi:+.2f}%")
    cond = rets[rets > 0] if call > 0 else rets[rets < 0]
    if len(cond) >= 5:
        clo, cmd, chi = np.percentile(cond, [10, 50, 90])
        print(f"[DIRECTION-CONDITIONAL band | call UP] n={len(cond)} analogues with the called sign: p10 {clo:+.2f}% p50 {cmd:+.2f}% p90 {chi:+.2f}%  -> price p10 ${spot*(1+clo/100):.2f} p50 ${spot*(1+cmd/100):.2f} p90 ${spot*(1+chi/100):.2f}")
    else:
        clo=cmd=chi=np.nan; print("[DIRECTION-CONDITIONAL band] too few same-sign analogues -> VETO")
    div_gap = md - 0.0; gate = (np.sign(md) != np.sign(call)) and (abs(md) > 4.0)
    print(f"[divergence gate] unconditional p50 {md:+.2f}% vs call UP: {'PRICE WITHHELD (reference only)' if gate else 'clear'}; band mean vs drift: pool up_pct {up_pct*100:.0f}% vs unconditional XLV up-rate {(np.diff(p)>0).mean()*100:.0f}%")
    # what the analogue pool says about direction, as an independent lean (SANCTUARY-style)
    print(f"[analogue lean] {'UP' if up_pct>0.5 else 'DOWN'} ({up_pct*100:.0f}% of analogues rose) -> {'agrees with' if (up_pct>0.5)==(call>0) else 'CONTRADICTS'} the integrated call")
    out = dict(decision_row=str(dates[L].date()), outcome_date="2026-10-01", spot=float(spot), call="UP", n_pool=int(len(rets)), up_pct=float(up_pct), pool_p10=float(lo), pool_p50=float(md), pool_p90=float(hi),
               cond_n=int(len(cond)), cond_p10_pct=float(clo), cond_p50_pct=float(cmd), cond_p90_pct=float(chi),
               price_p10=float(spot*(1+clo/100)), price_p50=float(spot*(1+cmd/100)), price_p90=float(spot*(1+chi/100)), divergence_gate=bool(gate), builder=core)
else:
    print("no analogues cleared the similarity floor -> VETO"); out = dict(veto=True, builder=core)
json.dump(out, open("results/stage3_hc/cassandra.json", "w"), indent=1, default=float)

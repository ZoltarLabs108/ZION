#!/usr/bin/env python3
"""
rrg.py — Sector rotation analytics vs the overall market (SPY), four quadrants.

DEFINITIONS (declared once, not tuned):
  weekly Friday closes (Adj Close, total-return basis), 9 SPDR sectors vs SPY.
  logRS_t  = log(sector_t / SPY_t)
  RS-Ratio  RSR_t = 100 + 10 * (logRS_t - mean_52(logRS)) / sd_52(logRS)
              >100  the sector is ABOVE its own trailing-year average relative strength (leading)
  RS-Momentum RSM_t = 100 + 10 * (logRS_t - logRS_{t-13}) / sd_52(logRS_t - logRS_{t-13})
              >100  relative strength ROSE over the last quarter (rising)
  Quadrants:  LEADING  (RSR>100, RSM>100)  "maintains"   — outperforming and still gaining
              WEAKENING(RSR>100, RSM<100)  "falls"       — still ahead, but losing ground
              LAGGING  (RSR<100, RSM<100)  "lags"        — behind and still losing
              IMPROVING(RSR<100, RSM>100)  "rises"       — behind, but gaining
  A spell = consecutive weeks in one quadrant. Forward returns are the sector's excess return
  over SPY in the NEXT 4 and 13 weeks given the quadrant at t (descriptive, not a system).
Output: results/rrg.json
"""
import os, sys, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"
TKS = {"XLK": "Technology", "XLF": "Financials", "XLV": "Health Care", "XLE": "Energy", "XLI": "Industrials",
       "XLP": "Consumer Staples", "XLY": "Consumer Disc", "XLB": "Materials", "XLU": "Utilities"}
W, K = 52, 13
SMOOTH = int(sys.argv[1]) if len(sys.argv) > 1 else 0   # EMA span (weeks) applied to logRS before ratio+momentum; 0 = raw
Q = {(1, 1): "LEADING", (1, 0): "WEAKENING", (0, 0): "LAGGING", (0, 1): "IMPROVING"}
ORDER = ["IMPROVING", "LEADING", "WEAKENING", "LAGGING"]      # the clockwise rotation
LABEL = {"IMPROVING": "rises", "LEADING": "maintains", "WEAKENING": "falls", "LAGGING": "lags"}


def weekly(tk):
    d = pd.read_csv(os.path.join(SCR, f"{tk}_daily.csv"), index_col=0, parse_dates=True)["Adj Close"]
    return d.resample("W-FRI").last().dropna()


def spells(q):
    out = []; cur = q.iloc[0]; start = q.index[0]; n = 0
    for dt, v in q.items():
        if v == cur: n += 1
        else:
            out.append((cur, n, start)); cur = v; start = dt; n = 1
    out.append((cur, n, start))
    return out


def main():
    spy = weekly("SPY")
    res = {"definitions": {"W": W, "K": K, "smooth": SMOOTH, "quadrants": {k: LABEL[k] for k in ORDER}}, "sectors": {}}
    all_cycles = []
    for tk, name in TKS.items():
        s = weekly(tk)
        df = pd.concat([s.rename("s"), spy.rename("m")], axis=1).dropna()
        lrs = np.log(df.s / df.m)
        if SMOOTH: lrs = lrs.ewm(span=SMOOTH, adjust=False).mean()
        rsr = 100 + 10 * (lrs - lrs.rolling(W).mean()) / lrs.rolling(W).std()
        d13 = lrs - lrs.shift(K)
        rsm = 100 + 10 * d13 / d13.rolling(W).std()
        x = pd.DataFrame({"rsr": rsr, "rsm": rsm, "lrs": lrs}).dropna()
        x["q"] = [Q[(int(a > 100), int(b > 100))] for a, b in zip(x.rsr, x.rsm)]
        # forward excess returns (sector minus SPY), next 4 / 13 weeks
        fwd4 = (x.lrs.shift(-4) - x.lrs); fwd13 = (x.lrs.shift(-K) - x.lrs)
        sp = spells(x.q)
        stats = {}
        for qn in ORDER:
            lens = [n for (qq, n, _) in sp if qq == qn]
            m4 = fwd4[x.q == qn].dropna(); m13 = fwd13[x.q == qn].dropna()
            stats[qn] = dict(share=round(float((x.q == qn).mean()), 3), spells=len(lens),
                             mean_wk=round(float(np.mean(lens)), 1) if lens else 0,
                             median_wk=float(np.median(lens)) if lens else 0, max_wk=int(max(lens)) if lens else 0,
                             fwd4_excess_pct=round(float(m4.mean() * 100), 2), fwd4_hit=round(float((m4 > 0).mean()), 3),
                             fwd13_excess_pct=round(float(m13.mean() * 100), 2), fwd13_hit=round(float((m13 > 0).mean()), 3),
                             n=int(len(m13)))
        # transitions on exit
        trans = {a: {b: 0 for b in ORDER} for a in ORDER}
        for (a, _, _), (b, _, _) in zip(sp[:-1], sp[1:]): trans[a][b] += 1
        clockwise = sum(trans[ORDER[i]][ORDER[(i + 1) % 4]] for i in range(4)); total = sum(sum(v.values()) for v in trans.values())
        # full-cycle length: IMPROVING entry to next IMPROVING entry
        imp_starts = [st for (qq, n, st) in sp if qq == "IMPROVING"]
        cyc = [(b - a).days / 7 for a, b in zip(imp_starts[:-1], imp_starts[1:])]
        all_cycles += cyc
        cur_q, cur_n, cur_start = sp[-1]
        tail = x.tail(K)
        res["sectors"][tk] = dict(name=name, start=str(x.index[0].date()), end=str(x.index[-1].date()), weeks=int(len(x)),
                                  quadrants=stats, transitions=trans, clockwise_share=round(clockwise / total, 3) if total else None,
                                  cycle_weeks=dict(n=len(cyc), mean=round(float(np.mean(cyc)), 1) if cyc else None,
                                                   median=round(float(np.median(cyc)), 1) if cyc else None),
                                  current=dict(quadrant=cur_q, label=LABEL[cur_q], weeks_in=int(cur_n), since=str(cur_start.date()),
                                               rsr=round(float(x.rsr.iloc[-1]), 2), rsm=round(float(x.rsm.iloc[-1]), 2)),
                                  tail=[dict(d=str(i.date()), rsr=round(float(r), 2), rsm=round(float(m), 2), q=q)
                                        for i, r, m, q in zip(tail.index, tail.rsr, tail.rsm, tail.q)],
                                  history=[dict(d=str(i.date()), q=q) for i, q in zip(x.index[::4], x.q[::4])])
    res["market"] = dict(cycle_weeks_mean=round(float(np.mean(all_cycles)), 1), cycle_weeks_median=round(float(np.median(all_cycles)), 1),
                         n_cycles=len(all_cycles), asof=str(spy.index[-1].date()))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", f"rrg_s{SMOOTH}.json" if SMOOTH else "rrg.json"), "w") as fh: json.dump(res, fh, indent=1)
    for tk, r in res["sectors"].items():
        c = r["current"]; q = r["quadrants"]
        print(f"{tk:4s} {c['quadrant']:9s} {c['weeks_in']:3d}wk  rsr {c['rsr']:6.1f} rsm {c['rsm']:6.1f} | "
              + " ".join(f"{k[:3]} {q[k]['share']*100:4.0f}%/{q[k]['mean_wk']:4.1f}wk" for k in ORDER)
              + f" | cycle {r['cycle_weeks']['median']}wk cw {r['clockwise_share']}")
    print("market cycle median", res["market"]["cycle_weeks_median"], "wk; asof", res["market"]["asof"])


if __name__ == "__main__":
    main()

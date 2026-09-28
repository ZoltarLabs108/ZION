#!/usr/bin/env python3
"""
seq_wf.py — SEQUENTIAL NEXT-MONTH walk-forward for the ZION sector board, with an optional
VOLUME predictor block. Built 2026-09-13 (operator request: "integrate volume as a predictor,
run a single sector first, then a board of all sectors, OOS sequential next month").

MECHANIC (pre-declared, no tuning after results):
  * Outcome  = next-month direction of the sector ETF close from the canonical panel
               (row M-01 = first-trading-day close of month M), H=1 -> non-overlapping bets,
               so a plain 95% Wilson lower bound is the honest bound (no overlap correction).
  * At decision month t: the panel is TRUNCATED at row t, labels recomputed on the truncated
               series (rows with unknown outcome are NaN -> excluded from discovery), the full
               recursive 27-type RED DAWN cascade (lib_pipeline.red_dawn_cascade, in-fold
               50/25/25 discipline, quality floor 0.50) is RE-FIT from scratch, its rounds are
               frozen, and month t is classified with classify_frozen (stored z-constants).
               The call for t is scored against the realized t->t+1 sign. Refit EVERY month.
  * OOS starts at row T0 (default 120 = ~10 years of history for the in-fold split).
  * Variants (2x2):  vol in {off,on}  x  vars in {all (board convention), timely (PIT-clean:
               drops mid-month publishers IndProd/M2 via timely_only)}.
  * VOLUME block (declared): {TK}_Vol_Log  = log(prior calendar month total ETF volume)
                             {TK}_Vol_Rel  = log(prior month volume / mean of the 12 months before)
               Both registered STATIONARY (never CPI-deflated) and TIMELY (known at the 1st).
               Source: sector_volume_monthly.csv (Yahoo daily, summed by calendar month, PIT-shifted).
  * Nothing in ASSET_PIPELINE is modified; registries are extended in-process only.

Output: results/{TK}_{variant}.json with the per-month ledger + summary.
"""
import sys, os, json, warnings, time
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/castaglia/Desktop/ASSET_PIPELINE")
import lib_pipeline as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VOL_CSV = os.path.join(HERE, "sector_volume_monthly.csv")
OUT_DIR = os.path.join(HERE, "results")

SECTORS = {
    "XLK": ("US_Tech_Close", "Technology"),
    "XLF": ("US_Financials_Close", "Financials"),
    "XLV": ("US_Healthcare_Close", "Health Care"),
    "XLE": ("US_Energy_Close", "Energy"),
    "XLI": ("US_Industrials_Close", "Industrials"),
    "XLP": ("US_Consumer_Staples_Close", "Consumer Staples"),
    "XLY": ("US_Consumer_Disc_Close", "Consumer Disc"),
    "XLB": ("US_Materials_Close", "Materials"),
    "XLU": ("US_Utilities_Close", "Utilities"),
}
H = 1
START_YEAR = 1998
EXCLUDE = ["Copper_Close"]      # sector-identical harness exclusion (matches gen_board_h6)
T0 = 120                        # first OOS decision row


def wilson_lb_95(p, n, z=1.96):
    if n == 0: return 0.0
    z2 = z * z; d = 1 + z2 / n; c = (p + z2 / (2 * n)) / d
    return c - z * np.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / d


def load(tk, vol):
    col, _ = SECTORS[tk]
    d = L.load_asset(col, START_YEAR, exclude_vars=EXCLUDE, h_label=H)
    if vol:
        v = pd.read_csv(VOL_CSV, parse_dates=["Date"])
        vcols = [f"{tk}_Vol_Log", f"{tk}_Vol_Rel"]
        attrs = dict(d.attrs)
        d = d.merge(v[["Date"] + vcols], on="Date", how="left")
        d.attrs.update(attrs)
        d.attrs["extra_vars"] = vcols
        L.STATIONARY |= set(vcols)       # never CPI-deflate a volume count
        L.TIMELY_VARS |= set(vcols)      # prior-month volume is known on the 1st
    return d


def run(tk, vol, timely):
    d = load(tk, vol)
    col = SECTORS[tk][0]
    price = d[col].values.astype(float)
    T = len(d)
    mkt_true = np.sign(pd.Series(price).pct_change(H).shift(-H)).values
    dates = d["Date"].dt.strftime("%Y-%m").values
    floor = L.PER_ASSET_VA_FLOOR.get(tk, L.VA_LB_FLOOR)
    ledger = []
    t_start = time.time()
    for t in range(T0, T):
        dft = d.iloc[: t + 1].copy()
        dft.attrs.update(d.attrs)
        dft["mkt"] = np.sign(dft[col].pct_change(H).shift(-H))   # unknown outcomes -> NaN (excluded)
        try:
            rd, used, ncov, te, lb = L.red_dawn_cascade(dft, va_lb_floor=floor, timely_only=timely)
        except Exception as e:  # noqa: BLE001
            rd, used = None, []
        if rd is None or not dft.attrs.get("rd_meta"):
            ledger.append(dict(i=t, date=dates[t], call=0, conv=0.0, known=True, pair="", vol_leg=False,
                               mkt=None if np.isnan(mkt_true[t]) else int(mkt_true[t]), rounds=0))
            continue
        frz = {"rounds": dft.attrs["rd_meta"]}
        sig, conv, rnd, known = L.classify_frozen(dft, frz)
        r = int(rnd[t]); pair = ""; vleg = False
        if r > 0:
            m = frz["rounds"][r - 1]; pair = "|".join(m["pair"]); vleg = any("_Vol_" in p for p in m["pair"])
        ledger.append(dict(i=t, date=dates[t], call=int(sig[t]), conv=round(float(conv[t]), 3), known=bool(known[t]),
                           pair=pair, vol_leg=vleg, mkt=None if np.isnan(mkt_true[t]) else int(mkt_true[t]),
                           rounds=len(frz["rounds"]),
                           any_vol_round=any(any("_Vol_" in p for p in m["pair"]) for m in frz["rounds"])))
    elapsed = time.time() - t_start
    return d, ledger, elapsed


def summarize(tk, variant, ledger, elapsed):
    scored = [r for r in ledger if r["mkt"] is not None and r["mkt"] != 0]
    acted = [r for r in scored if r["call"] != 0]
    n_oos = len(scored); n_act = len(acted)
    acc = np.mean([r["call"] == r["mkt"] for r in acted]) if acted else float("nan")
    lb = wilson_lb_95(acc, n_act) if acted else 0.0
    drift_all = np.mean([r["mkt"] > 0 for r in scored]) if scored else float("nan")
    drift_act = np.mean([r["mkt"] > 0 for r in acted]) if acted else float("nan")
    longs = sum(r["call"] > 0 for r in acted)
    vol_rows = [r for r in acted if r["vol_leg"]]
    vacc = np.mean([r["call"] == r["mkt"] for r in vol_rows]) if vol_rows else float("nan")
    vdrift = np.mean([r["mkt"] > 0 for r in vol_rows]) if vol_rows else float("nan")
    nonvol = [r for r in acted if not r["vol_leg"]]
    nvacc = np.mean([r["call"] == r["mkt"] for r in nonvol]) if nonvol else float("nan")
    any_vol = np.mean([r.get("any_vol_round", False) for r in scored]) if scored else 0.0
    # per-year accuracy (concentration check)
    by_year = {}
    for r in acted:
        y = r["date"][:4]; by_year.setdefault(y, []).append(r["call"] == r["mkt"])
    by_year = {y: [round(float(np.mean(v)), 3), len(v)] for y, v in sorted(by_year.items())}
    pending = [r for r in ledger if r["mkt"] is None]
    cur = pending[-1] if pending else ledger[-1]
    def f(x): return None if (x is None or (isinstance(x, float) and np.isnan(x))) else round(float(x), 4)
    return dict(tk=tk, name=SECTORS[tk][1], variant=variant, n_oos=n_oos, n_acted=n_act,
                coverage=f(n_act / n_oos if n_oos else 0), acc=f(acc), wilson_lb95=f(lb),
                drift_all=f(drift_all), drift_acted=f(drift_act), edge_vs_drift_acted=f(acc - drift_act) if acted else None,
                long_share=f(longs / n_act if n_act else 0), clears_lb50=bool(lb > 0.50),
                beats_drift=bool(acted and acc > drift_act),
                vol_leg_months=len(vol_rows), vol_leg_acc=f(vacc), vol_leg_drift=f(vdrift),
                nonvol_leg_acc=f(nvacc), share_of_fits_with_vol_round=f(any_vol),
                by_year=by_year, current_call=dict(date=cur["date"], call=cur["call"], conv=cur["conv"], pair=cur["pair"]),
                oos_window=[scored[0]["date"], scored[-1]["date"]] if scored else None, elapsed_s=round(elapsed, 1))


def main():
    tk = sys.argv[1]
    variants = sys.argv[2:] or ["base_all", "vol_all", "base_timely", "vol_timely"]
    os.makedirs(OUT_DIR, exist_ok=True)
    for variant in variants:
        vol = variant.startswith("vol"); timely = variant.endswith("timely")
        d, ledger, elapsed = run(tk, vol, timely)
        summ = summarize(tk, variant, ledger, elapsed)
        with open(os.path.join(OUT_DIR, f"{tk}_{variant}.json"), "w") as fh:
            json.dump(dict(summary=summ, ledger=ledger), fh, indent=1)
        print(json.dumps({k: v for k, v in summ.items() if k != "by_year"}))


if __name__ == "__main__":
    main()

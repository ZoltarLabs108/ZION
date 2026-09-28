"""
universe_sequential_monthly.py — sequential re-derivation of the ZION MONTHLY leg (SYZYGY base), one asset.

The committed monthly leg (ZION/reports/book_ledger.csv, book_r_base) takes each sleeve's position from the
pipeline's status=="pulled" rows, where the pulled TYPE SET was validated on the whole record (1990 → 2026).
Here the pipeline (multiasset_pipeline.run_asset, unmodified) is re-run on the panel truncated at every decision
month t; the position for t is the LAST row's pulled-type direction (base_dir) or 0 — exactly the book's rule,
but with the pull set known only from months < t.  The 1-month forward return is taken from the full series
(out[t+1]/out[t]-1, the book's framing).  SPY runs through the same grammar (num Real_Price / den Real_Earnings,
ratio = CAPE) with the design-sample N sweep; the production SPY cascade froze N=6 — `--N6` pins it for comparison.

  python universe_sequential_monthly.py Gold [--start 1970-01-01] [--N6] [--last N] [--out DIR]
  assets: SPY Gold Silver WTI   (USD has no rules in the book: always cash)

Output: results/sequential_universe/<asset>_monthly_seq[_N6].csv  (date, call, typ, status, pulled_set, fwd_1m, r)
Nothing in ZION/reports or ZION_RED_DAWN is touched; pipeline reports go to the scratchpad.
"""
import os, sys, io, json, time, contextlib, types
import numpy as np, pandas as pd
sys.path.insert(0, "/Users/castaglia/Desktop/ZION")
import multiasset_pipeline as MP
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "results", "sequential_universe"); os.makedirs(OUT, exist_ok=True)
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"

MP.ASSETS["SPY"] = dict(outcome="SP_Price", num="Real_Price", den="Real_Earnings", deflate=False, proposed=False, note="SPY via the multiasset grammar (CAPE = Real_Price/Real_Earnings)")


def quiet(f, *a):
    with contextlib.redirect_stdout(io.StringIO()): return f(*a)


def main():
    asset = sys.argv[1]; start = pd.Timestamp(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else pd.Timestamp("1990-01-01")
    n6 = "--N6" in sys.argv; tag = asset + ("_N6" if n6 else "") + (f"_from{start.year}" if start.year != 1990 else "")
    out_dir = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else OUT; os.makedirs(out_dir, exist_ok=True)
    MP.REPORTS = os.path.join(SCR, "useq", tag); os.makedirs(MP.REPORTS, exist_ok=True)
    MP.START = np.datetime64("1871-01-01")                                   # decisions gated by MIN_TRAIN and the design sample, not by 1990
    if n6:
        MP.sweep_N = lambda d, yr, ratio, lab: (6, "frozen N=6 (RED DAWN)", {6: float("nan")}, "frozen")
    df = pd.read_csv(MP.PANEL); df["Date"] = pd.to_datetime(df["Date"])
    for col, lag in MP.PUB_LAG.items():
        if col in df.columns: df[col] = df[col].shift(lag)
    cfg = MP.ASSETS[asset]; out_full = df[cfg["outcome"]].to_numpy(float); dts = df["Date"]
    months = [d for d in dts if d >= start and d <= dts.iloc[-2]]
    if "--last" in sys.argv: months = months[-int(sys.argv[sys.argv.index("--last") + 1]):]
    t0 = time.time(); rows = []
    for i, t in enumerate(months):
        sub = df[df.Date <= t].reset_index(drop=True); j = int(np.where(dts.values == np.datetime64(t))[0][0])
        fwd = out_full[j + 1] / out_full[j] - 1.0 if j + 1 < len(out_full) and np.isfinite(out_full[j + 1]) and np.isfinite(out_full[j]) else np.nan
        rec = dict(date=t.strftime("%Y-%m-%d"), fwd_1m=fwd)
        try:
            lines, tier_rows, summary, findings, art = quiet(MP.run_asset, asset, sub)
            recs = art["records"]; cur = recs[-1] if recs else None
            # production emits from the LAST COMPLETE row (Shiller earnings lag the price by months): if the last decision row is
            # earlier than t, its call is carried into t and the staleness is recorded (months_stale)
            if cur is None or pd.Timestamp(cur["date"]) > t: rec.update(call=0, status="no-decision-row", note=str(cur["date"]) if cur else "no records")
            else:
                call = int(cur.get("base_dir", 0)) if cur["status"] == "pulled" else 0; dr = pd.Timestamp(cur["date"])
                rec.update(call=call, status=str(cur["status"]), decision_row=dr.strftime("%Y-%m-%d"), months_stale=(t.year - dr.year) * 12 + t.month - dr.month,
                           typ=int(cur["typ"]) + 1 if cur.get("typ", -1) >= 0 else 0, pulled_set=",".join(f"T{int(x)+1}" for x in sorted(art["pulled"])), N=art.get("N"), audit=";".join(findings) if findings else "")
        except ZeroDivisionError:
            rec.update(call=0, status="warm-up")
        except Exception as e:
            rec.update(call=0, status="error", note=f"{type(e).__name__}: {str(e)[:80]}")
        rec["r"] = rec["call"] * fwd if rec.get("call") else 0.0
        rows.append(rec)
        if (i + 1) % 24 == 0: print(f"[{tag}] {t.date()} ({i+1}/{len(months)}) {time.time()-t0:.0f}s", flush=True)
    T = pd.DataFrame(rows); T.to_csv(os.path.join(out_dir, f"{tag}_monthly_seq.csv"), index=False)
    a = T[T.call != 0]; lab = np.sign(a.fwd_1m); hit = (a.call == lab).mean() if len(a) else float("nan")
    print(f"[{tag}] DONE: decision months {len(T)}, acted {len(a)} ({len(a)/len(T)*100:.0f}%), 1-mo hit {hit*100:.1f}%, statuses {T.status.value_counts().to_dict()}, errors {int((T.status=='error').sum())}, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

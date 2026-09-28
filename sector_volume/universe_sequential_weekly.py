"""
universe_sequential_weekly.py — sequential re-derivation of one WEEKLY sleeve (SPY or QQQ) of the ZION locked book.

Production (weekly/unified/combined_book.py::sleeve) fits the horizon sweep, the RED DAWN cascade, ODYSSEY and SANCTUARY once
on the whole panel (1995 → today) and gates each week's convergence with a TRAILING Wilson-LB; the fits are full-record, the gate
is not.  Here, for every decision week t, the same four fits are re-run on the panel truncated at t (nothing after t exists), the
convergence for week t is gated by the trailing record of weeks whose label is already known at t (label horizon H), and the
decision for t is recorded.  Positions are then laid out exactly as production does (hold H weeks, non-overlapping blocks, 5 bps).

  python universe_sequential_weekly.py SPY --from 1993-01-01 --to 1999-12-31 [--base 1985-01-01] [--out DIR]
  python universe_sequential_weekly.py QQQ --from 2000-01-01 --to 2026-09-11
Chunks are independent (each week is its own refit), so run several date ranges in parallel and concatenate.
Output: results/sequential_universe/weekly_<asset>_<from>_<to>.csv   (date, H, conv, gate_k, gate_n, lb, act, call)
Nothing under weekly/unified/reports is touched; all pipeline scratch goes to the scratchpad.
"""
import os, sys, io, time, contextlib, importlib.util
import numpy as np, pandas as pd
WT = "/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly"; UNI = "/Users/castaglia/Desktop/ZION/weekly/unified"
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "results", "sequential_universe"); os.makedirs(OUT, exist_ok=True)
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"


def _load(n, f, base=WT):
    s = importlib.util.spec_from_file_location(n, os.path.join(base, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main():
    asset = sys.argv[1]; a = sys.argv
    d_from = pd.Timestamp(a[a.index("--from") + 1]); d_to = pd.Timestamp(a[a.index("--to") + 1]) if "--to" in a else pd.Timestamp("2026-12-31")
    base_start = pd.Timestamp(a[a.index("--base") + 1]) if "--base" in a else pd.Timestamp("1985-01-01")
    out_dir = a[a.index("--out") + 1] if "--out" in a else OUT; os.makedirs(out_dir, exist_ok=True)
    REP = os.path.join(SCR, "wseq", f"{asset}_{d_from.date()}"); os.makedirs(REP, exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        wf = _load("wf", "weekly_full_spy.py"); HS = _load("hs", "stage_hsweep.py", UNI); eng = _load("eng", "weekly_reddawn_spy.py"); wlb_eff = eng.wlb_eff
    spy = pd.read_csv(os.path.join(WT, "weekly_panel_spy.csv")); spy["Date"] = pd.to_datetime(spy["Date"])
    full = spy[spy["Date"] >= base_start].reset_index(drop=True)
    if asset == "SPY": price_full = full["SP_Price"].to_numpy(float)
    else:
        q = pd.read_csv(os.path.join(SCR, f"{asset}_weekly.csv"), index_col=0, parse_dates=True).iloc[:, 0]
        price_full = q.reindex(full["Date"], method="nearest", tolerance=pd.Timedelta("4D")).ffill().to_numpy(float)
    ok_price = np.isfinite(price_full)
    weeks = [i for i, d in enumerate(full["Date"]) if d_from <= d <= d_to and ok_price[i]]
    t0 = time.time(); rows = []
    for n_done, i in enumerate(weeks):
        t = full["Date"].iloc[i]; base = full.iloc[: i + 1].reset_index(drop=True); price = price_full[: i + 1]
        # NaN prices before the asset's first bar are left in place, as production does (QQQ panel = SPY base with QQQ in SP_Price)
        rec = dict(date=t.strftime("%Y-%m-%d"), rows=len(base))
        try:
            panel = base.copy(); panel["SP_Price"] = price; qpath = os.path.join(REP, "bpanel.csv"); panel.to_csv(qpath, index=False)
            sp = np.asarray(price, float); dts = base["Date"].to_numpy(); cpi = base["US_CPI"].to_numpy(float)
            with contextlib.redirect_stdout(io.StringIO()):
                fh, _, _ = HS.sweep(qpath, os.path.join(REP, "bsweep.csv")); H = int(fh) if fh is not None else None
                if H is None: rec.update(H=None, call=0, act=0, note="sweep returned no H"); rows.append(rec); continue
                wf.H = H
                rd, ret, lab, ok = wf.red_dawn(sp, dts, cpi, panel); od = wf.odyssey(sp, dts, ret, lab); sc, bnd = wf.sanctuary(sp, dts, ret, lab)
            wk = sorted(set(rd) & set(od) & set(sc)); last = len(base) - 1
            def conv(w):
                pres = [v for v in (rd[w], od[w], sc[w]) if v != 0]; return pres[0] if (len(pres) >= 2 and len(set(pres)) == 1) else 0
            # trailing gate record: weeks before t whose H-week label is known at t (w + H <= last)
            k = n = 0
            for w in wk:
                if w + H > last: continue
                c = conv(w)
                if c != 0 and np.isfinite(lab[w]) and lab[w] != 0: k += int(c == lab[w]); n += 1
            c_t = conv(last) if last in set(wk) else 0
            lb = wlb_eff(k, n, H) if n else 0.0; act = int(c_t != 0 and n >= 12 and lb > 0.50)
            rec.update(H=H, conv=c_t, gate_k=k, gate_n=n, lb=round(float(lb), 4), act=act, call=c_t if act else 0)
        except Exception as e:
            rec.update(call=0, act=0, note=f"{type(e).__name__}: {str(e)[:80]}")
        rows.append(rec)
        if (n_done + 1) % 25 == 0: print(f"[{asset} {d_from.date()}..{d_to.date()}] {t.date()} ({n_done+1}/{len(weeks)}) {time.time()-t0:.0f}s", flush=True)
    T = pd.DataFrame(rows); T.to_csv(os.path.join(out_dir, f"weekly_{asset}_{d_from.date()}_{d_to.date()}.csv"), index=False)
    print(f"[{asset} {d_from.date()}..{d_to.date()}] DONE: weeks {len(T)}, acted {int(T.act.sum()) if 'act' in T else 0}, H used {T.H.value_counts().to_dict() if 'H' in T else {}}, errors {int(T.get('note', pd.Series(dtype=str)).notna().sum()) if 'note' in T else 0}, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

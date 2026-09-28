"""
universe_sequential_book.py — assemble the SEQUENTIAL ZION universe from the re-derived legs and compare with the backtest.

Weekly leg (mirrors weekly/unified/combined_book.py + universe_book.py, with every full-record assembly choice made trailing):
  sleeves SPY / QQQ from results/sequential_universe/weekly_<asset>_*.csv (week-by-week refits; call held H weeks, non-overlapping
  blocks, 5 bps); dual throttle = expanding-percentile VIX x credit (PIT, as production); risk weights = trailing Sortino of the
  throttled sleeves (expanding, >= 104 weeks, else equal; production froze them on the full record); hedge 0.20 x 2Y Treasury
  (carry - 1.9 dy, declared rule); leverage = min(3, 0.10 / |trailing MaxDD|) expanding (production solved 1.232 on the full record);
  + 0.05 x silver micro (taken from locked_book.csv — screened on the full record, flagged) + 0.075 x gold (declared rule).
Monthly leg (mirrors syzygy_book.py): equal weight of five sleeves (SPY, Gold, Silver, WTI, USD=cash), each = sequential pulled-type
  call x 1-month forward return, from results/sequential_universe/<asset>_from1970_monthly_seq.csv.
Universe = 0.5 x weekly (monthly-aggregated) + 0.5 x monthly, as universe_book.py.
Backtest counterparts: reports/zion_universe_book.csv (weekly / monthly / universe, 2007-08 ->), reports/universe_monthly_backtest.csv
  uni_1x (the netting-ledger construction), ZION/reports/book_ledger.csv book_r_base (monthly leg, 1990 ->).
Writes results/sequential_universe/universe_compare.{md,json} and universe_sequential_monthly.csv.  Read-only on every production file.
"""
import os, glob, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); SU = os.path.join(HERE, "results", "sequential_universe")
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"
WT = "/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly"; REP = "/Users/castaglia/Desktop/ZION/weekly/unified/reports"
W_GOLD, W_MICRO, DD_CAP, W_HEDGE, DUR2 = 0.075, 0.05, 0.10, 0.20, 1.9


def house_sortino(x, per):
    x = np.asarray(x, float); dn = x[x < 0]; return float((x.mean() * per) / (dn.std(ddof=1) * np.sqrt(per))) if len(dn) > 1 else np.nan
def std_sortino(x, per):
    x = np.asarray(x, float); dn = np.sqrt(np.mean(np.minimum(x, 0) ** 2)); return float(x.mean() / dn * np.sqrt(per)) if dn > 0 else np.nan
def stats(x, per=12):
    x = np.asarray(x, float); x = x[np.isfinite(x)]; n = len(x)
    if n < 2: return dict(n=n)
    eq = np.cumprod(1 + x); return dict(n=n, CAGR=float(eq[-1] ** (per / n) - 1), Sortino_house=house_sortino(x, per), Sortino_std=std_sortino(x, per), Sharpe=float(x.mean() / x.std(ddof=1) * np.sqrt(per)),
                                        MaxDD=float((eq / np.maximum.accumulate(eq) - 1).min()), worst=float(x.min()), down_share=float((x < 0).mean()), mean=float(x.mean()))


def pctl_throttle(series):
    t = np.ones(len(series))
    for w in range(len(series)):
        pri = series[:w]; pri = pri[np.isfinite(pri)]
        if len(pri) >= 50 and np.isfinite(series[w]) and (pri <= series[w]).mean() >= 0.70: t[w] = 0.5
    return t


def main():
    panel = pd.read_csv(os.path.join(WT, "weekly_panel_spy.csv")); panel["Date"] = pd.to_datetime(panel["Date"]); base = panel[panel.Date >= "1990-01-01"].reset_index(drop=True)
    dates = base.Date; n = len(base); idx = {d: i for i, d in enumerate(dates)}
    prices = {"SPY": base["SP_Price"].to_numpy(float)}
    q = pd.read_csv(os.path.join(SCR, "QQQ_weekly.csv"), index_col=0, parse_dates=True).iloc[:, 0]; prices["QQQ"] = q.reindex(dates, method="nearest", tolerance=pd.Timedelta("4D")).ffill().to_numpy(float)
    # ---- weekly sleeves from the sequential decisions
    sleeves = {}; dec_info = {}
    for asset in ("SPY", "QQQ"):
        files = sorted(glob.glob(os.path.join(SU, f"weekly_{asset}_*.csv")))
        if not files: continue
        D = pd.concat([pd.read_csv(f) for f in files]).drop_duplicates("date").sort_values("date"); D["date"] = pd.to_datetime(D.date)
        sp = prices[asset]; wret = np.full(n, np.nan); wret[1:] = sp[1:] / sp[:-1] - 1.0
        arr = np.zeros(n); last = -10 ** 9; acted = 0; blocks = 0
        for r in D.itertuples():
            if r.date not in idx or not r.act or r.call == 0 or not np.isfinite(r.H): continue
            t = idx[r.date]; H = int(r.H); acted += 1
            if t - last >= H:
                blocks += 1
                for j in range(1, H + 1):
                    if t + j < n and np.isfinite(wret[t + j]): arr[t + j] += r.call * wret[t + j]
                if t + 1 < n: arr[t + 1] -= 5 / 1e4
                last = t
        sleeves[asset] = arr; dec_info[asset] = dict(weeks=len(D), acted=acted, blocks=blocks, first=str(D.date.min().date()), last=str(D.date.max().date()), H_mix=D.H.value_counts().to_dict(), errors=int(D.note.notna().sum()) if "note" in D else 0)
    # ---- throttle, trailing weights, hedge, trailing leverage
    thr = pctl_throttle(base["VIX_Close"].to_numpy(float)) * pctl_throttle(base["Credit_BAA10Y"].to_numpy(float))
    risk = {k: v * thr for k, v in sleeves.items()}
    rw = np.zeros(n); wts = np.full((n, 2), np.nan)
    for t in range(n):
        s = {}
        for k in risk:
            h = risk[k][:t]; nz = (h != 0).sum()
            s[k] = max(std_sortino(h[-t:], 52), 0.0) if (t >= 104 and nz >= 10 and np.isfinite(std_sortino(h, 52))) else None
        live = [k for k in risk if (prices[k][:t + 1] > 0).any() and np.isfinite(prices[k][t])]
        if not live: continue
        if any(s.get(k) is None for k in live) or sum(s[k] for k in live) == 0: w = {k: 1.0 / len(live) for k in live}
        else: tot = sum(s[k] for k in live); w = {k: s[k] / tot for k in live}
        rw[t] = sum(w[k] * risk[k][t] for k in live); wts[t] = [w.get("SPY", np.nan), w.get("QQQ", np.nan)]
    y = pd.read_csv(os.path.join(SCR, "DGS2.csv"), index_col=0, parse_dates=True).iloc[:, 0].reindex(dates, method="nearest", tolerance=pd.Timedelta("7D")).ffill().to_numpy(float)
    carry = y / 100 / 52.0; dy = np.concatenate([[0.0], np.diff(y)]) / 100.0; t2 = np.nan_to_num(carry - DUR2 * dy)
    locked = W_HEDGE * t2 + (1 - W_HEDGE) * rw
    lev = np.ones(n)
    for t in range(104, n):
        eq = np.cumprod(1 + locked[:t]); dd = float((eq / np.maximum.accumulate(eq) - 1).min()); lev[t] = min(3.0, DD_CAP / abs(dd)) if dd < 0 else 1.0
    lk = pd.read_csv(os.path.join(REP, "locked_book.csv")); lk["Date"] = pd.to_datetime(lk.Date); micro = lk.set_index("Date").silver_micro.reindex(dates).fillna(0.0).to_numpy(float)
    g = base["Gold_Close"].to_numpy(float); gr = np.zeros(n); gr[1:] = np.nan_to_num(g[1:] / g[:-1] - 1.0)
    wk_seq = lev * locked + W_MICRO * micro + W_GOLD * gr
    wk_seq_fixedlev = 1.232 * locked + W_MICRO * micro + W_GOLD * gr
    W = pd.DataFrame(dict(date=dates, spy=sleeves.get("SPY", np.zeros(n)), qqq=sleeves.get("QQQ", np.zeros(n)), thr=thr, rw=rw, w_spy=wts[:, 0], w_qqq=wts[:, 1], t2=t2, locked=locked, lev=lev, micro=micro, gold=gr, weekly_seq=wk_seq))
    W.to_csv(os.path.join(SU, "weekly_sequential_book.csv"), index=False)
    wm = pd.Series(wk_seq, index=dates); wm = (1 + wm).groupby(wm.index.to_period("M")).prod() - 1
    wm_fl = pd.Series(wk_seq_fixedlev, index=dates); wm_fl = (1 + wm_fl).groupby(wm_fl.index.to_period("M")).prod() - 1
    # ---- monthly leg
    mfiles = {a: os.path.join(SU, f"{a}_from1970_monthly_seq.csv") for a in ("SPY", "Gold", "Silver", "WTI")}
    M = None
    for a, f in mfiles.items():
        if not os.path.exists(f): continue
        d = pd.read_csv(f); d["date"] = pd.to_datetime(d.date); s = d.set_index("date").r.fillna(0.0).rename(a)
        M = s.to_frame() if M is None else M.join(s, how="outer")
    M = M.fillna(0.0); M["USD"] = 0.0; M["monthly_seq"] = M[["SPY", "Gold", "Silver", "WTI", "USD"]].mean(axis=1); M.index = M.index.to_period("M")
    spy6 = os.path.join(SU, "SPY_N6_from1970_monthly_seq.csv")
    if os.path.exists(spy6):
        d = pd.read_csv(spy6); d["date"] = pd.to_datetime(d.date); s6 = d.set_index("date").r.fillna(0.0); s6.index = s6.index.to_period("M")
        M["monthly_seq_N6"] = (M[["Gold", "Silver", "WTI", "USD"]].sum(axis=1) + s6.reindex(M.index).fillna(0.0)) / 5.0
    # ---- backtest counterparts
    B = pd.read_csv(os.path.join(REP, "zion_universe_book.csv")); B.index = pd.PeriodIndex(B.month, freq="M")
    U = pd.read_csv(os.path.join(REP, "universe_monthly_backtest.csv")); U.index = pd.PeriodIndex(U.month, freq="M")
    bl = pd.read_csv("/Users/castaglia/Desktop/ZION/reports/book_ledger.csv"); bl.index = pd.PeriodIndex(pd.to_datetime(bl.date), freq="M")
    A = pd.DataFrame(dict(weekly_seq=wm, weekly_seq_fixedlev=wm_fl)).join(M[["monthly_seq"] + (["monthly_seq_N6"] if "monthly_seq_N6" in M else [])], how="outer")
    A = A.join(B[["weekly", "monthly", "universe"]].rename(columns=lambda c: f"bt_{c}"), how="outer").join(U[["uni_1x", "spy_bh"]].rename(columns={"uni_1x": "bt_uni_1x", "spy_bh": "spy_bh"}), how="outer").join(bl[["book_r_base"]].rename(columns={"book_r_base": "bt_monthly_1990"}), how="outer")
    A["universe_seq"] = 0.5 * A.weekly_seq.fillna(0.0) + 0.5 * A.monthly_seq.fillna(0.0)
    if "monthly_seq_N6" in A: A["universe_seq_N6"] = 0.5 * A.weekly_seq.fillna(0.0) + 0.5 * A.monthly_seq_N6.fillna(0.0)
    A.to_csv(os.path.join(SU, "universe_sequential_monthly.csv"))
    windows = {"sector window 2021-06..2026-07": ("2021-06", "2026-07"), "universe backtest 2007-08..2026-07": ("2007-08", "2026-07"), "weekly-seq full 1993-01..2026-07": ("1993-01", "2026-07"), "monthly-seq full 1970-01..2026-07": ("1970-01", "2026-07")}
    rows = []
    for wl, (a0, a1) in windows.items():
        S = A.loc[(A.index >= pd.Period(a0, "M")) & (A.index <= pd.Period(a1, "M"))]
        for col in ("bt_uni_1x", "bt_universe", "universe_seq", "universe_seq_N6", "bt_weekly", "weekly_seq", "weekly_seq_fixedlev", "bt_monthly", "bt_monthly_1990", "monthly_seq", "monthly_seq_N6", "spy_bh"):
            if col not in S or S[col].notna().sum() < 12: continue
            x = S[col].dropna(); st = stats(x.to_numpy()); st.update(window=wl, series=col, first=str(x.index.min()), last=str(x.index.max())); rows.append(st)
    R = pd.DataFrame(rows)
    out = dict(weekly_decisions=dec_info, lev_seq=dict(first=float(lev[104]) if n > 104 else None, last=float(lev[-1]), min=float(lev.min()), max=float(lev.max())), weights_last=dict(spy=float(wts[-1, 0]), qqq=float(wts[-1, 1])), table=R.to_dict("records"))
    json.dump(out, open(os.path.join(SU, "universe_compare.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    with open(os.path.join(SU, "universe_compare.md"), "w") as f:
        def P(s=""): print(s); f.write(s + "\n")
        P("# ZION universe — backtest v sequential re-derivation"); P(f"weekly decisions: {dec_info}"); P(f"trailing leverage: {out['lev_seq']}; last trailing weights {out['weights_last']}\n")
        for wl in windows:
            q = R[R.window == wl].copy()
            if q.empty: continue
            for c in ("CAGR", "MaxDD", "worst", "down_share", "mean"): q[c] = (q[c] * 100).round(2)
            P(f"## {wl}"); P(q[["series", "n", "first", "last", "CAGR", "Sortino_house", "Sortino_std", "Sharpe", "MaxDD", "worst", "down_share", "mean"]].round(2).to_string(index=False)); P()


if __name__ == "__main__":
    main()

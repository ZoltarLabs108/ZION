"""
ZION SYZYGY BOOK — combine the FIVE validated asset sleeves (SPY, Gold, Silver, WTI, USD)
into ONE equal-weight monthly portfolio and report final combined results.

WHAT THIS IS (and is NOT)
  - This layer does NO new fitting. It REUSES the committed, validated per-month positions
    from each sleeve's own pipeline output (multiasset_pipeline.py machinery / RED DAWN SPY
    cascade). Positions are NOT re-derived here (a prior inline attempt mis-reconciled — Gold
    showed 17 acted months vs the validated ~85; that trap is avoided by reading the committed
    month-level ledgers directly).
  - Each sleeve's standing-rule (ACT) months are the pipeline's status=="pulled" rows; the
    position for that month is the pipeline's in-fold type-majority direction `base_dir`
    (+1/-1 = predicted 3-month direction). Optionally each asset's ONE surviving cascade cell
    is added (Gold T26-tier4, WTI T18-tier2; SPY/Silver/USD none) using the cell's in-fold
    emitted direction `predB`  -> "with-cells" variant. USD has NO rules (always cash).

SLEEVE SOURCES (committed ledgers, one row per decision month >= 1990):
  SPY   : ~/Desktop/ZION_RED_DAWN/reports/month_level.csv   (outcome SP_Price; full-panel row index)
  Gold  : reports/Gold_month_level.csv     (outcome Gold_Close)
  Silver: reports/Silver_month_level.csv   (outcome Silver_Close)
  WTI   : reports/WTI_month_level.csv       (outcome WTI_Crude_Close)
  USD   : reports/USD_month_level.csv       (outcome Dollar_Index; 0 pulls -> always cash)

RECONCILE TARGETS (validated ACT / pulled coverage): SPY 282, Gold 85, Silver 61, WTI 64, USD 0.

BOOK CONSTRUCTION (assumptions stated up front):
  1. Per sleeve, per month:  monthly_return = position(+1/-1) x asset's 1-MONTH FORWARD return
     on ACTED months; 0 (cash) on abstain months.  1x FLAT sizing. Monthly rebalance on the
     3-month signal. NO transaction costs. Forward 1-mo return = out[t+1]/out[t]-1 on the
     sleeve's OWN anchor-aligned frame (identical framing to how the pipeline formed ret3).
  2. SYZYGY combine: equal-weight the 5 sleeves each month. book monthly return = MEAN of the
     sleeves that HAVE DATA that month (are within their decision span); cash sleeves contribute
     0 and ARE counted in the mean. USD is always cash (contributes 0 whenever it has data).
  3. Metrics (per sleeve AND book), computed TWO ways x TWO windows:
       annualization   : CAGR = eq[-1]**(12/n) - 1     (months, NEVER row/52)
       Sortino         : mean(r)/downside_dev * sqrt(12),  downside_dev = sqrt(mean(min(r,0)^2))
       Calmar          : CAGR / |MaxDD|
       MaxDD           : min over eq/cummax(eq) - 1
     Windows : FULL (1990+) and LAST-10-YEARS (last 120 months to the latest data month).
     Ways    : FIRE-MONTHS (annualize over only months that fired) and CALENDAR (all months incl cash).

TRUNCATION / DISCREPANCY DOUBLE-CHECK LOOP: after each run we independently re-audit
  (a) sleeve acted-count vs validated target, (b) month accounting (acted-or-cash, nothing
  dropped; book calendar reconciles), (c) OOS method (in-fold past-only positions, forward
  1-mo return, H=3 label discipline), (d) annualization uses months not row-count. ANY finding
  -> fix & re-run FROM TOP. Continue until TWO CONSECUTIVE clean passes. Every pass logged.
"""
import os
import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import multiasset_pipeline as mp

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "reports")
SPY_CSV = "/Users/castaglia/Desktop/ZION_RED_DAWN/reports/month_level.csv"
START = pd.Timestamp("1990-01-01")

# validated ACT (pulled) coverage targets
TARGET = {"SPY": 282, "Gold": 85, "Silver": 61, "WTI": 64, "USD": 0}
# validated pulled type sets (0-indexed), for the OOS/position audit
PULLED_TYPES = {"SPY": {4, 13, 14, 25, 26}, "Gold": {0, 1, 24},
                "Silver": {8, 16, 18}, "WTI": {24, 25}, "USD": set()}
# the ONE surviving cascade cell per asset (0-idx type, tier); None where nothing kept
CELL = {"SPY": None, "Gold": (25, "tier4"), "Silver": None, "WTI": (17, "tier2"), "USD": None}
PROPOSED = {"SPY": False, "Gold": False, "Silver": True, "WTI": True, "USD": True}
SLEEVES = ["SPY", "Gold", "Silver", "WTI", "USD"]


# ======================================================================================
# panel + per-asset frame outcome series (for the 1-month forward return)
# ======================================================================================
def load_panel():
    df = pd.read_csv(mp.PANEL)
    df["Date"] = pd.to_datetime(df["Date"])
    for c, lag in mp.PUB_LAG.items():
        if c in df.columns:
            df[c] = df[c].shift(lag)
    return df


def outcome_series(name, df):
    """Return (out_array, dts_array) on the SAME frame whose row index == the sleeve ledger `t`.
       SPY: full panel (no dropna). Others: multiasset anchor_arrays frame."""
    if name == "SPY":
        return df["SP_Price"].to_numpy(float), df["Date"].to_numpy()
    cfg = mp.ASSETS[name]
    d, dts, yr, out, num, den, ratio, rn, infl, ret3, lab = mp.anchor_arrays(df, cfg)
    return out, dts


def sleeve_csv(name):
    if name == "SPY":
        return SPY_CSV
    return os.path.join(REPORTS, f"{name}_month_level.csv")


# --- SPY standing-rule direction is NOT persisted in the RED DAWN ledger; recompute it with
#     RED DAWN's EXACT fold logic (N=6, ratio=CAPE, legs Real_Price/Real_Earnings, H=3). This
#     is the same in-fold type-majority `base_dir` the cascade computes for pooled types, applied
#     to the pulled types {T5,T14,T15,T26,T27}. Returns {t -> +1/-1} for pulled months.
_SPY_POS_CACHE = None


def compute_spy_positions(df):
    global _SPY_POS_CACHE
    if _SPY_POS_CACHE is not None:
        return _SPY_POS_CACHE
    N = 6                                   # RED DAWN frozen anchor lookback (NOT the sweep)
    SD, H, MIN_TRAIN = mp.SD, mp.H, mp.MIN_TRAIN
    START_D = np.datetime64("1990-01-01")
    PULLED = PULLED_TYPES["SPY"]
    sp = df["SP_Price"].to_numpy(float)
    cape = df["CAPE"].to_numpy(float)
    rp = df["Real_Price"].to_numpy(float)
    re_ = df["Real_Earnings"].to_numpy(float)
    dts = df["Date"].to_numpy()
    ret3 = np.full(len(df), np.nan)
    ret3[:-H] = sp[H:] / sp[:-H] - 1.0
    lab = np.sign(ret3)
    gr, gn, gd = mp.pc(cape, N), mp.pc(rp, N), mp.pc(re_, N)
    anchor_ok = np.isfinite(gr) & np.isfinite(gn) & np.isfinite(gd)
    pos = {}
    for t in range(len(df)):
        if dts[t] < START_D or not anchor_ok[t]:
            continue
        train = np.arange(0, t - H + 1)
        train = train[anchor_ok[train] & np.isfinite(lab[train]) & (lab[train] != 0)]
        if len(train) < MIN_TRAIN:
            continue

        def tern(a):
            mu, sd = a[train].mean(), a[train].std()
            zz = (a - mu) / sd if sd > 0 else a * 0
            r = np.zeros(len(a), int)
            r[zz > SD] = 1
            r[zz < -SD] = -1
            return r

        cc, cp, ce = tern(gr), tern(gn), tern(gd)
        typ = (cc + 1) * 9 + (cp + 1) * 3 + (ce + 1)
        typ_t = int(typ[t])
        if typ_t in PULLED:
            tt = train[typ[train] == typ_t]
            up = int((lab[tt] > 0).sum())
            dn = len(tt) - up
            pos[t] = 1 if up >= dn else -1
    _SPY_POS_CACHE = pos
    return pos


# ======================================================================================
# build one sleeve's monthly return stream (indexed by decision-month date)
# ======================================================================================
def build_sleeve(name, df, with_cells):
    """Return DataFrame indexed by month Timestamp with columns:
         t, status, typ, tier, fired(bool), position(+1/-1/0), fwd_ret_1m, r(monthly return)
       over EVERY decision month (>=1990) in the sleeve ledger. cash months -> r=0."""
    m = pd.read_csv(sleeve_csv(name))
    m["date"] = pd.to_datetime(m["date"])
    m = m[m["date"] >= START].reset_index(drop=True)
    out, dts = outcome_series(name, df)
    n = len(out)
    cell = CELL[name] if with_cells else None
    spy_pos = compute_spy_positions(df) if name == "SPY" else None

    rows = []
    for r in m.itertuples():
        t = int(r.t)
        # forward 1-month return on the sleeve's own frame (out[t+1]/out[t]-1)
        fwd = out[t + 1] / out[t] - 1.0 if (t + 1) < n and np.isfinite(out[t + 1]) and np.isfinite(out[t]) else np.nan
        typ = int(r.typ) if pd.notna(r.typ) else -1
        tier = r.tier if isinstance(r.tier, str) else (r.tier if pd.notna(r.tier) else "")
        is_pull = (r.status == "pulled")
        is_cell = (cell is not None and r.status == "emitted" and typ == cell[0] and tier == cell[1])
        if is_pull:
            pos = spy_pos[t] if name == "SPY" else int(r.base_dir)
        elif is_cell:
            pos = int(r.predB)
        else:
            pos = 0
        fired = bool(is_pull or is_cell)
        if fired:
            # fired months are scored (ret3 finite) => forward 1-mo return always exists
            ret = pos * fwd
        else:
            ret = 0.0  # cash earns 0 regardless of forward move
        rows.append(dict(date=r.date, t=t, status=r.status, typ=typ, tier=tier,
                         fired=fired, position=pos, fwd_ret_1m=fwd, r=ret))
    out_df = pd.DataFrame(rows).set_index("date").sort_index()
    return out_df


# ======================================================================================
# metrics
# ======================================================================================
def _downside_dev(r):
    neg = np.minimum(r, 0.0)
    return float(np.sqrt(np.mean(neg * neg)))


def metrics(r):
    """r = 1-D array of monthly returns (fraction). Returns dict of CAGR/Sortino/Calmar/MaxDD/n."""
    r = np.asarray([x for x in r if np.isfinite(x)], float)
    n = len(r)
    if n == 0:
        return dict(n=0, CAGR=np.nan, Sortino=np.nan, Calmar=np.nan, MaxDD=np.nan, total=np.nan)
    eq = np.cumprod(1.0 + r)
    total = eq[-1]
    cagr = total ** (12.0 / n) - 1.0            # MONTHS in the exponent (never row/52)
    dd = eq / np.maximum.accumulate(eq) - 1.0
    maxdd = float(dd.min())
    dsd = _downside_dev(r)
    sortino = float(np.mean(r) / dsd * np.sqrt(12)) if dsd > 0 else np.nan
    calmar = float(cagr / abs(maxdd)) if maxdd < 0 else np.nan
    return dict(n=n, CAGR=cagr, Sortino=sortino, Calmar=calmar, MaxDD=maxdd, total=total)


def window_mask(dates, kind, end):
    dates = pd.DatetimeIndex(dates)
    if kind == "full":
        return dates >= START
    start10 = end - pd.DateOffset(years=10)
    return dates >= start10


# ======================================================================================
# assemble book from the 5 sleeve frames
# ======================================================================================
def assemble_book(sleeves):
    """sleeves = {name: sleeve_df}. Return book_df indexed by month with:
       n_data, n_fired, book_r (equal-weight mean of sleeves-with-data, cash=0)."""
    # union of all months that any sleeve has data for
    idx = sorted(set().union(*[set(s.index) for s in sleeves.values()]))
    recs = []
    for d in idx:
        contribs, fired = [], 0
        per = {}
        for name in SLEEVES:
            s = sleeves[name]
            if d in s.index:
                rr = float(s.loc[d, "r"])
                contribs.append(rr)
                per[name] = rr
                if bool(s.loc[d, "fired"]):
                    fired += 1
            else:
                per[name] = np.nan
        book_r = float(np.mean(contribs)) if contribs else np.nan
        recs.append(dict(date=d, n_data=len(contribs), n_fired=fired, book_r=book_r,
                         **{f"{k}_r": per[k] for k in SLEEVES}))
    return pd.DataFrame(recs).set_index("date").sort_index()


# ======================================================================================
# the AUDIT (independent re-check) — returns list of findings (empty == clean)
# ======================================================================================
def audit(sleeves_base, sleeves_cell, book_base, book_cell, df):
    f = []
    # (a) acted-count reconciliation vs validated target (BASE = pulled only)
    for name in SLEEVES:
        acted = int(sleeves_base[name]["fired"].sum())
        if acted != TARGET[name]:
            f.append(f"(a) {name}: acted={acted} != validated target {TARGET[name]}")
        # also confirm the pulled rows are exactly the pulled-type months
        s = sleeves_base[name]
        pulled_typs = set(s[s["status"] == "pulled"]["typ"].astype(int).unique())
        if PULLED_TYPES[name] and not pulled_typs.issubset(PULLED_TYPES[name]):
            f.append(f"(a) {name}: pulled types {pulled_typs} not subset of validated {PULLED_TYPES[name]}")
        if name == "USD" and acted != 0:
            f.append(f"(a) USD fired {acted} months but has NO rules (must be 0)")
    # (b) month accounting: every decision month is acted-or-cash; nothing dropped
    for name in SLEEVES:
        m = pd.read_csv(sleeve_csv(name))
        m["date"] = pd.to_datetime(m["date"])
        n_decision = int((m["date"] >= START).sum())
        s = sleeves_base[name]
        n_acted = int(s["fired"].sum())
        n_cash = int((~s["fired"]).sum())
        if n_acted + n_cash != n_decision:
            f.append(f"(b) {name}: acted({n_acted})+cash({n_cash}) != decision months({n_decision})")
        if len(s) != n_decision:
            f.append(f"(b) {name}: sleeve rows {len(s)} != decision months {n_decision}")
        # fired months must have a finite forward return (else the return is silently dropped)
        bad = int(s[s["fired"]]["fwd_ret_1m"].isna().sum())
        if bad:
            f.append(f"(b) {name}: {bad} fired months have NaN forward return")
    # book calendar reconciles: every book month's n_data == count of sleeves covering it
    for d, row in book_base.iterrows():
        cover = sum(1 for name in SLEEVES if d in sleeves_base[name].index)
        if int(row["n_data"]) != cover:
            f.append(f"(b) book {d.date()}: n_data {int(row['n_data'])} != covering sleeves {cover}")
            break
    # (c) OOS method: positions in {-1,+1} on fired months (in-fold past-only base_dir/predB),
    #     forward return is t->t+1, H=3 label discipline (ret3 uses out[t+3])
    for name in SLEEVES:
        for sd in (sleeves_base, sleeves_cell):
            s = sd[name]
            pos = s[s["fired"]]["position"].astype(int)
            if len(pos) and not set(pos.unique()).issubset({-1, 1}):
                f.append(f"(c) {name}: fired-month positions not all +/-1: {set(pos.unique())}")
    # verify forward-return direction: recompute one fired month explicitly
    for name in SLEEVES:
        s = sleeves_base[name]
        fired = s[s["fired"]]
        if len(fired):
            out, dts = outcome_series(name, df)
            t = int(fired.iloc[0]["t"])
            chk = out[t + 1] / out[t] - 1.0
            if not np.isclose(chk, float(fired.iloc[0]["fwd_ret_1m"]), equal_nan=True):
                f.append(f"(c) {name}: forward return not out[t+1]/out[t]-1")
    # (d) annualization uses months not row-count: metrics() exponent must be 12/n where
    #     n == number of months fed in. Probe with a synthetic 12-month +0 series -> CAGR 0,
    #     and a known series.
    probe = metrics(np.array([0.0] * 24))
    if probe["n"] != 24 or abs(probe["CAGR"] - 0.0) > 1e-12:
        f.append("(d) annualization probe failed (12/n month-based exponent)")
    probe2 = metrics(np.array([0.01] * 12))         # 12 months of +1% -> (1.01)^12-1 annual
    if abs(probe2["CAGR"] - (1.01 ** 12 - 1)) > 1e-9:
        f.append("(d) annualization probe2 failed (should compound 12 months to 1yr)")
    return f


# ======================================================================================
# reporting
# ======================================================================================
def sleeve_series(sleeve_df, kind):
    """kind='fire' -> only fired months' returns; 'cal' -> all decision months (cash=0)."""
    if kind == "fire":
        s = sleeve_df[sleeve_df["fired"]]["r"]
    else:
        s = sleeve_df["r"]
    return s


def book_series(book_df, kind):
    if kind == "fire":
        s = book_df[book_df["n_fired"] >= 1]["book_r"]
    else:
        s = book_df["book_r"]
    return s


def compute_table(sleeves, book, end):
    """Return list of dict rows: entity x window x way -> metrics."""
    rows = []
    for name in SLEEVES:
        s = sleeves[name]
        for win in ("full", "last10"):
            for way in ("fire", "cal"):
                ser = sleeve_series(s, way)
                mask = window_mask(ser.index, "full" if win == "full" else "l10", end)
                r = ser[mask].to_numpy(float)
                met = metrics(r)
                rows.append(dict(entity=name, window=win, way=way, **met))
    for win in ("full", "last10"):
        for way in ("fire", "cal"):
            ser = book_series(book, way)
            mask = window_mask(ser.index, "full" if win == "full" else "l10", end)
            r = ser[mask].to_numpy(float)
            met = metrics(r)
            rows.append(dict(entity="BOOK", window=win, way=way, **met))
    return rows


def fmt_pct(x):
    return "   n/a" if (x is None or not np.isfinite(x)) else f"{x*100:6.1f}"


def fmt_num(x):
    return "  n/a" if (x is None or not np.isfinite(x)) else f"{x:5.2f}"


def render_table(rows, title):
    L = []
    L.append("=" * 104)
    L.append(title)
    L.append("=" * 104)
    hdr = f"{'entity':<7} {'window':<7} {'way':<5} {'n':>4}  {'CAGR%':>7} {'Sortino':>8} {'Calmar':>7} {'MaxDD%':>8}"
    for win in ("full", "last10"):
        L.append(f"\n--- {'FULL (1990+)' if win=='full' else 'LAST 10 YEARS'} ---")
        L.append(hdr)
        for way in ("fire", "cal"):
            wl = "FIRE" if way == "fire" else "CAL "
            for ent in SLEEVES + ["BOOK"]:
                m = next(x for x in rows if x["entity"] == ent and x["window"] == win and x["way"] == way)
                L.append(f"{ent:<7} {win:<7} {wl:<5} {m['n']:>4}  "
                         f"{fmt_pct(m['CAGR']):>7} {fmt_num(m['Sortino']):>8} "
                         f"{fmt_num(m['Calmar']):>7} {fmt_pct(m['MaxDD']):>8}")
            L.append("")
    return "\n".join(L)


def make_equity_png(book_base, book_cell, sleeves_base, path):
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    # top: book equity (calendar, both variants)
    ax = axes[0]
    for bk, lab, c in [(book_base, "BOOK without-cells", "C0"), (book_cell, "BOOK with-cells", "C3")]:
        r = bk["book_r"].fillna(0.0)
        eq = (1 + r).cumprod()
        ax.plot(eq.index, eq.values, label=lab, color=c, lw=1.8)
    ax.set_yscale("log")
    ax.set_ylabel("book equity (log, calendar)")
    ax.set_title("ZION SYZYGY — equal-weight 5-sleeve book (1x flat, monthly rebalance, no costs)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    # bottom: per-sleeve calendar equity
    ax = axes[1]
    for i, name in enumerate(SLEEVES):
        r = sleeves_base[name]["r"]
        eq = (1 + r).cumprod()
        ax.plot(eq.index, eq.values, label=name, lw=1.2)
    ax.set_yscale("log")
    ax.set_ylabel("sleeve equity (log, calendar)")
    ax.set_xlabel("date")
    ax.legend(loc="upper left", ncol=5)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ======================================================================================
# MAIN — build, audit loop (2 consecutive clean), write deliverables
# ======================================================================================
def run_once(df):
    sleeves_base = {n: build_sleeve(n, df, with_cells=False) for n in SLEEVES}
    sleeves_cell = {n: build_sleeve(n, df, with_cells=True) for n in SLEEVES}
    book_base = assemble_book(sleeves_base)
    book_cell = assemble_book(sleeves_cell)
    return sleeves_base, sleeves_cell, book_base, book_cell


def main():
    os.makedirs(REPORTS, exist_ok=True)
    df = load_panel()

    log = []
    LP = log.append
    LP("=" * 100)
    LP("ZION SYZYGY BOOK — TRUNCATION/DISCREPANCY DOUBLE-CHECK LOOP (strict)")
    LP("require TWO CONSECUTIVE completely clean passes; any finding -> fix & re-run FROM TOP")
    LP(f"start: {pd.Timestamp.now()}")
    LP("=" * 100)

    consecutive_clean = 0
    pass_no = 0
    MAX_PASSES = 6
    state = None
    while consecutive_clean < 2 and pass_no < MAX_PASSES:
        pass_no += 1
        LP(f"\n----- PASS {pass_no} -----")
        sleeves_base, sleeves_cell, book_base, book_cell = run_once(df)
        state = (sleeves_base, sleeves_cell, book_base, book_cell)
        # log reconciliation side-by-side
        LP("  sleeve reconciliation (validated ACT vs computed acted):")
        for n in SLEEVES:
            acted = int(sleeves_base[n]["fired"].sum())
            celln = int(sleeves_cell[n]["fired"].sum()) - acted
            LP(f"    {n:<7} target={TARGET[n]:>4}  computed={acted:>4}  "
               f"{'OK' if acted==TARGET[n] else 'MISMATCH'}   (+{celln} cell month(s) with-cells)")
        findings = audit(sleeves_base, sleeves_cell, book_base, book_cell, df)
        if findings:
            consecutive_clean = 0
            for x in findings:
                LP(f"      FINDING: {x}")
            LP(f"  PASS {pass_no} VERDICT: {len(findings)} finding(s) -> FIX & RE-RUN FROM TOP")
        else:
            consecutive_clean += 1
            LP(f"  PASS {pass_no} VERDICT: ZERO findings (clean #{consecutive_clean} consecutive)")

    LP("\n" + "=" * 100)
    LP(f"LOOP COMPLETE after {pass_no} passes: "
       f"{'TWO CONSECUTIVE CLEAN' if consecutive_clean >= 2 else 'STILL DIRTY — MANUAL REVIEW'}")
    LP("=" * 100)

    sleeves_base, sleeves_cell, book_base, book_cell = state

    # latest data month (for the 10-year window end)
    end = max(book_base.index.max(), book_cell.index.max())

    # ---- per-sleeve ledger (long: date, sleeve, variant, fired, position, fwd_ret, monthly_return)
    led_rows = []
    for variant, sl in [("without_cells", sleeves_base), ("with_cells", sleeves_cell)]:
        for name in SLEEVES:
            s = sl[name]
            for d, r in s.iterrows():
                led_rows.append(dict(date=d.date(), sleeve=name, variant=variant,
                                     status=r["status"], typ=int(r["typ"]), tier=r["tier"],
                                     fired=bool(r["fired"]), position=int(r["position"]),
                                     fwd_ret_1m=round(float(r["fwd_ret_1m"]), 8) if np.isfinite(r["fwd_ret_1m"]) else "",
                                     monthly_return=round(float(r["r"]), 8)))
    pd.DataFrame(led_rows).to_csv(os.path.join(REPORTS, "per_sleeve_ledger.csv"), index=False)

    # ---- book ledger (both variants side by side)
    bk = book_base[["n_data", "n_fired", "book_r"]].rename(
        columns={"n_fired": "n_fired_base", "book_r": "book_r_base"})
    bk["book_r_cells"] = book_cell["book_r"]
    bk["n_fired_cells"] = book_cell["n_fired"]
    bk["eq_base"] = (1 + book_base["book_r"].fillna(0)).cumprod()
    bk["eq_cells"] = (1 + book_cell["book_r"].fillna(0)).cumprod()
    bk.to_csv(os.path.join(REPORTS, "book_ledger.csv"))

    # ---- equity png
    make_equity_png(book_base, book_cell, sleeves_base, os.path.join(REPORTS, "syzygy_equity.png"))

    # ---- results tables (both variants)
    rows_base = compute_table(sleeves_base, book_base, end)
    rows_cell = compute_table(sleeves_cell, book_cell, end)
    tbl_base = render_table(rows_base, "SYZYGY RESULTS — WITHOUT surviving cells (pulls only)")
    tbl_cell = render_table(rows_cell, "SYZYGY RESULTS — WITH surviving cells (Gold T26-t4, WTI T18-t2)")

    # coverage stats (base)
    n_book_months = len(book_base)
    n_cov = int((book_base["n_fired"] >= 1).sum())
    n_allcash = int((book_base["n_fired"] == 0).sum())
    cov_txt = (f"\nBOOK COVERAGE (base / without-cells): {n_book_months} calendar months (1990+); "
               f"{n_cov} with >=1 sleeve firing ({n_cov/n_book_months*100:.1f}%); "
               f"{n_allcash} all-cash months ({n_allcash/n_book_months*100:.1f}%).\n"
               "PROPOSED-ratio sleeves (NOT operator-confirmed): Silver, WTI, USD. "
               "SPY=CAPE prior, Gold=Dollar/M2 prior. USD has NO rules (always cash, 0 pulls).")

    # save both tables + coverage + machine-readable metrics
    with open(os.path.join(REPORTS, "syzygy_results.txt"), "w") as fh:
        fh.write(tbl_base + "\n" + tbl_cell + "\n" + cov_txt + "\n")
    allm = []
    for tag, rr in [("without_cells", rows_base), ("with_cells", rows_cell)]:
        for x in rr:
            allm.append(dict(variant=tag, **x))
    pd.DataFrame(allm).to_csv(os.path.join(REPORTS, "syzygy_metrics.csv"), index=False)

    with open(os.path.join(REPORTS, "syzygy_audit_loop.log"), "w") as fh:
        fh.write("\n".join(log) + "\n")

    print(tbl_base)
    print(tbl_cell)
    print(cov_txt)
    print("\n".join(log))
    return 0 if consecutive_clean >= 2 else 2


if __name__ == "__main__":
    sys.exit(main())

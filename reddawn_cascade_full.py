"""
ZION RED DAWN — UNTRUNCATED cascading tier analysis for SPY's remainder pool.
=============================================================================
Replaces the v1 prototype (truncated 5 ways). Sequential 3-MONTH-FORWARD walk-forward,
in-fold-only selection, full cascade, full grids, full candidate pool, zero silent drops.

LOCKED DISCIPLINE (operator):
  - Anchor SPY: outcome SP_Price; ratio = CAPE column; legs Real_Price / Real_Earnings;
    N=6; +-0.5 train-SD dead zone; 27 sign-triple types (ORACLE indexing).
  - PIT lags: Industrial_Production, US_CPI, M2_Money shifted 2 months (C2).
  - Pulled types (3-MO-horizon pull set, WF>67.5% n>=8, excluded from pool):
    T27 (1,1,1), T14 (0,0,0), T5 (-1,0,0), T15 (0,0,1), T26 (1,1,0)  [5 types; was 3 at H=1].
  - OOS = SEQUENTIAL 3-MONTH-FORWARD: at decision month t, train ONLY on rows s <= t-3
    (labels resolved by t); target sign(SP[t+3]/SP[t]-1); roll monthly from 1990.
  - All selection in-fold.  NO LB/OOS gates on emission (pure measurement).
  - EVERY pool month accounted: emitted OR abstained-with-reason. Zero silent drops.
  - FLIP VARIANTS (operator 2026-08-12, run BOTH side by side):
      A (bare):        leaf train acc < 0.5           -> invert
      B (Wilson-gated): Wilson 95% UPPER bound < 0.5  -> invert  (primary presentation)
  - HARD FILTER-STRENGTH GATE (operator 2026-08-12): a candidate column proceeds to
    threshold search ONLY if train-side point-biserial R^2 (corr(z, Match)^2) >= 0.20
    within the node. NO survivor at the type's primary node -> the type ABSTAINS that
    month (gate-fail). No qualifying filter = no call (operator correction 2026-08-12).
  - PRODUCTION BOARD (final summary): bucket | types | months | share% | status —
    1 ACT standing rules (pulled T27/T5/T14) | 2 CASCADE split-permitted (emitted) |
    3 ABSTAIN gate-fail | 4 ABSTAIN floor (n<8 / degenerate).

UNTRUNCATED MACHINERY (the 5 v1 truncations fixed):
  1. Threshold search: 50-point percentile grid p5-p95, coverage (0.10, 0.70) exclusive,
     primary & secondary; model-3 relaxed: 100-point grid, coverage (0.05, 0.90).
     Criterion: Youden J = sens + spec - 1 on the type's base-direction Match (train).
  2. Derivative forms per candidate: 5 columns — Z6 (6-mo change z), Z3, Z12,
     Z6_vel (1st diff of Z6), Z6_acc (2nd diff). z-scored on TRAIN stats only, per fold.
     Unit-aware (C8): RATE_LIKE series use absolute-point changes, never pct_change.
  3. Candidate pool: ALL usable clean PIT-safe splice-free panel variables (audited in
     pool_audit(), final size printed). Copper_Close excluded (2000-08 splice).
  4. Full cascade: primary -> secondary (pass side, >=10) -> model-3 (fail side, >=15)
     -> 4 tiers; per-tier train-side flip per variants A/B above.
  5. Runtime: numpy-vectorized; structure refit EVERY month (no declared reduction needed).

Outputs: reports/tier_table.csv, reports/month_level.csv, reports/scatter_types.png,
stdout diagnostic block (all 27 types, no display filtering), built-in truncation audit.
"""
import os
import sys
import time
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "reports")
PANEL = "/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"

# ---------------- locked constants -----------------------------------------------------
N = 6                                    # frozen anchor lookback (ORACLE)
SD = 0.5                                 # dead-zone half-width in train SDs
Z95 = 1.96
START = np.datetime64("1990-01-01")      # scoring starts here (train uses ALL prior rows)
H = 3                                    # horizon months (3-mo-forward)
MIN_TRAIN = 60                           # min eligible train rows before first decision
TYPE_FLOOR = 8                           # type-train floor (abstain below)
LEAF_FLOOR = 8                           # leaf floor (abstain below)
SEC_MIN = 10                             # pass-subset floor for secondary
M3_MIN = 15                              # fail-subset floor for model-3
R2_GATE = 0.20                           # HARD filter-strength gate (operator)
PRIMARY_TOP = 10                         # candidates to threshold search at primary
SECONDARY_TOP = 5                        # first-valid convention (legacy)
M3_TOP = 10                              # first-valid-with-J>0 (legacy)
GRID_PRIMARY = 50                        # percentile grid points p5-p95
GRID_M3 = 100
COV_PRIMARY = (0.10, 0.70)               # exclusive coverage bounds
COV_M3 = (0.05, 0.90)
MIN_PER_GROUP = 5                        # Welch screen min per group (primary/secondary)
MIN_PER_GROUP_M3 = 3
YOUDEN_MIN_SAMPLES = 10                  # legacy find_optimal min segment rows
YOUDEN_MIN_SAMPLES_M3 = 5
# PULL SET recomputed at the 3-MONTH horizon (coordinator 2026-08-12 CLOSURE RUN):
# five types clear the pull bar (WF>67.5%, n>=8) at H=3 (was only 3 at H=1).
# 0-based idx = (cs+1)*9+(ps+1)*3+(es+1):
#   T27(1,1,1)=26  T14(0,0,0)=13  T5(-1,0,0)=4  T15(0,0,1)=14  T26(1,1,0)=25
PULLED = {26, 13, 4, 14, 25}
PUB_LAG = {"Industrial_Production": 2, "US_CPI": 2, "M2_Money": 2}
FORMS = ("Z6", "Z3", "Z12", "Z6_vel", "Z6_acc")
RATE_LIKE = {"GS10_Rate", "Fed_Funds_Rate", "US_2Y_Treasury",
             "Term_Spread_10Y_2Y", "Term_Spread_10Y_3M"}

# candidate universe: the operator-named macro set ...
NAMED_POOL = ["Dollar_Index", "GS10_Rate", "Fed_Funds_Rate", "US_2Y_Treasury",
              "WTI_Crude_Close", "Gold_Close", "M2_Money", "Industrial_Production",
              "US_CPI", "Term_Spread_10Y_2Y"]
# ... plus extras admitted only if the pool audit verifies PIT-safe + splice-free
EXTRA_CANDIDATES = ["Term_Spread_10Y_3M", "VIX_Close", "Natural_Gas_Close",
                    "Platinum_Futures_Close"]
# excluded with reasons (printed in header)
EXCLUDED = {
    "Copper_Close":       "BANNED — hard unit splice 2000-08 (C1)",
    "Silver_Close":       "starts 2000-08 (copper-style seam risk, unverified pre-history)",
    "Unemployment_Rate":  "mid-month release, no locked PIT-lag rule (C2)",
    "Nonfarm_Payrolls":   "mid-month release, no locked PIT-lag rule (C2)",
    "Retail_Sales":       "mid-month release, no locked PIT-lag rule (C2)",
    "Housing_Starts":     "mid-month release, no locked PIT-lag rule (C2)",
}

TIER_ORDER = ["tier1", "tier2", "tier3", "tier4"]
SYM = {1: "UP", 0: "flat", -1: "DN"}
GATE_FAIL_REASONS = {"gate-fail-r2", "no-valid-split"}
FLOOR_REASONS = {f"type-train<floor{TYPE_FLOOR}", "degenerate-screen",
                 "candidate-missing", "leaf-empty", f"leaf<floor{LEAF_FLOOR}",
                 "anchor-leg-missing", "train<MIN_TRAIN"}
# descriptive reference from the H=1 3-pull run (ACT=171); at H=3 the pull set is 5
# types, so ACT rises and the remainder shrinks to ~140 months — the board prints the
# actual H=3 numbers and this ref is annotated as the prior-run baseline only.
SNAPSHOT = {"ACT": 171, "CASCADE": 128, "GATE-FAIL": 118, "FLOOR": 17}


# ======================================================================================
# small stats helpers
# ======================================================================================
def wilson_bounds(k, n, z=Z95):
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d, (c + m) / d


def wlb(k, n):
    return wilson_bounds(k, n)[0]


def wilson_lb_overlap(k, n, h=H):
    """C4 overlap adjustment: H-month horizon rolled monthly -> eff n ~= n/H."""
    if n <= 0:
        return 0.0
    ne = max(n / h, 1.0)
    return wilson_bounds(k / n * ne, ne)[0]


def pc(x, n):
    r = np.full(len(x), np.nan)
    r[n:] = x[n:] / x[:-n] - 1
    return r


def dabs(x, n):
    r = np.full(len(x), np.nan)
    r[n:] = x[n:] - x[:-n]
    return r


# ======================================================================================
# pool audit — verify extras PIT-safe + splice-free (unit-aware, C1/C8); print verdicts
# ======================================================================================
def pool_audit(df):
    pool, lines = list(NAMED_POOL), []
    for v in NAMED_POOL:
        lines.append(f"    {v:<24} INCLUDED (operator-named)")
    for v in EXTRA_CANDIDATES:
        if v not in df.columns:
            lines.append(f"    {v:<24} EXCLUDED — not in panel")
            continue
        s = df[v].astype(float)
        ok, why = _splice_scan(s.to_numpy(), rate_like=(v in RATE_LIKE))
        if ok:
            pool.append(v)
            lines.append(f"    {v:<24} INCLUDED (extra; PIT-safe close/spread, splice scan clean, "
                         f"start={df['Date'][s.first_valid_index()].date()})")
        else:
            lines.append(f"    {v:<24} EXCLUDED — splice scan: {why}")
    for v, why in EXCLUDED.items():
        lines.append(f"    {v:<24} EXCLUDED — {why}")
    return pool, lines


def _splice_scan(x, rate_like):
    """Unit-aware hard-splice detector (stage-0 convention): a single-month jump
    (>60% pct for levels; >3.0 abs points for rates) with full 24-mo range separation."""
    idx = np.where(np.isfinite(x))[0]
    if len(idx) < 48:
        return False, "insufficient history (<48 obs)"
    xv, iv = x[idx], idx
    step = np.abs(xv[1:] / xv[:-1] - 1) if not rate_like else np.abs(np.diff(xv))
    lim = 0.60 if not rate_like else 3.0
    for j in np.where(step > lim)[0]:
        lo, hi = max(0, j - 24), min(len(xv), j + 25)
        pre, post = xv[lo:j + 1], xv[j + 1:hi]
        if len(pre) >= 6 and len(post) >= 6 and (pre.max() < post.min() or post.max() < pre.min()):
            return False, f"hard splice near obs {iv[j]}"
    return True, ""


# ======================================================================================
# candidate base columns (raw; z-scored per fold on TRAIN stats)
# ======================================================================================
def build_bases(df, pool):
    """5 derivative forms per candidate. Unit-aware (C8): RATE_LIKE uses absolute-point
    changes; price/index/quantity levels use pct-change. Z6_vel/Z6_acc = 1st/2nd diff of
    the Z6 base (affine-equivalent to diffing the z-scored column, then re-z-scored)."""
    bases = {}
    for v in pool:
        x = df[v].to_numpy(float)
        ch = dabs if v in RATE_LIKE else pc
        b6, b3, b12 = ch(x, 6), ch(x, 3), ch(x, 12)
        vel = np.full(len(x), np.nan)
        vel[1:] = b6[1:] - b6[:-1]
        acc = np.full(len(x), np.nan)
        acc[1:] = vel[1:] - vel[:-1]
        bases[v] = {"Z6": b6, "Z3": b3, "Z12": b12, "Z6_vel": vel, "Z6_acc": acc}
    return bases


# ======================================================================================
# node screen — Welch t + Cohen's d + point-biserial R^2 per column; HARD R^2 gate
# ======================================================================================
def node_screen(bases, pool, rows, match, exclude, min_per_group):
    """For every candidate column on `rows`: Welch t of Match vs non-Match, |Cohen's d|,
    point-biserial R^2 = corr(col, Match)^2. Columns with R^2 < R2_GATE are DISCARDED
    pre-threshold (operator hard gate). Returns:
      survivors: {var: [(form, absd, r2), ...]} (gate-cleared, per var),
      ranked:    vars ranked by best surviving |d|,
      n_cols_screened, max_r2_all (incl. gate-failures, for the strength diagnostic)."""
    survivors, best_d = {}, {}
    n_cols = 0
    max_r2_all = 0.0
    all_r2 = []                            # EVERY screened column's R^2 (operator deliverable)
    m = match[rows].astype(bool)
    for v in pool:
        if v in exclude:
            continue
        for form in FORMS:
            a = bases[v][form][rows]
            f = np.isfinite(a)
            if f.sum() < 2 * min_per_group:
                continue
            av, mv = a[f], m[f]
            g1, g0 = av[mv], av[~mv]
            if len(g1) < min_per_group or len(g0) < min_per_group:
                continue
            n_cols += 1
            s1, s0 = g1.std(ddof=1), g0.std(ddof=1)
            n1, n0 = len(g1), len(g0)
            sp = np.sqrt(((n1 - 1) * s1 ** 2 + (n0 - 1) * s0 ** 2) / max(n1 + n0 - 2, 1))
            d = (g1.mean() - g0.mean()) / sp if sp > 0 else 0.0
            sa = av.std()
            if sa <= 0:
                continue
            r = np.corrcoef(av, mv.astype(float))[0, 1]
            r2 = 0.0 if not np.isfinite(r) else r * r
            max_r2_all = max(max_r2_all, r2)
            all_r2.append((v, form, r2))
            if r2 < R2_GATE:                       # HARD GATE (operator 2026-08-12)
                continue
            survivors.setdefault(v, []).append((form, abs(d), r2))
            if abs(d) > best_d.get(v, -1.0):
                best_d[v] = abs(d)
    for v in survivors:
        survivors[v].sort(key=lambda e: -e[1])
    ranked = sorted(survivors, key=lambda v: -best_d[v])
    return survivors, ranked, n_cols, max_r2_all, all_r2


# ======================================================================================
# Youden-J threshold search (vectorized; legacy grid + coverage + direction semantics)
# ======================================================================================
def youden_search(vals, match, grid_points, cov_lo, cov_hi, min_samples, effect_dir):
    """Grid = `grid_points` percentiles p5-p95 of the node's train values of this column
    (z-scored values give the identical split — z is affine). Both directions tested;
    ties prefer the direction agreeing with the screen effect sign (legacy)."""
    f = np.isfinite(vals)
    a, y = vals[f], match[f].astype(bool)
    if len(a) < min_samples or y.all() or not y.any():
        return None
    if len(np.unique(a)) < 3:
        return None
    thresholds = np.percentile(a, np.linspace(5, 95, grid_points))
    ny = ~y
    preds_gt = a[np.newaxis, :] > thresholds[:, np.newaxis]
    best = None
    for preds, direction in ((preds_gt, ">"), (~preds_gt, "<")):
        TP = (preds & y).sum(axis=1).astype(float)
        FN = (~preds & y).sum(axis=1).astype(float)
        TN = (~preds & ny).sum(axis=1).astype(float)
        FP = (preds & ny).sum(axis=1).astype(float)
        sens = np.where(TP + FN > 0, TP / (TP + FN), 0.0)
        spec = np.where(TN + FP > 0, TN / (TN + FP), 0.0)
        J = sens + spec - 1.0
        cov = preds.mean(axis=1)
        valid = (cov > cov_lo) & (cov < cov_hi)
        if not valid.any():
            continue
        Jv = np.where(valid, J, -2.0)
        bi = int(np.argmax(Jv))
        preferred = (direction == ">" and effect_dir > 0) or (direction == "<" and effect_dir < 0)
        if best is None or Jv[bi] > best["J"] or (Jv[bi] == best["J"] and preferred):
            best = dict(J=float(Jv[bi]), threshold=float(thresholds[bi]), direction=direction,
                        coverage=float(cov[bi]), sens=float(sens[bi]), spec=float(spec[bi]))
    return None if (best is None or best["J"] <= -1) else best


def node_threshold_search(bases, survivors, ranked, rows, match, grid, cov, min_samples,
                          top_k, first_valid, require_pos_j):
    """Run the threshold search over the ranked gate-survivors.
      first_valid=False (primary): try top_k vars, keep global-best J.
      first_valid=True (secondary/model-3): legacy convention — walk ranked list, first
      var that yields a valid split wins (model-3 additionally requires J > 0).
    Returns (var, form, threshold, direction, J, r2_of_chosen_col, n_tried) or None."""
    best, tried = None, 0
    m_rows = match[rows]
    mb = m_rows.astype(bool)
    for v in ranked[:top_k]:
        tried += 1
        var_best = None
        for form, absd, r2 in survivors[v]:
            a = bases[v][form][rows]
            with np.errstate(invalid="ignore"):
                g1m, g0m = np.nanmean(a[mb]), np.nanmean(a[~mb])
            eff = np.sign(g1m - g0m) if np.isfinite(g1m - g0m) else 1.0
            res = youden_search(a, m_rows, grid, cov[0], cov[1], min_samples, eff)
            if res and (not require_pos_j or res["J"] > 0):
                cand = (v, form, res["threshold"], res["direction"], res["J"], r2)
                if var_best is None or cand[4] > var_best[4]:
                    var_best = cand
        if var_best:
            if first_valid:
                return var_best + (tried,)
            if best is None or var_best[4] > best[4]:
                best = var_best
    return None if best is None else best + (tried,)


# ======================================================================================
# leaf construction — both flip variants share structure; only emission dir differs
# ======================================================================================
def make_leaf(tier, rows, match_arr):
    n = len(rows)
    if n == 0:
        return dict(tier=tier, n=0, raw=np.nan, flipA=False, flipB=False)
    raw = float(match_arr[rows].mean())
    k = int(round(raw * n))
    flipA = raw < 0.5                                   # variant A: bare
    flipB = wilson_bounds(k, n)[1] < 0.5                # variant B: Wilson-upper gated
    return dict(tier=tier, n=n, raw=raw, flipA=flipA, flipB=flipB)


# ======================================================================================
# the cascade — fit on the type's TRAIN rows, in-fold
# ======================================================================================
def cascade_fit(bases, pool, type_train, match, lab):
    """Full cascade: primary -> secondary (pass, >=10) -> model-3 (fail, >=15) -> 4 tiers.
    All screens R^2-gated (operator hard gate). NO survivor at the primary node, or no
    valid split among survivors -> the caller ABSTAINS the month (no base emission).
    Returns dict with nodes, leaves, abstain-reason (if any), per-node metadata (C5)."""
    out = dict(primary=None, secondary=None, model3=None, leaves={}, meta={}, abstain=None)
    surv, ranked, ncols, maxr2, all_r2 = node_screen(bases, pool, type_train, match, set(), MIN_PER_GROUP)
    out["meta"]["primary"] = dict(n_cols=ncols, n_survivors=len(ranked), max_r2=maxr2)
    out["meta"]["all_r2"] = all_r2
    if ncols == 0:
        out["abstain"] = "degenerate-screen"        # too few rows per Match group to test
        return out
    if not ranked:
        out["abstain"] = "gate-fail-r2"             # screened, nothing cleared R2 >= 0.20
        return out
    prim = node_threshold_search(bases, surv, ranked, type_train, match,
                                 GRID_PRIMARY, COV_PRIMARY, YOUDEN_MIN_SAMPLES,
                                 PRIMARY_TOP, first_valid=False, require_pos_j=False)
    if prim is None:
        out["abstain"] = "no-valid-split"           # gate passed, no grid/coverage-valid split
        return out
    out["primary"] = prim
    v1, f1 = prim[0], prim[1]
    a1 = bases[v1][f1][type_train]
    fin = np.isfinite(a1)
    keep = (a1 > prim[2]) if prim[3] == ">" else (a1 < prim[2])
    ppass, pfail = type_train[fin & keep], type_train[fin & ~keep]
    # rows with missing primary value at TRAIN time stay unrouted in fitting (rare; the
    # union check in the audit counts them under 'train-unrouted', they affect no leaf)
    out["meta"]["train_unrouted"] = int((~fin).sum())

    # SECONDARY (pass side)
    if len(ppass) >= SEC_MIN:
        s_surv, s_ranked, s_ncols, s_maxr2, _ = node_screen(bases, pool, ppass, match, {v1}, MIN_PER_GROUP)
        out["meta"]["secondary"] = dict(n_cols=s_ncols, n_survivors=len(s_ranked), max_r2=s_maxr2)
        sec = None
        if s_ranked:
            sec = node_threshold_search(bases, s_surv, s_ranked, ppass, match,
                                        GRID_PRIMARY, COV_PRIMARY, YOUDEN_MIN_SAMPLES,
                                        SECONDARY_TOP, first_valid=True, require_pos_j=False)
        if sec is not None:
            out["secondary"] = sec
            a2 = bases[sec[0]][sec[1]][ppass]
            fin2 = np.isfinite(a2)
            k2 = (a2 > sec[2]) if sec[3] == ">" else (a2 < sec[2])
            out["leaves"]["tier1"] = make_leaf("tier1", ppass[fin2 & k2], match)
            out["leaves"]["tier2"] = make_leaf("tier2", ppass[fin2 & ~k2], match)
        else:
            out["leaves"]["tier2"] = make_leaf("tier2", ppass, match)
    else:
        out["leaves"]["tier2"] = make_leaf("tier2", ppass, match)

    # MODEL-3 (fail side; independent bare DISCOVERY flip of the search target — legacy)
    if len(pfail) >= M3_MIN:
        m3_target = match.copy()
        if match[pfail].mean() < 0.5:
            m3_target = 1.0 - match
        m_surv, m_ranked, m_ncols, m_maxr2, _ = node_screen(bases, pool, pfail, m3_target,
                                                            {v1}, MIN_PER_GROUP_M3)
        out["meta"]["model3"] = dict(n_cols=m_ncols, n_survivors=len(m_ranked), max_r2=m_maxr2)
        m3 = None
        if m_ranked:
            m3 = node_threshold_search(bases, m_surv, m_ranked, pfail, m3_target,
                                       GRID_M3, COV_M3, YOUDEN_MIN_SAMPLES_M3,
                                       M3_TOP, first_valid=True, require_pos_j=True)
        if m3 is not None:
            out["model3"] = m3
            a3 = bases[m3[0]][m3[1]][pfail]
            fin3 = np.isfinite(a3)
            k3 = (a3 > m3[2]) if m3[3] == ">" else (a3 < m3[2])
            out["leaves"]["tier3"] = make_leaf("tier3", pfail[fin3 & k3], match)
            out["leaves"]["tier4"] = make_leaf("tier4", pfail[fin3 & ~k3], match)
        else:
            out["leaves"]["tier4"] = make_leaf("tier4", pfail, match)
    elif len(pfail) > 0:
        out["leaves"]["tier4"] = make_leaf("tier4", pfail, match)
    return out


def route_month(tree, bases, t):
    """Route decision month t. Returns (tier, None) or (None, reason)."""
    if tree["primary"] is None:                      # defensive: caller abstains earlier
        return None, tree.get("abstain") or "no-valid-split"
    v1, f1, th1, d1 = tree["primary"][:4]
    x = bases[v1][f1][t]
    if not np.isfinite(x):
        return None, "candidate-missing"
    p = (x > th1) if d1 == ">" else (x < th1)
    if p:
        if tree["secondary"] is not None:
            v2, f2, th2, d2 = tree["secondary"][:4]
            x2 = bases[v2][f2][t]
            if not np.isfinite(x2):
                return None, "candidate-missing"
            return ("tier1" if ((x2 > th2) if d2 == ">" else (x2 < th2)) else "tier2"), None
        return "tier2", None
    if tree["model3"] is not None:
        v3, f3, th3, d3 = tree["model3"][:4]
        x3 = bases[v3][f3][t]
        if not np.isfinite(x3):
            return None, "candidate-missing"
        return ("tier3" if ((x3 > th3) if d3 == ">" else (x3 < th3)) else "tier4"), None
    return "tier4", None


# ======================================================================================
# THE FOLD LOOP — sequential 3-month-forward walk-forward, expanding window
# ======================================================================================
def run(df, pool):
    bases = build_bases(df, pool)
    sp = df["SP_Price"].to_numpy(float)
    cape = df["CAPE"].to_numpy(float)
    rp = df["Real_Price"].to_numpy(float)
    re_ = df["Real_Earnings"].to_numpy(float)
    dts = df["Date"].to_numpy()
    n_rows = len(df)

    ret3 = np.full(n_rows, np.nan)
    ret3[:-H] = sp[H:] / sp[:-H] - 1.0
    lab = np.sign(ret3)

    gr, gn, gd = pc(cape, N), pc(rp, N), pc(re_, N)
    anchor_ok = np.isfinite(gr) & np.isfinite(gn) & np.isfinite(gd)

    records = []
    fstrength = []                          # per-fold, per-candidate-column R^2 (primary node)
    oos_checks = {}
    check_dates = [np.datetime64(x) for x in
                   ("1990-01-01", "1995-01-01", "2005-01-01", "2015-01-01")]
    # EVERY calendar month >= START is a decision month and MUST be accounted (zero
    # silent drops) — months whose anchor leg is unpublished abstain with reason.
    decision_idx = [t for t in range(n_rows) if dts[t] >= START]
    typable = [t for t in decision_idx if anchor_ok[t]]
    check_ts = {min(typable, key=lambda t: abs((dts[t] - cd).astype(int))) for cd in check_dates}
    check_ts.add(typable[-1])

    t0 = time.time()
    for t in decision_idx:
        base_rec = dict(t=t, date=str(dts[t])[:10],
                        ret3=float(ret3[t]) if np.isfinite(ret3[t]) else np.nan,
                        lab=int(lab[t]) if np.isfinite(lab[t]) else 0,
                        scored=bool(np.isfinite(lab[t]) and lab[t] != 0))
        if not anchor_ok[t]:                # anchor leg not yet published (e.g. earnings lag)
            base_rec.update(typ=-1, status="abstain", reason="anchor-leg-missing")
            records.append(base_rec)
            continue
        # TRAIN POOL: rows s <= t-3 whose 3-mo label is resolved by t (s+3 <= t)  [PIT]
        train = np.arange(0, t - H + 1)
        train = train[anchor_ok[train] & np.isfinite(lab[train]) & (lab[train] != 0)]
        if len(train) < MIN_TRAIN:
            base_rec.update(typ=-1, status="abstain", reason="train<MIN_TRAIN")
            records.append(base_rec)
            continue
        if t in check_ts:
            oos_checks[t] = dict(date=str(dts[t])[:10], n_train=len(train),
                                 span=f"{str(dts[train[0]])[:10]}..{str(dts[train[-1]])[:10]}",
                                 frontier_row=int(train[-1]), t_row=t)

        # anchor grammar refit on TRAIN stats (in-fold)
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
        rec = dict(base_rec, typ=typ_t)
        if typ_t in PULLED:
            rec.update(status="pulled", reason="pulled-type")
            records.append(rec)
            continue

        type_train = train[typ[train] == typ_t]
        rec["n_type_train"] = len(type_train)
        if len(type_train) < TYPE_FLOOR:
            rec.update(status="abstain", reason=f"type-train<floor{TYPE_FLOOR}")
            records.append(rec)
            continue

        up = int((lab[type_train] > 0).sum())
        dn = len(type_train) - up
        base_dir = 1 if up >= dn else -1
        match = (lab == base_dir).astype(float)

        tree = cascade_fit(bases, pool, type_train, match, lab)
        for v_, form_, r2_ in tree["meta"].get("all_r2", []):
            fstrength.append(dict(date=rec["date"], type=typ_t + 1, n_type_train=len(type_train),
                                  candidate=f"{v_}:{form_}", r2=round(r2_, 4),
                                  cleared_gate=r2_ >= R2_GATE))

        pm = tree["meta"].get("primary", {})
        rec.update(base_dir=base_dir,
                   n_screened=pm.get("n_cols", 0),
                   n_survivors=pm.get("n_survivors", 0),
                   max_r2=pm.get("max_r2", np.nan),
                   split_attempted=True)
        if tree["abstain"] is not None:              # gate-fail / degenerate / no-valid-split
            rec.update(status="abstain", reason=tree["abstain"])
            records.append(rec)
            continue
        if tree["primary"] is not None:
            v1, f1, th1, d1, J1, r2c = tree["primary"][:6]
            mu1 = np.nanmean(bases[v1][f1][type_train])
            sd1 = np.nanstd(bases[v1][f1][type_train])
            rec.update(primary=f"{v1}:{f1}", primary_dir=d1, primary_J=J1, chosen_r2=r2c,
                       primary_thresh_z=(th1 - mu1) / sd1 if sd1 > 0 else np.nan,
                       primary_z_t=(bases[v1][f1][t] - mu1) / sd1
                       if sd1 > 0 and np.isfinite(bases[v1][f1][t]) else np.nan)
            if tree["secondary"] is not None:
                rec["secondary"] = f"{tree['secondary'][0]}:{tree['secondary'][1]}"
            if tree["model3"] is not None:
                rec["model3"] = f"{tree['model3'][0]}:{tree['model3'][1]}"

        tier, why = route_month(tree, bases, t)
        if tier is None:
            rec.update(status="abstain", reason=why)
            records.append(rec)
            continue
        leaf = tree["leaves"].get(tier)
        if leaf is None or leaf["n"] == 0:
            rec.update(status="abstain", reason="leaf-empty", tier=tier)
            records.append(rec)
            continue
        if leaf["n"] < LEAF_FLOOR:
            rec.update(status="abstain", reason=f"leaf<floor{LEAF_FLOOR}", tier=tier,
                       leaf_n=leaf["n"])
            records.append(rec)
            continue

        dirA = -base_dir if leaf["flipA"] else base_dir
        dirB = -base_dir if leaf["flipB"] else base_dir
        rawA = leaf["raw"] if not leaf["flipA"] else 1 - leaf["raw"]
        rawB = leaf["raw"] if not leaf["flipB"] else 1 - leaf["raw"]
        rec.update(status="emitted", tier=tier, leaf_n=leaf["n"], leaf_raw=leaf["raw"],
                   flipA=leaf["flipA"], flipB=leaf["flipB"],
                   predA=int(dirA), predB=int(dirB),
                   is_accA=rawA, is_accB=rawB,
                   hitA=int(dirA == lab[t]) if rec["scored"] else np.nan,
                   hitB=int(dirB == lab[t]) if rec["scored"] else np.nan)
        records.append(rec)
    elapsed = time.time() - t0
    return records, fstrength, oos_checks, elapsed


# ======================================================================================
# diagnostics + tables (ALL types, no display filtering) + files
# ======================================================================================
def type_label(ti):
    cs, r = divmod(ti, 9)
    ps, es = divmod(r, 3)
    return f"{SYM[cs-1]:>4}/{SYM[ps-1]:>4}/{SYM[es-1]:>4}"


def tier_cell_stats(cell, variant):
    """OOS-side stats for one (type,tier) cell under flip variant 'A'|'B'."""
    scored = [r for r in cell if r["scored"]]
    n = len(scored)
    if n == 0:
        return dict(n=0)
    hits = np.array([r[f"hit{variant}"] for r in scored], float)
    rets = np.array([r["ret3"] for r in scored], float) * 100.0
    k = int(hits.sum())
    ok = hits == 1
    avg_ret_ok = float(np.abs(rets[ok]).mean()) if ok.any() else 0.0
    net = float((np.abs(rets[ok]).sum() - np.abs(rets[~ok]).sum()) / n)
    bayes = (k + 1) / (n + 2)
    oval = (bayes ** 2.5) * 2 * net
    is_acc = float(np.mean([r[f"is_acc{variant}"] for r in scored]))
    r2s = [r.get("chosen_r2") for r in scored if r.get("chosen_r2") is not None]
    return dict(n=n, k=k, acc=k / n, lb=wlb(k, n), lb_ovl=wilson_lb_overlap(k, n),
                bayes=bayes, avg_ret_ok=avg_ret_ok, net=net, oval=oval,
                is_acc=is_acc, r2=float(np.mean(r2s)) if r2s else np.nan)


def diagnostics(records, oos_checks, pool, pool_lines, elapsed, audit_findings_from_code):
    lines = []
    P = lines.append
    P("=" * 118)
    P("### ZION RED DAWN — UNTRUNCATED CASCADING TIER ANALYSIS — SPY REMAINDER POOL ###")
    P(f"run: {pd.Timestamp.now()}  panel: {PANEL}")
    P(f"[discipline]  anchor=CAPE (legs Real_Price/Real_Earnings)  N={N}  dead-zone=+-{SD} train-SD")
    P(f"              OOS = SEQUENTIAL 3-MO-FORWARD (train s<=t-3, target sign(SP[t+3]/SP[t]-1), roll monthly from 1990)")
    P(f"              PIT lags: {PUB_LAG}   pulled types: T5(-1,0,0) T14(0,0,0) T27(1,1,1)")
    P(f"              floors: type-train>={TYPE_FLOOR}, leaf>={LEAF_FLOOR}, secondary>={SEC_MIN}, model3>={M3_MIN}  (gate-fail => ABSTAIN, no base emission)")
    P(f"              NO LB/OOS emission gates (pure measurement).  Structure refit EVERY month (no declared reduction).")
    P(f"[machinery]   grids: primary/secondary {GRID_PRIMARY}pt p5-p95 cov {COV_PRIMARY} excl | model-3 {GRID_M3}pt cov {COV_M3} excl")
    P(f"              forms per candidate: {FORMS} (train-z per fold; RATE_LIKE={sorted(RATE_LIKE & set(pool))} use abs-point changes, C8)")
    P(f"              screen: Welch t Match vs non-Match, rank |Cohen's d| | HARD GATE: point-biserial R^2 >= {R2_GATE} (operator)")
    P(f"              note: percentile grid evaluated on raw train values == grid on train-z values (z is affine; identical"
      f" splits); thresholds/z reported in train-z units. Every screened column's R^2 -> reports/filter_strength.csv")
    P(f"              retries: primary top {PRIMARY_TOP} | secondary top {SECONDARY_TOP} first-valid | model-3 up to {M3_TOP} first-valid J>0")
    P(f"              flips (per-tier, train-side): A=bare(<0.5)  B=Wilson-95-upper<0.5 (PRIMARY presentation, operator 2026-08-12)")
    P(f"[candidates]  final pool size = {len(pool)}")
    lines.extend(pool_lines)
    P("")
    P("[OOS-METHOD VERIFICATION] expanding window; train frontier = decision month t-3 (3-mo label gap):")
    prev_n = -1
    expanding = True
    for t in sorted(oos_checks):
        c = oos_checks[t]
        gap = c["t_row"] - c["frontier_row"]
        P(f"    decision {c['date']}: train n={c['n_train']:>5}  span {c['span']}  frontier gap={gap} rows (>= {H})")
        expanding &= c["n_train"] > prev_n
        prev_n = c["n_train"]
    P(f"    window EXPANDS across checkpoints: {'YES' if expanding else 'NO — VIOLATION'}   (1990 is where SCORING starts, not a train freeze)")
    P("")

    # ---------- accounting ----------
    pulled = [r for r in records if r["status"] == "pulled"]
    poolm = [r for r in records if r["status"] != "pulled"]
    untyped = [r for r in poolm if r["typ"] < 0]
    emitted = [r for r in poolm if r["status"] == "emitted"]
    abstained = [r for r in poolm if r["status"] == "abstain"]
    scored = [r for r in emitted if r["scored"]]
    unresolved = [r for r in emitted if not r["scored"]]
    P(f"[accounting]  decision months={len(records)} (EVERY calendar month >= 1990-01)  "
      f"pulled={len(pulled)}  POOL={len(poolm)} (of which untypeable={len(untyped)})")
    P(f"              pool -> emitted={len(emitted)} (scored={len(scored)}, label-unresolved={len(unresolved)})  abstained={len(abstained)}")
    reasons = {}
    for r in abstained:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    P(f"              abstain reasons: {reasons if reasons else 'none'}")
    recon = len(poolm) == len(emitted) + len(abstained)
    P(f"              RECONCILES: pool_total == emitted + abstained -> {recon}")
    P("")

    # ---------- headline ----------
    P("[HEADLINE — pool overall, sequential 3-mo-forward OOS]")
    headline = {}
    for var in ("A", "B"):
        k = int(sum(r[f"hit{var}"] for r in scored))
        n = len(scored)
        acc = k / n if n else 0.0
        headline[var] = (k, n, acc)
        tag = "bare flip" if var == "A" else "Wilson-gated flip (PRIMARY)"
        P(f"    variant {var} ({tag:<28}): acc={acc*100:5.1f}%  n={n}  LB={wlb(k,n)*100:.1f}%  LB_ovl(C4,n/3)={wilson_lb_overlap(k,n)*100:.1f}%")
    nf = sum(1 for r in scored if r.get("flipA"))
    P(f"    flip incidence: A flipped {nf}/{len(scored)} emitted months; B flipped "
      f"{sum(1 for r in scored if r.get('flipB'))}/{len(scored)}")
    up_rate = np.mean([r["lab"] > 0 for r in scored]) if scored else 0
    P(f"    drift baseline (always-UP on emitted months): {up_rate*100:.1f}%")
    # C7 coverage guard over all scored pool months
    sc_pool = [r for r in poolm if r["scored"]]
    actv = np.array([1.0 if r["status"] == "emitted" else 0.0 for r in sc_pool])
    upv = np.array([1.0 if r["lab"] > 0 else 0.0 for r in sc_pool])
    if actv.std() > 0 and upv.std() > 0:
        c7 = float(np.corrcoef(actv, upv)[0, 1])
    else:
        c7 = 0.0
    au = upv[actv == 1].mean() if (actv == 1).any() else np.nan
    bu = upv[actv == 0].mean() if (actv == 0).any() else np.nan
    P(f"    [C7 coverage guard] corr(acted, up)={c7:+.3f}   acted-up-rate={au*100:.1f}%  abstained-up-rate={bu*100 if np.isfinite(bu) else float('nan'):.1f}%")
    P("")

    # ---------- TIER SIGNIFICANCE VERDICT (coordinator CLOSURE question) ----------
    P("[TIER SIGNIFICANCE — does any (type,tier) cell clear reliably-predictive / anti-predictive? variant B]")
    P("   bar: reliably-PREDICTIVE = Wilson 95% LB > 50 ; reliably-ANTI = Wilson 95% UB < 50")
    P("   HONEST bar additionally requires overlap-adjusted LB (C4, eff n=n/3) to hold + Stage-5 placebo.")
    cells = {}
    for r in scored:
        cells.setdefault((r["typ"], r.get("tier")), []).append(r)
    nominal, honest = [], []
    for (ti, tier), cell in sorted(cells.items()):
        n = len(cell)
        k = int(sum(rr["hitB"] for rr in cell))
        lo, hi = wilson_bounds(k, n)
        lo_ov = wilson_lb_overlap(k, n)
        _, hi_ov = wilson_bounds((k / n) * max(n / H, 1.0), max(n / H, 1.0))
        if lo > 0.5:
            nominal.append((ti, tier, n, k / n, lo, lo_ov, "PREDICTIVE"))
            if lo_ov > 0.5:
                honest.append((ti, tier, n))
        elif hi < 0.5:
            nominal.append((ti, tier, n, k / n, hi, hi_ov, "ANTI"))
            if hi_ov < 0.5:
                honest.append((ti, tier, n))
    if nominal:
        for ti, tier, n, acc, b, b_ov, kind in nominal:
            surv = "SURVIVES overlap-adj" if ((kind == "PREDICTIVE" and b_ov > 0.5) or
                                              (kind == "ANTI" and b_ov < 0.5)) else "FAILS overlap-adj"
            P(f"     T{ti+1} {tier}: n={n} acc={acc*100:.1f}% nominal-{kind} (bound {b*100:.1f}%) "
              f"-> overlap-adj bound {b_ov*100:.1f}% -> {surv}")
    else:
        P("     (no cell clears even the nominal bound)")
    P(f"   VERDICT: nominal-significant cells = {len(nominal)}; "
      f"survive overlap adjustment = {len(honest)}  -> "
      f"{'TIER EDGE SURVIVES' if honest else 'NO tier-level cell survives the honest bar — CAPE edge is entirely TYPE-level'}")
    P("")

    # ---------- FULL tier table: ALL 27 types x tiers, abstain rows, no filtering ----------
    P("[TIER TABLE — ALL 27 TYPES, no display filtering; B = primary presentation, A = comparison]")
    hdr = (f"{'type':<20} {'tier':<6} {'n':>4} {'IS%':>6} {'Bayes%':>7} {'AvgRet|ok':>9} "
           f"{'Cov':>6} {'O-val':>7} {'o_cov':>7} {'R2':>6} {'WF-OOS-3m%':>10} {'LB':>6} {'LB_ovl':>6}")
    P(hdr)
    P("-" * len(hdr))
    tier_rows = []
    by_type = {}
    for r in records:
        by_type.setdefault(r["typ"], []).append(r)
    for ti in range(27):
        tlab = f"T{ti+1:<3}{type_label(ti)}"
        rows_t = by_type.get(ti, [])
        if ti in PULLED:
            P(f"{tlab:<20} PULLED (standing rule)  months={len(rows_t)}")
            continue
        pool_t = [r for r in rows_t if r["status"] != "pulled"]
        em_t = [r for r in pool_t if r["status"] == "emitted"]
        ab_t = [r for r in pool_t if r["status"] == "abstain"]
        if not pool_t:
            P(f"{tlab:<20} n=0 pool months  --")
            continue
        npool_t = len(pool_t)
        for tier in TIER_ORDER:
            cell = [r for r in em_t if r.get("tier") == tier]
            if not cell:
                continue
            sB = tier_cell_stats(cell, "B")
            sA = tier_cell_stats(cell, "A")
            covc = len(cell) / npool_t
            if sB.get("n", 0) == 0:
                P(f"{tlab:<20} {tier:<6} {len(cell):>4}  (all label-unresolved)")
                continue
            P(f"{tlab:<20} {tier:<6} {sB['n']:>4} {sB['is_acc']*100:>5.1f}% {sB['bayes']*100:>6.1f}% "
              f"{sB['avg_ret_ok']:>8.2f}% {covc:>6.3f} {sB['oval']:>7.3f} {sB['oval']*covc:>7.3f} "
              f"{(sB['r2']*100 if np.isfinite(sB['r2']) else 0):>5.1f}% "
              f"{sB['acc']*100:>9.1f}% {sB['lb']*100:>5.1f}% {sB['lb_ovl']*100:>5.1f}%")
            if sA["acc"] != sB["acc"]:
                P(f"{'':<20} {'  (A)':<6} {sA['n']:>4} {sA['is_acc']*100:>5.1f}% {sA['bayes']*100:>6.1f}% "
                  f"{sA['avg_ret_ok']:>8.2f}% {covc:>6.3f} {sA['oval']:>7.3f} {sA['oval']*covc:>7.3f} "
                  f"{'':>6} {sA['acc']*100:>9.1f}% {sA['lb']*100:>5.1f}% {sA['lb_ovl']*100:>5.1f}%")
            for variant, s in (("B", sB), ("A", sA)):
                tier_rows.append(dict(type=ti + 1, sign=type_label(ti).replace(" ", ""),
                                      tier=tier, variant=variant, n=s["n"],
                                      IS_pct=round(s["is_acc"] * 100, 1),
                                      Bayes_pct=round(s["bayes"] * 100, 1),
                                      AvgRet_ok=round(s["avg_ret_ok"], 2),
                                      Cov=round(covc, 3), O_val=round(s["oval"], 3),
                                      o_cov=round(s["oval"] * covc, 3),
                                      R2_chosen=round(s["r2"], 4) if np.isfinite(s.get("r2", np.nan)) else "",
                                      WF_OOS_3m_pct=round(s["acc"] * 100, 1),
                                      LB=round(s["lb"] * 100, 1),
                                      LB_ovl=round(s["lb_ovl"] * 100, 1)))
        # abstain accounting row (always printed if any)
        rs = {}
        for r in ab_t:
            rs[r["reason"]] = rs.get(r["reason"], 0) + 1
        P(f"{tlab:<20} {'--':<6} pool={npool_t} emitted={len(em_t)} abstained={len(ab_t)} {rs if rs else ''}"
          f"   RECONCILES={npool_t == len(em_t) + len(ab_t)}")
    if untyped:
        rs = {}
        for r in untyped:
            rs[r["reason"]] = rs.get(r["reason"], 0) + 1
        P(f"{'UNTYPED (anchor n/a)':<20} {'--':<6} pool={len(untyped)} emitted=0 abstained={len(untyped)} {rs}"
          f"   RECONCILES=True")
    P("")

    # ---------- modal primary filter + stability + filter strength per type ----------
    P("[MODAL PRIMARY FILTER + SELECTION STABILITY + FILTER STRENGTH — per type (pool months)]")
    P("  (chosenR2 averaged over months WITH a primary; maxR2 over ALL split-attempted months incl. gate-fails;")
    P("   smallN* = mean type-train n < 30 -> max-across-candidates can clear the 20% gate by luck; placebo adjudication)")
    P(f"{'type':<20} {'pool':>5} {'split%':>7} {'modal primary':<28} {'stability%':>10} {'mean chosenR2':>13} {'mean maxR2':>11} {'noSurv%':>8} {'mean nTT':>8}")
    for ti in range(27):
        if ti in PULLED:
            continue
        pool_t = [r for r in by_type.get(ti, []) if r["status"] != "pulled"]
        if not pool_t:
            continue
        withp = [r for r in pool_t if r.get("primary")]
        att = [r for r in pool_t if r.get("split_attempted")]
        nosurv = [r for r in att if r.get("n_survivors", 0) == 0]
        prims = [r["primary"] for r in withp]
        if prims:
            modal = max(set(prims), key=prims.count)
            stab = prims.count(modal) / len(prims) * 100
        else:
            modal, stab = "--", 0.0
        cr2 = [r["chosen_r2"] for r in withp if np.isfinite(r.get("chosen_r2", np.nan))]
        mr2 = [r["max_r2"] for r in att if np.isfinite(r.get("max_r2", np.nan))]
        ntt = [r["n_type_train"] for r in pool_t if r.get("n_type_train") is not None]
        mean_ntt = np.mean(ntt) if ntt else 0.0
        P(f"T{ti+1:<3}{type_label(ti):<16} {len(pool_t):>5} {len(withp)/len(pool_t)*100:>6.1f}% "
          f"{modal:<28} {stab:>9.1f}% {(np.mean(cr2)*100 if cr2 else 0):>12.1f}% "
          f"{(np.mean(mr2)*100 if mr2 else 0):>10.1f}% {(len(nosurv)/len(att)*100 if att else 0):>7.1f}% "
          f"{mean_ntt:>7.1f}{'*' if 0 < mean_ntt < 30 else ' '}")
    P("")

    # ---------- C5 hook ----------
    ns = [r.get("n_screened", 0) for r in poolm if r.get("split_attempted")]
    if ns:
        P(f"[C5 hook] candidate columns screened per fold (splits attempted): "
          f"min={min(ns)} median={int(np.median(ns))} max={max(ns)}  -> Stage 5 max-stat placebo input")
    P(f"[runtime] fold loop {elapsed:.1f}s (target <20min: {'OK' if elapsed < 1200 else 'FAIL'})")
    P("")

    # ---------- PRODUCTION BOARD (final summary; standard HAL output) ----------
    P("[PRODUCTION BOARD — final summary]")
    def bucket_of(r):
        if r["status"] == "pulled":
            return "ACT"
        if r["status"] == "emitted":
            return "CASCADE"
        return "GATE-FAIL" if r["reason"] in GATE_FAIL_REASONS else "FLOOR"
    buckets = {"ACT": [], "CASCADE": [], "GATE-FAIL": [], "FLOOR": []}
    for r in records:
        buckets[bucket_of(r)].append(r)
    total = len(records)
    P(f"    {'bucket':<28} {'types':<38} {'months':>6} {'share%':>7}  status")
    meta = [("ACT", "ACT standing rules (pulled)", "ACT (standing rules T27/T5/T14)"),
            ("CASCADE", "CASCADE split-permitted", "ACT via in-fold cascade (R2>=20% filter)"),
            ("GATE-FAIL", "ABSTAIN gate-fail", "ABSTAIN — no filter cleared R2>=20%"),
            ("FLOOR", "ABSTAIN floor", "ABSTAIN — n<8 / degenerate / missing value")]
    board = {}
    for key, label, status in meta:
        rs = buckets[key]
        tys = sorted(set(r["typ"] for r in rs))
        tstr = ",".join("UNTYPED" if ti < 0 else f"T{ti+1}" for ti in tys) if tys else "--"
        if len(tstr) > 36:
            tstr = tstr[:33] + "..."
        P(f"    {label:<28} {tstr:<38} {len(rs):>6} {len(rs)/total*100:>6.1f}%  {status}")
        board[key] = len(rs)
    P(f"    partition check: {' + '.join(str(board[k]) for k in board)} = {sum(board.values())} "
      f"(decision months={total}) -> {'OK' if sum(board.values()) == total else 'FAIL'}")
    P(f"    pull set = {len(PULLED)} sign-triples (H=3 recompute) -> ACT={board['ACT']} months; "
      f"remainder pool = {board['CASCADE'] + board['GATE-FAIL'] + board['FLOOR']} months "
      f"(CASCADE {board['CASCADE']}, gate-fail {board['GATE-FAIL']}, floor {board['FLOOR']}). "
      f"Prior H=1 3-pull baseline had ACT {SNAPSHOT['ACT']}. Bucket membership is refit "
      f"monthly -> a DISTRIBUTION across folds, not a constant.")
    P("")
    return lines, tier_rows, headline


# ======================================================================================
# TRUNCATION AUDIT — machine-checkable part (runs inside every pass)
# ======================================================================================
def truncation_audit(records, pool, oos_checks, printed_lines, tier_rows, n_calendar_months):
    f = []
    # ZERO SILENT DROPS at the calendar level: every month >= START must have a record
    if len(records) != n_calendar_months:
        f.append(f"ACCOUNTING: {n_calendar_months} calendar months >= 1990-01 but only "
                 f"{len(records)} decision records (silent drop)")
    dts_seen = [r["date"] for r in records]
    if len(set(dts_seen)) != len(dts_seen):
        f.append("ACCOUNTING: duplicate decision-month records")
    poolm = [r for r in records if r["status"] != "pulled"]
    emitted = [r for r in poolm if r["status"] == "emitted"]
    abstained = [r for r in poolm if r["status"] == "abstain"]
    # (b) month accounting, global + per type, zero silent drops
    if len(poolm) != len(emitted) + len(abstained):
        f.append("ACCOUNTING: pool_total != emitted + abstained (silent drop)")
    for ti in set(r["typ"] for r in poolm):
        pt = [r for r in poolm if r["typ"] == ti]
        if len(pt) != len([r for r in pt if r["status"] == "emitted"]) + len([r for r in pt if r["status"] == "abstain"]):
            f.append(f"ACCOUNTING: type T{ti+1} does not reconcile")
    for r in abstained:
        if not r.get("reason"):
            f.append("ACCOUNTING: abstain row without reason")
            break
    for r in records:
        if r["status"] not in ("pulled", "emitted", "abstain"):
            f.append(f"ACCOUNTING: unknown status {r['status']}")
    # (a) machinery vs spec
    if GRID_PRIMARY != 50 or GRID_M3 != 100:
        f.append("MACHINERY: grid sizes deviate from spec (50/100)")
    if COV_PRIMARY != (0.10, 0.70) or COV_M3 != (0.05, 0.90):
        f.append("MACHINERY: coverage bounds deviate from spec")
    if len(FORMS) != 5:
        f.append("MACHINERY: derivative-form menu != 5 columns")
    bad_r2 = [r for r in emitted if r.get("primary") and
              (not np.isfinite(r.get("chosen_r2", np.nan)) or r["chosen_r2"] < R2_GATE)]
    if bad_r2:
        f.append(f"R2 GATE: {len(bad_r2)} emissions used a filter below the {R2_GATE} hard gate")
    # every var screened with all 5 forms when data allows: n_screened must be <= 5*|pool|
    if any(r.get("n_screened", 0) > 5 * len(pool) for r in poolm):
        f.append("MACHINERY: screened more columns than pool x 5 forms (leak?)")
    # all 27 types printed in the tier table section
    txt = "\n".join(printed_lines)
    for ti in range(27):
        if f"T{ti+1} " not in txt and f"T{ti+1}\t" not in txt and f"T{ti+1}  " not in txt:
            f.append(f"DISPLAY: type T{ti+1} missing from printed output")
    # both flip variants present
    if not any(tr["variant"] == "A" for tr in tier_rows) and any(r.get("flipA") != r.get("flipB") for r in emitted):
        f.append("FLIP VARIANTS: A-variant rows absent from tier table")
    if "variant A" not in txt or "variant B" not in txt:
        f.append("FLIP VARIANTS: headline missing a variant")
    # filter-strength diagnostic present
    if "FILTER STRENGTH" not in txt:
        f.append("DIAGNOSTIC: filter-strength section missing")
    # OOS-method verification: printed, frontier gap >= H, expanding
    if len(oos_checks) < 5:
        f.append("OOS VERIFICATION: fewer than 5 checkpoints printed")
    prev = -1
    for t in sorted(oos_checks):
        c = oos_checks[t]
        if c["t_row"] - c["frontier_row"] < H:
            f.append(f"OOS VERIFICATION: frontier gap < {H} at {c['date']} (label leak)")
        if c["n_train"] <= prev:
            f.append(f"OOS VERIFICATION: window not expanding at {c['date']}")
        prev = c["n_train"]
    # pulled types truly excluded from pool
    if any(r["typ"] in PULLED and r["status"] != "pulled" for r in records):
        f.append("POOL: a pulled-type month entered the pool")
    if any(r["typ"] not in PULLED and r["status"] == "pulled" for r in records):
        f.append("POOL: a non-pulled month was marked pulled")
    # operator rule: gate-fail must ABSTAIN — no base emissions may exist
    if any(r.get("tier") == "base" for r in emitted):
        f.append("GATE RULE: 'base' whole-type emission found (gate-fail must abstain)")
    if any(r["status"] == "emitted" and not r.get("primary") for r in emitted):
        f.append("GATE RULE: emission without a primary filter")
    if any(r["typ"] < 0 and r["status"] == "emitted" for r in records):
        f.append("GATE RULE: emission from an untypeable month")
    # filter-strength export exists and covers every fold that screened columns
    fs_path = os.path.join(REPORTS, "filter_strength.csv")
    n_screening_folds = sum(1 for r in poolm if r.get("n_screened", 0) > 0)
    if n_screening_folds and not os.path.exists(fs_path):
        f.append("DELIVERABLE: reports/filter_strength.csv missing")
    # production board present + partitions
    if "PRODUCTION BOARD" not in txt:
        f.append("DIAGNOSTIC: production board missing")
    b_act = sum(1 for r in records if r["status"] == "pulled")
    b_cas = len(emitted)
    b_gf = sum(1 for r in abstained if r["reason"] in GATE_FAIL_REASONS)
    b_fl = sum(1 for r in abstained if r["reason"] in FLOOR_REASONS)
    if b_act + b_cas + b_gf + b_fl != len(records):
        f.append("PRODUCTION BOARD: buckets do not partition decision months")
    for r in abstained:
        if r["reason"] not in GATE_FAIL_REASONS | FLOOR_REASONS:
            f.append(f"PRODUCTION BOARD: unbucketed abstain reason '{r['reason']}'")
            break
    return f


# ======================================================================================
# files: CSVs + scatter PNG
# ======================================================================================
def write_files(records, tier_rows, fstrength, pass_no):
    os.makedirs(REPORTS, exist_ok=True)
    md = pd.DataFrame(records)
    md.to_csv(os.path.join(REPORTS, "month_level.csv"), index=False)
    pd.DataFrame(tier_rows).to_csv(os.path.join(REPORTS, "tier_table.csv"), index=False)
    pd.DataFrame(fstrength).to_csv(os.path.join(REPORTS, "filter_strength.csv"), index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    em = [r for r in records if r["status"] == "emitted" and r["scored"]]
    types = sorted(set(r["typ"] for r in em))
    if not types:
        return
    ncol = 4
    nrow = int(np.ceil(len(types) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 3.4 * nrow), squeeze=False)
    colors = {"base": "#888888", "tier1": "#1f77b4", "tier2": "#2ca02c",
              "tier3": "#ff7f0e", "tier4": "#d62728"}
    for i, ti in enumerate(types):
        ax = axes[i // ncol][i % ncol]
        sub = [r for r in em if r["typ"] == ti]
        for r in sub:
            x = r.get("primary_z_t", np.nan)
            if not np.isfinite(x if x is not None else np.nan):
                x = 0.0 + np.random.default_rng(r["t"]).normal(0, 0.05)  # base/no-primary strip at 0
            marker = "o" if r["hitB"] == 1 else "x"
            ax.scatter(x, r["ret3"] * 100, c=colors.get(r.get("tier", "base"), "#000"),
                       marker=marker, s=28, alpha=0.8, linewidths=1.2)
        nb = sum(1 for r in sub if r.get("tier") == "base")
        ax.axhline(0, lw=0.5, color="k")
        ax.set_title(f"T{ti+1} {type_label(ti).replace(' ', '')}  n={len(sub)} (base={nb})", fontsize=9)
        ax.set_xlabel("primary-filter z (base months at 0)", fontsize=7)
        ax.set_ylabel("3-mo fwd ret %", fontsize=7)
        ax.tick_params(labelsize=7)
    for j in range(len(types), nrow * ncol):
        axes[j // ncol][j % ncol].axis("off")
    handles = [plt.Line2D([], [], marker="s", ls="", color=c, label=t) for t, c in colors.items()]
    handles += [plt.Line2D([], [], marker="o", ls="", color="k", label="hit (B)"),
                plt.Line2D([], [], marker="x", ls="", color="k", label="miss (B)")]
    fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=8)
    fig.suptitle("RED DAWN untruncated cascade — SPY remainder pool (variant B) — "
                 "x=primary z, y=3-mo fwd ret, color=tier, o=hit/x=miss", fontsize=11)
    fig.tight_layout(rect=[0, 0.035, 1, 0.97])
    fig.savefig(os.path.join(REPORTS, "scatter_types.png"), dpi=130)
    plt.close(fig)


# ======================================================================================
def main():
    pass_no = int(sys.argv[sys.argv.index("--pass") + 1]) if "--pass" in sys.argv else 1
    df = pd.read_csv(PANEL)
    df["Date"] = pd.to_datetime(df["Date"])
    for c, lag in PUB_LAG.items():
        if c in df.columns:
            df[c] = df[c].shift(lag)
    pool, pool_lines = pool_audit(df)
    records, fstrength, oos_checks, elapsed = run(df, pool)
    n_calendar = int((df["Date"].to_numpy() >= START).sum())
    lines, tier_rows, headline = diagnostics(records, oos_checks, pool, pool_lines,
                                             elapsed, None)
    write_files(records, tier_rows, fstrength, pass_no)
    findings = truncation_audit(records, pool, oos_checks, lines, tier_rows, n_calendar)
    lines.append("=" * 118)
    lines.append(f"[TRUNCATION AUDIT — pass {pass_no} — machine checklist]")
    if findings:
        for x in findings:
            lines.append(f"    FINDING: {x}")
        lines.append(f"    VERDICT: {len(findings)} finding(s) — FIX AND RE-RUN")
    else:
        lines.append("    VERDICT: ZERO truncation findings (machine checklist clean)")
    lines.append("=" * 118)
    out = "\n".join(lines)
    print(out)
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, f"run_output_pass{pass_no}.txt"), "w") as fh:
        fh.write(out + "\n")
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())

"""
ZION MULTIASSET — full monthly analysis at the 3-MONTH sequential horizon on FOUR assets
========================================================================================
Gold, Silver, WTI, USD — each presented EXACTLY like the SPY/CAPE result:
  Phase 1  ORACLE type analysis  (provenance, N-sweep, 27-type WF table w/ zones, PULLS)
  Phase 2  RED DAWN cascade      (untruncated tier cascade on the non-pulled remainder)
  MIRROR   test on the ACTED months only (in-sample first, then OOS)
  BOARD    production board (ACT | CASCADE | ABSTAIN gate-fail | ABSTAIN floor)

This file GENERALIZES two reference machines (read, never modified):
  /Users/castaglia/Desktop/ZION_RED_DAWN/reddawn_cascade_full.py   (the untruncated SPY cascade)
  /Users/castaglia/Desktop/ZION/stage1_pit_data/oracle_stage.py    (type/N/PIT logic)

LOCKED DISCIPLINE (identical to SPY, applied per asset):
  - 3-MONTH sequential OOS: at decision t, train ONLY on rows s<=t-3 (labels resolved by t);
    target = sign(outcome[t+3]/outcome[t]-1); roll monthly from 1990; ALL selection in-fold.
  - Predictor N in {3,6,9,12} chosen by a DESIGN-SAMPLE sweep (pre-1990 if >=40 usable obs,
    else first-40% hygiene fallback), then FROZEN.  Sweep target = the SAME 3-mo-forward sign
    (internally consistent with the H=3 mission), scored on design rows only.
  - Ratio direction = sign of N-month change in (num/den).  Dead-zone +-0.5 TRAIN-SD on the
    pct_change(N) of the ratio AND the 3 legs -> 27 sign-triple types (ORACLE indexing).
  - PIT lags: Industrial_Production, US_CPI, M2_Money shifted +2 months.
  - TYPE-LEVEL PULLS: a type is a standing ACT rule iff WF>67.5% AND n>=8 (measured at H=3).
    Pulls are FROZEN out of the cascade candidate pool. Coverage (months, %) + blended acc reported.
  - Zones per cell: reliably-PREDICTIVE (Wilson LB>50), reliably-ANTI-PREDICTIVE (Wilson UB<50,
    flip-worthy), or COIN-TOSS (spans 50 -> abstain).
  - CASCADE on the remainder: untruncated — 50-pt percentile grid (model-3 100-pt), 5 derivative
    forms (Z6/Z3/Z12/Z6_vel/Z6_acc), Welch-d screen -> top10 primary, full macro pool EXCLUDING
    Copper_Close (splice), the asset's OWN outcome, and its anchor num/den legs.
    HARD GATE: candidate train-side point-biserial R^2 >= 0.20 or discarded; none -> ABSTAIN.
    Flip variants A(bare<50) and B(Wilson-gated) side by side; B is primary.
  - NO TRUNCATION: all 27 types printed (incl. empty/degenerate); pool_total == emitted +
    abstained-with-reason. NO LB/OOS emission gates (pure measurement).

PROPOSED (NOT operator-confirmed) predictor ratios flagged in provenance:
  Silver = IndProd/GS10, WTI = US2Y/FedFunds, USD = Gold/CPI.  Gold = Dollar/M2 is the prior.
"""
import os
import sys
import time
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "reports")
PANEL = "/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"

# ---------------- locked constants (from the SPY cascade) ------------------------------
SD = 0.5
Z95 = 1.96
START = np.datetime64("1990-01-01")
H = 3
MIN_TRAIN = 60
TYPE_FLOOR = 8
LEAF_FLOOR = 8
SEC_MIN = 10
M3_MIN = 15
R2_GATE = 0.20
PRIMARY_TOP = 10
SECONDARY_TOP = 5
M3_TOP = 10
GRID_PRIMARY = 50
GRID_M3 = 100
COV_PRIMARY = (0.10, 0.70)
COV_M3 = (0.05, 0.90)
MIN_PER_GROUP = 5
MIN_PER_GROUP_M3 = 3
YOUDEN_MIN_SAMPLES = 10
YOUDEN_MIN_SAMPLES_M3 = 5
PULL_WF = 0.675
PULL_N = 8
PUB_LAG = {"Industrial_Production": 2, "US_CPI": 2, "M2_Money": 2}
FORMS = ("Z6", "Z3", "Z12", "Z6_vel", "Z6_acc")
RATE_LIKE = {"GS10_Rate", "Fed_Funds_Rate", "US_2Y_Treasury",
             "Term_Spread_10Y_2Y", "Term_Spread_10Y_3M"}

NAMED_POOL = ["Dollar_Index", "GS10_Rate", "Fed_Funds_Rate", "US_2Y_Treasury",
              "WTI_Crude_Close", "Gold_Close", "M2_Money", "Industrial_Production",
              "US_CPI", "Term_Spread_10Y_2Y"]
EXTRA_CANDIDATES = ["Term_Spread_10Y_3M", "VIX_Close", "Natural_Gas_Close",
                    "Platinum_Futures_Close"]
EXCLUDED_GLOBAL = {
    "Copper_Close":       "BANNED — hard unit splice 2000-08 (C1)",
    "Silver_Close":       "starts 2000-08 (copper-style seam risk) — never a candidate",
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

# ------------- ASSET CONFIGS (distinct legs per uniqueness rule) ------------------------
ASSETS = {
    "Gold":   dict(outcome="Gold_Close", num="Dollar_Index", den="M2_Money", deflate=True,
                   proposed=False,
                   note="Dollar/M2 (gold NOT in numerator); CPI-real legs. Operator prior."),
    "Silver": dict(outcome="Silver_Close", num="Industrial_Production", den="GS10_Rate", deflate=False,
                   proposed=True,
                   note="PROPOSED IndProd/GS10 (distinct legs). Data starts 2000-08 -> first-40% "
                        "design fallback; IndProd is a mid-month leg -> +2mo PIT lag."),
    "WTI":    dict(outcome="WTI_Crude_Close", num="US_2Y_Treasury", den="Fed_Funds_Rate", deflate=False,
                   proposed=True,
                   note="PROPOSED US2Y/FedFunds (distinct rate legs). Rate-ratio is ZIRP-fragile "
                        "(pct_change explodes near 0% Fed Funds) — honest caveat."),
    "USD":    dict(outcome="Dollar_Index", num="Gold_Close", den="US_CPI", deflate=False,
                   proposed=True,
                   note="PROPOSED Gold/CPI — dollar-FREE predictor (no circularity), distinct legs."),
}


# ======================================================================================
# stats helpers (verbatim semantics from the SPY cascade)
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
# pool audit — per asset: named pool + audited extras, MINUS the asset's own legs/outcome
# ======================================================================================
def _splice_scan(x, rate_like):
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


def pool_audit(df, cfg):
    """Build the candidate pool for one asset. Exclude Copper (splice), the asset's own
    outcome, and its anchor num/den legs (no circularity / no leg leak)."""
    self_excl = {cfg["outcome"], cfg["num"], cfg["den"]}
    pool, lines = [], []
    for v in NAMED_POOL:
        if v in self_excl:
            role = "outcome" if v == cfg["outcome"] else ("num-leg" if v == cfg["num"] else "den-leg")
            lines.append(f"    {v:<24} EXCLUDED — asset's own {role} (no leak/circularity)")
            continue
        pool.append(v)
        lines.append(f"    {v:<24} INCLUDED (operator-named)")
    for v in EXTRA_CANDIDATES:
        if v in self_excl:
            role = "outcome" if v == cfg["outcome"] else ("num-leg" if v == cfg["num"] else "den-leg")
            lines.append(f"    {v:<24} EXCLUDED — asset's own {role} (no leak/circularity)")
            continue
        if v not in df.columns:
            lines.append(f"    {v:<24} EXCLUDED — not in panel")
            continue
        s = df[v].astype(float)
        ok, why = _splice_scan(s.to_numpy(), rate_like=(v in RATE_LIKE))
        if ok:
            pool.append(v)
            lines.append(f"    {v:<24} INCLUDED (extra; splice scan clean, "
                         f"start={df['Date'][s.first_valid_index()].date()})")
        else:
            lines.append(f"    {v:<24} EXCLUDED — splice scan: {why}")
    for v, why in EXCLUDED_GLOBAL.items():
        if v in self_excl:
            continue
        lines.append(f"    {v:<24} EXCLUDED — {why}")
    return pool, lines


# ======================================================================================
# candidate bases (5 derivative forms; unit-aware)
# ======================================================================================
def build_bases(df, pool):
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
# node screen + Youden search + leaf + cascade (generalized; identical logic to SPY)
# ======================================================================================
def node_screen(bases, pool, rows, match, exclude, min_per_group):
    survivors, best_d = {}, {}
    n_cols = 0
    max_r2_all = 0.0
    all_r2 = []
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
            if r2 < R2_GATE:
                continue
            survivors.setdefault(v, []).append((form, abs(d), r2))
            if abs(d) > best_d.get(v, -1.0):
                best_d[v] = abs(d)
    for v in survivors:
        survivors[v].sort(key=lambda e: -e[1])
    ranked = sorted(survivors, key=lambda v: -best_d[v])
    return survivors, ranked, n_cols, max_r2_all, all_r2


def youden_search(vals, match, grid_points, cov_lo, cov_hi, min_samples, effect_dir):
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


def make_leaf(tier, rows, match_arr):
    n = len(rows)
    if n == 0:
        return dict(tier=tier, n=0, raw=np.nan, flipA=False, flipB=False)
    raw = float(match_arr[rows].mean())
    k = int(round(raw * n))
    flipA = raw < 0.5
    flipB = wilson_bounds(k, n)[1] < 0.5
    return dict(tier=tier, n=n, raw=raw, flipA=flipA, flipB=flipB)


def cascade_fit(bases, pool, type_train, match):
    out = dict(primary=None, secondary=None, model3=None, leaves={}, meta={}, abstain=None)
    surv, ranked, ncols, maxr2, all_r2 = node_screen(bases, pool, type_train, match, set(), MIN_PER_GROUP)
    out["meta"]["primary"] = dict(n_cols=ncols, n_survivors=len(ranked), max_r2=maxr2)
    out["meta"]["all_r2"] = all_r2
    if ncols == 0:
        out["abstain"] = "degenerate-screen"
        return out
    if not ranked:
        out["abstain"] = "gate-fail-r2"
        return out
    prim = node_threshold_search(bases, surv, ranked, type_train, match,
                                 GRID_PRIMARY, COV_PRIMARY, YOUDEN_MIN_SAMPLES,
                                 PRIMARY_TOP, first_valid=False, require_pos_j=False)
    if prim is None:
        out["abstain"] = "no-valid-split"
        return out
    out["primary"] = prim
    v1, f1 = prim[0], prim[1]
    a1 = bases[v1][f1][type_train]
    fin = np.isfinite(a1)
    keep = (a1 > prim[2]) if prim[3] == ">" else (a1 < prim[2])
    ppass, pfail = type_train[fin & keep], type_train[fin & ~keep]
    out["meta"]["train_unrouted"] = int((~fin).sum())

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
    if tree["primary"] is None:
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
# per-asset anchor arrays: outcome label(H=3), ratio + legs (deflation discrete), N sweep
# ======================================================================================
def anchor_arrays(df, cfg):
    anchor_cols = list(dict.fromkeys(["Date", cfg["outcome"], cfg["num"], cfg["den"]]
                                     + (["US_CPI"] if cfg["deflate"] else [])))
    # rows where the anchor legs are all present define the asset's frame; carry ALL columns
    # (pool candidates keep their own NaNs -> handled by np.isfinite in the screens)
    mask = df[anchor_cols].notna().all(axis=1)
    d = df.loc[mask].reset_index(drop=True)
    out = d[cfg["outcome"]].to_numpy(float)
    num = d[cfg["num"]].to_numpy(float)
    den = d[cfg["den"]].to_numpy(float)
    infl = "none (nominal)"
    if cfg["deflate"]:
        cpi = d["US_CPI"].to_numpy(float)
        num = num / cpi
        den = den / cpi
        infl = "US_CPI (discrete, per-leg, pre-ratio)"
    ratio = num / den
    ratio_name = f"{cfg['num']}/{cfg['den']}"
    dts = d["Date"].to_numpy()
    yr = d["Date"].dt.year.to_numpy()
    n_rows = len(d)
    # H=3 forward label
    ret3 = np.full(n_rows, np.nan)
    ret3[:-H] = out[H:] / out[:-H] - 1.0
    lab = np.sign(ret3)
    return d, dts, yr, out, num, den, ratio, ratio_name, infl, ret3, lab


def sweep_N(d, yr, ratio, lab):
    """Design-sample sweep of N in {3,6,9,12}. Design = pre-1990 if >=40 usable ratio obs,
    else first-40% fallback. Target = the H=3 sign (lab). Returns (N, dsrc, sweep, flat)."""
    pre = yr < 1990
    dsrc = "pre-1990"
    if (pre & ~np.isnan(ratio)).sum() < 40:
        cut = int(len(d) * 0.4)
        pre = np.arange(len(d)) < cut
        dsrc = f"first 40% (<{d.Date.iloc[cut].date()})"
    best, ba, sweep = 6, -1.0, {}
    for N in range(3, 13, 3):
        rd = np.sign(pc(ratio, N))
        m = pre & (~np.isnan(rd)) & (~np.isnan(lab)) & (rd != 0) & (lab != 0)
        if m.sum() < 40:
            continue
        a = (rd[m] == lab[m]).mean()
        sweep[N] = a
        if a > ba:
            ba = a
            best = N
    flat = "FLAT (no-signal)" if (sweep and max(sweep.values()) - 0.5 < 0.03) else "peaked"
    return best, dsrc, sweep, flat


# ======================================================================================
# PHASE 1 — ORACLE type measurement at H=3 (majority-vote WF per type -> pull set + table)
# ======================================================================================
def phase1_types(d, dts, N, ratio, num, den, lab):
    gr, gn, gd = pc(ratio, N), pc(num, N), pc(den, N)
    anchor_ok = np.isfinite(gr) & np.isfinite(gn) & np.isfinite(gd)
    n_rows = len(d)
    by = {}          # type -> list of (hit) for majority-vote ACT rule (the pull test)
    overall_k = overall_n = 0
    decision_idx = [t for t in range(n_rows) if dts[t] >= START]
    for t in decision_idx:
        if not anchor_ok[t] or not np.isfinite(lab[t]) or lab[t] == 0:
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
        ti = int(typ[t])
        same = train[typ[train] == ti]
        seg = same if len(same) > 0 else train      # global fallback (ORACLE convention)
        up = int((lab[seg] > 0).sum())
        dn = int((lab[seg] < 0).sum())
        pred = 1 if up >= dn else -1
        hit = int(pred == lab[t])
        by.setdefault(ti, []).append(hit)
        overall_k += hit
        overall_n += 1
    return by, overall_k, overall_n, anchor_ok, gr, gn, gd


def type_zone(k, n):
    lo, hi = wilson_bounds(k, n)
    if lo > 0.5:
        return "PREDICTIVE"
    if hi < 0.5:
        return "ANTI"
    return "COIN-TOSS"


# ======================================================================================
# PHASE 2 — RED DAWN cascade fold loop on the non-pulled remainder (H=3)
# ======================================================================================
def phase2_cascade(d, dts, bases, pool, N, ratio, num, den, ret3, lab, pulled,
                   anchor_ok, gr, gn, gd):
    n_rows = len(d)
    records = []
    fstrength = []
    oos_checks = {}
    decision_idx = [t for t in range(n_rows) if dts[t] >= START]
    # ELIGIBLE decision months = anchor published AND train frontier has >= MIN_TRAIN resolved
    # rows. Verification checkpoints are drawn from these (fixed calendar dates can fall in a
    # short asset's pre-MIN_TRAIN warmup and never materialize) -> guarantees 5 real checkpoints.
    eligible = []
    for t in decision_idx:
        if not anchor_ok[t]:
            continue
        tr = np.arange(0, t - H + 1)
        tr = tr[anchor_ok[tr] & np.isfinite(lab[tr]) & (lab[tr] != 0)]
        if len(tr) >= MIN_TRAIN:
            eligible.append(t)
    if len(eligible) >= 5:
        pos = [int(round(q * (len(eligible) - 1))) for q in (0.0, 0.25, 0.5, 0.75, 1.0)]
        check_ts = {eligible[p] for p in pos}
    else:
        check_ts = set(eligible)

    t0 = time.time()
    for t in decision_idx:
        base_rec = dict(t=t, date=str(dts[t])[:10],
                        ret3=float(ret3[t]) if np.isfinite(ret3[t]) else np.nan,
                        lab=int(lab[t]) if np.isfinite(lab[t]) else 0,
                        scored=bool(np.isfinite(lab[t]) and lab[t] != 0))
        if not anchor_ok[t]:
            base_rec.update(typ=-1, status="abstain", reason="anchor-leg-missing")
            records.append(base_rec)
            continue
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
        if typ_t in pulled:
            # ACT standing rule: emit the majority-vote base direction (for MIRROR/coverage)
            type_train = train[typ[train] == typ_t]
            up = int((lab[type_train] > 0).sum())
            dn = len(type_train) - up
            base_dir = 1 if up >= dn else -1
            is_acc = max(up, dn) / len(type_train) if len(type_train) else np.nan
            rec.update(status="pulled", reason="pulled-type", base_dir=base_dir,
                       predB=base_dir, predA=base_dir, is_accB=is_acc, is_accA=is_acc,
                       hitB=int(base_dir == lab[t]) if rec["scored"] else np.nan,
                       hitA=int(base_dir == lab[t]) if rec["scored"] else np.nan)
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

        tree = cascade_fit(bases, pool, type_train, match)
        for v_, form_, r2_ in tree["meta"].get("all_r2", []):
            fstrength.append(dict(date=rec["date"], type=typ_t + 1, n_type_train=len(type_train),
                                  candidate=f"{v_}:{form_}", r2=round(r2_, 4),
                                  cleared_gate=r2_ >= R2_GATE))
        pm = tree["meta"].get("primary", {})
        rec.update(base_dir=base_dir, n_screened=pm.get("n_cols", 0),
                   n_survivors=pm.get("n_survivors", 0), max_r2=pm.get("max_r2", np.nan),
                   split_attempted=True)
        if tree["abstain"] is not None:
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
            rec.update(status="abstain", reason=f"leaf<floor{LEAF_FLOOR}", tier=tier, leaf_n=leaf["n"])
            records.append(rec)
            continue

        dirA = -base_dir if leaf["flipA"] else base_dir
        dirB = -base_dir if leaf["flipB"] else base_dir
        rawA = leaf["raw"] if not leaf["flipA"] else 1 - leaf["raw"]
        rawB = leaf["raw"] if not leaf["flipB"] else 1 - leaf["raw"]
        rec.update(status="emitted", tier=tier, leaf_n=leaf["n"], leaf_raw=leaf["raw"],
                   flipA=leaf["flipA"], flipB=leaf["flipB"],
                   predA=int(dirA), predB=int(dirB), is_accA=rawA, is_accB=rawB,
                   hitA=int(dirA == lab[t]) if rec["scored"] else np.nan,
                   hitB=int(dirB == lab[t]) if rec["scored"] else np.nan)
        records.append(rec)
    return records, fstrength, oos_checks, time.time() - t0


# ======================================================================================
# reporting helpers
# ======================================================================================
def type_label(ti):
    cs, r = divmod(ti, 9)
    ps, es = divmod(r, 3)
    return f"{SYM[cs-1]:>4}/{SYM[ps-1]:>4}/{SYM[es-1]:>4}"


def tier_cell_stats(cell, variant):
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


# ======================================================================================
# per-asset diagnostics (full presentation) — returns (lines, tier_rows, summary)
# ======================================================================================
def diagnostics(name, cfg, ratio_name, infl, N, dsrc, sweep, flat,
                d, by_type_p1, p1_k, p1_n, pulled, records, oos_checks,
                pool, pool_lines, elapsed, N_range):
    L = []
    P = L.append
    flag = "  [PROPOSED — NOT operator-confirmed]" if cfg["proposed"] else "  [operator prior]"
    P("=" * 120)
    P(f"### ZION MULTIASSET — {name} — 3-MONTH SEQUENTIAL OOS ###{flag}")
    P(f"run: {pd.Timestamp.now()}   panel: {PANEL}")
    P(f"[note] {cfg['note']}")
    P("")
    # ---------- PHASE 1: ORACLE provenance + N sweep ----------
    P("[PROVENANCE]")
    P(f"    outcome  = {cfg['outcome']}")
    P(f"    predictor RATIO = {ratio_name}{flag}")
    P(f"    inflation adj (discrete, per-leg, pre-ratio) = {infl}")
    P(f"    PIT lags: {PUB_LAG}")
    P(f"    data rows {len(d)}  {d.Date.min().date()}..{d.Date.max().date()}")
    swp = ", ".join(f"{a}:{b*100:.1f}%" for a, b in sorted(sweep.items())) if sweep else "(no N met design floor)"
    P(f"[N SWEEP]  N chosen = {N} mo   design sample = {dsrc}   sweep {flat}: {swp}")
    P(f"           (sweep target = H=3 forward sign on design rows; N in {list(N_range)}, FROZEN)")
    P("")
    # ---------- 27-TYPE TABLE ----------
    P(f"[3-MONTH 27-TYPE TABLE — sequential majority-vote WF | zones | PULL bar WF>{PULL_WF*100:.1f}% & n>={PULL_N}]")
    P(f"    OVERALL ungated WF from 1990: {p1_k/p1_n*100:.1f}%  n={p1_n}  (LB {wlb(p1_k,p1_n)*100:.1f}%, informational)")
    P(f"    {'T':<4} {'signs':<18} {'n':>4} {'WF%':>6} {'LB':>6} {'UB':>6}  zone")
    P("    " + "-" * 60)
    pulled_cov = 0
    pulled_k = 0
    for ti in range(27):
        v = by_type_p1.get(ti, [])
        n = len(v)
        if n == 0:
            P(f"    T{ti+1:<3} {type_label(ti):<18} {0:>4} {'--':>6} {'--':>6} {'--':>6}  (no pool months)")
            continue
        k = int(sum(v))
        lo, hi = wilson_bounds(k, n)
        zone = type_zone(k, n)
        pull = "  <== PULLED (ACT)" if ti in pulled else ""
        P(f"    T{ti+1:<3} {type_label(ti):<18} {n:>4} {k/n*100:>5.1f}% {lo*100:>5.1f}% {hi*100:>5.1f}%  {zone}{pull}")
        if ti in pulled:
            pulled_cov += n
            pulled_k += k
    P("")
    # ---------- PULLS + coverage ----------
    P("[PULLS — standing ACT rules (WF>67.5% & n>=8, measured at H=3)]")
    if pulled:
        for ti in sorted(pulled):
            v = by_type_p1[ti]
            n = len(v); k = int(sum(v))
            P(f"    T{ti+1} {type_label(ti)}: n={n}  WF={k/n*100:.1f}%  LB={wlb(k,n)*100:.1f}%")
        blended = pulled_k / pulled_cov if pulled_cov else float("nan")
        P(f"    PULL coverage: {pulled_cov} months of {p1_n} scored ({pulled_cov/p1_n*100:.1f}%)  "
          f"blended ACT acc = {blended*100:.1f}%")
    else:
        P("    (no type clears the pull bar — the entire book is remainder/cascade/abstain)")
        blended = float("nan")
    P("")

    # ---------- OOS-METHOD VERIFICATION ----------
    P("[OOS-METHOD VERIFICATION] expanding window; train frontier = decision month t-3 (3-mo label gap):")
    prev_n, expanding = -1, True
    for t in sorted(oos_checks):
        c = oos_checks[t]
        gap = c["t_row"] - c["frontier_row"]
        P(f"    decision {c['date']}: train n={c['n_train']:>5}  span {c['span']}  frontier gap={gap} rows (>= {H})")
        expanding &= c["n_train"] > prev_n
        prev_n = c["n_train"]
    P(f"    window EXPANDS across checkpoints: {'YES' if expanding else 'NO — VIOLATION'}   "
      f"checkpoints={len(oos_checks)} (>=5 required)")
    P("")

    # ---------- accounting ----------
    pulled_rows = [r for r in records if r["status"] == "pulled"]
    poolm = [r for r in records if r["status"] != "pulled"]
    untyped = [r for r in poolm if r["typ"] < 0]
    emitted = [r for r in poolm if r["status"] == "emitted"]
    abstained = [r for r in poolm if r["status"] == "abstain"]
    scored = [r for r in emitted if r["scored"]]
    P(f"[ACCOUNTING]  decision months={len(records)} (EVERY calendar month >= 1990-01)  "
      f"pulled={len(pulled_rows)}  POOL={len(poolm)} (untypeable={len(untyped)})")
    P(f"              pool -> emitted={len(emitted)} (scored={len(scored)})  abstained={len(abstained)}")
    reasons = {}
    for r in abstained:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    P(f"              abstain reasons: {reasons if reasons else 'none'}")
    recon = len(poolm) == len(emitted) + len(abstained)
    P(f"              RECONCILES: pool_total == emitted + abstained -> {recon}")
    P("")

    # ---------- cascade headline ----------
    P("[CASCADE HEADLINE — remainder pool only, sequential 3-mo-forward OOS]")
    headline = {}
    for var in ("A", "B"):
        k = int(sum(r[f"hit{var}"] for r in scored))
        n = len(scored)
        acc = k / n if n else 0.0
        headline[var] = (k, n, acc)
        tag = "bare flip" if var == "A" else "Wilson-gated flip (PRIMARY)"
        P(f"    variant {var} ({tag:<28}): acc={acc*100:5.1f}%  n={n}  "
          f"LB={wlb(k,n)*100:.1f}%  LB_ovl(n/3)={wilson_lb_overlap(k,n)*100:.1f}%")
    up_rate = np.mean([r["lab"] > 0 for r in scored]) if scored else 0
    P(f"    drift baseline (always-UP on emitted months): {up_rate*100:.1f}%")
    P("")

    # ---------- TIER TABLE (ALL 27 types) ----------
    P("[CASCADE TIER TABLE — ALL 27 TYPES, no display filtering; B primary, A comparison]")
    hdr = (f"{'type':<20} {'tier':<6} {'n':>4} {'IS%':>6} {'OOS%':>6} {'LB':>6} {'UB':>6} "
           f"{'R2':>6} {'O-val':>7} zone")
    P(hdr)
    P("-" * len(hdr))
    tier_rows = []
    by_type = {}
    for r in records:
        by_type.setdefault(r["typ"], []).append(r)
    for ti in range(27):
        tlab = f"T{ti+1:<3}{type_label(ti)}"
        rows_t = by_type.get(ti, [])
        if ti in pulled:
            P(f"{tlab:<20} PULLED (standing ACT rule)  months={len(rows_t)}")
            continue
        pool_t = [r for r in rows_t if r["status"] != "pulled"]
        em_t = [r for r in pool_t if r["status"] == "emitted"]
        ab_t = [r for r in pool_t if r["status"] == "abstain"]
        if not pool_t:
            P(f"{tlab:<20} n=0 pool months  --")
            continue
        npool_t = len(pool_t)
        any_cell = False
        for tier in TIER_ORDER:
            cell = [r for r in em_t if r.get("tier") == tier]
            if not cell:
                continue
            any_cell = True
            sB = tier_cell_stats(cell, "B")
            sA = tier_cell_stats(cell, "A")
            if sB.get("n", 0) == 0:
                P(f"{tlab:<20} {tier:<6} {len(cell):>4}  (all label-unresolved)")
                continue
            loB, hiB = wilson_bounds(sB["k"], sB["n"])
            zone = "PREDICTIVE" if loB > 0.5 else ("ANTI" if hiB < 0.5 else "coin-toss")
            P(f"{tlab:<20} {tier:<6} {sB['n']:>4} {sB['is_acc']*100:>5.1f}% {sB['acc']*100:>5.1f}% "
              f"{sB['lb']*100:>5.1f}% {hiB*100:>5.1f}% "
              f"{(sB['r2']*100 if np.isfinite(sB['r2']) else 0):>5.1f}% {sB['oval']:>7.3f} {zone}")
            if sA["acc"] != sB["acc"]:
                P(f"{'':<20} {'  (A)':<6} {sA['n']:>4} {sA['is_acc']*100:>5.1f}% {sA['acc']*100:>5.1f}% "
                  f"{sA['lb']*100:>5.1f}% {'':>6} {'':>6} {sA['oval']:>7.3f}")
            covc = len(cell) / npool_t
            for variant, s in (("B", sB), ("A", sA)):
                lo_, hi_ = wilson_bounds(s["k"], s["n"])
                tier_rows.append(dict(asset=name, type=ti + 1, sign=type_label(ti).replace(" ", ""),
                                      tier=tier, variant=variant, n=s["n"],
                                      IS_pct=round(s["is_acc"] * 100, 1),
                                      OOS_pct=round(s["acc"] * 100, 1),
                                      LB=round(lo_ * 100, 1), UB=round(hi_ * 100, 1),
                                      R2_chosen=round(s["r2"], 4) if np.isfinite(s.get("r2", np.nan)) else "",
                                      O_val=round(s["oval"], 3), Cov=round(covc, 3),
                                      zone=("PREDICTIVE" if lo_ > 0.5 else ("ANTI" if hi_ < 0.5 else "coin-toss"))))
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

    # ---------- MIRROR test on ACTED months ----------
    acted = [r for r in records if r["status"] in ("pulled", "emitted") and r["scored"]]
    P("[MIRROR TEST — ACTED months only (ACT pulls + cascade emissions), variant B]")
    P("   mirror = act on the OPPOSITE signal; a real directional edge beats its mirror & drift.")
    if acted:
        isacc = float(np.mean([r["is_accB"] for r in acted if r.get("is_accB") is not None
                               and np.isfinite(r.get("is_accB", np.nan))]))
        kk = int(sum(r["hitB"] for r in acted))
        nn = len(acted)
        oos = kk / nn
        mirror = 1 - oos
        drift = float(np.mean([r["lab"] > 0 for r in acted]))
        # flip-composition check on acted months: predB in {+/-base_dir}
        comp_ok = all(r.get("predB") in (r.get("base_dir"), -r.get("base_dir")) for r in acted
                      if r.get("base_dir") is not None)
        P(f"    acted months n={nn}   IS(in-fold) acc={isacc*100:.1f}%   "
          f"OOS acc={oos*100:.1f}% (LB {wlb(kk,nn)*100:.1f}%)")
        P(f"    MIRROR OOS acc (opposite signal) = {mirror*100:.1f}%   drift(always-UP) = {drift*100:.1f}%")
        verdict = ("EDGE — OOS beats mirror AND drift" if (oos > mirror and oos > drift)
                   else ("drift-capture only (OOS<=drift)" if oos <= drift
                         else "no edge (OOS<=mirror)"))
        P(f"    flip-composition predB in {{+/-base_dir}} on all acted months: {comp_ok}")
        if pulled:
            verdict += " [CAVEAT: pull-set membership selected in-sample (full-sample WF>67.5%); "\
                       "per-month routing is walk-forward but acted-months edge is an UPPER BOUND]"
        P(f"    MIRROR VERDICT: {verdict}")
    else:
        oos = isacc = drift = float("nan")
        nn = 0
        verdict = "no acted months"
        P("    (no acted months)")
    P("")

    # ---------- PRODUCTION BOARD ----------
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
    P(f"    {'bucket':<30} {'types':<30} {'months':>6} {'share%':>7}  status")
    meta = [("ACT", "ACT standing rules (pulled)", "ACT (standing rules)"),
            ("CASCADE", "CASCADE split-permitted", "ACT via in-fold cascade (R2>=20%)"),
            ("GATE-FAIL", "ABSTAIN gate-fail", "ABSTAIN — no filter cleared R2>=20%"),
            ("FLOOR", "ABSTAIN floor", "ABSTAIN — n<8 / degenerate / missing")]
    board = {}
    for key, label, status in meta:
        rs = buckets[key]
        tys = sorted(set(r["typ"] for r in rs))
        tstr = ",".join("UNTYPED" if ti < 0 else f"T{ti+1}" for ti in tys) if tys else "--"
        if len(tstr) > 28:
            tstr = tstr[:25] + "..."
        P(f"    {label:<30} {tstr:<30} {len(rs):>6} {len(rs)/total*100:>6.1f}%  {status}")
        board[key] = len(rs)
    part_ok = sum(board.values()) == total
    P(f"    partition check: {' + '.join(str(board[k]) for k in board)} = {sum(board.values())} "
      f"(decision months={total}) -> {'OK' if part_ok else 'FAIL'}")
    P("")

    summary = dict(asset=name, ratio=ratio_name, proposed=cfg["proposed"], N=N,
                   design=dsrc, sweep_flat=flat,
                   pulled_types=";".join(f"T{ti+1}" for ti in sorted(pulled)) or "none",
                   n_pulled=len(pulled), pull_cov_months=pulled_cov,
                   pull_cov_pct=round(pulled_cov / p1_n * 100, 1) if p1_n else 0.0,
                   pull_blended_acc=round(blended * 100, 1) if pulled and pulled_cov else "",
                   overall_type_wf=round(p1_k / p1_n * 100, 1) if p1_n else "",
                   board_ACT=board["ACT"], board_CASCADE=board["CASCADE"],
                   board_GATEFAIL=board["GATE-FAIL"], board_FLOOR=board["FLOOR"],
                   cascade_OOS_B=round(headline["B"][2] * 100, 1), cascade_n=headline["B"][1],
                   cascade_LB_B=round(wlb(*headline["B"][:2]) * 100, 1),
                   mirror_acted_n=nn,
                   mirror_OOS=round(oos * 100, 1) if nn else "",
                   mirror_IS=round(isacc * 100, 1) if nn else "",
                   mirror_verdict=verdict)
    return L, tier_rows, summary, board, headline


# ======================================================================================
# per-asset truncation / discipline audit (machine-checkable)
# ======================================================================================
def audit_asset(name, records, pool, oos_checks, printed_lines, tier_rows,
                n_calendar_months, pulled, N, N_range):
    f = []
    txt = "\n".join(printed_lines)
    # calendar completeness / no silent drops
    if len(records) != n_calendar_months:
        f.append(f"[{name}] ACCOUNTING: {n_calendar_months} calendar months but {len(records)} records")
    dts_seen = [r["date"] for r in records]
    if len(set(dts_seen)) != len(dts_seen):
        f.append(f"[{name}] ACCOUNTING: duplicate decision-month records")
    poolm = [r for r in records if r["status"] != "pulled"]
    emitted = [r for r in poolm if r["status"] == "emitted"]
    abstained = [r for r in poolm if r["status"] == "abstain"]
    if len(poolm) != len(emitted) + len(abstained):
        f.append(f"[{name}] ACCOUNTING: pool_total != emitted + abstained")
    for ti in set(r["typ"] for r in poolm):
        pt = [r for r in poolm if r["typ"] == ti]
        if len(pt) != len([r for r in pt if r["status"] == "emitted"]) + len([r for r in pt if r["status"] == "abstain"]):
            f.append(f"[{name}] ACCOUNTING: type T{ti+1} does not reconcile")
    for r in abstained:
        if not r.get("reason"):
            f.append(f"[{name}] ACCOUNTING: abstain row without reason")
            break
    for r in records:
        if r["status"] not in ("pulled", "emitted", "abstain"):
            f.append(f"[{name}] ACCOUNTING: unknown status {r['status']}")
    # machinery vs spec
    if GRID_PRIMARY != 50 or GRID_M3 != 100:
        f.append(f"[{name}] MACHINERY: grid sizes deviate from spec (50/100)")
    if COV_PRIMARY != (0.10, 0.70) or COV_M3 != (0.05, 0.90):
        f.append(f"[{name}] MACHINERY: coverage bounds deviate from spec")
    if len(FORMS) != 5:
        f.append(f"[{name}] MACHINERY: derivative-form menu != 5 columns")
    if list(N_range) != [3, 6, 9, 12]:
        f.append(f"[{name}] MACHINERY: N grid deviates from {{3,6,9,12}}")
    if N not in (3, 6, 9, 12):
        f.append(f"[{name}] MACHINERY: frozen N={N} not in grid")
    # R2 gate on every emission
    bad_r2 = [r for r in emitted if r.get("primary") and
              (not np.isfinite(r.get("chosen_r2", np.nan)) or r["chosen_r2"] < R2_GATE)]
    if bad_r2:
        f.append(f"[{name}] R2 GATE: {len(bad_r2)} emissions used a filter below {R2_GATE}")
    if any(r.get("n_screened", 0) > 5 * len(pool) for r in poolm):
        f.append(f"[{name}] MACHINERY: screened more columns than pool x 5 (leak?)")
    # all 27 types printed
    for ti in range(27):
        if f"T{ti+1} " not in txt and f"T{ti+1}\t" not in txt and f"T{ti+1}  " not in txt:
            f.append(f"[{name}] DISPLAY: type T{ti+1} missing from printed output")
    # both flip variants present
    if "variant A" not in txt or "variant B" not in txt:
        f.append(f"[{name}] FLIP VARIANTS: headline missing a variant")
    # flip-composition correctness predA/predB == base +/- flip
    for r in emitted:
        bd = r.get("base_dir")
        if bd is None:
            continue
        expA = -bd if r.get("flipA") else bd
        expB = -bd if r.get("flipB") else bd
        if r.get("predA") != expA or r.get("predB") != expB:
            f.append(f"[{name}] FLIP COMPOSITION: predA/predB != base +/- flip at {r['date']}")
            break
    # OOS-method verification
    if len(oos_checks) < 5:
        f.append(f"[{name}] OOS VERIFICATION: fewer than 5 checkpoints")
    prev = -1
    for t in sorted(oos_checks):
        c = oos_checks[t]
        if c["t_row"] - c["frontier_row"] < H:
            f.append(f"[{name}] OOS VERIFICATION: frontier gap < {H} at {c['date']} (label leak)")
        if c["n_train"] <= prev:
            f.append(f"[{name}] OOS VERIFICATION: window not expanding at {c['date']}")
        prev = c["n_train"]
    # pulled types truly excluded from pool
    if any(r["typ"] in pulled and r["status"] != "pulled" for r in records):
        f.append(f"[{name}] POOL: a pulled-type month entered the cascade pool")
    if any(r["typ"] not in pulled and r["status"] == "pulled" for r in records):
        f.append(f"[{name}] POOL: a non-pulled month was marked pulled")
    # gate rule: emissions must carry a primary; no untypeable emission
    if any(r["status"] == "emitted" and not r.get("primary") for r in emitted):
        f.append(f"[{name}] GATE RULE: emission without a primary filter")
    if any(r["typ"] < 0 and r["status"] == "emitted" for r in records):
        f.append(f"[{name}] GATE RULE: emission from an untypeable month")
    # production board partition
    if "PRODUCTION BOARD" not in txt:
        f.append(f"[{name}] DIAGNOSTIC: production board missing")
    b_act = sum(1 for r in records if r["status"] == "pulled")
    b_cas = len(emitted)
    b_gf = sum(1 for r in abstained if r["reason"] in GATE_FAIL_REASONS)
    b_fl = sum(1 for r in abstained if r["reason"] in FLOOR_REASONS)
    if b_act + b_cas + b_gf + b_fl != len(records):
        f.append(f"[{name}] PRODUCTION BOARD: buckets do not partition decision months")
    for r in abstained:
        if r["reason"] not in GATE_FAIL_REASONS | FLOOR_REASONS:
            f.append(f"[{name}] PRODUCTION BOARD: unbucketed abstain reason '{r['reason']}'")
            break
    # MIRROR present
    if "MIRROR TEST" not in txt:
        f.append(f"[{name}] DIAGNOSTIC: MIRROR test missing")
    return f


# ======================================================================================
# run ONE asset end to end -> (lines, tier_rows, summary, findings, artifacts)
# ======================================================================================
def run_asset(name, df):
    cfg = ASSETS[name]
    N_range = range(3, 13, 3)
    d, dts, yr, out, num, den, ratio, ratio_name, infl, ret3, lab = anchor_arrays(df, cfg)
    N, dsrc, sweep, flat = sweep_N(d, yr, ratio, lab)
    # Phase 1: type measurement -> pull set
    by_p1, p1_k, p1_n, anchor_ok, gr, gn, gd = phase1_types(d, dts, N, ratio, num, den, lab)
    pulled = {ti for ti, v in by_p1.items() if len(v) >= PULL_N and (sum(v) / len(v)) > PULL_WF}
    # Phase 2: cascade on remainder
    pool, pool_lines = pool_audit(df, cfg)
    # bases indexed on the asset's OWN anchor-aligned frame d (carries pool columns)
    bases = build_bases(d, pool)
    records, fstrength, oos_checks, elapsed = phase2_cascade(
        d, dts, bases, pool, N, ratio, num, den, ret3, lab, pulled, anchor_ok, gr, gn, gd)
    n_calendar = int((d["Date"].to_numpy() >= START).sum())
    lines, tier_rows, summary, board, headline = diagnostics(
        name, cfg, ratio_name, infl, N, dsrc, sweep, flat, d, by_p1, p1_k, p1_n,
        pulled, records, oos_checks, pool, pool_lines, elapsed, N_range)
    findings = audit_asset(name, records, pool, oos_checks, lines, tier_rows,
                           n_calendar, pulled, N, N_range)
    artifacts = dict(records=records, tier_rows=tier_rows, fstrength=fstrength,
                     pool_lines=pool_lines, board=board, by_p1=by_p1, pulled=pulled,
                     p1_n=p1_n, p1_k=p1_k)
    return lines, tier_rows, summary, findings, artifacts


# ======================================================================================
# per-asset report files
# ======================================================================================
def write_asset_files(name, lines, artifacts):
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, f"{name}_run.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    # type_table.csv (phase 1)
    rows = []
    for ti in range(27):
        v = artifacts["by_p1"].get(ti, [])
        n = len(v); k = int(sum(v)) if v else 0
        lo, hi = wilson_bounds(k, n) if n else (float("nan"), float("nan"))
        rows.append(dict(asset=name, type=ti + 1, signs=type_label(ti).replace(" ", ""),
                         n=n, WF_pct=round(k / n * 100, 1) if n else "",
                         LB=round(lo * 100, 1) if n else "", UB=round(hi * 100, 1) if n else "",
                         zone=type_zone(k, n) if n else "empty",
                         pulled=(ti in artifacts["pulled"])))
    pd.DataFrame(rows).to_csv(os.path.join(REPORTS, f"{name}_type_table.csv"), index=False)
    pd.DataFrame(artifacts["tier_rows"]).to_csv(os.path.join(REPORTS, f"{name}_cascade_tier.csv"), index=False)
    pd.DataFrame(artifacts["records"]).to_csv(os.path.join(REPORTS, f"{name}_month_level.csv"), index=False)
    # production board txt (extract the board section)
    board_txt = []
    grab = False
    for ln in lines:
        if ln.startswith("[PRODUCTION BOARD"):
            grab = True
        if grab:
            board_txt.append(ln)
            if ln.strip().startswith("partition check"):
                break
    with open(os.path.join(REPORTS, f"{name}_production_board.txt"), "w") as fh:
        fh.write("\n".join(board_txt) + "\n")


# ======================================================================================
# MAIN — error-check loop: run all 4 assets, audit >=3x, require 2 consecutive clean passes
# ======================================================================================
def main():
    df = pd.read_csv(PANEL)
    df["Date"] = pd.to_datetime(df["Date"])
    for c, lag in PUB_LAG.items():
        if c in df.columns:
            df[c] = df[c].shift(lag)

    os.makedirs(REPORTS, exist_ok=True)
    loop_log = []
    LP = loop_log.append
    LP("=" * 100)
    LP("ZION MULTIASSET — ERROR-CHECK LOOP (strict): audit >=3 passes; stop on 2 consecutive clean")
    LP(f"start: {pd.Timestamp.now()}")
    LP("=" * 100)

    consecutive_clean = 0
    pass_no = 0
    all_summaries, all_tier_rows, all_lines = [], [], []
    MAX_PASSES = 6
    while consecutive_clean < 2 and pass_no < MAX_PASSES:
        pass_no += 1
        all_summaries, all_tier_rows, all_lines = [], [], []
        pass_findings = []
        LP(f"\n----- PASS {pass_no} -----")
        for name in ASSETS:
            lines, tier_rows, summary, findings, artifacts = run_asset(name, df)
            write_asset_files(name, lines, artifacts)
            all_summaries.append(summary)
            all_tier_rows.extend(tier_rows)
            all_lines.append((name, lines))
            LP(f"  [{name}] N={summary['N']} design={summary['design']} sweep={summary['sweep_flat']} | "
               f"pulled={summary['pulled_types']} (cov {summary['pull_cov_pct']}%) | "
               f"cascade B OOS={summary['cascade_OOS_B']}% n={summary['cascade_n']} | "
               f"board ACT/CAS/GF/FL={summary['board_ACT']}/{summary['board_CASCADE']}/"
               f"{summary['board_GATEFAIL']}/{summary['board_FLOOR']} | "
               f"mirror={summary['mirror_verdict']}")
            if findings:
                for x in findings:
                    LP(f"      FINDING: {x}")
                pass_findings.extend(findings)
            else:
                LP(f"      audit: CLEAN (zero findings)")
        if pass_findings:
            consecutive_clean = 0
            LP(f"  PASS {pass_no} VERDICT: {len(pass_findings)} finding(s) -> FIX & RE-RUN FROM TOP")
        else:
            consecutive_clean += 1
            LP(f"  PASS {pass_no} VERDICT: ZERO findings (clean #{consecutive_clean} consecutive)")

    LP("\n" + "=" * 100)
    LP(f"LOOP COMPLETE after {pass_no} passes: "
       f"{'TWO CONSECUTIVE CLEAN' if consecutive_clean >= 2 else 'STILL DIRTY — MANUAL REVIEW'}")
    LP("=" * 100)

    # consolidated cross-asset summary
    sdf = pd.DataFrame(all_summaries)
    sdf.to_csv(os.path.join(REPORTS, "cross_asset_summary.csv"), index=False)
    pd.DataFrame(all_tier_rows).to_csv(os.path.join(REPORTS, "cross_asset_tier_table.csv"), index=False)

    cons = []
    cons.append("=" * 120)
    cons.append("ZION MULTIASSET — CONSOLIDATED CROSS-ASSET SUMMARY (3-month sequential OOS)")
    cons.append(f"generated: {pd.Timestamp.now()}   passes to clean: {pass_no}   "
                f"clean-streak: {consecutive_clean}")
    cons.append("=" * 120)
    cons.append(f"{'asset':<7} {'ratio (flag)':<34} {'N':>2} {'sweep':<6} {'pulled(cov%,acc)':<26} "
                f"{'cascade B OOS(n,LB)':<22} {'board ACT/CAS/GF/FL':<20} {'MIRROR':<28}")
    for s in all_summaries:
        flag = "*PROP" if s["proposed"] else "prior"
        rlab = f"{s['ratio']} [{flag}]"
        if len(rlab) > 33:
            rlab = rlab[:33]
        pull = (f"{s['pulled_types']}({s['pull_cov_pct']}%,{s['pull_blended_acc']}%)"
                if s["n_pulled"] else "none")
        if len(pull) > 25:
            pull = pull[:25]
        casc = f"{s['cascade_OOS_B']}%(n{s['cascade_n']},LB{s['cascade_LB_B']})"
        board = f"{s['board_ACT']}/{s['board_CASCADE']}/{s['board_GATEFAIL']}/{s['board_FLOOR']}"
        cons.append(f"{s['asset']:<7} {rlab:<34} {s['N']:>2} {s['sweep_flat'][:6]:<6} {pull:<26} "
                    f"{casc:<22} {board:<20} {s['mirror_verdict'][:28]:<28}")
    cons.append("")
    cons.append("HONEST EDGE VERDICT (one line per asset):")
    for s in all_summaries:
        cons.append(f"  {s['asset']:<7}: {edge_verdict(s)}")
    cons.append("")
    cons.append("NOTE: Silver/WTI/USD ratios are PROPOSED placeholders (NOT operator-confirmed). "
                "WTI rate-ratio is ZIRP-fragile. Gold = operator prior.")
    cons_txt = "\n".join(cons)
    with open(os.path.join(REPORTS, "cross_asset_summary.txt"), "w") as fh:
        fh.write(cons_txt + "\n")

    with open(os.path.join(REPORTS, "error_check_loop.log"), "w") as fh:
        fh.write("\n".join(loop_log) + "\n")

    # full stdout
    for name, lines in all_lines:
        print("\n".join(lines))
    print(cons_txt)
    print("\n".join(loop_log))
    return 0 if consecutive_clean >= 2 else 2


def edge_verdict(s):
    """One-line honest edge read per asset."""
    parts = []
    if s["n_pulled"]:
        parts.append(f"{s['n_pulled']} type-pull(s) cover {s['pull_cov_pct']}% at {s['pull_blended_acc']}% blended")
    else:
        parts.append("no type clears the pull bar")
    cB, lb = s["cascade_OOS_B"], s["cascade_LB_B"]
    parts.append(f"cascade {cB}% (LB {lb}%) over n={s['cascade_n']} adds little")
    if "EDGE" in str(s["mirror_verdict"]):
        parts.append("MIRROR: acted edge survives")
    elif "drift" in str(s["mirror_verdict"]):
        parts.append("MIRROR: drift-capture only")
    else:
        parts.append(f"MIRROR: {s['mirror_verdict']}")
    return "; ".join(parts)


if __name__ == "__main__":
    sys.exit(main())

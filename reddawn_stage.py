"""
ZION RED DAWN — Stage 3 (DISCOVERY engine).  SCAFFOLD.

Extends ORACLE from ONE anchor ratio per asset to MULTIPLE predictors: within each anchor
27-type it re-fits the four-model cascade to find the hidden predictor-cell -> next-month
direction correspondences a single anchor cannot see.

DISCIPLINE (identical to stage1_pit_data/oracle_stage.py):
  - target = sign(next-month return)  [1-month horizon, inherited from ORACLE]
  - sequential ONE-STEP-AHEAD walk-forward from 1990; retrain all-past each month; reset
  - anchor 27-type grammar refit IN-FOLD on train-only z-params (KEPT)
  - four-model cascade refit IN-FOLD per type (KEPT tree shape + independent per-leaf flip)
  - MULTIPLE candidate predictors admitted IN-FOLD: fixed a-priori SET, but which candidate
    + which threshold is selected per fold on a PURGED INNER-VALIDATION slice (see spec §4)
  - two-gate admission: TRAIN-ADMIT Wilson-LB >= GATE(0.45); WINNER = max inner-VAL Wilson-LB
  - abstain-by-default (NO forced prediction); NO OOS gate at measurement (pure measurement)
  - NO house-wide / fixed-split selection anywhere (the contaminated family is torn out)

This file is a SCAFFOLD: the fold loop, the cascade partition, and the two-gate in-fold
admission are structurally complete and PIT-correct; a few leaf helpers are marked
`# TODO(impl)` where the numeric search body is intentionally stubbed. It consumes ORACLE's
config (anchor legs, frozen N, PUB_LAG, leg-uniqueness) so the top-level cells are ORACLE's.

See spec/ZION_RED_DAWN.md for the canonical ordered steps and the exact admission mechanism.
"""
import numpy as np
import pandas as pd

# ---- consume ORACLE: anchor config, frozen N, PIT lags, leg-uniqueness ----------------
import importlib.util, os
_ORACLE_PATH = os.path.join(os.path.dirname(__file__), "stage1_pit_data", "oracle_stage.py")
_spec = importlib.util.spec_from_file_location("oracle_stage", _ORACLE_PATH)
oracle = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(oracle)

PANEL = oracle.PANEL
PUB_LAG = oracle.PUB_LAG                 # C2 guard, inherited verbatim
ASSETS = oracle.ASSETS                   # anchor num/den/deflate/ratio_col per asset
wilson_lb = oracle.wlb                   # reuse ORACLE's Wilson lower bound
pc = oracle.pc                           # N-step pct_change

# ---- RED DAWN constants ---------------------------------------------------------------
SD = oracle.SD                           # +-0.5 train-SD dead zone (anchor grammar), KEPT
Z = oracle.Z
START = oracle.START                     # predictions begin 1990
MIN_TRAIN = oracle.MIN_TRAIN             # min usable train before first decision
GATE = 0.45                              # TRAIN-ADMIT Wilson-LB floor (roadmap Stage 3d)
MIN_N = 8                                # min train support per leaf / kept region
MIN_GROUP = 6                            # min per-group support in a Youden split
VAL_FRAC = 0.25                          # latest 25% of type-train = purged inner-validation
PURGE = 1                                # H=1 -> drop 1 boundary month between inner tr/val

# Cascade candidate pool = grounded macro universe. The SET is fixed a-priori (never
# data-selected). Per-asset exclusions (outcome, own price, anchor legs, banned series) are
# applied in candidate_pool().  Copper (2000-08 splice) and Term_Spread (zero-crossing as a
# ratio leg) are globally banned; Term_Spread MAY still appear as an absolute-point feature.
GROUNDED = ['Dollar_Index', 'M2_Money', 'Industrial_Production', 'GS10_Rate',
            'Fed_Funds_Rate', 'US_2Y_Treasury', 'WTI_Crude_Close', 'Gold_Close',
            'Term_Spread_10Y_2Y']
BANNED = {'Copper_Close'}                # hard splice; never a candidate
KSET = (3, 6, 9)                         # vel/acc periods (quarterly-aligned)
WSET = (60, 92, 120)                     # cyclic detrend windows


# ======================================================================================
# small helpers
# ======================================================================================
def flip_is_significant(raw_acc, n, z=Z):
    """KEPT: invert a leaf/base ONLY when Wilson one-sided upper bound < 0.5 (significant
    evidence of sub-chance), never on a bare raw_acc < 0.5."""
    if n <= 0:
        return False
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (raw_acc + z2 / (2 * n)) / denom
    half = z * np.sqrt(raw_acc * (1 - raw_acc) / n + z2 / (4 * n * n)) / denom
    return bool((centre + half) < 0.5)


def tern_train(x, tr_idx):
    """Ternary classify x against a +-SD dead zone using TRAIN-only mean/sd (PIT, scale-free).
    Returns int array in {-1,0,1}; NaN -> 0 (excluded upstream by validity mask)."""
    tv = x[tr_idx]; tv = tv[np.isfinite(tv)]
    if len(tv) < 30:
        return None
    mu = float(tv.mean()); sd = float(tv.std())
    if sd == 0 or not np.isfinite(sd):
        return None
    z = (x - mu) / sd
    out = np.zeros(len(x), int)
    out[z > SD] = 1
    out[z < -SD] = -1
    out[~np.isfinite(z)] = 0
    return out


def anchor_types(ratio, num, den, N, tr_idx):
    """KEPT anchor grammar: 27 types = ternary triple of (ratio chg, num chg, den chg) over
    the frozen N, +-0.5 train-SD dead zone. Identical to ORACLE; refit each fold on tr_idx.
    Returns typ array in 0..26 (or None if a leg can't be classified on this train slice)."""
    gr, gn, gd = pc(ratio, N), pc(num, N), pc(den, N)
    cc = tern_train(gr, tr_idx); cp = tern_train(gn, tr_idx); ce = tern_train(gd, tr_idx)
    if cc is None or cp is None or ce is None:
        return None
    return (cc + 1) * 9 + (cp + 1) * 3 + (ce + 1)


# ======================================================================================
# candidate features (the "multiple predictors"), all z-scored on inner-train only
# ======================================================================================
def candidate_pool(name, cfg):
    """Fixed a-priori candidate SET for an asset: grounded universe minus outcome, own
    price, anchor legs, and banned series. Enforces cascade/anchor leg-orthogonality."""
    banned = set(BANNED) | {cfg['outcome'], cfg['num'], cfg['den']}
    if cfg.get('ratio_col'):
        banned.add(cfg['ratio_col'])
    return [v for v in GROUNDED if v not in banned]


def build_candidate_features(df, pool, inner_tr_idx):
    """Expand each candidate var into its fixed transform menu, z-scored on inner-train.
    The MENU is fixed a-priori; only which entry wins is selected in-fold (spec §4.2).
    Returns {feature_name: np.ndarray}.  feature_name = 'VAR:tag'."""
    feats = {}
    for v in pool:
        if v not in df.columns:
            continue
        s = df[v].astype(float)
        cand = [(f'{v}:lvl{w}', s - s.rolling(w, min_periods=w // 2).mean()) for w in WSET]
        cand += [(f'{v}:vel{k}', s.diff(k)) for k in KSET]
        cand += [(f'{v}:acc{k}', s.diff(k).diff(k)) for k in KSET]
        for fn, ser in cand:
            arr = ser.to_numpy(float)
            z = _ztrain(arr, inner_tr_idx)
            if z is not None:
                feats[fn] = z
    return feats


def _ztrain(arr, tr_idx):
    tv = arr[tr_idx]; tv = tv[np.isfinite(tv)]
    if len(tv) < 30:
        return None
    mu = float(tv.mean()); sd = float(tv.std())
    if sd == 0 or not np.isfinite(sd):
        return None
    return (arr - mu) / sd


# ======================================================================================
# Youden-J threshold + flip on a candidate feature (KEPT: kept region = high-correct side)
# ======================================================================================
def youden_split(feat, correct, idx):
    """Search threshold theta and direction on rows `idx` to best separate correct(1) from
    incorrect(0). J = TPR - FPR; flip kept side if J<0 so kept region is high-correct.
    Returns (theta, direction in {'>','<'}, kept_idx) or None. (KEPT logic; in-fold.)"""
    a = feat[idx]; c = correct[idx]
    m = np.isfinite(a)
    a, c, sub = a[m], c[m], idx[m]
    pos = a[c == 1]; neg = a[c == 0]
    if len(pos) < MIN_GROUP or len(neg) < MIN_GROUP:
        return None
    best = None
    for theta in np.quantile(a, np.linspace(0.15, 0.85, 15)):
        for sd in ('>', '<'):
            keep = (a > theta) if sd == '>' else (a < theta)
            if keep.sum() < MIN_N:
                continue
            tpr = c[keep].mean() if keep.sum() else 0.0
            fpr = (1 - c[keep]).mean() if keep.sum() else 0.0
            J = tpr - fpr
            direction = sd if J >= 0 else ('<' if sd == '>' else '>')
            if best is None or abs(J) > abs(best[0]):
                best = (J, theta, direction)
    if best is None:
        return None
    _, theta, direction = best
    a_all = feat[idx]
    keep_all = (a_all > theta) if direction == '>' else (a_all < theta)
    kept_idx = idx[np.isfinite(a_all) & keep_all]
    return (float(theta), direction, kept_idx)


def apply_split(feat, theta, direction, idx):
    a = feat[idx]
    keep = (a > theta) if direction == '>' else (a < theta)
    keep &= np.isfinite(a)
    return idx[keep], idx[~keep & np.isfinite(a)]


# ======================================================================================
# in-fold candidate ranking — the two-gate admission mechanism (spec §4.4)
# ======================================================================================
def select_best_candidate(feats, correct, inner_tr, inner_val, exclude):
    """Choose the winning candidate for ONE cascade node, past-only:
      1. fit (theta, dir) on inner_tr via Youden J with flip;
      2. TRAIN-ADMIT: kept-region Wilson-LB on inner_tr must be >= GATE (else drop);
      3. WINNER: among admitted, maximize kept-region Wilson-LB on inner_val (ties -> larger
         inner_val support).
    Returns (feature_name, theta, direction) or None (=> node cannot split -> becomes a leaf).
    `exclude` = variable stems already spent upstream on this branch (leg-uniqueness)."""
    best = None  # (val_lb, val_n, fn, theta, direction)
    for fn, feat in feats.items():
        if fn.split(':', 1)[0] in exclude:
            continue
        sp = youden_split(feat, correct, inner_tr)
        if sp is None:
            continue
        theta, direction, kept_tr = sp
        if len(kept_tr) < MIN_N:
            continue
        k_tr = int(correct[kept_tr].sum()); n_tr = len(kept_tr)
        if wilson_lb(k_tr, n_tr) < GATE:                     # gate 1: train-admit floor
            continue
        kept_val, _ = apply_split(feat, theta, direction, inner_val)
        if len(kept_val) < MIN_GROUP:
            continue
        k_va = int(correct[kept_val].sum()); n_va = len(kept_val)
        val_lb = wilson_lb(k_va, n_va)                       # gate 2: winner = max inner-val LB
        key = (val_lb, n_va)
        if best is None or key > best[:2]:
            best = (val_lb, n_va, fn, theta, direction)
    if best is None:
        return None
    return (best[2], best[3], best[4])


# ======================================================================================
# leaf construction (KEPT: train-majority direction + independent Wilson flip + conviction)
# ======================================================================================
def make_leaf(leaf_id, nxt, full_train_idx):
    """Direction = full-train majority next-month sign; independent flip if train raw-acc of
    that majority rule is significantly < 0.5; conviction = full-train Wilson-LB. Refit on the
    FULL train pool (inner_tr U inner_val), per spec §4.5."""
    idx = full_train_idx[np.isfinite(nxt[full_train_idx]) & (nxt[full_train_idx] != 0)]
    n = len(idx)
    if n < MIN_N:
        return dict(id=leaf_id, direction=0, conv=0.0, n=n, insufficient=True)
    up = int((nxt[idx] > 0).sum()); dn = int((nxt[idx] < 0).sum())
    direction = 1 if up >= dn else -1
    raw_acc = max(up, dn) / n
    flipped = flip_is_significant(raw_acc, n)
    if flipped:
        direction = -direction
    k = int((np.sign(nxt[idx]) == direction).sum())
    conv = wilson_lb(k, n)
    return dict(id=leaf_id, direction=direction, conv=conv, n=n,
                flipped=flipped, insufficient=False)


# ======================================================================================
# THE FOUR-MODEL CASCADE — re-fit IN-FOLD per type (KEPT tree shape; spec §3)
# ======================================================================================
def cascade_fit(type_train, nxt, feats, base_flip):
    """Recursively partition a type's TRAIN months into 4 leaf-models via three splits, each
    chosen by the two-gate in-fold mechanism. Returns a routable tree:
        {'primary': (fn,theta,dir) | None, 'secondary': ..., 'model3': ...,
         'leaves': {'model1':leaf, ...}}
    `type_train` = train rows of the current anchor type (full train pool, this fold).
    `base_flip`  = whether the type's base direction was flipped (KEPT; affects `correct`).
    `correct` = anchor-rule-right on train (1/0), used to grow the tree toward high-correct."""
    # correctness target for tree GROWTH (KEPT: split toward months the base rule gets right)
    base_dir = _majority_dir(nxt, type_train, base_flip)
    correct = (np.sign(nxt) == base_dir).astype(float)

    inner_tr, inner_val = purged_inner_split(type_train)
    tree = dict(primary=None, secondary=None, model3=None, leaves={})

    # ---- PRIMARY split on the whole type ----
    prim = select_best_candidate(feats, correct, inner_tr, inner_val, exclude=set())
    if prim is None:
        # no admissible split -> single leaf covering the whole type
        tree['leaves']['model2'] = make_leaf('model2', nxt, type_train)
        return tree
    tree['primary'] = prim
    fn, theta, direction = prim
    ppass, pfail = apply_split(feats[fn], theta, direction, type_train)
    prim_stem = fn.split(':', 1)[0]

    # ---- SECONDARY split within Primary_Pass -> model1 / model2 ----
    itr2, iva2 = purged_inner_split(ppass)
    sec = select_best_candidate(feats, correct, itr2, iva2, exclude={prim_stem})
    if sec is not None:
        tree['secondary'] = sec
        sfn, sth, sdir = sec
        m1_idx, m2_idx = apply_split(feats[sfn], sth, sdir, ppass)
        tree['leaves']['model1'] = make_leaf('model1', nxt, m1_idx)
        tree['leaves']['model2'] = make_leaf('model2', nxt, m2_idx)
    else:
        tree['leaves']['model2'] = make_leaf('model2', nxt, ppass)   # whole Pass subset

    # ---- MODEL3 split within Primary_Fail (INDEPENDENT flip on the fail subgroup) -------
    if len(pfail) >= MIN_N:
        fail_flip = flip_is_significant(_raw_acc(nxt, pfail), len(pfail))  # independent (KEPT)
        fail_dir = _majority_dir(nxt, pfail, fail_flip)
        correct_fail = (np.sign(nxt) == fail_dir).astype(float)
        itr3, iva3 = purged_inner_split(pfail)
        m3 = select_best_candidate({k: v for k, v in feats.items()
                                    if k.split(':', 1)[0] != prim_stem},
                                   correct_fail, itr3, iva3, exclude={prim_stem})
        if m3 is not None:
            tree['model3'] = m3
            m3fn, m3th, m3dir = m3
            m3_idx, m4_idx = apply_split(feats[m3fn], m3th, m3dir, pfail)
            tree['leaves']['model3'] = make_leaf('model3', nxt, m3_idx)
            tree['leaves']['model4'] = make_leaf('model4', nxt, m4_idx)
        else:
            tree['leaves']['model4'] = make_leaf('model4', nxt, pfail)  # residual
    return tree


def route(tree, feats, t):
    """Route decision row t through the fitted tree to exactly one leaf. Returns the leaf dict
    (with direction + conviction) or None if the tree can't place t (=> abstain)."""
    def side(split):
        fn, theta, direction = split
        v = feats[fn][t]
        if not np.isfinite(v):
            return None
        return (v > theta) if direction == '>' else (v < theta)

    if tree['primary'] is None:
        return tree['leaves'].get('model2')
    p = side(tree['primary'])
    if p is None:
        return None
    if p:  # Primary_Pass branch
        if tree['secondary'] is not None:
            s = side(tree['secondary'])
            if s is None:
                return None
            return tree['leaves'].get('model1' if s else 'model2')
        return tree['leaves'].get('model2')
    else:  # Primary_Fail branch
        if tree['model3'] is not None:
            m = side(tree['model3'])
            if m is None:
                return None
            return tree['leaves'].get('model3' if m else 'model4')
        return tree['leaves'].get('model4')


# ---- tree-growth helpers -------------------------------------------------------------
def _majority_dir(nxt, idx, flip):
    v = nxt[idx]; v = v[np.isfinite(v) & (v != 0)]
    if len(v) == 0:
        return 1
    d = 1 if (v > 0).sum() >= (v < 0).sum() else -1
    return -d if flip else d


def _raw_acc(nxt, idx):
    v = nxt[idx]; v = v[np.isfinite(v) & (v != 0)]
    if len(v) == 0:
        return 0.5
    d = 1 if (v > 0).sum() >= (v < 0).sum() else -1
    return max((v > 0).mean(), (v < 0).mean())


def purged_inner_split(type_train):
    """Split a (time-ordered) index into earlier inner-train and latest inner-val, dropping
    PURGE boundary months so no inner-val label leaks into inner-train (spec §4.1). Both ≤ t."""
    idx = np.sort(np.asarray(type_train))
    n = len(idx)
    if n < 2 * MIN_N:
        return idx, idx[:0]                      # too small: val empty -> select_best falls through
    cut = int(round(n * (1 - VAL_FRAC)))
    inner_tr = idx[:max(cut - PURGE, 0)]
    inner_val = idx[cut:]
    return inner_tr, inner_val


# ======================================================================================
# THE FOLD LOOP — sequential one-step-ahead (mirrors oracle_stage.run; spec §5)
# ======================================================================================
def run_asset(name, df):
    cfg = ASSETS[name]
    pool = candidate_pool(name, cfg)

    # assemble anchor legs + outcome (discrete CPI-real per ORACLE), and next-month target
    cols = list(dict.fromkeys(['Date', cfg['outcome'], cfg['num'], cfg['den']]
                + ([cfg['ratio_col']] if cfg.get('ratio_col') else [])
                + (['US_CPI'] if cfg['deflate'] else []) + pool))
    cols = [c for c in cols if c in df.columns]
    d = df[cols].dropna(subset=['Date', cfg['outcome'], cfg['num'], cfg['den']]).reset_index(drop=True)
    if len(d) < MIN_TRAIN + 24:
        print(f"[{name}] INSUFFICIENT DATA ({len(d)} rows) — BLOCK")
        return

    out = d[cfg['outcome']].to_numpy(float)
    num = d[cfg['num']].to_numpy(float); den = d[cfg['den']].to_numpy(float)
    if cfg['deflate']:
        cpi = d['US_CPI'].to_numpy(float); num = num / cpi; den = den / cpi
    ratio = d[cfg['ratio_col']].to_numpy(float) if cfg.get('ratio_col') else num / den
    nxt = np.sign(np.concatenate([out[1:] / out[:-1] - 1, [np.nan]]))     # next-month direction
    dts = d['Date'].to_numpy()

    N = frozen_N(name, d, ratio, nxt)                                     # from ORACLE pre-1990 sweep
    records = []                                                          # OOS stream
    for t in range(len(d)):
        if dts[t] < START or not np.isfinite(nxt[t]) or nxt[t] == 0:
            continue
        train = np.arange(0, t)                                          # all-past, PIT (as ORACLE)
        train = train[np.isfinite(nxt[train]) & (nxt[train] != 0)]
        if len(train) < MIN_TRAIN:
            continue

        typ = anchor_types(ratio, num, den, N, train)                    # KEPT grammar, refit fold
        if typ is None:
            continue
        typ_t = typ[t]
        type_train = train[typ[train] == typ_t]
        if len(type_train) < MIN_N:
            records.append(dict(t=t, typ=int(typ_t), acted=False, reason='thin-type'))
            continue

        base_flip = flip_is_significant(_raw_acc(nxt, type_train), len(type_train))
        inner_tr_for_feats, _ = purged_inner_split(type_train)
        feats = build_candidate_features(d, pool, inner_tr_for_feats)    # z on inner-train only
        tree = cascade_fit(type_train, nxt, feats, base_flip)            # four-model, in-fold
        leaf = route(tree, feats, t)

        if leaf is None or leaf.get('insufficient') or leaf['direction'] == 0 \
                or leaf['conv'] < GATE:                                  # emit iff leaf clears floor
            records.append(dict(t=t, typ=int(typ_t), acted=False, reason='abstain'))
            continue
        records.append(dict(t=t, typ=int(typ_t), leaf=leaf['id'], acted=True,
                            pred=int(leaf['direction']), real=int(nxt[t]),
                            conv=float(leaf['conv']),
                            chosen=chosen_vars(tree),
                            up=int(nxt[t] > 0)))
    diagnostics(name, cfg, N, pool, records, d)


def frozen_N(name, d, ratio, nxt):
    """Inherit the ORACLE frozen N (pre-1990 design-sample sweep over {3,6,9,12}). Scaffold
    re-derives it here with ORACLE's exact rule so RED DAWN and ORACLE share the same N.
    # TODO(impl): import ORACLE's chosen N directly once ORACLE exposes it as a return value."""
    yr = d['Date'].dt.year.to_numpy()
    pre = yr < 1990
    if (pre & np.isfinite(ratio)).sum() < 40:
        cut = int(len(d) * 0.4); pre = np.arange(len(d)) < cut
    best, ba = 3, -1.0
    for N in range(3, 13, 3):
        rd = np.sign(pc(ratio, N))
        m = pre & np.isfinite(rd) & np.isfinite(nxt) & (rd != 0) & (nxt != 0)
        if m.sum() < 40:
            continue
        a = (rd[m] == nxt[m]).mean()
        if a > ba:
            ba, best = a, N
    return best


def chosen_vars(tree):
    """Which candidate stems this fold's tree actually used (for the per-model modal-predictor
    distribution in diagnostics)."""
    out = {}
    for node in ('primary', 'secondary', 'model3'):
        if tree.get(node):
            out[node] = tree[node][0]
    return out


# ======================================================================================
# END-OF-STAGE DIAGNOSTICS — per-asset, per-type, per-model; NO truncation (spec §6)
# ======================================================================================
def diagnostics(name, cfg, N, pool, records, d):
    acted = [r for r in records if r.get('acted')]
    n = len(acted)
    print("=" * 100)
    print(f"### RED DAWN — {name} ###   anchor={cfg.get('ratio_col') or cfg['num']+'/'+cfg['den']}")
    print(f"[provenance] frozen N={N}mo (ORACLE)  PUB_LAG={PUB_LAG}")
    print(f"[candidates] pool ({len(pool)}): {', '.join(pool)}   "
          f"| excluded anchor legs: {cfg['num']}, {cfg['den']}"
          + (f", {cfg['ratio_col']}" if cfg.get('ratio_col') else "")
          + f"  | banned: {', '.join(sorted(BANNED))}")
    if n == 0:
        print("[OVERALL]    ABSTAIN board — no leaf cleared the admission floor OOS. "
              "(no-edge is an acceptable output; ORACLE baseline stands.)")
        print("=" * 100)
        return
    k = sum(1 for r in acted if r['pred'] == r['real'])
    print(f"[OVERALL]    sequential-WF acc {k/n*100:.1f}%  n_acted={n}  "
          f"LB={wilson_lb(k, n)*100:.0f}% (informational)  abstained={len(records)-n}")
    # coverage-selection guard (C7)
    up = np.array([r['up'] for r in acted]); act = np.ones(len(acted))
    print(f"[coverage]   acted-up-rate={up.mean()*100:.1f}%   "
          f"corr(acted,up) computed over full span in the full runner  # TODO(impl): full-span corr")

    # ---- PER-TYPE table: ALL 27, NO TRUNCATION ----
    print(" ALL 27 TYPES (anchor sign triple) | n_acted | WF acc | LB | leaves fired:")
    sym = {1: 'UP', 0: 'flat', -1: 'DN'}
    for cs in (1, 0, -1):
        for ps in (1, 0, -1):
            for es in (1, 0, -1):
                ti = (cs + 1) * 9 + (ps + 1) * 3 + (es + 1)
                v = [r for r in acted if r['typ'] == ti]
                tag = f"T{ti+1:<2} {sym[cs]:>4}/{sym[ps]:>4}/{sym[es]:>4}"
                if v:
                    kk = sum(1 for r in v if r['pred'] == r['real'])
                    leaves = sorted(set(r['leaf'] for r in v))
                    print(f"   {tag}  n={len(v):<4} {kk/len(v)*100:5.1f}%  "
                          f"LB={wilson_lb(kk, len(v))*100:2.0f}%  {','.join(leaves)}")
                else:
                    print(f"   {tag}  n=0     --")

    # ---- PER-MODEL table within each populated type: modal predictor distribution ----
    print(" PER-MODEL (leaf) — modal chosen predictor across folds (a stable modal = real "
          "correspondence; churning = noise):")
    for ti in sorted(set(r['typ'] for r in acted)):
        for leaf_id in ('model1', 'model2', 'model3', 'model4'):
            v = [r for r in acted if r['typ'] == ti and r['leaf'] == leaf_id]
            if not v:
                continue
            kk = sum(1 for r in v if r['pred'] == r['real'])
            # modal primary predictor stem across the folds that reached this leaf
            prims = [r['chosen'].get('primary') for r in v if r.get('chosen')]
            prims = [p for p in prims if p]
            modal = max(set(prims), key=prims.count) if prims else '--'
            freq = (prims.count(modal) / len(prims) * 100) if prims else 0.0
            print(f"   T{ti+1:<2} {leaf_id:>6}  n={len(v):<4} {kk/len(v)*100:5.1f}%  "
                  f"LB={wilson_lb(kk, len(v))*100:2.0f}%  modal_primary={modal} ({freq:.0f}%)")
    print("[C5 hook] candidates searched per fold -> Stage 5 max-stat placebo  # TODO(impl): record per-fold count")
    print("=" * 100)


# ======================================================================================
if __name__ == '__main__':
    import sys
    df = pd.read_csv(PANEL); df['Date'] = pd.to_datetime(df['Date'])
    for c, lag in PUB_LAG.items():                       # inherit ORACLE PIT lags (C2)
        if c in df.columns:
            df[c] = df[c].shift(lag)
    print(f"[PIT LAGS] {PUB_LAG}")
    ok = oracle.check_leg_uniqueness()                   # anchor leg-uniqueness must PASS
    names = [a for a in sys.argv[1:] if a in ASSETS] or list(ASSETS)
    if ok:
        for nm in names:
            run_asset(nm, df)

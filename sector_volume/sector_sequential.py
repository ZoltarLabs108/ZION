"""
sector_sequential.py — sequential next-month OOS re-derivation of one sector's integrated call.

Why: results/<TK>/integrated_ledger.csv marks a month "pulled" if the TYPE's walk-forward accuracy over the WHOLE
record clears the pull bar (WF>67.5%, n>=8), and the anchor was chosen by R1 on the whole post-design record.
A month in 2020 therefore "knows" how its type did through 2026.  This harness refits EVERYTHING on the panel
truncated at each decision month t (rows with Date <= t; the outcome of t is unknown), and takes the call the
runner would have emitted at t (the last decision row), exactly as s13_tape does today.  Nothing here is fitted
on a month after t: the N sweep (first 40% of the truncated frame), the pull set, the cascade folds, the tier
admission (R3) and, in --mode strict, the anchor choice (R1) are all recomputed from data <= t.

  python sector_sequential.py XLV --mode fixed    # anchor+label held at the admitted one (a one-time design choice)
  python sector_sequential.py XLV --mode strict   # anchor+label chosen by R1 each month on the truncated record

Outputs (never touches results/<TK>/):  results/sequential/<TK>_<mode>_tape.csv, <TK>_<mode>_summary.json
"""
import os, sys, io, json, time, contextlib
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv_saved = list(sys.argv)
import sector_recipe as SR
import types, importlib

EMBARGO = int(sys.argv[sys.argv.index("--embargo") + 1]) if "--embargo" in sys.argv else 0     # training frontier = t - EMBARGO (ZION: 3)
HORIZON = int(sys.argv[sys.argv.index("--horizon") + 1]) if "--horizon" in sys.argv else 1     # outcome horizon in months (method: 1)
FRONT = max(HORIZON, EMBARGO)                                                                   # last training row = t - FRONT


def _load_patched(path, name, subs):
    """Load a module from source with exact-text substitutions (production files untouched); every sub must hit."""
    src = open(path).read()
    for a, b, k in subs:
        assert src.count(a) == k, f"{name}: expected {k} of {a!r}, found {src.count(a)}"
        src = src.replace(a, b)
    m = types.ModuleType(name); m.__file__ = path; sys.modules[name] = m; exec(compile(src, path, "exec"), m.__dict__); return m


MPP = _load_patched("/Users/castaglia/Desktop/ZION/multiasset_pipeline.py", "multiasset_pipeline_seq",
                    [("np.arange(0, t - H + 1)", "np.arange(0, t - FRONT + 1)", 3)])
MPP.FRONT = FRONT
R = _load_patched(os.path.join(HERE, "sector_runner.py"), "sector_runner_seq",
                  [("MP.H = 1;", "MP.H = HORIZON;", 1),
                   ("nxt = np.sign(np.concatenate([out[1:] / out[:-1] - 1, [np.nan]]))", "nxt = np.sign(np.concatenate([out[HORIZON:] / out[:-HORIZON] - 1, [np.nan] * HORIZON]))", 1),
                   ("tr = np.arange(0, t); tr = tr[", "tr = np.arange(0, t - FRONT + 1); tr = tr[", 1)])
R.MP = MPP; R.HORIZON = HORIZON; R.FRONT = FRONT

OUT = os.path.join(HERE, "results", "sequential"); os.makedirs(OUT, exist_ok=True)
SCR = SR.SCR


def wlb95(p, n, z=1.96): return R.wlb95(p, n, z)


def quiet(f, *a):
    with contextlib.redirect_stdout(io.StringIO()): return f(*a)


def main():
    tk = sys.argv[1]; mode = sys.argv[sys.argv.index("--mode") + 1] if "--mode" in sys.argv else "fixed"
    excl = sys.argv[sys.argv.index("--exclude") + 1].split(",") if "--exclude" in sys.argv else []
    c = R.Ctx(tk, excl); tag = tk + ("_ex" + "_".join(x.replace("-", "") for x in excl) if excl else "")
    base_mode = mode; mode = mode + (f"_e{EMBARGO}" if EMBARGO else "") + (f"_h{HORIZON}" if HORIZON != 1 else "")   # tag carries the variant; the branch uses base_mode
    c.out = os.path.join(SCR, "seq", f"{tag}_{mode}"); os.makedirs(c.out, exist_ok=True)      # scratch: runner writes go here
    t0 = time.time(); quiet(R.s1_legs, c); quiet(R.s2_constituents, c); quiet(R.s3_cape, c)
    cape_full = c.cape.copy()
    # full-record anchor (what the runner admitted), for --mode fixed and for the comparison
    quiet(R.s4_oracle, c)                                             # writes oracle_anchors.json into the scratch out dir (s5 reads it when no anchor)
    # the admitted anchor is the runner's H=1 choice on record (results/<TK>/oracle_anchors.json) — held fixed as a design choice in --mode fixed,
    # including under --embargo / --horizon variants; strict mode re-chooses it monthly on the truncated record at the variant's horizon
    _oa = [r for r in json.load(open(os.path.join(HERE, "results", tag, "oracle_anchors.json"))) if r.get("eligible")]
    _b = max(_oa, key=lambda r: r["edge"]) if _oa else None; adm_anchor = _b["anchor"] if _b else None; adm_label = _b["label"] if _b else "absolute"
    c.anchor, c.label, c.rel = adm_anchor, adm_label, adm_label == "relative"
    print(f"[{tag}] {mode}: data ready {time.time()-t0:.0f}s; admitted anchor {adm_anchor} / {adm_label}; CAPE10 rows {len(cape_full.dropna(subset=['CAPE10']))}", flush=True)

    # decision months: every month from the first decision row of the full-record run to the last resolvable month
    quiet(R.s5_stage3, c); ML_full = c.s3["ML"]
    months = [pd.Timestamp(d) for d in ML_full.date]; last_resolvable = c.px_close.index[-1 - HORIZON]
    months = [m for m in months if m <= last_resolvable]
    if "--last" in sys.argv: months = months[-int(sys.argv[sys.argv.index("--last") + 1]):]          # smoke-test: last N months only
    out_dir = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else OUT; os.makedirs(out_dir, exist_ok=True)

    panel_orig = R._panel_df
    rows = []
    for t in months:
        c.cape = cape_full[cape_full.Date <= t].reset_index(drop=True)
        R._panel_df = lambda cc, _t=t: panel_orig(cc)[lambda d: d.Date <= _t].reset_index(drop=True)
        rec = dict(date=t.strftime("%Y-%m-%d"))
        try:
            if base_mode == "strict":
                quiet(R.s4_oracle, c)                      # R1 on the truncated record; c.anchor may be None
            else:
                c.anchor, c.label = adm_anchor, adm_label; c.rel = (adm_label == "relative")
            rec.update(anchor=c.anchor, label=c.label)
            quiet(R.s5_stage3, c); quiet(R.s6_pretype, c)
            A = c.s3["ML"]; P = c.pre["ML"]; cur = A.iloc[-1]; pc_ = P.iloc[-1]
            if pd.Timestamp(cur.date) != t or pd.Timestamp(pc_.date) != t:
                rec.update(call=0.0, source="no-decision-row", note=f"last rows {cur.date}/{pc_.date}"); rows.append(rec); continue
            tcall = 0.0 if cur.status not in ("pulled", "emitted") else float(cur.get("base_dir", 0) if cur.status == "pulled" else cur.get("predB", 0))
            tstate = "pull" if cur.status == "pulled" else ("remainder-cascade" if cur.status == "emitted" else ("warm-up" if cur.reason == "train<MIN_TRAIN" else "abstain"))
            tier = str(pc_.get("tier", "")); scall = float(pc_.get("predB", 0)) if (pc_.status == "emitted" and tier in c.second) else 0.0
            if tcall: call, src = tcall, ("type-pull" if tstate == "pull" else "post-type-cascade")
            elif scall and tstate != "warm-up": call, src = scall, "second-instrument"
            else: call, src = 0.0, "abstain"
            rec.update(type_call=tcall, type_state=tstate, type_cell=f"T{int(cur.typ)+1}" if cur.typ >= 0 else "untyped", pulled=",".join(f"T{x}" for x in c.s3["pulled"]),
                       second_call=scall, tier=tier, second_set=",".join(c.second), call=call, source=src, type_silent=bool(c.type_silent))
        except SystemExit as e:
            rec.update(call=0.0, source="blocked", note=str(e)[:80])
        except ZeroDivisionError:
            rec.update(call=0.0, source="warm-up", type_state="warm-up", note="no scored phase-1 decision yet on the truncated frame (MP diagnostics p1_n=0)")
        except Exception as e:
            rec.update(call=0.0, source="error", note=f"{type(e).__name__}: {str(e)[:80]}")
        rows.append(rec)
        if len(rows) % 12 == 0: print(f"[{tag}] {mode} {t.date()} ({len(rows)}/{len(months)}) {time.time()-t0:.0f}s", flush=True)
    R._panel_df = panel_orig; c.cape = cape_full

    T = pd.DataFrame(rows); T["date"] = pd.to_datetime(T.date)
    # outcomes (both labels), month-start Close as in _panel_df; the scored label is the one the month's anchor used
    px = c.px_close; spy = c.spy_close; nx = px.shift(-HORIZON) / px - 1; nr = (px / spy).shift(-HORIZON) / (px / spy) - 1
    T["ret_abs"] = nx.reindex(T.date).values; T["ret_rel"] = nr.reindex(T.date).values
    T["lab_abs"] = np.sign(T.ret_abs); T["lab_rel"] = np.sign(T.ret_rel)
    T["lab"] = np.where(T.label.fillna("absolute") == "relative", T.lab_rel, T.lab_abs)
    T["hit"] = np.where(T.call != 0, (T.call == T.lab).astype(float), np.nan)
    ra = c.px_adj.shift(-HORIZON) / c.px_adj - 1; rr = ra - (c.spy_adj.shift(-HORIZON) / c.spy_adj - 1).reindex(ra.index)
    T["sleeve_ret"] = np.where(T.label.fillna("absolute") == "relative", rr.reindex(T.date).values, ra.reindex(T.date).values)
    T["pnl_unit"] = T.call * T.sleeve_ret
    T.to_csv(os.path.join(out_dir, f"{tag}_{mode}_tape.csv"), index=False)

    # summary + comparison with the full-record ledger
    a = T[(T.call != 0) & T.lab.notna() & (T.lab != 0)]; n = len(a); acc = float(a.hit.mean()) if n else None
    up = float((a.lab > 0).mean()) if n else None; maj = max(up, 1 - up) if n else None
    ys = {int(y): [float(g.hit.mean()), len(g)] for y, g in a.groupby(a.date.dt.year)}
    J = pd.read_csv(os.path.join(HERE, "results", tag, "integrated_ledger.csv")); J["date"] = pd.to_datetime(J.date); J = J[J.type_state != "warm-up"]
    if HORIZON != 1: J = J.iloc[0:0]                                     # the H=1 ledger is not comparable to a 3-month label
    M = T.merge(J[["date", "call", "source", "lab"]].rename(columns={"call": "call_full", "source": "source_full", "lab": "lab_full"}), on="date", how="inner")
    Mf = M[M.call_full != 0]; Ms = M[M.call != 0]
    summ = dict(tk=tag, mode=mode, embargo=EMBARGO, horizon=HORIZON, admitted_anchor=adm_anchor, admitted_label=adm_label, months=len(T), first=str(T.date.min().date()), last=str(T.date.max().date()),
                acted=n, acc=acc, lb95=float(wlb95(acc, n)) if n else None, up_rate=up, majority=maj, edge=(acc - maj) if n else None,
                long_n=int((a.call > 0).sum()), long_acc=float(a[a.call > 0].hit.mean()) if (a.call > 0).any() else None,
                short_n=int((a.call < 0).sum()), short_acc=float(a[a.call < 0].hit.mean()) if (a.call < 0).any() else None,
                by_source={s: [len(g), float(g.hit.mean())] for s, g in a.groupby("source")}, by_year=ys,
                anchors_used={str(k): int(v) for k, v in T.anchor.fillna("NONE").value_counts().items()},
                errors=int((T.source == "error").sum()), blocked=int((T.source == "blocked").sum()),
                vs_full=dict(overlap=len(M), full_acted=int(len(Mf)), full_acc=float((Mf.call_full == Mf.lab_full).mean()) if len(Mf) else None,
                             seq_acted=int(len(Ms)), same_call=int(((M.call == M.call_full) & (M.call != 0)).sum()), seq_only=int(((M.call != 0) & (M.call_full == 0)).sum()),
                             full_only=int(((M.call == 0) & (M.call_full != 0)).sum()), opposite=int(((M.call * M.call_full) < 0).sum())),
                elapsed_s=round(time.time() - t0))
    json.dump(summ, open(os.path.join(out_dir, f"{tag}_{mode}_summary.json"), "w"), indent=1, default=float)
    print(f"[{tag}] {mode} DONE: acted {n}/{len(T)} acc {acc*100 if acc else 0:.1f}% LB95 {summ['lb95']*100 if n else 0:.1f}% majority {maj*100 if maj else 0:.0f}% | sources {summ['by_source']} | vs full-record: same {summ['vs_full']['same_call']} full-only {summ['vs_full']['full_only']} seq-only {summ['vs_full']['seq_only']} opposite {summ['vs_full']['opposite']} | errors {summ['errors']} | {summ['elapsed_s']}s", flush=True)


if __name__ == "__main__":
    main()

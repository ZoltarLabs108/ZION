"""
ZION HYPERION — data-assembly stage (master_panel builder).

Assembles master_panel.csv: one row per month (first-of-month anchor), one column per ZION
variable, with PER-SERIES PIT publication-lag alignment and unit-aware splice checks. It is
the database of record every downstream ZION stage reads.

Two modes (--mode):
  panel  (DEFAULT)  read the existing HYACINTH_X combined_macro panel, select the ZION
                    variables, apply lags + splice checks, write master_panel. Fully offline,
                    deterministic, always produces output.
  live              fetch each series live from FRED + Yahoo (mirrors AEGIS/WF_PILOT/BF.py:
                    fetch_fred_series with the TED->BAA10Y splice, fetch_yahoo_daily), then the
                    same align/lag/splice path. Requires a FRED key (~/.config/ghsys/fred_key or
                    $FRED_API_KEY) AND network. Endpoints/keys documented in LIVE_FETCH_NOTES.

The VARIABLES registry below is the single source of truth and mirrors the finalized table in
spec/ZION_HYPERION.md. It drives fetch, lag, splice and provenance.

PIT lag = months a reference-month value is shifted FORWARD so that at a 1st-of-month decision,
row M holds only what was published by then. Applied on a complete monthly grid so shift(lag) is
an exact month offset. Default applied set matches oracle_stage.py's PUB_LAG so ORACLE can drop
its private lag once HYPERION bakes it here.

Usage:
  python3 hyperion_build.py                         # panel mode -> data/master_panel.csv
  python3 hyperion_build.py --apply-all-lags        # also lag Real_Earnings (changes CAPE timing)
  python3 hyperion_build.py --mode live             # live FRED/Yahoo fetch (needs key+network)

Author: ZION / HYPERION stage
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

# ============================================================================
# PATHS
# ============================================================================
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PANEL_SRC = "/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
DATA_DIR = os.path.join(REPO, "data")                       # gitignored produced artifacts
RECORD_CSV = os.path.join(HERE, "analysis_record.csv")      # committed provenance ledger
SAMPLE_CSV = os.path.join(HERE, "master_panel_sample.csv")  # committed shape sample

# ============================================================================
# VARIABLE REGISTRY  (single source of truth — mirrors spec/ZION_HYPERION.md)
#   role     : short purpose string
#   unit     : 'price' | 'index' | 'level' | 'rate'  -> drives the splice check
#   fred     : FRED series id (live mode) or None
#   yahoo    : Yahoo ticker (live mode) or None
#   derived  : True if built by SHILLER/ORACLE upstream (not fetched here)
#   pit_lag  : PIT lag in months (recorded)
#   applied  : whether pit_lag is applied by DEFAULT (baked into master_panel)
#   splice   : ('YYYY-MM-01', 'reason') for a known HARD unit splice, else None
# ============================================================================
VARIABLES = {
    # ---- Outcomes (five assets) ----
    "SP_Price":              dict(role="OUTCOME S&P500",   unit="index", fred="SP500",      yahoo="^GSPC",     derived=False, pit_lag=0, applied=False, splice=None),
    "Gold_Close":            dict(role="OUTCOME Gold",     unit="price", fred=None,         yahoo="GC=F",      derived=False, pit_lag=0, applied=False, splice=None),
    "Silver_Close":          dict(role="OUTCOME Silver",   unit="price", fred=None,         yahoo="SI=F",      derived=False, pit_lag=0, applied=False, splice=None),
    "WTI_Crude_Close":       dict(role="OUTCOME WTI",      unit="price", fred="DCOILWTICO", yahoo="CL=F",      derived=False, pit_lag=0, applied=False, splice=None),
    "Dollar_Index":          dict(role="OUTCOME USD / Gold num", unit="index", fred="DTWEXM",  yahoo="DX-Y.NYB", derived=False, pit_lag=0, applied=False, splice=None),
    # ---- Predictor legs in use ----
    "Real_Price":            dict(role="S&P num (CAPE)",   unit="index", fred=None,         yahoo=None,        derived=True,  pit_lag=0, applied=False, splice=None),
    "Real_Earnings":         dict(role="S&P den (CAPE) CYCLE", unit="index", fred=None,      yahoo=None,        derived=True,  pit_lag=2, applied=False, splice=None),  # recorded, opt-in only
    "M2_Money":              dict(role="Gold den",         unit="level", fred="M2SL",       yahoo=None,        derived=False, pit_lag=2, applied=True,  splice=None),
    "Industrial_Production": dict(role="Silver num",       unit="level", fred="INDPRO",     yahoo=None,        derived=False, pit_lag=2, applied=True,  splice=None),
    "GS10_Rate":             dict(role="Silver den",       unit="rate",  fred="GS10",       yahoo=None,        derived=False, pit_lag=0, applied=False, splice=None),
    "US_2Y_Treasury":        dict(role="WTI num",          unit="rate",  fred="DGS2",       yahoo=None,        derived=False, pit_lag=0, applied=False, splice=None),
    "Fed_Funds_Rate":        dict(role="WTI den",          unit="rate",  fred="FEDFUNDS",   yahoo=None,        derived=False, pit_lag=0, applied=False, splice=None),
    "US_CPI":                dict(role="USD den + DEFLATOR", unit="level", fred="CPIAUCSL", yahoo=None,        derived=False, pit_lag=2, applied=True,  splice=None),
    # ---- Cycle inputs kept for ORACLE (CAPE ratio_col + reals) ----
    "Earnings":              dict(role="nominal earnings (cycle)", unit="index", fred=None, yahoo=None,        derived=True,  pit_lag=0, applied=False, splice=None),
    "CPI":                   dict(role="Shiller CPI (reals)", unit="level", fred=None,      yahoo=None,        derived=True,  pit_lag=0, applied=False, splice=None),
    "CAPE":                  dict(role="ORACLE ratio_col (S&P)", unit="index", fred=None,   yahoo=None,        derived=True,  pit_lag=0, applied=False, splice=None),
    # ---- Candidate pool (reserved; not predictors yet) ----
    "Term_Spread_10Y_2Y":    dict(role="CAND regime lens (rate/level)", unit="rate", fred="T10Y2Y", yahoo=None, derived=False, pit_lag=0, applied=False, splice=None),
    "Copper_Close":          dict(role="CAND Dr.Copper growth", unit="price", fred="PCOPPUSDM", yahoo="HG=F", derived=False, pit_lag=0, applied=False, splice=("2000-08-01", "$/tonne->$/lb ~2000x unit break")),
    "Natural_Gas_Close":     dict(role="CAND 5th asset",    unit="price", fred="DHHNGSP",    yahoo="NG=F",      derived=False, pit_lag=0, applied=False, splice=None),
}

# Splice-check thresholds by unit
SPLICE_RULES = {
    "price": dict(metric="pct", warn=0.40, block=0.60),
    "index": dict(metric="pct", warn=0.40, block=0.60),
    "level": dict(metric="pct", warn=0.40, block=0.60),
    "rate":  dict(metric="pts", warn=3.0,  block=5.0),
}

# ============================================================================
# LIVE-FETCH NOTES  (what `--mode live` requires — printed on demand)
# ============================================================================
LIVE_FETCH_NOTES = """
LIVE FETCH REQUIREMENTS (--mode live)
  FRED : key from ~/.config/ghsys/fred_key or $FRED_API_KEY
         endpoint https://api.stlouisfed.org/fred/series/observations
         ids used: DCOILWTICO, DTWEXM(+DTWEXBGS splice), M2SL, INDPRO, GS10, DGS2,
                   FEDFUNDS, CPIAUCSL, T10Y2Y, PCOPPUSDM, DHHNGSP
         pacing: >=0.55s between request starts (~109/min, under FRED's ~120/min cap)
         splice: TEDRATE->BAA10Y scale-match after 2022-01-21 (BF.py pattern; not used by ZION legs)
  Yahoo: endpoint https://query1.finance.yahoo.com/v8/finance/chart/<ticker> interval=1d
         tickers: ^GSPC, GC=F, SI=F, CL=F, DX-Y.NYB, HG=F, NG=F ; UA header required; throttle bulk pulls
  Derived (Real_Price/Real_Earnings/Earnings/CPI/CAPE): produced upstream by SHILLER/ORACLE,
         NOT fetched here. In live mode they are read from the SHILLER replica if present, else
         carried from the panel. Live mode currently REQUIRES the panel for derived Shiller cols.
"""


# ============================================================================
# LIVE FETCH PRIMITIVES  (mirror AEGIS/WF_PILOT/BF.py)
# ============================================================================
_last_fred = [0.0]
FRED_MIN_INTERVAL = 0.55
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def _fred_key():
    k = os.environ.get("FRED_API_KEY")
    if k:
        return k.strip()
    p = os.path.expanduser("~/.config/ghsys/fred_key")
    if os.path.exists(p):
        return open(p).read().strip()
    return ""


def _fred_pace():
    wait = FRED_MIN_INTERVAL - (time.monotonic() - _last_fred[0])
    if wait > 0:
        time.sleep(wait)
    _last_fred[0] = time.monotonic()


def fetch_fred_series(series_id, series_name, api_key, start="1871-01-01", retries=4):
    """Monthly-normalized FRED fetch (mirrors BF.py fetch_fred_series). First-of-month dated."""
    import requests
    end = datetime.now().strftime("%Y-%m-%d")
    params = dict(series_id=series_id, api_key=api_key, file_type="json",
                  observation_start=start, observation_end=end, limit=100000)
    for attempt in range(retries):
        _fred_pace()
        try:
            r = requests.get(FRED_BASE, params=params, timeout=15)
            if r.status_code == 200:
                rows = []
                for obs in r.json().get("observations", []):
                    v = obs.get("value", ".")
                    if v not in (".", "", "NA", None):
                        try:
                            rows.append({"Date": pd.to_datetime(obs["date"]).replace(day=1),
                                         series_name: float(v)})
                        except Exception:
                            continue
                if not rows:
                    return pd.DataFrame(columns=["Date", series_name])
                df = pd.DataFrame(rows).groupby("Date").first().reset_index().sort_values("Date")
                print(f"  FRED {series_name} ({series_id}): {len(df)} obs")
                return df
            time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
        except Exception as e:
            print(f"  FRED {series_name} attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    return pd.DataFrame(columns=["Date", series_name])


def fetch_yahoo_daily_monthly(ticker, series_name, start="1968-01-01"):
    """Daily Yahoo close -> first-of-month value (mirrors BF.py fetch_yahoo_daily + monthly reduce)."""
    import requests
    s_ts = int(pd.Timestamp(start).timestamp())
    e_ts = int(datetime.now().timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = dict(period1=s_ts, period2=e_ts, interval="1d")
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame(columns=["Date", series_name])
        res = r.json()["chart"]["result"][0]
        df = pd.DataFrame({"Date": pd.to_datetime(res["timestamp"], unit="s").normalize(),
                           series_name: res["indicators"]["quote"][0]["close"]}).dropna()
        df["YM"] = df["Date"].dt.to_period("M")
        cur = pd.Timestamp.now().to_period("M")
        hist = df[df["YM"] < cur].groupby("YM").first()   # first-of-month for history
        curr = df[df["YM"] == cur].groupby("YM").last()   # latest for current partial month
        out = pd.concat([hist, curr]).reset_index()
        out["Date"] = out["YM"].dt.to_timestamp()
        print(f"  Yahoo {series_name} ({ticker}): {len(out)} months")
        return out[["Date", series_name]].sort_values("Date")
    except Exception as e:
        print(f"  Yahoo {series_name} failed: {e}")
        return pd.DataFrame(columns=["Date", series_name])


# ============================================================================
# PROVENANCE LEDGER
# ============================================================================
RECORD_COLS = ["run_ts", "run_id", "stage", "asset", "action", "inputs", "inputs_hash",
               "params", "key_outputs", "rows_in", "rows_out", "status", "note"]


class Ledger:
    def __init__(self, run_id, inputs_hash):
        self.run_id = run_id
        self.inputs_hash = inputs_hash
        self.rows = []

    def log(self, stage, asset, action, inputs="", params=None, key_outputs=None,
            rows_in="", rows_out="", status="OK", note=""):
        self.rows.append({
            "run_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.run_id, "stage": stage, "asset": asset, "action": action,
            "inputs": inputs, "inputs_hash": self.inputs_hash,
            "params": json.dumps(params, separators=(",", ":")) if params is not None else "",
            "key_outputs": json.dumps(key_outputs, separators=(",", ":")) if key_outputs is not None else "",
            "rows_in": rows_in, "rows_out": rows_out, "status": status, "note": note,
        })
        print(f"  [{status}] {stage}/{asset}/{action} {note}".rstrip())

    def flush(self, path):
        new = pd.DataFrame(self.rows, columns=RECORD_COLS)
        if os.path.exists(path):
            old = pd.read_csv(path)
            new = pd.concat([old, new], ignore_index=True)
        new.to_csv(path, index=False)


def _sha12(path):
    if not os.path.exists(path):
        return "NA"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


# ============================================================================
# ASSEMBLY HELPERS
# ============================================================================
def to_monthly_grid(df, led):
    """First-of-month normalize, dedup(last), monotonic, reindex to a COMPLETE monthly grid."""
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"]).values.astype("datetime64[M]").astype("datetime64[ns]")
    df = df.sort_values("Date").drop_duplicates("Date", keep="last")
    full = pd.date_range(df["Date"].min(), df["Date"].max(), freq="MS")
    gaps = len(full) - df["Date"].nunique()
    df = df.set_index("Date").reindex(full).rename_axis("Date").reset_index()
    led.log("HYPERION", "ALL", "grid_reindex",
            params={"freq": "MS"},
            key_outputs={"first": str(full.min().date()), "last": str(full.max().date()),
                         "months": len(full), "gaps_filled": int(gaps)},
            rows_out=len(df), note=f"{gaps} internal month(s) inserted")
    return df


def apply_pit_lag(df, name, lag, led):
    """Shift a series FORWARD by `lag` months on the complete grid (row M := value from M-lag)."""
    before_last = df[name].last_valid_index()
    df[name] = df[name].shift(lag)
    after_last = df[name].last_valid_index()
    dropped_tail = (df.loc[before_last, "Date"].strftime("%Y-%m-%d")
                    if before_last is not None else None)
    led.log("HYPERION", name, "apply_lag", params={"lag": lag},
            key_outputs={"new_last_known": (df.loc[after_last, "Date"].strftime("%Y-%m-%d")
                                            if after_last is not None else None),
                         "tail_ref_dropped_to": dropped_tail},
            status="OK", note=f"shifted +{lag}mo (PIT)")
    return df


def splice_check(df, name, meta, led, allow_splice=False):
    """Unit-aware splice/jump detection. Returns 'OK'|'WARN'|'BLOCK'|'QUARANTINE'."""
    unit = meta["unit"]
    rule = SPLICE_RULES.get(unit, SPLICE_RULES["price"])
    s = df[["Date", name]].dropna().reset_index(drop=True)
    if len(s) < 3:
        led.log("HYPERION", name, "splice_check", status="WARN",
                key_outputs={"n": len(s)}, note="too few obs to check")
        return "WARN"

    # 1) Declared HARD splice (e.g. Copper 2000-08): seam level-ratio test
    if meta.get("splice"):
        seam_date, reason = meta["splice"]
        seam = pd.Timestamp(seam_date)
        pre = s[s["Date"] < seam][name]
        post = s[s["Date"] >= seam][name]
        if len(pre) and len(post):
            ratio = float(post.iloc[0]) / float(pre.iloc[-1]) if pre.iloc[-1] else np.inf
            hard = (ratio < 0.1 or ratio > 10)  # order-of-magnitude unit break
            if hard and not allow_splice:
                led.log("HYPERION", name, "quarantine", params={"seam": seam_date},
                        key_outputs={"seam_ratio": round(ratio, 6)}, status="QUARANTINE",
                        note=f"HARD splice unrepaired ({reason}) -> column excluded")
                return "QUARANTINE"
            led.log("HYPERION", name, "splice_check", params={"seam": seam_date},
                    key_outputs={"seam_ratio": round(ratio, 6)},
                    status="WARN" if hard else "OK",
                    note=("allow_splice set — kept despite unit break" if hard else "seam within tolerance"))

    # 2) General jump scan
    if rule["metric"] == "pct":
        jump = s[name].pct_change().abs()
    else:
        jump = s[name].diff().abs()
    mx = float(jump.max()) if len(jump.dropna()) else 0.0
    when = s.loc[jump.idxmax(), "Date"].strftime("%Y-%m-%d") if jump.notna().any() else None
    n_review = int((jump > rule["block"]).sum())  # exceed the high tier -> human review, NOT auto-excluded
    n_warn = int((jump > rule["warn"]).sum())
    # General jumps are FLAGGED, never auto-excluded: a real crash (WTI 2020, Volcker rates,
    # 2008 earnings) is not a unit error. Only a DECLARED hard splice quarantines a column.
    status = "OK" if n_warn == 0 else "WARN"
    led.log("HYPERION", name, "splice_check",
            params={"unit": unit, "metric": rule["metric"], "warn": rule["warn"], "review": rule["block"]},
            key_outputs={"max_jump": round(mx, 4), "at": when, "n_warn": n_warn, "n_review": n_review},
            status=status,
            note=("clean" if status == "OK" else
                  f"{n_warn} jump(s) > warn; {n_review} > review-tier (flagged, kept)"))
    return status


# ============================================================================
# SOURCES
# ============================================================================
def load_from_panel(cols, led):
    if not os.path.exists(PANEL_SRC):
        print(f"FATAL: panel not found: {PANEL_SRC}")
        sys.exit(2)
    have = pd.read_csv(PANEL_SRC, nrows=0).columns.tolist()
    present = [c for c in cols if c in have]
    missing = [c for c in cols if c not in have]
    df = pd.read_csv(PANEL_SRC, usecols=["Date"] + present)
    led.log("HYPERION", "ALL", "load_source", inputs=PANEL_SRC,
            key_outputs={"cols_present": len(present), "cols_missing": len(missing),
                         "missing": missing}, rows_in=len(df), rows_out=len(df),
            status="OK" if not missing else "WARN",
            note=f"panel mode; {len(present)}/{len(cols)} vars present")
    return df, present, missing


def load_live(cols, led):
    key = _fred_key()
    if not key:
        print("FATAL: --mode live needs a FRED key (~/.config/ghsys/fred_key or $FRED_API_KEY).")
        print(LIVE_FETCH_NOTES)
        sys.exit(2)
    # Derived Shiller columns are produced upstream; carry them from the panel if available.
    frames = []
    for name in cols:
        meta = VARIABLES[name]
        if meta["derived"]:
            continue
        if meta["fred"]:
            f = fetch_fred_series(meta["fred"], name, key)
        elif meta["yahoo"]:
            f = fetch_yahoo_daily_monthly(meta["yahoo"], name)
        else:
            f = pd.DataFrame(columns=["Date", name])
        if not f.empty:
            frames.append(f)
            led.log("HYPERION", name, "fetch", inputs=(meta["fred"] or meta["yahoo"]),
                    key_outputs={"n": len(f)}, rows_out=len(f))
    derived = [c for c in cols if VARIABLES[c]["derived"]]
    if derived and os.path.exists(PANEL_SRC):
        have = pd.read_csv(PANEL_SRC, nrows=0).columns.tolist()
        dpresent = [c for c in derived if c in have]
        dfd = pd.read_csv(PANEL_SRC, usecols=["Date"] + dpresent)
        frames.append(dfd)
        led.log("HYPERION", "ALL", "load_derived", inputs=PANEL_SRC,
                key_outputs={"derived_cols": dpresent}, status="WARN",
                note="derived Shiller cols carried from panel (SHILLER replica not wired)")
    if not frames:
        print("FATAL: no data fetched.")
        sys.exit(2)
    df = frames[0]
    for f in frames[1:]:
        f = f.copy()
        f["Date"] = pd.to_datetime(f["Date"])
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.merge(f, on="Date", how="outer")
    present = [c for c in cols if c in df.columns]
    missing = [c for c in cols if c not in df.columns]
    return df.sort_values("Date"), present, missing


# ============================================================================
# MAIN
# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="ZION HYPERION master_panel builder")
    ap.add_argument("--mode", choices=["panel", "live"], default="panel")
    ap.add_argument("--apply-all-lags", action="store_true",
                    help="Also apply recorded-but-off lags (e.g. Real_Earnings=2). Changes CAPE timing.")
    ap.add_argument("--allow-splice", action="store_true",
                    help="Keep hard-splice columns (e.g. Copper) instead of quarantining them.")
    ap.add_argument("--out", default=None, help="Output path (default data/master_panel.csv)")
    ap.add_argument("--live-notes", action="store_true", help="Print live-fetch requirements and exit")
    args = ap.parse_args()

    if args.live_notes:
        print(LIVE_FETCH_NOTES)
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    run_id = "HYPERION_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    src_hash = _sha12(PANEL_SRC)
    led = Ledger(run_id, src_hash)
    cols = list(VARIABLES.keys())

    print(f"\n{'='*80}\nZION HYPERION — master_panel build  ({args.mode} mode)  run={run_id}\n{'='*80}")

    # 1) LOAD
    if args.mode == "live":
        df, present, missing = load_live(cols, led)
    else:
        df, present, missing = load_from_panel(cols, led)
    if missing:
        print(f"  NOTE: {len(missing)} registry var(s) absent from source: {missing}")

    # 2) MONTHLY GRID
    df = to_monthly_grid(df, led)

    # 3) PER-COLUMN COVERAGE (record before lagging)
    for name in present:
        s = df[["Date", name]].dropna()
        led.log("HYPERION", name, "coverage",
                params={"unit": VARIABLES[name]["unit"], "role": VARIABLES[name]["role"]},
                key_outputs={"n": len(s),
                             "first": (str(s["Date"].min().date()) if len(s) else None),
                             "last": (str(s["Date"].max().date()) if len(s) else None)})

    # 4) SPLICE CHECKS  -> quarantine hard-splice columns
    quarantined = []
    for name in present:
        st = splice_check(df, name, VARIABLES[name], led, allow_splice=args.allow_splice)
        if st == "QUARANTINE":
            quarantined.append(name)
    keep = [c for c in present if c not in quarantined]

    # 5) PIT LAGS
    for name in keep:
        meta = VARIABLES[name]
        lag = meta["pit_lag"]
        do = lag > 0 and (meta["applied"] or args.apply_all_lags)
        if do:
            df = apply_pit_lag(df, name, lag, led)
        elif lag > 0:
            led.log("HYPERION", name, "apply_lag", params={"lag": lag}, status="WARN",
                    note="lag RECORDED but not applied (use --apply-all-lags)")

    # 6) WRITE
    out_cols = ["Date"] + keep
    master = df[out_cols].copy()
    mmyy = datetime.now().strftime("%m%y")
    out_path = args.out or os.path.join(DATA_DIR, "master_panel.csv")
    ver_path = os.path.join(DATA_DIR, f"master_panel_{mmyy}.csv")
    master.to_csv(out_path, index=False)
    master.to_csv(ver_path, index=False)
    # committed shape sample (head+tail) so in-repo reviewers see the schema
    sample = pd.concat([master.head(3), master.tail(3)])
    sample.to_csv(SAMPLE_CSV, index=False)

    led.log("HYPERION", "ALL", "write_master", inputs=PANEL_SRC,
            params={"applied_all_lags": args.apply_all_lags, "allow_splice": args.allow_splice},
            key_outputs={"path": out_path, "shape": list(master.shape),
                         "first": str(master["Date"].min().date()),
                         "last": str(master["Date"].max().date()),
                         "quarantined": quarantined},
            rows_out=len(master), status="OK",
            note=f"{master.shape[0]}x{master.shape[1]}; quarantined={quarantined}")

    led.flush(RECORD_CSV)

    print(f"\n{'='*80}\nDONE")
    print(f"  master_panel : {out_path}")
    print(f"  versioned    : {ver_path}")
    print(f"  shape        : {master.shape[0]} rows x {master.shape[1]} cols "
          f"({master['Date'].min().date()}..{master['Date'].max().date()})")
    print(f"  columns      : {', '.join(keep)}")
    if quarantined:
        print(f"  QUARANTINED  : {quarantined} (hard splice; use --allow-splice to keep)")
    print(f"  ledger       : {RECORD_CSV} (+{len(led.rows)} rows)")
    print(f"  sample       : {SAMPLE_CSV}")
    print("="*80)


if __name__ == "__main__":
    main()

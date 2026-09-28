#!/usr/bin/env python3
"""
hc_stage3.py — STAGE 3 for Health Care on the selected anchor (PE against Growth = CAPE10 / g10), run through the
S&P's OWN Phase 1/2 machinery (ZION/multiasset_pipeline.py: ORACLE 27-type table with zones -> type-level PULLS
(WF > 67.5%, n >= 8) -> untruncated tier cascade on the non-pulled remainder, 27 types printed, audit invariants).
Sector adaptations (declared): H = 1 month (operator ruling); scoring START = end of the design sample (first 40%
of the anchor frame) instead of 1990; sector legs added to the candidate pool as EXTRA_CANDIDATES (splice-scanned
like any extra); PUB_LAG applied to the panel exactly as the pipeline's main() does; outputs redirected.
"NO CHANGE" CRITERION (verbatim from the pipeline): a leg's N-month pct_change is z-scored on the TRAIN rows only
(expanding, PIT); |z| <= 0.5 train-SD -> flat (0); z > 0.5 -> UP; z < -0.5 -> DN. Type = 9*(ratio+1)+3*(num+1)+(den+1).
"""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, "/Users/castaglia/Desktop/ZION"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import multiasset_pipeline as MP
import sector_recipe as SR

HERE = os.path.dirname(os.path.abspath(__file__))
MP.H = 1
MP.REPORTS = os.path.join(HERE, "results", "stage3_hc_pretype"); os.makedirs(MP.REPORTS, exist_ok=True)

# panel + PUB_LAG exactly as MP.main()
df = pd.read_csv(MP.PANEL); df["Date"] = pd.to_datetime(df["Date"])
for c, lag in MP.PUB_LAG.items():
    if c in df.columns: df[c] = df[c].shift(lag)
# sector legs (discrete CAPE legs + FRED drivers, PIT-lagged) merged on Date
legs = SR.sector_legs("XLV"); df = df.merge(legs, on="Date", how="left")
cape = pd.read_csv(os.path.join(HERE, "results", "hc_cape_monthly.csv"), parse_dates=["Date"])
for c in ("RealPrice", "E10"):
    df = df.merge(cape[["Date", c]].rename(columns={c: f"XLV_{c}"}), on="Date", how="left")
df["XLV_Close"] = df["US_Healthcare_Close"]; df["CONST_A"] = 1.0; df["CONST_B"] = 1.0

# scoring start = end of the design sample of the anchor frame (first 40% of rows where anchor legs exist)
frame = df.dropna(subset=["XLV_Close", "XLV_CAPE10", "XLV_g10"])   # same window as the anchored run.reset_index(drop=True)
cut = int(len(frame) * 0.4); MP.START = np.datetime64(frame.Date.iloc[cut])
print(f"anchor frame {frame.Date.min().date()}..{frame.Date.max().date()} ({len(frame)} rows); design = first 40% (< {frame.Date.iloc[cut].date()}); scoring START {MP.START}; H={MP.H}; MIN_TRAIN={MP.MIN_TRAIN}")

MP.EXTRA_CANDIDATES = ["XLV_CAPE10", "XLV_g10", "XLV_CAPEG", "XLV_DivYield", "XLV_RelSPY", "MedCPI_Rel", "HC_Employment", "Pharma_PPI", "XLV_CAPE5", "XLV_CAPE5G",
                       "Term_Spread_10Y_3M", "VIX_Close"]
MP.ASSETS = {"HealthCare": dict(outcome="XLV_Close", num="CONST_A", den="CONST_B", deflate=False, proposed=False,
                                note="TYPE-AGNOSTIC pre-type tier screen (constant anchor => single type); was: PE against Growth: sector CAPE10 / 10-yr trend real earnings growth (both cycle/CPI-adjusted discretely, pre-ratio)")}
lines, tier_rows, summary, findings, artifacts = MP.run_asset("HealthCare", df)
MP.write_asset_files("HealthCare", lines, artifacts)
print("\n".join(lines))
print("\nAUDIT FINDINGS:", findings if findings else "none (clean)")
json.dump(dict(summary=summary, findings=findings, pulled=sorted(int(x) + 1 for x in artifacts["pulled"])), open(os.path.join(MP.REPORTS, "summary.json"), "w"), indent=1, default=str)

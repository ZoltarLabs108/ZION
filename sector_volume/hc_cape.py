#!/usr/bin/env python3
"""
hc_cape.py — Health Care sector CAPE and cyclically adjusted PEG, bottom-up from SEC XBRL filings.

DEFINITIONS (declared 2026-09-13, before any result was seen):
  Universe    the 59 current XLV / S&P 500 Health Care constituents (survivorship: current members only — stated).
  Earnings    annual net income attributable to the company (us-gaap NetIncomeLoss, fallback ProfitLoss), from 10-K
              facts with a ~1-year duration. AS-ISSUED: for each fiscal-year end the value from the EARLIEST filing;
              a value becomes usable only from its FILING date (point-in-time). Real = deflated by CPI at fiscal-year end.
  Shares      weighted-average diluted shares from the same 10-K (fallback dei shares outstanding), usable from filing date.
  Company     E10_i,t = mean of company i's real annual earnings over its last 10 fiscal years usable at t (>= 7 required);
              E5_i,t likewise over 5 (>= 4 required). Negative years are kept, as Shiller does.
  Sector      CAPE10_t = sum_i (price_i,t x shares_i,t) / CPI_t   divided by   sum_i E10_i,t   over companies with both
              price and E10 at t  — i.e. the cap-weighted (harmonic) aggregate of company CAPEs, the Shiller aggregate.
              CAPE5_t the same with E5.
  Growth      g_ca,t = log-linear trend (%/yr) of the sector's aggregate real annual earnings over the last 10 usable
              fiscal years, summed over companies reporting in every year of that window (balanced within window).
  CAPEG_t     = CAPE10_t / max(g_ca,t, 0.5).   CAPE5G_t = CAPE5_t / max(g5_ca,t, 0.5) with a 5-year trend.
Output: results/hc_cape_monthly.csv, results/hc_cape_companies.csv
"""
import os, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
X = json.load(open(os.path.join(HERE, "data", "xbrl", "xlv_companyfacts.json")))
PX = pd.read_csv(os.path.join(HERE, "data", "xbrl", "xlv_constituent_monthly_close.csv"), index_col=0, parse_dates=True)
cpi = pd.read_csv(os.path.join(HERE, "data", "fred_CPIAUCSL.csv")); cpi.columns = ["Date", "cpi"]; cpi["Date"] = pd.to_datetime(cpi.Date)
CPI = cpi.set_index("Date")["cpi"].resample("MS").last().ffill()


def annual(rows, lo=340, hi=380):
    """as-issued annual values: earliest filing per period end, ~1-year durations, 10-K only."""
    out = {}
    for r in rows:
        if r.get("form") not in ("10-K", "10-K/A", "20-F", "40-F") or "start" not in r: continue
        d = (pd.Timestamp(r["end"]) - pd.Timestamp(r["start"])).days
        if not (lo <= d <= hi): continue
        end = pd.Timestamp(r["end"]); filed = pd.Timestamp(r["filed"])
        if end not in out or filed < out[end][1]: out[end] = (float(r["val"]), filed)
    return out


def instant_latest(rows):
    """dei shares outstanding: (as-of end, filed) -> value; usable from filed."""
    out = {}
    for r in rows:
        end = pd.Timestamp(r["end"]); filed = pd.Timestamp(r["filed"])
        if end not in out or filed < out[end][1]: out[end] = (float(r["val"]), filed)
    return out


def usable_series(d, t):
    """values whose filing date <= t, ordered by period end."""
    items = sorted((end, v, f) for end, (v, f) in d.items() if f <= t)
    return items


months = pd.date_range("2009-01-01", PX.index.max(), freq="MS")
comp_rows = []; sector = []
EARN = {}; SHR = {}
for tk, rec in X.items():
    ni = annual(rec.get("NetIncomeLoss", [])) or annual(rec.get("ProfitLoss", []))
    sh = annual(rec.get("WeightedAverageNumberOfDilutedSharesOutstanding", []))
    if not sh and "dei_shares" in rec: sh = instant_latest(rec["dei_shares"])
    if ni and sh: EARN[tk] = ni; SHR[tk] = sh
print("companies with earnings+shares:", len(EARN), "of", len(X))

for t in months:
    num = 0.0; den10 = 0.0; den5 = 0.0; n10 = 0; n5 = 0; caps = {}
    real_by_year = {}   # for the growth trend: tk -> {fy_end_year: real earnings}
    for tk in EARN:
        if tk not in PX.columns or t not in PX.index or np.isnan(PX.at[t, tk]): continue
        e = usable_series(EARN[tk], t); s = usable_series(SHR[tk], t)
        if not e or not s: continue
        shares = s[-1][1]; price = PX.at[t, tk]; cap = price * shares
        real = [(end, v / CPI.asof(end)) for end, v, f in e]
        last10 = real[-10:]; last5 = real[-5:]
        if len(last10) >= 7:
            E10 = np.mean([v for _, v in last10])
            if E10 > 0: num += cap; den10 += E10; n10 += 1; caps[tk] = cap
        if len(last5) >= 4:
            E5 = np.mean([v for _, v in last5])
            if E5 > 0: den5 += E5; n5 += 1
        for end, v in real[-10:]: real_by_year.setdefault(tk, {})[end.year] = v
    # sector trend growth on a balanced window of the last 10 (and 5) fiscal years
    def trend(nyrs):
        cnt = {}
        for d in real_by_year.values():
            for y in d: cnt[y] = cnt.get(y, 0) + 1
        # a fiscal year enters the window only once >= 60% of reporting companies have filed it (mixed FY ends)
        yrs = sorted(y for y, c in cnt.items() if c >= 0.6 * len(real_by_year))[-nyrs:]
        if len(yrs) < max(4, nyrs - 2): return np.nan
        tot = []
        for y in yrs:
            names = [tk for tk in real_by_year if all(yy in real_by_year[tk] for yy in yrs)]
            if len(names) < 10: return np.nan
            tot.append(sum(real_by_year[tk][y] for tk in names))
        tot = np.array(tot)
        if (tot <= 0).any(): return np.nan
        return np.polyfit(np.arange(len(yrs)), np.log(tot), 1)[0] * 100
    g10 = trend(10); g5 = trend(5)
    real_cap = num / CPI.asof(t) if num > 0 else np.nan
    cape10 = real_cap / den10 if den10 > 0 and n10 >= 15 else np.nan
    # CAPE5 uses the same numerator set only approximately (n5 >= n10); recompute strictly with its own caps for honesty
    cape5 = np.nan
    if n5 >= 15:
        num5 = 0.0; d5 = 0.0
        for tk in EARN:
            if tk not in PX.columns or np.isnan(PX.at[t, tk]): continue
            e = usable_series(EARN[tk], t); s = usable_series(SHR[tk], t)
            if not e or not s: continue
            real = [v / CPI.asof(end) for end, v, f in e][-5:]
            if len(real) >= 4 and np.mean(real) > 0: num5 += PX.at[t, tk] * s[-1][1]; d5 += np.mean(real)
        cape5 = (num5 / CPI.asof(t)) / d5 if d5 > 0 else np.nan
    sector.append(dict(Date=t, CAPE10=cape10, CAPE5=cape5, n10=n10, n5=n5, g10=g10, g5=g5,
                       RealPrice=real_cap if n10 >= 15 else np.nan,            # discrete leg: real market cap of the CAPE10 set (CPI-deflated)
                       E10=den10 if n10 >= 15 else np.nan,                      # discrete leg: 10-yr smoothed real earnings of the same set
                       CAPEG=cape10 / max(g10, 0.5) if cape10 == cape10 and g10 == g10 else np.nan,
                       CAPE5G=cape5 / max(g5, 0.5) if cape5 == cape5 and g5 == g5 else np.nan,
                       mcap_bn=num / 1e9 if num else np.nan, top5=", ".join(sorted(caps, key=caps.get, reverse=True)[:5])))
S = pd.DataFrame(sector)
S.to_csv(os.path.join(HERE, "results", "hc_cape_monthly.csv"), index=False)
# company snapshot at the last month
t = months[-1]
for tk in EARN:
    e = usable_series(EARN[tk], t); s = usable_series(SHR[tk], t)
    if not e or not s or tk not in PX.columns: continue
    real = [(end, v / CPI.asof(end)) for end, v, f in e]
    E10 = np.mean([v for _, v in real[-10:]]); shares = s[-1][1]; price = PX.at[t, tk]
    comp_rows.append(dict(ticker=tk, years=len(real), first_fy=real[0][0].year, last_fy=real[-1][0].year,
                          mcap_bn=price * shares / 1e9, E10_todays_dollars_bn=E10 * CPI.asof(t) / 1e9,
                          company_CAPE10=(price * shares / CPI.asof(t)) / E10 if E10 > 0 else np.nan,
                          last_fy_earnings_todays_dollars_bn=real[-1][1] * CPI.asof(t) / 1e9))
C = pd.DataFrame(comp_rows).sort_values("mcap_bn", ascending=False)
C.to_csv(os.path.join(HERE, "results", "hc_cape_companies.csv"), index=False)
v = S.dropna(subset=["CAPE10"])
print("CAPE10 available", v.Date.min().date(), "to", v.Date.max().date(), f"({len(v)} months)")
v5 = S.dropna(subset=["CAPE5"]); print("CAPE5 available", v5.Date.min().date(), "to", v5.Date.max().date(), f"({len(v5)} months)")
print(S.tail(3)[["Date", "CAPE10", "CAPE5", "n10", "g10", "g5", "CAPEG", "CAPE5G", "mcap_bn"]].round(2).to_string(index=False))
print("\nlargest 8 by cap:"); print(C.head(8).round(2).to_string(index=False))

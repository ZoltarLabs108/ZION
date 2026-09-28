#!/usr/bin/env python3
"""
sector_recipe.py — run a SECTOR through the enforced monthly recipe (lib_pipeline.run_asset) with a
TAILORED Stage-1 predictor set and PIT publication lags, then score it on the sequential next-month
walk-forward. Built 2026-09-13 after the Health Care truncation review.

Per-sector declared legs (all derived in-process; ASSET_PIPELINE untouched):
  {TK}_DivYield : log(trailing-12m dividends / price), dividends known through the PRIOR month  (STATIONARY, TIMELY)
  {TK}_RelSPY   : log(sector adj close / SPY adj close), month-start                            (STATIONARY, TIMELY)
  sector drivers from FRED (lagged to publication, see LAGS) and the panel (see SECTOR_LEGS)
GROUNDED macro legs stay in the pool, but Industrial_Production (+2), M2_Money (+1) and US_CPI (+2)
are shifted to their publication month before anything sees them (house pit_lag convention).
"""
import sys, os, json, io, urllib.request, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/castaglia/Desktop/ASSET_PIPELINE")
import lib_pipeline as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = "/private/tmp/claude-501/-Users-castaglia-Desktop-HYACINTH/37cfa8fd-9b03-4ca8-bc96-d52cc2393226/scratchpad"
DATA = os.path.join(HERE, "data"); os.makedirs(DATA, exist_ok=True)

SECTORS = {
    "XLK": ("US_Tech_Close", "Technology"), "XLF": ("US_Financials_Close", "Financials"),
    "XLV": ("US_Healthcare_Close", "Health Care"), "XLE": ("US_Energy_Close", "Energy"),
    "XLI": ("US_Industrials_Close", "Industrials"), "XLP": ("US_Consumer_Staples_Close", "Consumer Staples"),
    "XLY": ("US_Consumer_Disc_Close", "Consumer Disc"), "XLB": ("US_Materials_Close", "Materials"),
    "XLU": ("US_Utilities_Close", "Utilities"),
}
# FRED drivers per sector (declared 2026-09-13; id -> (name, lag_months, stationary?)).
# lag = months between the data month and the first trading day on which it is public.
FRED = {
    "XLV": {"CPIMEDSL": ("MedCPI_Rel", 2, True), "CES6562000001": ("HC_Employment", 2, True), "PCU325412325412": ("Pharma_PPI", 2, False)},
    "XLK": {"PCU334413334413": ("Semi_PPI", 2, False), "IPG334S": ("Electronics_IP", 2, False)},
    "XLF": {"BAA10Y": ("Credit_Spread", 1, True), "TOTLL": ("Bank_Loans", 2, False)},
    "XLE": {"WPU0571": ("Crude_PPI", 2, False), "IPG211S": ("OilGas_IP", 2, False)},
    "XLI": {"DGORDER": ("Durable_Orders", 2, False), "IPMAN": ("Manuf_IP", 2, False)},
    "XLP": {"CPIUFDSL": ("FoodCPI_Rel", 2, True), "RSDBS": ("Grocery_Sales", 2, False)},
    "XLY": {"UMCSENT": ("Consumer_Sentiment", 1, True), "RSXFS": ("Retail_Sales", 2, False)},
    "XLB": {"PCU325325": ("Chemicals_PPI", 2, False), "IPG325S": ("Chemicals_IP", 2, False)},
    "XLU": {"CUSR0000SEHF": ("EnergyServ_CPI_Rel", 2, True), "IPUTIL": ("Utilities_IP", 2, False)},   # IPG2211A2S 404 on FRED (verified 13 Sep) -> IPUTIL
}
REL_TO_CPI = {"MedCPI_Rel", "FoodCPI_Rel", "EnergyServ_CPI_Rel"}     # expressed as log(index / headline CPI)
PANEL_LEGS = {"XLB": ["Copper_Close"]}   # UnitedHealth_CAPE dropped: panel per-stock CAPEs rest on ~3y EPS (method doc §1)   # in-panel sector legs (Copper re-admitted for Materials)
PIT_LAG = {"Industrial_Production": 2, "M2_Money": 1, "US_CPI": 2}


def fred(fid):
    p = os.path.join(DATA, f"fred_{fid}.csv")
    if not os.path.exists(p):
        r = urllib.request.urlopen(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fid}", timeout=30).read().decode()
        open(p, "w").write(r)
    s = pd.read_csv(p); s.columns = ["Date", "v"]; s["Date"] = pd.to_datetime(s.Date); s["v"] = pd.to_numeric(s.v, errors="coerce")
    return s.set_index("Date")["v"].resample("MS").last()


def sector_legs(tk):
    """Build the sector's declared extra legs as a monthly frame indexed at month start (row M-01)."""
    d = pd.read_csv(os.path.join(SCR, f"{tk}_daily.csv"), index_col=0, parse_dates=True)
    spy = pd.read_csv(os.path.join(SCR, "SPY_daily.csv"), index_col=0, parse_dates=True)
    import yfinance as yf
    dvp = os.path.join(DATA, f"{tk}_dividends.csv")
    if not os.path.exists(dvp): yf.Ticker(tk).dividends.to_csv(dvp)
    dv = pd.read_csv(dvp, index_col=0, parse_dates=True).iloc[:, 0]
    dv.index = pd.to_datetime(dv.index, utc=True).tz_convert(None)
    ttm = dv.resample("MS").sum().rolling(12).sum().shift(1)      # dividends paid in the 12 months ENDING prior month
    px = d["Close"].resample("MS").first()                         # first trading day close of month M
    rel = np.log(d["Adj Close"].resample("MS").first() / spy["Adj Close"].resample("MS").first())
    f = pd.DataFrame({f"{tk}_DivYield": np.log(ttm / px), f"{tk}_RelSPY": rel})
    cpi = fred("CPIAUCSL")
    for fid, (nm, lag, stat) in FRED.get(tk, {}).items():
        s = fred(fid)
        if nm in REL_TO_CPI: s = np.log(s / cpi.reindex(s.index))
        f[nm] = s.shift(lag).reindex(f.index)                      # publication lag
    capep = globals().get("_CAPE_OVERRIDE") or os.path.join(HERE, "results", f"{'hc' if tk == 'XLV' else tk.lower()}_cape_monthly.csv")
    if os.path.exists(capep):                                       # sector CAPE legs (SEC XBRL bottom-up, PIT by filing date)
        c = pd.read_csv(capep, parse_dates=["Date"]).set_index("Date")
        for col in ("CAPE10", "CAPE5", "CAPEG", "CAPE5G", "g10", "g5"): f[f"{tk}_{col}"] = c[col].reindex(f.index)
    f = f.replace([np.inf, -np.inf], np.nan)
    f.index.name = "Date"
    return f.reset_index()


def legs_meta(tk):
    cape = [f"{tk}_{c}" for c in ("CAPE10", "CAPE5", "CAPEG", "CAPE5G", "g10", "g5")]
    stat = {f"{tk}_DivYield", f"{tk}_RelSPY", *cape} | {nm for nm, lag, s in FRED.get(tk, {}).values() if s} | set(PANEL_LEGS.get(tk, [])) & {"UnitedHealth_CAPE"}
    names = [f"{tk}_DivYield", f"{tk}_RelSPY", *cape] + [nm for nm, _, _ in FRED.get(tk, {}).values()] + PANEL_LEGS.get(tk, [])
    return names, stat


def install(tk, relative=False):
    """Monkeypatch load_asset so run_asset sees the tailored legs + PIT lags. Returns extra var names.
    relative=True: the OUTCOME becomes the sector/SPY price ratio (month-start closes), so labels, returns, engines,
    DECISION and MIRROR all work on the market-relative series (the "relative tag", operator ruling 2026-09-13)."""
    names, stat = legs_meta(tk)
    legs = sector_legs(tk)
    L.STATIONARY |= stat
    L.TIMELY_VARS |= {f"{tk}_DivYield", f"{tk}_RelSPY", *[f"{tk}_{c}" for c in ("CAPE10", "CAPE5", "CAPEG", "CAPE5G", "g10", "g5")]}
    if not hasattr(L, "_orig_load_asset"): L._orig_load_asset = L.load_asset
    def load_asset(outcome_col, start_year=1971, extra_vars=None, exclude_vars=None, h_label=1):
        panel_extra = [v for v in PANEL_LEGS.get(tk, []) if v not in (extra_vars or [])]
        d = L._orig_load_asset(outcome_col, start_year, extra_vars=panel_extra, exclude_vars=exclude_vars, h_label=h_label)
        attrs = dict(d.attrs)
        d = d.merge(legs, on="Date", how="left"); d.attrs.update(attrs)
        for v, k in PIT_LAG.items():
            if v in d.columns: d[v] = d[v].shift(k)
        d.attrs["extra_vars"] = [v for v in names if v in d.columns]
        d.attrs["pit_lag"] = PIT_LAG
        if relative:
            spy = pd.read_csv(os.path.join(SCR, "SPY_daily.csv"), index_col=0, parse_dates=True)["Close"].resample("MS").first()
            rel_col = f"{tk}_rel_SPY"
            d[rel_col] = d[outcome_col].values / spy.reindex(pd.to_datetime(d["Date"])).values
            d["r"] = d[rel_col].pct_change()
            d["mkt"] = np.sign(d[rel_col].pct_change(h_label).shift(-h_label))
            d.attrs["outcome"] = rel_col
            d.attrs["relative"] = True
        return d
    L.load_asset = load_asset
    return names


def run_full(tk, relative=False):
    col, name = SECTORS[tk]
    names = install(tk, relative=relative)
    exclude = [] if tk == "XLB" else ["Copper_Close"]
    res = L.run_asset(name, col, start_year=1998, extra_vars=names, exclude_vars=exclude, verbose=False)
    return res


if __name__ == "__main__":
    tk = sys.argv[1]; relative = len(sys.argv) > 2 and sys.argv[2] == "relative"
    res = run_full(tk, relative=relative)
    print("\n".join(res["log"]))
    print("\nVERDICT:", res["verdict"])
    if res.get("df") is not None:
        rounds = res["df"].attrs.get("rd_meta", [])
        for r, m in enumerate(rounds, 1):
            print(f"round {r}: {m['pair'][0]}|{m['pair'][1]} k={m['k']} w={m['w']} T={m['t']} dir={m['D']:+d} vaLB={m['valb']:.3f} va_n={m['va_n']}")
    out = {k: v for k, v in res.items() if k in ("name", "verdict", "log")}
    json.dump(out, open(os.path.join(HERE, "results", f"{tk}_recipe{'_relative' if relative else ''}.json"), "w"), indent=1)

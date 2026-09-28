#!/usr/bin/env python3
"""
sector_runner.py — THE PARAMETERIZED SECTOR RUNNER. Executes the SECTOR_METHOD procedure (steps 1–16) for one SPDR sector,
in order, with every step asserting its output before the next starts, and writes results/<TK>/REPORT.md with every table.
Usage: python sector_runner.py XLE            (standard run — the sector as the S&P 500 defines it)
       python sector_runner.py XLF --exclude BRK-B   (declared SENSITIVITY: constituents removed from the sector CAPE; results/<TK>_ex<...>/)

Constants fixed across sectors (never tuned per sector): H = 1 month; dead zone 0.5 SD; pull bar WF > 67.5% & n >= 8; floors 8;
MIN_TRAIN 60; design sample = first 40% of the anchor frame; DECISION gate 0.45; sleeve 5% notional, static.

DECLARED RULES FOR MULTI-SECTOR RUNS (2026-09-13, before any second sector was run):
  R1  Anchor selection (step 4): among the four anchors on EITHER label (absolute or relative — extended by operator ruling 13 Sep after
      the Energy run), the one with the highest edge over the majority-class
      rate, subject to LB95 > 50%, n >= 60, two-sided (long share between 15% and 90%), and no calendar year with >= 8 calls below 50%
      (AMENDED 14 Sep, operator, after Consumer Discretionary: a year needs 8 calls to count, whichever end of the walk-forward it sits at —
      the same sample floor the type-pull rule uses; the original >= 4 disqualified an 87-month anchor on a 7-call partial first year).
      Ill-conditioned growth: an anchor whose denominator is the growth leg is INELIGIBLE if g10 sits at the 0.5%/yr floor in more than
      20% of the anchor frame (Energy-type cyclicality). If no anchor qualifies -> the sector is TYPE-INELIGIBLE: report, no Stage 3 verdict.
  R2  No-pull branch (step 5): if no type clears the pull bar, the type system is SILENT for the sector; the integrated instrument
      is then the second instrument alone, the sector is flagged TYPE-SILENT, and it cannot be sized (WATCH only).
  R3  Second instrument (step 6): the tier(s) of the type-agnostic run whose sequential OOS accuracy has Wilson LB95 > 50% with n >= 8,
      chosen by that rule, not by inspection. If none qualifies there is no second instrument.
  R4  Selection caveat: nine sectors x four anchors x full-record pull membership = many chances; the honest controls are the
      majority-class benchmark and the forward tape. Sector results are candidates until the tape resolves.
  R5  Portfolio: sector sleeves share a 15% total GROSS cap and are netted per bucket; a sleeve that fails the |corr| < 0.30 gate
      against the book, or adds no Sortino to the THROTTLED universe (the adopted form; amended 13 Sep after Consumer Discretionary
      passed on the unthrottled book grid while the throttled universe fell), is NOT admitted (reported).
  R5p PAIR RULE (13 Sep, after Energy): a relative-label sleeve is a long/short pair and costs TWO legs of gross. Every sector sleeve
      spends the same 5% of gross: a single-leg sleeve is 5% notional; a pair sleeve is 2.5% per leg (2.5% sector, 2.5% SPY netted
      into US_EQ). The 15% sector cap counts gross legs. No universe-cap allowance: in any week where adding the sleeve would push
      universe gross (netted gross x UNIVERSE_LEV) above the 6.0x cap, the sleeve is CLIPPED to zero for that week (counted, reported).
  R5s SHORT-ONLY OVERLAY RULE (declared 14 Sep, operator, after Technology): a sector instrument that ACTS (DECISION) but fails the
      R5 correlation gate, where the failure is on its LONG side — long-only stream corr >= +0.30 with the book AND short-only stream
      corr <= +0.30 — enters the book as a SHORT-ONLY OVERLAY: act on the instrument's SHORT calls only, single leg, 5% notional x lev,
      own bucket, counted against the 15% sector cap. Overlay admission: >= 15 short calls on the record, short-call accuracy above the
      down-rate of the window, no calendar year holding > 50% of the short calls, and a Sortino lift on the universe. The overlay is
      hedge-class and therefore UNTHROTTLED (like the 2Y hedge and gold ballast; a position that pays in stress is not flattened in
      stress); the throttled variant is reported beside it. Real capital 0% until the tape resolves, as for every sleeve.
  R6  Foreign / IFRS filers (no us-gaap net income) are dropped from the sector CAPE and LISTED in the report — never silently.
  R8  Integration (step 8-10, declared 28 Sep, AMENDED to PRUNE): pull > TIER > abstain. The post-type CASCADE is REMOVED entirely
      (not demoted). Cascade fails the LB95>50 admission bar every other source must clear (sector 52-57% LB 42-47%; monthly sleeves
      Gold 51.9 / Silver 50.0 / WTI 56.8, all sub-bar). Keeping it as last-resort scored a higher IN-SAMPLE block Sortino (7.83 vs
      5.79 pruned @2.5x) purely by diversifying coverage with coin-flip calls — the diversification-of-noise trap — so it is pruned
      on principle (operator, 28 Sep): a source below the admission bar does not emit. SHADOW SECTOR SYSTEM ONLY; live ZION book
      untouched (its monthly sleeves show the SAME weak cascade and are a separate prune candidate needing seq test + authorization).
  R9  Call-stability (step 8-10 + 13, declared 28 Sep): a STANDING DIAGNOSTIC that classifies each acted call straight / flip-once /
      flip-twice (a flip reverses the prior acted call; flip-twice = the prior call had also reversed = a whipsaw). OOS: straight 70.9%
      (LB 63.7), flip-once 69.0% (LB 50.8), flip-twice 50.0% (LB 23.7). The EMISSION filter R9_MODE controls whether flips abstain.
      TESTED per sector AND at the block: the filter LOWERED every sector's own Sortino and the block's (block @2.5x: keep-all 4.56 >
      drop-flip2 4.08 > straight 3.61; unanimous across all six sectors) — call accuracy is not portfolio contribution, and dropping
      calls loses diversifying coverage. So R9_MODE defaults to "off": the stability is flagged (a flip-twice current call raises a
      caution) but NOT filtered out. Left as a toggle for the tape to revisit, not a live filter.
"""
import sys, os, json, glob, time, gzip, urllib.request, warnings, importlib.util
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, "/Users/castaglia/Desktop/ZION"); sys.path.insert(0, "/Users/castaglia/Desktop/ZION/reports_gen")
import sector_recipe as SR, lib_pipeline as L, multiasset_pipeline as MP, gen_cassandra_prices as G
SCR = SR.SCR; DATA = os.path.join(HERE, "data")
ETF_NAME = {"XLK": "Information_Technology", "XLF": "Financials", "XLV": "Health_Care", "XLE": "Energy", "XLI": "Industrials", "XLP": "Consumer_Staples",
            "XLY": "Consumer_Discretionary", "XLB": "Materials", "XLU": "Utilities"}
UA = {"User-Agent": "ZOLTAR research (shaun@zoltarpredicts.com)", "Accept-Encoding": "gzip, deflate"}
R9_MODE = "off"   # 28 Sep: call-stability EMISSION filter. off = diagnostic only (DEFAULT — the filter lowered every sector's own Sortino and the block's, sweep-tested); "flip2" drops whipsaws only; "straight" acts on straight calls only. Diagnostic always prints.
W_HC = 0.05; W_PAIR = 0.025; UNIVERSE_LEV = 3.80; UNIVERSE_CAP = 6.0; HOUSE_CAP = 2.0; EXEC_LEV = 2.5; CAPITAL = 100000; SECTOR_TOTAL_CAP = 0.15
ANCHORS = {"PE": ("RealPrice", "E10"), "PE_G": ("CAPE10", "g10"), "P_G": ("RealPrice", "g10"), "E_G": ("E10", "g10")}
# R6b PREDECESSOR REGISTRANTS (declared 13 Sep): the SEC ticker map points at a successor CIK whose companyfacts hold only recent
# filings; the history lives under the predecessor CIK. Facts from both are merged (per period end, earliest filing wins). Every
# constituent with < 8 annual rows after the merge is listed in the report so this map can be extended BEFORE a sector is run.
PREDECESSOR = {"XOM": [34088], "APA": [6769], "BLK": [1364742], "APO": [1411494]}   # BLK: BlackRock Finance (2022 reorg); APO: Apollo Asset Management (2022 merger)


def sleeve_ret(c):
    """next-month return the sleeve earns per unit call: sector total return (absolute) or sector minus SPY (relative = long/short pair)."""
    r = c.px_adj.pct_change().shift(-1)
    return (r - c.spy_adj.pct_change().shift(-1).reindex(r.index)) if getattr(c, "rel", False) else r


def wlb95(p, n, z=1.96): return (p + z*z/(2*n) - z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)))/(1 + z*z/n) if n else 0.0


class Ctx:
    def __init__(self, tk, exclude=()):
        self.tk = tk; self.col, self.name = SR.SECTORS[tk]; self.exclude = list(exclude)
        self.out = os.path.join(HERE, "results", tk + ("_ex" + "_".join(x.replace("-", "") for x in self.exclude) if self.exclude else "")); os.makedirs(self.out, exist_ok=True)
        self.log = []; self.tables = {}; self.t0 = time.time()
        self.px_close = pd.read_csv(os.path.join(SCR, f"{tk}_daily.csv"), index_col=0, parse_dates=True)["Close"].resample("MS").first().dropna()
        self.px_adj = pd.read_csv(os.path.join(SCR, f"{tk}_daily.csv"), index_col=0, parse_dates=True)["Adj Close"].resample("MS").first().dropna()
        self.spy_close = pd.read_csv(os.path.join(SCR, "SPY_daily.csv"), index_col=0, parse_dates=True)["Close"].resample("MS").first().dropna()
        self.spy_adj = pd.read_csv(os.path.join(SCR, "SPY_daily.csv"), index_col=0, parse_dates=True)["Adj Close"].resample("MS").first().dropna()
    def say(self, s): print(s, flush=True); self.log.append(s)
    def need(self, cond, msg):
        if not cond: self.say(f"BLOCKED: {msg}"); raise SystemExit(f"[{self.tk}] BLOCKED: {msg}")
    def save(self, name, obj): json.dump(obj, open(os.path.join(self.out, name), "w"), indent=1, default=float)


# ---------------------------------------------------------------- step 1: data + legs
def s1_legs(c):
    legs = SR.sector_legs(c.tk); names, stat = SR.legs_meta(c.tk)
    fred = [(fid, nm, lag) for fid, (nm, lag, st) in SR.FRED[c.tk].items()]
    rows = [(nm, f"FRED {fid}", f"+{lag}", int(legs[nm].notna().sum()), str(legs.Date[legs[nm].first_valid_index()].date()) if legs[nm].notna().any() else "NONE") for fid, nm, lag in fred]
    for nm in (f"{c.tk}_DivYield", f"{c.tk}_RelSPY"): rows.append((nm, "Yahoo", "0", int(legs[nm].notna().sum()), str(legs.Date[legs[nm].first_valid_index()].date())))
    c.need(all(r[3] > 120 for r in rows), f"a leg has < 120 months: {[r for r in rows if r[3] <= 120]}")
    c.tables["legs"] = pd.DataFrame(rows, columns=["leg", "source", "lag_months", "n", "first"]); c.say(f"[1] legs OK: {len(rows)} sector legs + 9 macro (IndProd +2, M2 +1, CPI +2)")
    legs.to_csv(os.path.join(c.out, "legs.csv"), index=False)


# ---------------------------------------------------------------- step 2: constituents / PE list
def s2_constituents(c):
    f = glob.glob(os.path.join(DATA, "fundamentals", "lists", f"{c.tk}_*.csv")); c.need(f, "no constituent PE/PEG list — run build_pe_lists.py")
    c.cons = pd.read_csv(f[0])
    if c.exclude:
        c.cons = c.cons[~c.cons.ticker.isin(c.exclude)]; c.say(f"[2] SENSITIVITY RUN: excluded {c.exclude} from the sector CAPE (report-only; the standard run is the system)")
    c.say(f"[2] constituents: {len(c.cons)} names; sector median PE {c.cons.trailingPE.median():.1f}, median PEG {c.cons.pegRatio.median():.2f} (snapshot, peer medians only)")


# ---------------------------------------------------------------- step 3: XBRL -> sector CAPE
def _get(url):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60); b = r.read()
    return gzip.decompress(b) if r.headers.get("Content-Encoding") == "gzip" else b


def s3_cape(c):
    xp = os.path.join(DATA, "xbrl", f"{c.tk.lower()}_companyfacts.json"); os.makedirs(os.path.dirname(xp), exist_ok=True)
    if not os.path.exists(xp):
        ckp = os.path.join(DATA, "xbrl", "ticker_cik.json")
        if not os.path.exists(ckp):
            m = json.loads(_get("https://www.sec.gov/files/company_tickers.json")); json.dump({v["ticker"]: v["cik_str"] for v in m.values()}, open(ckp, "w"))
        cik = json.load(open(ckp)); out = {}; miss = []
        TAGS = ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "EarningsPerShareDiluted", "WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic", "CommonStockSharesOutstanding"]
        for tk in c.cons.ticker:
            ck = cik.get(tk) or cik.get(tk.replace("-", "."))
            if ck is None: miss.append(f"{tk}:no CIK"); continue
            cf = None
            for attempt in range(3):                                  # validated fetch: a partial response (seen on XOM) is retried
                try:
                    cf = json.loads(_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{ck:010d}.json"))
                    g0 = cf["facts"].get("us-gaap", {}); nrows = sum(len(v) for t in ("NetIncomeLoss", "ProfitLoss") for u in [g0.get(t, {}).get("units", {})] for v in u.values())
                    if nrows >= 8 or attempt == 2: break
                    time.sleep(2)
                except Exception as e:
                    cf = None; time.sleep(2)
            if cf is None: miss.append(f"{tk}:fetch failed"); continue
            facts_list = [cf["facts"]]
            for pck in PREDECESSOR.get(tk, []):                       # R6b: merge predecessor registrant history
                try: facts_list.append(json.loads(_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{pck:010d}.json"))["facts"]); time.sleep(0.15)
                except Exception as e: miss.append(f"{tk}:predecessor {pck} {str(e)[:30]}")
            rec = {"cik": ck, "name": cf.get("entityName"), "ifrs": "ifrs-full" in cf["facts"] and "us-gaap" not in cf["facts"], "merged_predecessors": PREDECESSOR.get(tk, [])}
            for tag in TAGS:
                rows_all = []
                for F in facts_list:
                    g = F.get("us-gaap", {})
                    if tag in g:
                        u = g[tag]["units"]; k = "USD" if "USD" in u else ("shares" if "shares" in u else list(u)[0]); rows_all += u[k]
                if rows_all: rec[tag] = rows_all
            dei = []
            for F in facts_list: dei += F.get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
            if dei: rec["dei_shares"] = dei
            out[tk] = rec; time.sleep(0.15)
        json.dump(out, open(xp, "w")); c.say(f"[3] XBRL pulled {len(out)} companies; missing: {miss or 'none'}")
    X = json.load(open(xp)); X = {k: v for k, v in X.items() if k in set(c.cons.ticker)}   # sensitivity exclusions apply to the CAPE build too
    pp = os.path.join(DATA, "xbrl", f"{c.tk.lower()}_constituent_monthly_close.csv")
    if not os.path.exists(pp):
        import yfinance as yf
        raw = yf.download(c.cons.ticker.tolist(), start="2005-01-01", interval="1mo", auto_adjust=False, progress=False, group_by="column", threads=True)
        raw["Close"].to_csv(pp)
    PX = pd.read_csv(pp, index_col=0, parse_dates=True)
    cpi = pd.read_csv(os.path.join(DATA, "fred_CPIAUCSL.csv")); cpi.columns = ["Date", "cpi"]; cpi["Date"] = pd.to_datetime(cpi.Date); CPI = cpi.set_index("Date")["cpi"].resample("MS").last().ffill()
    def annual(rows, lo=340, hi=380):
        o = {}
        for r in rows:
            if r.get("form") not in ("10-K", "10-K/A", "20-F", "40-F") or "start" not in r: continue
            dd = (pd.Timestamp(r["end"]) - pd.Timestamp(r["start"])).days
            if not (lo <= dd <= hi): continue
            end = pd.Timestamp(r["end"]); filed = pd.Timestamp(r["filed"])
            if end not in o or filed < o[end][1]: o[end] = (float(r["val"]), filed)
        return o
    def inst(rows):
        o = {}
        for r in rows:
            end = pd.Timestamp(r["end"]); filed = pd.Timestamp(r["filed"])
            if end not in o or filed < o[end][1]: o[end] = (float(r["val"]), filed)
        return o
    def annual_union(rec):
        """Annual net income from the UNION of the income tags (per period end; NetIncomeLoss preferred, then ProfitLoss, then
        NetIncomeLossAvailableToCommonStockholdersBasic). Booking (13 Sep): NetIncomeLoss held 3 annual rows, the other tags 20+."""
        out = {}
        for tag in ("NetIncomeLossAvailableToCommonStockholdersBasic", "ProfitLoss", "NetIncomeLoss"):
            for end, v in annual(rec.get(tag, [])).items(): out[end] = v          # later (preferred) tags overwrite
        return out
    EARN, SHR, dropped, short = {}, {}, [], []
    for tk, rec in X.items():
        ni = annual_union(rec)
        sh = (annual(rec.get("WeightedAverageNumberOfDilutedSharesOutstanding", [])) or annual(rec.get("WeightedAverageNumberOfSharesOutstandingBasic", []))
              or (inst(rec["dei_shares"]) if "dei_shares" in rec else {}) or inst(rec.get("CommonStockSharesOutstanding", [])))   # shares fallback chain (Erie: basic only)
        if ni and sh:
            EARN[tk] = ni; SHR[tk] = sh
            if len(ni) < 7: short.append(f"{tk}({len(ni)}y)")
        else: dropped.append(f"{tk}({'IFRS' if rec.get('ifrs') else 'no NI/shares'})")
    c.short_history = short; c.merged = [f"{tk}<-{rec['merged_predecessors']}" for tk, rec in X.items() if rec.get("merged_predecessors")]
    c.say(f"[3] earnings+shares for {len(EARN)} of {len(X)}; DROPPED (R6, listed): {dropped or 'none'}; predecessor histories merged (R6b): {c.merged or 'none'}; SHORT registrant history < 7y (excluded from E10 by the >= 7-year rule, listed — extend PREDECESSOR if a successor CIK): {short or 'none'}")
    usable = lambda d, t: sorted((e, v, f) for e, (v, f) in d.items() if f <= t)
    months = pd.date_range("2009-01-01", PX.index.max(), freq="MS"); rows = []
    for t in months:
        num = den10 = den5 = 0.0; n10 = n5 = 0; rby = {}
        for tk in EARN:
            if tk not in PX.columns or t not in PX.index or np.isnan(PX.at[t, tk]): continue
            e = usable(EARN[tk], t); s = usable(SHR[tk], t)
            if not e or not s: continue
            cap = PX.at[t, tk] * s[-1][1]; real = [(end, v / CPI.asof(end)) for end, v, f in e]
            if len(real[-10:]) >= 7:
                E10 = np.mean([v for _, v in real[-10:]])
                if E10 > 0: num += cap; den10 += E10; n10 += 1
            if len(real[-5:]) >= 4:
                E5 = np.mean([v for _, v in real[-5:]])
                if E5 > 0: den5 += E5; n5 += 1
            for end, v in real[-10:]: rby.setdefault(tk, {})[end.year] = v
        def trend(ny):
            """v1: log-linear trend of aggregate real earnings over the last ny fiscal years (balanced names).
            v2 FALLBACK (declared 13 Sep, Energy): when any window year's aggregate <= 0 the log trend is undefined ->
            annualised log ratio of the mean of the later half of the window to the mean of the earlier half (block means,
            cyclically adjusted in the CAPE sense); NaN if either block mean <= 0. Returns (value, version)."""
            cnt = {}
            for dct in rby.values():
                for y in dct: cnt[y] = cnt.get(y, 0) + 1
            yrs = sorted(y for y, k in cnt.items() if k >= 0.6 * max(1, len(rby)))[-ny:]
            if len(yrs) < max(4, ny - 2): return np.nan, "none"
            names = [tk for tk in rby if all(yy in rby[tk] for yy in yrs)]
            if len(names) < 8: return np.nan, "none"
            tot = np.array([sum(rby[tk][y] for tk in names) for y in yrs])
            if (tot > 0).all(): return np.polyfit(np.arange(len(yrs)), np.log(tot), 1)[0] * 100, "v1"
            h = len(tot) // 2; a, b = tot[:h].mean(), tot[h:].mean()
            if a <= 0 or b <= 0: return np.nan, "none"
            return np.log(b / a) / (len(tot) - h) * 100, "v2"
        (g10, g10v), (g5, g5v) = trend(10), trend(5); real_cap = num / CPI.asof(t) if num > 0 else np.nan
        cape10 = real_cap / den10 if den10 > 0 and n10 >= 8 else np.nan
        cape5 = np.nan
        if n5 >= 8:
            n5c = d5 = 0.0
            for tk in EARN:
                if tk not in PX.columns or np.isnan(PX.at[t, tk]): continue
                e = usable(EARN[tk], t); s = usable(SHR[tk], t)
                if not e or not s: continue
                rr = [v / CPI.asof(end) for end, v, f in e][-5:]
                if len(rr) >= 4 and np.mean(rr) > 0: n5c += PX.at[t, tk] * s[-1][1]; d5 += np.mean(rr)
            cape5 = (n5c / CPI.asof(t)) / d5 if d5 > 0 else np.nan
        rows.append(dict(Date=t, CAPE10=cape10, CAPE5=cape5, n10=n10, n5=n5, g10=g10, g5=g5, g10_version=g10v, RealPrice=real_cap if n10 >= 8 else np.nan, E10=den10 if n10 >= 8 else np.nan,
                         CAPEG=cape10 / max(g10, 0.5) if cape10 == cape10 and g10 == g10 else np.nan, CAPE5G=cape5 / max(g5, 0.5) if cape5 == cape5 and g5 == g5 else np.nan, mcap_bn=num / 1e9 if num else np.nan))
    S = pd.DataFrame(rows); capep = os.path.join(HERE, "results", f"{c.tk.lower()}{'_ex' if c.exclude else ''}_cape_monthly.csv"); S.to_csv(capep, index=False)
    SR._CAPE_OVERRIDE = capep                                            # sector_recipe.sector_legs reads THIS run's CAPE file for the legs (every run)
    v = S.dropna(subset=["CAPE10"]); c.need(len(v) >= 90, f"CAPE10 has only {len(v)} months")
    gfloor = float((S.dropna(subset=['g10']).g10 <= 0.5).mean()) if S.g10.notna().any() else 1.0
    v2share = float((S.loc[S.CAPE10.notna(), "g10_version"] == "v2").mean()); gnan = float(S.loc[S.CAPE10.notna(), "g10"].isna().mean())
    c.cape = S; c.gfloor = max(gfloor, gnan); c.dropped = dropped; c.gnote = f"g10 v2 (block-mean) fallback used in {v2share*100:.0f}% of CAPE months; g10 undefined in {gnan*100:.0f}%"
    last = S.dropna(subset=["CAPE10"]).iloc[-1]
    c.say(f"[3] CAPE10 {v.Date.min().date()}..{v.Date.max().date()} ({len(v)} mo), companies in aggregate {int(last.n10)} of {len(EARN)}; latest CAPE10 {last.CAPE10:.1f} CAPE5 {last.CAPE5:.1f} g10 {last.g10:.2f}%/yr ({last.g10_version}) CAPEG {last.CAPEG:.1f}; g10 at floor/undefined in {c.gfloor*100:.0f}% of months; {c.gnote}")
    c.tables["cape"] = pd.DataFrame([dict(item=k, value=round(float(last[k]), 2)) for k in ("CAPE10", "CAPE5", "g10", "g5", "CAPEG", "n10")])


# ---------------------------------------------------------------- step 4: ORACLE four anchors x two labels
def s4_oracle(c):
    S = c.cape.copy(); S["abs"] = c.px_close.reindex(S.Date).values; S["rel"] = (c.px_close / c.spy_close).reindex(S.Date).values
    SD = 0.5; MIN_TRAIN = 60
    def pc(x, N): r = np.full(len(x), np.nan); r[N:] = x[N:] / x[:-N] - 1; return r
    res = []
    for label in ("absolute", "relative"):
        S["out"] = S["abs"] if label == "absolute" else S["rel"]
        for name, (nn, dn) in ANCHORS.items():
            d = S[["Date", "out", nn, dn]].dropna().reset_index(drop=True)
            if len(d) < MIN_TRAIN + 24: res.append(dict(anchor=name, label=label, blocked=f"rows {len(d)}")); continue
            out = d.out.to_numpy(float); num = d[nn].to_numpy(float); den = d[dn].to_numpy(float); ratio = num / den
            nxt = np.sign(np.concatenate([out[1:] / out[:-1] - 1, [np.nan]])); cut = int(len(d) * 0.4); pre = np.arange(len(d)) < cut
            best, ba, sweep = 3, -1, {}
            for N in range(3, 13, 3):
                rd = np.sign(pc(ratio, N)); m = pre & (~np.isnan(rd)) & (~np.isnan(nxt)) & (rd != 0) & (nxt != 0)
                if m.sum() < 24: continue
                a = (rd[m] == nxt[m]).mean(); sweep[N] = a
                if a > ba: ba, best = a, N
            N = best; gr, gn, gd = pc(ratio, N), pc(num, N), pc(den, N); calls = []
            for t in range(cut, len(d)):
                if nxt[t] == 0 or np.isnan(nxt[t]) or np.isnan(gr[t]): continue
                tr = np.arange(0, t); tr = tr[(~np.isnan(gr[tr])) & (~np.isnan(gn[tr])) & (~np.isnan(gd[tr])) & (~np.isnan(nxt[tr])) & (nxt[tr] != 0)]
                if len(tr) < MIN_TRAIN: continue
                def tern(a):
                    mu = a[tr].mean(); sd = a[tr].std(); zz = (a - mu) / sd if sd > 0 else a * 0; r = np.zeros(len(a), int); r[zz > SD] = 1; r[zz < -SD] = -1; return r
                typ = (tern(gr) + 1) * 9 + (tern(gn) + 1) * 3 + (tern(gd) + 1); same = tr[typ[tr] == typ[t]]; seg = same if len(same) > 0 else tr
                pred = 1 if (nxt[seg] > 0).sum() >= (nxt[seg] < 0).sum() else -1; calls.append((d.Date[t], pred, nxt[t]))
            if not calls: res.append(dict(anchor=name, label=label, blocked="no calls")); continue
            cd = pd.DataFrame(calls, columns=["Date", "pred", "mkt"]); cd["hit"] = cd.pred == cd.mkt; n = len(cd); acc = cd.hit.mean(); up = (cd.mkt > 0).mean(); maj = max(up, 1 - up); ls = (cd.pred > 0).mean()
            years = {int(y): (float(g.hit.mean()), len(g)) for y, g in cd.groupby(cd.Date.dt.year)}
            bad_year = any(v[1] >= 8 and v[0] < 0.5 for v in years.values())   # R1 amended 14 Sep: a year counts only with >= 8 calls
            ill = dn == "g10" and c.gfloor > 0.20
            elig = (acc - maj > 0 and wlb95(acc, n) > 0.5 and n >= 60 and 0.15 <= ls <= 0.90 and not bad_year and not ill)   # R1 extended: both labels
            res.append(dict(anchor=name, label=label, N=N, n=n, acc=float(acc), lb=float(wlb95(acc, n)), up=float(up), majority=float(maj), edge=float(acc - maj), long=float(ls), years=years, bad_year=bad_year, ill_conditioned=ill, eligible=bool(elig), sweep={int(k): float(v) for k, v in sweep.items()}))
    c.save("oracle_anchors.json", res)
    ok = [r for r in res if r.get("eligible")]
    best = max(ok, key=lambda r: r["edge"]) if ok else None
    c.anchor = best["anchor"] if best else None; c.label = best["label"] if best else "absolute"; c.rel = (c.label == "relative")
    c.tables["anchors"] = pd.DataFrame([{k: r.get(k) for k in ("anchor", "label", "N", "n", "acc", "lb", "up", "majority", "edge", "long", "bad_year", "ill_conditioned", "eligible", "blocked")} for r in res])
    c.say(f"[4] ORACLE four anchors x two labels done; eligible: {[(r['anchor'], r['label']) for r in ok] or 'NONE'} -> selected anchor: {c.anchor or 'NONE (R1: TYPE-INELIGIBLE)'} on the {c.label.upper()} label" + (" -> the sleeve is a LONG/SHORT PAIR, sector vs SPY" if c.rel else ""))


# ---------------------------------------------------------------- steps 5-7: Stage 3 via multiasset_pipeline
def _panel_df(c):
    df = pd.read_csv(MP.PANEL); df["Date"] = pd.to_datetime(df["Date"])
    for col, lag in MP.PUB_LAG.items():
        if col in df.columns: df[col] = df[col].shift(lag)
    legs = SR.sector_legs(c.tk); df = df.merge(legs, on="Date", how="left")
    for col in ("RealPrice", "E10"): df = df.merge(c.cape[["Date", col]].rename(columns={col: f"{c.tk}_{col}"}), on="Date", how="left")
    df[f"{c.tk}_Close"] = df[c.col]
    if getattr(c, "rel", False):                                     # relative label: outcome = sector / SPY month-start price ratio
        df[f"{c.tk}_Close"] = df[c.col] / c.spy_close.reindex(df.Date).values
    df["CONST_A"] = 1.0; df["CONST_B"] = 1.0
    return df


def _mp_run(c, tag, num, den, extra, sd=0.5, pull_wf=0.675):
    MP.H = 1; MP.SD = sd; MP.PULL_WF = pull_wf; MP.REPORTS = os.path.join(c.out, f"stage3_{tag}"); os.makedirs(MP.REPORTS, exist_ok=True)
    df = _panel_df(c); frame = df.dropna(subset=[f"{c.tk}_Close", f"{c.tk}_CAPE10", f"{c.tk}_g10"]).reset_index(drop=True)
    cut = int(len(frame) * 0.4); MP.START = np.datetime64(frame.Date.iloc[cut])
    MP.EXTRA_CANDIDATES = extra; MP.ASSETS = {c.name.replace(" ", ""): dict(outcome=f"{c.tk}_Close", num=num, den=den, deflate=False, proposed=False, note=f"{tag}")}
    key = list(MP.ASSETS)[0]
    lines, tier_rows, summary, findings, art = MP.run_asset(key, df); MP.write_asset_files(key, lines, art)
    ML = pd.read_csv(os.path.join(MP.REPORTS, f"{key}_month_level.csv")); TT = pd.read_csv(os.path.join(MP.REPORTS, f"{key}_type_table.csv"))
    return dict(lines=lines, findings=findings, pulled=sorted(int(x) + 1 for x in art["pulled"]), ML=ML, TT=TT, key=key, start=str(frame.Date.iloc[cut].date()))


def s5_stage3(c):
    if c.anchor is None:
        # R1: TYPE-INELIGIBLE -> no anchored Stage 3. Run the anchored machinery on the best-edge anchor for the RECORD only
        # (its pulls are not admitted), mark the type system silent, continue with the second instrument alone (R2).
        best = max([r for r in json.load(open(os.path.join(c.out, "oracle_anchors.json"))) if "edge" in r], key=lambda r: r["edge"], default=None)
        c.anchor_record = best["anchor"] if best else "PE"; c.label = best["label"] if best else "absolute"; c.rel = (c.label == "relative"); c.say(f"[5] R1 TYPE-INELIGIBLE: no anchor admitted; Stage 3 run on {c.anchor_record} for the RECORD only (pulls not admitted); type system SILENT (R2)")
        nn, dn = ANCHORS[c.anchor_record]
    else:
        c.anchor_record = c.anchor; nn, dn = ANCHORS[c.anchor]
    sector_legs = [n for n in SR.legs_meta(c.tk)[0] if n not in (f"{c.tk}_{nn}", f"{c.tk}_{dn}")]
    c.extra = sector_legs + ["Term_Spread_10Y_3M", "VIX_Close"]
    r = _mp_run(c, "anchored", f"{c.tk}_{nn}", f"{c.tk}_{dn}", c.extra); c.s3 = r
    if c.anchor is None:
        r["pulled_record"] = list(r["pulled"]); r["pulled"] = []
        r["ML"].loc[r["ML"].status.isin(["pulled", "emitted"]), "status"] = "not-admitted"   # R1: type calls not admitted
    ML = r["ML"]; scored = ML[ML.scored == True]
    c.say(f"[5] Stage 3 ({c.anchor_record}{' RECORD-ONLY' if c.anchor is None else ''}) from {r['start']}: decision months {len(ML)}, scored {len(scored)}; types populated {int((r['TT'].n > 0).sum())}/27; PULLED {r['pulled'] or 'NONE'}{' (record-only pulls not admitted: ' + str(r.get('pulled_record')) + ')' if c.anchor is None else ''}; pulled months {int((ML.status=='pulled').sum())}, cascade-emitted {int((ML.status=='emitted').sum())}; audit {'clean' if not r['findings'] else r['findings']}")
    c.type_silent = (not r["pulled"]) or (c.anchor is None)
    if c.type_silent: c.say("[5] R2 NO-PULL BRANCH: type system SILENT for this sector -> integrated instrument = second instrument only; WATCH, cannot be sized")
    c.tables["types"] = r["TT"][["type", "signs", "n", "WF_pct", "LB", "UB", "zone", "pulled"]]


def s6_pretype(c):
    r = _mp_run(c, "pretype", "CONST_A", "CONST_B", [f"{c.tk}_CAPE10", f"{c.tk}_g10", f"{c.tk}_CAPEG"] + c.extra); c.pre = r
    ML = r["ML"]; em = ML[(ML.status == "emitted") & (ML.scored == True)] if "tier" in ML.columns else ML.iloc[0:0]; rows = []
    for tier, g in (em.groupby("tier") if len(em) else []):
        a = (g.predB == g.lab).mean(); rows.append(dict(tier=tier, n=len(g), acc=float(a), lb95=float(wlb95(a, len(g))), up=float((g.lab > 0).mean()), feature=g.primary.mode().iloc[0] if len(g) else ""))
    c.tables["pretype_tiers"] = pd.DataFrame(rows); c.second = [x["tier"] for x in rows if x["lb95"] > 0.5 and x["n"] >= 8]
    c.say(f"[6] pre-type (type-agnostic) tiers: " + "; ".join(f"{x['tier']} n{x['n']} {x['acc']*100:.0f}% LB{x['lb95']*100:.0f}" for x in rows) + f" -> second instrument (R3): {c.second or 'NONE'}")


def s7_sd(c):
    rows = []
    for sd in (0.25, 0.35, 0.5, 0.75, 1.0):
        try:
            r = c.s3 if sd == 0.5 else _mp_run(c, f"sd{sd}", f"{c.tk}_{ANCHORS[c.anchor_record][0]}", f"{c.tk}_{ANCHORS[c.anchor_record][1]}", c.extra, sd=sd)
            ML = r["ML"]; pu = ML[(ML.status == "pulled") & (ML.scored == True)]; sc = ML[ML.scored == True]
            rows.append(dict(SD=sd, types=int((r["TT"].n > 0).sum()), pulled=len(r["pulled"]), pull_months=len(pu), pull_acc=float((pu.base_dir == pu.lab).mean()) if len(pu) else None, scored=len(sc)))
        except SystemExit: raise
        except Exception as e: rows.append(dict(SD=sd, error=str(e)[:60]))
    c.tables["sd"] = pd.DataFrame(rows); c.say("[7] dead-zone sensitivity (report-only): " + "; ".join(f"SD{x['SD']}: pulled {x.get('pulled')} ({x.get('pull_months')} mo @ {x['pull_acc']*100:.0f}%)" if x.get('pull_acc') is not None else f"SD{x['SD']}: {x.get('pulled', x.get('error'))}" for x in rows))


# ---------------------------------------------------------------- steps 8-10: convergence, integration, abstentions
def s8_s10_integrate(c):
    A = c.s3["ML"].copy(); P = c.pre["ML"].copy()
    for col in ("base_dir", "predB"):
        if col not in A.columns: A[col] = 0.0
    A["type_call"] = np.where(A.status == "pulled", A.base_dir, np.where(A.status == "emitted", A.predB, 0)).astype(float)
    A["type_state"] = np.where(A.status == "pulled", "pull", np.where(A.status == "emitted", "remainder-cascade", np.where(A.reason == "train<MIN_TRAIN", "warm-up", "abstain")))
    if "tier" not in P.columns: P["tier"] = ""
    if "predB" not in P.columns: P["predB"] = 0.0
    P["tier_call"] = np.where((P.status == "emitted") & (P.tier.isin(c.second)), P.predB, 0).astype(float)
    J = A[["date", "lab", "scored", "type_call", "type_state"]].merge(P[["date", "tier_call", "tier"]], on="date", how="outer").sort_values("date"); J = J[J.scored == True].copy(); J["lab"] = J.lab.astype(int)
    def state(r):
        t, s = r.type_call, r.tier_call
        if t and s: return "CONVERGE" if t == s else "DIVERGE"
        return "TYPE only" if t else ("TIER only" if s else "NEITHER")
    J["state"] = J.apply(state, axis=1); rows = []
    for st in ("CONVERGE", "DIVERGE", "TYPE only", "TIER only", "NEITHER"):
        g = J[J.state == st]; n = len(g)
        if not n: rows.append(dict(state=st, n=0)); continue
        act = np.where(g.type_call != 0, g.type_call, g.tier_call); aa = (act == g.lab).mean() if st != "NEITHER" else np.nan
        rows.append(dict(state=st, n=n, up=float((g.lab > 0).mean()), act_acc=None if st == "NEITHER" else float(aa), lb95=None if st == "NEITHER" else float(wlb95(aa, n))))
    c.tables["states"] = pd.DataFrame(rows)
    def integ(r):                                                    # R8 (28 Sep, amended): cascade PRUNED — pull > TIER > abstain (cascade fails the LB95>50 bar; removed, not demoted)
        if r.type_call and r.type_state == "pull": return r.type_call, "type-pull"
        if r.tier_call and r.type_state != "warm-up": return r.tier_call, "second-instrument"
        return 0.0, "abstain"
    J[["call", "source"]] = J.apply(lambda r: pd.Series(integ(r)), axis=1); J = J.sort_values("date").reset_index(drop=True)
    # STANDING CASCADE DIAGNOSTIC + R9 (28 Sep, operator): classify each acted call's stability (straight / flip-once / flip-twice) on the
    # RAW call sequence, report per-category next-month OOS accuracy, THEN act only on STRAIGHT calls (R9: flip-once / flip-twice -> abstain).
    prev = []; fcl = []
    for cv in J.call.values:
        if cv == 0 or not np.isfinite(cv): fcl.append(""); continue
        if len(prev) < 1: fcl.append("straight")
        elif len(prev) < 2: fcl.append("straight" if cv == prev[-1] else "flip1")
        else: fcl.append("straight" if cv == prev[-1] else ("flip1" if prev[-1] == prev[-2] else "flip2"))
        prev.append(cv)
    J["flipcat"] = fcl; draw = J[J.call != 0]; hbd = (draw.call == draw.lab).astype(int)
    by_flip = {k: [int((draw.flipcat == k).sum()), float(hbd[draw.flipcat == k].mean()) if (draw.flipcat == k).any() else None, float(wlb95(hbd[draw.flipcat == k].mean(), int((draw.flipcat == k).sum()))) if (draw.flipcat == k).any() else None] for k in ("straight", "flip1", "flip2")}
    c.flip_series = J.set_index("date").flipcat; c.raw_acted = list(zip(draw.date.values, draw.call.values.astype(int)))   # raw (pre-R9) for s13
    _drop = {"off": [], "flip2": ["flip2"], "straight": ["flip1", "flip2"]}.get(R9_MODE, [])   # R9 emission filter (default OFF)
    if _drop:
        fm = J.flipcat.isin(_drop); J.loc[fm, "source"] = "abstain-flip"; J.loc[fm, "call"] = 0.0
    c.J = J
    a = J[J.call != 0]; win = J[J.type_state != "warm-up"]; n = len(a); acc = (a.call == a.lab).mean() if n else np.nan
    c.integrated = dict(acted=n, scored=len(win), acc=float(acc) if n else None, lb95=float(wlb95(acc, n)) if n else None, up_acted=float((a.lab > 0).mean()) if n else None, up_window=float((win.lab > 0).mean()), long=float((a.call > 0).mean()) if n else None,
                        long_n=int((a.call > 0).sum()), long_up=float((a[a.call > 0].lab > 0).mean()) if (a.call > 0).any() else None, short_n=int((a.call < 0).sum()), short_down=float((a[a.call < 0].lab < 0).mean()) if (a.call < 0).any() else None,
                        by_source={s: [len(g), float((g.call == g.lab).mean())] for s, g in a.groupby("source")}, by_year={int(y): [float((g.call == g.lab).mean()), len(g)] for y, g in a.groupby(pd.to_datetime(a.date).dt.year)})
    c.integrated["by_flip"] = by_flip
    ab = win[win.call == 0]; r = sleeve_ret(c); ab_ret = r.reindex(pd.to_datetime(ab.date)).mean() * 100 if len(ab) else np.nan
    c.abst = dict(genuine=len(ab), up=int((ab.lab > 0).sum()), down=int((ab.lab < 0).sum()), mean_next_ret_pct=float(ab_ret) if ab_ret == ab_ret else None, warmup=int((J.type_state == "warm-up").sum()))
    J.to_csv(os.path.join(c.out, "integrated_ledger.csv"), index=False); c.save("integrated.json", dict(integrated=c.integrated, abstentions=c.abst))
    I = c.integrated; c.say(f"[8-10] integrated: acted {I['acted']}/{I['scored']} acc {I['acc']*100 if I['acc'] else float('nan'):.1f}% LB95 {I['lb95']*100 if I['lb95'] else 0:.1f}% up-rate window {I['up_window']*100:.0f}% long {I['long']*100 if I['long'] is not None else 0:.0f}% | sources {I['by_source']} | abstentions {c.abst['genuine']} ({c.abst['up']} up / {c.abst['down']} down, mean next {c.abst['mean_next_ret_pct']}), warm-up {c.abst['warmup']}")
    bf = c.integrated["by_flip"]; c.say("[8-10] call-stability (OOS next-month): " + " | ".join(f"{k} n{v[0]} {v[1]*100:.0f}% LB{v[2]*100:.0f}" for k, v in bf.items() if v[1] is not None) + "  (flip-twice = whipsaw)")
    # money test
    d = pd.to_datetime(win.date); rr = r.reindex(d).values; calls = win.call.values; rs = c.spy_adj.pct_change().shift(-1).reindex(d).values
    def st(x): x = np.asarray(x, float); x = x[~np.isnan(x)]; nn = len(x); cg = np.prod(1 + x) ** (12 / nn) - 1; dn = x[x < 0]; so = (x.mean() * 12) / (dn.std(ddof=1) * np.sqrt(12)) if len(dn) > 1 else np.nan; eq = np.cumprod(1 + x); return float(cg), float(so), float((eq / np.maximum.accumulate(eq) - 1).min())
    lab = "sector-minus-SPY pair" if c.rel else "sector"
    c.tables["money"] = pd.DataFrame([dict(strategy=k, CAGR=v[0], Sortino=v[1], MaxDD=v[2]) for k, v in ((f"constant long {lab}", st(rr)), ("buy&hold SPY", st(rs)), (f"integrated two-sided on {lab}, flat on abstain", st(calls * rr)), (f"integrated long/flat on {lab}", st(np.where(calls > 0, 1, 0) * rr)))])


# ---------------------------------------------------------------- step 11: engines + DECISION
def s11_decision(c):
    if c.integrated["acted"] == 0:
        c.decision = dict(note="no acted months — nothing to decide"); c.say("[11] DECISION: no instrument acted -> nothing to decide (sector WATCH-NONE)"); return
    names = SR.install(c.tk, relative=getattr(c, "rel", False)); d = L.load_asset(c.col, 1998, extra_vars=names, exclude_vars=[] if c.tk == "XLB" else ["Copper_Close"], h_label=1)
    rd = np.zeros(len(d)); J = c.J[c.J.call != 0]
    for r in J.itertuples():
        i = np.where(d.Date.values == np.datetime64(pd.Timestamp(r.date)))[0]
        if len(i): rd[i[0]] = r.call
    eng = L.engines(d); dec = L.decision(d, rd, eng); mkt = d["mkt"].values; acted = [i for i in range(len(d)) if rd[i] != 0 and not np.isnan(mkt[i]) and mkt[i] != 0]
    sd_ = eng["sdir"]; od = eng["odir"]; agree = [i for i in acted if sd_[i] == rd[i]]; dis = [i for i in acted if sd_[i] != 0 and sd_[i] != rd[i]]
    c.decision = dict(rd_acc=float(dec["rd_acc"]), rd_n=int(dec["rd_n"]), rd_lb=float(dec["rd_lb"]), conv_acc=float(dec["conv_acc"]) if dec["conv_n"] else None, conv_n=int(dec["conv_n"]), conv_lb=float(dec["conv_lb"]), acts=bool(dec["acts"] or dec["rd_lb"] > L.GATE),
                      sanct_agree=len(agree), sanct_dis=len(dis), sanct_dis_integrated_acc=float(np.mean([rd[i] == mkt[i] for i in dis])) if dis else None, ody_emits=int(sum(od[i] != 0 for i in acted)),
                      cur=dict(date=str(d.Date.iloc[-1].date()), ody=int(od[-1]), sanct=int(sd_[-1])))
    c.save("decision.json", c.decision); D = c.decision
    c.say(f"[11] DECISION: integrated test {D['rd_acc']*100:.1f}% (n {D['rd_n']}, LB {D['rd_lb']:.2f}); SANCTUARY-converged {D['conv_acc']*100 if D['conv_acc'] else float('nan'):.1f}% (n {D['conv_n']}, LB {D['conv_lb']:.2f}) -> {'ACTS' if D['acts'] else 'ABSTAIN'}; SANCTUARY opposes {D['sanct_dis']} months (integrated {D['sanct_dis_integrated_acc']*100 if D['sanct_dis_integrated_acc'] is not None else float('nan'):.0f}% there); ODYSSEY emits {D['ody_emits']}")


# ---------------------------------------------------------------- step 12: relative label (driver)
def s12_relative(c):
    try:
        res = SR.run_full(c.tk, relative=True); c.rel_log = res["log"]; c.rel_verdict = res["verdict"]
    except Exception as e:
        c.rel_log = [f"relative driver failed: {e}"]; c.rel_verdict = "FAILED"
    c.say(f"[12] relative-label driver verdict: {c.rel_verdict}")


# ---------------------------------------------------------------- step 13: current month + tape
def s13_tape(c):
    A = c.s3["ML"]; cur = A.iloc[-1]; P = c.pre["ML"]; pc_ = P.iloc[-1]
    tcall = "ABSTAIN" if cur.status not in ("pulled", "emitted") else ("UP" if (cur.get("base_dir", 0) if cur.status == "pulled" else cur.get("predB", 0)) > 0 else "DOWN")
    scall = "silent" if not (pc_.status == "emitted" and str(pc_.get("tier", "")) in c.second) else ("UP" if pc_.get("predB", 0) > 0 else "DOWN")
    # R8 (28 Sep): priority pull > TIER > cascade — a genuine type-pull leads; else the second-instrument tier; else a cascade emission as last resort
    pull_call = tcall if cur.status == "pulled" else "ABSTAIN"; casc_call = tcall if cur.status == "emitted" else "ABSTAIN"
    if pull_call != "ABSTAIN": integ = pull_call
    elif scall != "silent": integ = scall.upper()
    else: integ = "ABSTAIN"   # R8 amended: cascade PRUNED (casc_call no longer emits)
    if getattr(c, "rel", False) and integ in ("UP", "DOWN"): integ = {"UP": "LONG_REL (long sector / short SPY)", "DOWN": "SHORT_REL (short sector / long SPY)"}[integ]
    # current-call stability (STANDING DIAGNOSTIC) + R9: classify vs the prior two RAW acted calls; act ONLY on straight
    flipcat = "straight"
    if integ in ("UP", "DOWN") or (getattr(c, "rel", False) and integ.startswith(("LONG", "SHORT"))):
        cur_sign = 1 if integ.startswith(("UP", "LONG")) else -1
        prev = [s for _, s in getattr(c, "raw_acted", [])][-2:]
        if len(prev) >= 2: flipcat = "straight" if cur_sign == prev[-1] else ("flip1" if prev[-1] == prev[-2] else "flip2")
        elif len(prev) == 1: flipcat = "straight" if cur_sign == prev[-1] else "flip1"
        _drop = {"off": [], "flip2": ["flip2"], "straight": ["flip1", "flip2"]}.get(R9_MODE, [])
        if flipcat in _drop:
            c.say(f"[13] R9 ({R9_MODE}): current call {integ} is {flipcat.upper()} -> ABSTAIN"); integ = "ABSTAIN"
        elif flipcat == "flip2": c.say(f"[13] NOTE: current call {integ} is FLIP-TWICE (whipsaw, ~50% OOS) — FLAGGED, not filtered (R9 off; the filter hurt every sector)")
    c.current = dict(decision_row=str(cur.date), type_call=tcall, type=f"T{int(cur.typ)+1}" if cur.typ >= 0 else "untyped", type_status=str(cur.status), second=scall, second_tier=str(pc_.get("tier", "")), integrated=integ, stability=flipcat)
    tape = pd.DataFrame([dict(issued=pd.Timestamp.today().strftime("%Y-%m-%d"), decision_row=cur.date, horizon_months=1, label=c.label, integrated_call=integ, type_call=tcall, type_cell=c.current["type"], second_call=scall, anchor=c.anchor, pulled_types=",".join(f"T{t}" for t in c.s3["pulled"]), px=float(c.px_adj.iloc[-1]), resolves=(pd.Timestamp(cur.date) + pd.DateOffset(months=2)).strftime("%Y-%m-01"), outcome="")])
    tp = os.path.join(c.out, f"{c.tk}_forward_tape.csv")
    if os.path.exists(tp): old = pd.read_csv(tp); tape = pd.concat([old, tape], ignore_index=True)
    tape.to_csv(tp, index=False); c.say(f"[13] current ({cur.date}): type {tcall} ({c.current['type']}, {cur.status}); second {scall}; INTEGRATED {integ}; tape row written")


# ---------------------------------------------------------------- step 14: CASSANDRA
def s14_cassandra(c):
    p = c.px_close.to_numpy(float); spot = float(p[-1]); core = G.build_ticker(c.tk, p, spot); rets = G.analogue_returns(p, 1)
    nxt = sleeve_ret(c) * 100; hist = nxt.iloc[:-1].dropna(); J = c.J
    call = 1 if c.current["integrated"].startswith(("UP", "LONG")) else (-1 if c.current["integrated"].startswith(("DOWN", "SHORT")) else 0)
    def band(r):
        r = np.asarray(r, float); r = r[~np.isnan(r)]
        if len(r) < 5: return None
        lo, md, hi = np.percentile(r, [10, 50, 90]); return dict(n=int(len(r)), up=float((r > 0).mean()), p10=float(lo), p50=float(md), p90=float(hi), price_p10=spot * (1 + lo / 100), price_p50=spot * (1 + md / 100), price_p90=spot * (1 + hi / 100))
    bands = {"statistical (all months)": band(hist), "analogue pool": band(rets) if len(rets) else None}
    if call: bands[f"call-conditioned ({'UP' if call>0 else 'DOWN'} calls)"] = band(nxt.reindex(pd.to_datetime(J[J.call == call].date)))
    c.cass = dict(spot=spot, call=c.current["integrated"], basis=("relative: bands are sector-minus-SPY next-month excess return; prices assume SPY unchanged" if c.rel else "absolute"), analogue_n=int(len(rets)), builder=dict(p10=core["p10"], p50=core["p50"], p90=core["p90"], method=core.get("method")), bands={k: v for k, v in bands.items() if v})
    c.save("cassandra.json", c.cass); c.say(f"[14] CASSANDRA: spot ${spot:.2f}, analogues {len(rets)} ({'VETO -> cell-conditioned' if len(rets)==0 else 'analogue band'}); " + "; ".join(f"{k}: p50 ${v['price_p50']:.2f} ({v['p50']:+.1f}%)" for k, v in c.cass["bands"].items()))


# ---------------------------------------------------------------- steps 15-16: sizing + portfolio shadow
def s15_s16_portfolio(c):
    if c.type_silent or c.integrated["acted"] == 0:
        c.say("[15-16] R2: type-silent / no-instrument sector -> WATCH only, not sized"); c.sizing = c.port = None
        c.save("portfolio.json", dict(sizing=None, portfolio=None, note="not sized (type-silent / no instrument)")); return
    J = c.J[c.J.type_state != "warm-up"]; r = sleeve_ret(c); sleeve = pd.Series(J.call.values * r.reindex(pd.to_datetime(J.date)).values, index=pd.to_datetime(J.date).dt.strftime("%Y-%m"))
    B = pd.read_csv("/Users/castaglia/Desktop/ZION/weekly/unified/reports/universe_monthly_backtest.csv").set_index("month"); ov = B.index.intersection(sleeve.index); b = B.loc[ov, "uni_1x"]; s = sleeve.loc[ov].fillna(0)
    def st(x): x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); cg = np.prod(1 + x) ** (12 / n) - 1; dn = x[x < 0]; so = (x.mean() * 12) / (dn.std(ddof=1) * np.sqrt(12)) if len(dn) > 1 else np.nan; eq = np.cumprod(1 + x); return float(cg), float(so), float((eq / np.maximum.accumulate(eq) - 1).min())
    corr = float(np.corrcoef(s, b)[0, 1]); wts = (0, 0.0125, 0.025, 0.05) if c.rel else (0, 0.025, 0.05, 0.10)
    grid = [(w, *st(b + w * s)) for w in wts]                       # R5p: pair weights are per leg (half the single-leg grid)
    admit = abs(corr) < 0.30 and grid[2][2] > grid[0][2]
    wlab = "2.5% per leg (5% gross, R5p pair)" if c.rel else "5% notional"
    c.sizing = dict(corr_book=corr, sleeve=st(s), book=st(b), grid=grid, admit=bool(admit), recommendation=(f"{wlab} overlay, 0% real capital until tape" if admit else "NOT admitted (R5): " + ("|corr| >= 0.30" if abs(corr) >= 0.30 else "no Sortino lift")))
    c.tables["sizing"] = pd.DataFrame([dict(weight=(f"{w*100:.2f}% per leg ({w*200:.0f}% gross)" if c.rel else f"{w*100:.1f}%"), CAGR=cg, Sortino=so, MaxDD=dd) for w, cg, so, dd in grid])
    c.say(f"[15] sizing: corr(sleeve, book) {corr:+.2f}; sleeve Sortino {c.sizing['sleeve'][1]:.2f}; book Sortino {grid[0][2]:.2f} -> +5% {grid[2][2]:.2f} -> {c.sizing['recommendation']}")
    Lg = pd.read_csv("/Users/castaglia/Desktop/ZION/weekly/unified/reports/netting_ledger.csv", parse_dates=["week"]); pos_m = dict(zip(pd.to_datetime(c.J.date).dt.strftime("%Y-%m"), c.J.call))
    W = W_PAIR if c.rel else W_HC
    Lg["m"] = Lg.week.dt.strftime("%Y-%m"); Lg["pos"] = Lg.m.map(pos_m).fillna(0.0); Lg["onoff"] = (Lg.thr >= 1.0).astype(float); Lg["SLEEVE"] = W * Lg.pos * Lg.lev * Lg.onoff; Lg["gross_new"] = Lg.gross + Lg.SLEEVE.abs()
    if c.rel:   # long/short pair: the SPY leg nets into the US_EQ bucket
        Lg["gross_new"] = Lg.gross - Lg.US_EQ.abs() + (Lg.US_EQ - Lg.SLEEVE).abs() + Lg.SLEEVE.abs()
    clip = (Lg.SLEEVE != 0) & (Lg.gross_new * UNIVERSE_LEV > UNIVERSE_CAP) & (Lg.gross * UNIVERSE_LEV <= UNIVERSE_CAP + 1e-9)   # R5p clip: sleeve caused the breach
    Lg.loc[clip, "SLEEVE"] = 0.0; Lg["gross_new"] = Lg.gross + Lg.SLEEVE.abs() if not c.rel else Lg.gross - Lg.US_EQ.abs() + (Lg.US_EQ - Lg.SLEEVE).abs() + Lg.SLEEVE.abs()
    c.clipped_weeks = int(clip.sum()); c.base_breach_weeks = int((Lg.gross * UNIVERSE_LEV > UNIVERSE_CAP).sum())
    cur = Lg.iloc[-1]; sign = 1 if c.current["integrated"].startswith(("UP", "LONG")) else (-1 if c.current["integrated"].startswith(("DOWN", "SHORT")) else 0)
    expo = W * sign * cur.lev * (1.0 if cur.thr >= 1 else 0.0); last = float(pd.read_csv(os.path.join(SCR, f"{c.tk}_daily.csv"), index_col=0)["Close"].iloc[-1]); spy_last = float(pd.read_csv(os.path.join(SCR, "SPY_daily.csv"), index_col=0)["Close"].iloc[-1])
    # universe with the sleeve: throttled (adopted form) and unthrottled, monthly 1x, same window as the sleeve
    first = Lg.groupby("m").first(); months = [m for m in sleeve.index if m in B.index and m in first.index]
    def useries(throttled):
        return pd.Series([W * first.loc[m, "lev"] * (1.0 if (first.loc[m, "thr"] >= 1.0 or not throttled) else 0.0) * sleeve.get(m, 0.0) for m in months], index=months)
    base = B.loc[months, "uni_1x"]; ut = base + useries(True) / 1.0; uu = base + useries(False)
    wl = "2.5%/leg pair" if c.rel else "5%"
    c.tables["universe"] = pd.DataFrame([dict(universe_1x=k, CAGR=v[0], Sortino=v[1], MaxDD=v[2]) for k, v in (("no sleeve", st(base)), (f"+ {c.name} {wl}, throttled", st(ut)), (f"+ {c.name} {wl}, unthrottled", st(uu)))])
    # ---- R5s short-only overlay: triggered when the full instrument fails R5 on its LONG side
    c.overlay = None
    if not c.sizing["admit"] and abs(corr) >= 0.30:
        J2 = c.J[c.J.type_state != "warm-up"]; rr2 = r.reindex(pd.to_datetime(J2.date)).values; idx2 = pd.to_datetime(J2.date).dt.strftime("%Y-%m")
        lo = pd.Series(np.where(J2.call.values > 0, 1, 0) * rr2, index=idx2).loc[ov].fillna(0); so_ = pd.Series(np.where(J2.call.values < 0, -1, 0) * rr2, index=idx2).loc[ov].fillna(0)
        c_long = float(np.corrcoef(lo, b)[0, 1]); c_short = float(np.corrcoef(so_, b)[0, 1])
        if c_long >= 0.30 and c_short <= 0.30:
            sc = J2[J2.call < 0]; n_s = len(sc); acc_s = float((sc.call == sc.lab).mean()) if n_s else 0.0
            down_rate = float((J2.lab < 0).mean()); yrs = pd.to_datetime(sc.date).dt.year.value_counts(); maxyr = float(yrs.max() / n_s) if n_s else 1.0
            first = Lg.groupby("m").first() if "Lg" in dir() else None
            # universe with the short-only overlay (unthrottled = declared form; throttled reported)
            Lg0 = pd.read_csv("/Users/castaglia/Desktop/ZION/weekly/unified/reports/netting_ledger.csv", parse_dates=["week"]); Lg0["m"] = Lg0.week.dt.strftime("%Y-%m"); f0 = Lg0.groupby("m").first()
            months = [m for m in so_.index if m in B.index and m in f0.index]; base0 = B.loc[months, "uni_1x"]
            def ov_series(throttled): return pd.Series([W_HC * f0.loc[m, "lev"] * (1.0 if (f0.loc[m, "thr"] >= 1.0 or not throttled) else 0.0) * so_.get(m, 0.0) for m in months], index=months)
            u_un = base0 + ov_series(False); u_th = base0 + ov_series(True); lift_un = st(u_un)[1] - st(base0)[1]
            admit_ov = n_s >= 15 and acc_s > down_rate and maxyr <= 0.50 and lift_un > 0
            c.overlay = dict(trigger=True, corr_long=c_long, corr_short=c_short, n_short=n_s, acc_short=acc_s, down_rate_window=down_rate, max_year_share=maxyr,
                             sleeve_short=st(so_), grid=[(w, *st(b + w * so_)) for w in (0, 0.025, 0.05, 0.10)],
                             universe=dict(base=st(base0), unthrottled=st(u_un), throttled=st(u_th)), admit=bool(admit_ov),
                             recommendation=("SHORT-ONLY OVERLAY admitted: 5% notional on short calls, unthrottled, 0% real capital until tape" if admit_ov else
                                             "short-only overlay NOT admitted: " + "; ".join(x for x, ok in ((f"n_short {n_s} < 15", n_s < 15), (f"short acc {acc_s:.0%} <= down-rate {down_rate:.0%}", acc_s <= down_rate), (f"max-year share {maxyr:.0%} > 50%", maxyr > 0.5), (f"universe lift {lift_un:+.2f} <= 0", lift_un <= 0)) if ok)))
            c.tables["overlay_sizing"] = pd.DataFrame([dict(weight=f"{w*100:.1f}%", CAGR=cg, Sortino=so, MaxDD=dd) for w, cg, so, dd in c.overlay["grid"]])
            c.tables["overlay_universe"] = pd.DataFrame([dict(universe_1x=k, CAGR=v[0], Sortino=v[1], MaxDD=v[2]) for k, v in (("no overlay", st(base0)), (f"+ {c.name} short-only 5%, unthrottled (declared form)", st(u_un)), (f"+ {c.name} short-only 5%, throttled (reported)", st(u_th)))])
            c.say(f"[15s] R5s TRIGGERED: long-only corr {c_long:+.2f}, short-only corr {c_short:+.2f}; short calls {n_s} @ {acc_s:.0%} vs window down-rate {down_rate:.0%}, max-year {maxyr:.0%}; universe unthrottled lift {lift_un:+.2f} -> {c.overlay['recommendation']}")
            c.say("   overlay universe 1x: " + " | ".join(f"{r_.universe_1x}: CAGR {r_.CAGR*100:.2f}% Sortino {r_.Sortino:.2f} MaxDD {r_.MaxDD*100:.2f}%" for r_ in c.tables["overlay_universe"].itertuples()))
    lift = st(ut)[1] - st(base)[1]
    if lift <= 0 and c.sizing["admit"]:
        c.sizing["admit"] = False; c.sizing["recommendation"] = f"NOT admitted (R5): throttled-universe Sortino lift {lift:+.2f} <= 0"; c.say(f"[16] R5: throttled-universe Sortino lift {lift:+.2f} <= 0 -> NOT admitted")
    c.sizing["throttled_lift"] = float(lift)
    c.port = dict(gross_max=float(Lg.gross_new.max()), gross_mean=float(Lg.gross_new.mean()), uni_gross_max=float(Lg.gross_new.max() * UNIVERSE_LEV), active_weeks=int((Lg.pos != 0).sum()), clipped_weeks=c.clipped_weeks, base_book_breach_weeks=c.base_breach_weeks,
                  ticket=dict(week=str(cur.week.date()), exposure=float(expo), notional=float(CAPITAL * EXEC_LEV * expo), shares=int(round(CAPITAL * EXEC_LEV * expo / last)), price=last,
                              spy_leg_shares=(int(round(-CAPITAL * EXEC_LEV * expo / spy_last)) if c.rel else 0), spy_price=spy_last), sector_cap_note=f"R5: all sector sleeves share a {SECTOR_TOTAL_CAP*100:.0f}% notional cap")
    c.save("portfolio.json", dict(sizing=c.sizing, portfolio=c.port, overlay=c.overlay)); Lg[["week", "lev", "thr", "gross", "pos", "SLEEVE", "gross_new"]].to_csv(os.path.join(c.out, "shadow_netting_ledger.csv"), index=False)
    c.say(f"[16] portfolio shadow: netted gross max {c.port['gross_max']:.2f}x (house cap {HOUSE_CAP}x {'ok' if c.port['gross_max']<=HOUSE_CAP else 'BREACH'}), universe @3.8x max {c.port['uni_gross_max']:.2f}x; ticket {c.port['ticket']['shares']} sh {c.tk}" + (f" / {c.port['ticket']['spy_leg_shares']:+d} sh SPY (pair)" if c.rel else "") + f" exposure {expo:+.4f} (${c.port['ticket']['notional']:,.0f} at $100k@2.5x)")
    c.say("   universe 1x: " + " | ".join(f"{r.universe_1x}: CAGR {r.CAGR*100:.2f}% Sortino {r.Sortino:.2f} MaxDD {r.MaxDD*100:.2f}%" for r in c.tables["universe"].itertuples()))


# ---------------------------------------------------------------- report
def report(c):
    def tbl(df):
        if df is None or len(df) == 0: return "_(none)_\n"
        cols = list(df.columns); out = "| " + " | ".join(str(x) for x in cols) + " |\n|" + "---|" * len(cols) + "\n"
        for _, r in df.iterrows(): out += "| " + " | ".join(("" if (isinstance(v, float) and np.isnan(v)) else (f"{v:.3f}" if isinstance(v, float) else str(v))) for v in r.values) + " |\n"
        return out
    I = getattr(c, "integrated", {}); D = getattr(c, "decision", {}); md = [f"# Sector Method — {c.name} ({c.tk}) — runner report {pd.Timestamp.today().date()}\n",
          f"Procedure: `sector_runner.py {c.tk}` (steps 1–16, constants fixed, rules R1–R6 in the script header). Runtime {time.time()-c.t0:.0f}s.\n",
          "## Step log\n" + "\n".join(f"- {l}" for l in c.log) + "\n", "## 1. Legs\n" + tbl(c.tables.get("legs")), "## 3. Sector CAPE (latest)\n" + tbl(c.tables.get("cape")) + f"\nDropped constituents (R6): {getattr(c,'dropped',[]) or 'none'}; short-history (< 7y, excluded from E10): {getattr(c,'short_history',[]) or 'none'}; {getattr(c,'gnote','')}; g10 at floor/undefined in {getattr(c,'gfloor',0)*100:.0f}% of months.\n",
          f"## 4. Stage-1 anchors (R1 selection, both labels) — selected: **{getattr(c, 'anchor', None)}** on the **{getattr(c, 'label', 'absolute')}** label\n" + tbl(c.tables.get("anchors"))]
    if hasattr(c, "s3"):
        md += [f"## 5. Stage 3 on {getattr(c,'anchor_record',None)}{' (RECORD ONLY — type-ineligible, pulls not admitted: ' + str(c.s3.get('pulled_record')) + ')' if c.anchor is None else ''} — 27 types (pulled = {c.s3['pulled'] or 'NONE'})\n" + tbl(c.tables.get("types")), "## 6. Pre-type tiers (R3 second instrument = " + (", ".join(getattr(c, 'second', [])) or "none") + ")\n" + tbl(c.tables.get("pretype_tiers")), "## 7. Dead-zone sensitivity (report-only)\n" + tbl(c.tables.get("sd")),
               "## 8. Joint states\n" + tbl(c.tables.get("states")), "## 9–10. Integrated instrument\n" + f"```\n{json.dumps(I, indent=1, default=float)}\n```\nAbstentions: `{json.dumps(getattr(c, 'abst', {}))}`\n\n" + tbl(c.tables.get("money")),
               "## 11. Engines + DECISION\n" + f"```\n{json.dumps(D, indent=1, default=float)}\n```\n", "## 12. Relative label (driver)\n```\n" + "\n".join(getattr(c, "rel_log", [])) + "\n```\n", f"## 13. Current month\n`{json.dumps(getattr(c,'current',{}))}`\n",
               "## 14. CASSANDRA\n```\n" + json.dumps(getattr(c, "cass", {}), indent=1, default=float) + "\n```\n", "## 15. Sizing\n" + (tbl(c.tables.get("sizing")) + f"\n{c.sizing['recommendation'] if getattr(c, 'sizing', None) else 'not sized'}\n"), "## 15s. R5s short-only overlay\n" + (tbl(c.tables.get("overlay_sizing")) + "\n" + tbl(c.tables.get("overlay_universe")) + f"\n{c.overlay['recommendation']}\n" if getattr(c, "overlay", None) else "_(not triggered)_\n") + "## 16. Portfolio shadow\n" + tbl(c.tables.get("universe")) + "\n```\n" + json.dumps(getattr(c, "port", None), indent=1, default=float) + "\n```\n"]
    open(os.path.join(c.out, "REPORT.md"), "w").write("\n".join(md)); c.say(f"REPORT written: {os.path.join(c.out, 'REPORT.md')}")


def main():
    tk = sys.argv[1]; excl = sys.argv[sys.argv.index("--exclude") + 1].split(",") if "--exclude" in sys.argv else []
    c = Ctx(tk, excl); c.say(f"=== SECTOR RUNNER {tk} {c.name}{' EX ' + ','.join(excl) if excl else ''} === {pd.Timestamp.now()}")
    steps = [s1_legs, s2_constituents, s3_cape, s4_oracle, s5_stage3, s6_pretype, s7_sd, s8_s10_integrate, s11_decision, s12_relative, s13_tape, s14_cassandra, s15_s16_portfolio]
    try:
        for f in steps: f(c)
    except SystemExit as e:
        c.say(str(e))
    finally:
        report(c)


if __name__ == "__main__":
    main()

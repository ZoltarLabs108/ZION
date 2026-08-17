"""
ZION — clean MCP server (v2, 2026-08-17; design: serve/MCP_SERVER_GUIDE.md).

READ-ONLY, SERVES ARTIFACTS. Never recomputes, never writes, never runs pipelines (launchd owns
execution). As-issued rows verbatim. Every payload carries its caveats. Three namespaces:
weekly (locked book, positions), universe (tape, netting, ZION-vs-LIVE), monthly (board, book).

  pip install "mcp[cli]" pandas numpy
  claude mcp add zion -- python /Users/castaglia/Desktop/ZION/serve/zion_mcp.py

v2 supersedes the 2026-08 monthly-only server: hardcoded WEIGHTS removed (book metrics come from
the SYZYGY artifact book_ledger.csv), NatGas added as WATCH-ONLY, weekly/universe/compare added.
"""
import os
import numpy as np
import pandas as pd
try:                                      # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:                       # mcp 1.x
    from mcp.server.fastmcp import FastMCP

ROOT = os.environ.get("ZION_ROOT", os.path.expanduser("~/Desktop/ZION"))
REP = os.path.join(ROOT, "reports")
U = os.path.join(ROOT, "weekly", "unified", "reports")
WK = os.path.join(ROOT, "weekly")
ASSETS = ["SPY", "Gold", "Silver", "WTI", "USD"]          # SYZYGY book sleeves
WATCH_ONLY = {"NatGas": "monthly OOS 58.8%, Wilson-LB .478 < .50 gate — tracked, never sized"}
STALE_DAYS = 8                                              # > one missed Friday job

mcp = FastMCP("zion")


def _p(*parts):
    return os.path.join(*parts)


def _read(path):
    return pd.read_csv(path) if os.path.exists(path) else None


def _age_days(path):
    if not os.path.exists(path): return None
    import time
    return max(0, int((time.time() - os.path.getmtime(path)) / 86400))


def _stale_banner():
    """Freshness contract: WARN loudly if the Friday job appears to have missed."""
    warn = []
    for f in ("netting_ledger.csv", "universe_forward_tape.csv"):
        a = _age_days(_p(U, f))
        if a is None: warn.append(f"MISSING artifact: {f}")
        elif a > STALE_DAYS: warn.append(f"STALE artifact: {f} is {a}d old (Friday job may have missed)")
    return ("\n".join("** " + w + " **" for w in warn) + "\n") if warn else ""


# ======================= status / recipes =======================
def status_impl():
    rows = []
    for label, path in [("weekly netting ledger", _p(U, "netting_ledger.csv")),
                        ("universe forward tape", _p(U, "universe_forward_tape.csv")),
                        ("zion-vs-live ledger", _p(U, "zion_vs_live_ledger.csv")),
                        ("monthly sleeve ledger", _p(REP, "per_sleeve_ledger.csv")),
                        ("monthly book ledger", _p(REP, "book_ledger.csv")),
                        ("NatGas watch ledger", _p(REP, "NatGas_month_level.csv"))]:
        a = _age_days(path)
        rows.append(f"  {label:24s} {'MISSING' if a is None else f'{a}d old'}")
    return _stale_banner() + "ZION artifact freshness (read-only server; launchd job com.zoltar.zion.universe runs Fri 17:30):\n" + "\n".join(rows)


def recipes_impl(cadence="all"):
    m = {"all": _p(ROOT, "RECIPES_INDEX.md"),
         "weekly": _p(WK, "ZION_WEEKLY_RECIPE.md"),
         "monthly": _p(ROOT, "monthly", "FINAL_MONTHLY_RECIPE_snapshot_20260817.md")}
    path = m.get(cadence.strip().lower())
    if path is None or not os.path.exists(path):
        return f"unknown/missing cadence '{cadence}'. Options: all, weekly, monthly. (Daily lives in AEGIS, out of ZION scope by design.)"
    return open(path).read()


# ======================= weekly =======================
def weekly_book_spec_impl():
    return open(_p(ROOT, "weekly/unified/LOCKED_BOOK_SPEC_20260816.md")).read()


def weekly_positions_impl():
    d = _read(_p(U, "netting_ledger.csv"))
    if d is None: return "netting_ledger.csv missing — run the Friday job."
    r = d.iloc[-1]
    lines = [f"# ZION weekly/universe as-issued exposures — week {r['week']}",
             f"  US_EQ {r['US_EQ']:+.3f}  NASDAQ {r['NASDAQ']:+.3f}  GOLD {r['GOLD']:+.3f}  "
             f"SILVER {r['SILVER']:+.3f}  WTI {r['WTI']:+.3f}  UST2Y {r['UST2Y']:+.3f}",
             f"  throttle {r['thr']:.2f}   netted gross {r['gross']:.2f}x (house cap 2.0x)",
             "rules: Amendment 2 (positions persist to next gated decision; FLAT while throttle stressed);",
             "       20% 2Y hedge + 7.5% gold always-on; 5% silver micro episodic; lev 1.190x to 10% DD cap.",
             "CAVEAT: backtest Sortino 2.82 weekly / 4.71 universe is PROVISIONAL until 12 resolved tape weeks."]
    return _stale_banner() + "\n".join(lines)


# ======================= universe =======================
def universe_tape_impl():
    d = _read(_p(U, "universe_forward_tape.csv"))
    if d is None: return "tape missing."
    res = d[d["status"] == "RESOLVED"]
    rr = pd.to_numeric(res["realized_ret"], errors="coerce").dropna()
    lines = [f"# UNIVERSE forward tape (as-issued, append-only) — {len(d)} rows, {len(res)} resolved",
             f"evidence window: {len(rr)}/12 resolved weeks (BINDING gate before capital; ~mid-Nov 2026)"]
    for _, r in d.iterrows():
        tail = f"realized {float(r['realized_ret'])*100:+.2f}%" if str(r["status"]) == "RESOLVED" else "open"
        lines.append(f"  {r['week_ending']}  [{r['status']:8s}] US_EQ {r['US_EQ']:+.2f} NASDAQ {r['NASDAQ']:+.2f} "
                     f"GOLD {r['GOLD']:+.2f} SILVER {r['SILVER']:+.2f} UST2Y {r['UST2Y']:+.2f} "
                     f"gross {r['gross']:.2f}x  {tail}")
    if len(rr):
        lines.append(f"forward record: {(rr > 0).mean()*100:.0f}% positive, cum {(np.prod(1+rr)-1)*100:+.2f}%")
    lines.append("NOTE: row 1 (2026-08-07) is a PIT-reconstruction; true as-issued from 2026-08-14 on.")
    return _stale_banner() + "\n".join(lines)


def zion_vs_live_impl():
    d = _read(_p(U, "zion_vs_live_ledger.csv"))
    if d is None: return "comparison ledger missing."
    lines = [f"# ZION vs LIVE — standing weekly comparison ({len(d)} trade weeks; verdicts need 12 resolved)"]
    for _, r in d.sort_values("trade_week").iterrows():
        z = f"{float(r['zion_ret'])*100:+.2f}%" if pd.notna(r.get("zion_ret")) else "open"
        l = f"{float(r['live_ret'])*100:+.2f}%" if pd.notna(r.get("live_ret")) else "open"
        lines.append(f"  {str(r['trade_week'])[:10]}  ZION gross {r.get('zion_gross', float('nan')):.2f}x "
                     f"vs LIVE gross {r.get('live_gross', float('nan')):.2f}x   z_ret {z}  l_ret {l}")
    res = d.dropna(subset=["zion_ret", "live_ret"])
    if len(res):
        zc = (1 + res["zion_ret"]).prod() - 1; lc = (1 + res["live_ret"]).prod() - 1
        lines.append(f"cumulative ({len(res)} resolved): ZION {zc*100:+.2f}% vs LIVE {lc*100:+.2f}% | "
                     f"ZION wins {(res['zion_ret'] > res['live_ret']).sum()}/{len(res)}")
    lines.append("CAVEAT: live side recomputed from Yahoo closes; AEGIS settlement tapes are the live book's official record.")
    return _stale_banner() + "\n".join(lines)


def universe_book_spec_impl():
    return open(_p(ROOT, "weekly/unified/ZION_UNIVERSE_BOOK_20260816.md")).read()


# ======================= monthly =======================
def _sleeve_ledger():
    d = _read(_p(REP, "per_sleeve_ledger.csv"))
    if d is None: return None
    d["date"] = pd.to_datetime(d["date"])
    d = d[d.variant == "without_cells"].copy()
    d["sleeve"] = d["sleeve"].replace({"SP500": "SPY", "S&P500": "SPY"})
    return d


def monthly_board_impl():
    d = _sleeve_ledger()
    if d is None: return "per_sleeve_ledger.csv missing."
    lines = ["# ZION monthly board (last-produced artifacts — NOT a live recompute)"]
    for a in ASSETS:
        s = d[d.sleeve == a].sort_values("date")
        if not len(s): lines.append(f"  {a:7s} no ledger rows"); continue
        r = s.iloc[-1]
        call = {1: "UP (long)", -1: "DOWN (short)", 0: "ABSTAIN"}[int(r.position)]
        lines.append(f"  {a:7s} latest {r['date'].date()}  T{int(r.typ)}  {r.status:8s} -> {call}")
    ng = _read(_p(REP, "NatGas_month_level.csv"))
    if ng is not None and len(ng):
        ngr = ng.iloc[-1]
        lines.append(f"  NatGas  latest {str(ngr.get('date', '?'))[:10]}  status={ngr.get('status', '?')}  "
                     f"** WATCH-ONLY: {WATCH_ONLY['NatGas']} **")
    lines.append("Silver/WTI/USD ride PROPOSED (unconfirmed) anchor ratios — treat as tentative.")
    return "\n".join(lines)


def monthly_book_impl(leverage=1.0):
    d = _read(_p(REP, "book_ledger.csv"))
    if d is None: return "book_ledger.csv missing."
    r = pd.to_numeric(d["book_r_base"], errors="coerce").dropna().to_numpy() * float(leverage)
    eq = np.cumprod(1 + r); cagr = eq[-1] ** (12 / len(r)) - 1
    dn = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2)); sortino = float(np.mean(r) / dn * np.sqrt(12)) if dn > 0 else float("nan")
    mdd = float((eq / np.maximum.accumulate(eq) - 1).min())
    return (f"# ZION monthly SYZYGY book @ {leverage:g}x (from book_ledger.csv artifact, equal-weight-of-covering-sleeves)\n"
            f"  n={len(r)} months  CAGR {cagr*100:.2f}%  Sortino {sortino:.2f}  MaxDD {mdd*100:.1f}%\n"
            f"  (universe = this book x the weekly locked book, 50/50 — see universe_book_spec)\n"
            f"  CAVEAT: 1x-flat, uncosted; Sortino is leverage-invariant; NatGas NOT in this book (watch-only).")


# ======================= tool registrations =======================
@mcp.tool()
def status() -> str:
    """Artifact freshness for every served file; warns loudly if the Friday job missed."""
    return status_impl()


@mcp.tool()
def recipes(cadence: str = "all") -> str:
    """The ZION recipes: 'all' = the cross-cadence index; 'weekly' / 'monthly' = full recipe text.
    Daily is out of ZION scope by design (AEGIS owns it)."""
    return recipes_impl(cadence)


@mcp.tool()
def weekly_book_spec() -> str:
    """The LOCKED weekly book spec verbatim (config, Amendments 1-2, gates, caveats)."""
    return weekly_book_spec_impl()


@mcp.tool()
def weekly_positions() -> str:
    """Latest as-issued per-instrument exposures (netting ledger last row) + throttle + gross."""
    return weekly_positions_impl()


@mcp.tool()
def universe_tape() -> str:
    """The universe book's as-issued forward tape, verbatim, with the 12-week evidence count."""
    return universe_tape_impl()


@mcp.tool()
def zion_vs_live() -> str:
    """The standing weekly ZION-vs-LIVE ticket comparison ledger with cumulative record."""
    return zion_vs_live_impl()


@mcp.tool()
def universe_book_spec() -> str:
    """The ZION-universe combined book spec verbatim (weekly x monthly 50/50, netting, gates)."""
    return universe_book_spec_impl()


@mcp.tool()
def monthly_board() -> str:
    """Per-asset latest monthly calls (SYZYGY sleeves + NatGas watch-only), from artifacts."""
    return monthly_board_impl()


@mcp.tool()
def monthly_book(leverage: float = 1.0) -> str:
    """SYZYGY monthly book metrics from the book ledger artifact (no hardcoded weights)."""
    return monthly_book_impl(leverage)


if __name__ == "__main__":
    mcp.run()

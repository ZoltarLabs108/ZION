"""
ZION monthly — MCP server (read-only). Serves the LAST-PRODUCED monthly board:
per-asset predictive types (WF acc + Wilson bounds), each asset's current monthly call,
and the SYZYGY book (locked weights, live positions, base/levered metrics).

  pip install "mcp[cli]" pandas numpy
  python /Users/castaglia/Desktop/ZION/serve/zion_mcp.py            # stdio
  # register (Claude Code):
  claude mcp add zion -- python /Users/castaglia/Desktop/ZION/serve/zion_mcp.py

NOTE: this serves the artifacts of the last analysis run — it does NOT recompute live.
Live emission (HYPERION->ORACLE nightly) is a separate, deferred stage. Silver/WTI legs
ride PROPOSED (unconfirmed) ratios; the server flags that.
"""
import os, glob, pandas as pd, numpy as np
from mcp.server.fastmcp import FastMCP

ROOT    = os.environ.get("ZION_ROOT", os.path.expanduser("~/Desktop/ZION"))
REP     = os.path.join(ROOT, "reports", "multiasset")
SEARCH  = [REP, os.path.join(ROOT, "reports", "reddawn"), os.path.join(ROOT, "reports")]
ASSETS  = ["SPY", "Gold", "Silver", "WTI", "USD"]
WEIGHTS = {"SPY": 0.50, "Gold": 0.20, "Silver": 0.15, "WTI": 0.15, "USD": 0.0}
PROPOSED = {"Silver", "WTI", "USD"}                       # ratios not yet operator-confirmed
mcp = FastMCP("zion-monthly")

def _find(*names):
    for d in SEARCH:
        for nm in names:
            p = os.path.join(d, nm)
            if os.path.exists(p): return p
    return None

def _type_table(asset):
    aliases = [asset] + (["SP500", "S&P500"] if asset == "SPY" else [])
    p = _find(*[f"{a}_type_table.csv" for a in aliases])
    return pd.read_csv(p) if p else None

def _ledger():
    p = _find("per_sleeve_ledger.csv")
    if not p: return None
    d = pd.read_csv(p); d["date"] = pd.to_datetime(d["date"])
    d = d[d.variant == "without_cells"].copy()
    d["sleeve"] = d["sleeve"].replace({"SP500": "SPY", "S&P500": "SPY"})
    return d

def _latest(asset, led=None):
    d = _ledger() if led is None else led
    if d is None: return None
    s = d[d.sleeve == asset].sort_values("date")
    return s.iloc[-1] if len(s) else None

def _norm(asset):
    for a in ASSETS:
        if asset.strip().lower() == a.lower(): return a
    return asset

@mcp.tool()
def zion_assets() -> str:
    """The five ZION assets: book weight, predictive-type count, and latest monthly call."""
    led = _ledger(); out = []
    for a in ASSETS:
        tt = _type_table(a); r = _latest(a, led)
        npred = int((tt.zone == "PREDICTIVE").sum()) if tt is not None else "?"
        call = "n/a"
        if r is not None:
            call = {1: "UP (long)", -1: "DOWN (short)", 0: "ABSTAIN"}[int(r.position)]
        star = " *PROPOSED-ratio" if a in PROPOSED else ""
        dt = r["date"].date() if r is not None else "?"
        out.append(f"{a:6s} w={WEIGHTS[a]:.2f}  predictive_types={npred}  latest={dt}  call={call}{star}")
    return "\n".join(out)

@mcp.tool()
def zion_asset(asset: str) -> str:
    """One asset in detail: its predictive standing-rule types (WF acc + Wilson LB/UB) and the current call."""
    asset = _norm(asset); tt = _type_table(asset)
    lines = [f"# ZION {asset}  (book weight {WEIGHTS.get(asset, 0):.2f})"]
    if asset in PROPOSED:
        lines.append("  ** predictor ratio is PROPOSED / not operator-confirmed — treat as tentative **")
    if tt is not None:
        pred = tt[tt.pulled == True].sort_values("WF_pct", ascending=False)
        lines.append("predictive standing-rule types (pulled: WF>67.5% & n>=8):")
        for _, x in pred.iterrows():
            lines.append(f"  T{int(x.type):<2} {str(x.signs):12s} n={int(x.n):<4} "
                         f"WF={x.WF_pct:.1f}%  LB={x.LB:.1f} UB={x.UB:.1f}  [{x.zone}]")
        if len(pred) == 0:
            lines.append("  (none clear the bar — asset ABSTAINS at type level)")
    else:
        lines.append("  (type table not in board dir; call is from the sleeve ledger)")
    r = _latest(asset)
    if r is not None:
        call = {1: "UP (go long)", -1: "DOWN (go short)", 0: "ABSTAIN (flat/cash)"}[int(r.position)]
        lines.append(f"\nLATEST {r['date'].date()}: current type T{int(r.typ)}, status={r.status} -> CALL: {call}")
    else:
        lines.append(f"\nunknown asset '{asset}'. Known: {', '.join(ASSETS)}")
    return "\n".join(lines)

@mcp.tool()
def zion_book(leverage: float = 1.0) -> str:
    """The SYZYGY book: locked SPY-anchored weights, live per-sleeve positions, base/levered metrics.
    Sortino is leverage-invariant; leverage scales CAGR and drawdown."""
    d = _ledger()
    if d is None: return "sleeve ledger not found under reports/."
    piv = d.pivot_table(index="date", columns="sleeve", values="monthly_return", aggfunc="sum").fillna(0.0)
    for s in WEIGHTS:
        if s not in piv: piv[s] = 0.0
    book = (sum(piv[s] * w for s, w in WEIGHTS.items()).sort_index()) * leverage
    r = book.to_numpy(float); eq = np.cumprod(1 + r)
    cagr = eq[-1] ** (12 / len(r)) - 1
    dn = r[r < 0]; dd = np.sqrt((dn ** 2).mean()) if len(dn) else 1e-9
    sortino = r.mean() / dd * np.sqrt(12)
    peak = np.maximum.accumulate(eq); mdd = ((eq - peak) / peak).min()
    lines = [f"# ZION BOOK  ({leverage:g}x)  weights: " + ", ".join(f"{k} {v:.2f}" for k, v in WEIGHTS.items()),
             f"full-record: CAGR {cagr*100:.2f}%  {r.mean()*100:+.2f}%/mo  "
             f"Sortino {sortino:.2f} (down-month)  MaxDD {mdd*100:.1f}%  n={len(r)}",
             "latest positions:"]
    for a in ASSETS:
        rr = _latest(a, d)
        if rr is not None:
            c = {1: "LONG", -1: "SHORT", 0: "flat"}[int(rr.position)]
            lines.append(f"  {a:6s} w={WEIGHTS[a]:.2f}  {c}  (T{int(rr.typ)}, {rr.status})")
    lines.append("NOTE: last-produced board, not a live recompute. Silver/WTI/USD ride PROPOSED ratios.")
    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run()

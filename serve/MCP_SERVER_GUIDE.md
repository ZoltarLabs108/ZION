# ZION → clean MCP server: directions (2026-08-17)

## What exists now
`serve/zion_mcp.py` — read-only FastMCP server for the **monthly board only** (per-asset type
tables, monthly calls, SYZYGY book). **STALE in three ways:** (1) hardcoded `WEIGHTS 50/20/15/15`
predate the current book; (2) knows nothing of the weekly unified/locked book, the universe book,
the forward tape, the netting ledger, or the ZION-vs-LIVE comparison; (3) `ASSETS` lacks NatGas
(watch-only). It still works for what it covers.

## Design rules for the clean server (inherit these, they are house law)
1. **Read-only, serves artifacts.** The server never recomputes and never writes — it reads the
   files the pipelines produced (`reports/`, `weekly/unified/reports/`). Live computation belongs
   to the launchd job; the server is a window, not a runner ("routines observe, never re-run").
2. **As-issued discipline.** Tape/ledger rows are served verbatim; no reconstruction of history.
3. **Honest labels.** Every payload carries its caveat fields (watch-only flags, PROVISIONAL
   status, evidence-window counts) — the numbers never travel without their asterisks.

## The clean server: one server, three cadence namespaces
Extend `serve/zion_mcp.py` (or create `serve/zion_mcp2.py` and retire the old after parity):

```python
mcp = FastMCP("zion")
U = os.path.join(ROOT, "weekly", "unified", "reports")

@mcp.tool()   # ---- WEEKLY ----
def weekly_book_spec() -> str:
    """LOCKED_BOOK_SPEC_20260816.md verbatim (config, Amendments 1-2, caveats)."""
    return open(os.path.join(ROOT, "weekly/unified/LOCKED_BOOK_SPEC_20260816.md")).read()

@mcp.tool()
def weekly_positions() -> dict:
    """Latest as-issued exposures = last row of netting_ledger.csv (per-bucket net, throttle, gross)."""
    d = pd.read_csv(os.path.join(U, "netting_ledger.csv")); return d.iloc[-1].to_dict()

@mcp.tool()   # ---- UNIVERSE ----
def universe_tape() -> list[dict]:
    """Forward tape verbatim (ISSUED/RESOLVED rows) + evidence-window count (n/12)."""
    d = pd.read_csv(os.path.join(U, "universe_forward_tape.csv")); return d.to_dict("records")

@mcp.tool()
def zion_vs_live() -> list[dict]:
    """Standing weekly comparison ledger (trade-week aligned, both tickets, resolved returns)."""
    d = pd.read_csv(os.path.join(U, "zion_vs_live_ledger.csv")); return d.to_dict("records")

@mcp.tool()   # ---- MONTHLY (port the existing tools, fix staleness) ----
def monthly_board() -> dict: ...       # existing logic; ASSETS += NatGas w/ watch_only=True;
                                       # drop hardcoded WEIGHTS -> read from syzygy artifacts

@mcp.tool()   # ---- RECIPES ----
def recipes(cadence: str = "all") -> str:
    """RECIPES_INDEX.md, or the weekly/monthly recipe text on request."""
```

## Registration
```bash
pip install "mcp[cli]" pandas numpy
claude mcp add zion -- python /Users/castaglia/Desktop/ZION/serve/zion_mcp.py
```
(For claude.ai/desktop: same command via its MCP config; stdio transport, no network needed.)

## Freshness contract
The server is only as fresh as the last Friday job. Add a `status()` tool returning the mtimes of
`netting_ledger.csv` / `universe_forward_tape.csv` and WARN if > 8 days old (job missed) — the
HAL-freshness pattern: stale artifact → say so loudly, never serve silently stale data as current.

## Explicitly out of scope
Daily (AEGIS/GREEK_WATCH owns it — a ZION server must not re-serve another system's tapes) and
any tool that *runs* pipelines (that's launchd's job; an MCP "run" tool would double-execute and
violate the no-duplicate-runner rule).

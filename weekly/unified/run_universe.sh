#!/bin/zsh
# com.zoltar.zion.universe — Friday post-close: refresh panel -> issue exposures -> resolve matured
PY=/Users/castaglia/Desktop/HYACINTH/venv/bin/python3
export ZION_LEV=2.5        # LADDER: 2.5 now -> 3.2 (~wk6, clean gates) -> 4.0 (~wk12 review). See spec.
export ZION_CAPITAL=100000 # operator: set to actual account capital
U=/Users/castaglia/Desktop/ZION/weekly/unified
WT=/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly
TS=$(date +%Y%m%d_%H%M)
echo "=== universe run $TS ==="
echo "--- [1/3] refresh weekly panel ---";        (cd "$WT" && $PY build_weekly_panel.py)  || echo "PANEL REFRESH FAILED (continuing on stale panel)"
echo "--- [2/3] netting ledger + tape issue ---"; (cd "$U"  && $PY netting_ledger.py)       || echo "NETTING LEDGER FAILED"
echo "--- [3/3] resolve matured issues ---";      (cd "$U"  && $PY universe_tape_resolve.py) || echo "RESOLVER FAILED"

echo "--- [4/8] paper Mon-close rule ---";        (cd "$U"  && $PY paper_monclose.py)        || echo "PAPER MON-CLOSE FAILED"
echo "--- [5/8] ZION vs LIVE comparison ---";     (cd "$U"  && $PY zion_vs_live.py)          || echo "COMPARISON FAILED"
echo "--- [6/8] forward Sortino reconcile ---";   (cd "$U"  && $PY forward_sortino.py)       || echo "FORWARD SORTINO FAILED"
echo "--- [7/8] ZION desk ticket ---";            (cd "$U"  && $PY zion_desk_ticket.py)      || echo "TICKET FAILED"
echo "--- [8/8] fills reconcile (read-only) ---"; (cd "$U"  && $PY zion_reconcile.py)        || echo "RECONCILE SKIPPED (token/creds — see output)"
echo "=== done $TS ==="

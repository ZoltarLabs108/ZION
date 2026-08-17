#!/bin/zsh
# com.zoltar.zion.universe — Friday post-close: refresh panel -> issue exposures -> resolve matured
PY=/Users/castaglia/Desktop/HYACINTH/venv/bin/python3
U=/Users/castaglia/Desktop/ZION/weekly/unified
WT=/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly
TS=$(date +%Y%m%d_%H%M)
echo "=== universe run $TS ==="
echo "--- [1/3] refresh weekly panel ---";        (cd "$WT" && $PY build_weekly_panel.py)  || echo "PANEL REFRESH FAILED (continuing on stale panel)"
echo "--- [2/3] netting ledger + tape issue ---"; (cd "$U"  && $PY netting_ledger.py)       || echo "NETTING LEDGER FAILED"
echo "--- [3/3] resolve matured issues ---";      (cd "$U"  && $PY universe_tape_resolve.py) || echo "RESOLVER FAILED"
echo "=== done $TS ==="

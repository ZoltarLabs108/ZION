# PHASE: SYZYGY — RECIPE STEP 11 · 11b · 12 (book netting + DD-cap + USD overlay)
Tier:    AUTO   (once a sleeve is built)
Worktree: ZION_SYZYGY   Branch: syzygy-dev
Owns:    ZION assembly — aligns direction + magnitude into the emitted book; the portfolio layer

## CONTRACT (the handoff)
IN   ← MIMESIS: the per-asset certified signals / as-issued tickets (all assets).
OUT  → RECAL: the netted book — per-instrument NETTED exposure with weight caps, DD-cap applied,
              USD overlay attached. Frozen as `book_net_exposure.csv` / final_portfolio output.
GATE :  book == tape (no drift between assembled book and the as-issued tickets); net ledger;
        2.0× gross cap on NET; DD-cap 6%.

## ACTIONS  (in order)
1. **SYZYGY netting (11)** — combine per-asset signals; NET per-instrument (not projection);
   cap on the NET exposure (naive per-ticket sizing = ~4x intended — must net).
2. **DD-cap (11b)** — apply the 6% drawdown cap in final_portfolio.
3. **Terminal USD overlay (12)** — `overlay = −k·(spy_dir + gold_dir)·DXY` (SPY+Gold anchor ladder
   ±2..∓2; net-long → short-USD); **k TRAIN-calibrated** (declared TILT, not a hedge). Per-month
   `USD_tilt` through the current month; sign 100%.

## DIAGNOSTICS
- pass criterion: book == tape; net ledger balances; sizing respects sleeve caps + DD-cap.
- emitted: `book_net_exposure.csv`, net ledger, per-month USD_tilt, SLEEVE_RISK_CHECK.
- failure mode → book ≠ tape → BLOCK (loud); pre/post 07-28 live record must NOT be pooled.

## CADENCE
- MONTHLY : F — netted book + DD-cap + USD overlay.
- WEEKLY  : F — weekly book update.
- DAILY   : s — daily net-exposure mark.

## PROVENANCE / PRIOR ART
- [[janus-two-sided-sizer]] (NETTING not projection; naive per-ticket ≈ 4x intended),
  [[sleeve-sizing-risk-concentration]] (Pt 30→18.5%, 2.0x gross cap, SLEEVE_RISK_CHECK.py; don't
  pool pre/post 07-28), [[currency-step-verdict]] (STEP 12 = DECLARED short-USD TILT, not a hedge;
  k TRAIN-calibrated, marginal — 4-asset book Pt/NG removed: 3.92%/1.23/−5.7%),
  [[ledger-annualization-defect]] (calendar annualization, never row-count).

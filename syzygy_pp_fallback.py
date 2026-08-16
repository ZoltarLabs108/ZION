"""
syzygy_pp_fallback.py — wire the Permanent-Portfolio sleeve into SYZYGY as the ABSTAIN-FALLBACK.

On months where the ZION book holds all-cash (n_fired==0, ~61%), deploy the PP sleeve
(Browne-4 + INTERSTELLAR throttle) instead of earning 0. On acted months the book is unchanged.
Reuses syzygy_book.metrics() so annualization stays honest (12/n month exponent, not row-count).

This is an OVERLAY (safe, validating). The permanent one-line change to assemble_book is printed
at the end. Non-predictive by construction — it only substitutes structure for idle cash.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, '/Users/castaglia/Desktop/ZION')
from syzygy_book import metrics, START

PANEL = '/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv'
p = pd.read_csv(PANEL, low_memory=False); p['Date'] = pd.to_datetime(p['Date'])
p = p.sort_values('Date').drop_duplicates('Date').reset_index(drop=True)

# ---- PP legs (match permanent_portfolio.py) ----
eq = p['SP_Price'].pct_change()
gs10 = p['GS10_Rate']; bond = gs10/100/12 - 8.0*(gs10.diff()/100)
gold = p['Gold_Close'].pct_change()
comm = p['WTI_Crude_Close'].pct_change()
cash = p['Fed_Funds_Rate']/100/12
nfci = p['Chicago_Fed_NFCI'].to_numpy()
thr = np.where(np.isnan(nfci), 1.0, np.where(nfci < 0.5, 1.0, np.where(nfci < 1.0, 0.5, 0.25)))

def pp_series(commodity_tail=0.0):
    """Browne-4 EW + throttle; optional commodity tail funded pro-rata from the 4 legs."""
    base_w = (1.0 - commodity_tail) / 4.0
    gross = base_w*(eq.fillna(0)+bond.fillna(0)+gold.fillna(0)+cash.fillna(0)) + commodity_tail*comm.fillna(0)
    r = thr*gross.to_numpy() + (1-thr)*cash.fillna(0).to_numpy()
    return pd.Series(r, index=p['Date'])

pp = pp_series(0.0)           # primary fallback = Browne-4 + throttle
pp_tail = pp_series(0.10)     # variant: +10% commodity tail (2022 protection)

# ---- book ledger ----
bk = pd.read_csv('/Users/castaglia/Desktop/ZION/reports/book_ledger.csv')
bk['date'] = pd.to_datetime(bk['date'])
bk = bk.merge(pd.DataFrame({'date': p['Date'], 'pp': pp.values, 'pp_tail': pp_tail.values}), on='date', how='left')
bk = bk[bk['date'] >= START].reset_index(drop=True)

def overlay(nfired_col, bookr_col, pp_col):
    fb = bk[nfired_col] == 0
    out = bk[bookr_col].to_numpy(float).copy()
    ppv = bk[pp_col].to_numpy(float)
    out[fb.to_numpy() & np.isfinite(ppv)] = ppv[fb.to_numpy() & np.isfinite(ppv)]
    return out, int(fb.sum())

L = ['# SYZYGY × PP abstain-fallback — full-record effect (2026-08-14)',
     f"Book months: {len(bk)} ({bk.date.min():%Y-%m}..{bk.date.max():%Y-%m}). "
     "PP deployed ONLY on all-cash (n_fired==0) months; acted months unchanged.", '']

for variant, col, ppcol in [('BASE (rules only)', 'book_r_base', 'pp'),
                            ('BASE + commodity-tail PP', 'book_r_base', 'pp_tail'),
                            ('CELLS variant', 'book_r_cells', 'pp')]:
    nf = 'n_fired_base' if 'base' in col else 'n_fired_cells'
    orig = bk[col].to_numpy(float)
    fb_ret, n_fb = overlay(nf, col, ppcol)
    mo, mf = metrics(orig), metrics(fb_ret)
    ppm = bk.loc[bk[nf] == 0, ppcol]
    L += [f"## {variant}",
          f"- all-cash months converted to PP: **{n_fb}** of {len(bk)} ({n_fb/len(bk)*100:.0f}%); "
          f"PP mean there **{ppm.mean()*100:+.2f}%/mo**, {(ppm > 0).mean()*100:.0f}% positive.",
          '| metric | book (cash on abstain) | book + PP-fallback | Δ |',
          '|---|---|---|---|',
          f"| CAGR | {mo['CAGR']*100:.2f}% | {mf['CAGR']*100:.2f}% | **{(mf['CAGR']-mo['CAGR'])*100:+.2f}pp** |",
          f"| Sortino | {mo['Sortino']:.2f} | {mf['Sortino']:.2f} | **{mf['Sortino']-mo['Sortino']:+.2f}** |",
          f"| MaxDD | {mo['MaxDD']*100:.1f}% | {mf['MaxDD']*100:.1f}% | {(mf['MaxDD']-mo['MaxDD'])*100:+.1f}pp |",
          f"| Calmar | {mo['Calmar']:.2f} | {mf['Calmar']:.2f} | {mf['Calmar']-mo['Calmar']:+.2f} |", '']

# save the fallback book ledger
fb_ret, _ = overlay('n_fired_base', 'book_r_base', 'pp')
bk['book_r_base_ppfb'] = fb_ret
bk[['date', 'n_fired_base', 'book_r_base', 'pp', 'book_r_base_ppfb']].to_csv(
    '/Users/castaglia/Desktop/ZION/reports/book_ledger_ppfallback.csv', index=False)

L += ['## Permanent integration (one change in `syzygy_book.assemble_book`)',
      "In assemble_book, after computing `book_r`, on all-cash months substitute the PP return:",
      '```python',
      "# abstain-fallback: hold PP structure instead of cash when no sleeve fires",
      "if fired == 0 and np.isfinite(pp_r.get(d, np.nan)):",
      "    book_r = float(pp_r[d])            # pp_r = precomputed Browne-4+throttle monthly series",
      '```',
      "PP is non-predictive; judge on Sortino/MaxDD above, never on directional accuracy.", '',
      '## Caveats (carried from the PP build)',
      '- Equities price-only (no dividends) → understates ~2%/yr; real uplift larger.',
      '- 10Y-TR proxy + Fed-funds cash; throttle = NFCI fixed thresholds (swap for v3.2 composite).']
open('/Users/castaglia/Desktop/ZION/SYZYGY_PP_FALLBACK_20260814.md', 'w').write('\n'.join(L))
print('\n'.join(L)); print('\n[written] SYZYGY_PP_FALLBACK_20260814.md + reports/book_ledger_ppfallback.csv')

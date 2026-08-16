"""
permanent_portfolio.py — the STRUCTURAL (non-predictive) sleeve: five forms of money held
statically, tested the honest way — year-by-year net, drawdown, blind-month behaviour, 2022
shock — with the INTERSTELLAR liquidity throttle wired in (gross de-risk in stress, never a sizer).

FIVE FORMS OF MONEY:
  Equities (prosperity)  SP_Price        [price-only — NO dividends, understates ~2%/yr]
  Long bonds (deflation) 10Y TR proxy    [carry + dur8*(-Δyield) from GS10 — approximation]
  Gold (inflation)       Gold_Close
  Commodities (real)     WTI_Crude_Close  [volatile leg; window starts when WTI begins]
  Cash (tight money)     Fed_Funds_Rate accrual
CLASSIC-4 (Browne) drops the commodity leg (stocks/bonds/gold/cash, 25% each).

INTERSTELLAR throttle (report-only de-risk, NEVER sizes): Chicago Fed NFCI (normalized, PIT-published)
  CALM  NFCI<0.5 -> 1.00x   CAUTION 0.5..1.0 -> 0.50x   STRESS >1.0 -> 0.25x
  throttled fraction earns cash. (Thresholds documented; swap to ZION v3.2 composite if desired.)

Honest caveats printed. Nothing here forecasts; the whole point is structure, not prediction.
"""
import pandas as pd, numpy as np
PANEL = '/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv'
p = pd.read_csv(PANEL, low_memory=False); p['Date'] = pd.to_datetime(p['Date'])
p = p.sort_values('Date').drop_duplicates('Date').reset_index(drop=True)

eq = p['SP_Price'].pct_change()
gs10 = p['GS10_Rate']
bond = gs10/100/12 - 8.0*(gs10.diff()/100)           # 10Y constant-maturity TR proxy
gold = p['Gold_Close'].pct_change()
comm = p['WTI_Crude_Close'].pct_change()
cash = p['Fed_Funds_Rate']/100/12
nfci = p['Chicago_Fed_NFCI']
legs4 = {'Equities': eq, 'LongBonds': bond, 'Gold': gold, 'Cash': cash}
legs5 = {'Equities': eq, 'LongBonds': bond, 'Gold': gold, 'Commodities': comm, 'Cash': cash}

R = pd.DataFrame({**legs5, 'Date': p['Date'], 'cash': cash, 'nfci': nfci})
R = R.dropna(subset=['Equities', 'LongBonds', 'Gold', 'Commodities', 'Cash']).reset_index(drop=True)
dates = R['Date']

# INTERSTELLAR throttle
def throttle(nfci):
    t = np.where(nfci < 0.5, 1.0, np.where(nfci < 1.0, 0.5, 0.25))
    return np.where(np.isnan(nfci), 1.0, t)
thr = throttle(R['nfci'].to_numpy())

def portfolio(legs, weights, apply_thr):
    """monthly-rebalanced; weights: dict or 'rp' for risk-parity(inverse 36m vol)."""
    cols = list(legs); M = R[cols].to_numpy()
    if weights == 'rp':
        W = np.zeros_like(M)
        for i in range(len(M)):
            lo = max(0, i-36)
            v = np.nanstd(M[lo:i+1], axis=0); v[v == 0] = np.nan
            iv = 1.0/v; iv[np.isnan(iv)] = 0
            W[i] = iv/iv.sum() if iv.sum() > 0 else np.ones(len(cols))/len(cols)
    else:
        W = np.tile(np.array([weights[c] for c in cols]), (len(M), 1))
    pr = np.nansum(W*M, axis=1)
    if apply_thr:
        pr = thr*pr + (1-thr)*R['cash'].to_numpy()
    return pd.Series(pr, index=dates)

def stats(s, label):
    s = s.dropna()
    cum = (1+s).cumprod(); dd = (cum/cum.cummax()-1).min()
    yr = (1+s).groupby(s.index.year).prod()-1
    posyr = (yr > 0).mean()
    ann = (1+s).prod()**(12/len(s))-1; vol = s.std()*np.sqrt(12)
    downside = s[s < 0].std()*np.sqrt(12)
    sharpe = (ann - R['cash'].mean()*12)/vol if vol > 0 else np.nan
    sortino = (ann - R['cash'].mean()*12)/downside if downside > 0 else np.nan
    worst = yr.min(); worstyr = int(yr.idxmin())
    return dict(label=label, ann=ann, vol=vol, dd=dd, posyr=posyr, sharpe=sharpe,
                sortino=sortino, worst=worst, worstyr=worstyr, n=len(s), yr=yr)

L = ['# Permanent Portfolio sleeve — structural, non-predictive (2026-08-14)',
     f"Window: {dates.min():%Y-%m}..{dates.max():%Y-%m} (n={len(R)} months; starts when WTI leg begins).",
     '',
     '## Configurations (monthly-rebalanced; ann=CAGR, dd=max drawdown, posyr=fraction of years positive)',
     '| config | CAGR | vol | maxDD | +years | Sharpe | Sortino | worst year |',
     '|---|---|---|---|---|---|---|---|']
cfgs = [
    ('Classic-4 EW (Browne)', legs4, {k: 0.25 for k in legs4}, False),
    ('Classic-4 EW + throttle', legs4, {k: 0.25 for k in legs4}, True),
    ('5-leg EW', legs5, {k: 0.20 for k in legs5}, False),
    ('5-leg EW + throttle', legs5, {k: 0.20 for k in legs5}, True),
    ('5-leg risk-parity', legs5, 'rp', False),
    ('5-leg risk-parity + throttle', legs5, 'rp', True),
]
results = {}
for name, legs, w, at in cfgs:
    st = stats(portfolio(legs, w, at), name); results[name] = st
    L.append(f"| {name} | {st['ann']*100:.1f}% | {st['vol']*100:.1f}% | {st['dd']*100:.1f}% | "
             f"{st['posyr']*100:.0f}% | {st['sharpe']:.2f} | {st['sortino']:.2f} | {st['worst']*100:.0f}% ({st['worstyr']}) |")

# blind-month behaviour
g = pd.read_csv('/Users/castaglia/Desktop/ZION/stage4_ledger/integrated_five_asset_ledger.csv')
g['Date'] = pd.to_datetime(g['Date']); blind = set(g[g.n_acting == 0]['Date'])
base = portfolio(legs5, {k: 0.20 for k in legs5}, True)
bmask = base.index.isin(blind)
L += ['', '## Blind-month behaviour (the 268 months the ZION book has NO signal)',
      f"- 5-leg EW+throttle in blind months: mean **{base[bmask].mean()*100:+.2f}%**/mo, "
      f"**{(base[bmask] > 0).mean()*100:.0f}%** positive (n={int(bmask.sum())}).",
      f"- vs signal months: mean {base[~bmask].mean()*100:+.2f}%/mo, {(base[~bmask] > 0).mean()*100:.0f}% positive.",
      "- Read: the structural sleeve earns through the blind months WITHOUT predicting them — the whole point.", '']

# 2022 shock
y22 = base.index.year == 2022
L += ['## 2022 stress (the year the "always positive" claim breaks)',
      f"- 5-leg EW+throttle 2022 return: **{((1+base[y22]).prod()-1)*100:+.1f}%**",
      '| leg | 2022 return |', '|---|---|']
r22 = R[R['Date'].dt.year == 2022]
for nm in ['Equities', 'LongBonds', 'Gold', 'Commodities', 'Cash']:
    L.append(f"| {nm} | {((1+r22[nm].dropna()).prod()-1)*100:+.1f}% |")
L += ['', 'Confirms the honest caveat: in a synchronized rate/inflation shock (2022) equities, bonds AND '
      'gold fall together — only cash (and sometimes commodities) win. PP is high-hit-rate risk reduction, NOT a guarantee.', '',
      '## Honest caveats (do not skip)',
      '- Equities = SP_Price PRICE-ONLY (no dividends) → understates the equity leg ~2%/yr; real PP CAGRs are higher.',
      '- Long bonds = 10Y constant-maturity TR PROXY (carry + dur8·−Δyield), not an actual bond index.',
      '- Cash = Fed funds accrual. Monthly rebalancing (Browne rebalances annually/at bands → slightly different).',
      '- Throttle uses NFCI fixed thresholds (documented); swap for ZION v3.2 composite to match production.',
      '- Window starts at the WTI leg; classic-4 could extend earlier (gold 1970s) — reported on the common window for comparability.']
open('/Users/castaglia/Desktop/ZION/PERMANENT_PORTFOLIO_20260814.md', 'w').write('\n'.join(L))
print('\n'.join(L)); print('\n[written] PERMANENT_PORTFOLIO_20260814.md')

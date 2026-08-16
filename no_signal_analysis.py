"""
no_signal_analysis.py — the coherent arc for the book's BLIND months:
 (2) characterize the 268 no-signal months by EXOGENOUS regime (descriptive, zero overfit)
 (3) is there anything real to trade there? (SPY behaviour in blind months)
 (4) NUCLEAR SWEEP as INTEL ONLY — brute-force all *_Return_6M predictors vs SPY direction
     in blind months, and DEMONSTRATE the multiplicity (how many hit high by pure chance)
 (5) inputs for the inverse-layer decision.
Everything labelled: descriptive facts vs search-noise. Nothing here is a tradeable result.
"""
import pandas as pd, numpy as np
PANEL = '/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv'

def wlb(k, n, z=1.96):
    if n <= 0: return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); m = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)); return (c-m)/d

g = pd.read_csv('/Users/castaglia/Desktop/ZION/stage4_ledger/integrated_five_asset_ledger.csv')
g['Date'] = pd.to_datetime(g['Date'])
spy = pd.read_csv('/Users/castaglia/Desktop/ZION/stage4_convergence/spy_convergence_ledger.csv')
spy['Date'] = pd.to_datetime(spy['Date']); spy = spy[['Date', 'y']]
m = g[['Date', 'n_acting']].merge(spy, on='Date', how='left')
m['blind'] = (m['n_acting'] == 0)

pan = pd.read_csv(PANEL, low_memory=False); pan['Date'] = pd.to_datetime(pan['Date'])
# exogenous regime vars (all decision-time observable)
reg = pan[['Date', 'VIX_Close', 'Dollar_Index', 'GS10_Rate', 'Term_Spread_10Y_2Y',
           'Chicago_Fed_NFCI', 'US_CPI', 'Fed_Funds_Rate']].copy()
reg['dollar_12m'] = pan['Dollar_Index'].pct_change(12) * 100
reg['cpi_yoy'] = pan['US_CPI'].pct_change(12) * 100
reg['real_rate'] = reg['GS10_Rate'] - reg['cpi_yoy']
m = m.merge(reg, on='Date', how='left')

L = ['# No-signal months — regime, tradability, and the inverse-layer question (2026-08-14)', '']
b = m[m.blind]; s = m[~m.blind]
L += [f"Blind (no-signal) months: **{len(b)}** · signal months: **{len(s)}**", '',
      '## (2) What regime are the blind months? (descriptive, exogenous — zero overfit risk)',
      '| regime var | blind mean | signal mean | Δ |', '|---|---|---|---|']
for v, nm in [('VIX_Close', 'VIX level'), ('Chicago_Fed_NFCI', 'NFCI (fin. conditions, +=tight)'),
              ('dollar_12m', 'Dollar 12-mo %'), ('real_rate', 'Real 10Y rate'),
              ('Term_Spread_10Y_2Y', 'Term spread 10Y-2Y'), ('Fed_Funds_Rate', 'Fed funds')]:
    bm, sm = b[v].mean(), s[v].mean()
    if pd.notna(bm) and pd.notna(sm):
        L.append(f"| {nm} | {bm:.2f} | {sm:.2f} | {bm-sm:+.2f} |")
L += ['', "Read: if blind months don't differ much from signal months on these, the book's blindness is "
      "NOT a clean exogenous regime — it's idiosyncratic, and no regime risk-rule cleanly separates it.", '']

# (3) is there anything to trade in blind months?
by = b['y'].dropna()
up = (by > 0).mean()
L += ['## (3) Is there anything real to trade in the blind months?',
      f"- SPY next-month up-rate IN blind months: **{up:.0%}** (n={len(by)}) vs all-months ~{(m['y']>0).mean():.0%}.",
      f"- So even a naive 'always long SPY' in blind months would be ~{max(up,1-up):.0%} — that's the drift floor any "
      f"'blind-month signal' must beat to be real, not just re-captured drift.", '']

# (4) NUCLEAR SWEEP as INTEL — brute-force *_Return_6M vs SPY dir in blind months
r6 = [c for c in pan.columns if c.endswith('_Return_6M')]
pj = pan[['Date'] + r6].copy()
mb = m[m.blind][['Date', 'y']].merge(pj, on='Date', how='left')
yb = mb['y'].to_numpy()
res = []
for c in r6:
    x = mb[c].to_numpy()
    ok = ~np.isnan(x) & ~np.isnan(yb) & (yb != 0)
    if ok.sum() < 30: continue
    # best of the two trivial rules: sign(x) predicts y, or -sign(x)
    d = np.sign(x[ok]); yy = yb[ok]
    a1 = (d == yy).mean(); acc = max(a1, 1-a1); n = ok.sum()
    res.append((c, acc, n, wlb(int(round(acc*n)), int(n))))
res.sort(key=lambda r: -r[1])
n_cand = len(res)
hi70 = sum(1 for _, a, _, _ in res if a >= 0.70)
hi65 = sum(1 for _, a, _, _ in res if a >= 0.65)
L += ['## (4) NUCLEAR SWEEP — INTEL ONLY (this is a multiplicity demo, NOT a result)',
      f"Brute-forced **{n_cand}** `*_Return_6M` predictors vs SPY direction in blind months (best of sign/−sign each).",
      f"- **{hi70} predictors ≥70%**, **{hi65} ≥65%** — out of {n_cand} searched.",
      f"- Under pure noise you EXPECT ~{n_cand*0.5*(1-0.841):.0f}+ to clear 70% by chance on this n; a big hit-count "
      f"is the winner's-curse signature, not discovery.", '',
      'Top 12 "matches" (INTEL — presumed noise until independently re-discovered out-of-search):', '',
      '| predictor (6-mo change) | acc in blind mo | n | Wilson-LB |', '|---|---|---|---|']
for c, a, n, lb in res[:12]:
    L.append(f"| {c.replace('_Return_6M','')} | {a:.0%} | {n} | {lb:.2f} |")
L += ['', f"Even the TOP match's Wilson-LB is {res[0][3]:.2f} — and it's the MAX over {n_cand} tries, so its "
      f"honest search-corrected LB is far lower. Treat all of the above as noise-shaped-like-signal.", '']

# (5) inverse-layer decision inputs
L += ['## (5) Verdict: worth adding as an inverse layer?',
      f"- The blind months are {'NOT a clean exogenous regime' if abs(b['VIX_Close'].mean()-s['VIX_Close'].mean())<3 else 'somewhat regime-distinct (see VIX/NFCI Δ)'} (see §2).",
      f"- SPY drifts ~{max(up,1-up):.0%} in blind months, so any 'edge' there must clear that drift floor.",
      f"- The nuclear sweep produces {hi65} high matches from noise — exactly the residual-fishing trap.",
      "- **Conclusion:** a *directional* inverse layer is NOT justified — you'd be trading the residual, and the "
      "sweep shows that residual yields confident noise. The only defensible use of the blind-month structure is a "
      "**risk/abstention overlay** IF §2 shows a clean regime (size down / stay flat when the book is structurally "
      "blind), never a directional bet. Decision gates on §2, not on the sweep."]
open('/Users/castaglia/Desktop/ZION/NO_SIGNAL_ANALYSIS_20260814.md', 'w').write('\n'.join(L))
print('\n'.join(L)); print('\n[written] NO_SIGNAL_ANALYSIS_20260814.md')

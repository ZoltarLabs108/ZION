"""
decision_review.py — agree/disagree among RD/ODYSSEY/SANCTUARY (SPY monthly, real ledger) +
the book-level NO-DECENT-SIGNAL months (integrated 5-asset ledger). Honest about what exists:
  - SPY monthly three-voice ledger EXISTS -> full agree/disagree here.
  - Gold/Silver per-VOICE ledgers do NOT exist (only their cascades); weekly convergence
    is a recipe doc, NOT a computed pipeline. Those cells are reported as NOT-BUILT, not faked.
"""
import pandas as pd, numpy as np

def wlb(k, n, z=1.96):
    if n <= 0: return 0.0
    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n); m = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c - m) / d

L = ['# DECISION review — voice agreement + no-signal months (2026-08-14)', '']

# ---------- SPY monthly: three-voice agree/disagree ----------
d = pd.read_csv('/Users/castaglia/Desktop/ZION/stage4_convergence/spy_convergence_ledger.csv')
d['Date'] = pd.to_datetime(d['Date'])
y = d['y'].to_numpy()
V = d[['rd', 'od', 'sc']].to_numpy()
present = np.sum(~np.isnan(V), axis=1)
up = np.nansum(V == 1, axis=1); dn = np.nansum(V == -1, axis=1)
unanimous = (present >= 2) & ((up == 0) | (dn == 0))
split = (present >= 2) & (up > 0) & (dn > 0)
thin = present < 2
agreed_dir = np.where(unanimous, np.sign(up - dn), 0)

L += [f"## SPY monthly — RED DAWN / ODYSSEY / SANCTUARY  (n={len(d)} decision-months, "
      f"{d.Date.min():%Y-%m}..{d.Date.max():%Y-%m})", '']
for c, nm in [('rd', 'RED DAWN'), ('od', 'ODYSSEY'), ('sc', 'SANCTUARY')]:
    pr = d[c].notna().to_numpy(); acc = (d.loc[pr, c].to_numpy() == y[pr]).mean()
    L.append(f"- **{nm}** present {int(pr.sum())}/{len(d)} months · standalone dir acc {acc*100:.1f}%")
ua = unanimous.sum(); acc_u = (agreed_dir[unanimous] == y[unanimous]).mean()
lb_u = wlb(int((agreed_dir[unanimous] == y[unanimous]).sum()), int(ua))
L += ['',
      f"| convergence state | months | share | next-month acc |",
      f"|---|---|---|---|",
      f"| **UNANIMOUS (≥2 present, agree)** → ACT | {int(ua)} | {ua/len(d):.0%} | **{acc_u*100:.1f}%** (LB {lb_u*100:.0f}%) |",
      f"| SPLIT (≥2 present, disagree) → ABSTAIN | {int(split.sum())} | {split.sum()/len(d):.0%} | — (no call) |",
      f"| THIN (<2 engines present) → ABSTAIN | {int(thin.sum())} | {thin.sum()/len(d):.0%} | — (no call) |", '']
# all-3 present & unanimous (the high-conviction core)
allp = (present == 3)
core = allp & unanimous
if core.sum():
    acc_c = (agreed_dir[core] == y[core]).mean()
    lb_c = wlb(int((agreed_dir[core] == y[core]).sum()), int(core.sum()))
    L.append(f"- **CORE (all 3 present & unanimous):** n={int(core.sum())} · acc {acc_c*100:.1f}% · LB {lb_c*100:.0f}%")
# pairwise agreement rate among present
L.append('')
for a, b in [('rd', 'od'), ('rd', 'sc'), ('od', 'sc')]:
    both = d[a].notna() & d[b].notna()
    ag = (d.loc[both, a].to_numpy() == d.loc[both, b].to_numpy()).mean()
    L.append(f"- pairwise agree {a.upper()}~{b.upper()} (both present, n={int(both.sum())}): {ag*100:.0f}%")

# ---------- book-level NO-SIGNAL months (integrated 5-asset) ----------
g = pd.read_csv('/Users/castaglia/Desktop/ZION/stage4_ledger/integrated_five_asset_ledger.csv')
g['Date'] = pd.to_datetime(g['Date'])
nosig = g[g['n_acting'] == 0].copy()
L += ['', '---', '',
      f"## Book-level NO-DECENT-SIGNAL months (integrated 5-asset ledger, n={len(g)})",
      f"Months where **no asset** (SP500/Gold/Silver/WTI/USD) clears its DECISION gate — `n_acting==0`.",
      '',
      f"- **{len(nosig)} of {len(g)} months ({len(nosig)/len(g):.0%})** have zero acting assets.",
      f"- by decade:"]
nosig['decade'] = (nosig['Date'].dt.year // 10) * 10
for dec, cnt in nosig['decade'].value_counts().sort_index().items():
    tot = ((g['Date'].dt.year // 10) * 10 == dec).sum()
    L.append(f"    - {int(dec)}s: {cnt}/{tot} months no-signal")
L += ['', 'First 24 no-signal months (full list in decision_review_nosignal.csv):', '',
      '| Date | SP500 | Gold | Silver | WTI | USD |', '|---|---|---|---|---|---|']
def cell(r, a):
    p = r[f'{a}_pred']
    return '—' if pd.isna(p) else ('↑' if p > 0 else '↓')
for _, r in nosig.head(24).iterrows():
    L.append(f"| {r['Date']:%Y-%m} | {cell(r,'SP500')} | {cell(r,'Gold')} | {cell(r,'Silver')} | {cell(r,'WTI')} | {cell(r,'USD')} |")
nosig.to_csv('/Users/castaglia/Desktop/ZION/decision_review_nosignal.csv', index=False)

# ---------- honest gaps ----------
L += ['', '---', '',
      '## What is NOT built (stated, not faked)',
      '- **Gold / Silver three-VOICE ledgers**: do not exist. Only their RED DAWN cascades are computed '
      '(`reports/Gold_*`, `reports/Silver_*`). The ODYSSEY/SANCTUARY voices are SPY-wired in `engines.py` '
      '(`load_spine()` = SP). Running them per-asset needs gold/silver spines built to the engine schema — a real build, not a read.',
      '- **Weekly convergence (any asset)**: not computed. `weekly/` holds only `ZION_WEEKLY_RECIPE.md` (a spec). '
      'No weekly voice ledger exists, so weekly agree/disagree cannot be shown without building the weekly pipeline.',
      '- The book-level no-signal months above use the integrated 5-asset **final** DECISION (real), which is '
      'the right input for the "match an asset to the missing months" step.']
open('/Users/castaglia/Desktop/ZION/DECISION_REVIEW_20260814.md', 'w').write('\n'.join(L))
print('\n'.join(L)); print('\n[written] DECISION_REVIEW_20260814.md + decision_review_nosignal.csv')

"""
ZION Stage 3 prototype — clean expanding-window walk-forward, 1-month direction.
DISCIPLINE:
  - target = sign(next-month Gold return)  [legacy 1-month analysis]
  - at decision month t: train ONLY on rows <= t-3 (3-month embargo)
  - 27-type grammar (grammar27) fit INSIDE the fold on train rows only
  - z-score params, cell->direction map, Wilson-LB all from train slice only
  - admit a cell if train n>=MIN_N and train Wilson-LB >= GATE(0.45)
  - abstain when the decision-month cell is not admitted  (NO forced prediction)
No house-wide selection anywhere. Every number below is genuine OOS.
"""
import pandas as pd, numpy as np

PANEL = "/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
GATE = 0.45          # train-side Wilson-LB admission floor (operator-set)
MIN_N = 8            # min train support per cell
FLAT = 0.5           # ternary dead zone in train-sd units
MIN_TRAIN = 120      # need >=10y of usable train before first decision
Z = 1.96

def wilson_lb(k, n, z=Z):
    if n == 0: return 0.0
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    m = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c - m) / d

def tern(x, mu, sd):
    if sd == 0 or np.isnan(sd): return np.zeros_like(x, dtype=int)
    z = (x - mu) / sd
    out = np.zeros_like(z, dtype=int)
    out[z >  FLAT] = 1
    out[z < -FLAT] = -1
    return out

def run_pair(A, B, G, label, kept):
    # keep rows where all three present; work on the contiguous available series
    m = np.isfinite(A) & np.isfinite(B) & np.isfinite(G)
    A, B, G = A[m], B[m], G[m]
    n = len(G)
    ret = np.full(n, np.nan)
    ret[:-1] = G[1:]/G[:-1] - 1.0          # next-month gold return
    y = np.sign(ret)                        # target: next-month direction
    dA = np.diff(A, prepend=A[0])
    dB = np.diff(B, prepend=B[0])

    preds = []   # (idx, pred_dir, realized_dir, gold_ret)
    for t in range(MIN_TRAIN + 3, n - 1):
        tr = np.arange(0, t - 2)            # rows <= t-3 (embargo); labels resolve <= t-2
        tr = tr[np.isfinite(y[tr])]
        if len(tr) < MIN_TRAIN: continue
        sdA = A[tr].std(); sdB = B[tr].std()
        if sdA == 0 or sdB == 0: continue
        s1 = dA; s2 = dB; s3 = dA/sdA - dB/sdB   # spread-change (means cancel in diff)
        c1 = tern(s1, s1[tr].mean(), s1[tr].std())
        c2 = tern(s2, s2[tr].mean(), s2[tr].std())
        c3 = tern(s3, s3[tr].mean(), s3[tr].std())
        cell = (c1*9 + c2*3 + c3)           # 27-type id in [-13..13]
        # train cell -> majority direction + Wilson-LB
        adm = {}
        for c in np.unique(cell[tr]):
            idx = tr[cell[tr] == c]
            yy = y[idx]; yy = yy[yy != 0]
            if len(yy) < MIN_N: continue
            up = (yy > 0).sum(); dn = (yy < 0).sum()
            k = max(up, dn); nn = up + dn
            if wilson_lb(k, nn) >= GATE:
                adm[c] = 1 if up >= dn else -1
        d = adm.get(cell[t])
        if d is not None and y[t] != 0:
            preds.append((t, d, int(y[t]), ret[t]))

    if not preds:
        return dict(label=label, kept=kept, n=0)
    P = np.array([p[1] for p in preds]); R = np.array([p[2] for p in preds])
    gr = np.array([p[3] for p in preds])
    correct = (P == R).sum(); nact = len(P)
    acc = correct/nact
    lb = wilson_lb(correct, nact)
    # money test on acted months (dir*gold_ret); annualize by months
    sr = P*gr
    eq = np.cumprod(1+sr)
    months = nact
    cagr = eq[-1]**(12/months) - 1
    downs = sr[sr < 0]
    sortino = (sr.mean()/downs.std()*np.sqrt(12)) if len(downs) and downs.std()>0 else float('nan')
    peak = np.maximum.accumulate(eq); maxdd = ((eq-peak)/peak).min()
    # buy-hold over same acted months
    bh_up = (R > 0).mean()
    edge = acc - bh_up
    # coverage-selection guard: corr(acted, market-up) over full evaluable span
    return dict(label=label, kept=kept, n=nact, acc=acc, lb=lb,
                bh_up=bh_up, edge=edge, cagr=cagr, sortino=sortino, maxdd=maxdd)

df = pd.read_csv(PANEL)
df["Date"] = pd.to_datetime(df["Date"])
def col(c): return df[c].to_numpy(dtype=float)
G = col("Gold_Close")

candidates = [
    ("Dollar_Index / Gold_Close",        "Dollar_Index",  "Gold_Close",        False),
    ("GS10_Rate / US_CPI",               "GS10_Rate",     "US_CPI",            False),
    ("Copper_Close / WTI_Crude_Close",   "Copper_Close",  "WTI_Crude_Close",  False),
    ("Fed_Funds_Rate / US_CPI",          "Fed_Funds_Rate","US_CPI",            False),
    ("M2_Money / Term_Spread_10Y_2Y",    "M2_Money",      "Term_Spread_10Y_2Y", True),  # control (kept-set)
]

print(f"{'candidate':34s} {'kept?':5s} {'n':>4s} {'OOS_acc':>8s} {'WilsonLB':>9s} {'BH_up':>6s} {'edge':>7s} {'CAGR':>7s} {'Sortino':>8s} {'MaxDD':>7s}")
print("-"*110)
rows=[]
for label, a, b, kept in candidates:
    r = run_pair(col(a), col(b), G, label, kept)
    rows.append(r)
    if r["n"]==0:
        print(f"{label:34s} {'Y' if kept else 'N':5s} {'--- no admitted cells / all abstain ---'}")
        continue
    print(f"{label:34s} {'Y' if kept else 'N':5s} {r['n']:4d} {r['acc']*100:7.1f}% {r['lb']*100:8.1f}% {r['bh_up']*100:5.1f}% {r['edge']*100:+6.1f}% {r['cagr']*100:6.1f}% {r['sortino']:8.2f} {r['maxdd']*100:6.1f}%")
print("-"*110)
print("All numbers are clean expanding-window WF OOS (t-3 embargo, in-fold 27-type fit, Wilson-LB>=0.45 admit, abstain-by-default).")
print("Buy-hold reference over the Gold sample: up-rate ~%.1f%%." % ((np.sign(G[1:]/G[:-1]-1)>0).mean()*100))

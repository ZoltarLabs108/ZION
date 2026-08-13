"""
ZION ODYSSEY — composite-waveform engine (RECIPE STEP 2, EXAM voice).

Implements ZION_ODYSSEY/PHASE.md ACTION 4-5: on top of the PIT 6-bin analogue core
(ported faithfully from ASSET_PIPELINE/deps/lib_spy.py), it adds the NEW build the
operator asked for:

  (a) # of periods / cycle length          — ported from HYACINTH_3_RED_DAWN_X.py
      (find_optimal_cycle_length peak/trough  +  _est_natural_cycle autocorr peak)
  (b) average/composite waveform IN TRAIN -> applied to TEST
      (period-P fold of the z-waveform: shape=phase-means, amplitude, momentum)
  (c) change-of-extremes  (period-to-period amplitude variability)
  (d) OPTIONAL Markov      (6-bin transition matrix -> next-state up-prob)
  (e) per-pattern OOS accuracy + a WAVEFORM-QUALITY gate that isolates the FEW
      months whose waveform is genuinely regular.

DISCIPLINE (matches ZION stage2_walkforward/wf_prototype.py):
  * one-step-ahead expanding walk-forward; at decision month t we fit ONLY on rows
    whose label is known and embargoed (index+1 <= t-EMBARGO).
  * the composite template, period P, Markov matrix, analogue pool, and the
    strong-quality threshold are ALL train-only. TEST is the unbiased scorecard.
  * ODYSSEY is a VOICE — its value is at DECISION. This script's headline is the
    honest question: do the FEW strong-waveform months beat the base up-rate?

Run:  python3 odyssey_waveform.py [ASSET]      (default SP500; also Gold/Silver/WTI/USD)
Emits: odyssey_voice.csv  +  waveform_patterns_oos.csv  +  a printed scorecard.
"""
import sys, numpy as np, pandas as pd

PANEL   = "/Users/castaglia/Desktop/HYACINTH_X/combined_macro_0826.csv"
OUTCOME = {'SP500':'SP_Price','Gold':'Gold_Close','Silver':'Silver_Close',
           'WTI':'WTI_Crude_Close','USD':'Dollar_Index'}
SDLB      = 36     # rolling-SD lookback (months) for z-scores          (lib_spy)
LB        = 4      # bin-pattern lookback                               (lib_spy)
EMBARGO   = 3      # months between train label and decision            (wf_prototype)
MIN_TRAIN = 120    # >=10y usable train before first decision           (wf_prototype)
Z         = 1.96
STRONG_PCT = 80    # a month is "strong-waveform" if quality >= train STRONG_PCT-ile
MIN_MATCH  = 7     # analogue-pool minimum                              (lib_spy)
MIN_SIM    = 0.5

# ───────────────────────── primitives ─────────────────────────
def wilson_lb(k, n, z=Z):
    if n == 0: return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    return (c - z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)))/d

def zbin_fixed(z):                 # PIT-safe constant thresholds (lib_spy._zbin_fixed)
    if np.isnan(z): return 0
    if z < -1.5: return -3
    if z < -0.5: return -2
    if z < 0.0:  return -1
    if z < 0.5:  return 1
    if z <= 1.5: return 2
    return 3

def sim_bins(a, b):                # fuzzy product similarity (lib_spy._sim_bins)
    s = 1.0
    for x, y in zip(a, b):
        d = abs(x-y)
        if d == 0: s *= 1.0
        elif d == 1: s *= 0.67
        elif d == 2: s *= 0.33
        else: return 0.0
    return s

def pit_z(r):                      # z-score of returns vs TRAILING SDLB window only (PIT)
    N = len(r); sd = np.full(N, np.nan); z = np.full(N, np.nan)
    for i in range(SDLB, N):
        v = r[i-SDLB:i]; v = v[~np.isnan(v)]
        if len(v) >= 20: sd[i] = np.std(v, ddof=1)
    for i in range(N):
        if not (np.isnan(r[i]) or np.isnan(sd[i]) or sd[i] == 0): z[i] = r[i]/sd[i]
    return z

# ───────────── (a) period detection (ported from RED_DAWN_X) ─────────────
def find_cycle_length(series, min_move=0.15, min_gap=12, decay=0.1):
    """Peak-to-peak / trough-to-trough cycle counting (find_optimal_cycle_length)."""
    s = pd.Series(series).dropna()
    if len(s) < 60: return None
    sm = s.rolling(6, center=True, min_periods=3).mean().dropna()
    if len(sm) < 36: return None
    v = sm.to_numpy(); peaks, troughs = [], []
    for i in range(12, len(v)-12):
        w = v[max(0,i-12):min(len(v),i+13)]
        if v[i] == w.max():
            fut = v[i:min(i+36,len(v))]
            if v[i] > 0 and (v[i]-fut.min())/abs(v[i]) > min_move:
                if not peaks or (i-peaks[-1]) > min_gap: peaks.append(i)
        if v[i] == w.min():
            fut = v[i:min(i+36,len(v))]
            if abs(v[i]) > 1e-3 and (fut.max()-v[i])/abs(v[i]) > min_move:
                if not troughs or (i-troughs[-1]) > min_gap: troughs.append(i)
    cyc = [peaks[i+1]-peaks[i] for i in range(len(peaks)-1) if 12 <= peaks[i+1]-peaks[i] <= 240]
    cyc += [troughs[i+1]-troughs[i] for i in range(len(troughs)-1) if 12 <= troughs[i+1]-troughs[i] <= 240]
    if len(cyc) < 2: return None
    w = np.exp(-decay*np.arange(len(cyc))[::-1]) if len(cyc) >= 3 else None
    P = int(np.average(cyc, weights=w) if w is not None else np.mean(cyc))
    conf = 'high' if len(cyc) >= 5 else 'medium' if len(cyc) >= 3 else 'low'
    return {'P': P, 'n_cycles': len(cyc), 'conf': conf}

def est_natural_cycle(series, lo=6, hi=180):
    """Autocorrelation-peak period (_est_natural_cycle)."""
    s = pd.Series(series).dropna()
    if len(s) < 60: return None
    sn = (s - s.mean())/(s.std()+1e-10); best_lag, best = None, -1
    for lag in range(lo, min(hi, len(sn)//3)):
        c = sn.iloc[lag:].reset_index(drop=True).corr(sn.iloc[:-lag].reset_index(drop=True))
        if pd.notna(c) and c > best: best, best_lag = c, lag
    return best_lag if best > 0.1 else None

def detect_period(price_train, z_train):
    """Combine the two detectors; peak/trough count leads, autocorr backs up."""
    cyc = find_cycle_length(price_train)
    if cyc is not None:
        return cyc['P'], cyc['n_cycles'], cyc['conf']
    nat = est_natural_cycle(price_train)
    if nat is not None: return nat, 0, 'autocorr'
    nat = est_natural_cycle(z_train)
    if nat is not None: return nat, 0, 'autocorr_z'
    return None, 0, 'none'

# ───────────── (b,c) composite waveform: fold the z-series at period P ─────────────
def composite(z_all, train_idx, P):
    """Build the train average waveform by folding z at absolute-index phase (i mod P).
    Returns: template[phase], R (variance explained by the fold = periodic-signal
    strength), extremes_cv (period-to-period amplitude variability, lower=cleaner)."""
    if P is None or P < 4: return None
    zt = z_all[train_idx]; ok = ~np.isnan(zt)
    zt = zt[ok]; idx = train_idx[ok]
    if len(zt) < 3*P: return None
    phase = idx % P
    tmpl = np.array([zt[phase == ph].mean() if (phase == ph).any() else 0.0 for ph in range(P)])
    fit  = tmpl[phase]                       # fitted value per train point
    ss_res = np.sum((zt-fit)**2); ss_tot = np.sum((zt-zt.mean())**2)
    R = 1.0 - ss_res/ss_tot if ss_tot > 0 else 0.0
    # per-period amplitude (max-min of each full P-segment) -> coefficient of variation
    segs = [zt[(idx>=s)&(idx<s+P)] for s in range(idx.min(), idx.max()-P+1, P)]
    amps = [seg.max()-seg.min() for seg in segs if len(seg) >= P//2]
    ecv = (np.std(amps)/np.mean(amps)) if len(amps) >= 2 and np.mean(amps) > 0 else np.nan
    return {'tmpl': tmpl, 'R': max(R, 0.0), 'ecv': ecv}

# ───────────── (d) Markov: 6-bin transition matrix on train ─────────────
def markov_up(bins_train, r_train_next, cur_bin):
    """P(next return up | current bin) from train transitions of (bin_t -> sign r_{t+1})."""
    ups = r_train_next[(bins_train == cur_bin) & ~np.isnan(r_train_next)]
    if len(ups) < 8: return np.nan, 0
    return (ups > 0).mean(), len(ups)

# ───────────── analogue direction (train pool only) — the existing ODYSSEY voice ─────────────
def analogue_dir(bins, r_next, t_train_hi, cur):
    if 0 in cur: return 0, np.nan
    rets = []
    for j in range(SDLB+LB, t_train_hi):
        mb = list(bins[j-LB+1:j+1])
        if 0 in mb or sim_bins(cur, mb) < MIN_SIM: continue
        if not np.isnan(r_next[j]): rets.append(r_next[j])
    if len(rets) < MIN_MATCH: return 0, np.nan
    up = (np.array(rets) > 0).mean()
    return (1 if up >= 0.5 else -1), max(up, 1-up)

# ───────────────────────── walk-forward ─────────────────────────
def run(asset):
    col = OUTCOME[asset]
    df = pd.read_csv(PANEL, usecols=['Date', col], low_memory=False)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', col]).sort_values('Date').reset_index(drop=True)
    price = df[col].to_numpy(float); dates = df['Date'].to_numpy()
    N = len(price)
    r = np.full(N, np.nan); r[1:] = price[1:]/price[:-1] - 1.0
    r_next = np.full(N, np.nan); r_next[:-1] = r[1:]           # outcome: next-month return
    z = pit_z(r)
    bins = np.array([zbin_fixed(zz) for zz in z])

    rows = []
    for t in range(max(MIN_TRAIN, SDLB+LB+P_MIN_SEG), N-1):
        if np.isnan(z[t]) or np.isnan(r_next[t]): continue
        hi = t - EMBARGO                       # train labels known & embargoed: idx+1 <= hi
        if hi < MIN_TRAIN: continue
        tr = np.arange(0, hi)
        P, ncyc, conf = detect_period(price[tr], z[tr])
        comp = composite(z, tr, P)
        cur = list(bins[t-LB+1:t+1])
        adir, aconf = analogue_dir(bins, r_next, hi, cur)
        mup, mn = markov_up(bins[tr], r_next[tr], bins[t])
        mdir = 0 if np.isnan(mup) else (1 if mup >= 0.5 else -1)
        # composite direction: slope of the train template across the current phase
        cdir = 0; R = np.nan; ecv = np.nan; qual = np.nan
        if comp is not None and P:
            tmpl = comp['tmpl']; R = comp['R']; ecv = comp['ecv']
            cdir = int(np.sign(tmpl[(t+1) % P] - tmpl[t % P]))
            conf_f = {'high':1.0,'medium':0.7,'low':0.4}.get(conf, 0.5)
            qual = R * conf_f / (1.0 + (0.0 if np.isnan(ecv) else ecv))
        rows.append(dict(date=pd.Timestamp(dates[t]).date(), t=t, P=(P or 0), n_cycles=ncyc,
                         conf=conf, R=R, ecv=ecv, quality=qual, pattern=''.join(f'{b:+d}' for b in cur),
                         analogue_dir=adir, analogue_conf=aconf, markov_dir=mdir, markov_up=mup,
                         comp_dir=cdir, realized=int(np.sign(r_next[t])), ret_next=r_next[t]))
    V = pd.DataFrame(rows)
    if V.empty:
        print(f"[{asset}] no decision rows"); return
    # PIT strong-quality flag: quality >= expanding TRAIN percentile of quality
    q = V['quality'].to_numpy()
    strong = np.zeros(len(V), bool)
    for i in range(len(V)):
        past = q[:i][~np.isnan(q[:i])]
        if not np.isnan(q[i]) and len(past) >= 30 and q[i] >= np.percentile(past, STRONG_PCT):
            strong[i] = True
    V['strong'] = strong
    V.to_csv('odyssey_voice.csv', index=False)

    def scorecard(name, sub, dircol):
        d = sub[(sub[dircol] != 0)]
        if len(d) == 0: return f"  {name:<28} n=0"
        hit = (d[dircol] == d['realized']).mean(); k = int((d[dircol]==d['realized']).sum())
        return (f"  {name:<28} n={len(d):4d}  acc={hit:5.1%}  LB={wilson_lb(k,len(d)):5.1%}")

    base_up = (V['realized'] > 0).mean()
    print(f"\n════════ ODYSSEY composite-waveform — {asset} ════════")
    print(f"panel rows={N}  decision months={len(V)}  base up-rate={base_up:5.1%}  "
          f"(the number any direction vote must BEAT)")
    print(f"period P: median={int(V['P'].replace(0,np.nan).median() or 0)}  "
          f"conf mix={dict(V['conf'].value_counts())}")
    print("── ALL months ──")
    for nm, dc in [('analogue (bin) vote','analogue_dir'),('markov vote','markov_dir'),
                   ('composite-slope vote','comp_dir')]:
        print(scorecard(nm, V, dc))
    print(f"── STRONG-waveform months only (top {100-STRONG_PCT}% train quality, n={int(V['strong'].sum())}) ──")
    for nm, dc in [('analogue (bin) vote','analogue_dir'),('markov vote','markov_dir'),
                   ('composite-slope vote','comp_dir')]:
        print(scorecard(nm, V[V['strong']], dc))

    # per-pattern OOS accuracy (analogue direction), strongest patterns first
    pat = (V[V['analogue_dir']!=0].groupby('pattern')
           .apply(lambda g: pd.Series({'n':len(g),
                  'acc':(g['analogue_dir']==g['realized']).mean(),
                  'lb':wilson_lb(int((g['analogue_dir']==g['realized']).sum()), len(g))}),
                  include_groups=False)
           .reset_index().sort_values('lb', ascending=False))
    pat.to_csv('waveform_patterns_oos.csv', index=False)
    strong_pat = pat[(pat['n']>=8) & (pat['lb']>0.50)]
    print(f"── per-pattern OOS: {len(pat)} distinct patterns; "
          f"{len(strong_pat)} clear n>=8 & Wilson-LB>0.50 ──")
    for _, p in strong_pat.head(6).iterrows():
        print(f"  {p['pattern']:<14} n={int(p['n']):3d}  acc={p['acc']:5.1%}  LB={p['lb']:5.1%}")
    print("wrote odyssey_voice.csv, waveform_patterns_oos.csv")

P_MIN_SEG = 12   # need at least a short cycle before first decision

if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'SP500')

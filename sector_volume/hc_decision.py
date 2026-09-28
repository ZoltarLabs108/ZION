"""ENGINES + DECISION on the INTEGRATED Health Care signal (recipe steps 2-3 and 5, lib_pipeline.engines / decision, unmodified).
Engines = ODYSSEY (binned pattern analogue) and SANCTUARY (similarity-weighted analogue, permutation-scored), both on XLV's own
monthly returns, PIT. DECISION (recipe): convergence = integrated call kept only where SANCTUARY's direction agrees; scored on the
test block (last 35% of labelled months); ACTS iff Wilson-LB(z=1.645) > GATE 0.45, or the raw signal's own test LB > GATE.
Also reported: ODYSSEY agreement and the three-engine tally (integrated + ODYSSEY + SANCTUARY, >= 2 agree), the house Stage-4 form."""
import sys, os, json, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sector_recipe as SR, lib_pipeline as L
names = SR.install("XLV"); d = L.load_asset("US_Healthcare_Close", 1998, extra_vars=names, exclude_vars=["Copper_Close"], h_label=1)
I = pd.read_csv("results/stage3_hc/integrated_ledger.csv"); I["Date"] = pd.to_datetime(I.date)
rd = np.zeros(len(d)); src = {}
for r in I[I.call != 0].itertuples():
    idx = np.where(d.Date.values == np.datetime64(r.Date))[0]
    if len(idx): rd[idx[0]] = r.call; src[idx[0]] = r.source
mkt = d["mkt"].values; T = len(d)
eng = L.engines(d); odir, sdir, oconf, sdr = eng["odir"], eng["sdir"], eng["oconf"], eng["sdr"]
dec = L.decision(d, rd, eng)
def wlb95(p, n, z=1.96): return (p + z*z/(2*n) - z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)))/(1 + z*z/n) if n else 0
acted = [i for i in range(T) if rd[i] != 0 and not np.isnan(mkt[i]) and mkt[i] != 0]
U = [i for i in range(T) if not np.isnan(mkt[i]) and mkt[i] != 0]; TE = set(U[int(len(U)*0.65):])
print(f"integrated signal mapped: {len(acted)} acted months ({d.Date[acted[0]].date()} .. {d.Date[acted[-1]].date()}); all inside DECISION test block: {all(i in TE for i in acted)} (test block from {d.Date[min(TE)].date()})")
def acc(idx, sig): return (np.mean([sig[i] == mkt[i] for i in idx]) if idx else float('nan'), len(idx))
print(f"\nENGINES standalone on the same {len(acted)} months: ODYSSEY emits {sum(odir[i]!=0 for i in acted)} acc {acc([i for i in acted if odir[i]!=0], odir)[0]:.1%} | SANCTUARY emits {sum(sdir[i]!=0 for i in acted)} acc {acc([i for i in acted if sdir[i]!=0], sdir)[0]:.1%}")
print(f"ENGINES standalone, whole test block: ODYSSEY acc {acc([i for i in TE if odir[i]!=0], odir)[0]:.1%} (n {acc([i for i in TE if odir[i]!=0], odir)[1]}) | SANCTUARY acc {acc([i for i in TE if sdir[i]!=0], sdir)[0]:.1%} (n {acc([i for i in TE if sdir[i]!=0], sdir)[1]}) | up-rate test block {np.mean([mkt[i]>0 for i in TE]):.0%}")
print(f"\nDECISION (lib_pipeline.decision, GATE {L.GATE}): integrated test acc {dec['rd_acc']:.1%} (n {dec['rd_n']}, LB {dec['rd_lb']:.2f}) | convergence w/ SANCTUARY {dec['conv_acc']:.1%} (n {dec['conv_n']}, LB {dec['conv_lb']:.2f}) -> {'ACTS' if dec['acts'] or dec['rd_lb'] > L.GATE else 'ABSTAIN'}")
agree_s = [i for i in acted if sdir[i] == rd[i]]; dis_s = [i for i in acted if sdir[i] != 0 and sdir[i] != rd[i]]; sil_s = [i for i in acted if sdir[i] == 0]
agree_o = [i for i in acted if odir[i] == rd[i]]; dis_o = [i for i in acted if odir[i] != 0 and odir[i] != rd[i]]; sil_o = [i for i in acted if odir[i] == 0]
print(f"\nSANCTUARY vs integrated on acted months: agree {len(agree_s)} (acc {acc(agree_s, rd)[0]:.1%}), disagree {len(dis_s)} (integrated acc {acc(dis_s, rd)[0]:.1%}, SANCTUARY acc {acc(dis_s, sdir)[0]:.1%}), SANCTUARY silent {len(sil_s)} (integrated acc {acc(sil_s, rd)[0]:.1%})")
print(f"ODYSSEY   vs integrated on acted months: agree {len(agree_o)} (acc {acc(agree_o, rd)[0]:.1%}), disagree {len(dis_o)} (integrated acc {acc(dis_o, rd)[0]:.1%}, ODYSSEY acc {acc(dis_o, odir)[0]:.1%}), ODYSSEY silent {len(sil_o)} (integrated acc {acc(sil_o, rd)[0]:.1%})")
votes = {}
for i in acted:
    v = 1 + (odir[i] == rd[i]) + (sdir[i] == rd[i]); against = (odir[i] != 0 and odir[i] != rd[i]) + (sdir[i] != 0 and sdir[i] != rd[i])
    key = "unanimous 3/3" if v == 3 else ("2 of 3" if v == 2 else ("1 alone (others silent)" if against == 0 else "1 vs opposition"))
    votes.setdefault(key, []).append(i)
print("\nTHREE-ENGINE TALLY on the integrated acted months:")
for k in ("unanimous 3/3", "2 of 3", "1 alone (others silent)", "1 vs opposition"):
    idx = votes.get(k, []); a, n = acc(idx, rd); print(f"   {k:26s} n={n:3d}  integrated acc {a:.1%}  LB95 {wlb95(a, n):.0%}  up-rate {np.mean([mkt[i]>0 for i in idx]) if idx else float('nan'):.0%}")
maj = votes.get("unanimous 3/3", []) + votes.get("2 of 3", []); a, n = acc(maj, rd); print(f"   >=2 agree (house Stage-4 gate)  n={n}  acc {a:.1%}  LB95 {wlb95(a,n):.0%}")
# current row engines
li = T - 1; print(f"\ncurrent row {d.Date[li].date()}: ODYSSEY {int(odir[li]):+d} (conf {oconf[li] if not np.isnan(oconf[li]) else float('nan'):.2f}) | SANCTUARY {int(sdir[li]):+d} (perm-p {sdr[li] if hasattr(sdr,'__len__') else 'n/a'}) | integrated (Aug row) ABSTAIN")
json.dump(dict(dec={k: (float(v) if isinstance(v,(int,float,np.floating,np.integer,bool)) else None) for k, v in dec.items() if k != 'conv'}, tally={k: [len(v), acc(v, rd)[0]] for k, v in votes.items()},
               sanct=dict(agree=len(agree_s), dis=len(dis_s), silent=len(sil_s)), ody=dict(agree=len(agree_o), dis=len(dis_o), silent=len(sil_o)),
               cur=dict(date=str(d.Date[li].date()), ody=int(odir[li]), sanct=int(sdir[li]))), open("results/stage3_hc/decision.json", "w"), indent=1, default=float)

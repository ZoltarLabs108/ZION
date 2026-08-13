"""
ZION STAGE 4 — VALIDATION HARNESS for the SPY convergence gate.
The recipe forbids believing an isolated bright number until it clears:
  (C3) DRIFT baseline / EDGE   — SPY rises ~62%/mo; a call only counts if acc beats
        the always-up rate ON THE ACTED MONTHS. Report emitted-UP fraction + EDGE.
  (lift) AGREE vs DISAGREE     — the honest convergence mechanism: on months where
        RD & SANC are both present, is RD more accurate when they AGREE than DISAGREE?
        (Convergence changes nothing directionally on agreed months -> it is pure
         month-SELECTION; the lift is real only if agree-acc >> disagree-acc.)
  (C5) MAX-STAT PLACEBO        — permute the realized outcomes, re-run the SAME gate,
        1000 draws; p = tail. Preserves the marginal up-rate so it tests genuine
        predictability, not drift.
  TRUNCATION CHECK 2           — month accounting: pool == acted + abstained_with_reason.
"""
import pandas as pd, numpy as np
import engines as E
from convergence import build, gate_stream, record_gate, LB_BAR, N_FLOOR

RNG=np.random.default_rng(20260812)
m=build(); y=m.y.to_numpy(); N=len(m)

print("="*100)
print(f"ZION STAGE 4 VALIDATION — SPY convergence   spine months={N}  {m.Date.min().date()}..{m.Date.max().date()}")
print("="*100)

# ---- drift baseline (C3) ----
up_all=(y>0).mean()
print(f"[C3 drift]  full-spine up-rate (always-UP baseline) = {up_all*100:.1f}%   (this is the number to beat)")

def edge_report(stream, label):
    a=stream!=0; n=int(a.sum())
    if n==0: print(f"  {label}: acted=0"); return
    acc=(stream[a]==y[a]).mean()
    up_mkt=(y[a]>0).mean()                     # what always-UP scores on these months
    up_emit=(stream[a]>0).mean()               # how often the gate SAYS up
    print(f"  {label}: acted={n:4d}  acc={acc*100:5.1f}%  always-UP-here={up_mkt*100:4.1f}%  "
          f"EDGE={100*(acc-up_mkt):+5.1f}pp  emit-UP={up_emit*100:4.0f}%")

# rebuild the key 3-engine unanimous streams
agreed_u,_=gate_stream(m,['rd','od','sc'],'unanimous')
gated_u=record_gate(m,agreed_u)
agreed_maj,_=gate_stream(m,['rd','od','sc'],'majority')
gated_maj=record_gate(m,agreed_maj)
agreed_2,_=gate_stream(m,['rd','od'],'unanimous')

# RED DAWN standalone stream as a drift reference
rd_stream=np.where(m['rd'].notna(), m['rd'].fillna(0).astype(int), 0)

print("\n[EDGE vs drift]  (acc must beat always-UP-here, else it's just drift-capture)")
edge_report(rd_stream,        "RED DAWN standalone          ")
edge_report(agreed_2,         "2-eng RD+ODY   pure agree     ")
edge_report(agreed_u,         "3-eng unanimous pure agree    ")
edge_report(gated_u,          "3-eng unanimous GATED         ")
edge_report(agreed_maj,       "3-eng majority pure agree     ")

# ---- AGREE vs DISAGREE decomposition (the convergence mechanism) ----
print("\n[AGREE vs DISAGREE]  months where BOTH RD & SANC present (ODYSSEY usually absent):")
both=m['rd'].notna()&m['sc'].notna()
ag = both & (m['rd']==m['sc']); dis= both & (m['rd']!=m['sc'])
for nm,msk in [('BOTH present',both),('AGREE',ag),('DISAGREE',dis)]:
    mm=msk.to_numpy(); n=int(mm.sum())
    if n==0: continue
    # on agree months emitted=rd=sc; on disagree, RD's own call is the reference
    acc=(m['rd'].to_numpy()[mm]==y[mm]).mean(); up=(y[mm]>0).mean()
    print(f"  {nm:14s} n={n:4d}  RD-acc={acc*100:5.1f}%  always-UP={up*100:4.1f}%  EDGE={100*(acc-up):+5.1f}pp")
print("  -> convergence = act on AGREE, abstain on DISAGREE. Lift is real iff AGREE-EDGE >> DISAGREE-EDGE.")

# ---- MAX-STAT PLACEBO (C5) ----
def gate_acc(yv):
    """Recompute 3-eng unanimous pure-agreement accuracy under outcome vector yv."""
    # agreement pattern is FIXED (engine dirs unchanged); only outcomes permuted.
    a=agreed_u!=0
    return (agreed_u[a]==yv[a]).mean(), int(a.sum())

obs_acc,obs_n=gate_acc(y)
NP=2000
null=np.empty(NP)
for i in range(NP):
    yp=RNG.permutation(y)                      # preserves marginal up-rate
    null[i]=gate_acc(yp)[0]
p=(null>=obs_acc).mean()
print(f"\n[C5 placebo]  3-eng unanimous pure-agree: obs acc={obs_acc*100:.1f}% (n={obs_n})")
print(f"              permuted-null mean={null.mean()*100:.1f}%  95th pct={np.quantile(null,0.95)*100:.1f}%  max={null.max()*100:.1f}%")
print(f"              p(null>=obs) = {p:.4f}   {'PASS (<0.05)' if p<0.05 else 'FAIL — not distinguishable from drift-shuffled null'}")

# also placebo the GATED stream
ag2=gated_u!=0; obs2=(gated_u[ag2]==y[ag2]).mean(); n2=int(ag2.sum())
null2=np.array([(gated_u[ag2]==RNG.permutation(y)[ag2]).mean() for _ in range(NP)])
p2=(null2>=obs2).mean()
print(f"[C5 placebo]  3-eng unanimous GATED: obs acc={obs2*100:.1f}% (n={n2})  null mean={null2.mean()*100:.1f}%  p={p2:.4f}  {'PASS' if p2<0.05 else 'FAIL'}")

# ---- TRUNCATION CHECK 2: month accounting ----
# ---- DOWNSIDE SKILL: the only place edge can hide when emit-UP ~ drift ----
print("\n[DOWNSIDE skill]  the systems emit UP ~90-97%; any real edge lives in the rare DOWN calls.")
down_base=(y<0).mean()
print(f"  base DOWN-rate (full spine) = {down_base*100:.1f}%  -> a DOWN call must beat this to add value")
for nm,stream in [('RED DAWN',rd_stream),('3-eng unanimous pure',agreed_u),('3-eng unanimous GATED',gated_u)]:
    dn=stream==-1; n=int(dn.sum())
    if n==0: print(f"  {nm:22s} DOWN-calls=0"); continue
    hit=(y[dn]<0).mean()                       # fraction of DOWN calls where next month fell
    lb=E.wlb(int((y[dn]<0).sum()),n)
    print(f"  {nm:22s} DOWN-calls={n:3d}  hit-rate={hit*100:5.1f}%  LB={lb*100:4.0f}%  "
          f"EDGE_vs_base={100*(hit-down_base):+5.1f}pp")

print("\n[CHECK 2 month accounting]  3-eng unanimous, pure agreement:")
present=m[['rd','od','sc']].notna().sum(axis=1).to_numpy()
acted=agreed_u!=0
r_lt2 = int((present<2).sum())
r_split = int(((present>=2)&(~acted)).sum())
r_act = int(acted.sum())
print(f"  pool={N}  = acted {r_act}  + abstain[<2 engines present] {r_lt2}  + abstain[split/no-majority] {r_split}")
print(f"  reconciles: {r_act+r_lt2+r_split==N}")
print("="*100)

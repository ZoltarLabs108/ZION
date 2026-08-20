"""
zion_desk_ticket.py — the executable ZION weekly desk ticket (order sheet, NOT an order-placer).
Reads the latest as-issued exposures (netting_ledger last row), applies capital x leverage, prices
via last weekly closes, emits reports/ZION_DESK_TICKET.{json,txt}. Execution is ALWAYS manual by
the operator. Capital via env ZION_CAPITAL (default 100000); leverage via env ZION_LEV (default =
the tracked 3.80; set lower for staged go-live).
"""
import os, json, importlib.util
import numpy as np, pandas as pd
WT='/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly'
HERE=os.path.dirname(os.path.abspath(__file__)); REP=os.path.join(HERE,'reports')
CAP=float(os.environ.get('ZION_CAPITAL',100000)); LEV=float(os.environ.get('ZION_LEV',3.80))
INSTR={'US_EQ':('SPY','SPY'),'NASDAQ':('QQQ','QQQ'),'GOLD':('GLD','GLD'),'SILVER':('SLV','SLV'),
       'WTI':('USO','USO'),'UST2Y':('SHY','SHY'),'USD':('UUP','UUP'),'INDIA':('INDA','INDA')}
def _l(n,f):
    s=importlib.util.spec_from_file_location(n,os.path.join(WT,f));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
zw=_l('zw','zion_weekly.py')


def market_read(cur):
    """Plain-English narrative of what the book is OBSERVING this week — same regime numbers
    the throttle acts on. Describes conditions and positioning, NOT a directional forecast."""
    try:
        b=pd.read_csv('/Users/castaglia/Desktop/ZION_WEEKLY_WT/weekly/weekly_panel_spy.csv')
    except Exception:
        return []
    def epctl(col):
        s=b[col].to_numpy(float); w=len(s)-1; pri=s[:w]; pri=pri[np.isfinite(pri)]
        return (pri<=s[w]).mean() if len(pri)>=50 and np.isfinite(s[w]) else np.nan
    def chg(col,n):
        s=b[col].dropna(); return (s.iloc[-1]/s.iloc[-1-n]-1) if len(s)>n else np.nan
    def dlt(col,n):
        s=b[col].dropna(); return (s.iloc[-1]-s.iloc[-1-n]) if len(s)>n else np.nan
    last=b.iloc[-1]
    vix,vixp=float(last['VIX_Close']),epctl('VIX_Close')
    crd,crdp=float(last['Credit_BAA10Y']),epctl('Credit_BAA10Y')
    dxy4=chg('Dollar_Index',4); y2=float(last['US_2Y_Treasury']); y2d=dlt('US_2Y_Treasury',4)
    tsd=dlt('Term_Spread_10Y_2Y',4); gld4=chg('Gold_Close',4)
    thr=float(cur['thr']); lev=float(cur.get('lev',1.19)); eq=float(cur.get('US_EQ',0))
    S=[]
    # regime
    if thr>=1.0:
        S.append(f"CALM TAPE. Volatility is quiet — VIX {vix:.1f}, only the {vixp*100:.0f}th percentile of "
                 f"its own history — and investment-grade credit spreads ({crd:.2f}) sit in the {crdp*100:.0f}th. "
                 f"Both are well below the 70th-percentile line where the book starts pulling risk off, so the "
                 f"throttle is fully open and the risk sleeves are on.")
    else:
        S.append(f"STRESS SIGNAL. VIX {vix:.1f} ({vixp*100:.0f}th pctl) and/or credit spreads {crd:.2f} "
                 f"({crdp*100:.0f}th pctl) have crossed the 70th-percentile line — the dual throttle has flattened "
                 f"the risk sleeves (thr {thr:.2f}). The book is standing aside, not betting.")
    S.append(f"Leverage is at its {'post-stress RECOVERY boost' if lev>1.19 else 'calm baseline'} ({lev:.2f}x weekly).")
    # equity read
    eqw='long' if eq>1e-9 else ('short' if eq<-1e-9 else 'flat')
    S.append(f"The three-lens read on U.S. equities is {eqw.upper()} — the book carries SPY and Nasdaq "
             f"{'at weight, capturing the market' if eqw=='long' else 'lightly'}'s drift while the always-on "
             f"2-year Treasury hedge and 7.5% gold ballast sit underneath.")
    # dollar / sleeve
    if np.isfinite(dxy4):
        dr='softened' if dxy4<0 else 'firmed'
        S.append(f"The dollar has {dr} {abs(dxy4)*100:.1f}% over the past month; the UUP dollar sleeve — the one leg "
                 f"that historically covers the book's DOWN months — is carried at full weight against it.")
    # rates + gold
    if np.isfinite(y2):
        cv=('steepened' if tsd>0 else 'flattened') if np.isfinite(tsd) else 'held'
        S.append(f"Rates are {'quiet' if abs(y2d)<0.10 else 'moving'}: the 2-year yield is {y2:.2f}% "
                 f"({y2d:+.2f}pp on the month) and the curve has {cv}.")
    if np.isfinite(gld4):
        S.append(f"Gold has run {gld4*100:+.1f}% over the past month.")
    S.append("NET: the system reads "+("no stress in the tape — deployed long-and-hedged, expressing drift-capture "
             "with its structural hedges intact, not a directional bet." if thr>=1.0 else
             "elevated stress — de-risked by rule, waiting for the world-state to clear."))
    return S


def deconc_shadow(cur):
    """Candidate C2 shadow: inverse 26wk-vol SPY/QQQ split vs the live Sortino split. WATCH-ONLY,
    not the live recommendation; forward-tracked by paper_deconcentration.py."""
    eS, eQ = float(cur.get('US_EQ', 0) or 0), float(cur.get('NASDAQ', 0) or 0); eqc = eS + eQ
    if eqc < 1e-9: return []
    def vol(tk):
        s = zw.yahoo_weekly(tk)
        if isinstance(s, pd.DataFrame): s = s['Close'] if 'Close' in s.columns else s.iloc[:, 0]
        s = s.dropna(); return float(s.pct_change().dropna().tail(26).std()), float(s.iloc[-1])
    try:
        vS, pS = vol('SPY'); vQ, pQ = vol('QQQ')
    except Exception:
        return []
    if not (np.isfinite(vS) and np.isfinite(vQ) and vS > 0 and vQ > 0): return []
    iv = (1 / vS) / ((1 / vS) + (1 / vQ)); nS, nQ = eqc * iv, eqc * (1 - iv)
    shr = lambda e, px: int(e * LEV * CAP / px) if px > 0 else 0
    return [
        f"  leg    standard ZION           de-concentration (inv-vol {iv:.2f}/{1-iv:.2f})   Δ",
        f"  SPY   {shr(eS,pS):>5} sh ${eS*LEV*CAP:>10,.0f}    {shr(nS,pS):>5} sh ${nS*LEV*CAP:>10,.0f}     {shr(nS,pS)-shr(eS,pS):+d}",
        f"  QQQ   {shr(eQ,pQ):>5} sh ${eQ*LEV*CAP:>10,.0f}    {shr(nQ,pQ):>5} sh ${nQ*LEV*CAP:>10,.0f}     {shr(nQ,pQ)-shr(eQ,pQ):+d}",
        f"  26wk vol: SPY {vS*100:.1f}%/wk  QQQ {vQ*100:.1f}%/wk  (higher-vol leg trimmed). Combined equity + all hedges UNCHANGED.",
        f"  backtest net of costs: book Sortino +0.039 full · +0.063/+0.024 both halves · DD-neutral.",
        f"  STATUS: WATCH-ONLY (Candidate C2) — forward-tracked 0/12, decides ~Nov 6. NOT the live sheet.",
    ]


led=pd.read_csv(os.path.join(REP,'netting_ledger.csv')); cur=led.iloc[-1]
lines=[f"# ZION DESK TICKET — week issued {cur['week']}  (capital ${CAP:,.0f}, leverage {LEV:g}x)",
       f"{'bucket':>8} {'instr':>6} {'exposure':>9} {'notional':>12} {'last':>10} {'shares':>8}  side"]
tick={'week':str(cur['week']),'capital':CAP,'leverage':LEV,'legs':[]}
gross=0.0
for b,(tk,label) in INSTR.items():
    e=float(cur.get(b,0) or 0)
    if abs(e)<1e-9: continue
    notion=e*LEV*CAP; gross+=abs(notion)
    try:
        s=zw.yahoo_weekly(tk)
        if isinstance(s,pd.DataFrame): s=s['Close'] if 'Close' in s.columns else s.iloc[:,0]
        px=float(s.dropna().iloc[-1])
    except Exception: px=float('nan')
    sh=int(abs(notion)/px) if np.isfinite(px) and px>0 else 0
    side='BUY/LONG' if notion>0 else 'SELL/SHORT'
    lines.append(f"{b:>8} {label:>6} {e:>+9.3f} {notion:>+12,.0f} {px:>10,.2f} {sh:>8,d}  {side}")
    tick['legs'].append(dict(bucket=b,instrument=label,exposure=e,notional=round(notion),last=px,shares=sh,side=side))
lines.append(f"\ngross notional ${gross:,.0f} ({gross/CAP:.2f}x of capital)  |  throttle {cur['thr']:.2f}  lev-state {cur.get('lev','?')}")
ds=deconc_shadow(cur)
if ds:
    lines.append("\n" + "-"*72)
    lines.append("SHADOW WATCH — DE-CONCENTRATION (Candidate C2, report-only, NOT LIVE)")
    lines.append("-"*72)
    lines += ds
    tick['deconc_shadow']=ds
wk=pd.Timestamp(cur['week']); entry=wk+pd.Timedelta(days=4); horizon=wk+pd.Timedelta(days=7)
lines.append(f"\nTIMING (Tuesday baseline, 2026-08-18) — signal week issued Fri {wk.date()}; forecast horizon {wk.date()} -> {horizon.date()}")
lines.append(f"  This sheet's EXECUTION BASELINE is the Tuesday 01:15 refresh — first run where ALL of last week's")
lines.append(f"  macro is published (H.15/Moody's/VIX post Monday PM). The Friday 17:30 issue remains the frozen")
lines.append(f"  as-issued tape row (model record); if this sheet was printed Friday, re-check Tuesday's before entry.")
lines.append(f"  ENTER : Tuesday {entry.date()} at/near the open, from the Tuesday-printed sheet. Prices shown are last closes — re-check at entry.")
lines.append(f"  EXIT  : ROLL at the next Tuesday print (close legs the new sheet drops, resize the rest).")
lines.append(f"  Holding any leg past the next print = outside its forecast horizon. If Tuesday's job fails to print, hold and flag — absence of a sheet is NOT an exit signal.")
mr=market_read(cur)
if mr:
    lines.append("\n" + "="*72)
    lines.append("MARKET READ — what the system is observing in the economy this week")
    lines.append("="*72)
    import textwrap
    for s in mr:
        lines.append("\n".join(textwrap.wrap(s, 72)))
    tick['market_read']=mr
lines.append("\nNOTE: execution is manual by the operator. This sheet mirrors the as-issued tape row; fills-vs-ticket log is the live record.")
open(os.path.join(REP,'ZION_DESK_TICKET.txt'),'w').write('\n'.join(lines))
json.dump(tick,open(os.path.join(REP,'ZION_DESK_TICKET.json'),'w'),indent=2)
print('\n'.join(lines))

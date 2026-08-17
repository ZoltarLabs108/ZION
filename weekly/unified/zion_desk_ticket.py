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
lines.append("NOTE: execution is manual by the operator. This sheet mirrors the as-issued tape row; fills-vs-ticket log is the live record.")
open(os.path.join(REP,'ZION_DESK_TICKET.txt'),'w').write('\n'.join(lines))
json.dump(tick,open(os.path.join(REP,'ZION_DESK_TICKET.json'),'w'),indent=2)
print('\n'.join(lines))

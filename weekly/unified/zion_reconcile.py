"""
zion_reconcile.py — READ-ONLY fills-vs-ticket verification against the live Schwab account
(the AEGIS-bridge pattern, pointed at the ZION desk ticket). NEVER places, modifies, or cancels
orders — it only reads positions and compares them to the printed ticket.

Requires: ~/.schwab_token.json (7-day life; refresh via AEGIS/schwab_login_manual.py — operator-run)
and SCHWAB_API_KEY / SCHWAB_APP_SECRET (env, or parsed from ~/.zshrc without display).
Output: per-leg MATCH/PARTIAL/MISSING vs the ticket, extras flagged as previous-book holdings;
report appended to reports/reconcile_history.csv.
"""
import os, re, json, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, 'reports')
TOK = os.path.expanduser('~/.schwab_token.json')
SHARE_TOL = 0.02   # 2% share tolerance = MATCH

def _creds():
    k = os.environ.get('SCHWAB_API_KEY'); s = os.environ.get('SCHWAB_APP_SECRET')
    if k and s: return k, s
    try:
        txt = open(os.path.expanduser('~/.zshrc')).read()
        mk = re.search(r'export\s+SCHWAB_API_KEY=["\']?([^"\'\n]+)', txt)
        ms = re.search(r'export\s+SCHWAB_APP_SECRET=["\']?([^"\'\n]+)', txt)
        if mk and ms: return mk.group(1).strip(), ms.group(1).strip()
    except Exception: pass
    return None, None

def main():
    if not os.path.exists(TOK):
        print('✗ no token at ~/.schwab_token.json — run AEGIS/schwab_login_manual.py (operator).'); return 1
    k, s = _creds()
    if not (k and s):
        print('✗ SCHWAB_API_KEY / SCHWAB_APP_SECRET not found (env or ~/.zshrc).'); return 1
    try:
        from schwab.auth import client_from_token_file
        c = client_from_token_file(TOK, k, s)
        r = c.get_account_numbers(); r.raise_for_status()
        acct = r.json()[0]; h = acct['hashValue']; num = str(acct.get('accountNumber', ''))
        r = c.get_account(h, fields=c.Account.Fields.POSITIONS); r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f'✗ Schwab read failed: {type(e).__name__}: {e}')
        print('  If token expired (7-day wall): re-run AEGIS/schwab_login_manual.py.'); return 1
    sec = data.get('securitiesAccount', data)
    positions = {}
    for p in sec.get('positions', []):
        sym = p.get('instrument', {}).get('symbol', '?')
        qty = float(p.get('longQuantity', 0)) - float(p.get('shortQuantity', 0))
        mv = float(p.get('marketValue', 0))
        positions[sym] = dict(qty=qty, mv=mv)
    cash = sec.get('currentBalances', {}).get('cashBalance', None)
    tick = json.load(open(os.path.join(REP, 'ZION_DESK_TICKET.json')))
    print(f"# ZION RECONCILE — account …{num[-4:] if num else '????'} vs ticket wk {tick['week']} "
          f"(capital ${tick['capital']:,.0f} @ {tick['leverage']:g}x)")
    print(f"{'instr':>6} {'ticket sh':>10} {'held sh':>9} {'delta':>7} {'held $':>12}  verdict")
    rows = []; matched = 0
    tick_syms = set()
    for leg in tick['legs']:
        sym = leg['instrument']; tick_syms.add(sym)
        want = leg['shares'] * (1 if leg['side'].startswith('BUY') else -1)
        have = positions.get(sym, {}).get('qty', 0.0)
        mv = positions.get(sym, {}).get('mv', 0.0)
        if want == 0 and have == 0: v = 'FLAT-OK'
        elif have == 0: v = 'MISSING (not yet executed)'
        elif abs(have - want) <= max(1, abs(want) * SHARE_TOL): v = 'MATCH'; matched += 1
        else: v = f'PARTIAL ({have - want:+.0f} sh off)'
        print(f"{sym:>6} {want:>10,d} {have:>9,.0f} {have - want:>+7,.0f} {mv:>12,.2f}  {v}")
        rows.append(dict(week=tick['week'], instr=sym, ticket_sh=want, held_sh=have, mv=mv, verdict=v))
    extras = {s2: p for s2, p in positions.items() if s2 not in tick_syms and abs(p['qty']) > 0}
    if extras:
        print('\nheld but NOT on the ZION ticket (previous book / other holdings):')
        for s2, p in extras.items():
            print(f"{s2:>6} {'':>10} {p['qty']:>9,.0f} {'':>7} {p['mv']:>12,.2f}  EXTRA")
            rows.append(dict(week=tick['week'], instr=s2, ticket_sh=0, held_sh=p['qty'], mv=p['mv'], verdict='EXTRA'))
    if cash is not None: print(f"\ncash balance: ${cash:,.2f}")
    print(f"ticket legs matched: {matched}/{len(tick['legs'])}")
    hist = os.path.join(REP, 'reconcile_history.csv')
    df = pd.DataFrame(rows); df['checked'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
    df.to_csv(hist, mode='a', header=not os.path.exists(hist), index=False)
    print(f"[appended] reports/reconcile_history.csv")
    return 0

if __name__ == '__main__':
    sys.exit(main())

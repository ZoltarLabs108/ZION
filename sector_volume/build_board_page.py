#!/usr/bin/env python3
"""build_board_page.py — the SECTOR BOARD page: every sector's machinery and result in one table, the admitted block integrated into the
ZION universe (monthly and weekly level), and the dashboard-integration proposal. Reads results/<TK>/*.json and
results/portfolio_integration_all.json. Output: sector_board.html"""
import os, json, glob, html
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
ORDER = ["XLV", "XLY", "XLI", "XLF", "XLK", "XLE", "XLB", "XLP", "XLU"]
NAMES = {"XLV": "Health Care", "XLF": "Financials", "XLY": "Consumer Disc", "XLE": "Energy", "XLK": "Technology", "XLI": "Industrials", "XLP": "Cons Staples", "XLB": "Materials", "XLU": "Utilities"}
INT = json.load(open(os.path.join(RES, "portfolio_integration_all.json")))


def pct(x, d=1): return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x*100:.{d}f}%"


def load(tk):
    d = {}
    d["anchors"] = json.load(open(os.path.join(RES, tk, "oracle_anchors.json")))
    d["int"] = json.load(open(os.path.join(RES, tk, "integrated.json")))
    d["port"] = json.load(open(os.path.join(RES, tk, "portfolio.json")))
    d["dec"] = json.load(open(os.path.join(RES, tk, "decision.json"))) if os.path.exists(os.path.join(RES, tk, "decision.json")) else {}
    tape = pd.read_csv(os.path.join(RES, tk, f"{tk}_forward_tape.csv")).iloc[-1]; d["tape"] = tape
    tt = glob.glob(os.path.join(RES, tk, "stage3_anchored", "*_type_table.csv")); d["types"] = pd.read_csv(tt[0]) if tt else None
    cape = pd.read_csv(os.path.join(RES, f"{tk.lower()}_cape_monthly.csv")).dropna(subset=["CAPE10"]).iloc[-1]; d["cape"] = cape
    return d


rows = []; board = {}
for tk in ORDER:
    d = load(tk); a = d["anchors"]; i = d["int"]["integrated"]; p = d["port"]; t = d["tape"]
    sel = [r for r in a if r.get("eligible")]; sel = max(sel, key=lambda r: r["edge"]) if sel else None
    pulled = ",".join(f"T{x}" for x in (d["types"][d["types"].pulled].type.tolist() if d["types"] is not None else []))
    kind = "sleeve 5%" if (p.get("sizing") and p["sizing"].get("admit") and not str(t.get("label")) == "relative") else ("pair 2.5%/leg" if (p.get("sizing") and p["sizing"].get("admit")) else ("short-only overlay 5%" if (p.get("overlay") and p["overlay"].get("admit")) else "not admitted"))
    status = "ADMITTED" if kind != "not admitted" else ("WATCH (R2, tier only)" if i["acted"] and not sel else ("WATCH-NONE" if not i["acted"] else "ACTS, not admitted"))
    call = str(t.get("integrated_call", "ABSTAIN"))
    shares = (p.get("portfolio") or {}).get("ticket", {}).get("shares", 0) if p.get("portfolio") else 0
    edge = (i["acc"] - max(i["up_acted"], 1 - i["up_acted"])) if i.get("acc") is not None else None
    board[tk] = dict(name=NAMES[tk], anchor=(f"{sel['anchor'].replace('_', '/')} · {sel['label'][:3]}" if sel else "none (R1)"), cape=float(d["cape"].CAPE10), pulled=pulled or "—",
                     acted=i["acted"], scored=i["scored"], acc=i.get("acc"), lb=i.get("lb95"), longn=i.get("long_n", 0), shortn=i.get("short_n", 0), short_acc=i.get("short_down"), edge=edge,
                     dec=("ACTS" if d["dec"].get("acts") else ("—" if not i["acted"] else "no")), call=call, kind=kind, status=status, shares=shares,
                     corr=(p.get("sizing") or {}).get("corr_book"), sortino=((p.get("sizing") or {}).get("sleeve") or [None, None])[1])
tab = "".join(
    f"<tr class='{ 'adm' if b['status']=='ADMITTED' else ''}'><th scope=row><span class=tk>{tk}</span> {b['name']}</th><td>{b['anchor']}</td><td class=num>{b['cape']:.1f}</td><td class=sub>{b['pulled']}</td>"
    f"<td class=num>{b['acted']}<span class=sub>/{b['scored']}</span></td><td class=num>{pct(b['acc'])}</td><td class=num>{pct(b['lb'])}</td><td class=num>{b['longn']}<span class=sub> L</span> / {b['shortn']}<span class=sub> S</span></td>"
    f"<td class=num>{pct(b['short_acc'],0)}</td><td class='num {'pos' if (b['edge'] or 0)>0 else ''}'>{'—' if b['edge'] is None else f'{b['edge']*100:+.1f}'}</td><td>{b['dec']}</td>"
    f"<td><span class='call {'up' if b['call'].startswith(('UP','LONG')) else ('dn' if b['call'].startswith(('DOWN','SHORT')) else 'ab')}'>{html.escape(b['call'].split(' ')[0])}</span></td>"
    f"<td class=num>{'—' if b['corr'] is None else f'{b['corr']:+.2f}'}</td><td>{b['kind']}</td><td><span class='st {'adm' if b['status']=='ADMITTED' else 'w'}'>{b['status']}</span></td><td class=num>{b['shares'] if b['shares'] else '—'}</td></tr>"
    for tk, b in board.items())
# ---- backtest v OOS-validated (sequential re-derivation, R7): results/sequential/integration_compare.json
SEQ = json.load(open(os.path.join(RES, "sequential", "integration_compare.json"))) if os.path.exists(os.path.join(RES, "sequential", "integration_compare.json")) else None
SRC_LABEL = {"backtest": "backtest (ledger)", "seq-fixed": "sequential · anchor held", "seq-strict": "sequential · anchor by R1 monthly", "seq-fixed_e3": "sequential · held · embargo 3", "seq-strict_e3": "sequential · strict · embargo 3", "seq-fixed_h3": "sequential · held · 3-mo horizon", "seq-strict_h3": "sequential · strict · 3-mo horizon"}
seqtab = sequniv = seqblk = ""; seq_sources = []
if SEQ:
    seq_sources = ["backtest"] + [m for m in SEQ["modes"]]; recs = {r["sector"]: r for r in SEQ["records"]}
    def cell(r, src, k):
        key = f"{src}_{k}" if src != "backtest" else f"backtest_{k}"; v = r.get(key)
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        return f"{v:.0f}" if k in ("acted",) else (f"{v*100:+.1f}" if k == "edge" else f"{v*100:.1f}%")
    head = "<tr><th rowspan=2>Sector</th>" + "".join(f"<th colspan=4>{SRC_LABEL.get(src, src)}</th>" for src in seq_sources) + "</tr><tr>" + "".join("<th>acted</th><th>acc</th><th>LB95</th><th>edge</th>" for _ in seq_sources) + "</tr>"
    body = "".join(f"<tr class='{ 'adm' if board[tk]['status']=='ADMITTED' else ''}'><th scope=row><span class=tk>{tk}</span> {NAMES[tk]}</th>" + "".join(f"<td class=num>{cell(recs[tk], src, 'acted')}</td><td class=num>{cell(recs[tk], src, 'acc')}</td><td class=num>{cell(recs[tk], src, 'lb95')}</td><td class='num {'pos' if (recs[tk].get(('backtest_' if src=='backtest' else src+'_')+'edge') or 0) > 0 else ''}'>{cell(recs[tk], src, 'edge')}</td>" for src in seq_sources) + "</tr>" for tk in ORDER if tk in recs)
    seqtab = f"<div class=tablewrap><table><caption>Backtest v OOS-validated · per instrument · acted months, accuracy, Wilson LB95, edge vs the acted-months majority (points)</caption><thead>{head}</thead><tbody>{body}</tbody></table></div>"
    P = [r for r in SEQ["portfolio"] if r["window"] == "extended" and r["variant"].startswith("B equal-gross")]; ext = SEQ["windows"]["extended"]
    def prow(src, variant):
        rr = {r["lev"]: r for r in P if r["source"] == src and r["variant"] == variant}
        if not rr: return ""
        r1 = rr["1x"]; return f"<tr><th scope=row>{SRC_LABEL.get(src, src)}{' + sequential admission' if 'admission' in variant else ''}</th><td class=num>{pct(r1['CAGR'],1)}</td><td class=num><b>{r1['Sortino']:.2f}</b></td><td class=num>{pct(r1['MaxDD'],1)}</td><td class=num>{pct(rr['2.5x']['CAGR'],1)}</td><td class=num>{pct(rr['2.5x']['MaxDD'],1)}</td><td class=num>{pct(rr['4.0x']['CAGR'],1)}</td><td class=num>{pct(rr['4.0x']['MaxDD'],1)}</td><td class='num {'pos' if r1['dSortino']>0 else ''}'>{r1['dSortino']:+.2f}</td></tr>"
    base = next(r for r in P if r["lev"] == "1x"); b25 = next(r for r in P if r["lev"] == "2.5x"); b40 = next(r for r in P if r["lev"] == "4.0x")
    rows_u = f"<tr><th scope=row>universe, no block</th><td class=num>{pct(base['base_CAGR'],1)}</td><td class=num>{base['base_Sortino']:.2f}</td><td class=num>{pct(base['base_MaxDD'],1)}</td><td class=num>{pct(b25['base_CAGR'],1)}</td><td class=num>{pct(b25['base_MaxDD'],1)}</td><td class=num>{pct(b40['base_CAGR'],1)}</td><td class=num>{pct(b40['base_MaxDD'],1)}</td><td class=num>—</td></tr>"
    rows_u += "".join(prow(src, "B equal-gross") for src in seq_sources) + "".join(prow(src, "B equal-gross + sequential admission") for src in seq_sources if src.startswith("seq-strict"))
    sequniv = f"<div class=tablewrap><table><caption>Universe with the block · backtest v OOS-validated · 15% cap, equal gross · {ext[0]} → {ext[1]} ({ext[2]} months) · Sortino is leverage-invariant</caption><thead><tr><th></th><th>CAGR 1×</th><th>Sortino</th><th>MaxDD 1×</th><th>CAGR 2.5×</th><th>MaxDD 2.5×</th><th>CAGR 4.0×</th><th>MaxDD 4.0×</th><th>Δ Sortino</th></tr></thead><tbody>{rows_u}</tbody></table></div>"
    BL = [r for r in SEQ["block"] if r["window"] == "extended" and r["variant"] == "B equal-gross"] + [r for r in SEQ["block"] if r["window"] == "extended" and "admission" in r["variant"]]
    seqblk = "<div class=tablewrap><table><caption>Block only · 2.5× on $100k · equal gross</caption><thead><tr><th></th><th>active mo</th><th>up / down</th><th>mean $/mo</th><th>worst month</th><th>block MaxDD</th><th>block Sortino</th><th>down when universe down</th></tr></thead><tbody>" + "".join(f"<tr><th scope=row>{SRC_LABEL.get(r['source'], r['source'])}{' + sequential admission' if 'admission' in r['variant'] else ''}</th><td class=num>{r['active']}</td><td class=num>{r['up']} / {r['down']}</td><td class=num>{r['mean_usd']:+,.0f}</td><td class=num>{r['worst_usd']:+,.0f}</td><td class=num>{pct(r['block_MaxDD'],2)}</td><td class=num>{'—' if r['block_Sortino'] is None or (isinstance(r['block_Sortino'], float) and np.isnan(r['block_Sortino'])) else f'{r['block_Sortino']:.2f}'}</td><td class=num>{r['block_down_when_uni_down']} of {r['uni_down']}</td></tr>" for r in BL) + "</tbody></table></div>"
wC = INT["variants"]["C"]["weights"]; corr = INT["correlations"]; tabl = INT["table"]
def find(v, lev): return next(r for r in tabl if r["variant"].startswith(v) and r["lev"] == lev)
def rowU(lev, label):
    b = find("15% cap, Sortino", lev); return f"<tr><th scope=row>{label}</th><td class=num>{pct(b['base_CAGR'],2)}</td><td class=num>{b['base_Sortino']:.2f}</td><td class=num>{pct(b['base_MaxDD'],2)}</td><td class=num>{pct(b['CAGR'],2)}</td><td class=num><b>{b['Sortino']:.2f}</b></td><td class=num>{pct(b['MaxDD'],2)}</td><td class='num pos'>{b['Sortino']-b['base_Sortino']:+.2f}</td></tr>"
univ = "".join(rowU(l, lab) for l, lab in (("1x", "universe, 1× (tape basis)"), ("2.5x exec", "universe, 2.5× (executed)"), ("3.8x model", "universe, 3.8× (model)"), ("1x weekly leg", "weekly leg alone, 1×"), ("1x monthly leg", "monthly leg alone, 1×")))
var = "".join(f"<tr><th scope=row>{v}</th><td class=num>{r['gross']}</td><td class=num>{pct(r['CAGR'],2)}</td><td class=num>{r['Sortino']:.2f}</td><td class=num>{pct(r['MaxDD'],2)}</td></tr>" for v in ("as admitted", "15% cap, equal", "15% cap, Sortino", "15% cap, inverse") for r in [find(v, "1x")])
wrow = "".join(f"<tr><th scope=row><span class=tk>{tk}</span> {NAMES[tk]}</th><td>{INT['instruments'][tk]}</td><td class=num>{w*100:.2f}%</td><td class=num>{'—' if board[tk]['sortino'] is None else f'{board[tk]['sortino']:.2f}'}</td><td class=num>{corr[tk]['universe']:+.2f}</td><td class=num>{corr[tk]['weekly_leg']:+.2f}</td><td class=num>{corr[tk]['monthly_leg']:+.2f}</td></tr>" for tk, w in wC.items())
keys = list(INT["instruments"]); cm = "<tr><th></th>" + "".join(f"<th>{k}</th>" for k in keys) + "</tr>" + "".join("<tr><th>" + k + "</th>" + "".join(f"<td class='num {'hot' if (i!=j and abs(corr[k][k2])>=0.3) else ''}'>{corr[k][k2]:+.2f}</td>" for j, k2 in enumerate(keys)) + "</tr>" for i, k in enumerate(keys))
adm = [tk for tk, b in board.items() if b["status"] == "ADMITTED"]; u1 = find("15% cap, Sortino", "1x"); u25 = find("15% cap, Sortino", "2.5x exec")
page = f"""<title>ZION Sector Board</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#F5F6F8;--surface:#FFFFFF;--ink:#172033;--muted:#5B6577;--rule:#D9DEE6;--accent:#24519E;--pos:#1F6E3A;--neg:#8E3B22;--pill:#EEF1F5;--admbg:#EEF4FB;--hot:#FBEFE6}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0F141C;--surface:#161D28;--ink:#E6EAF0;--muted:#9AA6B8;--rule:#2A3442;--accent:#5F95DC;--pos:#6CC08A;--neg:#E07A8A;--pill:#202A38;--admbg:#182436;--hot:#3A2A22}}}}
:root[data-theme="dark"]{{--bg:#0F141C;--surface:#161D28;--ink:#E6EAF0;--muted:#9AA6B8;--rule:#2A3442;--accent:#5F95DC;--pos:#6CC08A;--neg:#E07A8A;--pill:#202A38;--admbg:#182436;--hot:#3A2A22}}
*{{box-sizing:border-box}} body{{background:var(--bg);color:var(--ink);font-family:"Source Serif 4",Georgia,serif;font-size:15px;line-height:1.5;margin:0}}
main{{max-width:1180px;margin:0 auto;padding:36px 24px 72px}}
h1,h2,h3{{font-family:Archivo,sans-serif;text-wrap:balance;margin:0;line-height:1.15}} h1{{font-size:2rem;font-weight:700}} h2{{font-size:1.3rem;font-weight:600;margin-top:48px;padding-top:16px;border-top:1px solid var(--rule)}} h3{{font-size:1rem;font-weight:600;margin-top:24px}}
.eyebrow{{font-family:Archivo,sans-serif;font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
p{{max-width:72ch;margin:10px 0}} .lede{{color:var(--muted);font-size:1.02rem}}
.strip{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0 8px}} .strip>div{{background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:12px 14px}}
.strip .k{{font-family:Archivo,sans-serif;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}} .strip .v{{font-family:Archivo,sans-serif;font-size:1.25rem;font-weight:600;margin-top:4px}} .strip .s{{font-size:.84rem;color:var(--muted)}}
.tablewrap{{overflow-x:auto;background:var(--surface);border:1px solid var(--rule);border-radius:6px;margin:12px 0}}
table{{border-collapse:collapse;width:100%;font-size:.83rem;font-variant-numeric:tabular-nums}} caption{{text-align:left;font-family:Archivo,sans-serif;font-size:.78rem;color:var(--muted);padding:10px 12px 4px;caption-side:top}}
th,td{{padding:6px 9px;border-top:1px solid var(--rule);text-align:left;white-space:nowrap;vertical-align:top}} thead th{{font-family:Archivo,sans-serif;font-size:.68rem;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);border-top:none}} tbody th{{font-weight:400}}
td.num{{text-align:right;font-family:"JetBrains Mono",monospace;font-size:.8rem}} .tk{{font-family:"JetBrains Mono",monospace;font-weight:500;color:var(--accent)}} .sub{{color:var(--muted);font-size:.74rem}}
.pos{{color:var(--pos)}} .neg{{color:var(--neg)}} tr.adm td,tr.adm th{{background:var(--admbg)}} td.hot{{background:var(--hot)}}
.call{{font-family:Archivo,sans-serif;font-size:.68rem;letter-spacing:.06em;padding:2px 7px;border-radius:3px;background:var(--pill)}} .call.up{{color:var(--pos)}} .call.dn{{color:var(--neg)}} .call.ab{{color:var(--muted)}}
.st{{font-family:Archivo,sans-serif;font-size:.66rem;letter-spacing:.05em;padding:2px 6px;border-radius:3px;background:var(--pill);color:var(--muted)}} .st.adm{{color:var(--accent);font-weight:600}}
ul{{max-width:76ch;padding-left:22px}} li{{margin:6px 0}} .note{{border-left:3px solid var(--accent);padding:6px 14px;background:var(--surface);margin:16px 0;max-width:76ch}}
code{{font-family:"JetBrains Mono",monospace;font-size:.84em;background:var(--pill);padding:1px 5px;border-radius:3px}}
@media (max-width:820px){{.strip{{grid-template-columns:1fr 1fr}}}}
</style>
<main>
<div class=eyebrow>ZION · sector system · runner results as of 2026-09-14 · shadow, 0% real capital, tapes open</div>
<h1>ZION Sector Board</h1>
<p class=lede>Nine SPDR sectors run through one procedure: sector CAPE from SEC filings, four valuation anchors typed the S&amp;P way, Stage-3 type pulls, a type-agnostic second instrument, DECISION with the engines, CASSANDRA, sizing against the book and shadow netting. Every constant is fixed across sectors; the rules that admit an instrument are the same for all nine. Section A is the board; Section B is what the admitted block does to the whole ZION universe.</p>
<div class=strip>
<div><div class=k>Admitted instruments</div><div class=v>{len(adm)} of 9</div><div class=s>{', '.join(adm)}</div></div>
<div><div class=k>Universe Sortino, 1×</div><div class=v>{u1['base_Sortino']:.2f} → {u1['Sortino']:.2f}</div><div class=s>backtest; sequential: 8.65 anchor held · 7.85 strict · 7.29 with sequential admission</div></div>
<div><div class=k>Universe CAGR, 1× / 2.5× executed</div><div class=v>{pct(u1['base_CAGR'])} → {pct(u1['CAGR'])}</div><div class=s>{pct(u25['base_CAGR'])} → {pct(u25['CAGR'])} at 2.5× (backtest); sequential 63.8% held · 61.0% strict</div></div>
<div><div class=k>Universe MaxDD, 1×</div><div class=v>{pct(u1['base_MaxDD'],2)} → {pct(u1['MaxDD'],2)}</div><div class=s>2021-06 → 2026-07, 62 months</div></div>
</div>

<h2>A. The sector board</h2>
<p>One row per sector. Anchor is the valuation ratio the rules selected (label: abs = sector direction, rel = sector minus SPY); CAPE10 is the sector's own cyclically adjusted P/E today; pulled types are the Stage-3 cells admitted (WF &gt; 67.5%, n ≥ 8); acted/scored, accuracy and Wilson LB95 in this table are the integrated instrument's <b>backtest ledger</b> (pull set and anchor chosen on the whole record — R4/R7); the OOS-validated (sequential) record is the table that follows; edge is accuracy minus the majority-class rate of the acted months (a constant call's score); the call is this month's as-issued read; shadow shares are the position a $100k book at 2.5× would carry. Shaded rows are admitted to the book.</p>
<div class=tablewrap><table><caption>Sector board · backtest ledger (full-record pull set) · windows 2019-10 or 2020-05 → 2026-07 · the OOS-validated record is in A2</caption>
<thead><tr><th>Sector</th><th>Anchor · label</th><th>CAPE10</th><th>Pulled types</th><th>Acted</th><th>Acc</th><th>LB95</th><th>Long / short</th><th>Short acc</th><th>Edge vs majority</th><th>DECISION</th><th>Call now</th><th>Corr to book</th><th>Instrument</th><th>Status</th><th>Shadow sh</th></tr></thead>
<tbody>{tab}</tbody></table></div>

<h3>A2. Backtest v OOS-validated (R7, as in ZION)</h3>
<p>The ledger above marks a month as a pull if its type cleared the pull bar over the <i>whole</i> record, and the anchor was chosen on the whole record. The sequential re-derivation refits everything on the panel truncated at each decision month — the pull set, the cascade, the tier admission and (strict) the anchor — and takes the call the runner would have issued that month. That record, not the ledger, is the evidence the rules admit on. "Embargo 3" trains only through t−3 (ZION's locked frontier); "3-mo horizon" is reported for interest, the method's horizon is one month. Edge is accuracy minus the majority-class rate of the acted months.</p>
{seqtab}
<ul>
<li><b>Two-sided instruments</b> (Health Care, Consumer Discretionary, Industrials, Technology) all get their shorts from the same cell, T2: valuation and price falling with growth flat — the de-rating signature. Materials has it too but is too thin to admit.</li>
<li><b>Long-selection</b> (Financials): accuracy equals the up-rate of the months it chooses; what it earns is selecting months that rise 69% of the time against 59% for the window.</li>
<li><b>Short-relative pair</b> (Energy): its valuation says when Energy lags the market, almost never when it leads; 2.5% per leg, SPY leg netted.</li>
<li><b>Short-only overlay</b> (Technology): the full instrument fails the correlation gate on its long side (+0.71 with the book), so only its shorts enter, unthrottled, hedge-class.</li>
<li><b>Not admitted:</b> Utilities and Consumer Staples (growth leg ill-conditioned — multi-year real-earnings declines inside the windows; Staples' type-agnostic tier qualifies but a tier alone is WATCH by rule), Materials (passes correlation, fails the throttled lift).</li>
</ul>

<h2>B. The admitted block inside the ZION universe</h2>
<p>Six instruments at their admitted sizes would total 30% gross, twice the 15% sector cap (R5). The cap is allocated three ways; the Sortino-weighted variant is the one carried below (house convention: static weights, no conviction multipliers). Sleeves are flat while the dual throttle is stressed; the Technology overlay is unthrottled.</p>
<div class=tablewrap><table><caption>Sortino-weighted allocation of the 15% cap (variant C)</caption>
<thead><tr><th>Instrument</th><th>Kind</th><th>Notional weight</th><th>Own Sortino</th><th>Corr · universe</th><th>Corr · weekly leg</th><th>Corr · monthly leg</th></tr></thead><tbody>{wrow}</tbody></table></div>
<div class=tablewrap><table><caption>What the block does to the universe and to each leg · monthly basis, down-months Sortino · 2021-06 → 2026-07</caption>
<thead><tr><th></th><th>CAGR</th><th>Sortino</th><th>MaxDD</th><th>CAGR with block</th><th>Sortino with block</th><th>MaxDD with block</th><th>Δ Sortino</th></tr></thead><tbody>{univ}</tbody></table></div>
<div class=tablewrap><table><caption>Allocation variants · universe 1×</caption><thead><tr><th>Variant</th><th>Gross</th><th>CAGR</th><th>Sortino</th><th>MaxDD</th></tr></thead><tbody>{var}</tbody></table></div>
<h3>Backtest v OOS-validated · the universe with the block</h3>
<p>Same instruments, same equal-gross weights under the 15% cap, the block's calls taken from each source; extended window from the first decision month (zeros before an instrument's first call). The "sequential admission" row keeps an instrument out until its own sequential record has twelve resolved months clearing the DECISION bound, edge, correlation and lift gates — the book as the rules would actually have built it.</p>
{sequniv}
{seqblk}
<h3>Weekly level</h3>
<p>The locked weekly book at its own leverage, with the sector block's positions held across the weeks of each decision month (variant C). Weekly-basis Sortino is shown for reference only; the house headline is the same series aggregated to months, because a √52 annualisation of a sparse weekly stream inflates it.</p>
<div class=tablewrap><table><thead><tr><th></th><th>Weekly basis · CAGR</th><th>Sortino</th><th>MaxDD</th><th>Aggregated to months · CAGR</th><th>Sortino</th><th>MaxDD</th></tr></thead>
<tbody><tr><th scope=row>weekly book × lev</th><td class=num>24.12%</td><td class=num>3.47</td><td class=num>−9.93%</td><td class=num>24.15%</td><td class=num>4.07</td><td class=num>−9.81%</td></tr>
<tr><th scope=row>weekly book + sector block</th><td class=num>27.68%</td><td class=num>3.99</td><td class=num>−8.85%</td><td class=num>27.72%</td><td class=num><b>5.01</b></td><td class=num>−8.85%</td></tr></tbody></table></div>
<h3>Correlation among the admitted instruments</h3>
<div class=tablewrap><table><thead>{cm.split('</tr>',1)[0]}</tr></thead><tbody>{cm.split('</tr>',1)[1]}</tbody></table></div>
<p>Shaded cells are |corr| ≥ 0.30: Consumer Discretionary with Technology (+0.47) and Industrials (+0.41), Technology with Industrials (+0.32) — the three sectors that share the de-rating short cell fire together in the same months. Everything else is near zero, and the block as a whole correlates −0.17 to −0.32 with the universe: it is diversification first.</p>
<div class=note><p><b>Gross.</b> With the whole block at the cap: netted gross max 1.63× (house cap 2.0× holds), mean 1.00×; at the 3.8× model leverage the peak is 6.21× against the 6.0× universe cap — the base book itself peaks at 5.67×, so the block adds 0.54× in the worst week and the R5p clip would apply; at the executed 2.5× the peak is 4.09×. Sector block gross never exceeds 0.28×.</p></div>

<h2>C. How CAGR and Sortino land in the final calculation</h2>
<ul>
<li><b>Sortino is the number the house sizes on, and it moves first.</b> At the 15% cap the universe Sortino goes from 7.30 to 8.79 (1×, monthly, down-months), and it is leverage-invariant, so the same +1.49 applies at the executed 2.5× and the 3.8× model. The weekly leg on its own goes 4.26 → 4.86, the monthly leg 1.47 → 2.36; the weekly book measured week by week goes 4.07 → 5.01 on the monthly-aggregated basis.</li>
<li><b>CAGR follows the leverage.</b> At 1× the block adds 3.7 points (21.1% → 24.8%); at the executed 2.5× that is 58.5% → 70.6%; at 3.8× 97.2% → 120.2%. These are the backtest series, not the tape; the honest figure is the 1× tape basis, and financing is unmodelled.</li>
<li><b>Drawdown improves at every leverage</b> (−3.56% → −2.75% at 1×; −8.78% → −6.84% at 2.5×) because the block's correlation with the universe is negative in the book's down-months — the shorts and the short-relative pair are where that comes from.</li>
<li><b>What the number is and is not.</b> Every instrument's pull membership is chosen on its full record (R4); the common window is 62 months; the six-instrument combination was not itself selected — the rules admitted it — but its joint weights are in-sample. The forward tapes opened 2026-09-13 are the evidence channel, and real capital stays at 0% until they resolve, as with every sleeve before this one.</li>
</ul>

<h2>D. Dashboard integration — proposal (not wired)</h2>
<ul>
<li><b>A new "Sectors" section</b> under the existing US Domestic Markets board, fed by <code>results/&lt;TK&gt;/&lt;TK&gt;_forward_tape.csv</code> and a board JSON written by a <code>gen_sector_board.py</code> in <code>reports_gen/</code>: the Section-A table above, one row per sector, with the as-issued call, the instrument kind, the status pill, and the conviction shown as the instrument's LB95 (not the old valb star — the sector system's evidence is the sequential bound).</li>
<li><b>Current calls as the operator reads them:</b> UP / DOWN for sleeves, LONG-REL / SHORT-REL for the pair, ON / OFF for the overlay, ABSTAIN otherwise; a "thin source" flag when a call comes from the post-type cascade rather than a pulled type (Industrials this month).</li>
<li><b>Inside the integrated portfolio view:</b> one added row "universe + sector block" beside the existing universe row, carrying the 1× and 2.5× CAGR / Sortino / MaxDD from Section B, and a sector-block line on the desk ticket listing the shadow legs (this month: XLV +90, XLF +260, XLI +86, XLK −79 shares; Energy and Discretionary abstain) marked SHADOW, exactly as the de-concentration candidate is shown today.</li>
<li><b>Monthly emission</b> of the nine tapes needs a scheduled job; per the jobs inventory that is a production change requiring explicit authorisation, as is any edit to <code>refresh_reports.sh</code>, the netting ledger, the desk ticket or the locked book spec.</li>
<li><b>Gates before anything leaves shadow:</b> 12 resolved tape months per instrument; the block's Sortino lift holding on the tape; the sector cap and the R5p clip enforced in the live netting; the standard leverage-ladder gates unchanged.</li>
</ul>
<p class=sub>Method document: <code>ZION/sector_volume/SECTOR_METHOD_HEALTHCARE.md</code> (procedure §7, rules §8, sector results §9, re-verification §10, integration §11). Runner: <code>sector_runner.py &lt;TK&gt;</code>. Integration: <code>portfolio_integration_all.py</code>.</p>
</main>"""
open(os.path.join(HERE, "sector_board.html"), "w").write(page); json.dump(board, open(os.path.join(RES, "sector_board.json"), "w"), indent=1, default=float); print("board page written; admitted:", adm)

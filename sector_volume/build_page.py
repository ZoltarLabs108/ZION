#!/usr/bin/env python3
"""build_page.py — compose the Sector Volume & Rotation report (HTML artifact) from results/*.json."""
import os, json, glob, html
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "sector_rotation_report.html")
ORDER = ["XLK", "XLF", "XLV", "XLE", "XLI", "XLP", "XLY", "XLB", "XLU"]
VARIANTS = ["base_all", "vol_all", "base_timely", "vol_timely"]
QORDER = ["IMPROVING", "LEADING", "WEAKENING", "LAGGING"]
QLABEL = {"IMPROVING": "Rises", "LEADING": "Maintains", "WEAKENING": "Falls", "LAGGING": "Lags"}
QCLASS = {"IMPROVING": "q-imp", "LEADING": "q-lea", "WEAKENING": "q-wea", "LAGGING": "q-lag"}


def pct(x, d=1):
    return "—" if x is None else f"{x * 100:.{d}f}%"


def load():
    R = {}
    for f in glob.glob(os.path.join(RES, "*_*.json")):
        if os.path.basename(f).startswith("rrg"): continue
        j = json.load(open(f)); s = j["summary"]; R.setdefault(s["tk"], {})[s["variant"]] = j
    G = json.load(open(os.path.join(RES, "rrg.json")))
    GS = {k: json.load(open(os.path.join(RES, f"rrg_s{k}.json"))) for k in (4, 8)}
    return R, G, GS


def call_txt(c):
    return {1: "BUY", -1: "SELL", 0: "ABSTAIN"}[int(c)]


def board_table(R, variants, caption):
    hdr = "".join(f"<th colspan=5 class=grp>{v.replace('_', ' ').replace('base', 'no volume').replace('vol', '+ volume').replace('all', '· all vars').replace('timely', '· timely vars')}</th>" for v in variants)
    sub = "".join("<th>acted</th><th>acc</th><th>LB95</th><th>edge</th><th>call</th>" for _ in variants)
    rows = []
    for tk in ORDER:
        cells = [f"<th scope=row><span class=tk>{tk}</span> {R[tk][variants[0]]['summary']['name']}</th>"]
        for v in variants:
            s = R[tk][v]["summary"]
            lb = s["wilson_lb95"]; clears = lb is not None and lb > 0.5
            edge = s["edge_vs_drift_acted"]
            cc = s["current_call"]["call"]
            cells.append(f"<td class=num>{s['n_acted']}<span class=sub>/{s['n_oos']}</span></td>"
                         f"<td class=num>{pct(s['acc'])}</td>"
                         f"<td class='num {'ok' if clears else ''}'>{pct(lb)}</td>"
                         f"<td class='num {'neg' if (edge is not None and edge < 0) else ''}'>{'—' if edge is None else f'{edge*100:+.1f}'}</td>"
                         f"<td><span class='call c{cc}'>{call_txt(cc)}</span></td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"""<div class=tablewrap><table class=board><caption>{caption}</caption>
<thead><tr><th rowspan=2>Sector</th>{hdr}</tr><tr>{sub}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""


def xlp_section(R):
    s = {v: R["XLP"][v]["summary"] for v in VARIANTS}
    rows = "".join(
        f"<tr><th scope=row>{v.replace('base', 'no volume').replace('vol', '+ volume').replace('_all', ' · all vars').replace('_timely', ' · timely vars')}</th>"
        f"<td class=num>{s[v]['n_acted']}</td><td class=num>{pct(s[v]['coverage'])}</td><td class=num>{pct(s[v]['acc'])}</td>"
        f"<td class=num>{pct(s[v]['wilson_lb95'])}</td><td class=num>{pct(s[v]['drift_acted'])}</td>"
        f"<td class=num>{'—' if s[v]['edge_vs_drift_acted'] is None else f'{s[v]['edge_vs_drift_acted']*100:+.1f}'}</td>"
        f"<td class=num>{s[v]['vol_leg_months']}</td><td class=num>{pct(s[v]['vol_leg_acc'])}</td><td class=num>{pct(s[v]['share_of_fits_with_vol_round'], 0)}</td></tr>"
        for v in VARIANTS)
    return f"""<div class=tablewrap><table class=board>
<caption>Consumer Staples (XLP), sequential next-month walk-forward, {s['base_all']['oos_window'][0]} to {s['base_all']['oos_window'][1]} ({s['base_all']['n_oos']} scored months)</caption>
<thead><tr><th>Variant</th><th>acted</th><th>coverage</th><th>accuracy</th><th>Wilson LB95</th><th>drift on acted</th><th>edge</th><th>volume-leg months</th><th>volume-leg acc</th><th>fits using a volume cell</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""


def rrg_svg(G, gid="raw"):
    # domain 70..130 both axes; 640x520 drawing with margins
    W, H = 640, 520; ml, mr, mt, mb = 56, 24, 28, 48
    pw, ph = W - ml - mr, H - mt - mb
    lo, hi = 70, 130
    def X(v): return ml + (min(max(v, lo), hi) - lo) / (hi - lo) * pw
    def Y(v): return mt + ph - (min(max(v, lo), hi) - lo) / (hi - lo) * ph
    parts = []
    # quadrant tints
    cx, cy = X(100), Y(100)
    parts.append(f'<rect x="{cx}" y="{mt}" width="{ml+pw-cx}" height="{cy-mt}" class="qt q-lea"/>')
    parts.append(f'<rect x="{ml}" y="{mt}" width="{cx-ml}" height="{cy-mt}" class="qt q-imp"/>')
    parts.append(f'<rect x="{ml}" y="{cy}" width="{cx-ml}" height="{mt+ph-cy}" class="qt q-lag"/>')
    parts.append(f'<rect x="{cx}" y="{cy}" width="{ml+pw-cx}" height="{mt+ph-cy}" class="qt q-wea"/>')
    for t in range(lo, hi + 1, 10):
        parts.append(f'<line x1="{X(t)}" y1="{mt}" x2="{X(t)}" y2="{mt+ph}" class="grid"/>')
        parts.append(f'<line x1="{ml}" y1="{Y(t)}" x2="{ml+pw}" y2="{Y(t)}" class="grid"/>')
        parts.append(f'<text x="{X(t)}" y="{mt+ph+16}" class="tick" text-anchor="middle">{t}</text>')
        parts.append(f'<text x="{ml-8}" y="{Y(t)+4}" class="tick" text-anchor="end">{t}</text>')
    parts.append(f'<line x1="{cx}" y1="{mt}" x2="{cx}" y2="{mt+ph}" class="axis"/>')
    parts.append(f'<line x1="{ml}" y1="{cy}" x2="{ml+pw}" y2="{cy}" class="axis"/>')
    parts.append(f'<text x="{ml+pw-6}" y="{mt+16}" class="qlabel" text-anchor="end">LEADING · maintains</text>')
    parts.append(f'<text x="{ml+6}" y="{mt+16}" class="qlabel">IMPROVING · rises</text>')
    parts.append(f'<text x="{ml+6}" y="{mt+ph-8}" class="qlabel">LAGGING · lags</text>')
    parts.append(f'<text x="{ml+pw-6}" y="{mt+ph-8}" class="qlabel" text-anchor="end">WEAKENING · falls</text>')
    parts.append(f'<text x="{ml+pw/2}" y="{H-8}" class="axname" text-anchor="middle">RS-Ratio · relative strength vs SPY, 100 = its own trailing-year average</text>')
    parts.append(f'<text transform="translate(14,{mt+ph/2}) rotate(-90)" class="axname" text-anchor="middle">RS-Momentum · 13-week change, 100 = flat</text>')
    for tk in ORDER:
        s = G["sectors"][tk]; tail = s["tail"]
        pts = " ".join(f"{X(p['rsr']):.1f},{Y(p['rsm']):.1f}" for p in tail)
        cls = QCLASS[s["current"]["quadrant"]]
        parts.append(f'<polyline points="{pts}" class="tail {cls}"/>')
        for p in tail[:-1]:
            parts.append(f'<circle cx="{X(p["rsr"]):.1f}" cy="{Y(p["rsm"]):.1f}" r="2.2" class="dot {cls}"/>')
        e = tail[-1]
        parts.append(f'<g class="head" data-tk="{tk}" data-g="{gid}" tabindex="0"><circle cx="{X(e["rsr"]):.1f}" cy="{Y(e["rsm"]):.1f}" r="12" class="hit"/>'
                     f'<circle cx="{X(e["rsr"]):.1f}" cy="{Y(e["rsm"]):.1f}" r="5.5" class="headdot {cls}"/>'
                     f'<text x="{X(e["rsr"])+8:.1f}" y="{Y(e["rsm"])-7:.1f}" class="tklabel">{tk}</text></g>')
    return f'<svg viewBox="0 0 {W} {H}" class="rrg" role="img" aria-label="Relative rotation graph, nine sectors versus SPY, 13-week tails">{"".join(parts)}</svg>'


def ribbon_svg(G):
    # each sector: one row of 4-week samples as rects, colored by quadrant
    rows = ORDER; n = len(G["sectors"][rows[0]]["history"])
    cw = 2.6; W = 70 + n * cw + 8; rh = 16; H = 20 + len(rows) * (rh + 6)
    parts = []
    hist0 = G["sectors"][rows[0]]["history"]
    yrs_done = set()
    for i, h in enumerate(hist0):
        y = h["d"][:4]
        if y not in yrs_done and int(y) % 4 == 0 and h["d"][5:7] in ("01", "02"):
            yrs_done.add(y); parts.append(f'<text x="{70+i*cw:.1f}" y="12" class="tick">{y}</text>')
    for r, tk in enumerate(rows):
        y0 = 20 + r * (rh + 6)
        parts.append(f'<text x="0" y="{y0+12}" class="tklabel">{tk}</text>')
        for i, h in enumerate(G["sectors"][tk]["history"]):
            parts.append(f'<rect x="{70+i*cw:.1f}" y="{y0}" width="{cw+0.3:.1f}" height="{rh}" class="cell {QCLASS[h["q"]]}"><title>{tk} {h["d"]} {h["q"]}</title></rect>')
    return f'<svg viewBox="0 0 {W:.0f} {H}" class="ribbon" role="img" aria-label="Quadrant occupancy over time, one row per sector, sampled every four weeks">{"".join(parts)}</svg>'


def smooth_compare(ALLG):
    rows = []
    for g, title in (("raw", "raw (no smoothing)"), ("s4", "4-week EMA"), ("s8", "8-week EMA")):
        V = ALLG[g]; S = V["sectors"]
        med = lambda q: np.median([S[t]["quadrants"][q]["median_wk"] for t in ORDER])
        mean = lambda q: np.mean([S[t]["quadrants"][q]["mean_wk"] for t in ORDER])
        cw = np.mean([S[t]["clockwise_share"] for t in ORDER])
        hit = np.mean([S[t]["quadrants"][q]["fwd13_hit"] for t in ORDER for q in ("LEADING", "IMPROVING")])
        hitn = np.mean([S[t]["quadrants"][q]["fwd13_hit"] for t in ORDER for q in ("LAGGING", "WEAKENING")])
        exc = np.mean([S[t]["quadrants"][q]["fwd13_excess_pct"] for t in ORDER for q in ("LEADING", "IMPROVING")])
        excn = np.mean([S[t]["quadrants"][q]["fwd13_excess_pct"] for t in ORDER for q in ("LAGGING", "WEAKENING")])
        rows.append(f"<tr><th scope=row>{title}</th>"
                    f"<td class=num>{med('IMPROVING'):.0f} / {mean('IMPROVING'):.1f}</td><td class=num>{med('LEADING'):.0f} / {mean('LEADING'):.1f}</td>"
                    f"<td class=num>{med('WEAKENING'):.0f} / {mean('WEAKENING'):.1f}</td><td class=num>{med('LAGGING'):.0f} / {mean('LAGGING'):.1f}</td>"
                    f"<td class=num>{V['market']['cycle_weeks_median']:.0f} / {V['market']['cycle_weeks_mean']:.0f}</td>"
                    f"<td class=num>{cw*100:.0f}%</td><td class=num>{exc:+.2f}% · {hit*100:.0f}%</td><td class=num>{excn:+.2f}% · {hitn*100:.0f}%</td></tr>")
    return f"""<div class=tablewrap><table class=board>
<caption>Effect of smoothing on the rotation's behaviour — spell lengths are median / mean weeks averaged over the nine sectors; forward columns are the next-13-week excess return over SPY and its hit rate, pooled over the two gaining quadrants and the two losing quadrants</caption>
<thead><tr><th>Momentum input</th><th>Rises</th><th>Maintains</th><th>Falls</th><th>Lags</th><th>Full cycle</th><th>Exits clockwise</th><th>Fwd 13 wk, gaining quadrants</th><th>Fwd 13 wk, losing quadrants</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def now_row(ALLG):
    cells = []
    for tk in ORDER:
        qs = [ALLG[g]["sectors"][tk]["current"] for g in ("raw", "s4", "s8")]
        cells.append("<tr><th scope=row><span class=tk>" + tk + "</span></th>" + "".join(
            f"<td><span class='qpill {QCLASS[c['quadrant']]}'>{QLABEL[c['quadrant']]}</span> <span class=sub>{c['weeks_in']} wk</span></td>" for c in qs) + "</tr>")
    return f"""<div class=tablewrap><table class=board><caption>Where each sector sits now under the three inputs (quadrant, weeks in it)</caption>
<thead><tr><th>Sector</th><th>Raw</th><th>4-week EMA</th><th>8-week EMA</th></tr></thead><tbody>{''.join(cells)}</tbody></table></div>"""


def dwell_table(G):
    rows = []
    for tk in ORDER:
        s = G["sectors"][tk]; q = s["quadrants"]; c = s["current"]
        cells = [f"<th scope=row><span class=tk>{tk}</span> {s['name']}</th>",
                 f"<td><span class='qpill {QCLASS[c['quadrant']]}'>{QLABEL[c['quadrant']]}</span> <span class=sub>{c['weeks_in']} wk</span></td>"]
        for qn in QORDER:
            v = q[qn]
            cells.append(f"<td class=num>{v['share']*100:.0f}%<span class=sub> · {v['median_wk']:.0f}/{v['mean_wk']:.1f}/{v['max_wk']} wk</span></td>")
        cells.append(f"<td class=num>{s['cycle_weeks']['median']:.0f}<span class=sub> / {s['cycle_weeks']['mean']:.0f} wk</span></td>")
        cells.append(f"<td class=num>{s['clockwise_share']*100:.0f}%</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"""<div class=tablewrap><table class=board>
<caption>Time in each quadrant since 2000 — share of weeks, then median / mean / longest spell in weeks</caption>
<thead><tr><th>Sector</th><th>Now</th><th>Rises</th><th>Maintains</th><th>Falls</th><th>Lags</th><th>Full cycle (median / mean)</th><th>Exits that continue clockwise</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def fwd_table(G):
    rows = []
    for tk in ORDER:
        q = G["sectors"][tk]["quadrants"]
        cells = [f"<th scope=row><span class=tk>{tk}</span></th>"]
        for qn in QORDER:
            v = q[qn]; x = v["fwd13_excess_pct"]
            cells.append(f"<td class='num {'neg' if x < 0 else ''}'>{x:+.2f}%<span class=sub> · {v['fwd13_hit']*100:.0f}%</span></td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"""<div class=tablewrap><table class=board>
<caption>What the quadrant says about the NEXT 13 weeks — mean excess return over SPY, then share of positive outcomes (descriptive, overlapping weeks)</caption>
<thead><tr><th>Sector</th><th>Rises</th><th>Maintains</th><th>Falls</th><th>Lags</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""


def main():
    R, G, GS = load()
    xlp = {v: R["XLP"][v]["summary"] for v in VARIANTS}
    n_clear = {v: sum(1 for tk in ORDER if (R[tk][v]["summary"]["wilson_lb95"] or 0) > 0.5) for v in VARIANTS}
    n_beat = {v: sum(1 for tk in ORDER if R[tk][v]["summary"]["beats_drift"]) for v in VARIANTS}
    best_vol = max(ORDER, key=lambda tk: (R[tk]["vol_all"]["summary"]["wilson_lb95"] or 0))
    bv = R[best_vol]["vol_all"]["summary"]
    lead = [tk for tk in ORDER if G["sectors"][tk]["current"]["quadrant"] == "LEADING"]
    lag = [tk for tk in ORDER if G["sectors"][tk]["current"]["quadrant"] == "LAGGING"]
    imp = [tk for tk in ORDER if G["sectors"][tk]["current"]["quadrant"] == "IMPROVING"]
    wea = [tk for tk in ORDER if G["sectors"][tk]["current"]["quadrant"] == "WEAKENING"]
    ALLG = {"raw": G, "s4": GS[4], "s8": GS[8]}
    tail_json = json.dumps({g: {tk: v["sectors"][tk]["tail"] for tk in ORDER} for g, v in ALLG.items()})
    cur_json = json.dumps({g: {tk: v["sectors"][tk]["current"] for tk in ORDER} for g, v in ALLG.items()})

    page = f"""<title>Sector Volume & Rotation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#F5F6F8;--surface:#FFFFFF;--ink:#172033;--muted:#5B6577;--rule:#D9DEE6;--accent:#24519E;
  --imp:#24519E;--lea:#4F93CF;--wea:#C9861E;--lag:#8E3B22;--tint:.10;--ok:#1F6E3A;--neg:#8E3B22;--pill:#EEF1F5;}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0F141C;--surface:#161D28;--ink:#E6EAF0;--muted:#9AA6B8;--rule:#2A3442;--accent:#5F95DC;
  --imp:#5F95DC;--lea:#2F6CC4;--wea:#BD8432;--lag:#C24E62;--tint:.16;--ok:#6CC08A;--neg:#E07A8A;--pill:#202A38;}}}}
:root[data-theme="dark"]{{--bg:#0F141C;--surface:#161D28;--ink:#E6EAF0;--muted:#9AA6B8;--rule:#2A3442;--accent:#5F95DC;
  --imp:#5F95DC;--lea:#2F6CC4;--wea:#BD8432;--lag:#C24E62;--tint:.16;--ok:#6CC08A;--neg:#E07A8A;--pill:#202A38;}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font-family:"Source Serif 4",Georgia,serif;font-size:16px;line-height:1.55;margin:0}}
main{{max-width:980px;margin:0 auto;padding:40px 24px 72px}}
h1,h2,h3{{font-family:Archivo,"Helvetica Neue",Arial,sans-serif;text-wrap:balance;line-height:1.15;margin:0}}
h1{{font-size:2.1rem;font-weight:700;letter-spacing:-.01em}}
h2{{font-size:1.35rem;font-weight:600;margin-top:56px;padding-top:18px;border-top:1px solid var(--rule)}}
h3{{font-size:1.02rem;font-weight:600;margin-top:28px}}
p{{max-width:68ch;margin:12px 0}}
.eyebrow{{font-family:Archivo,sans-serif;font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
.lede{{font-size:1.08rem;color:var(--muted);max-width:66ch}}
.strip{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:28px 0 8px}}
.strip>div{{background:var(--surface);border:1px solid var(--rule);padding:14px 16px;border-radius:6px}}
.strip .k{{font-family:Archivo,sans-serif;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.strip .v{{font-family:Archivo,sans-serif;font-size:1.25rem;font-weight:600;margin-top:4px}}
.strip .s{{font-size:.88rem;color:var(--muted);margin-top:2px}}
.tablewrap{{overflow-x:auto;margin:16px 0;background:var(--surface);border:1px solid var(--rule);border-radius:6px}}
table.board{{border-collapse:collapse;width:100%;font-size:.86rem;font-variant-numeric:tabular-nums}}
table.board caption{{text-align:left;font-family:Archivo,sans-serif;font-size:.8rem;color:var(--muted);padding:10px 12px 6px;caption-side:top}}
table.board th,table.board td{{padding:7px 10px;border-top:1px solid var(--rule);text-align:left;vertical-align:top;white-space:nowrap}}
table.board thead th{{font-family:Archivo,sans-serif;font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);border-top:none}}
table.board thead th.grp{{text-align:center;border-bottom:1px solid var(--rule)}}
table.board tbody th{{font-weight:400}}
td.num{{text-align:right;font-family:"JetBrains Mono",ui-monospace,monospace;font-size:.82rem}}
.tk{{font-family:"JetBrains Mono",monospace;font-weight:500;color:var(--accent)}}
.sub{{color:var(--muted);font-size:.76rem}}
.ok{{color:var(--ok);font-weight:500}} .neg{{color:var(--neg)}}
.call{{font-family:Archivo,sans-serif;font-size:.7rem;letter-spacing:.06em;padding:2px 7px;border-radius:3px;background:var(--pill)}}
.call.c1{{color:var(--ok)}} .call.c-1{{color:var(--neg)}} .call.c0{{color:var(--muted)}}
.qpill{{font-family:Archivo,sans-serif;font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;border-radius:3px;color:#fff}}
.q-imp{{--q:var(--imp)}} .q-lea{{--q:var(--lea)}} .q-wea{{--q:var(--wea)}} .q-lag{{--q:var(--lag)}}
.qpill{{background:var(--q)}}
figure{{margin:18px 0;background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:14px}}
figcaption{{font-size:.84rem;color:var(--muted);margin-top:8px;max-width:none}}
svg.rrg{{width:100%;height:auto;display:block;font-family:Archivo,sans-serif}}
svg.rrg .qt{{fill:var(--q);opacity:var(--tint)}}
svg.rrg .grid{{stroke:var(--rule);stroke-width:1}}
svg.rrg .axis{{stroke:var(--muted);stroke-width:1.2}}
svg.rrg .tick,svg.ribbon .tick{{font-size:10px;fill:var(--muted);font-family:"JetBrains Mono",monospace}}
svg.rrg .qlabel{{font-size:10px;letter-spacing:.08em;fill:var(--muted);font-weight:600}}
svg.rrg .axname{{font-size:11px;fill:var(--muted)}}
svg.rrg .tail{{fill:none;stroke:var(--q);stroke-width:2;stroke-linejoin:round;opacity:.85}}
svg.rrg .dot{{fill:var(--q);stroke:var(--surface);stroke-width:1}}
svg.rrg .headdot{{fill:var(--q);stroke:var(--surface);stroke-width:2}}
svg.rrg .hit{{fill:transparent;cursor:pointer}}
svg.rrg .head:focus{{outline:none}} svg.rrg .head:focus .headdot,svg.rrg .head:hover .headdot{{stroke:var(--ink)}}
svg.rrg .tklabel,svg.ribbon .tklabel{{font-size:11.5px;font-weight:600;fill:var(--ink);font-family:"JetBrains Mono",monospace}}
svg.ribbon{{width:100%;height:auto;display:block}}
svg.ribbon .cell{{fill:var(--q)}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .pair figure{{margin:0}}
@media (max-width:820px){{.pair{{grid-template-columns:1fr}}}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;font-family:Archivo,sans-serif;font-size:.78rem;color:var(--muted);margin:8px 0}}
.legend span::before{{content:"";display:inline-block;width:10px;height:10px;border-radius:2px;background:var(--q);margin-right:6px;vertical-align:-1px}}
#tip{{position:fixed;pointer-events:none;background:var(--surface);color:var(--ink);border:1px solid var(--rule);border-radius:4px;padding:8px 10px;font-size:.8rem;font-family:"JetBrains Mono",monospace;box-shadow:0 2px 10px rgba(0,0,0,.12);max-width:260px}}
.note{{border-left:3px solid var(--accent);padding:6px 14px;background:var(--surface);margin:16px 0;max-width:72ch}}
.note p{{margin:6px 0}}
ol,ul{{max-width:70ch;padding-left:22px}} li{{margin:6px 0}}
dl.method{{max-width:72ch}} dl.method dt{{font-family:Archivo,sans-serif;font-weight:600;margin-top:14px}} dl.method dd{{margin:4px 0 0 0;color:var(--ink)}}
code{{font-family:"JetBrains Mono",monospace;font-size:.84em;background:var(--pill);padding:1px 5px;border-radius:3px}}
@media (max-width:720px){{.strip{{grid-template-columns:1fr}} h1{{font-size:1.7rem}}}}
@media (prefers-reduced-motion:no-preference){{svg.rrg .head .headdot{{transition:r .15s}}}}
</style>
<main>
<div class=eyebrow>ZION sector board · research note · 13 Sep 2026</div>
<h1>Sector Volume &amp; Rotation</h1>
<p class=lede>Three things were asked and answered here: does ETF volume add predictive power to the sector cascade (tested first on Consumer Staples), how accurate is every sector on an honest sequential next-month walk-forward, and where does each sector sit in the four-quadrant rotation against the S&amp;P 500 and for how long.</p>

<div class=strip>
<div><div class=k>Volume on XLP</div><div class=v>{pct(xlp['vol_all']['wilson_lb95'])} LB95 <span class=sub>vs {pct(xlp['base_all']['wilson_lb95'])} without</span></div><div class=s>edge over drift {xlp['vol_all']['edge_vs_drift_acted']*100:+.1f} pts; volume cells fired {xlp['vol_all']['vol_leg_months']} months</div></div>
<div><div class=k>Sectors clearing LB95 &gt; 50%</div><div class=v>{n_clear['vol_all']} of 9 <span class=sub>with volume · {n_clear['base_all']} without</span></div><div class=s>{n_beat['vol_all']} of 9 beat the up-rate of their own acted months</div></div>
<div><div class=k>Rotation now</div><div class=v>{len(lead)} leading · {len(lag)} lagging</div><div class=s>maintains: {', '.join(lead) or 'none'} · lags: {', '.join(lag) or 'none'} · rises: {', '.join(imp) or 'none'} · falls: {', '.join(wea) or 'none'}</div></div>
</div>

<h2>1. Volume as a predictor, Consumer Staples first</h2>
<p>Two volume legs were declared before any result was seen and added to the cascade's variable pool: the log of the prior calendar month's total XLP volume, and the log of that month's volume relative to the mean of the twelve months before it. Both are point-in-time (fully known on the first trading day of the month), and both are registered as stationary so they are never CPI-deflated. The cascade then treats them like any other leg: it can pair volume with a macro variable, or two volume legs with each other, and a volume cell has to win the in-fold validation ranking to be accepted.</p>
{xlp_section(R)}
<p><b>Reading.</b> On Consumer Staples, volume {"raises" if (xlp['vol_all']['wilson_lb95'] or 0) > (xlp['base_all']['wilson_lb95'] or 0) else "does not raise"} the lower bound ({pct(xlp['base_all']['wilson_lb95'])} to {pct(xlp['vol_all']['wilson_lb95'])} on all variables; {pct(xlp['base_timely']['wilson_lb95'])} to {pct(xlp['vol_timely']['wilson_lb95'])} on timely variables). Volume cells were accepted in {pct(xlp['vol_all']['share_of_fits_with_vol_round'], 0)} of the monthly refits and fired on {xlp['vol_all']['vol_leg_months']} acted months at {pct(xlp['vol_all']['vol_leg_acc'])} accuracy against a {pct(xlp['vol_all']['vol_leg_drift'])} up-rate on those same months. No variant clears the house admission bar of a 95% Wilson lower bound above 50%, and the edge over drift on acted months is {xlp['vol_all']['edge_vs_drift_acted']*100:+.1f} points. The honest verdict for XLP is that volume buys coverage, not skill.</p>

<h2>2. All nine sectors, sequential next-month out-of-sample</h2>
<p>Every month from December 2008 the panel is truncated at that month, the full recursive 27-type cascade is refit from scratch on what was known, its cells are frozen, and the month is classified with those frozen constants. The call is scored against the realised next-month sign and the fit is thrown away. Bets are one month long and non-overlapping, so a plain 95% Wilson lower bound is the honest bound. "Edge" is accuracy minus the up-rate of the months the system chose to act in, which is the drift a long-biased system captures for free.</p>
{board_table(R, ["base_all", "vol_all"], "Board convention: all panel variables (includes mid-month publishers carried forward). acted = acted months / scored months.")}
{board_table(R, ["base_timely", "vol_timely"], "Point-in-time strict: timely variables only (daily market series plus rates; industrial production and M2 dropped).")}
<p><b>Reading.</b> With volume, {n_clear['vol_all']} of 9 sectors clear a lower bound of 50% on the board convention and {n_clear['vol_timely']} of 9 on strict timely variables; without it {n_clear['base_all']} and {n_clear['base_timely']}. The best volume-inclusive sector is {best_vol} at {pct(bv['acc'])} on {bv['n_acted']} acted months (lower bound {pct(bv['wilson_lb95'])}, edge {bv['edge_vs_drift_acted']*100:+.1f} points). Compare this with the standing 6-month board, where the same sectors show 74–88% fitted accuracy: that board is a single 50/25/25 split with overlapping 6-month labels, and the sequential 1-month test is the harsher, more honest instrument. Wherever a sector shows a high accuracy and a small or negative edge, it is being long in months that went up anyway.</p>

<h2>3. Sector rotation against the market</h2>
<p>Weekly total-return closes since 2000. RS-Ratio is a sector's relative strength versus SPY expressed as standard deviations from its own trailing-year average, centred on 100; RS-Momentum is the 13-week change in that relative strength, centred on 100. The four quadrants are read clockwise: a sector <b>rises</b> (improving: behind, but gaining), then <b>maintains</b> (leading: ahead and still gaining), then <b>falls</b> (weakening: still ahead, losing ground), then <b>lags</b> (behind and losing). Tails show the last 13 weeks; hover or focus a ticker for the weekly readings.</p>
<figure>{rrg_svg(G)}
<div class=legend><span class=q-imp>Improving · rises</span><span class=q-lea>Leading · maintains</span><span class=q-wea>Weakening · falls</span><span class=q-lag>Lagging · lags</span></div>
<figcaption>Relative rotation of the nine SPDR sectors versus SPY, week ending {G['market']['asof']}. Tail colour is the sector's current quadrant; quadrant is also given by position.</figcaption></figure>
{dwell_table(G)}
<figure>{ribbon_svg(G)}<figcaption>Quadrant occupancy since 2000, one row per sector, one cell per four weeks. Long unbroken runs are the persistent states (maintains, lags); the thin slivers are the transitional ones (rises, falls).</figcaption></figure>

<h3>Smoothed momentum</h3>
<p>The raw tails above are jagged because the 13-week momentum flips sign on ordinary week-to-week noise. Below, the relative-strength series is passed through an exponential moving average before the ratio and momentum are computed, at a 4-week and an 8-week span. Everything else is unchanged. Smoothing makes the tails rotate more like the textbook picture and lengthens every spell; it also introduces lag, so the 8-week version reports a quadrant change a few weeks after the raw one.</p>
<div class=pair>
<figure>{rrg_svg(GS[4], "s4")}<figcaption>4-week EMA, week ending {GS[4]['market']['asof']}.</figcaption></figure>
<figure>{rrg_svg(GS[8], "s8")}<figcaption>8-week EMA, week ending {GS[8]['market']['asof']}.</figcaption></figure>
</div>
{smooth_compare(ALLG)}
{now_row(ALLG)}
<ul>
<li><b>Rotation becomes a rotation.</b> Clockwise exits rise from about half in the raw series to about {np.mean([GS[4]['sectors'][t]['clockwise_share'] for t in ORDER])*100:.0f}% at 4 weeks and {np.mean([GS[8]['sectors'][t]['clockwise_share'] for t in ORDER])*100:.0f}% at 8 weeks. The transitional quadrants stop being one-week slivers: rising and falling last a median of {np.median([GS[8]['sectors'][t]['quadrants']['IMPROVING']['median_wk'] for t in ORDER]):.0f} weeks at the 8-week span, and a full cycle stretches to a median of {GS[8]['market']['cycle_weeks_median']:.0f} weeks.</li>
<li><b>Forecast content stays thin.</b> Pooled over sectors, the next-quarter excess return in the two gaining quadrants versus the two losing ones separates only slightly with smoothing (table above), and the per-sector signs still disagree. Smoothing cleans the description; it does not create a signal, which is what the sector cascade and cross-sectional screen already found.</li>
<li><b>Current reads that move.</b> Health Care is improving on the raw series but already leading once smoothed; Technology reads weakening raw and at 4 weeks but still leading at 8 weeks, which is the lag showing. The persistent laggards (Consumer Disc, Utilities, Consumer Staples) read the same under all three.</li>
</ul>
<h3>How the rotation actually behaves (raw series)</h3>
<ul>
<li><b>Two persistent states, two transitional ones.</b> Sectors spend roughly a third to a half of their time either maintaining or lagging, with typical spells of 3–4 weeks and the longest running 40–68 weeks. The rising and falling quadrants are short: median 1–2 weeks, mean under 3, because a 13-week momentum burst usually reverses before the year-long ratio crosses 100.</li>
<li><b>The circle is only half a circle.</b> Only about half of quadrant exits continue clockwise (range {min(G['sectors'][t]['clockwise_share'] for t in ORDER)*100:.0f}–{max(G['sectors'][t]['clockwise_share'] for t in ORDER)*100:.0f}% by sector). A sector that starts rising is about as likely to drop straight back to lagging as to go on to lead. A full rotation, measured from one entry into the rising quadrant to the next, has a median of {G['market']['cycle_weeks_median']:.0f} weeks and a mean of {G['market']['cycle_weeks_mean']:.0f}, so the "cycle" is a skewed mix of quick false starts and a few long tours.</li>
<li><b>Quadrant is a description, not a forecast.</b> The next-13-week excess return conditional on quadrant is small and inconsistent in sign across sectors (table below), with hit rates clustering around one half. This graph tells you where a sector is, not where it is going; that is consistent with the ZION finding that absolute sector direction is drift wearing nine jerseys.</li>
</ul>
{fwd_table(G)}

<h2>4. How ZION predicts the S&amp;P 500</h2>
<p>ZION runs two different objects under one name. The <b>monthly directional board</b> makes a call on the S&amp;P's direction and abstains when it cannot; the <b>live universe book</b> holds structural positions regardless of any call. The method below is the directional one; the book is described at the end because it is what is actually traded.</p>
<dl class=method>
<dt>Data and predictor (Stage 1)</dt>
<dd>A monthly point-in-time panel (Shiller price, earnings, CPI, FRED rates and money, daily market series). The S&amp;P's anchor predictor is a valuation ratio, real price over ten-year real earnings (CAPE), the only asset in the five with a true cyclical adjustment. The change window is swept only on pre-1990 data and then frozen; changes inside a half-standard-deviation dead zone count as flat. Every predictor leg may be used once across the five assets, and mid-month publishers are carried forward or excluded from emission.</dd>
<dt>The 27-type grammar and recursive cascade (RED DAWN, Stage 3)</dt>
<dd>For a pair of variables A and B the system builds a ternary triple: the change in A, the change in B, and the change in the composite (z of A minus z of B), each classified up, flat or down against a dead zone, giving 27 types. A type's direction is the majority of the training pool; a candidate needs a training Wilson lower bound above 0.45 and is ranked by its validation-pool lower bound; the test block is never touched by selection. The winning cell's months are removed and the entire discovery is re-run on the remainder, so leftover months get their own best predictor; recursion stops when the best remaining validation lower bound is at or below 0.50. Each accepted cell is frozen with its z-constants so new months can be classified without re-fitting. For the S&amp;P the horizon was locked at three months, and five CAPE-type cells were pulled (the strongest at about 90%, 80% and 77% in walk-forward), covering about two thirds of months at roughly 77%. The tier cascade on the remaining months scores about 56% and admits nothing; the edge is entirely type-level.</dd>
<dt>Convergence (Stage 4)</dt>
<dd>Three independent engines vote on the same one-month direction: RED DAWN (the CAPE types), ODYSSEY (a binned pattern-analogue with expanding, in-fold bins) and SANCTUARY (a similarity-weighted analogue). The system acts only when at least two agree and abstains on a split. On a true sequential walk-forward the unanimous set reaches about 68% but that is only about one point above simply being long in those same months; convergence de-selects disagreement months well but adds no skill on the months it acts. The deployable Stage-4 output for the S&amp;P is therefore ABSTAIN, and the monthly board currently reads ABSTAIN for SPY as of the August 2026 row.</dd>
<dt>Gates, evidence and what is refused</dt>
<dd>Admission is a genuine one-step-ahead walk-forward with a Wilson lower bound above the gate plus the as-issued forward tape; placebo and shuffled-null tests are reported but never gate. There is no forced prediction: the pipeline ends in a gated call or an abstention. Flips are allowed only for cells whose upper bound sits below 50%; the S&amp;P has none. Accuracy is always reported next to drift, because the S&amp;P's headline 71% monthly accuracy equals the up-rate of the months it chose to be long in, which is long-drift capture rather than timing skill.</dd>
<dt>The live book (what is traded)</dt>
<dd>Weekly cadence, 50/50 with the monthly sleeve. The S&amp;P weekly sleeve is a hybrid: the type cascade first, a tier fallback on abstain weeks, and an anchor block on the remaining weeks; its own edge-over-drift gate scores it as drift capture, so the book's return comes from structure. That structure is a Sortino-weighted SPY and Nasdaq risk block (about 30/50), an always-on 20% two-year Treasury hedge, 7.5% gold ballast, a 19.3% dollar sleeve, 2.5% India, a 5% episodic silver micro-sleeve, an exogenous VIX-times-credit throttle that flattens risk in stress, persistence of positions between decisions with a stress exit, and a two-times boost for four weeks after a stress spell ends. It is executed at 2.5 times, staged towards 4, with the scale-up gated on twelve resolved tape weeks and now also on valuation (CAPE at about plus three standard deviations). As of the week ending 11 September 2026 the as-issued exposures are US equity +0.19, Nasdaq +0.29, gold +0.05, two-year Treasury +0.12, throttle fully on, netted gross 0.86 times. The spec's own words: this book is structure, not alpha; the edge is second-moment loss-limiting, not first-moment direction.</dd>
</dl>

<h2>Method notes and caveats</h2>
<ul>
<li>Sequential test window December 2008 to July 2026, {xlp['base_all']['n_oos']} scored months per sector, refit every month (first decision after 120 months of history so the in-fold 50/25/25 split has a floor of 30 training months). Cascade code is the production <code>lib_pipeline.red_dawn_cascade</code> and <code>classify_frozen</code>, untouched; volume legs are added in-process only.</li>
<li>Outcome is the panel's month-start close series (row M-01 equals the first trading day close of month M); volume features are calendar-month totals from Yahoo shifted one month so nothing in a row postdates its price.</li>
<li>The "all variables" convention matches the standing sector board and carries the same macro-lag caveat (industrial production and M2 are released mid-month); the "timely" runs remove that leak entirely.</li>
<li>Rotation parameters (52-week ratio window, 13-week momentum) were fixed before results. The EMA spans of 4 and 8 weeks were added afterwards at the operator's request and are shown next to the raw series rather than replacing it.</li>
<li>Nothing here is wired into the Friday job or the dashboard. Scripts and JSON live in <code>~/Desktop/ZION/sector_volume/</code>.</li>
</ul>
</main>
<div id=tip hidden></div>
<script>
const TAILS={tail_json};const CUR={cur_json};
const tip=document.getElementById('tip');
function show(g,tk,x,y){{const t=TAILS[g][tk],c=CUR[g][tk];const rows=t.slice(-6).map(p=>`${{p.d}}  ${{p.rsr.toFixed(1)}}  ${{p.rsm.toFixed(1)}}  ${{p.q.toLowerCase()}}`).join('\\n');
tip.innerHTML=`<b>${{tk}}</b> · ${{c.label}} for ${{c.weeks_in}} wk (since ${{c.since}})<br><span style="opacity:.7">week · ratio · momentum · quadrant</span><pre style="margin:4px 0 0;white-space:pre">${{rows}}</pre>`;
tip.hidden=false;const w=tip.offsetWidth,h=tip.offsetHeight;tip.style.left=Math.min(x+14,innerWidth-w-8)+'px';tip.style.top=Math.max(8,y-h-10)+'px';}}
document.querySelectorAll('.head').forEach(g=>{{const tk=g.dataset.tk,gid=g.dataset.g;
g.addEventListener('mousemove',e=>show(gid,tk,e.clientX,e.clientY));g.addEventListener('mouseleave',()=>tip.hidden=true);
g.addEventListener('focus',()=>{{const r=g.getBoundingClientRect();show(gid,tk,r.left,r.top);}});g.addEventListener('blur',()=>tip.hidden=true);}});
</script>
"""
    with open(OUT, "w") as fh: fh.write(page)
    print("wrote", OUT, len(page), "bytes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""build_pe_lists.py — per-sector PE / PEG lists from data/fundamentals/sp500_fundamentals.csv.
Writes data/fundamentals/lists/{SECTOR}.csv (one per GICS sector, sorted by PEG), a sector summary CSV,
and the HTML page sector_pe_peg.html. Source: Yahoo Finance quote fundamentals, as-of the pull date.
PEG shown = Yahoo 'pegRatio' (trailing PE / expected EPS growth); trailingPegRatio kept as a cross-check.
"""
import os, json, html
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "data", "fundamentals"); LD = os.path.join(FD, "lists"); os.makedirs(LD, exist_ok=True)
ETF = {"Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV", "Energy": "XLE", "Industrials": "XLI",
       "Consumer Staples": "XLP", "Consumer Discretionary": "XLY", "Materials": "XLB", "Utilities": "XLU",
       "Communication Services": "XLC", "Real Estate": "XLRE"}
ORDER = ["Information Technology", "Financials", "Health Care", "Energy", "Industrials", "Consumer Staples",
         "Consumer Discretionary", "Materials", "Utilities", "Communication Services", "Real Estate"]


def clean(df):
    for c in ("trailingPE", "forwardPE", "pegRatio", "trailingPegRatio", "earningsGrowth", "marketCap", "priceToBook", "dividendYield"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # negative or absurd PE = loss-making / distorted; keep the row, blank the multiple so medians are meaningful
    df.loc[(df.trailingPE <= 0) | (df.trailingPE > 500), "trailingPE"] = np.nan
    df.loc[(df.forwardPE <= 0) | (df.forwardPE > 500), "forwardPE"] = np.nan
    df.loc[(df.pegRatio <= 0) | (df.pegRatio > 50), "pegRatio"] = np.nan
    df["mcap_bn"] = df.marketCap / 1e9
    return df


def fmt(x, d=1):
    return "" if (x is None or (isinstance(x, float) and np.isnan(x))) else f"{x:.{d}f}"


def main():
    df = clean(pd.read_csv(os.path.join(FD, "sp500_fundamentals.csv")))
    asof = df["asof"].iloc[0]
    summ = []; sections = []
    for sec in ORDER:
        s = df[df.sector == sec].copy()
        s["pe_vs_sector"] = s.trailingPE / s.trailingPE.median()
        s["peg_vs_sector"] = s.pegRatio / s.pegRatio.median()
        s = s.sort_values("pegRatio", na_position="last")
        cols = ["ticker", "name", "sub_industry", "trailingPE", "forwardPE", "pegRatio", "trailingPegRatio", "earningsGrowth",
                "mcap_bn", "priceToBook", "dividendYield", "pe_vs_sector", "peg_vs_sector"]
        s[cols].to_csv(os.path.join(LD, f"{ETF[sec]}_{sec.replace(' ', '_')}.csv"), index=False)
        # cap-weighted PE = sum(cap) / sum(cap / PE) over names with a PE
        w = s.dropna(subset=["trailingPE", "marketCap"])
        capw = w.marketCap.sum() / (w.marketCap / w.trailingPE).sum() if len(w) else np.nan
        summ.append(dict(sector=sec, etf=ETF[sec], n=len(s), n_pe=int(s.trailingPE.notna().sum()), n_peg=int(s.pegRatio.notna().sum()),
                         pe_median=s.trailingPE.median(), pe_capweighted=capw, fwd_pe_median=s.forwardPE.median(),
                         peg_median=s.pegRatio.median(), peg_q1=s.pegRatio.quantile(.25), peg_q3=s.pegRatio.quantile(.75),
                         cheapest_peg=", ".join(s.dropna(subset=["pegRatio"]).head(3).ticker), richest_peg=", ".join(s.dropna(subset=["pegRatio"]).tail(3).ticker[::-1])))
        rows = "".join(
            f"<tr><td class=tk>{r.ticker}</td><td>{html.escape(str(r['name']))}</td><td class=sub>{html.escape(str(r.sub_industry))}</td>"
            f"<td class=num>{fmt(r.trailingPE)}</td><td class=num>{fmt(r.forwardPE)}</td><td class='num {'hi' if r.pegRatio==r.pegRatio and r.pegRatio>2 else ('lo' if r.pegRatio==r.pegRatio and r.pegRatio<1 else '')}'>{fmt(r.pegRatio,2)}</td>"
            f"<td class=num>{fmt(r.trailingPegRatio,2)}</td><td class=num>{fmt(r.earningsGrowth*100 if r.earningsGrowth==r.earningsGrowth else np.nan,0)}</td>"
            f"<td class=num>{fmt(r.mcap_bn,0)}</td><td class=num>{fmt(r.pe_vs_sector,2)}</td><td class=num>{fmt(r.peg_vs_sector,2)}</td></tr>"
            for _, r in s.iterrows())
        m = summ[-1]
        sections.append(f"""<section id="{ETF[sec]}"><h2>{ETF[sec]} · {sec} <span class=count>{m['n']} shares</span></h2>
<p class=secsum>Median trailing PE <b>{fmt(m['pe_median'])}</b> (cap-weighted {fmt(m['pe_capweighted'])}), median forward PE <b>{fmt(m['fwd_pe_median'])}</b>, median PEG <b>{fmt(m['peg_median'],2)}</b> (interquartile {fmt(m['peg_q1'],2)}–{fmt(m['peg_q3'],2)}). PE available for {m['n_pe']} of {m['n']}, PEG for {m['n_peg']}. Cheapest on PEG: {m['cheapest_peg']}; richest: {m['richest_peg']}.</p>
<div class=tablewrap><table class=list><thead><tr><th>Ticker</th><th>Company</th><th>Sub-industry</th><th>PE (ttm)</th><th>PE (fwd)</th><th>PEG</th><th>PEG (ttm)</th><th>EPS growth %</th><th>Mkt cap $bn</th><th>PE / sector median</th><th>PEG / sector median</th></tr></thead>
<tbody>{rows}</tbody></table></div></section>""")
    S = pd.DataFrame(summ); S.to_csv(os.path.join(FD, "sector_summary.csv"), index=False)
    srows = "".join(f"<tr><td class=tk><a href='#{r.etf}'>{r.etf}</a></td><td>{r.sector}</td><td class=num>{r.n}</td><td class=num>{fmt(r.pe_median)}</td><td class=num>{fmt(r.pe_capweighted)}</td><td class=num>{fmt(r.fwd_pe_median)}</td><td class=num>{fmt(r.peg_median,2)}</td><td class=num>{fmt(r.peg_q1,2)}–{fmt(r.peg_q3,2)}</td><td class=sub>{r.cheapest_peg}</td><td class=sub>{r.richest_peg}</td></tr>" for _, r in S.iterrows())
    page = f"""<title>Sector PE & PEG Lists</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#F5F6F8;--surface:#FFFFFF;--ink:#172033;--muted:#5B6577;--rule:#D9DEE6;--accent:#24519E;--lo:#1F6E3A;--hi:#8E3B22;--pill:#EEF1F5}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0F141C;--surface:#161D28;--ink:#E6EAF0;--muted:#9AA6B8;--rule:#2A3442;--accent:#5F95DC;--lo:#6CC08A;--hi:#E07A8A;--pill:#202A38}}}}
:root[data-theme="dark"]{{--bg:#0F141C;--surface:#161D28;--ink:#E6EAF0;--muted:#9AA6B8;--rule:#2A3442;--accent:#5F95DC;--lo:#6CC08A;--hi:#E07A8A;--pill:#202A38}}
*{{box-sizing:border-box}} body{{background:var(--bg);color:var(--ink);font-family:"Source Serif 4",Georgia,serif;font-size:15px;line-height:1.5;margin:0}}
main{{max-width:1100px;margin:0 auto;padding:36px 24px 72px}}
h1,h2{{font-family:Archivo,sans-serif;text-wrap:balance;margin:0;line-height:1.15}} h1{{font-size:2rem;font-weight:700}}
h2{{font-size:1.2rem;font-weight:600;margin-top:44px;padding-top:16px;border-top:1px solid var(--rule)}}
.count{{font-size:.8rem;color:var(--muted);font-weight:500;margin-left:8px}}
.eyebrow{{font-family:Archivo,sans-serif;font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
p{{max-width:72ch;margin:10px 0}} .secsum{{color:var(--muted);font-size:.92rem}}
.tablewrap{{overflow-x:auto;background:var(--surface);border:1px solid var(--rule);border-radius:6px;margin:12px 0}}
table{{border-collapse:collapse;width:100%;font-size:.84rem;font-variant-numeric:tabular-nums}}
th,td{{padding:6px 9px;border-top:1px solid var(--rule);text-align:left;white-space:nowrap}}
thead th{{font-family:Archivo,sans-serif;font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);border-top:none;position:sticky;top:0;background:var(--surface)}}
td.num{{text-align:right;font-family:"JetBrains Mono",monospace;font-size:.8rem}} .tk{{font-family:"JetBrains Mono",monospace;font-weight:500;color:var(--accent)}} .sub{{color:var(--muted);font-size:.78rem}}
td.lo{{color:var(--lo);font-weight:500}} td.hi{{color:var(--hi)}} a{{color:var(--accent);text-decoration:none}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}} nav a{{font-family:Archivo,sans-serif;font-size:.78rem;padding:3px 9px;border:1px solid var(--rule);border-radius:3px;background:var(--surface)}}
</style>
<main>
<div class=eyebrow>S&amp;P 500 constituents by GICS sector · Yahoo Finance quote fundamentals as of {asof}</div>
<h1>Sector PE &amp; PEG Lists</h1>
<p>Every S&amp;P 500 share grouped into the eleven GICS sectors that the SPDR sector ETFs track, with trailing and forward price-to-earnings, PEG (trailing PE over expected earnings growth, Yahoo's figure) and each share's multiple relative to its own sector's median. Loss-making or distorted multiples (negative, or PE above 500, PEG above 50) are left blank rather than dragging the medians. Sorted within each sector by PEG, cheapest first; PEG below 1 is marked green, above 2 red.</p>
<nav>{"".join(f'<a href="#{ETF[s]}">{ETF[s]}</a>' for s in ORDER)}</nav>
<div class=tablewrap><table><thead><tr><th>ETF</th><th>Sector</th><th>Shares</th><th>Median PE</th><th>Cap-wt PE</th><th>Median fwd PE</th><th>Median PEG</th><th>PEG IQR</th><th>Cheapest PEG</th><th>Richest PEG</th></tr></thead><tbody>{srows}</tbody></table></div>
{"".join(sections)}
<p class=secsum>Files: one CSV per sector in <code>ZION/sector_volume/data/fundamentals/lists/</code>, plus <code>sector_summary.csv</code> and the raw pull <code>sp500_fundamentals.csv</code>. Quote fundamentals are a snapshot, not a point-in-time history; they are usable as today's peer-basket medians (for example the sector-relative PEG covariate in the 10 September overextension pre-registration) but not as a backtest input.</p>
</main>"""
    open(os.path.join(HERE, "sector_pe_peg.html"), "w").write(page)
    print(S[["etf", "n", "n_pe", "n_peg", "pe_median", "pe_capweighted", "fwd_pe_median", "peg_median"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()

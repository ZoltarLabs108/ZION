#!/usr/bin/env python3
"""
zion_dashboard_gen.py — generate the ZION System Dashboard (daily).

Pulls LIVE where it matters:
  - GREEKWATCH 21-day gamma picks   (~/Desktop/GREEK_WATCH/GREEKWATCH_PREDICTIONS.csv)
  - gamma / volume heatmap          (~/Desktop/GREEK_WATCH/greek_history_yahoo.db)
  - macro sector board              (~/Desktop/HYACINTH_X/AUG26_REPORT/rd_report_targets_sectors_monthly.csv)
and carries the weekly/monthly ZION book + backtest from CONFIG (updated on their own cadence).

Every panel is stamped with its own as-of date and evidentiary basis. Nothing is extrapolated.
Writes zion_system_dashboard.html next to this script. Schedule daily to keep it fresh.
"""
import os, csv, sqlite3, html, json
import numpy as np
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
GW   = os.path.expanduser("~/Desktop/GREEK_WATCH")
PRED = os.path.join(GW, "GREEKWATCH_PREDICTIONS.csv")
DB   = os.path.join(GW, "greek_history_yahoo.db")
SECT = os.path.expanduser("~/Desktop/HYACINTH_X/AUG26_REPORT/rd_report_targets_sectors_monthly.csv")
PANEL = os.path.expanduser("~/Desktop/ZION_WEEKLY_WT/weekly/weekly_panel_spy.csv")  # throttle inputs (VIX, credit)
TICKET = os.path.expanduser("~/Desktop/ZION/weekly/unified/reports/ZION_DESK_TICKET.json")  # the live desk ticket
SECTOR_GAUNTLET = os.path.expanduser("~/Desktop/ZION/reports/sector_gauntlet.json")  # OOS monthly full-recipe per sector
SECTOR_WEEKLY = os.path.expanduser("~/Desktop/ZION/reports/sector_weekly_gauntlet.json")  # weekly gauntlet per sector
SECTOR_INSAMPLE = os.path.expanduser("~/Desktop/ZION/reports/sector_insample.json")  # in-sample acc up to first-stage close
SECTOR_H6 = os.path.expanduser("~/Desktop/ZION/reports/board_h6.json")  # 6mo horizon board: overlap-corrected LB vs drift, conviction
SECTOR_HEDGE = os.path.expanduser("~/Desktop/ZION/reports/hedge_sortino.json")  # per-sector hedge/Sortino recommendation
METALS_H6 = os.path.expanduser("~/Desktop/ZION/reports/metals_h6.json")        # precious-metals board (same rating system)
INDICES_H6 = os.path.expanduser("~/Desktop/ZION/reports/indices_h6.json")      # S&P / QQQ / Dow board
INDEX_CALL = os.path.expanduser("~/Desktop/ZION/reports/index_call.json")      # S&P current call -> conditional hedge rec
CASSANDRA_PRICES = os.path.expanduser("~/Desktop/ZION/reports/cassandra_prices.json")  # CASSANDRA 1mo-ahead price band per asset
try: CASS = json.load(open(CASSANDRA_PRICES))
except Exception: CASS = {}

def price_cell(c, show_gate=True):
    """First column: CASSANDRA predicted price + band. Validated assets (6-mo forecast landed in-band)
    show the 6-MONTH forecast (continuing the proven path); others show the 1-month. When gated, the price
    is still shown for reference; the 'gated' flag appears underneath UNLESS show_gate=False (indices move
    that flag into the Sell-by column instead)."""
    if not c: return '<span class="s-price"><b class="none">&mdash;</b></span>'
    # ROLLING price (US Domestic Markets): the 6-month forecast made ~5 months ago, resolving NEXT MONTH.
    rolling = bool(c.get("rolling6")) and c.get("p50_6") is not None
    use6 = rolling or (c.get("use6") and c.get("p50_6") is not None)
    p50 = c.get("p50_6") if use6 else c.get("p50")
    lo = c.get("p10_6") if use6 else c.get("p10")
    hi = c.get("p90_6") if use6 else c.get("p90")
    if p50 is None: return '<span class="s-price"><b class="none">&mdash;</b></span>'
    meth = (c.get("method6") if use6 else c.get("method")) or "analogue"
    nn = c.get("n_6") if use6 else c.get("n")
    if rolling:
        _MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        _t = (c.get("target_6") or "")
        _lbl = f'{_MON[int(_t[5:7])-1]} {_t[:4]}' if len(_t) == 7 else "next mo"
        tag = f'&asymp; {_lbl}' + (" &middot; stat" if meth == "stat" else "")
        src = (f"Rolling CASSANDRA forecast made {c.get('anchor_6','~5mo ago')} (a point-in-time vintage), "
               f"resolving {_lbl} &mdash; {nn} analogues. The prediction now ~5 months in and about to be tested.")
    else:
        tag = ("6mo &#10003;" if use6 else "1mo") + (" &middot; stat" if meth == "stat" else "")
        src = (f"Statistical random-walk band ({nn} months)" if meth == "stat"
               else f"CASSANDRA {'6-month (validated path)' if use6 else '1-month'} analogue band ({nn} analogues)")
    fmt = (lambda v: f'${v:,.0f}') if (p50 or 0) >= 1000 else (lambda v: f'${v:,.2f}')
    sub = f'{fmt(lo)}&ndash;{fmt(hi)[1:]} &middot; {tag}'
    # Divergence gate: still SHOW the price for reference, but flag it underneath (the call itself auto-ABSTAINS).
    if c.get("gated") and show_gate:
        sub += (f'<br><b class="gated" title="Divergence gate: predicted per-month move ~{c.get("div_pm")}%/mo '
                'is too wide to trust &mdash; backtest shows gaps this wide don\'t close, so the call auto-ABSTAINS. '
                'Price shown for reference only.">&#8856; gated &middot; reference only</b>')
    return (f'<span class="s-price" title="{src}">'
            f'<b>{fmt(p50)}</b><small>{sub}</small></span>')

ASSET_JS = r"""
function zaMoney(d,v){return d.spot>=1000?('$'+Math.round(v).toLocaleString()):('$'+v.toFixed(2));}
function zaShow(tk){
  var d=window.__ZA[tk]; if(!d||!d.hist_px){return;}
  var H=d.hist_px,D=d.hist_dates,n=H.length;
  var use6=((d.use6||d.rolling6)&&d.p50_6!=null),HZ=use6?6:1;
  var P10=use6?d.p10_6:d.p10,P50=use6?d.p50_6:d.p50,P90=use6?d.p90_6:d.p90,NAN=use6?d.n_6:d.n;
  var meth=(use6?d.method6:d.method)||'analogue';
  var gated=!!d.gated,hasB=(P50!=null)&&!gated;
  var vals=hasB?H.concat([P10,P50,P90,d.spot]):H.slice();
  var lo=Math.min.apply(null,vals),hi=Math.max.apply(null,vals);
  var pad=(hi-lo)*0.10||Math.abs(hi)*0.05||1; lo-=pad; hi+=pad;
  var W=620,Ht=300,ML=66,MR=(hasB?104:22),MT=14,MB=30,pw=W-ML-MR,ph=Ht-MT-MB,N=hasB?n+HZ:n;
  var xf=function(i){return ML+i/Math.max(N-1,1)*pw;},yf=function(v){return MT+(1-(v-lo)/(hi-lo))*ph;};
  var s='<svg viewBox="0 0 '+W+' '+Ht+'" style="width:100%;height:auto" font-family="var(--mono),monospace">';
  [0.15,0.5,0.85].forEach(function(t){var v=lo+(hi-lo)*t,y=yf(v);
    s+='<line x1="'+ML+'" y1="'+y+'" x2="'+(ML+pw)+'" y2="'+y+'" stroke="var(--rule)"/>';
    s+='<text x="'+(ML-6)+'" y="'+(y+3)+'" text-anchor="end" font-size="10" fill="var(--faint)">'+zaMoney(d,v)+'</text>';});
  var pts=H.map(function(v,i){return xf(i)+','+yf(v);}).join(' ');
  s+='<polyline points="'+pts+'" fill="none" stroke="var(--mystic)" stroke-width="2"/>';
  s+='<circle cx="'+xf(n-1)+'" cy="'+yf(H[n-1])+'" r="3.5" fill="var(--mystic)"/>';
  var g='';
  if(hasB){
    var xi=xf(n-1),xt=xf(N-1),ys=yf(H[n-1]),yh=yf(P90),ym=yf(P50),yl=yf(P10);
    s+='<line x1="'+xt+'" y1="'+MT+'" x2="'+xt+'" y2="'+(MT+ph)+'" stroke="var(--rule)" stroke-dasharray="3,3"/>';
    s+='<polygon points="'+xi+','+ys+' '+xt+','+yh+' '+xt+','+yl+'" fill="var(--forest-soft)" opacity="0.8"/>';
    s+='<line x1="'+xi+'" y1="'+ys+'" x2="'+xt+'" y2="'+ym+'" stroke="var(--forest)" stroke-width="2" stroke-dasharray="4,2"/>';
    [[yh,P90,'high','var(--up)'],[ym,P50,'median','var(--forest)'],[yl,P10,'low','var(--down)']].forEach(function(a){
      s+='<circle cx="'+xt+'" cy="'+a[0]+'" r="3" fill="'+a[3]+'"/>';
      s+='<text x="'+(xt+6)+'" y="'+(a[0]+3)+'" font-size="10.5" font-weight="700" fill="'+a[3]+'">'+zaMoney(d,a[1])+' '+a[2]+'</text>';});
    var posf=(P90===P10)?0.5:(d.spot-P10)/(P90-P10),pos=Math.max(0,Math.min(1,posf));
    g='<div style="font-family:var(--mono);font-size:10.5px;color:var(--faint);margin-bottom:6px">Where it sits in the expected range today</div>';
    g+='<div style="position:relative;height:24px">';
    g+='<div style="position:absolute;top:9px;left:0;right:0;height:6px;border-radius:3px;background:linear-gradient(90deg,var(--down),var(--faint),var(--up))"></div>';
    g+='<div style="position:absolute;top:2px;left:'+(pos*100)+'%;transform:translateX(-50%);width:3px;height:20px;background:var(--ink);border-radius:2px"></div></div>';
    g+='<div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;margin-top:3px">';
    g+='<span style="color:var(--down)">low '+zaMoney(d,P10)+'</span>';
    g+='<span style="color:var(--ink);font-weight:700">now '+zaMoney(d,d.spot)+' · '+Math.round(pos*100)+'% of range'+(posf<0?' (below)':(posf>1?' (above)':''))+'</span>';
    g+='<span style="color:var(--up)">high '+zaMoney(d,P90)+'</span></div>';
  }
  var xlab=hasB?[[0,D[0]],[n-1,D[n-1]],[N-1,'+'+HZ+'mo']]:[[0,D[0]],[n-1,D[n-1]]];
  xlab.forEach(function(t){s+='<text x="'+xf(t[0])+'" y="'+(Ht-MB+18)+'" text-anchor="middle" font-size="9.5" fill="var(--faint)">'+t[1]+'</text>';});
  s+='</svg>';
  document.getElementById('zam-title').textContent=d.name+' · '+tk;
  document.getElementById('zam-sub').innerHTML=hasB?((meth==='stat'?('Statistical random-walk band · '+HZ+'-month · '+NAN+' months of returns'):('CASSANDRA '+HZ+'-month analogue band · '+NAN+' analogues'+(use6?' · <b style="color:var(--forest)">validated 6-mo path</b>':'')))+' · spot '+zaMoney(d,d.spot)):(gated?('<b style="color:var(--amber)">Prediction GATED</b> · predicted move ~'+d.div_pm+'%/mo is too wide to trust — the backtest shows gaps this wide don\'t close, so no forecast is offered · spot '+zaMoney(d,d.spot)):('Price history · CASSANDRA found too few analogues for a forecast band this month · spot '+zaMoney(d,d.spot)));
  document.getElementById('zam-chart').innerHTML=s;
  document.getElementById('zam-gauge').innerHTML=g;
  zaHind(tk);
  document.getElementById('zamodal').style.display='flex';
}
function zaHind(tk){
  var el=document.getElementById('zam-hind'); if(!el)return;
  var h=window.__ZH[tk];
  if(!h||!h.hist_p||h.hp50==null){el.innerHTML='<div style="font-family:var(--mono);font-size:10.5px;color:var(--faint)">No 6-month hindcast available for this asset.</div>';return;}
  var HP=h.hist_p,AP=h.act_p,na=HP.length,full=HP.concat(AP.slice(1)),nf=full.length,ai=na-1,ti=ai+6;
  var big=h.hp50>=1000,M=function(v){return big?('$'+Math.round(v).toLocaleString()):('$'+v.toFixed(2));};
  var vv=full.filter(function(v){return v!=null;}).concat([h.hp10,h.hp50,h.hp90]);
  var lo=Math.min.apply(null,vv),hi=Math.max.apply(null,vv),pad=(hi-lo)*0.08||1;lo-=pad;hi+=pad;
  var W=620,Ht=210,ML=64,MR=20,MT=12,MB=24,pw=W-ML-MR,ph=Ht-MT-MB;
  var xf=function(i){return ML+i/(nf-1)*pw;},yf=function(v){return MT+(1-(v-lo)/(hi-lo))*ph;};
  var s='<svg viewBox="0 0 '+W+' '+Ht+'" style="width:100%;height:auto" font-family="var(--mono),monospace">';
  [0.2,0.8].forEach(function(t){var v=lo+(hi-lo)*t,y=yf(v);s+='<line x1="'+ML+'" y1="'+y+'" x2="'+(ML+pw)+'" y2="'+y+'" stroke="var(--rule)"/><text x="'+(ML-6)+'" y="'+(y+3)+'" text-anchor="end" font-size="9.5" fill="var(--faint)">'+M(v)+'</text>';});
  var spot=HP[na-1],xa=xf(ai),xt=xf(ti);
  s+='<polygon points="'+xa+','+yf(spot)+' '+xt+','+yf(h.hp90)+' '+xt+','+yf(h.hp10)+'" fill="var(--forest-soft)" opacity="0.8"/>';
  s+='<line x1="'+xa+'" y1="'+yf(spot)+'" x2="'+xt+'" y2="'+yf(h.hp50)+'" stroke="var(--forest)" stroke-width="1.6" stroke-dasharray="4,2"/>';
  var hp=HP.map(function(v,i){return xf(i)+','+yf(v);}).join(' ');
  s+='<polyline points="'+hp+'" fill="none" stroke="var(--faint)" stroke-width="1.6"/>';
  var apP=AP.map(function(v,i){return xf(ai+i)+','+yf(v);}).join(' ');
  s+='<polyline points="'+apP+'" fill="none" stroke="var(--mystic)" stroke-width="2.4"/>';
  if(ti<nf){s+='<circle cx="'+xf(ti)+'" cy="'+yf(AP[6])+'" r="3.5" fill="var(--mystic)"/>';}
  s+='<circle cx="'+xt+'" cy="'+yf(h.hp90)+'" r="2.5" fill="var(--up)"/><circle cx="'+xt+'" cy="'+yf(h.hp10)+'" r="2.5" fill="var(--down)"/>';
  [[0,h.hist_d[0]],[ai,h.anchor],[Math.min(ti,nf-1),h.target]].forEach(function(t){s+='<text x="'+xf(t[0])+'" y="'+(Ht-MB+16)+'" text-anchor="middle" font-size="9" fill="var(--faint)">'+t[1]+'</text>';});
  s+='</svg>';
  var verdict=h.within?'landed INSIDE the band ✓ (+1★)':(h.dir_ok?'right direction, outside band (+½★)':'missed (0★)');
  el.innerHTML='<div style="font-family:var(--mono);font-size:10.5px;color:var(--faint);margin:2px 0 4px">How the 6-month forecast from '+h.anchor+' did &mdash; forecast '+M(h.hp50)+' (band '+M(h.hp10)+'&ndash;'+M(h.hp90)+'), actual '+M(h.actual_target)+' &middot; <b style="color:var(--ink)">'+verdict+'</b></div>'+s;
}
document.querySelectorAll('[data-tk]').forEach(function(r){
  var tk=r.getAttribute('data-tk');
  if(window.__ZA[tk]&&window.__ZA[tk].hist_px){r.style.cursor='pointer';r.title='Click for the forecast range chart';
    r.addEventListener('click',function(){zaShow(tk);});}
});
// momentum marker: click the triangle/dot to unfold its explanation; click again to collapse.
document.querySelectorAll('.mombadge').forEach(function(b){
  function toggle(e){e.stopPropagation();e.preventDefault();
    var p=document.getElementById('mi-'+b.getAttribute('data-mi'));if(p)p.classList.toggle('open');}
  b.addEventListener('click',toggle);
  b.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' ')toggle(e);});
});
(function(){var m=document.getElementById('zamodal');if(!m)return;
  function hide(){m.style.display='none';}
  m.addEventListener('click',function(e){if(e.target===m)hide();});
  var c=document.getElementById('zam-close');if(c)c.addEventListener('click',hide);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')hide();});
})();
"""

try: HB = json.load(open(os.path.expanduser("~/Desktop/ZION/reports/hindcast_bonus.json")))
except Exception: HB = {}
# validated 6-month forecast (actual landed inside its band 5 months in) -> continue the 6-mo path
# DIVERGENCE GATE (operator 2026-08-27): a wide gap between prediction and spot does NOT presage a
# catch-up move (S&P backtest: month-6 moves toward target ~48% = coin flip, ~0% of the gap closes).
# So a wide per-month predicted move lowers conviction and, past a hard threshold, is NOT offered at all.
for _tk, _c in CASS.items():
    _c["use6"] = bool(HB.get(_tk, {}).get("within")) and _c.get("p50_6") is not None
    _u6 = _c["use6"]; _p50 = _c.get("p50_6") if _u6 else _c.get("p50"); _sp = _c.get("spot"); _hz = 6 if _u6 else 1
    if _p50 is not None and _sp:
        _dpm = abs(_p50 - _sp) / _sp * 100.0 / _hz          # predicted move, % per month
        _c["div_pm"] = round(_dpm, 2)
        _c["gated"] = _dpm > 4.0                             # divergence gate: price shown for reference only
    else:
        _c["gated"] = False

# OOS-validated conviction-star bands (star_validate_oos.py, 2026-09-01). The old additive composite
# (edge/independence/hindcast/confirmation/divergence) was REFUTED empirically: bucketing 212 walk-forward
# out-of-sample decisions, the backtest-Sortino candidate INVERTED (top-vs-bottom -1.22%/6mo), while the
# cascade's convergence value (valb) RANKED results OOS -- top quintile +7.6%/6mo, and the top band
# (valb>=0.875) earned +9.96%/6mo at 77.8% hit / OOS Sortino 4.86. So the star IS the conviction.
VALB_STAR_EDGES = [0.589, 0.715, 0.788, 0.875]     # 1|2, 2|3, 3|4, 4|5 thresholds on valb

def star_rating(valb):
    """OOS-VALIDATED conviction star (2026-09-01). The star = the cascade's convergence value (valb) at the
    current frozen row, mapped to results-calibrated bands. 5 stars = valb >= 0.875 (~13-15% of picks) --
    the only tier that decisively tops realized results out-of-sample. valb of 0 / no cell fired -> 0 stars
    -> ABSTAIN gate. Market-independence is no longer summed into the star (it's shown as a separate badge);
    hindcast/divergence are dropped from the star -- the empirical test showed conviction ranks results, they
    did not."""
    if valb is None or valb <= 0: return 0.0
    e = VALB_STAR_EDGES
    return 5.0 if valb >= e[3] else 4.0 if valb >= e[2] else 3.0 if valb >= e[1] else 2.0 if valb >= e[0] else 1.0

def zero_star_gate(stars):
    """0 stars = no conviction at all -> automatic ABSTAIN (operator 2026-08-27), whatever the signals say."""
    return stars is not None and stars <= 0

def dec_badge(beta):
    """'Decorrelated' badge for low-|beta| assets (operator 2026-09-01). Independence is a PORTFOLIO virtue
    (diversification), NOT directional conviction, so it lives OUTSIDE the star as its own badge."""
    if beta is None or abs(beta) > 0.35: return ''
    return (f' <span class="dec-badge" title="Decorrelated &mdash; &beta; {beta}: moves largely independent of '
            f'the market. A portfolio diversifier, shown as a badge (not folded into the conviction star).">'
            f'&#9672; decorrelated</span>')

def momentum_state(tk):
    """Is the current price above its 6-month-ago forecast band (running) or below it (lagging)?
    Backtest: above-band = mild momentum (keeps rising, 64% vs 61% base), NOT mean-reversion; a broken
    forecast it is not. Below-band = the weakest forward. None when inside the band or no hindcast."""
    v = HB.get(tk)
    if not v or "hp90" not in v or not v.get("act_p"): return None
    cur = v["act_p"][-1]
    if cur > v["hp90"]: return "running"
    if cur < v["hp10"]: return "lagging"
    return None

def _mom_parts(tk):
    """Momentum state -> (glyph, css-class, explanation). Green triangle = running (price above its
    6-month band); yellow dot = not running (lagging, inside the band, or no validated forecast yet)."""
    ms = momentum_state(tk)
    if ms == "running":
        return ("&#9650;", "run",
                "Running &mdash; the current price is <b>above</b> its 6-month forecast band. Backtest: names above "
                "the band at month 5 keep rising (64% up vs 61% base), so this is momentum, not a broken forecast.")
    if ms == "lagging":
        return ("&#9679;", "flat",
                "Not running &mdash; the current price is <b>below</b> its 6-month forecast band, the weakest-forward "
                "cohort historically.")
    _v = HB.get(tk) or {}
    if "hp90" in _v and _v.get("act_p"):
        return ("&#9679;", "flat", "Not running &mdash; tracking <b>inside</b> its 6-month forecast band, on the predicted path.")
    return ("&#9679;", "flat", "Not running &mdash; no validated 6-month forecast yet to compare against the current price.")

def _mom_badge(tk):
    """Just the clickable marker, embedded in the detail column. Clicking it toggles #mi-<tk>."""
    glyph, cls, _ = _mom_parts(tk)
    return (f' &middot; <span class="mombadge {cls}" data-mi="{tk}" role="button" tabindex="0" '
            f'title="Click to expand">{glyph}</span>')

def _mom_info(tk):
    """The unfolding explanation panel, emitted as a direct child of the .srow so it spans full width."""
    _, _, info = _mom_parts(tk)
    return f'<span class="mominfo" id="mi-{tk}">{info}</span>'

def load_board(path):
    """Load a metals/indices board json and attach the shared star rating."""
    try: rows = [d for d in json.load(open(path)) if "err" not in d]
    except Exception: return []
    for d in rows:
        c = CASS.get(d["tk"]); d["cass"] = c
        d["stars"] = star_rating(d.get("cur_valb"))              # OOS-validated conviction star
        # divergence gate DECOUPLED from the call (operator 2026-09-01): it only withholds the PRICE
        # (price_cell shows "reference only"); it no longer vetoes the validated directional call, since the
        # valb star was proven to rank results WITHOUT the divergence gate applied.
    rows.sort(key=lambda x: -(x.get("stars") or 0))
    return rows

def render_board(rows):
    """Render a metals/indices board row (same 5-col srow grid as sectors, no hedge column)."""
    import html as _h
    # boards may store the call as BUY/SELL (raw classifier) OR already as LONG/SHORT (indices) — accept both
    callmap = {"BUY": "LONG", "SELL": "SHORT", "LONG": "LONG", "SHORT": "SHORT"}; callcls = {"LONG": "long", "SHORT": "sell"}
    out = ""
    for x in rows:
        st = x.get("stars", 0.0); pct = round(st / 5.0 * 100)
        lb = x.get("no_lb"); dr = x.get("drift"); marg = x.get("margin"); bta = x.get("beta")
        lbtxt = f'{lb}%' if lb is not None else '&mdash;'
        raw = x.get("call", "ABSTAIN")
        call = callmap.get(raw, "ABSTAIN")
        zgate = zero_star_gate(st)
        if zgate: call = "ABSTAIN"                               # 0-star gate: no conviction -> ABSTAIN
        ccls = callcls.get(call, "abst")
        vb = x.get("cur_valb"); calltag = f'{call}<small> {vb}</small>' if (call in ("LONG", "SHORT") and vb) else call
        asof = x.get("asof", "")
        gate = (f'LB {lb}% vs drift {dr}% <b style="color:var(--forest)">(+{marg})</b>' if (marg is not None and marg > 0)
                else (f'LB {lb}% vs drift {dr}% ({marg})' if marg is not None else '&mdash;'))
        zg = ' &middot; <span style="color:var(--amber)">&#8856; 0-star gate</span>' if zgate else ''
        det = f'{gate} &middot; &beta; {bta if bta is not None else "&mdash;"}{zg}' + (
            f' &middot; <span style="color:var(--faint)">as of {asof}</span>' if asof else '') + _mom_badge(x["tk"])
        out += (f'<div class="srow" data-tk="{x["tk"]}"><span class="s-nm">{_h.escape(x["name"])}<span class="tk">{x["tk"]}</span>{dec_badge(x.get("beta"))}</span>'
                f'{price_cell(x.get("cass"))}'
                f'<span class="stars" title="{st}/5"><span class="bg">&#9733;&#9733;&#9733;&#9733;&#9733;</span>'
                f'<span class="fg" style="width:{pct}%">&#9733;&#9733;&#9733;&#9733;&#9733;</span></span>'
                f'<span class="s-call {ccls}">{calltag}</span>'
                f'<span class="s-best">{det}</span>{_mom_info(x["tk"])}</div>')
    return out

try: IDX_OVERLAY = json.load(open(os.path.expanduser("~/Desktop/ZION/reports/indices_overlay.json")))
except Exception: IDX_OVERLAY = {}

_MON3 = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def _fmt_day(s):
    if not s: return "&mdash;"
    try: y,m,d = s.split("-"); return f"{_MON3[int(m)-1]} {int(d)}"
    except Exception: return s

def render_indices(rows):
    """Indices board with the 3-timeframe overlay: the CALL combines monthly cascade + weekly book +
    5-day options signal (any BUY -> BUY), and a SELL-BY column gives the shortest active horizon."""
    import html as _h
    callcls = {"BUY": "long", "SELL": "sell", "MIXED": "watch", "ABSTAIN": "abst"}
    out = ('<div class="srow idx shdr">'
           '<span>Index</span>'
           '<span>Predicted price</span>'
           '<span>Conviction</span>'
           '<span>Call</span>'
           '<span>Sell by</span>'
           '<span style="text-align:center">Detail</span></div>')
    for x in rows:
        tk = x["tk"]; ov = IDX_OVERLAY.get(tk, {})
        st = star_rating(x.get("cur_valb"))              # OOS-validated conviction star (monthly cascade valb)
        pct = round(st / 5.0 * 100)
        call = ov.get("call", "ABSTAIN")
        zgate = zero_star_gate(st)
        if zgate: call = "ABSTAIN"                       # 0-star gate: no conviction -> ABSTAIN
        ccls = callcls.get(call, "abst")
        cassx = x.get("cass"); is_gated = bool(cassx and cassx.get("gated"))
        sb = ov.get("sell_by"); driver = ov.get("driver") or ""; hold = ov.get("hold") or ""
        if is_gated:
            sell_cell = (f'<span class="s-sell"><b class="gated" title="Divergence gate: predicted per-month move '
                         f'~{cassx.get("div_pm")}%/mo is too wide to trust &mdash; the price above is reference only and '
                         f'the call auto-ABSTAINS.">&#8856; gated</b><small>reference only</small></span>')
        elif call in ("BUY", "SELL", "MIXED") and sb:
            sell_cell = (f'<span class="s-sell" title="Hold-until = shortest active signal horizon">'
                         f'<b>{_fmt_day(sb)}</b><small>{_h.escape(driver)}<br>{_h.escape(hold)}</small></span>')
        else:
            sell_cell = '<span class="s-sell"><b class="none">&mdash;</b></span>'
        sigs = " &middot; ".join(_h.escape(s) for s in ov.get("signals", [])) or "&mdash;"
        unval = ov.get("unvalidated_note")
        lb = x.get("no_lb"); dr = x.get("drift"); co = x.get("casc_oos"); wf = x.get("tier_wf"); bta = x.get("beta")
        acc = (f'cascOOS {co}% &middot; tierWF {wf}% &middot; LB {lb}% vs drift {dr}%'
               if co is not None else (f'LB {lb}% vs drift {dr}%' if lb is not None else '&mdash;'))
        n_conf = ov.get("n_confirm", 0)          # multi-timeframe agreement is informational (the star is valb, not a sum)
        conf_note = (f'<br><span style="color:var(--faint)">{n_conf} timeframes agree</span>' if n_conf > 1 else '')
        gate_note = ('<br><span style="color:var(--amber)">&#8856; 0-star gate &mdash; no conviction, ABSTAIN</span>'
                     if zgate else '')
        # Everything collapses INTO the marker icon (operator 2026-08-27): the row shows only the green
        # triangle / orange circle; clicking it unfolds signals + confirmation + gate + accuracy + momentum.
        glyph, mcls, minfo = _mom_parts(tk)
        marker = (f'<span class="mombadge {mcls}" data-mi="{tk}" role="button" tabindex="0" '
                  f'title="Click for signals, call detail &amp; accuracy">{glyph}</span>')
        panel = (f'<span class="mominfo" id="mi-{tk}">'
                 f'<b style="color:var(--ink-soft)">{sigs}</b>'
                 + (f'<br><span style="color:var(--amber)">+ {_h.escape(unval)}</span>' if unval else '')
                 + conf_note + gate_note
                 + f'<br>{acc} &middot; &beta; {bta if bta is not None else "&mdash;"}'
                 + f'<br><span style="color:var(--faint)">{minfo}</span></span>')
        nm_sep = ' / ' if tk == "QQQ" else ''          # operator: slash between Nasdaq-100 and its QQQ ticker
        out += (f'<div class="srow idx" data-tk="{tk}"><span class="s-nm">{_h.escape(x["name"])}{nm_sep}<span class="tk">{tk}</span>{dec_badge(x.get("beta"))}</span>'
                f'{price_cell(x.get("cass"), show_gate=False)}'
                f'<span class="stars" title="{st}/5"><span class="bg">&#9733;&#9733;&#9733;&#9733;&#9733;</span>'
                f'<span class="fg" style="width:{pct}%">&#9733;&#9733;&#9733;&#9733;&#9733;</span></span>'
                f'<span class="s-call {ccls}">{call}</span>'
                f'{sell_cell}'
                f'<span class="s-best" style="text-align:center">{marker}</span>{panel}</div>')
    return out
OUT  = os.path.join(HERE, "zion_system_dashboard.html")

# ------- carried book / backtest (weekly + monthly cadence) -------
CFG = {
    "portfolio_asof": "2026-08-14",
    "account": 100000,
    "positions": [  # (label, ticker, exposure, role)
        ("S&P 500", "SPY", 0.185, "core"), ("Nasdaq 100", "QQQ", 0.291, "core"),
        ("Gold overlay", "GLD", 0.045, "hedge"), ("2Y Treasury", "SHY", 0.119, "hedge"),
        ("Silver", "SLV", 0.0, "flat"), ("WTI", "USO", 0.0, "flat"),
    ],
    "prices_config": {"SHY": 82.02},  # tickers not in the options feed (SHY as of 2026-08-20)
    "gross": 0.86, "throttle": 1.00, "leverage": 4.0, "cap": 2.0, "monthly_leg": "Cash",
    "board_asof": "2026-08-01",
    # nav targets (edit to repoint)
    "recent_picks_url": "#picks",   # jumps to the stock-picks panel on this page
    "backtest_url": "https://claude.ai/code/artifact/dfd3d043-49c5-4bec-8f1d-8773171efc9f",  # ZION backtest / structural evidence
    "backtest": {"sortino": 5.20, "spy_sortino": 0.91, "maxdd": "-16%", "spy_maxdd": "-52%",
                 "y2008": "+13%", "y2022": "+36%"},
    "metals": [  # (name, cell, cert_acc, oos_note, stance)
        ("Gold", "Dollar Index / M2 money", "71.8%", "beats drift OOS", "Abstain (T13)"),
        ("Silver", "Industrial prod. / 10-yr yield", "70.5%", "beats drift OOS", "Abstain (T4)"),
        ("Platinum", "precious-correlated", "—", "redundant", "Watch-only"),
    ],
}

def read_csv(p):
    if not os.path.exists(p): return []
    with open(p) as f: return list(csv.DictReader(f))

def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def vol_fmt(v):
    if v is None: return "—"
    v = float(v)
    for u, d in (("M", 1e6), ("K", 1e3)):
        if v >= d: return f"{v/d:.1f}{u}"
    return f"{int(v)}"

def read_ticket():
    if not os.path.exists(TICKET): return None
    try: return json.load(open(TICKET))
    except Exception: return None

def live_prices(tickers):
    """Latest spot from the options feed; fall back to prices_config."""
    px = {}
    if os.path.exists(DB):
        c = sqlite3.connect(DB); cur = c.cursor()
        for t in tickers:
            r = cur.execute("select spot from gex_levels_history where symbol=? order by ts desc limit 1", (t,)).fetchone()
            if r and r[0]: px[t] = float(r[0])
        c.close()
    for t, p in CFG.get("prices_config", {}).items():
        px.setdefault(t, p)
    return px

def odyssey_flames(sym, conf):
    """ODYSSEY waveform confirmation from the last 5 intraday descriptors. If the 5-day waveform is
    momentum-up (positive cumulative return with real participation), the pick is ALSO a momentum play:
    &#128293; one flame; &#128293;&#128293; a second flame when CASSANDRA confidence is HIGH. Dormant for
    names the intraday logger doesn't track (currently a crypto/momentum watchlist, not the pick universe)."""
    if not os.path.exists(DB): return ""
    try:
        cn = sqlite3.connect(DB)
        rows = cn.execute("select ret, rvol from intraday_descriptors where symbol=? order by date desc limit 5", (sym,)).fetchall()
        cn.close()
    except Exception: return ""
    rets = [r[0] for r in rows if r[0] is not None]; rvols = [r[1] for r in rows if r[1] is not None]
    if len(rets) < 3: return ""
    momentum_up = sum(rets) > 0 and (sum(rvols) / len(rvols) if rvols else 0) >= 1.0
    if not momentum_up: return ""
    return "&#128293;&#128293;" if conf == "HIGH" else "&#128293;"

# ---------------- GREEKWATCH 21-day picks ----------------
def greek_picks():
    rows = read_csv(PRED)
    if not rows: return "", []
    asof = max(r["as_of"] for r in rows)
    picks = []
    for r in rows:
        if r["as_of"] != asof: continue
        d = (r.get("pred21_dir") or "").strip().upper()
        if d not in ("UP", "DOWN"): continue
        if (r.get("pred21_validated_wf") or "").strip() != "True": continue
        if (fnum(r.get("pred21_bayes")) or 0) < 0.65: continue     # Bayes must be >= 65% (operator 2026-08-27)
        if (fnum(r.get("pred21_board_oos")) or 0) < 0.60: continue  # board OOS must be >= 60% (operator 2026-08-27)
        # NOTE: the CASSANDRA-sign convergence filter is SHADOW-ONLY (operator 2026-08-27) — a backtest
        # (42 stocks, ~11k stock-months) found CASSANDRA's sign has no forward value, so it does NOT drop
        # live picks; the pos-vs-neg (and HIGH-vs-MEDIUM) comparison runs on the forward tape instead.
        _entry = (r.get("entry_date") or "").strip()
        try: _resolve = str(np.busday_offset(np.datetime64(_entry, 'D'), 21, roll='forward')) if _entry else ""
        except Exception: _resolve = ""
        picks.append({
            "sym": r["symbol"], "dir": r["pred21_dir"].upper(),
            "bayes": fnum(r.get("pred21_bayes")), "oos": fnum(r.get("pred21_board_oos")),
            "cass": fnum(r.get("pred21_cassandra_ret")), "conf": (r.get("pred21_cassandra_conf") or "").strip(),
            "entry": _entry, "resolve": _resolve,
        })
    picks.sort(key=lambda p: (p["bayes"] or 0), reverse=True)
    return asof, picks

# ---------------- gamma / volume heatmap ----------------
def gamma_grid(symbols):
    if not os.path.exists(DB): return "", []
    c = sqlite3.connect(DB); cur = c.cursor()
    asof = cur.execute("select max(ts) from gex_levels_history").fetchone()[0]
    tiles = []
    for s in symbols:
        r = cur.execute("""select ts,spot,total_gex,gamma_flip,call_wall,put_wall,regime,pcr_vol
                           from gex_levels_history where symbol=? order by ts desc limit 1""", (s,)).fetchone()
        if not r: continue
        ts, spot, tg, flip, cw, pw, reg, pcr = r
        v = cur.execute("""select sum(volume) from chain_history where symbol=? and
                           ts=(select max(ts) from chain_history where symbol=?)""", (s, s)).fetchone()
        tiles.append({"sym": s, "spot": spot, "flip": flip, "cw": cw, "pw": pw, "tg": tg,
                      "reg": (reg or "").strip(), "pcr": pcr, "vol": v[0] if v else None,
                      "above": (spot is not None and flip is not None and spot >= flip)})
    c.close()
    # only COILED (negative-gamma) names — positive/pinned names are flat and not shown (operator 2026-08-27)
    tiles = [t for t in tiles if t["reg"] == "negative"]
    # expected-intensity 1-3 from the size of the negative-gamma imbalance (bigger imbalance = bigger move)
    mags = [abs(t["tg"]) for t in tiles if t.get("tg") is not None]
    mx = max(mags) if mags else 0
    for t in tiles:
        m = abs(t["tg"]) if t.get("tg") is not None else 0
        t["intensity"] = 3 if (mx and m >= 0.66 * mx) else (2 if (mx and m >= 0.33 * mx) else 1)
    return (asof or "")[:16], tiles

# ---------------- GREEKWATCH options desk (desk calls + squeeze + corner) ----------------
def greek_desk_panel():
    """Reads GREEK_WATCH/greek_desk.json (written daily by greek_desk_export.py) —
    the desk-call track record + cheap-vol squeeze watch + Options Corner.
    Returns a full <section> HTML block, or '' if the file is absent."""
    p = os.path.join(GW, "greek_desk.json")
    if not os.path.exists(p):
        return ""
    try:
        d = json.load(open(p))
    except Exception:
        return ""
    gen = (d.get("generated") or "")[:16]
    rows = ""
    for t in d.get("trades", []):
        st = t.get("status", "")
        col = "#16c784" if st == "CLOSED_WIN" else ("#ea3943" if st == "CLOSED_LOSS" else "#f0b90b")
        res = t.get("result_pct")
        res_s = "&mdash;" if res is None else (("+" if res >= 0 else "") + str(res) + "%")
        res_col = "#16c784" if (res is not None and res >= 0) else ("#ea3943" if res is not None else "#888")
        ended = html.escape(str(t.get("ended") or t.get("expected_exit") or "—"))
        exp = (" &middot; exp " + html.escape(str(t.get("expiry")))) if t.get("expiry") else ""
        label = "OPEN" if st == "OPEN" else st.replace("_", " ")
        rows += ("<tr>"
                 f"<td style='padding:7px 8px;font-weight:700'>{html.escape(str(t.get('symbol','')))}</td>"
                 f"<td style='padding:7px 8px;color:#555'>{html.escape(str(t.get('instrument','')))}</td>"
                 f"<td style='padding:7px 8px;color:#555'>{html.escape(str(t.get('prediction_date','')))}</td>"
                 f"<td style='padding:7px 8px;color:#555'>{ended}{exp}</td>"
                 f"<td style='padding:7px 8px;font-weight:700;color:{col}'>{label}</td>"
                 f"<td style='padding:7px 8px;text-align:right;font-weight:700;color:{res_col}'>{res_s}</td>"
                 "</tr>")
    calls = ("<table style='width:100%;border-collapse:collapse;font-size:12.5px'>"
             "<thead><tr style='text-align:left;color:#999;border-bottom:1px solid #ddd'>"
             "<th style='padding:6px 8px'>Symbol</th><th style='padding:6px 8px'>Instrument</th>"
             "<th style='padding:6px 8px'>Predicted</th><th style='padding:6px 8px'>Ended / expected exit</th>"
             "<th style='padding:6px 8px'>Status</th><th style='padding:6px 8px;text-align:right'>Result</th>"
             f"</tr></thead><tbody>{rows}</tbody></table>") if rows else "<p class='note'>No desk calls recorded.</p>"
    sq = ""
    for s in d.get("squeeze", []):
        cheap = s.get("vol") == "CHEAP"
        bc = "#16c784" if cheap else "#ccc"
        vc = "#16c784" if cheap else "#999"
        sq += (f"<span style='display:inline-block;border:1px solid {bc};border-radius:6px;"
               f"padding:4px 9px;margin:3px 4px 3px 0;font-size:12px'>"
               f"<b>{html.escape(str(s.get('symbol','')))}</b> {int(s.get('score') or 0)} "
               f"<span style='color:{vc}'>{html.escape(str(s.get('vol','')))}</span></span>")
    oc = d.get("options_corner", {})
    bB = ", ".join(html.escape(str(b.get("symbol", ""))) for b in oc.get("bucketB_condor", [])) or "none today"
    bA = ", ".join(f"{html.escape(str(a.get('symbol','')))} ({a.get('put_wall')}&ndash;{a.get('call_wall')})"
                   for a in oc.get("bucketA_strangle", [])) or "none today"
    # gamma heat map block (jumped to by the orange corner link)
    hm = d.get("heatmap", {})
    hm_pos = " ".join(
        f"<span style='display:inline-block;padding:3px 8px;margin:2px;border-radius:5px;"
        f"background:#16c78418;color:#0f7a4f;font-size:12px'><b>{html.escape(str(x.get('symbol','')))}</b> "
        f"+{x.get('gex_m')}</span>" for x in hm.get("positive", []))
    hm_neg = " ".join(
        f"<span style='display:inline-block;padding:3px 8px;margin:2px;border-radius:5px;"
        f"background:#ea394318;color:#c0392b;font-size:12px'><b>{html.escape(str(x.get('symbol','')))}</b> "
        f"{x.get('gex_m')}</span>" for x in hm.get("negative", []))
    heat_block = (
        "<div id='gw-heatmap' style='margin-top:18px;scroll-margin-top:16px;padding-top:12px;border-top:1px solid var(--rule,#eee)'>"
        "<b style='font-size:13px'>Gamma heat map (net dealer GEX, $M)</b>"
        f"<div style='margin-top:6px'><span style='font-size:11px;color:#888'>&#9650; most positive (pinned): </span>{hm_pos}</div>"
        f"<div style='margin-top:4px'><span style='font-size:11px;color:#888'>&#9660; most negative (breakout-prone): </span>{hm_neg}</div></div>"
    ) if (hm_pos or hm_neg) else ""
    return (
        "<section class='card wide' style='margin-top:14px;position:relative'>"
        f"<div class='ch'><h2>GreekWatch Options Desk</h2><span class='basis live'>Desk track record &middot; {gen}</span></div>"
        "<p class='note'>The desk's actual options calls (as-issued), with the cheap-vol gamma-squeeze "
        "watch and defined-risk Options Corner. Heuristic, not a validated signal &mdash; sell into pops, "
        "never hold to expiry.</p>"
        f"<div style='overflow-x:auto'>{calls}</div>"
        f"<div style='margin-top:16px'><b style='font-size:13px'>Gamma squeeze watch (cheap-vol profile)</b>"
        f"<div style='margin-top:6px'>{sq or '&mdash;'}</div></div>"
        f"<div style='margin-top:14px;font-size:13px'><b>Options Corner</b> &mdash; Bucket B condor "
        f"(neg-&gamma; + high IV): {bB} &middot; Bucket A strangle (pinned): {bA}</div>"
        f"{heat_block}"
        "<a href='#gw-heatmap' style='position:absolute;bottom:12px;right:16px;color:#e8862b;"
        "font-size:12px;font-weight:700;text-decoration:none'>Gamma heat map &rarr;</a>"
        "</section>"
    )


# ---------------- structural (Minervini) picks for the Stock Picks section ----------------
def structural_picks_panel():
    """Minervini-passing multi-year-base names (KO, ABBV, ...) — the STRUCTURAL,
    LEAPS / hold-the-trend picks, shown inside Stock Picks. Reads
    GREEK_WATCH/structural_base_screen.csv; emerging + tt_pass only."""
    p = os.path.join(GW, "structural_base_screen.csv")
    if not os.path.exists(p):
        return ""
    try:
        rows = list(csv.DictReader(open(p)))
    except Exception:
        return ""
    picks = [r for r in rows if str(r.get("tt_pass")) == "True" and str(r.get("emerging")) == "True"]
    if not picks:
        return ""
    picks.sort(key=lambda r: -float(r.get("base_yrs") or 0))
    cards = ""
    for r in picks:
        rs = r.get("tt_rs") or ""
        cards += (
            "<div style='border:1px solid var(--line,#e2e2e2);border-radius:10px;padding:11px 13px;"
            "min-width:150px;flex:1'>"
            f"<div style='font-weight:700;font-size:15px'>{html.escape(str(r.get('symbol','')))} "
            "<span style='color:var(--forest,#1a7f5a);font-size:10.5px;font-weight:700'>&uarr; LEAPS</span></div>"
            f"<div style='font-size:11.5px;color:#666;margin-top:4px'>{r.get('base_yrs')}yr base &middot; "
            f"+{r.get('to_ceiling%')}% to ${r.get('ceiling')}</div>"
            f"<div style='font-size:11.5px;color:#666'>Minervini &check; RS{rs} &middot; ~{r.get('leaps_dte')}d LEAPS</div>"
            "</div>")
    return (
        "<div style='margin-top:18px'>"
        "<div class='ch' style='border:0;padding:0;margin-bottom:6px'>"
        "<h2 style='font-size:15px'>Structural picks &middot; Minervini gate</h2>"
        "<span class='basis live'>Multi-year base &middot; LEAPS / hold the trend</span></div>"
        "<p class='note' style='margin:0 0 10px'>Multi-year consolidations pressing their ceiling that pass the "
        "full Minervini Trend Template (price &gt; 50 &gt; 150 &gt; 200-day, 50 &gt; 150 &gt; 200 stacked, RS &ge; 65, "
        "within 25% of the 52-week high). Long-horizon LEAPS / share holds &mdash; hold the TREND, stop on a fail "
        "back into the base. Needs a catalyst to release.</p>"
        f"<div style='display:flex;flex-wrap:wrap;gap:10px'>{cards}</div>"
        "</div>")


# ---------------- macro sector board ----------------
def sectors():
    """OOS full-recipe gauntlet per sector (recursive cascade -> STEP-1p central-pool -> engines -> MIRROR)."""
    if not os.path.exists(SECTOR_GAUNTLET): return "", []
    try: data = json.load(open(SECTOR_GAUNTLET))
    except Exception: return "", []
    out = [d for d in data if "err" not in d]
    wk = {}; iss = {}
    try: wk = {d["tk"]: d for d in json.load(open(SECTOR_WEEKLY)) if "err" not in d}
    except Exception: pass
    try: iss = json.load(open(SECTOR_INSAMPLE))
    except Exception: pass
    h6 = {}; hedge = {}; idxc = "ABSTAIN"
    try: h6 = {d["tk"]: d for d in json.load(open(SECTOR_H6)) if "err" not in d}
    except Exception: pass
    try: hedge = {d["tk"]: d for d in json.load(open(SECTOR_HEDGE))}
    except Exception: pass
    try: idxc = json.load(open(INDEX_CALL)).get("call", "ABSTAIN")   # S&P current call -> conditional hedge
    except Exception: pass
    blk = {}                                                          # RECONCILE: pruned 1-month sector-strategy block (R8, shadow 0% capital)
    try: blk = json.load(open(os.path.expanduser("~/Desktop/ZION/sector_volume/results/sector_board.json")))
    except Exception: pass
    for d in out:
        w = wk.get(d["tk"], {}); d["wk_call"] = w.get("call", "—"); d["wk_conv"] = w.get("conv_acc"); d["wk_H"] = w.get("H")
        d["is_acc"] = (iss.get(d["tk"]) or {}).get("is_acc")
        h = h6.get(d["tk"], {}); hh = hedge.get(d["tk"], {})
        d["h6_lb"] = h.get("no_lb"); d["h6_drift"] = h.get("drift"); d["h6_clears"] = h.get("clears", "no")
        margin = (h.get("no_lb") - h.get("drift")) if (h.get("no_lb") is not None and h.get("drift") is not None) else None
        d["h6_margin"] = round(margin, 1) if margin is not None else None
        # Conviction star = the cascade's OOS-validated convergence value (valb); see star_rating. Beta is
        # kept only for the separate "decorrelated" badge (independence is no longer part of the star).
        bta = hh.get("beta"); d["beta"] = bta; d["cass"] = CASS.get(d["tk"])
        d["stars"] = star_rating(h.get("cur_valb"))         # OOS-validated conviction star (cascade valb)
        # corrected current-month call via classify_frozen: BUY / SELL / ABSTAIN / DATA-LAG (features not yet published)
        d["call_now"] = h.get("call", "ABSTAIN"); d["cur_valb"] = h.get("cur_valb"); d["asof"] = h.get("asof")
        # divergence gate DECOUPLED (operator 2026-09-01): withholds the PRICE only, not the validated call.
        # hedge is INDEX-CONDITIONAL: HOLD LONG only when the S&P is predicted LONG (the drift edge is real);
        # if the index is predicted SHORT the long is exposed, so HEDGE; otherwise no standing rec.
        d["hedge_rec"] = {"LONG": "HOLD LONG", "SHORT": "HEDGE"}.get(idxc, "—")
        d["idx_call"] = idxc; d["s_long"] = hh.get("s_long"); d["s_beta"] = hh.get("s_beta")
        d["block"] = blk.get(d["tk"])                                # reconciled 1-month pruned block for this sector
    out.sort(key=lambda x: -(x.get("stars") or 0))
    return "6-month horizon · overlap-corrected · OOS", out

# ---------------- dangers: credit/spreads + INTERSTELLAR liquidity regime ----------------
def dangers():
    rows = read_csv(PANEL)
    if not rows: return None
    def series(col): return [float(r[col]) for r in rows if r.get(col) not in (None, "", "nan")]
    specs = [("VIX", "VIX_Close", "equity volatility", "{:.2f}"),
             ("Credit BAA–10Y", "Credit_BAA10Y", "corporate credit spread", "{:.2f}%")]
    gauges = []; n_stressed = 0
    for label, col, kind, fmt in specs:
        if col not in rows[0]: continue
        s = series(col); cur = s[-1]
        pctl = sum(1 for v in s if v <= cur) / len(s) * 100.0
        state = "stress" if pctl >= 70 else ("watch" if pctl >= 60 else "calm")
        if pctl >= 70: n_stressed += 1
        gauges.append({"label": label, "kind": kind, "val": fmt.format(cur), "pctl": pctl, "state": state})
    regime = ["CALM", "CAUTION", "STRESS"][min(n_stressed, 2)]
    return {"asof": rows[-1].get("Date", ""), "gauges": gauges, "regime": regime, "throttle": 0.5 ** n_stressed}

# ======================= RENDER =======================
def arrow(d): return "&uarr;" if d == "UP" else "&darr;"

def render():
    gw_asof, picks = greek_picks()
    gcov = ["SPY", "QQQ", "GLD", "NVDA", "SPGI", "RTX"]
    g_asof, tiles = gamma_grid(gcov)
    s_asof, secs = sectors()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # portfolio table — prefer the LIVE desk ticket, else fall back to CFG snapshot
    LBL = {"US_EQ": "S&P 500", "NASDAQ": "Nasdaq 100", "GOLD": "Gold", "UST2Y": "2Y Treasury",
           "USD": "US Dollar", "INDIA": "India", "SILVER": "Silver", "WTI": "WTI"}
    HEDGE = {"GOLD", "UST2Y", "USD"}
    tkt = read_ticket()
    posrows = ""; total_notional = 0.0
    if tkt and tkt.get("legs"):
        # leverage from the ACTUAL ticket (currently 2.5x, laddering toward 4.0x) — not a hardcoded label
        acct = tkt.get("capital", CFG["account"]); p_week = tkt.get("week", ""); p_lev = tkt.get("leverage", CFG["leverage"])
        for leg in tkt["legs"]:
            b = leg.get("bucket"); e = leg.get("exposure", 0.0); notional = leg.get("notional", 0)
            price = leg.get("last"); shares = leg.get("shares"); tk = leg.get("instrument", "")
            total_notional += notional
            cls = "flat" if not shares else ("hedge" if b in HEDGE else "core")
            prs = f"${price:,.2f}" if price else "&mdash;"
            shs = f"{shares:,}" if shares is not None else "&mdash;"
            posrows += (f'<tr class="{cls}" data-tk="{tk}"><td class="lab">{html.escape(LBL.get(b, b))}'
                        f'<span class="tk">{tk}</span></td><td class="num">{e:+.3f}</td>'
                        f'<td class="num">${notional:,.0f}</td><td class="num">{prs}</td>'
                        f'<td class="num sh">{shs}</td></tr>')
        p_gross = total_notional / acct if acct else 0
        p_basis = f"Live ticket &middot; wk {p_week}"
        p_note = (f"The live desk ticket — week issued {p_week}, executed at the Tuesday open, sized for a "
                  f"${acct:,.0f} account at {p_lev:g}&times; staged leverage. Notional and whole shares per the ticket.")
        gross_str = f"{p_gross:.2f}"; lev_str = f"{p_lev:g}"
    else:
        acct = CFG["account"]; px = live_prices([tk for _, tk, _, _ in CFG["positions"]])
        for label, tk, e, role in CFG["positions"]:
            notional = e * acct; total_notional += notional
            price = px.get(tk); shares = round(notional / price) if (price and e != 0) else (0 if e == 0 else None)
            cls = "flat" if e == 0 else role
            prs = f"${price:,.2f}" if price else "&mdash;"
            shs = f"{shares:,}" if shares is not None else "&mdash;"
            posrows += (f'<tr class="{cls}" data-tk="{tk}"><td class="lab">{html.escape(label)}<span class="tk">{tk}</span></td>'
                        f'<td class="num">{e:+.3f}</td><td class="num">${notional:,.0f}</td>'
                        f'<td class="num">{prs}</td><td class="num sh">{shs}</td></tr>')
        p_basis = f"As-issued &middot; wk {CFG['portfolio_asof']}"
        p_note = ("Netted weekly exposures mapped to their ETF and sized for a $100,000 account — notional and "
                  "whole shares at the latest price.")
        gross_str = f"{CFG['gross']:.2f}"; lev_str = f"{CFG['leverage']:g}"

    # top picks cards
    _MON3 = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    def _md(dstr):
        if not dstr or len(dstr) < 10: return "&mdash;"
        return f'{_MON3[int(dstr[5:7])-1]} {int(dstr[8:10])}'
    _today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pk = ""
    for p in picks:
        cv = p["cass"]
        cass = f'{cv*100:+.1f}%' if cv is not None else "—"
        confcls = {"HIGH": "hi", "MEDIUM": "med"}.get(p["conf"], "lo")
        # CASSANDRA disagrees with the 21-day pick direction -> flag as shadow-tracked (not dropped)
        disagree = cv is not None and ((p["dir"] == "UP" and cv < 0) or (p["dir"] == "DOWN" and cv > 0))
        flag = ' <b style="color:var(--down)">&#9888; shadow</b>' if disagree else ''
        # ODYSSEY waveform momentum confirmation -> flame(s) + a momentum colorbox around the card
        flames = odyssey_flames(p["sym"], p["conf"])
        style = 'position:relative' + ('' if not flames else ';border:2px solid var(--amber);box-shadow:0 0 0 1px var(--amber-soft)')
        flame_span = f'<span style="position:absolute;right:8px;bottom:7px;font-size:14px" title="ODYSSEY waveform momentum">{flames}</span>' if flames else ''
        _closed = bool(p.get("resolve")) and p["resolve"] < _today
        _rlbl = (f'<span style="color:var(--faint)">resolved {_md(p.get("resolve"))}</span>' if _closed
                 else f'resolves <b>{_md(p.get("resolve"))}</b>')
        dates = (f'<div class="pk-dates">entered {_md(p.get("entry"))} &middot; {_rlbl}</div>'
                 if p.get("entry") else '')
        # (Second-issuance fade FALSIFIED on the 16-board holdout 2026-09-01: 2nd-issuance hit 60.9% long-side,
        #  no crater, no U-shape — the discovery was in-sample search noise. No streak flag / gate.)
        pk += (f'<div class="pick" style="{style}"><div class="pk-top"><span class="pk-sym">{p["sym"]}</span>'
               f'<span class="pk-dir up">{arrow(p["dir"])} {p["dir"]}</span></div>'
               f'<div class="pk-stats"><span>bayes <b>{(p["bayes"] or 0)*100:.0f}%</b></span>'
               f'<span>OOS <b>{(p["oos"] or 0)*100:.0f}%</b></span></div>'
               f'{dates}'
               f'<div class="pk-cass {confcls}">Cassandra {cass} &middot; {html.escape(p["conf"] or "—")}{flag}</div>{flame_span}</div>')

    # gamma tiles (null-safe)
    def f1(v, spec, dash="—"):
        try: return format(v, spec)
        except (TypeError, ValueError): return dash
    gt = ""
    for t in tiles:
        loc = "above flip" if t["above"] else ("below flip" if t.get("spot") is not None and t.get("flip") is not None else "—")
        ii = t.get("intensity", 1)
        dots = "".join("&#9679;" if i < ii else "&#9675;" for i in range(3))   # ● filled = expected intensity 1-3
        gt += (f'<div class="gtile neg">'
               f'<div class="gt-h"><span>{t["sym"]}</span>'
               f'<span class="gt-reg" title="Expected move intensity {ii}/3 (from the negative-gamma imbalance)">COILED <span style="letter-spacing:1px">{dots}</span></span></div>'
               f'<div class="gt-spot">{f1(t["spot"],".2f")} <span>{loc}</span></div>'
               f'<div class="gt-row"><span>flip {f1(t["flip"],".1f")}</span><span>PCR {f1(t["pcr"],".2f")}</span></div>'
               f'<div class="gt-row"><span>walls {f1(t["pw"],".0f")}/{f1(t["cw"],".0f")}</span>'
               f'<span class="gt-vol">vol {vol_fmt(t["vol"])}</span></div></div>')

    # sectors — 6mo board (previous layout): 5-star conviction | LB | LONG/SHORT/ABSTAIN call | gate + hedge detail
    sr = ""
    callmap = {"BUY": "LONG", "SELL": "SHORT"}          # column categories: LONG / SHORT / ABSTAIN
    callcls = {"LONG": "long", "SHORT": "sell"}
    for x in secs:
        st = x.get("stars", 0.0); pct = round(st / 5.0 * 100)
        lb = x.get("h6_lb"); dr = x.get("h6_drift"); marg = x.get("h6_margin")
        lbtxt = f'{lb}%' if lb is not None else '&mdash;'
        raw = x.get("call_now", "ABSTAIN")
        call = callmap.get(raw, "ABSTAIN")
        zgate = zero_star_gate(st)
        if zgate: call = "ABSTAIN"                               # 0-star gate: no conviction -> ABSTAIN
        ccls = callcls.get(call, "abst")
        vb = x.get("cur_valb"); calltag = f'{call}<small> {vb}</small>' if (call in ("LONG", "SHORT") and vb) else call
        hrec = x.get("hedge_rec", "—"); asof = x.get("asof", "")
        gate = (f'LB {lb}% vs drift {dr}% <b style="color:var(--forest)">(+{marg})</b>' if (marg is not None and marg > 0)
                else (f'LB {lb}% vs drift {dr}% ({marg})' if marg is not None else '&mdash;'))
        zg = ' &middot; <span style="color:var(--amber)">&#8856; 0-star gate</span>' if zgate else ''
        bk = x.get("block") or {}                                   # RECONCILED 1-month pruned block (shadow)
        bcall = str(bk.get("call", "")).split()[0] if bk.get("call") else ""
        bcls = "var(--forest)" if bcall in ("UP", "LONG_REL", "LONG") else ("var(--down)" if bcall in ("DOWN", "SHORT_REL", "SHORT") else "var(--faint)")
        badm = "ADMITTED" in str(bk.get("status", ""))
        blktag = (f' &middot; <b>1mo strat:</b> <b style="color:{bcls}">{bcall or "ABSTAIN"}</b>'
                  f' <span style="color:var(--faint)">{html.escape(str(bk.get("kind", "")))}'
                  + (f' &middot; {bk.get("shares")} sh shadow' if (badm and bk.get("shares")) else '') + '</span>') if bk else ''
        det = f'{gate} &middot; hedge <b>{hrec}</b>{zg}{blktag}' + (f' &middot; <span style="color:var(--faint)">as of {asof}</span>' if asof else '') + _mom_badge(x["tk"])
        sr += (f'<div class="srow" data-tk="{x["tk"]}"><span class="s-nm">{html.escape(x["name"])}<span class="tk">{x["tk"]}</span>{dec_badge(x.get("beta"))}</span>'
               f'{price_cell(x.get("cass"))}'
               f'<span class="stars" title="{st}/5 conviction &mdash; overlap-corrected LB vs 6mo drift">'
               f'<span class="bg">&#9733;&#9733;&#9733;&#9733;&#9733;</span>'
               f'<span class="fg" style="width:{pct}%">&#9733;&#9733;&#9733;&#9733;&#9733;</span></span>'
               f'<span class="s-call {ccls}">{calltag}</span>'
               f'<span class="s-best">{det}</span>{_mom_info(x["tk"])}</div>')

    # indices (S&P / QQQ / Dow) and precious-metals boards — same rating system
    indices_rows = load_board(INDICES_H6); metals_rows = load_board(METALS_H6)
    indices_board = render_indices(indices_rows); metals_board = render_board(metals_rows)

    # TOP PICKS — top-ranked across the ENTIRE system by conviction star (valb), any board
    allrows = ([dict(name=x["name"], tk=x["tk"], stars=x.get("stars", 0), call=x.get("call_now", "ABSTAIN"), cass=x.get("cass"), grp="Sector") for x in secs]
             + [dict(name=x["name"], tk=x["tk"], stars=x.get("stars", 0), call=x.get("call", "ABSTAIN"), cass=x.get("cass"), grp="Index") for x in indices_rows]
             + [dict(name=x["name"], tk=x["tk"], stars=x.get("stars", 0), call=x.get("call", "ABSTAIN"), cass=x.get("cass"), grp="Metal") for x in metals_rows])
    # Top Picks = highest-rated with an ACTUAL directional call (BUY/SELL); abstains excluded (operator 2026-08-27)
    allrows = [r for r in allrows if r["call"] in ("BUY", "SELL", "LONG", "SHORT")]
    allrows.sort(key=lambda r: -(r["stars"] or 0))
    top_picks = "" if allrows else '<div class="note" style="margin:0">No BUY/SELL calls on the board right now &mdash; the system is abstaining across the universe this cycle.</div>'
    for r in allrows[:6]:
        call = {"BUY": "LONG", "SELL": "SHORT"}.get(r["call"], r["call"])
        dcls = "up" if call == "LONG" else ("down" if call == "SHORT" else "")
        c = r["cass"] or {}; use6 = c.get("use6") and c.get("p50_6") is not None
        if c.get("gated"):
            pxt = '<span style="color:var(--amber);font-size:11px">&#8856; gated</span>'
        else:
            p50 = c.get("p50_6") if use6 else c.get("p50")
            pxt = (f'${p50:,.0f}' if (p50 and p50 >= 1000) else (f'${p50:,.2f}' if p50 else '&mdash;'))
        st = r["stars"]; pct = round(st / 5 * 100)
        top_picks += (f'<div class="pick" data-tk="{r["tk"]}" style="cursor:pointer;border-left-color:var(--mystic)">'
                      f'<div class="pk-top"><span class="pk-sym">{r["tk"]}</span>'
                      f'<span class="pk-dir {dcls}">{call}</span></div>'
                      f'<div style="font-size:11px;color:var(--ink-soft);margin-top:2px">{html.escape(r["name"])} &middot; {r["grp"]}</div>'
                      f'<div class="stars" style="margin-top:6px;font-size:13px"><span class="bg">&#9733;&#9733;&#9733;&#9733;&#9733;</span>'
                      f'<span class="fg" style="width:{pct}%">&#9733;&#9733;&#9733;&#9733;&#9733;</span></div>'
                      f'<div class="pk-stats" style="margin-top:6px"><b>{pxt}</b><span>{st}&#9733;</span></div></div>')
    try: idx_call_now = json.load(open(INDEX_CALL)).get("call", "ABSTAIN")
    except Exception: idx_call_now = "ABSTAIN"

    # dangers being monitored
    dg = dangers()
    danger_gauges = ""; regime_html = ""; danger_summary = ""; d_asof = "—"; d_regime = "calm"
    if dg:
        d_asof = dg["asof"]; d_regime = dg["regime"].lower()
        for g in dg["gauges"]:
            danger_gauges += (
                f'<div class="gauge {g["state"]}"><div class="gg-h"><span>{g["label"]}</span>'
                f'<span class="gg-state">{g["state"].upper()}</span></div>'
                f'<div class="gg-val">{g["val"]} <span>{g["kind"]} &middot; {g["pctl"]:.0f}th pctile</span></div>'
                f'<div class="gg-track"><span class="gg-fill" style="width:{g["pctl"]:.0f}%"></span>'
                f'<span class="gg-thresh" style="left:70%"></span></div>'
                f'<div class="gg-scale"><span>calm</span><span>70th &rarr; trip</span></div></div>')
        regime_html = (
            f'<div class="regime {d_regime}"><div class="rg-l">Liquidity regime &middot; INTERSTELLAR</div>'
            f'<div class="rg-v">{dg["regime"]}</div>'
            f'<div class="rg-x">throttle {dg["throttle"]:.2f}&times; &middot; report-only, never sizes</div></div>')
        calm = [g["label"] for g in dg["gauges"] if g["state"] == "calm"]
        hot = [g["label"] for g in dg["gauges"] if g["state"] != "calm"]
        if not hot:
            danger_summary = ("No dangers active — volatility and the credit spread are both well below their "
                              "trip levels, so the throttle holds at full and the book carries risk.")
        else:
            danger_summary = ("Elevated: " + ", ".join(hot) + " at/above trip; the throttle halves exposure and "
                              "the book flattens the stressed sleeves, mechanically.")

    m = CFG["metals"]; bt = CFG["backtest"]
    metals = "".join(
        f'<div class="mtile"><div class="mt-h">{html.escape(nm)}<span>{stance}</span></div>'
        f'<div class="mt-cell">{html.escape(cell)}</div>'
        f'<div class="mt-oos">{acc} · <span>{note}</span></div></div>'
        for nm, cell, acc, note, stance in m)

    asset_modal = (
        '<div id="zamodal" '
        'style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.55);'
        'align-items:center;justify-content:center;padding:18px">'
        '<div style="background:var(--surface);border:1px solid var(--line);border-radius:14px;'
        'padding:20px 22px;max-width:670px;width:100%;box-shadow:var(--shadow)">'
        '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:2px">'
        '<h2 id="zam-title" style="margin:0;font-size:17px;font-weight:700"></h2>'
        '<span id="zam-close" '
        'style="cursor:pointer;color:var(--faint);font-size:22px;line-height:1">&times;</span></div>'
        '<div id="zam-sub" style="font-family:var(--mono);font-size:11px;color:var(--faint);margin-bottom:12px"></div>'
        '<div id="zam-chart"></div><div id="zam-gauge" style="margin-top:14px"></div>'
        '<div id="zam-hind" style="margin-top:18px;padding-top:14px;border-top:1px solid var(--line)"></div>'
        '</div></div>'
        '<script>window.__ZA=' + json.dumps(CASS) + ';window.__ZH=' + json.dumps(HB) + ';' + ASSET_JS + '</script>'
    )
    return TEMPLATE.format(
        asset_modal=asset_modal,
        now=now, gw_asof=gw_asof or "—", g_asof=g_asof or "—", s_asof=s_asof or "—",
        p_asof=CFG["portfolio_asof"], b_asof=CFG["board_asof"], n_picks=len(picks),
        posrows=posrows, gross=gross_str, throttle=CFG["throttle"], lev=lev_str,
        cap=CFG["cap"], monthly=CFG["monthly_leg"], picks=pk, gamma=gt, sectors=sr, metals=metals,
        structural_picks=structural_picks_panel(),   # Minervini structural picks (KO, ABBV, …) in Stock Picks
        greek_desk=greek_desk_panel(),
        top_picks=top_picks,
        indices_board=indices_board, metals_board=metals_board, idx_call_now=idx_call_now,
        p_basis=p_basis, p_note=p_note,
        sortino=bt["sortino"], spy_sortino=bt["spy_sortino"], maxdd=bt["maxdd"], spy_maxdd=bt["spy_maxdd"],
        y2008=bt["y2008"], y2022=bt["y2022"],
        recent_url=CFG["recent_picks_url"], backtest_url=CFG["backtest_url"],
        acct=f"${acct:,.0f}", total_notional=f"${total_notional:,.0f}",
        d_asof=d_asof, danger_gauges=danger_gauges, regime_html=regime_html, danger_summary=danger_summary,
    )

TEMPLATE = r"""<meta charset="utf-8">
<title>ZION System Dashboard</title>
<style>
  :root{{
    --ground:#ffffff;--surface:#f6f5fb;--surface-2:#eeecf8;--line:#e4e1f2;--rule:#e8e5f2;
    --ink:#181919;--ink-soft:#54525f;--faint:#8b8898;
    --mystic:#6a49e8;--mystic-soft:#efeafe;--forest:#2f8f63;--forest-soft:#e7f5ee;
    --up:#1a7a3a;--down:#c0392b;--amber:#c77d20;--amber-soft:#fbf1e2;--hold:#8b8898;
    --sans:'Helvetica Neue',Helvetica,Arial,system-ui,sans-serif;
    --mono:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    --shadow:0 1px 2px rgba(24,25,25,.04),0 8px 24px -12px rgba(106,73,232,.14);
  }}
  @media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
    --ground:#121319;--surface:#1b1d25;--surface-2:#22242e;--line:#2b2d38;--rule:#2a2c37;
    --ink:#ecebf3;--ink-soft:#a8a5b6;--faint:#6f6c7d;--mystic:#8f78f2;--mystic-soft:#221f3a;
    --forest:#5fa385;--forest-soft:#16241d;--up:#5fa385;--down:#e0725c;--amber:#e0a24e;--amber-soft:#2a2113;--hold:#6f6c7d;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);}}}}
  :root[data-theme="dark"]{{
    --ground:#121319;--surface:#1b1d25;--surface-2:#22242e;--line:#2b2d38;--rule:#2a2c37;
    --ink:#ecebf3;--ink-soft:#a8a5b6;--faint:#6f6c7d;--mystic:#8f78f2;--mystic-soft:#221f3a;
    --forest:#5fa385;--forest-soft:#16241d;--up:#5fa385;--down:#e0725c;--amber:#e0a24e;--amber-soft:#2a2113;--hold:#6f6c7d;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;line-height:1.5}}
  .page{{max-width:1180px;margin:0 auto;padding:clamp(18px,4vw,40px) clamp(14px,4vw,36px) 60px}}
  .num{{font-variant-numeric:tabular-nums}}
  .mast{{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:14px;border-bottom:2px solid var(--ink);padding-bottom:14px}}
  .brand .wm{{font-size:clamp(26px,5vw,40px);font-weight:700;letter-spacing:.14em;line-height:1}}
  .brand .wm .o{{color:var(--mystic)}}
  .brand .sub{{font-family:var(--mono);font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-soft);margin-top:5px}}
  .mast .meta{{text-align:right;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);line-height:1.7}}
  .recent-fixed{{position:fixed;right:16px;bottom:16px;z-index:50;font-family:var(--mono);font-size:10px;letter-spacing:.11em;
    text-transform:uppercase;font-weight:600;color:var(--ink-soft);background:var(--surface);border:1px solid var(--line);
    padding:6px 13px;border-radius:999px;text-decoration:none;box-shadow:var(--shadow);opacity:.72;transition:opacity .12s,color .12s,border-color .12s}}
  .recent-fixed:hover{{opacity:1;color:var(--mystic);border-color:var(--mystic)}}
  .card-link{{display:inline-block;margin-top:13px;font-family:var(--mono);font-size:11px;letter-spacing:.05em;
    font-weight:700;color:var(--mystic);text-decoration:none;border-bottom:1.5px solid var(--mystic-soft);padding-bottom:1px}}
  .card-link:hover{{border-bottom-color:var(--mystic)}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}}
  .card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:var(--shadow)}}
  .card.wide{{grid-column:1/-1}}
  .ch{{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:4px}}
  .ch h2{{margin:0;font-size:16px;font-weight:700;letter-spacing:-.01em}}
  .basis{{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;padding:3px 7px;border-radius:5px;white-space:nowrap}}
  .basis.live{{background:var(--forest-soft);color:var(--forest)}}
  .basis.issued{{background:var(--mystic-soft);color:var(--mystic)}}
  .basis.model{{background:var(--amber-soft);color:var(--amber)}}
  .note{{color:var(--faint);font-size:11.5px;margin:2px 0 14px}}
  /* portfolio */
  .exp{{display:flex;flex-direction:column;gap:9px}}
  .exp-row{{display:grid;grid-template-columns:96px 1fr 58px;align-items:center;gap:11px}}
  .exp-row .nm{{font-family:var(--mono);font-size:11px;color:var(--ink-soft)}}
  .track{{position:relative;height:11px;background:var(--surface-2);border-radius:6px;overflow:hidden}}
  .track .fill{{position:absolute;left:0;top:0;bottom:0;border-radius:6px;background:var(--mystic)}}
  .track .fill.hedge{{background:var(--forest)}}
  .exp-row .v{{font-family:var(--mono);font-size:12px;text-align:right;font-variant-numeric:tabular-nums}}
  .exp-row .v.z{{color:var(--faint)}}
  .tw{{overflow-x:auto}}
  table.ptab{{border-collapse:collapse;width:100%;font-size:13px}}
  .ptab th,.ptab td{{text-align:right;padding:7px 8px;border-bottom:1px solid var(--rule)}}
  .ptab th:first-child,.ptab td:first-child{{text-align:left}}
  .ptab thead th{{font-family:var(--mono);font-size:8.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);font-weight:400;border-bottom:1.5px solid var(--ink)}}
  .ptab tbody td{{font-variant-numeric:tabular-nums}}
  .ptab td.lab{{font-weight:600}}
  .ptab .tk{{font-family:var(--mono);font-size:10px;color:var(--mystic);font-weight:400;margin-left:6px}}
  .ptab td.sh{{font-weight:700}}
  .ptab tr.flat td{{color:var(--faint)}} .ptab tr.flat .tk{{color:var(--faint)}}
  .ptab tr.hedge td.lab{{color:var(--forest)}}
  .ptab tfoot td{{border-bottom:none;border-top:1.5px solid var(--rule);font-family:var(--mono);font-size:11px;color:var(--ink-soft);padding-top:9px}}
  .ptab tfoot td.lab{{font-weight:600;text-transform:uppercase;letter-spacing:.06em;font-size:9.5px}}
  .pfoot{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:14px;padding-top:12px;border-top:1px solid var(--rule)}}
  .stat{{display:flex;flex-direction:column;justify-content:flex-end;gap:3px}}
  .stat .sl{{font-family:var(--mono);font-size:9px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}}
  .stat .sv{{font-size:18px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}}
  /* picks */
  .picks{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:9px}}
  .pick{{background:var(--surface-2);border:1px solid var(--line);border-radius:9px;padding:10px 12px;border-left:3px solid var(--forest)}}
  .pk-top{{display:flex;justify-content:space-between;align-items:baseline}}
  .pk-sym{{font-weight:700;font-size:15px;letter-spacing:.02em}}
  .pk-dir{{font-family:var(--mono);font-size:11px;font-weight:700}}
  .pk-dir.up{{color:var(--up)}}
  .pk-stats{{display:flex;gap:12px;font-family:var(--mono);font-size:10.5px;color:var(--ink-soft);margin-top:6px}}
  .pk-dates{{font-family:var(--mono);font-size:9px;color:var(--faint);margin-top:5px;letter-spacing:.01em}}
  .pk-dates b{{color:var(--ink-soft);font-weight:600}}
  .pk-stats b{{color:var(--ink)}}
  .pk-cass{{font-family:var(--mono);font-size:9.5px;margin-top:6px;color:var(--faint)}}
  .pk-cass.hi{{color:var(--forest)}} .pk-cass.med{{color:var(--amber)}}
  /* gamma */
  .gamma{{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:9px;margin-top:6px}}
  .gtile{{border-radius:9px;padding:11px 13px;border:1px solid var(--line)}}
  .gtile.pos{{background:var(--forest-soft)}} .gtile.neg{{background:var(--amber-soft)}}
  .gt-h{{display:flex;justify-content:space-between;align-items:baseline;font-weight:700}}
  .gt-reg{{font-family:var(--mono);font-size:9px;letter-spacing:.05em;text-transform:uppercase;font-weight:600}}
  .gtile.pos .gt-reg{{color:var(--forest)}} .gtile.neg .gt-reg{{color:var(--amber)}}
  .gt-spot{{font-family:var(--mono);font-size:15px;font-weight:700;margin:6px 0 8px;font-variant-numeric:tabular-nums}}
  .gt-spot span{{font-size:10px;font-weight:400;color:var(--ink-soft);letter-spacing:.03em}}
  .gt-row{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;color:var(--ink-soft);margin-top:3px}}
  .gt-vol{{color:var(--ink);font-weight:600}}
  /* metals */
  .metals{{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}}
  .mtile{{background:var(--surface-2);border:1px solid var(--line);border-radius:9px;padding:11px 13px}}
  .mt-h{{display:flex;justify-content:space-between;align-items:baseline;font-weight:700}}
  .mt-h span{{font-family:var(--mono);font-size:9.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);font-weight:400}}
  .mt-cell{{font-size:12px;color:var(--ink-soft);margin:7px 0 8px}}
  .mt-oos{{font-family:var(--mono);font-size:10.5px;font-weight:700;color:var(--forest)}}
  .mt-oos span{{color:var(--faint);font-weight:400}}
  /* sectors */
  .sect{{display:flex;flex-direction:column;gap:0}}
  .srow{{display:grid;grid-template-columns:1fr 104px 84px 92px 1.25fr;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--rule);font-size:13px}}
  /* name is the sole flexible track; the detail column is just an icon (fixed narrow) so the name gets the
     slack and stays on ONE line -> rows are as compact as the Sectors/Precious-metals boards */
  .srow.idx{{grid-template-columns:1fr 116px 64px 58px 96px 40px}}
  .srow.idx>*{{min-width:0}}
  .srow.idx .s-nm{{padding-right:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .srow.idx .s-price{{overflow:hidden;padding-right:10px}}   /* clamp so the band can never spill into Conviction */
  .srow.idx .s-price small{{white-space:normal;word-break:break-word}}  /* band wraps if a wide font makes it too long */
  .srow.shdr{{padding:0 0 6px;font-family:var(--mono);font-size:8px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);cursor:default}}
  .srow.shdr span{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .s-sell{{display:flex;flex-direction:column;align-items:flex-start;line-height:1.18;text-align:left}}
  .s-sell b{{font-family:var(--mono);font-size:12px;font-weight:700;color:var(--ink);font-variant-numeric:tabular-nums}}
  .s-sell b.none{{color:var(--faint);font-weight:400}}
  .s-sell b.gated{{color:var(--amber);font-size:11px;font-weight:600}}
  .s-sell small{{font-family:var(--mono);font-size:8px;color:var(--faint);line-height:1.3}}
  .srow.idx .s-call{{justify-self:start;text-align:left}}
  .s-price{{display:flex;flex-direction:column;line-height:1.15}}
  .s-price b{{font-family:var(--mono);font-size:13.5px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--ink)}}
  .s-price b.none{{color:var(--faint);font-weight:400}}
  .s-price b.gated{{color:var(--amber);font-weight:600;font-size:11px}}
  .s-price small{{font-family:var(--mono);font-size:8.5px;color:var(--faint);font-variant-numeric:tabular-nums}}
  .stars{{position:relative;display:inline-block;font-size:14px;line-height:1;letter-spacing:1px;white-space:nowrap}}
  .stars .bg{{color:var(--line)}}
  .stars .fg{{position:absolute;left:0;top:0;overflow:hidden;color:var(--amber)}}
  .srow:last-child{{border-bottom:none}}
  .s-nm{{font-weight:600}}
  .dec-badge{{font-family:var(--mono);font-size:7.5px;font-weight:600;letter-spacing:.04em;color:var(--mystic);
    background:var(--mystic-soft);border:1px solid var(--mystic);border-radius:4px;padding:1px 4px;margin-left:6px;
    white-space:nowrap;vertical-align:middle;text-transform:uppercase}}
  .s-call{{font-family:var(--mono);font-size:9.5px;font-weight:700;letter-spacing:.06em;text-align:center;padding:3px 6px;border-radius:5px}}
  .s-call.abst{{background:var(--amber-soft,#2a2113);color:var(--amber,#e0a24e);border:1px solid var(--amber,#e0a24e)}}
  .s-call.fire{{background:var(--forest-soft);color:var(--forest);border:1px solid var(--forest)}}
  .s-call.long{{background:var(--forest-soft);color:var(--forest);border:1px solid var(--forest)}}
  .s-call.high{{background:var(--forest);color:#fff;border:1px solid var(--forest)}}
  .s-call.watch{{background:var(--amber-soft,#4a3a12);color:var(--amber,#d9a441);border:1px solid var(--amber,#d9a441)}}
  .s-call.sell{{background:rgba(224,114,92,0.14);color:var(--down);border:1px solid var(--down)}}
  .s-call.hold{{background:var(--surface-2);color:var(--ink-soft);border:1px solid var(--line)}}
  .s-call.lag{{background:var(--amber-soft,#2a2113);color:var(--amber,#d9a441);border:1px dashed var(--amber,#d9a441)}}
  .s-call small{{font-family:var(--mono);font-size:8.5px;opacity:.8;margin-left:2px}}
  .s-dir{{font-family:var(--mono);font-size:11px;font-weight:700}}
  .s-dir.up{{color:var(--up)}} .s-dir.dn{{color:var(--down)}}
  .s-acc{{font-family:var(--mono);font-size:12px;text-align:right;font-variant-numeric:tabular-nums}}
  .s-acc small{{color:var(--faint);font-size:8.5px;letter-spacing:.05em}}
  .s-best{{font-family:var(--mono);font-size:10px;color:var(--faint);text-align:right}}
  .mombadge{{cursor:pointer;font-size:11px;line-height:1;padding:0 2px;user-select:none;vertical-align:baseline}}
  .mombadge.run{{color:var(--forest)}}
  .mombadge.flat{{color:var(--amber)}}
  .mombadge:focus{{outline:1px dotted var(--faint);outline-offset:1px}}
  .mominfo{{display:none;grid-column:1/-1;text-align:left;margin:4px 0 2px;padding:7px 9px;border-left:2px solid var(--rule);
    background:var(--surface-2);border-radius:5px;font-family:var(--mono);font-size:10px;line-height:1.5;color:var(--ink-soft);white-space:normal}}
  .mominfo.open{{display:block}}
  /* dangers */
  .danger-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:6px}}
  .gauge{{background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:13px 15px;border-left:3px solid var(--forest)}}
  .gauge.watch{{border-left-color:var(--amber)}} .gauge.stress{{border-left-color:var(--down)}}
  .gg-h{{display:flex;justify-content:space-between;align-items:baseline;font-weight:700;font-size:14px}}
  .gg-state{{font-family:var(--mono);font-size:9px;letter-spacing:.08em;color:var(--forest)}}
  .gauge.watch .gg-state{{color:var(--amber)}} .gauge.stress .gg-state{{color:var(--down)}}
  .gg-val{{font-family:var(--mono);font-size:17px;font-weight:700;margin:8px 0 11px;font-variant-numeric:tabular-nums}}
  .gg-val span{{font-size:10px;font-weight:400;color:var(--ink-soft);letter-spacing:.02em}}
  .gg-track{{position:relative;height:8px;background:var(--surface);border:1px solid var(--line);border-radius:5px}}
  .gg-fill{{position:absolute;left:0;top:0;bottom:0;border-radius:5px;background:var(--forest)}}
  .gauge.watch .gg-fill{{background:var(--amber)}} .gauge.stress .gg-fill{{background:var(--down)}}
  .gg-thresh{{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--down);opacity:.75}}
  .gg-scale{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:8.5px;color:var(--faint);margin-top:5px;text-transform:uppercase;letter-spacing:.05em}}
  .regime{{border-radius:10px;padding:13px 15px;border:1px solid var(--line);background:var(--forest-soft)}}
  .regime.caution{{background:var(--amber-soft)}} .regime.stress{{background:var(--down)}}
  .rg-l{{font-family:var(--mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft)}}
  .rg-v{{font-size:26px;font-weight:700;letter-spacing:.02em;margin:5px 0 6px;color:var(--forest)}}
  .regime.caution .rg-v{{color:var(--amber)}}
  .regime.stress .rg-l,.regime.stress .rg-v,.regime.stress .rg-x{{color:#fff}}
  .rg-x{{font-family:var(--mono);font-size:10px;color:var(--ink-soft)}}
  @media(max-width:820px){{.danger-grid{{grid-template-columns:1fr}}}}
  /* backtest strip */
  .bstrip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}}
  .bt{{background:var(--surface-2);border-radius:9px;padding:12px 14px}}
  .bt .bl{{font-family:var(--mono);font-size:9px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}}
  .bt .bv{{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:3px}}
  .bt .bx{{font-size:11px;color:var(--ink-soft)}} .bt .bx b{{color:var(--down)}}
  .foot{{margin-top:18px;padding-top:14px;border-top:1px solid var(--rule);font-size:11.5px;color:var(--faint);line-height:1.6}}
  .disclaimer{{margin-top:10px;padding-top:10px;border-top:1px solid var(--rule);font-size:9px;color:var(--faint);line-height:1.55;text-align:justify}}
  .foot b{{color:var(--ink-soft)}}
  .colo{{margin-top:10px;font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
  @media(max-width:820px){{.grid{{grid-template-columns:1fr}}.pfoot{{grid-template-columns:repeat(2,1fr)}}.metals{{grid-template-columns:1fr}}}}
</style>
<div class="page">
  <header class="mast">
    <div class="brand"><div class="wm">ZI<span class="o">&#9670;</span>N</div>
      <div class="sub">System Dashboard &middot; Zoltar Predicts</div></div>
    <div class="meta"><div style="text-align:left">Rebuilt {now}</div>Daily refresh</div>
  </header>

  <!-- PORTFOLIO -->
  <section class="card wide" style="margin-top:16px">
    <div class="ch"><h2>The ZION Portfolio &middot; {acct}</h2><span class="basis issued">{p_basis}</span></div>
    <p class="note">{p_note}</p>
    <div class="tw"><table class="ptab">
      <thead><tr><th>Sleeve</th><th>Exposure</th><th>Notional</th><th>Last</th><th>Shares</th></tr></thead>
      <tbody>{posrows}</tbody>
      <tfoot><tr><td class="lab">Deployed (net)</td><td></td><td class="num">{total_notional}</td><td></td><td></td></tr></tfoot>
    </table></div>
    <div class="pfoot" style="grid-template-columns:repeat(7,1fr);align-items:end">
      <div class="stat"><div class="sl">Sortino</div><div class="sv num">{sortino}</div></div>
      <div class="stat"><div class="sl">Gross notional</div><div class="sv num">{gross}&times;</div></div>
      <div class="stat"><div class="sl">Throttle</div><div class="sv num">{throttle}</div></div>
      <div class="stat"><div class="sl">Leverage (staged)</div><div class="sv num">{lev}&times;</div></div>
      <div class="stat"><div class="sl">Monthly leg</div><div class="sv num">{monthly}</div></div>
      <div class="stat"><div class="sl">Max DD @4&times;</div><div class="sv num">{maxdd}</div></div>
      <div class="stat"><div class="sl">2008 / 2022</div><div class="sv num" style="font-size:14px">{y2008} / {y2022}</div></div>
    </div>
    <a class="card-link" href="{backtest_url}" target="_blank" rel="noopener">Backtest Results &rarr;</a>
  </section>

  <!-- INDICES -->
  <section class="card wide" style="margin-top:14px">
    <div class="ch"><h2>US Domestic Markets</h2></div>
    <div class="sect">{indices_board}</div>
  </section>

  <!-- PRECIOUS METALS — RATING -->
  <section class="card wide" style="margin-top:14px">
    <div class="ch"><h2>Precious Metals</h2></div>
    <div class="sect">{metals_board}</div>
  </section>

  <!-- SECTORS -->
  <section class="card wide" style="margin-top:14px">
    <div class="ch"><h2>Sectors &middot; OOS gauntlet</h2></div>
    <div class="sect">{sectors}</div>
  </section>

  <!-- STOCK PICKS (board-scanner 21d directional + structural Minervini) -->
  <section class="card wide" style="margin-top:14px">
    <div class="ch"><h2>Stock Picks</h2></div>
    <div class="picks">{picks}</div>
    {structural_picks}
  </section>

  <!-- GREEKWATCH OPTIONS DESK (desk calls + squeeze + Options Corner) -->
  {greek_desk}

  <!-- DANGERS BEING MONITORED -->
  <section class="card wide" style="margin-top:14px">
    <div class="ch"><h2>Dangers Being Monitored</h2><span class="basis issued">Stress gate &middot; {d_asof}</span></div>
    <p class="note">The two inputs to ZION's stress throttle — equity volatility and the corporate credit spread —
      with INTERSTELLAR's liquidity regime. Each input trips (halving exposure) only at its 70th percentile;
      under stress the book flattens the affected sleeves, mechanically, before a drawdown compounds.</p>
    <div class="danger-grid">
      {danger_gauges}
      {regime_html}
    </div>
    <p class="note" style="margin:12px 0 0">{danger_summary}</p>
  </section>

  <!-- METHODOLOGY FOOTNOTES -->
  <section class="card wide" style="margin-top:14px">
    <div class="ch"><h2>Methodology notes</h2></div>
    <p class="note"><b>The boards (US markets, precious metals, sectors).</b> The first column is the
      <b>CASSANDRA</b> predicted price &mdash; the median of similarity-weighted historical analogues, with the
      p10&ndash;p90 band beneath. Where too few analogues clear the similarity floor it falls back to a
      <b>statistical random-walk band</b> (tagged &ldquo;stat&rdquo;); where the predicted per-month move is too
      wide to trust, the price is <b style="color:var(--amber,#d9a441)">gated</b> (shown for reference only) &mdash;
      but the validated directional call still stands. <b>Conviction (&#9733; of 5)</b> is the cascade's
      convergence value (<b>valb</b>) at the current frozen row, mapped to bands calibrated on a walk-forward
      <b>out-of-sample</b> test: the 5&#9733; band (valb &ge; 0.875, ~13&ndash;15% of picks) earned <b>+9.96%/6mo</b>
      at 77.8% hit / OOS Sortino 4.86 &mdash; the only tier that decisively tops realized results (a backtest-Sortino
      candidate <i>inverted</i> out-of-sample and was rejected). No cell firing &rarr; 0&#9733; &rarr; ABSTAIN.
      <b>Call</b> is the standing recommendation &mdash; each frozen cell classified on the newest
      <b>complete-data</b> row and carried forward until new macro lands (the current month's inputs publish
      mid-cycle, so the live call is the last fully-published month's, dated on each row).
      <b style="color:var(--forest)">LONG/BUY</b> &middot; <b style="color:var(--down)">SHORT/SELL</b> carry the
      cell's valb; otherwise <b>ABSTAIN</b>. On sectors, <b>Hedge</b> is index-conditional: HOLD LONG shows only
      while the S&amp;P is predicted LONG, else it flips to HEDGE (S&amp;P currently <b>{idx_call_now}</b>).</p>
    <p class="note" style="margin-top:10px"><b>Decorrelated badge.</b> A <span style="color:var(--mystic)">&#9672;
      decorrelated</span> tag marks low-beta assets (|&beta;| &le; 0.35 &mdash; e.g. Gold &beta;&asymp;0.03,
      Platinum &beta;&asymp;0.30). It is a <b>portfolio-diversification</b> virtue (a decorrelated edge diversifies
      the book), shown as its own badge and deliberately <b>not</b> folded into the conviction star &mdash; the
      out-of-sample test showed conviction (valb), not independence, is what ranks results.</p>
    <p class="note" style="margin-top:10px"><b>Stock Picks (21-day).</b> Names that cleared the board scanner's
      walk-forward gate on the 21-day horizon &mdash; Bayesian probability, board out-of-sample accuracy, and the
      CASSANDRA expected move; options-greeks driven, forward not backtest. Gated on <b>Bayes &ge; 65%</b> and
      <b>board OOS &ge; 60%</b>. The CASSANDRA sign is shown as context, not a gate (a backtest found it has no
      forward value on stocks), so picks where CASSANDRA disagrees are flagged <b style="color:var(--down)">&#9888;
      shadow</b> (kept on the board, tracked on the forward tape) rather than dropped. A pick also confirmed by the
      <b>ODYSSEY 5-day waveform</b> (momentum-up) carries a &#128293; flame &mdash; a second when its CASSANDRA
      confidence is HIGH.</p>
  </section>

  <!-- TOP PICKS (system-wide) — placed at the very end (operator 2026-09-28) -->
  <section class="card wide" id="picks" style="margin-top:14px;scroll-margin-top:16px">
    <div class="ch"><h2>Top Picks</h2><span class="basis live">System-wide &middot; conviction star</span></div>
    <p class="note">The highest-ranked names across the <b>entire system</b> &mdash; sectors, indices and metals &mdash; by conviction star.</p>
    <div class="picks">{top_picks}</div>
  </section>

  <div class="foot">
    <b>Reading the basis.</b> Portfolio &amp; metals stance are as-issued (frozen at the weekly/monthly gate).
    The 21-day stock picks are forward and walk-forward-validated but unsettled. Sector accuracies are in-sample
    (context). ZION backtest figures are hypothetical (walk-forward components, fitted assembly) — the live forward
    tape is the binding test, ~mid-November 2026. Not investment advice.
  </div>
  <div class="disclaimer">
    <b>Disclaimer.</b> This dashboard is provided for informational and educational purposes only and does not
    constitute investment advice, a research report, or an offer, solicitation or recommendation to buy, sell or
    hold any security or to adopt any investment strategy. ZOLTAR Predicts is not a registered investment adviser
    or broker-dealer, and nothing here is tailored to any individual's financial situation. All forecasts,
    conviction ratings (&#9733;), price targets and directional calls are <b>model outputs and are hypothetical</b>;
    backtested and walk-forward results do not represent actual trading, were prepared with the benefit of
    hindsight, and have inherent limitations. <b>Past performance is not indicative of future results</b>, and no
    representation is made that any account will or is likely to achieve profits or losses similar to those shown.
    Trading and investing involve substantial risk, including the possible loss of principal. Do your own research
    and consult a licensed financial professional before making any investment decision.
  </div>
  <div class="colo"><span>Zoltar Predicts &middot; ZION</span><span>Hidden patterns in plain sight</span><span>Regenerated daily</span></div>
  <a class="recent-fixed" href="{recent_url}">Recent Picks &rarr;</a>
</div>
{asset_modal}
"""

if __name__ == "__main__":
    open(OUT, "w").write(render())
    print("wrote", OUT)

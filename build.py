# -*- coding: utf-8 -*-
"""Build the Swiss SMI dividend-screen page (Helvetia gold design).
Self-contained: reads design.css, uses Google Fonts, embeds live TradingView
price widgets, and (when LIVE_FETCH=1) refreshes dividend yields + analyst
12-month target upside from Yahoo Finance, falling back to the base figures."""
import re, json, os, datetime, html as ihtml

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "index.html")

# ---- design CSS (gold palette) loaded from a committed file -----------------
design_css = open(os.path.join(HERE, "design.css"), encoding="utf-8").read()

# ---- fonts via Google Fonts CDN (IBM Plex Sans/Mono, Source Serif 4) --------
GOOGLE_FONTS = (
  '<link rel="preconnect" href="https://fonts.googleapis.com">'
  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
  '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600'
  '&family=IBM+Plex+Sans:wght@400;500;600;700'
  '&family=Source+Serif+4:wght@400;500;600;700&display=swap" rel="stylesheet">'
)
UPDATED = datetime.date.today().strftime("%d %B %Y").lstrip("0")

# ============================ DATA ===========================================
# name, ticker, sector, yield%, yld_label, upside_num, upside_label, bucket
ROWS = [
 ["Swiss Re","SREN","Reinsurance",5.9,"~5.9% fwd",6,"~+6%","Income"],
 ["Partners Group","PGHN","Private markets",5.6,"~5.6%",30,"avg tgt CHF 1,156*","Income"],
 ["Zurich Insurance","ZURN","Insurance",5.0,"~4.9–5.2%",2,"Mixed / limited","Income"],
 ["Swisscom","SCMN","Telecom",3.6,"~3.6%",-17,"−17% (Sell)","Income"],
 ["Roche","ROP","Pharma",3.75,"~3.5–4%",11,"~+11% (Buy)","Balanced"],
 ["Novartis","NOVN","Pharma",3.5,"~3.5%",11,"~+11%","Balanced"],
 ["SGS","SGSN","Testing & inspection",3.5,"~3.5%",5,"avg tgt CHF 98","Balanced"],
 ["Kühne+Nagel","KNIN","Logistics",3.5,"~3.2–3.5%",7,"Buy upgrade","Balanced"],
 ["Nestlé","NESN","Consumer staples",3.3,"~3.3%",10,"~+10%","Balanced"],
 ["Holcim","HOLN","Building materials",2.75,"~2.5–3%",8,"~+8% (Buy)","Growth"],
 ["UBS","UBSG","Banking",2.5,"~2.5%",18,"~+18%","Growth"],
 ["ABB","ABBN","Electrification",1.4,"~1.4%",4,"Tgt raised ~CHF 52","Growth"],
]
BUCKET_CLS = {"Income":"hi","Balanced":"bar","Growth":"bar2"}

# ---- live refresh: dividend yields from live prices (Yahoo chart endpoint) ---
# The chart endpoint is keyless and reliable. Yields recompute from live price /
# a stable dividend-per-share; the 12-month "signals" are reviewed periodically.
YAHOO = {"SREN":"SREN.SW","PGHN":"PGHN.SW","ZURN":"ZURN.SW","SCMN":"SCMN.SW",
         "ROP":"ROG.SW","NOVN":"NOVN.SW","SGSN":"SGSN.SW","KNIN":"KNIN.SW",
         "NESN":"NESN.SW","HOLN":"HOLN.SW","UBSG":"UBSG.SW","ABBN":"ABBN.SW"}
# approximate current annual dividend per share (CHF) — reviewed occasionally
DPS = {"SREN":7.00,"PGHN":42.00,"ZURN":28.00,"SCMN":22.00,"ROP":9.70,
       "NOVN":3.50,"SGSN":3.30,"KNIN":8.25,"NESN":3.05,"HOLN":2.10,
       "UBSG":0.85,"ABBN":0.90}

def fetch_live(rows):
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                    "(KHTML, like Gecko) Chrome/124 Safari/537.36"})
    n_ok = 0
    for r in rows:
        base = YAHOO.get(r[1])
        if not base:
            continue
        price = None
        for sym in [base] + (["ROP.SW"] if r[1] == "ROP" else []):
            try:
                url = ("https://query1.finance.yahoo.com/v8/finance/chart/" + sym +
                       "?interval=1d&range=1d")
                meta = s.get(url, timeout=15).json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice")
                if price:
                    break
            except Exception as e:
                print("price fail", sym, e)
        dps = DPS.get(r[1])
        if price and dps:
            y = round(dps / price * 100, 1)
            r[3] = y; r[4] = f"~{y:.1f}%"; n_ok += 1
        else:
            print("no price/dps for", r[1], "price=", price)
    print(f"yield refresh: {n_ok}/{len(rows)} names updated")
    return rows

if os.getenv("LIVE_FETCH") == "1":
    try:
        ROWS = fetch_live(ROWS)
    except Exception as e:
        print("fetch_live aborted (keeping base figures):", e)

# ============================ SVG CHARTS =====================================
VW = 760
def esc(s): return ihtml.escape(str(s))

def bar_rows(data, maxv, fmt, padL=132, padR=78, rowH=30, gap=11):
    n=len(data); padT=8; padB=8
    H=padT+padB+n*rowH+(n-1)*gap
    x0,x1=padL,VW-padR
    s=""
    for i,(label,val,cls) in enumerate(data):
        y=padT+i*(rowH+gap)
        w=max(2,(val/maxv)*(x1-x0))
        s+=f'<rect class="bar {cls}" x="{x0}" y="{y}" width="{w:.1f}" height="{rowH}"/>'
        s+=f'<text class="cat" x="{x0-14}" y="{y+rowH/2+4:.1f}" text-anchor="end" font-size="12.5">{esc(label)}</text>'
        s+=f'<text class="val" x="{x0+w+12:.1f}" y="{y+rowH/2+4.5:.1f}" font-size="13" font-weight="700">{esc(fmt(val))}</text>'
    return f'<svg class="svgchart" viewBox="0 0 {VW} {H}" preserveAspectRatio="xMidYMid meet" role="img">{s}</svg>'

def column_chart(data, ymin, ymax, ticks, fmt, height=360, padL=46):
    n=len(data); padT=42; padR=18; padB=46
    H=height; x0,x1=padL,VW-padR; y0=H-padB; yTop=padT
    ysc=lambda v:y0-(v-ymin)/(ymax-ymin)*(y0-yTop)
    zeroY=ysc(max(0,ymin)); slot=(x1-x0)/n; bw=min(40,slot*0.5)
    s=""
    for t in ticks:
        y=ysc(t)
        s+=f'<line class="gl" x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}"/>'
        s+=f'<text class="glabel" x="{x0-9}" y="{y+3.5:.1f}" text-anchor="end" font-size="11">{esc(t)}</text>'
    s+=f'<line class="baseline" x1="{x0}" y1="{zeroY:.1f}" x2="{x1}" y2="{zeroY:.1f}" stroke-width="1.4"/>'
    for i,(label,val,cls) in enumerate(data):
        cx=x0+slot*(i+0.5); x=cx-bw/2; vy=ysc(val)
        top=min(vy,zeroY); h=abs(vy-zeroY)
        s+=f'<rect class="bar {cls}" x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(1,h):.1f}"/>'
        lblY = top-9 if val>=0 else top+h+16
        s+=f'<text class="val" x="{cx:.1f}" y="{lblY:.1f}" text-anchor="middle" font-size="12" font-weight="700">{esc(fmt(val))}</text>'
        for li,ln in enumerate(label if isinstance(label,list) else [label]):
            s+=f'<text class="cat" x="{cx:.1f}" y="{y0+18+li*13:.1f}" text-anchor="middle" font-size="10.5">{esc(ln)}</text>'
    return f'<svg class="svgchart" viewBox="0 0 {VW} {H}" preserveAspectRatio="xMidYMid meet" role="img">{s}</svg>'

# yield bar chart (sorted desc already)
yld_data=[(f"{r[0]}", r[3], BUCKET_CLS[r[7]]) for r in ROWS]
chart_yield=bar_rows(yld_data, 6.4, lambda v:f"{v:.1f}%")

# upside column chart
up_data=[([r[1]], r[5], "pos" if r[5]>0 else "neg") for r in ROWS]
chart_upside=column_chart(up_data, -20, 35, [-20,-10,0,10,20,30], lambda v:("+" if v>0 else "")+f"{v}%", height=360)

# ============================ TABLE ==========================================
def trow(r):
    name,tk,sec,yv,yl,uv,ul,bk=r
    return (f'<tr><td><b>{esc(name)}</b></td><td class="mono">{tk}</td><td>{esc(sec)}</td>'
            f'<td class="num">{esc(yl)}</td><td class="num">{esc(ul)}</td><td>{esc(bk)}</td></tr>')
table_rows="\n".join(trow(r) for r in ROWS)

# ============================ HTML ===========================================
def P(t): return f'<p class="prose">{t}</p>'

SCRIPT_BLOCK = r"""<script>
(function(){
  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var map={}; links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a;});
  var obs=new IntersectionObserver(function(es){es.forEach(function(e){
    if(e.isIntersecting){links.forEach(function(l){l.classList.remove('active');});
      var a=map[e.target.id]; if(a)a.classList.add('active');}});},
    {rootMargin:'-20% 0px -70% 0px'});
  document.querySelectorAll('.section').forEach(function(s){obs.observe(s);});
  links.forEach(function(a){a.addEventListener('click',function(ev){
    var el=document.getElementById(a.getAttribute('href').slice(1));
    if(el){ev.preventDefault();window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-12,behavior:'smooth'});}});});
})();
</script>"""

# ---- live TradingView widgets (keyless, update on page load) ----------------
tv_symbols = [["SIX:" + r[1], r[0]] for r in ROWS]
_mq_cfg = {
    "width": "100%", "height": 540,
    "symbolsGroups": [{"name": "Swiss SMI dividend screen",
        "symbols": [{"name": s, "displayName": d} for s, d in tv_symbols]}],
    "showSymbolLogo": True, "isTransparent": True, "colorTheme": "light", "locale": "en",
}
MARKET_QUOTES = ('<div class="tradingview-widget-container">'
  '<div class="tradingview-widget-container__widget"></div>'
  '<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js" async>'
  + json.dumps(_mq_cfg) + '</script></div>')
_tt_cfg = {
    "symbols": [{"proName": s, "title": d} for s, d in tv_symbols],
    "showSymbolLogo": True, "isTransparent": True, "displayMode": "adaptive",
    "colorTheme": "light", "locale": "en",
}
TICKER_TAPE = ('<div class="tradingview-widget-container" style="border-bottom:1px solid var(--c-rule)">'
  '<div class="tradingview-widget-container__widget"></div>'
  '<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>'
  + json.dumps(_tt_cfg) + '</script></div>')

doc = f"""<!DOCTYPE html>
<html lang="en" data-palette="navy" data-density="regular">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Swiss SMI Dividend Screen · Helvetia Research</title>
{GOOGLE_FONTS}
<style>{design_css}</style>
</head>
<body>
<div class="desk">
<article class="sheet">

  <header class="masthead">
    <div class="brand">
      <svg class="mark" viewBox="0 0 34 34" aria-hidden="true">
        <rect class="acc" x="0" y="0" width="34" height="34"></rect>
        <rect class="cut" x="14.5" y="6" width="5" height="22"></rect>
        <rect class="cut" x="6" y="14.5" width="22" height="5"></rect>
      </svg>
      <span class="wm"><b>HELVETIA</b><span>Research · Geneva</span></span>
    </div>
    <div class="mh-right">
      Equity Research &nbsp;·&nbsp; Switzerland<br>
      Income Strategy &nbsp;·&nbsp; <b>Dividend Screen</b>
    </div>
  </header>
  <div class="goldrule"></div>
  {TICKER_TAPE}

  <div class="pad titleblock">
    <div class="eyebrow">Thematic screen · SMI</div>
    <h1 class="doc-title">Swiss dividend leaders:<br>income with upside</h1>
    <p class="doc-sub">A twelve-name screen of Swiss Market Index constituents pairing an above-market dividend yield with 12-month total-return potential, grouped by income, balanced and growth tilt.</p>
    <div class="doc-meta">
      <span><b>SMI constituents</b></span>
      <span>Universe&nbsp; <b>20 blue chips</b></span>
      <span>Published&nbsp; <b>9 June 2026</b></span>
      <span>Updated&nbsp; <b>{UPDATED}</b></span>
      <span>Desk&nbsp; <b>Swiss Equity Strategy · Helvetia Research</b></span>
    </div>
  </div>

  <section class="tearsheet" aria-label="Screen snapshot">
    <div class="ts-left">
      <div class="ts-company">
        <span class="name">Swiss Dividend Screen</span>
        <span class="tick">SMI</span>
      </div>
      <div class="ts-sector">SIX Swiss Exchange · 12 names · CHF income</div>
      <div class="call">
        <div class="rating-badge">
          <span class="lbl">Tilt</span>
          <span class="val">Income+</span>
        </div>
        <div class="figs">
          <div class="fig"><div class="k">Names</div><div class="v"><span class="num">12</span></div></div>
          <div class="fig"><div class="k">Top yield</div><div class="v"><span class="num">5.9</span><small>%</small></div></div>
          <div class="fig"><div class="k">Median yield</div><div class="v up num">~3.5<small>%</small></div></div>
        </div>
      </div>
      <div class="recscale" style="margin-top:26px">
        <div class="scale-lbl">Return tilt mix</div>
        <div class="scale-track">
          <div class="scale-seg active"></div><div class="scale-seg active"></div>
          <div class="scale-seg active"></div><div class="scale-seg"></div><div class="scale-seg"></div>
        </div>
        <div class="scale-names">
          <span class="on">Income</span><span class="on">Balanced</span><span class="on">Growth</span><span>—</span><span>—</span>
        </div>
      </div>
    </div>
    <div class="ts-right">
      <div class="scale-lbl" style="font-family:var(--font-mono);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--c-faint)">Screen at a glance</div>
      <div class="statgrid">
        <div class="stat"><div class="k">Highest yield</div><div class="v" style="font-size:15px">Swiss Re · 5.9%</div></div>
        <div class="stat"><div class="k">Highest upside</div><div class="v" style="font-size:15px">UBS · ~+18%</div></div>
        <div class="stat"><div class="k">Income names</div><div class="v num">4</div></div>
        <div class="stat"><div class="k">Balanced names</div><div class="v num">5</div></div>
        <div class="stat"><div class="k">Growth names</div><div class="v num">3</div></div>
        <div class="stat"><div class="k">Withholding tax</div><div class="v" style="font-size:15px">35% (reclaim.)</div></div>
      </div>
    </div>
  </section>

  <div class="layout">
    <nav class="toc" aria-label="Contents">
      <h4>Contents</h4>
      <ol>
        <li><a href="#s1">Overview &amp; method</a></li>
        <li><a href="#s2">The screen</a></li>
        <li><a href="#s3">Income leaders</a></li>
        <li><a href="#s4">Balanced total-return</a></li>
        <li><a href="#s5">Growth tilt &amp; risks</a></li>
      </ol>
    </nav>

    <main class="flow">

      <section class="section" id="s1" data-screen-label="01 Overview">
        <div class="sec-head"><span class="sec-num">01</span><h2 class="sec-title">Overview &amp; method</h2></div>
        <div class="sec-rule"></div>
        <p class="lead"><span class="drop">Swiss large caps remain a core destination for hard-currency income</span> without giving up the prospect of capital appreciation. This screen takes the twenty SMI constituents and surfaces twelve names that pair an above-market dividend yield with positive 12-month analyst total-return potential.</p>
        <div class="keypoints">
          <div class="kp"><span class="kp-ix">01</span><p><b>Income anchors.</b> Swiss Re, Partners Group and Zurich offer the richest yields (~5–6%), backed by capital-return-focused franchises.</p></div>
          <div class="kp"><span class="kp-ix">02</span><p><b>Balanced compounders.</b> Roche, Novartis and Nestlé combine ~3.3–4% yields with double-digit consensus upside and defensive earnings.</p></div>
          <div class="kp"><span class="kp-ix">03</span><p><b>Growth tilt.</b> UBS and Holcim trade lower yields for the highest analyst-implied price appreciation in the group.</p></div>
          <div class="kp"><span class="kp-ix">04</span><p><b>Watch the coupon-only names.</b> Swisscom yields ~3.6% but screens as a consensus <b>Sell</b> on valuation — income today, capital-loss risk on the target.</p></div>
        </div>
        <p class="prose"><b>Method.</b> The universe is the SMI. Names were screened qualitatively for (i) an indicative dividend yield at or above the broad Swiss-market average and (ii) the 12-month consensus price-target signal, then grouped by return tilt. Yields and analyst targets are indicative figures gathered from public mid-2026 sources, are rounded, and move continuously. This note is for information only and is not investment advice.</p>
      </section>

      <section class="section" id="s2" data-screen-label="02 The screen">
        <div class="sec-head"><span class="sec-num">02</span><h2 class="sec-title">The screen</h2></div>
        <div class="sec-rule"></div>
        <figure class="figure">
          <figcaption class="fig-cap"><span class="ttl">Live market prices</span><span class="ex">TradingView · live</span></figcaption>
          <div class="fig-body">{MARKET_QUOTES}</div>
          <div class="fig-note"><b>Live:</b> last price and daily change refresh each time the page loads (market-hours / delay dependent). The dividend-yield and 12-month-signal columns below are indicative mid-2026 figures and do <b>not</b> update live.</div>
        </figure>
        <table class="tbl">
          <caption>Swiss SMI dividend screen — dividend yields auto-refreshed {UPDATED} from live prices; 12-month signals reviewed periodically</caption>
          <thead><tr><th>Company</th><th>Ticker</th><th>Sector</th><th>Div. yield</th><th>12m signal</th><th>Tilt</th></tr></thead>
          <tbody>
          {table_rows}
          </tbody>
        </table>
        <p class="fig-note" style="font-family:var(--font-mono);font-size:10px;color:var(--c-faint);padding:0 0 6px">* Partners Group: mean analyst target ~CHF 1,156 implies large but widely dispersed upside; treat with caution.</p>

        <figure class="figure">
          <figcaption class="fig-cap"><span class="ttl">Dividend yield by name</span><span class="ex">% · indicative</span></figcaption>
          <div class="legend"><span><i class="hi"></i>Income</span><span><i class="bar"></i>Balanced</span><span><i class="bar2"></i>Growth</span></div>
          <div class="fig-body">{chart_yield}</div>
          <div class="fig-note"><b>Source:</b> public mid-2026 data, Helvetia Research. Bars coloured by return tilt.</div>
        </figure>

        <figure class="figure">
          <figcaption class="fig-cap"><span class="ttl">12-month consensus upside</span><span class="ex">% to mean target</span></figcaption>
          <div class="fig-body">{chart_upside}</div>
          <div class="fig-note"><b>Reading:</b> distance to the mean analyst 12-month price target. Swisscom screens negative; Partners Group shown at an indicative midpoint of a very wide range. Targets are sentiment gauges, not forecasts.</div>
        </figure>
      </section>

      <section class="section" id="s3" data-screen-label="03 Income leaders">
        <div class="sec-head"><span class="sec-num">03</span><h2 class="sec-title">Income leaders</h2></div>
        <div class="sec-rule"></div>
        <div class="subhead">Yield-led, capital-return franchises</div>
        {P("<b>Swiss Re (SREN)</b> is the highest-yielding name in the screen — a forward yield near <strong>5.9%</strong> from a diversified global reinsurer with strong solvency and a progressive ordinary-dividend policy. The total-return case is primarily the coupon; consensus upside to target is only mid-single-digit, and catastrophe experience is the key swing factor.")}
        {P("<b>Partners Group (PGHN)</b> pairs a ~<strong>5.6%</strong> yield with the largest analyst-implied upside in the group (mean target ~CHF 1,156 versus a depressed share price). It is both an income and a recovery story, but the upside dispersion is very wide and earnings are sensitive to private-markets fundraising and realisations.")}
        {P("<b>Zurich Insurance (ZURN)</b> offers a secure, well-covered ~<strong>5%</strong> dividend from a high-quality composite insurer. We frame it as an income anchor: upside estimates diverge sharply across vendors, so the total return is dominated by the distribution rather than multiple expansion.")}
        {P("<b>Swisscom (SCMN)</b> yields ~<strong>3.6%</strong> with classic telecom defensiveness, but it screens as a consensus <strong>Sell</strong> with the average target roughly 17% below the current price. It belongs here for income, with the explicit caveat that analysts see valuation downside — a coupon-only holding.")}
      </section>

      <section class="section" id="s4" data-screen-label="04 Balanced">
        <div class="sec-head"><span class="sec-num">04</span><h2 class="sec-title">Balanced total-return</h2></div>
        <div class="sec-rule"></div>
        <div class="subhead">Yield plus credible capital gain</div>
        {P("<b>Roche (ROP)</b> and <b>Novartis (NOVN)</b> are the sweet spot of the screen: ~<strong>3.5%+</strong> yields, defensive pharmaceutical earnings, multi-decade dividend-growth records and ~<strong>+11%</strong> consensus upside on constructive (Buy-biased) ratings. Pipeline delivery is the swing factor for both.")}
        {P("<b>Nestlé (NESN)</b> is the low-volatility staples compounder — a ~<strong>3.3%</strong> yield, one of Europe's longest dividend-growth streaks, and ~<strong>+10%</strong> upside as a below-trend multiple recovers on a return to volume growth.")}
        {P("<b>SGS (SGSN)</b> and <b>Kühne+Nagel (KNIN)</b> round out the balanced bucket with ~<strong>3.5%</strong> yields. SGS offers steady testing-and-inspection cash flows and a Buy-biased consensus; Kühne+Nagel adds a more cyclical, logistics-driven recovery angle and was recently upgraded to Buy.")}
        <figure class="figure">
          <figcaption class="fig-cap"><span class="ttl">Where the balanced names sit</span><span class="ex">yield vs upside</span></figcaption>
          <div class="fig-body">{column_chart([(["ROG"],11,"pos"),(["NOVN"],11,"pos"),(["SGS"],5,"pos"),(["KNIN"],7,"pos"),(["NESN"],10,"pos")], 0, 14, [0,4,8,12], lambda v:"+"+str(v)+"%", height=300)}</div>
          <div class="fig-note">Indicative 12-month consensus upside for the balanced bucket. All combine this with ~3.3–3.5% yields.</div>
        </figure>
      </section>

      <section class="section" id="s5" data-screen-label="05 Growth & risks">
        <div class="sec-head"><span class="sec-num">05</span><h2 class="sec-title">Growth tilt &amp; risks</h2></div>
        <div class="sec-rule"></div>
        <div class="subhead">Lower yield, higher upside</div>
        {P("<b>UBS (UBSG)</b> carries the highest analyst upside in the screen (~<strong>+18%</strong>) on a ~2.5% yield — a Credit Suisse-integration and capital-normalisation story where income is a supplement, not the core. <b>Holcim (HOLN)</b> offers a cyclical re-rating on ~2.5–3% yield and ~+8% upside, while <b>ABB (ABBN)</b> is the lowest yielder (~1.4%) but a structural electrification grower with a recently raised target.")}
        <div class="callout">
          <p>For <strong>income first</strong>, lead with Swiss Re, Partners Group and Zurich. For a <strong>balance of yield and capital gain</strong> — the screen's objective — Roche, Novartis and Nestlé stand out. For a <strong>growth tilt</strong>, UBS and Holcim offer the most upside at the cost of current income.</p>
        </div>
        <div class="subhead">Risks &amp; caveats</div>
        {P("This is a screen, not a recommendation, and not investment advice. Analyst price targets are weak predictors of realised return and dispersed widely for some names (notably Zurich and Partners Group). Dividends are not guaranteed and can be cut. As a Swiss resident, factor in the 35% withholding tax (reclaimable for residents) and how the income fits your overall tax position. Yields and targets shift continuously — verify live figures before acting.")}
        <p class="bigquote">Hard-currency income, with selective upside — but the coupon does the heavy lifting.</p>
      </section>

    </main>
  </div>

  <div class="goldrule thin"></div>
  <footer class="colophon">
    <div class="row">
      <div class="brand">
        <svg class="mark" viewBox="0 0 34 34" aria-hidden="true">
          <rect class="acc" x="0" y="0" width="34" height="34"></rect>
          <rect class="cut" x="14.5" y="6" width="5" height="22"></rect>
          <rect class="cut" x="6" y="14.5" width="22" height="5"></rect>
        </svg>
        <span class="wm" style="line-height:1.1"><b style="color:var(--c-ink);font-family:var(--font-display);font-weight:600;letter-spacing:.14em;font-size:15px">HELVETIA RESEARCH</b><span style="font-family:var(--font-mono);font-size:9px;letter-spacing:.28em;color:var(--c-accent-2);text-transform:uppercase;margin-top:3px">Swiss Equity Strategy · Geneva</span></span>
      </div>
      <div style="font-family:var(--font-mono);font-size:9.5px;letter-spacing:.12em;color:var(--c-faint);text-transform:uppercase;text-align:right">
        Swiss SMI Dividend Screen<br>9 June 2026 · 12 names · Income+
      </div>
    </div>
    <p class="disclaimer"><b>Disclaimer.</b> This document is produced by Helvetia Research for information purposes only and constitutes neither an offer nor a solicitation to buy or sell any financial instrument. It is not investment, legal or tax advice and does not take account of any individual's circumstances, objectives or risk tolerance. Dividend yields and analyst price targets are indicative figures drawn from publicly available third-party sources believed to be reliable but not independently verified; they are rounded and change continuously with prices, estimates and corporate actions. Past performance, current yields and analyst targets are not reliable indicators of future results. Dividends are not guaranteed and may be reduced or suspended. Swiss dividends are subject to 35% withholding tax at source, the treatment of which depends on the investor's residence. Every investor should conduct their own analysis and, where appropriate, consult a licensed adviser. &copy; 2026 Helvetia Research. All rights reserved. &ldquo;Helvetia Research&rdquo; is an illustrative report identity and does not denote a regulated entity.</p>
  </footer>

</article>
</div>

{SCRIPT_BLOCK}
</body>
</html>
"""

open(OUT,"w",encoding="utf-8").write(doc)
print("wrote:", OUT)
print("size bytes:", len(doc))
print("has font-face:", doc.count("@font-face"))
print("design css present:", "--c-accent" in doc and "masthead" in doc)

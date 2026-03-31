# modules/financials.py — Financial data with asset-type awareness

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ── Asset type detection ──────────────────────────────────────────────────────
def get_asset_type(ticker):
    t = ticker.upper()
    if t.endswith('-USD') or t in ['BTC','ETH','SOL','XRP','BNB','DOGE','ADA','AVAX']: return 'crypto'
    if t.endswith('=F'): return 'futures'
    if t.endswith('=X'): return 'forex'
    if t.startswith('^'): return 'index'
    etfs = {'SPY','QQQ','IWM','DIA','GLD','SLV','TLT','HYG','LQD','XLK','XLF','XLE',
            'XLV','XLI','XLRE','XLU','XLP','XLY','XLB','XLC','ARKK','TQQQ','SQQQ',
            'USO','UNG','VXX','EEM','EFA','VTI','VOO','AGG','BND','UVXY','SVXY',
            'IEF','SHY','EMB','GDX','GDXJ','IAU','IEMG','ACWI','VEA','VWO'}
    if t in etfs: return 'etf'
    return 'stock'

ASSET_TABS = {
    'stock':   ["Chart", "Overview", "Financials", "Valuation", "Analyst", "Ownership", "Options", "News"],
    'etf':     ["Chart", "Overview", "Holdings", "Options", "News"],
    'crypto':  ["Chart", "Market Data", "News"],
    'futures': ["Chart", "Market Data", "News"],
    'forex':   ["Chart", "Market Data", "News"],
    'index':   ["Chart", "Market Data", "News"],
}

ASSET_INDICATORS = {
    'stock':   ["RSI (14)","MACD","Volume + MA","Bollinger Bands %B","ADX + DI","OBV (On Balance Volume)","EMA Ribbon (9/21/50/200)","Stochastic %K/%D"],
    'etf':     ["RSI (14)","MACD","Volume + MA","Bollinger Band Width","EMA Ribbon (9/21/50/200)","Historical Volatility (20)"],
    'crypto':  ["RSI (14)","MACD","Volume + MA","Bollinger Bands %B","Stochastic RSI","Awesome Oscillator","VWAP Deviation","Chaikin Money Flow"],
    'futures': ["RSI (14)","MACD","ATR (14)","Volume + MA","ADX + DI","Bollinger Bands %B","EMA Ribbon (9/21/50/200)"],
    'forex':   ["RSI (14)","MACD","Stochastic %K/%D","Bollinger Bands %B","ATR (14)","Williams %R","CCI (20)"],
    'index':   ["RSI (14)","MACD","Volume + MA","Bollinger Bands %B","Historical Volatility (20)"],
}

@st.cache_data(ttl=3600)
def get_financials(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        result = {'info': info}
        try: result['income_annual'] = t.income_stmt
        except: result['income_annual'] = None
        try: result['income_qtr'] = t.quarterly_income_stmt
        except: result['income_qtr'] = None
        try: result['balance_annual'] = t.balance_sheet
        except: result['balance_annual'] = None
        try: result['balance_qtr'] = t.quarterly_balance_sheet
        except: result['balance_qtr'] = None
        try: result['cashflow_annual'] = t.cashflow
        except: result['cashflow_annual'] = None
        try: result['cashflow_qtr'] = t.quarterly_cashflow
        except: result['cashflow_qtr'] = None
        try: result['recommendations'] = t.recommendations
        except: result['recommendations'] = None
        try: result['major_holders'] = t.major_holders
        except: result['major_holders'] = None
        try: result['institutional'] = t.institutional_holders
        except: result['institutional'] = None
        try: result['earnings_dates'] = t.earnings_dates
        except: result['earnings_dates'] = None
        return result
    except Exception as e:
        return {}

@st.cache_data(ttl=300)
def get_info(ticker):
    try:
        info = yf.Ticker(ticker).info or {}
        return info
    except:
        return {}

def fmt_num(val, decimals=2, prefix="", suffix="", abbrev=True):
    if val is None or (isinstance(val, float) and np.isnan(val)): return "—"
    try:
        val = float(val)
        if abbrev:
            if abs(val)>=1e12: return f"{prefix}{val/1e12:.{decimals}f}T{suffix}"
            if abs(val)>=1e9:  return f"{prefix}{val/1e9:.{decimals}f}B{suffix}"
            if abs(val)>=1e6:  return f"{prefix}{val/1e6:.{decimals}f}M{suffix}"
            if abs(val)>=1e3:  return f"{prefix}{val/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{val:,.{decimals}f}{suffix}"
    except: return str(val)

def fmt_pct(val, decimals=2):
    if val is None: return "—"
    try: return f"{float(val)*100:.{decimals}f}%"
    except: return str(val)

def fmt_ratio(val, decimals=2):
    if val is None: return "—"
    try:
        f = float(val)
        if np.isnan(f) or f <= 0: return "—"
        return f"{f:.{decimals}f}x"
    except: return "—"

def _kv_row(label, val, C):
    return (f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
            f'border-bottom:1px solid {C["BOR"]}08;">'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:{C["TXT3"]};">{label}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;font-weight:500;color:{C["TXT2"]};">{val}</span>'
            f'</div>')

def _section_label(title, C):
    return (f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;'
            f'letter-spacing:0.1em;text-transform:uppercase;color:{C["TXT3"]};'
            f'padding:0 0 6px;border-bottom:1px solid {C["BOR"]};margin-bottom:8px;">{title}</div>')

def render_key_stats(info, C):
    if not info:
        st.info("Statistics not available.")
        return

    sections = {
        "Valuation": [
            ("Market Cap",       fmt_num(info.get('marketCap'), prefix="$")),
            ("Enterprise Value", fmt_num(info.get('enterpriseValue'), prefix="$")),
            ("P/E (TTM)",        fmt_ratio(info.get('trailingPE'))),
            ("P/E (Forward)",    fmt_ratio(info.get('forwardPE'))),
            ("PEG Ratio",        fmt_ratio(info.get('pegRatio'))),
            ("P/S (TTM)",        fmt_ratio(info.get('priceToSalesTrailing12Months'))),
            ("P/B",              fmt_ratio(info.get('priceToBook'))),
            ("EV/EBITDA",        fmt_ratio(info.get('enterpriseToEbitda'))),
            ("EV/Revenue",       fmt_ratio(info.get('enterpriseToRevenue'))),
        ],
        "Profitability": [
            ("Revenue (TTM)",    fmt_num(info.get('totalRevenue'), prefix="$")),
            ("Gross Margin",     fmt_pct(info.get('grossMargins'))),
            ("Operating Margin", fmt_pct(info.get('operatingMargins'))),
            ("Net Margin",       fmt_pct(info.get('profitMargins'))),
            ("EBITDA",           fmt_num(info.get('ebitda'), prefix="$")),
            ("ROE",              fmt_pct(info.get('returnOnEquity'))),
            ("ROA",              fmt_pct(info.get('returnOnAssets'))),
            ("Net Income",       fmt_num(info.get('netIncomeToCommon'), prefix="$")),
        ],
        "Per Share": [
            ("EPS (TTM)",        fmt_num(info.get('trailingEps'), prefix="$", abbrev=False)),
            ("EPS (Fwd)",        fmt_num(info.get('forwardEps'), prefix="$", abbrev=False)),
            ("Revenue/Share",    fmt_num(info.get('revenuePerShare'), prefix="$", abbrev=False)),
            ("Book Value",       fmt_num(info.get('bookValue'), prefix="$", abbrev=False)),
            ("Cash/Share",       fmt_num(info.get('totalCashPerShare'), prefix="$", abbrev=False)),
            ("Dividend",         fmt_num(info.get('dividendRate'), prefix="$", abbrev=False)),
            ("Div Yield",        fmt_pct(info.get('dividendYield'))),
            ("Payout Ratio",     fmt_pct(info.get('payoutRatio'))),
        ],
        "Balance Sheet": [
            ("Total Cash",       fmt_num(info.get('totalCash'), prefix="$")),
            ("Total Debt",       fmt_num(info.get('totalDebt'), prefix="$")),
            ("Net Cash",         fmt_num((info.get('totalCash') or 0)-(info.get('totalDebt') or 0), prefix="$")),
            ("Debt/Equity",      fmt_ratio((info.get('debtToEquity') or 0)/100) if info.get('debtToEquity') else "—"),
            ("Current Ratio",    fmt_ratio(info.get('currentRatio'))),
            ("Quick Ratio",      fmt_ratio(info.get('quickRatio'))),
        ],
        "Market Data": [
            ("52W High",         fmt_num(info.get('fiftyTwoWeekHigh'), prefix="$", abbrev=False)),
            ("52W Low",          fmt_num(info.get('fiftyTwoWeekLow'), prefix="$", abbrev=False)),
            ("50D MA",           fmt_num(info.get('fiftyDayAverage'), prefix="$", abbrev=False)),
            ("200D MA",          fmt_num(info.get('twoHundredDayAverage'), prefix="$", abbrev=False)),
            ("Beta",             fmt_num(info.get('beta'), decimals=2, abbrev=False)),
            ("Short %",          fmt_pct(info.get('shortPercentOfFloat'))),
            ("Shares Out",       fmt_num(info.get('sharesOutstanding'))),
            ("Avg Volume",       fmt_num(info.get('averageVolume'))),
        ],
        "Growth": [
            ("Rev Growth (YoY)", fmt_pct(info.get('revenueGrowth'))),
            ("EPS Growth",       fmt_pct(info.get('earningsGrowth'))),
            ("EPS Growth (QoQ)", fmt_pct(info.get('earningsQuarterlyGrowth'))),
        ],
    }

    # Filter out sections where all values are "—"
    valid_sections = {k: v for k, v in sections.items()
                      if any(val != "—" for _, val in v)}

    if not valid_sections:
        st.info("No statistics data available for this symbol.")
        return

    cols = st.columns(3)
    sec_items = list(valid_sections.items())
    for ci, col in enumerate(cols):
        with col:
            for i in range(ci*2, min(ci*2+2, len(sec_items))):
                sec_name, items = sec_items[i]
                valid_items = [(l,v) for l,v in items if v != "—"]
                if not valid_items: continue
                html = _section_label(sec_name, C)
                html += "".join(_kv_row(l,v,C) for l,v in valid_items)
                st.markdown(f'<div style="margin-bottom:14px;">{html}</div>', unsafe_allow_html=True)

def render_market_data(ticker, info, C):
    """For crypto, futures, forex — show relevant market data"""
    asset = get_asset_type(ticker)
    UP=C['UP']; DOWN=C['DOWN']; TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']
    BG2=C['BG2']; BOR=C['BOR']

    sections = {}

    if asset == 'crypto':
        sections["Price"] = [
            ("Current Price",   fmt_num(info.get('currentPrice') or info.get('regularMarketPrice'), prefix="$", abbrev=False)),
            ("24h High",        fmt_num(info.get('dayHigh'), prefix="$", abbrev=False)),
            ("24h Low",         fmt_num(info.get('dayLow'), prefix="$", abbrev=False)),
            ("52W High",        fmt_num(info.get('fiftyTwoWeekHigh'), prefix="$", abbrev=False)),
            ("52W Low",         fmt_num(info.get('fiftyTwoWeekLow'), prefix="$", abbrev=False)),
        ]
        sections["Market"] = [
            ("Market Cap",      fmt_num(info.get('marketCap'), prefix="$")),
            ("Volume 24h",      fmt_num(info.get('volume24Hr') or info.get('regularMarketVolume'))),
            ("Circulating Sup", fmt_num(info.get('circulatingSupply'))),
            ("Total Supply",    fmt_num(info.get('totalSupply'))),
            ("Max Supply",      fmt_num(info.get('maxSupply'))),
        ]

    elif asset in ('futures', 'index'):
        sections["Price"] = [
            ("Last Price",      fmt_num(info.get('regularMarketPrice'), abbrev=False)),
            ("Open",            fmt_num(info.get('regularMarketOpen'), abbrev=False)),
            ("Day High",        fmt_num(info.get('regularMarketDayHigh'), abbrev=False)),
            ("Day Low",         fmt_num(info.get('regularMarketDayLow'), abbrev=False)),
            ("Prev Close",      fmt_num(info.get('regularMarketPreviousClose'), abbrev=False)),
            ("52W High",        fmt_num(info.get('fiftyTwoWeekHigh'), abbrev=False)),
            ("52W Low",         fmt_num(info.get('fiftyTwoWeekLow'), abbrev=False)),
        ]
        sections["Stats"] = [
            ("Volume",          fmt_num(info.get('regularMarketVolume'))),
            ("50D MA",          fmt_num(info.get('fiftyDayAverage'), abbrev=False)),
            ("200D MA",         fmt_num(info.get('twoHundredDayAverage'), abbrev=False)),
        ]

    elif asset == 'forex':
        sections["Price"] = [
            ("Rate",            fmt_num(info.get('regularMarketPrice'), decimals=5, abbrev=False)),
            ("Open",            fmt_num(info.get('regularMarketOpen'), decimals=5, abbrev=False)),
            ("Day High",        fmt_num(info.get('regularMarketDayHigh'), decimals=5, abbrev=False)),
            ("Day Low",         fmt_num(info.get('regularMarketDayLow'), decimals=5, abbrev=False)),
            ("52W High",        fmt_num(info.get('fiftyTwoWeekHigh'), decimals=5, abbrev=False)),
            ("52W Low",         fmt_num(info.get('fiftyTwoWeekLow'), decimals=5, abbrev=False)),
        ]

    if not sections:
        # Generic fallback
        sections["Data"] = [
            ("Price",           fmt_num(info.get('regularMarketPrice') or info.get('currentPrice'), abbrev=False)),
            ("Volume",          fmt_num(info.get('regularMarketVolume'))),
            ("52W High",        fmt_num(info.get('fiftyTwoWeekHigh'), abbrev=False)),
            ("52W Low",         fmt_num(info.get('fiftyTwoWeekLow'), abbrev=False)),
        ]

    cols = st.columns(min(len(sections), 3))
    for ci, (sec_name, items) in enumerate(sections.items()):
        with cols[ci % len(cols)]:
            valid = [(l,v) for l,v in items if v != "—"]
            if not valid: continue
            html = _section_label(sec_name, C)
            html += "".join(_kv_row(l,v,C) for l,v in valid)
            st.markdown(f'<div style="background:{BG2};border:1px solid {BOR};border-radius:6px;padding:14px;margin-bottom:12px;">{html}</div>', unsafe_allow_html=True)

def render_income_statement(fin, C, period="Annual"):
    df = fin.get('income_annual') if period=="Annual" else fin.get('income_qtr')
    _render_fin_table(df, "Income Statement", C)

def render_balance_sheet(fin, C, period="Annual"):
    df = fin.get('balance_annual') if period=="Annual" else fin.get('balance_qtr')
    _render_fin_table(df, "Balance Sheet", C)

def render_cashflow(fin, C, period="Annual"):
    df = fin.get('cashflow_annual') if period=="Annual" else fin.get('cashflow_qtr')
    _render_fin_table(df, "Cash Flow Statement", C)

def _render_fin_table(df, title, C):
    if df is None or (hasattr(df,'empty') and df.empty):
        st.info(f"{title} data not available for this symbol.")
        return
    try:
        df = df.copy()
        df.columns = [str(c)[:10] for c in df.columns]
        disp = df.applymap(lambda x: fmt_num(x, prefix="$") if pd.notna(x) and x != 0 else ("—" if pd.notna(x) else "—"))
        disp.index = [str(i).replace('_',' ').title() for i in disp.index]
        st.dataframe(disp, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render {title}: {e}")

def render_dcf_model(info, C):
    TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']; BG2=C['BG2']; BOR=C['BOR']
    UP=C['UP']; DOWN=C['DOWN']; BLUE=C['BLUE']

    rev = info.get('totalRevenue') or 0
    margin = info.get('profitMargins') or 0.1
    shares = info.get('sharesOutstanding') or 1e9
    cash = info.get('totalCash') or 0
    debt = info.get('totalDebt') or 0
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0

    if rev <= 0:
        st.info("Revenue data not available for DCF — this model applies to stocks with reported revenue.")
        return

    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:12px;">DCF — Discounted Cash Flow Model</div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        rev_growth = st.slider("Revenue Growth Y1-5 %", 0.0, 50.0, 10.0, 0.5, key="dcf_g1") / 100
        term_growth = st.slider("Terminal Growth %", 0.0, 5.0, 2.5, 0.1, key="dcf_tg") / 100
    with c2:
        wacc = st.slider("WACC %", 5.0, 20.0, 10.0, 0.5, key="dcf_wacc") / 100
        margin_t = st.slider("FCF Margin %", 0.0, 40.0, float(margin*100), 0.5, key="dcf_margin") / 100
    with c3:
        years = st.selectbox("Projection Years", [5, 7, 10], index=1, key="dcf_years")

    fcfs = []; rev_p = rev
    for y in range(1, years+1):
        g = max(rev_growth*(1-y/(years*2)), term_growth)
        rev_p *= (1+g)
        fcfs.append(rev_p * margin_t)

    pv_fcfs = [f/(1+wacc)**y for y,f in enumerate(fcfs,1)]
    tv = fcfs[-1]*(1+term_growth)/(wacc-term_growth) if wacc>term_growth else 0
    pv_tv = tv/(1+wacc)**years
    eq = sum(pv_fcfs)+pv_tv+cash-debt
    intrinsic = eq/shares if shares>0 else 0
    upside = (intrinsic-current_price)/current_price*100 if current_price>0 else 0
    vc = UP if upside>0 else DOWN

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Intrinsic Value", f"${intrinsic:,.2f}")
    m2.metric("Current Price", f"${current_price:,.2f}")
    m3.metric("Upside/Downside", f"{upside:+.1f}%")
    m4.metric("PV of FCFs", fmt_num(sum(pv_fcfs), prefix="$"))

    st.markdown(
        f'<div style="background:{BG2};border:1px solid {BOR};border-radius:6px;padding:14px;margin-top:8px;">'
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:6px;">Summary</div>'
        f'<div style="display:flex;gap:20px;flex-wrap:wrap;font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{TXT2};">'
        f'<span>PV FCFs: <b style="color:{TXT1}">{fmt_num(sum(pv_fcfs),prefix="$")}</b></span>'
        f'<span>PV Terminal: <b style="color:{TXT1}">{fmt_num(pv_tv,prefix="$")}</b></span>'
        f'<span>Net Cash: <b style="color:{TXT1}">{fmt_num(cash-debt,prefix="$")}</b></span>'
        f'<span>Intrinsic/Share: <b style="color:{vc}">${intrinsic:,.2f}</b></span>'
        f'<span>Implied Upside: <b style="color:{vc}">{upside:+.1f}%</b></span>'
        f'</div>'
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:{TXT3};margin-top:6px;">Simplified model. For reference only.</div>'
        f'</div>',
        unsafe_allow_html=True
    )

def render_comps(ticker, info, C):
    TXT3=C['TXT3']
    sector = info.get('sector','')
    PEERS = {
        'Technology':          ['AAPL','MSFT','NVDA','GOOGL','META','AMD','INTC','CSCO','ORCL','IBM'],
        'Financial Services':  ['JPM','BAC','WFC','GS','MS','C','BLK','SCHW','AXP','USB'],
        'Healthcare':          ['JNJ','UNH','PFE','ABBV','MRK','TMO','ABT','DHR','AMGN','GILD'],
        'Consumer Cyclical':   ['AMZN','TSLA','HD','MCD','NKE','LOW','SBUX','TGT','GM','F'],
        'Communication Services':['GOOGL','META','NFLX','DIS','CMCSA','T','VZ','TMUS'],
        'Energy':              ['XOM','CVX','COP','SLB','EOG','PSX','MPC','VLO','OXY'],
        'Industrials':         ['CAT','DE','HON','UPS','BA','GE','MMM','RTX','LMT'],
        'Consumer Defensive':  ['WMT','PG','KO','PEP','COST','PM','MO','CL'],
        'Basic Materials':     ['LIN','APD','FCX','NEM','NUE','CF','ALB'],
        'Real Estate':         ['AMT','PLD','CCI','EQIX','SPG','O','DLR','WELL'],
        'Utilities':           ['NEE','DUK','SO','AEP','SRE','EXC','XEL'],
    }
    peers = [p for p in PEERS.get(sector, []) if p != ticker][:7]
    if not peers:
        st.info("No comparable companies data available.")
        return

    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:10px;">Comparable Companies — {sector}</div>', unsafe_allow_html=True)
    rows = []
    for t in [ticker]+peers:
        try:
            inf = yf.Ticker(t).fast_info
            full = yf.Ticker(t).info
            rows.append({
                'Ticker': t, 'Name': (full.get('shortName','') or '')[:20],
                'Mkt Cap': fmt_num(full.get('marketCap'), prefix="$"),
                'P/E': fmt_ratio(full.get('trailingPE')),
                'Fwd P/E': fmt_ratio(full.get('forwardPE')),
                'EV/EBITDA': fmt_ratio(full.get('enterpriseToEbitda')),
                'Rev Growth': fmt_pct(full.get('revenueGrowth')),
                'Net Margin': fmt_pct(full.get('profitMargins')),
                'ROE': fmt_pct(full.get('returnOnEquity')),
            })
        except: pass
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def render_analyst_data(ticker, info, C):
    UP=C['UP']; DOWN=C['DOWN']; AMBER=C['AMBER']
    TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']; BG2=C['BG2']; BOR=C['BOR']

    target = info.get('targetMeanPrice')
    current = info.get('currentPrice') or info.get('regularMarketPrice') or 0
    rec = (info.get('recommendationKey') or '').upper()
    n_analysts = info.get('numberOfAnalystOpinions') or 0
    target_high = info.get('targetHighPrice')
    target_low = info.get('targetLowPrice')

    if not target and not rec:
        st.info("No analyst coverage data available for this symbol.")
        return

    upside = ((target-current)/current*100) if target and current else 0
    rc = UP if rec in ['BUY','STRONG_BUY'] else DOWN if rec in ['SELL','STRONG_SELL'] else AMBER

    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Consensus", rec.replace('_',' ') or "—")
    m2.metric("# Analysts", str(n_analysts) if n_analysts else "—")
    m3.metric("Mean Target", f"${target:,.2f}" if target else "—")
    m4.metric("Implied Upside", f"{upside:+.1f}%" if target else "—")
    m5.metric("Range", f"${target_low:,.0f} — ${target_high:,.0f}" if target_low and target_high else "—")

def render_ownership(fin, C):
    TXT3=C['TXT3']
    inst = fin.get('institutional')
    major = fin.get('major_holders')
    has_data = False

    if inst is not None and not inst.empty:
        has_data = True
        st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:8px;">Top Institutional Holders</div>', unsafe_allow_html=True)
        try:
            d = inst.copy()
            if 'Date Reported' in d.columns:
                d['Date Reported'] = pd.to_datetime(d['Date Reported']).dt.strftime('%Y-%m-%d')
            st.dataframe(d.head(15), use_container_width=True, hide_index=True)
        except: st.dataframe(inst.head(15), use_container_width=True, hide_index=True)

    if major is not None and not major.empty:
        has_data = True
        st.markdown(f'<div style="height:10px"></div><div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:8px;">Major Holders</div>', unsafe_allow_html=True)
        st.dataframe(major, use_container_width=True, hide_index=True)

    if not has_data:
        st.info("Ownership data not available for this symbol.")

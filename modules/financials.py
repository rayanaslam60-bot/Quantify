# modules/financials.py — Financial statements, fundamentals, valuation models

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

@st.cache_data(ttl=3600)
def get_financials(ticker):
    """Fetch all financial statement data"""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        return {
            'info':          info,
            'income_annual': t.income_stmt,
            'income_qtr':    t.quarterly_income_stmt,
            'balance_annual':t.balance_sheet,
            'balance_qtr':   t.quarterly_balance_sheet,
            'cashflow_annual':t.cashflow,
            'cashflow_qtr':   t.quarterly_cashflow,
            'earnings':       t.earnings_dates,
            'recommendations':t.recommendations,
            'major_holders':  t.major_holders,
            'institutional':  t.institutional_holders,
            'insider':        t.insider_transactions,
        }
    except Exception as e:
        return {}

@st.cache_data(ttl=3600)
def get_info(ticker):
    try:
        return yf.Ticker(ticker).info or {}
    except:
        return {}

def fmt_num(val, decimals=2, prefix="", suffix="", abbrev=True):
    """Format large numbers with B/M/K abbreviations"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    try:
        val = float(val)
        if abbrev:
            if abs(val) >= 1e12: return f"{prefix}{val/1e12:.{decimals}f}T{suffix}"
            if abs(val) >= 1e9:  return f"{prefix}{val/1e9:.{decimals}f}B{suffix}"
            if abs(val) >= 1e6:  return f"{prefix}{val/1e6:.{decimals}f}M{suffix}"
            if abs(val) >= 1e3:  return f"{prefix}{val/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{val:,.{decimals}f}{suffix}"
    except:
        return str(val)

def fmt_pct(val, decimals=2):
    if val is None: return "—"
    try: return f"{float(val)*100:.{decimals}f}%"
    except: return str(val)

def fmt_ratio(val, decimals=2):
    if val is None: return "—"
    try: return f"{float(val):.{decimals}f}x"
    except: return str(val)

def render_key_stats(info, C):
    """Render key statistics panel"""
    UP=C['UP']; DOWN=C['DOWN']; TXT1=C['TXT1']; TXT2=C['TXT2']
    TXT3=C['TXT3']; BG2=C['BG2']; BOR=C['BOR']; BG0=C['BG0']

    sections = {
        "Valuation": [
            ("Market Cap",      fmt_num(info.get('marketCap'), prefix="$")),
            ("Enterprise Value",fmt_num(info.get('enterpriseValue'), prefix="$")),
            ("P/E (TTM)",       fmt_ratio(info.get('trailingPE'))),
            ("P/E (Forward)",   fmt_ratio(info.get('forwardPE'))),
            ("PEG Ratio",       fmt_ratio(info.get('pegRatio'))),
            ("P/S (TTM)",       fmt_ratio(info.get('priceToSalesTrailing12Months'))),
            ("P/B",             fmt_ratio(info.get('priceToBook'))),
            ("EV/EBITDA",       fmt_ratio(info.get('enterpriseToEbitda'))),
            ("EV/Revenue",      fmt_ratio(info.get('enterpriseToRevenue'))),
        ],
        "Profitability": [
            ("Revenue (TTM)",   fmt_num(info.get('totalRevenue'), prefix="$")),
            ("Gross Margin",    fmt_pct(info.get('grossMargins'))),
            ("Operating Margin",fmt_pct(info.get('operatingMargins'))),
            ("Net Margin",      fmt_pct(info.get('profitMargins'))),
            ("EBITDA",          fmt_num(info.get('ebitda'), prefix="$")),
            ("Return on Equity",fmt_pct(info.get('returnOnEquity'))),
            ("Return on Assets",fmt_pct(info.get('returnOnAssets'))),
            ("Earnings (TTM)",  fmt_num(info.get('netIncomeToCommon'), prefix="$")),
        ],
        "Per Share": [
            ("EPS (TTM)",       fmt_num(info.get('trailingEps'), prefix="$", abbrev=False)),
            ("EPS (Forward)",   fmt_num(info.get('forwardEps'), prefix="$", abbrev=False)),
            ("Revenue/Share",   fmt_num(info.get('revenuePerShare'), prefix="$", abbrev=False)),
            ("Book Value/Share",fmt_num(info.get('bookValue'), prefix="$", abbrev=False)),
            ("Cash/Share",      fmt_num(info.get('totalCashPerShare'), prefix="$", abbrev=False)),
            ("Dividend/Share",  fmt_num(info.get('dividendRate'), prefix="$", abbrev=False)),
            ("Dividend Yield",  fmt_pct(info.get('dividendYield'))),
            ("Payout Ratio",    fmt_pct(info.get('payoutRatio'))),
        ],
        "Balance Sheet": [
            ("Total Cash",      fmt_num(info.get('totalCash'), prefix="$")),
            ("Total Debt",      fmt_num(info.get('totalDebt'), prefix="$")),
            ("Net Cash",        fmt_num((info.get('totalCash',0) or 0) - (info.get('totalDebt',0) or 0), prefix="$")),
            ("Debt/Equity",     fmt_ratio(info.get('debtToEquity') and info.get('debtToEquity')/100)),
            ("Current Ratio",   fmt_ratio(info.get('currentRatio'))),
            ("Quick Ratio",     fmt_ratio(info.get('quickRatio'))),
            ("Total Assets",    fmt_num(info.get('totalAssets'), prefix="$")),
        ],
        "Growth": [
            ("Revenue Growth",  fmt_pct(info.get('revenueGrowth'))),
            ("Earnings Growth", fmt_pct(info.get('earningsGrowth'))),
            ("EPS Growth (QoQ)",fmt_pct(info.get('earningsQuarterlyGrowth'))),
        ],
        "Market Data": [
            ("52W High",        fmt_num(info.get('fiftyTwoWeekHigh'), prefix="$", abbrev=False)),
            ("52W Low",         fmt_num(info.get('fiftyTwoWeekLow'), prefix="$", abbrev=False)),
            ("50D Avg",         fmt_num(info.get('fiftyDayAverage'), prefix="$", abbrev=False)),
            ("200D Avg",        fmt_num(info.get('twoHundredDayAverage'), prefix="$", abbrev=False)),
            ("Beta",            fmt_num(info.get('beta'), decimals=2, abbrev=False)),
            ("Short Float",     fmt_pct(info.get('shortPercentOfFloat'))),
            ("Shares Out",      fmt_num(info.get('sharesOutstanding'))),
            ("Float",           fmt_num(info.get('floatShares'))),
            ("Avg Volume",      fmt_num(info.get('averageVolume'))),
        ],
    }

    cols = st.columns(3)
    sec_list = list(sections.items())
    for col_idx, col in enumerate(cols):
        with col:
            for i in range(col_idx * 2, min(col_idx * 2 + 2, len(sec_list))):
                sec_name, items = sec_list[i]
                st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};padding:0 0 6px;border-bottom:1px solid {BOR};margin-bottom:8px;">{sec_name}</div>', unsafe_allow_html=True)
                for label, val in items:
                    st.markdown(f'''<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {BOR}08;">
                        <span style="font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:{TXT3};">{label}</span>
                        <span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;font-weight:500;color:{TXT2};">{val}</span>
                    </div>''', unsafe_allow_html=True)
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

def render_income_statement(fin, C, period="Annual"):
    """Render income statement"""
    df = fin.get('income_annual') if period == "Annual" else fin.get('income_qtr')
    if df is None or df.empty:
        st.info("No income statement data available.")
        return
    _render_financial_table(df, "Income Statement", C)

def render_balance_sheet(fin, C, period="Annual"):
    df = fin.get('balance_annual') if period == "Annual" else fin.get('balance_qtr')
    if df is None or df.empty:
        st.info("No balance sheet data available.")
        return
    _render_financial_table(df, "Balance Sheet", C)

def render_cashflow(fin, C, period="Annual"):
    df = fin.get('cashflow_annual') if period == "Annual" else fin.get('cashflow_qtr')
    if df is None or df.empty:
        st.info("No cash flow data available.")
        return
    _render_financial_table(df, "Cash Flow Statement", C)

def _render_financial_table(df, title, C):
    TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']
    BG2=C['BG2']; BOR=C['BOR']; UP=C['UP']; DOWN=C['DOWN']
    try:
        df = df.copy()
        # Format columns as dates
        df.columns = [str(col)[:10] for col in df.columns]
        # Format values
        display_df = df.copy()
        for col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: fmt_num(x, prefix="$") if pd.notna(x) else "—"
            )
        display_df.index = [str(i).replace('_',' ').title() for i in display_df.index]
        st.dataframe(display_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering {title}: {e}")

def render_dcf_model(info, C):
    """Simplified DCF model"""
    TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']
    BG2=C['BG2']; BOR=C['BOR']; BLUE=C['BLUE']
    UP=C['UP']; DOWN=C['DOWN']; AMBER=C['AMBER']

    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:12px;">DCF — Discounted Cash Flow Model</div>', unsafe_allow_html=True)

    rev = info.get('totalRevenue', 0) or 0
    margin = info.get('profitMargins', 0.1) or 0.1
    shares = info.get('sharesOutstanding', 1e9) or 1e9
    cash = info.get('totalCash', 0) or 0
    debt = info.get('totalDebt', 0) or 0
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0)) or 0

    c1, c2, c3 = st.columns(3)
    with c1:
        rev_growth = st.slider("Revenue Growth Y1-5 %", 0.0, 50.0, 10.0, 0.5, key="dcf_g1") / 100
        term_growth = st.slider("Terminal Growth %", 0.0, 5.0, 2.5, 0.1, key="dcf_tg") / 100
    with c2:
        wacc = st.slider("WACC (Discount Rate) %", 5.0, 20.0, 10.0, 0.5, key="dcf_wacc") / 100
        margin_target = st.slider("Target FCF Margin %", 0.0, 40.0, float(margin*100), 0.5, key="dcf_margin") / 100
    with c3:
        years = st.selectbox("Projection Years", [5, 7, 10], index=1, key="dcf_years")

    if rev <= 0:
        st.warning("Revenue data not available for DCF model.")
        return

    # Project FCF
    fcf_base = rev * margin_target
    fcfs = []
    rev_proj = rev
    for y in range(1, years + 1):
        growth = rev_growth * (1 - y / (years * 2))  # declining growth
        rev_proj *= (1 + max(growth, term_growth))
        fcf = rev_proj * margin_target
        fcfs.append(fcf)

    # PV of FCFs
    pv_fcfs = [fcf / (1 + wacc)**y for y, fcf in enumerate(fcfs, 1)]

    # Terminal value
    terminal_fcf = fcfs[-1] * (1 + term_growth)
    terminal_val = terminal_fcf / (wacc - term_growth) if wacc > term_growth else 0
    pv_terminal = terminal_val / (1 + wacc)**years

    # Equity value
    total_pv = sum(pv_fcfs) + pv_terminal
    equity_val = total_pv + cash - debt
    intrinsic = equity_val / shares if shares > 0 else 0

    upside = ((intrinsic - current_price) / current_price * 100) if current_price > 0 else 0
    val_color = UP if upside > 0 else DOWN

    # Display results
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Intrinsic Value", f"${intrinsic:,.2f}")
    r2.metric("Current Price", f"${current_price:,.2f}")
    r3.metric("Upside/Downside", f"{upside:+.1f}%")
    r4.metric("PV of FCFs", fmt_num(sum(pv_fcfs), prefix="$"))

    st.markdown(f"""<div style="background:{BG2};border:1px solid {BOR};border-radius:6px;padding:14px 16px;margin-top:8px;">
        <div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:8px;">DCF Summary</div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{TXT2};">
            <span>PV of FCFs: <b style="color:{TXT1}">{fmt_num(sum(pv_fcfs), prefix="$")}</b></span>
            <span>PV Terminal: <b style="color:{TXT1}">{fmt_num(pv_terminal, prefix="$")}</b></span>
            <span>Net Cash: <b style="color:{TXT1}">{fmt_num(cash-debt, prefix="$")}</b></span>
            <span>Equity Value: <b style="color:{TXT1}">{fmt_num(equity_val, prefix="$")}</b></span>
            <span>Intrinsic/Share: <b style="color:{val_color}">${intrinsic:,.2f}</b></span>
            <span>Implied Upside: <b style="color:{val_color}">{upside:+.1f}%</b></span>
        </div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:{TXT3};margin-top:8px;">
            Note: Simplified DCF. Uses revenue × FCF margin projection. For reference only.
        </div>
    </div>""", unsafe_allow_html=True)

def render_comps(ticker, info, C):
    """Comparable company analysis"""
    TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']
    BG2=C['BG2']; BOR=C['BOR']

    sector = info.get('sector','')
    # Peer mapping by sector
    PEERS = {
        'Technology': ['AAPL','MSFT','GOOGL','META','NVDA','AMD','INTC','CSCO','ORCL','IBM'],
        'Financial Services': ['JPM','BAC','WFC','GS','MS','C','BLK','SCHW','AXP','USB'],
        'Healthcare': ['JNJ','UNH','PFE','ABBV','MRK','TMO','ABT','DHR','AMGN','GILD'],
        'Consumer Cyclical': ['AMZN','TSLA','HD','MCD','NKE','LOW','SBUX','TGT','GM','F'],
        'Communication Services': ['GOOGL','META','NFLX','DIS','CMCSA','T','VZ','TMUS','EA','TTWO'],
        'Energy': ['XOM','CVX','COP','SLB','EOG','PXD','PSX','MPC','VLO','OXY'],
        'Industrials': ['CAT','DE','HON','UPS','BA','GE','MMM','RTX','LMT','NOC'],
        'Consumer Defensive': ['WMT','PG','KO','PEP','COST','PM','MO','CL','KHC','GIS'],
        'Basic Materials': ['LIN','APD','FCX','NEM','NUE','CF','MOS','ALB','EMN','PPG'],
        'Real Estate': ['AMT','PLD','CCI','EQIX','SPG','O','DLR','WELL','PSA','EQR'],
        'Utilities': ['NEE','DUK','SO','AEP','SRE','EXC','XEL','WEC','ES','CMS'],
    }
    peers = PEERS.get(sector, ['SPY','QQQ','DIA','IWM','VTI'])
    # Remove current ticker from peers
    peers = [p for p in peers if p != ticker][:8]

    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:10px;">Comparable Companies — {sector}</div>', unsafe_allow_html=True)

    rows = []
    all_tickers = [ticker] + peers
    for t in all_tickers:
        try:
            inf = yf.Ticker(t).info
            rows.append({
                'Ticker': t,
                'Name': (inf.get('shortName','') or '')[:20],
                'Mkt Cap': fmt_num(inf.get('marketCap'), prefix="$"),
                'P/E': fmt_ratio(inf.get('trailingPE')),
                'Fwd P/E': fmt_ratio(inf.get('forwardPE')),
                'EV/EBITDA': fmt_ratio(inf.get('enterpriseToEbitda')),
                'Rev Growth': fmt_pct(inf.get('revenueGrowth')),
                'Margin': fmt_pct(inf.get('profitMargins')),
                'ROE': fmt_pct(inf.get('returnOnEquity')),
            })
        except:
            pass

    if rows:
        df_comps = pd.DataFrame(rows)
        st.dataframe(df_comps, use_container_width=True, hide_index=True)

def render_analyst_data(ticker, info, C):
    """Analyst ratings and price targets"""
    TXT1=C['TXT1']; TXT2=C['TXT2']; TXT3=C['TXT3']
    BG2=C['BG2']; BOR=C['BOR']; UP=C['UP']; DOWN=C['DOWN']; AMBER=C['AMBER']

    target = info.get('targetMeanPrice')
    current = info.get('currentPrice', info.get('regularMarketPrice', 0))
    rec = info.get('recommendationKey','').upper()
    n_analysts = info.get('numberOfAnalystOpinions', 0)
    target_high = info.get('targetHighPrice')
    target_low = info.get('targetLowPrice')
    target_med = info.get('targetMedianPrice')

    if not target:
        st.info("No analyst data available for this symbol.")
        return

    upside = ((target - current) / current * 100) if current else 0
    rec_color = UP if rec in ['BUY','STRONG_BUY'] else DOWN if rec in ['SELL','STRONG_SELL'] else AMBER

    r1,r2,r3,r4,r5 = st.columns(5)
    r1.metric("Consensus", rec.replace('_',' '))
    r2.metric("Analysts", str(n_analysts))
    r3.metric("Price Target", f"${target:,.2f}" if target else "—")
    r4.metric("Implied Upside", f"{upside:+.1f}%" if target else "—")
    r5.metric("Target Range", f"${target_low:,.0f}–${target_high:,.0f}" if target_low and target_high else "—")

def render_ownership(fin, C):
    """Ownership data"""
    TXT3=C['TXT3']; BOR=C['BOR']

    inst = fin.get('institutional')
    major = fin.get('major_holders')
    insider = fin.get('insider')

    if inst is not None and not inst.empty:
        st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:8px;">Top Institutional Holders</div>', unsafe_allow_html=True)
        try:
            disp = inst.copy()
            if 'Date Reported' in disp.columns:
                disp['Date Reported'] = pd.to_datetime(disp['Date Reported']).dt.strftime('%Y-%m-%d')
            st.dataframe(disp.head(15), use_container_width=True, hide_index=True)
        except:
            st.dataframe(inst.head(15), use_container_width=True, hide_index=True)

    if major is not None and not major.empty:
        st.markdown(f'<div style="height:12px"></div><div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{TXT3};margin-bottom:8px;">Major Holders</div>', unsafe_allow_html=True)
        st.dataframe(major, use_container_width=True, hide_index=True)

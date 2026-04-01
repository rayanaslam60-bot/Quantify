# modules/market_data.py — Markets, Macro, Screener, Calendar data

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import urllib.request, json

NY = pytz.timezone('America/New_York')

# ── MARKET OVERVIEW DATA ─────────────────────────────────────────────────────

MARKET_GROUPS = {
    "US Indices": [
        ("S&P 500","^GSPC"),("Nasdaq 100","^NDX"),("Dow Jones","^DJI"),
        ("Russell 2000","^RUT"),("VIX","^VIX"),("S&P 400 Mid","^MID"),
    ],
    "Global Indices": [
        ("FTSE 100","^FTSE"),("DAX","^DAX"),("Nikkei 225","^N225"),
        ("Hang Seng","^HSI"),("CAC 40","^FCHI"),("ASX 200","^AXJO"),
        ("Euro Stoxx 50","^STOXX50E"),("MSCI EM","EEM"),
    ],
    "US Sectors": [
        ("Technology","XLK"),("Financials","XLF"),("Healthcare","XLV"),
        ("Energy","XLE"),("Industrials","XLI"),("Consumer Disc","XLY"),
        ("Consumer Stap","XLP"),("Real Estate","XLRE"),("Utilities","XLU"),
        ("Materials","XLB"),("Comm Services","XLC"),
    ],
    "Fixed Income": [
        ("10Y Treasury","^TNX"),("2Y Treasury","^IRX"),("30Y Treasury","^TYX"),
        ("TLT 20Y ETF","TLT"),("HY Bond","HYG"),("IG Bond","LQD"),
        ("TIPS","TIP"),("Short Bond","SHY"),
    ],
    "FX": [
        ("EUR/USD","EURUSD=X"),("GBP/USD","GBPUSD=X"),("USD/JPY","USDJPY=X"),
        ("AUD/USD","AUDUSD=X"),("USD/CAD","USDCAD=X"),("USD/CHF","USDCHF=X"),
        ("DXY","DX-Y.NYB"),("USD/CNY","USDCNY=X"),
    ],
    "Commodities": [
        ("Gold","GC=F"),("Silver","SI=F"),("Crude Oil","CL=F"),
        ("Nat Gas","NG=F"),("Copper","HG=F"),("Wheat","ZW=F"),
        ("Corn","ZC=F"),("Soybeans","ZS=F"),
    ],
    "Crypto": [
        ("Bitcoin","BTC-USD"),("Ethereum","ETH-USD"),("Solana","SOL-USD"),
        ("XRP","XRP-USD"),("BNB","BNB-USD"),("Dogecoin","DOGE-USD"),
    ],
    "Futures": [
        ("S&P Futures","ES=F"),("Nasdaq Futures","NQ=F"),("Dow Futures","YM=F"),
        ("Gold Futures","GC=F"),("Oil Futures","CL=F"),("VIX Futures","VX=F"),
    ],
}

@st.cache_data(ttl=60)
def get_market_snapshot(tickers):
    """Fetch quick price data for multiple tickers"""
    results = {}
    for name, ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            p = getattr(fi, 'last_price', None)
            prev = getattr(fi, 'previous_close', None)
            if p and prev:
                chg = p - prev
                pct = chg / prev * 100
                results[ticker] = {'name': name, 'price': p, 'change': chg, 'pct': pct}
            else:
                results[ticker] = {'name': name, 'price': None, 'change': 0, 'pct': 0}
        except:
            results[ticker] = {'name': name, 'price': None, 'change': 0, 'pct': 0}
    return results

# ── SCREENER ─────────────────────────────────────────────────────────────────

SCREENER_UNIVERSE = {
    "Large Cap US": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK.B","JPM","V",
                     "UNH","MA","XOM","JNJ","PG","HD","CVX","MRK","ABBV","LLY",
                     "BAC","PFE","KO","PEP","COST","TMO","WMT","AVGO","DIS","CSCO"],
    "Tech Growth":  ["NVDA","AMD","MSFT","AAPL","GOOGL","META","AMZN","TSLA","NFLX","SNOW",
                     "CRWD","PANW","ZS","DDOG","MDB","NET","COIN","PLTR","MSTR","ARM"],
    "Financials":   ["JPM","BAC","WFC","GS","MS","C","BLK","SCHW","AXP","USB","PNC","TFC"],
    "Healthcare":   ["UNH","JNJ","PFE","ABBV","MRK","LLY","TMO","ABT","DHR","AMGN","GILD"],
    "Energy":       ["XOM","CVX","COP","SLB","EOG","PXD","PSX","MPC","VLO","OXY","HES"],
    "ETFs":         ["SPY","QQQ","IWM","DIA","GLD","SLV","TLT","HYG","XLK","XLF","XLE",
                     "XLV","ARKK","TQQQ","VTI","VOO","EEM","EFA","AGG"],
}

@st.cache_data(ttl=300)
def run_screener(tickers, filters=None):
    """Fetch fundamentals for screener universe"""
    rows = []
    for t in tickers[:30]:  # limit for performance
        try:
            info = yf.Ticker(t).info
            fi = yf.Ticker(t).fast_info
            p = getattr(fi, 'last_price', None)
            prev = getattr(fi, 'previous_close', None)
            pct = (p-prev)/prev*100 if p and prev else 0
            rows.append({
                'Ticker': t,
                'Name': (info.get('shortName','') or '')[:18],
                'Price': round(p, 2) if p else None,
                'Chg %': round(pct, 2),
                'Mkt Cap': info.get('marketCap'),
                'P/E': info.get('trailingPE'),
                'Fwd P/E': info.get('forwardPE'),
                'EV/EBITDA': info.get('enterpriseToEbitda'),
                'Rev Growth': info.get('revenueGrowth'),
                'Net Margin': info.get('profitMargins'),
                'ROE': info.get('returnOnEquity'),
                'Beta': info.get('beta'),
                'Volume': info.get('regularMarketVolume'),
                'Avg Vol': info.get('averageVolume'),
                'Div Yield': info.get('dividendYield'),
            })
        except: pass
    return pd.DataFrame(rows)

# ── CALENDAR DATA ─────────────────────────────────────────────────────────────

MACRO_EVENTS = [
    # (name, country, category, importance)
    ("Non-Farm Payrolls", "US", "Employment", "HIGH"),
    ("CPI YoY", "US", "Inflation", "HIGH"),
    ("Fed Interest Rate Decision", "US", "Central Bank", "HIGH"),
    ("GDP Growth Rate QoQ", "US", "GDP", "HIGH"),
    ("FOMC Meeting Minutes", "US", "Central Bank", "HIGH"),
    ("PPI MoM", "US", "Inflation", "MEDIUM"),
    ("Retail Sales MoM", "US", "Consumer", "MEDIUM"),
    ("Unemployment Rate", "US", "Employment", "HIGH"),
    ("ISM Manufacturing PMI", "US", "PMI", "MEDIUM"),
    ("ISM Services PMI", "US", "PMI", "MEDIUM"),
    ("Consumer Confidence", "US", "Consumer", "MEDIUM"),
    ("Building Permits", "US", "Housing", "LOW"),
    ("Existing Home Sales", "US", "Housing", "LOW"),
    ("Trade Balance", "US", "Trade", "MEDIUM"),
    ("Industrial Production MoM", "US", "Industry", "MEDIUM"),
    ("ECB Interest Rate Decision", "EU", "Central Bank", "HIGH"),
    ("BOE Interest Rate Decision", "UK", "Central Bank", "HIGH"),
    ("BOJ Interest Rate Decision", "JP", "Central Bank", "HIGH"),
    ("EU CPI Flash Estimate YoY", "EU", "Inflation", "HIGH"),
    ("UK CPI YoY", "UK", "Inflation", "HIGH"),
]

@st.cache_data(ttl=3600)
def get_earnings_calendar(tickers):
    """Get upcoming earnings for a list of tickers"""
    events = []
    for t in tickers[:20]:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            next_date = info.get('earningsTimestamp') or info.get('earningsDate')
            if next_date:
                if isinstance(next_date, (list, tuple)):
                    next_date = next_date[0]
                try:
                    if isinstance(next_date, (int, float)):
                        dt = datetime.fromtimestamp(next_date)
                    else:
                        dt = pd.to_datetime(next_date)
                    events.append({
                        'Ticker': t,
                        'Company': (info.get('shortName','') or '')[:20],
                        'Date': dt.strftime('%Y-%m-%d'),
                        'EPS Est': info.get('epsForward'),
                        'Rev Est': info.get('revenueEstimate') or info.get('totalRevenue'),
                    })
                except: pass
        except: pass
    return pd.DataFrame(events) if events else pd.DataFrame()

# ── MACRO DATA ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_yield_curve():
    """Fetch US Treasury yield curve data"""
    maturities = {
        "1M": "^IRX", "3M": "^IRX", "6M": "^IRX",
        "2Y": "^IRX", "5Y": "^FVX", "10Y": "^TNX", "30Y": "^TYX"
    }
    # Use fixed income ETF proxies for curve shape
    etf_proxies = {"1Y":("SHY","1"),"2Y":("SHY","2"),"5Y":("IEF","5"),"10Y":("TLT","10"),"30Y":("TLT","30")}
    yields = {}
    for label, ticker in [("3M","^IRX"),("5Y","^FVX"),("10Y","^TNX"),("30Y","^TYX")]:
        try:
            p = yf.Ticker(ticker).fast_info.last_price
            if p: yields[label] = round(p, 3)
        except: pass
    return yields

@st.cache_data(ttl=3600)
def get_macro_indicators():
    """Fetch macro indicator proxies via ETFs and indices"""
    indicators = {
        "S&P 500":    ("^GSPC","Equities"),
        "VIX":        ("^VIX","Volatility"),
        "10Y Yield":  ("^TNX","Rates"),
        "2Y Yield":   ("^IRX","Rates"),
        "DXY":        ("DX-Y.NYB","FX"),
        "Gold":       ("GC=F","Commodities"),
        "Oil":        ("CL=F","Commodities"),
        "HY Spread":  ("HYG","Credit"),
        "IG Credit":  ("LQD","Credit"),
        "Copper":     ("HG=F","Commodities"),
        "Breakevens": ("TIP","Inflation"),
    }
    results = {}
    for name, (ticker, cat) in indicators.items():
        try:
            fi = yf.Ticker(ticker).fast_info
            p = fi.last_price; prev = fi.previous_close
            if p and prev:
                results[name] = {'ticker':ticker,'category':cat,'price':p,
                                  'pct':(p-prev)/prev*100}
        except: pass
    return results

# ── CORPORATE ACTIONS ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_corporate_actions(ticker):
    """Fetch dividends, splits, and other corporate actions"""
    try:
        tk = yf.Ticker(ticker)
        result = {}
        try:
            divs = tk.dividends
            result['dividends'] = divs.reset_index() if not divs.empty else pd.DataFrame()
        except: result['dividends'] = pd.DataFrame()
        try:
            splits = tk.splits
            result['splits'] = splits.reset_index() if not splits.empty else pd.DataFrame()
        except: result['splits'] = pd.DataFrame()
        info = tk.info
        result['info'] = {
            'dividend_rate':  info.get('dividendRate'),
            'dividend_yield': info.get('dividendYield'),
            'ex_date':        info.get('exDividendDate'),
            'payout_ratio':   info.get('payoutRatio'),
            'five_year_avg_yield': info.get('fiveYearAvgDividendYield'),
        }
        return result
    except: return {}

# ── INSIDER ACTIVITY ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_insider_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        insider = tk.insider_transactions
        if insider is not None and not insider.empty:
            return insider
        return pd.DataFrame()
    except: return pd.DataFrame()

# ── ESTIMATES ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_estimates(ticker):
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        result = {
            'eps_current_yr':   info.get('epsCurrentYear'),
            'eps_forward':      info.get('epsForward'),
            'revenue_estimate': info.get('revenueEstimate'),
            'earnings_date':    info.get('earningsTimestamp'),
            'earnings_avg':     info.get('earningsEstimate'),
            'earnings_low':     info.get('earningsEstimateLow'),
            'earnings_high':    info.get('earningsEstimateHigh'),
            'rev_est_avg':      info.get('revenueAverage'),
            'rev_est_low':      info.get('revenueLow'),
            'rev_est_high':     info.get('revenueHigh'),
            'growth_est':       info.get('earningsGrowth'),
            'analyst_count':    info.get('numberOfAnalystOpinions'),
            'price_target':     info.get('targetMeanPrice'),
            'target_high':      info.get('targetHighPrice'),
            'target_low':       info.get('targetLowPrice'),
            'rec_key':          info.get('recommendationKey'),
        }
        # Earnings history
        try:
            hist = tk.earnings_history
            result['history'] = hist
        except: result['history'] = None
        # Next earnings dates
        try:
            dates = tk.earnings_dates
            result['earnings_dates'] = dates
        except: result['earnings_dates'] = None
        return result
    except: return {}

# ── FILINGS ──────────────────────────────────────────────────────────────────

def get_sec_filings_url(ticker):
    """Returns SEC EDGAR link for a ticker"""
    return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type=10-K&dateb=&owner=include&count=10"

# ── RISK METRICS ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def calculate_risk_metrics(ticker, benchmark="^GSPC"):
    """Calculate beta, volatility, Sharpe, max drawdown"""
    try:
        import yfinance as yf
        df = yf.download(ticker, period="2y", interval="1d",
                         auto_adjust=True, progress=False)
        bm = yf.download(benchmark, period="2y", interval="1d",
                         auto_adjust=True, progress=False)
        if df.empty or bm.empty: return {}

        ret = df['Close'].squeeze().pct_change().dropna()
        bret = bm['Close'].squeeze().pct_change().dropna()
        ret, bret = ret.align(bret, join='inner')

        # Beta
        cov = np.cov(ret, bret)
        beta = cov[0,1] / cov[1,1] if cov[1,1] != 0 else 1.0

        # Annualised vol
        vol = ret.std() * np.sqrt(252) * 100

        # Sharpe (rf=4%)
        rf = 0.04/252
        sharpe = (ret.mean()-rf) / ret.std() * np.sqrt(252) if ret.std()>0 else 0

        # Max drawdown
        prices = df['Close'].squeeze()
        roll_max = prices.cummax()
        drawdown = (prices - roll_max) / roll_max * 100
        max_dd = drawdown.min()

        # Correlation
        corr = ret.corr(bret)

        # Sortino
        downside = ret[ret < 0].std() * np.sqrt(252)
        sortino = (ret.mean()-rf)*252 / downside if downside>0 else 0

        # VaR (95%)
        var_95 = np.percentile(ret, 5) * 100
        var_99 = np.percentile(ret, 1) * 100

        return {
            'beta': round(beta, 3),
            'volatility_pct': round(vol, 2),
            'sharpe': round(sharpe, 3),
            'sortino': round(sortino, 3),
            'max_drawdown_pct': round(max_dd, 2),
            'correlation': round(corr, 3),
            'var_95': round(var_95, 3),
            'var_99': round(var_99, 3),
            'alpha': round((ret.mean() - bret.mean()) * 252 * 100, 3),
        }
    except: return {}


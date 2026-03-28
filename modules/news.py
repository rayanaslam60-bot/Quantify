# modules/news.py — Live news feed with RSS sources and NY time

import streamlit as st
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
import pytz
import yfinance as yf

NY_TZ = pytz.timezone('America/New_York')

def ny_time():
    return datetime.now(NY_TZ).strftime('%H:%M:%S ET')

def ny_timestamp(dt_str):
    """Convert any timestamp string to NY time"""
    try:
        dt = parsedate_to_datetime(dt_str)
        dt_ny = dt.astimezone(NY_TZ)
        now_ny = datetime.now(NY_TZ)
        diff = now_ny - dt_ny
        secs = int(diff.total_seconds())
        if secs < 60: return f"{secs}s ago"
        if secs < 3600: return f"{secs//60}m ago"
        if secs < 86400: return f"{secs//3600}h ago"
        return dt_ny.strftime('%b %d %H:%M ET')
    except:
        return dt_str[:16] if dt_str else ''

def unix_to_ny(ts):
    try:
        dt = datetime.fromtimestamp(ts, tz=NY_TZ)
        now_ny = datetime.now(NY_TZ)
        diff = now_ny - dt
        secs = int(diff.total_seconds())
        if secs < 60: return f"{secs}s ago"
        if secs < 3600: return f"{secs//60}m ago"
        if secs < 86400: return f"{secs//3600}h ago"
        return dt.strftime('%b %d %H:%M ET')
    except:
        return ''

# RSS feeds per category
RSS_FEEDS = {
    "MARKET": [
        ("Reuters Markets",  "https://feeds.reuters.com/reuters/businessNews"),
        ("CNBC Markets",     "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
        ("MarketWatch",      "https://feeds.marketwatch.com/marketwatch/topstories/"),
        ("Seeking Alpha",    "https://seekingalpha.com/market_currents.xml"),
        ("Yahoo Finance",    "https://finance.yahoo.com/news/rssindex"),
        ("Investopedia",     "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline"),
        ("The Street",       "https://www.thestreet.com/rss/common/rss.xml"),
        ("Motley Fool",      "https://www.fool.com/feeds/index.aspx"),
    ],
    "CRYPTO": [
        ("CoinDesk",         "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("CoinTelegraph",    "https://cointelegraph.com/rss"),
        ("Decrypt",          "https://decrypt.co/feed"),
        ("The Block",        "https://www.theblock.co/rss.xml"),
        ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
        ("Crypto Briefing",  "https://cryptobriefing.com/feed/"),
    ],
    "COMMODITIES": [
        ("Reuters Commodities","https://feeds.reuters.com/reuters/commoditiesNews"),
        ("OilPrice.com",       "https://oilprice.com/rss/main"),
        ("Kitco Gold",         "https://www.kitco.com/rss/news.xml"),
    ],
    "EQUITIES": [
        ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
        ("CNBC Investing",   "https://www.cnbc.com/id/15839135/device/rss/rss.html"),
        ("Barrons",          "https://www.barrons.com/xml/rss/3_7510.xml"),
        ("Seeking Alpha",    "https://seekingalpha.com/market_currents.xml"),
    ],
}

TICKER_CATEGORY = {
    "BTC-USD":"CRYPTO","ETH-USD":"CRYPTO","SOL-USD":"CRYPTO","XRP-USD":"CRYPTO",
    "BNB-USD":"CRYPTO","DOGE-USD":"CRYPTO","ADA-USD":"CRYPTO","AVAX-USD":"CRYPTO",
    "LINK-USD":"CRYPTO","DOT-USD":"CRYPTO","MATIC-USD":"CRYPTO",
    "GC=F":"COMMODITIES","SI=F":"COMMODITIES","CL=F":"COMMODITIES",
    "NG=F":"COMMODITIES","HG=F":"COMMODITIES","ZW=F":"COMMODITIES",
    "ES=F":"MARKET","NQ=F":"MARKET","YM=F":"MARKET",
    "SPY":"MARKET","QQQ":"MARKET","DIA":"MARKET","IWM":"MARKET",
}

def parse_rss(url, source_name, limit=5):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        items = root.findall('.//item') or root.findall('.//atom:entry', ns)
        out = []
        for item in items[:limit]:
            title = (item.findtext('title') or
                     item.findtext('atom:title', namespaces=ns) or '').strip()
            link  = (item.findtext('link') or
                     (item.find('atom:link', ns).get('href','') if item.find('atom:link', ns) is not None else '') or
                     item.findtext('guid') or '#').strip()
            pub   = (item.findtext('pubDate') or
                     item.findtext('published') or
                     item.findtext('atom:published', namespaces=ns) or '')
            time_str = ny_timestamp(pub) if pub else ''
            if title and len(title) > 10:
                out.append({'title': title, 'link': link,
                            'source': source_name, 'time': time_str})
        return out
    except:
        return []

@st.cache_data(ttl=60)  # Refresh every 60 seconds
def fetch_live_news(ticker="SPY", limit=30):
    """Fetch live news — refreshes every 60 seconds"""
    category = TICKER_CATEGORY.get(ticker.upper(), "EQUITIES")
    feeds = RSS_FEEDS.get(category, RSS_FEEDS["EQUITIES"])
    if category not in ("MARKET",):
        feeds = feeds + RSS_FEEDS["MARKET"][:3]

    all_news = []
    for source_name, url in feeds:
        articles = parse_rss(url, source_name, limit=5)
        all_news.extend(articles)

    # Yahoo Finance fallback — always reliable
    try:
        yf_news = yf.Ticker(ticker).news or []
        for n in yf_news[:8]:
            ts = n.get('providerPublishTime', 0)
            all_news.append({
                'title': n.get('title', ''),
                'link': n.get('link', '#'),
                'source': n.get('publisher', 'Yahoo Finance'),
                'time': unix_to_ny(ts) if ts else ''
            })
    except:
        pass

    # Google News RSS for broader coverage
    try:
        ticker_clean = ticker.replace('-USD','').replace('=F','').replace('=X','').replace('^','')
        gn_url = f"https://news.google.com/rss/search?q={ticker_clean}+stock+market&hl=en-US&gl=US&ceid=US:en"
        gn_articles = parse_rss(gn_url, "Google News", limit=6)
        all_news.extend(gn_articles)
    except:
        pass

    # Deduplicate
    seen = set()
    unique = []
    for item in all_news:
        key = item['title'][:50].lower().strip()
        if key not in seen and item['title']:
            seen.add(key)
            unique.append(item)

    return unique[:limit]

SOURCE_COLORS = {
    "reuters": "#FF8000","bloomberg": "#1E90FF","wsj": "#E31E24",
    "cnbc": "#00D4AA","marketwatch": "#CC0000","coindesk": "#F7931A",
    "cointelegraph": "#2D9CDB","ft": "#FCD200","yahoo": "#720E9E",
    "seeking alpha": "#1DB954","barrons": "#E31E24","the block": "#00A3FF",
    "decrypt": "#00C4B4","google news": "#4285F4","oilprice": "#8B4513",
    "kitco": "#FFD700","motley fool": "#21A366","the street": "#1B5E20",
    "investopedia": "#003087","bitcoin magazine": "#F7931A",
    "crypto briefing": "#6C3483",
}

def get_source_color(source, default="#2979ff"):
    sl = source.lower()
    for k, v in SOURCE_COLORS.items():
        if k in sl:
            return v
    return default

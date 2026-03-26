# modules/tickers.py — Ticker database and search

TICKER_DB = [
    # Mega Cap US
    ("AAPL","Apple Inc"),("MSFT","Microsoft Corp"),("NVDA","NVIDIA Corp"),
    ("AMZN","Amazon"),("GOOGL","Alphabet A"),("GOOG","Alphabet C"),
    ("META","Meta Platforms"),("TSLA","Tesla Inc"),("BRK.B","Berkshire B"),
    ("UNH","UnitedHealth"),("JPM","JPMorgan Chase"),("V","Visa Inc"),
    ("XOM","Exxon Mobil"),("JNJ","Johnson & Johnson"),("PG","Procter & Gamble"),
    ("MA","Mastercard"),("HD","Home Depot"),("CVX","Chevron"),
    ("AVGO","Broadcom Inc"),("LLY","Eli Lilly"),("ABBV","AbbVie"),
    ("MRK","Merck & Co"),("KO","Coca-Cola"),("PEP","PepsiCo"),
    ("COST","Costco"),("TMO","Thermo Fisher"),("MCD","McDonald's"),
    ("CSCO","Cisco"),("ACN","Accenture"),("ABT","Abbott Labs"),
    ("WMT","Walmart"),("CRM","Salesforce"),("AMD","AMD"),
    ("NFLX","Netflix"),("INTC","Intel"),("DIS","Walt Disney"),
    ("ADBE","Adobe"),("PYPL","PayPal"),("QCOM","Qualcomm"),
    ("NKE","Nike"),("GS","Goldman Sachs"),("MS","Morgan Stanley"),
    ("WFC","Wells Fargo"),("C","Citigroup"),("GE","General Electric"),
    ("BA","Boeing"),("CAT","Caterpillar"),("MMM","3M Company"),
    ("IBM","IBM Corp"),("UBER","Uber"),("LYFT","Lyft"),
    ("SNAP","Snap Inc"),("SQ","Block Inc"),("SHOP","Shopify"),
    ("SPOT","Spotify"),("HOOD","Robinhood"),("PLTR","Palantir"),
    ("RBLX","Roblox"),("COIN","Coinbase"),("MSTR","MicroStrategy"),
    ("SMCI","Super Micro"),("ARM","ARM Holdings"),
    # International
    ("TSM","Taiwan Semi"),("ASML","ASML Holding"),("SAP","SAP SE"),
    ("TM","Toyota"),("SONY","Sony Group"),("BABA","Alibaba"),
    ("JD","JD.com"),("PDD","PDD Holdings"),("BIDU","Baidu"),
    ("NIO","NIO Inc"),("HSBC","HSBC Holdings"),("BP","BP PLC"),
    ("SHEL","Shell PLC"),("RIO","Rio Tinto"),("BHP","BHP Group"),
    # ETFs
    ("SPY","S&P 500 ETF"),("QQQ","Nasdaq 100 ETF"),("DIA","Dow Jones ETF"),
    ("IWM","Russell 2000 ETF"),("VTI","Vanguard Total Market"),
    ("VOO","Vanguard S&P 500"),("VEA","Vanguard Intl"),("VWO","Vanguard EM"),
    ("GLD","Gold ETF"),("SLV","Silver ETF"),("USO","Oil ETF"),
    ("TLT","20Y Treasury ETF"),("HYG","High Yield Bond"),
    ("XLK","Tech ETF"),("XLF","Financials ETF"),("XLE","Energy ETF"),
    ("XLV","Health ETF"),("XLI","Industrial ETF"),("XLRE","Real Estate ETF"),
    ("XLU","Utilities ETF"),("XLP","Consumer Staples ETF"),
    ("ARKK","ARK Innovation"),("TQQQ","3x Long QQQ"),("SQQQ","3x Short QQQ"),
    # Crypto
    ("BTC-USD","Bitcoin"),("ETH-USD","Ethereum"),("SOL-USD","Solana"),
    ("XRP-USD","XRP Ripple"),("BNB-USD","BNB Binance"),("DOGE-USD","Dogecoin"),
    ("ADA-USD","Cardano"),("AVAX-USD","Avalanche"),("LINK-USD","Chainlink"),
    ("DOT-USD","Polkadot"),("MATIC-USD","Polygon"),("UNI-USD","Uniswap"),
    ("ATOM-USD","Cosmos"),("LTC-USD","Litecoin"),("BCH-USD","Bitcoin Cash"),
    ("SHIB-USD","Shiba Inu"),("PEPE-USD","Pepe"),("WIF-USD","dogwifhat"),
    ("ARB-USD","Arbitrum"),("OP-USD","Optimism"),("APT-USD","Aptos"),
    ("SUI-USD","Sui"),("INJ-USD","Injective"),("TIA-USD","Celestia"),
    # Futures
    ("ES=F","S&P 500 Futures"),("NQ=F","Nasdaq Futures"),("YM=F","Dow Futures"),
    ("RTY=F","Russell Futures"),("ZN=F","10Y Treasury"),("ZB=F","30Y Treasury"),
    ("GC=F","Gold Futures"),("SI=F","Silver Futures"),("CL=F","Crude Oil WTI"),
    ("BZ=F","Brent Crude"),("NG=F","Natural Gas"),("HG=F","Copper"),
    ("ZW=F","Wheat"),("ZC=F","Corn"),("ZS=F","Soybeans"),
    ("PL=F","Platinum"),("PA=F","Palladium"),
    # Forex
    ("EURUSD=X","EUR/USD"),("GBPUSD=X","GBP/USD"),("USDJPY=X","USD/JPY"),
    ("AUDUSD=X","AUD/USD"),("USDCAD=X","USD/CAD"),("USDCHF=X","USD/CHF"),
    ("NZDUSD=X","NZD/USD"),("EURGBP=X","EUR/GBP"),("EURJPY=X","EUR/JPY"),
    # Indices
    ("^VIX","VIX Volatility"),("^GSPC","S&P 500"),("^DJI","Dow Jones"),
    ("^IXIC","Nasdaq Composite"),("^RUT","Russell 2000"),("^FTSE","FTSE 100"),
    ("^DAX","DAX Germany"),("^N225","Nikkei 225"),("^HSI","Hang Seng"),
]

TICKER_MAP = {t: n for t, n in TICKER_DB}

def search_tickers(q, limit=10):
    if not q or len(q) < 1:
        return []
    qu = q.upper().strip()
    exact, prefix, name = [], [], []
    for t, n in TICKER_DB:
        key = f"{t} — {n}"
        if t.upper() == qu:
            exact.append(key)
        elif t.upper().startswith(qu):
            prefix.append(key)
        elif qu in n.upper():
            name.append(key)
    return (exact + prefix + name)[:limit]

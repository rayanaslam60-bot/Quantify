# modules/tradingview.py — TradingView widget integration

TV_SYMBOL_MAP = {
    # US Large Cap - NYSE
    "JPM":"NYSE:JPM","GS":"NYSE:GS","MS":"NYSE:MS","BAC":"NYSE:BAC",
    "WFC":"NYSE:WFC","C":"NYSE:C","V":"NYSE:V","MA":"NYSE:MA",
    "JNJ":"NYSE:JNJ","UNH":"NYSE:UNH","PFE":"NYSE:PFE","ABBV":"NYSE:ABBV",
    "MRK":"NYSE:MRK","LLY":"NYSE:LLY","ABT":"NYSE:ABT","TMO":"NYSE:TMO",
    "XOM":"NYSE:XOM","CVX":"NYSE:CVX","COP":"NYSE:COP","SLB":"NYSE:SLB",
    "WMT":"NYSE:WMT","HD":"NYSE:HD","MCD":"NYSE:MCD","NKE":"NYSE:NKE",
    "KO":"NYSE:KO","PEP":"NYSE:PEP","PG":"NYSE:PG","CL":"NYSE:CL",
    "DIS":"NYSE:DIS","BA":"NYSE:BA","GE":"NYSE:GE","CAT":"NYSE:CAT",
    "MMM":"NYSE:MMM","HON":"NYSE:HON","RTX":"NYSE:RTX","LMT":"NYSE:LMT",
    "BRK.B":"NYSE:BRK.B","BRK.A":"NYSE:BRK.A",
    "T":"NYSE:T","VZ":"NYSE:VZ","TMUS":"NASDAQ:TMUS",
    "CVS":"NYSE:CVS","UPS":"NYSE:UPS","FDX":"NYSE:FDX",
    "USB":"NYSE:USB","PNC":"NYSE:PNC","TFC":"NYSE:TFC","COF":"NYSE:COF",
    "AXP":"NYSE:AXP","BLK":"NYSE:BLK","SCHW":"NYSE:SCHW",
    "NEE":"NYSE:NEE","DUK":"NYSE:DUK","SO":"NYSE:SO","AEP":"NYSE:AEP",
    "AMT":"NYSE:AMT","PLD":"NYSE:PLD","CCI":"NYSE:CCI","EQIX":"NASDAQ:EQIX",
    "SHW":"NYSE:SHW","LIN":"NYSE:LIN","APD":"NYSE:APD","ECL":"NYSE:ECL",
    "UNP":"NYSE:UNP","CSX":"NYSE:CSX","NSC":"NYSE:NSC",
    "UBER":"NYSE:UBER","LYFT":"NASDAQ:LYFT","SQ":"NYSE:SQ",
    "SHOP":"NYSE:SHOP","COIN":"NASDAQ:COIN","HOOD":"NASDAQ:HOOD",
    "PLTR":"NYSE:PLTR","RBLX":"NYSE:RBLX","SNAP":"NYSE:SNAP",
    "NIO":"NYSE:NIO","BABA":"NYSE:BABA","JD":"NASDAQ:JD",
    "TSM":"NYSE:TSM","ASML":"NASDAQ:ASML","SAP":"NYSE:SAP",
    "TM":"NYSE:TM","SONY":"NYSE:SONY","BP":"NYSE:BP",
    "SHEL":"NYSE:SHEL","RIO":"NYSE:RIO","BHP":"NYSE:BHP",
    "HSBC":"NYSE:HSBC","UBS":"NYSE:UBS","CS":"NYSE:CS",
    # US Large Cap - NASDAQ
    "AAPL":"NASDAQ:AAPL","MSFT":"NASDAQ:MSFT","NVDA":"NASDAQ:NVDA",
    "AMZN":"NASDAQ:AMZN","GOOGL":"NASDAQ:GOOGL","GOOG":"NASDAQ:GOOG",
    "META":"NASDAQ:META","TSLA":"NASDAQ:TSLA","AMD":"NASDAQ:AMD",
    "NFLX":"NASDAQ:NFLX","INTC":"NASDAQ:INTC","QCOM":"NASDAQ:QCOM",
    "CSCO":"NASDAQ:CSCO","ADBE":"NASDAQ:ADBE","PYPL":"NASDAQ:PYPL",
    "AVGO":"NASDAQ:AVGO","COST":"NASDAQ:COST","PDD":"NASDAQ:PDD",
    "BIDU":"NASDAQ:BIDU","MSTR":"NASDAQ:MSTR","SMCI":"NASDAQ:SMCI",
    "ARM":"NASDAQ:ARM","MRVL":"NASDAQ:MRVL","MU":"NASDAQ:MU",
    "LRCX":"NASDAQ:LRCX","AMAT":"NASDAQ:AMAT","KLAC":"NASDAQ:KLAC",
    "PANW":"NASDAQ:PANW","CRWD":"NASDAQ:CRWD","ZS":"NASDAQ:ZS",
    "SNOW":"NYSE:SNOW","DDOG":"NASDAQ:DDOG","MDB":"NASDAQ:MDB",
    "NET":"NYSE:NET","GTLB":"NASDAQ:GTLB","OKTA":"NASDAQ:OKTA",
    "TEAM":"NASDAQ:TEAM","WDAY":"NASDAQ:WDAY","NOW":"NYSE:NOW",
    "CRM":"NYSE:CRM","ORCL":"NYSE:ORCL","IBM":"NYSE:IBM","ACN":"NYSE:ACN",
    # ETFs
    "SPY":"AMEX:SPY","QQQ":"NASDAQ:QQQ","DIA":"AMEX:DIA","IWM":"AMEX:IWM",
    "VTI":"AMEX:VTI","VOO":"AMEX:VOO","VEA":"AMEX:VEA","VWO":"AMEX:VWO",
    "GLD":"AMEX:GLD","SLV":"AMEX:SLV","USO":"AMEX:USO","UNG":"AMEX:UNG",
    "TLT":"NASDAQ:TLT","IEF":"NASDAQ:IEF","SHY":"NASDAQ:SHY",
    "HYG":"AMEX:HYG","LQD":"AMEX:LQD","EMB":"NASDAQ:EMB",
    "XLK":"AMEX:XLK","XLF":"AMEX:XLF","XLE":"AMEX:XLE","XLV":"AMEX:XLV",
    "XLI":"AMEX:XLI","XLRE":"AMEX:XLRE","XLU":"AMEX:XLU",
    "XLP":"AMEX:XLP","XLY":"AMEX:XLY","XLB":"AMEX:XLB","XLC":"AMEX:XLC",
    "ARKK":"AMEX:ARKK","ARKW":"AMEX:ARKW","ARKG":"AMEX:ARKG",
    "TQQQ":"NASDAQ:TQQQ","SQQQ":"NASDAQ:SQQQ",
    "SPXL":"AMEX:SPXL","SPXS":"AMEX:SPXS",
    "UVXY":"AMEX:UVXY","SVXY":"AMEX:SVXY","VXX":"AMEX:VXX",
    "IEMG":"AMEX:IEMG","EEM":"AMEX:EEM","EFA":"AMEX:EFA",
    "AGG":"AMEX:AGG","BND":"NASDAQ:BND",
    # Crypto - all on Binance or Coinbase
    "BTC-USD":"BINANCE:BTCUSDT","ETH-USD":"BINANCE:ETHUSDT",
    "SOL-USD":"BINANCE:SOLUSDT","XRP-USD":"BINANCE:XRPUSDT",
    "BNB-USD":"BINANCE:BNBUSDT","DOGE-USD":"BINANCE:DOGEUSDT",
    "ADA-USD":"BINANCE:ADAUSDT","AVAX-USD":"BINANCE:AVAXUSDT",
    "LINK-USD":"BINANCE:LINKUSDT","DOT-USD":"BINANCE:DOTUSDT",
    "MATIC-USD":"BINANCE:MATICUSDT","UNI-USD":"BINANCE:UNIUSDT",
    "ATOM-USD":"BINANCE:ATOMUSDT","LTC-USD":"BINANCE:LTCUSDT",
    "BCH-USD":"BINANCE:BCHUSDT","SHIB-USD":"BINANCE:SHIBUSDT",
    "PEPE-USD":"BINANCE:PEPEUSDT","WIF-USD":"BINANCE:WIFUSDT",
    "ARB-USD":"BINANCE:ARBUSDT","OP-USD":"BINANCE:OPUSDT",
    "APT-USD":"BINANCE:APTUSDT","SUI-USD":"BINANCE:SUIUSDT",
    "INJ-USD":"BINANCE:INJUSDT","TIA-USD":"BINANCE:TIAUSDT",
    "JTO-USD":"BINANCE:JTOUSDT","BONK-USD":"BINANCE:BONKUSDT",
    "WLD-USD":"BINANCE:WLDUSDT","JUP-USD":"BINANCE:JUPUSDT",
    "FLOKI-USD":"BINANCE:FLOKIUSDT","SEI-USD":"BINANCE:SEIUSDT",
    "FET-USD":"BINANCE:FETUSDT","RENDER-USD":"BINANCE:RENDERUSDT",
    "IMX-USD":"BINANCE:IMXUSDT","SAND-USD":"BINANCE:SANDUSDT",
    "MANA-USD":"BINANCE:MANAUSDT","AXS-USD":"BINANCE:AXSUSDT",
    "NEAR-USD":"BINANCE:NEARUSDT","FTM-USD":"BINANCE:FTMUSDT",
    "ALGO-USD":"BINANCE:ALGOUSDT","XLM-USD":"BINANCE:XLMUSDT",
    "VET-USD":"BINANCE:VETUSDT","HBAR-USD":"BINANCE:HBARUSDT",
    "ICP-USD":"BINANCE:ICPUSDT","EGLD-USD":"BINANCE:EGLDUSDT",
    # Futures - all continuous contracts
    "ES=F":"CME_MINI:ES1!","NQ=F":"CME_MINI:NQ1!",
    "YM=F":"CBOT_MINI:YM1!","RTY=F":"CME_MINI:RTY1!",
    "ZN=F":"CBOT:ZN1!","ZB=F":"CBOT:ZB1!",
    "ZF=F":"CBOT:ZF1!","ZT=F":"CBOT:ZT1!",
    "GC=F":"COMEX:GC1!","SI=F":"COMEX:SI1!","HG=F":"COMEX:HG1!",
    "CL=F":"NYMEX:CL1!","BZ=F":"NYMEX:BB1!","NG=F":"NYMEX:NG1!",
    "ZW=F":"CBOT:ZW1!","ZC=F":"CBOT:ZC1!","ZS=F":"CBOT:ZS1!",
    "PL=F":"NYMEX:PL1!","PA=F":"NYMEX:PA1!",
    "LE=F":"CME:LE1!","HE=F":"CME:HE1!",
    "KC=F":"ICEUS:KC1!","CC=F":"ICEUS:CC1!","SB=F":"ICEUS:SB1!",
    "CT=F":"ICEUS:CT1!","OJ=F":"ICEUS:OJ1!",
    # Forex pairs
    "EURUSD=X":"FX:EURUSD","GBPUSD=X":"FX:GBPUSD","USDJPY=X":"FX:USDJPY",
    "AUDUSD=X":"FX:AUDUSD","USDCAD=X":"FX:USDCAD","USDCHF=X":"FX:USDCHF",
    "NZDUSD=X":"FX:NZDUSD","USDCNY=X":"FX:USDCNY","USDHKD=X":"FX:USDHKD",
    "USDSGD=X":"FX:USDSGD","USDINR=X":"FX:USDINR","USDMXN=X":"FX:USDMXN",
    "USDBRL=X":"FX:USDBRL","USDKRW=X":"FX:USDKRW","EURGBP=X":"FX:EURGBP",
    "EURJPY=X":"FX:EURJPY","GBPJPY=X":"FX:GBPJPY","CADJPY=X":"FX:CADJPY",
    "AUDJPY=X":"FX:AUDJPY","CHFJPY=X":"FX:CHFJPY","EURCHF=X":"FX:EURCHF",
    "EURAUD=X":"FX:EURAUD","EURCAD=X":"FX:EURCAD","GBPAUD=X":"FX:GBPAUD",
    "GBPCAD=X":"FX:GBPCAD","AUDCAD=X":"FX:AUDCAD","AUDNZD=X":"FX:AUDNZD",
    # Indices
    "^VIX":"CBOE:VIX","^GSPC":"SP:SPX","^DJI":"DJ:DJI",
    "^IXIC":"NASDAQ:COMP","^RUT":"RUSSELL:RUT","^FTSE":"SPREADEX:FTSE",
    "^DAX":"XETR:DAX","^N225":"TVC:NI225","^HSI":"TVC:HSI",
    "^STOXX50E":"EURONEXT:SX5E","^AXJO":"ASX:XJO","^BVSP":"BMFBOVESPA:IBOV",
    "^NSEI":"NSE:NIFTY","^GDAXI":"XETR:DAX","^FCHI":"EURONEXT:PX1",
    "^IBEX":"BME:IBEX","^AEX":"EURONEXT:AEX",
}

TV_INTERVALS = {
    "1m":"1","5m":"5","15m":"15","30m":"30",
    "1h":"60","2h":"120","4h":"240","1D":"1D","1W":"1W","1M":"1M",
}

# Known NYSE vs NASDAQ — prevents "symbol not available" errors
NYSE_STOCKS = {
    "JPM","GS","MS","BAC","WFC","C","V","MA","JNJ","UNH","PFE","ABBV","MRK","LLY",
    "ABT","TMO","XOM","CVX","COP","SLB","WMT","HD","MCD","NKE","KO","PEP","PG",
    "DIS","BA","GE","CAT","MMM","HON","RTX","LMT","BRK.B","BRK.A","T","VZ",
    "CVS","UPS","FDX","USB","PNC","TFC","COF","AXP","BLK","SCHW","NEE","DUK","SO",
    "AMT","PLD","CCI","SPG","O","WELL","PSA","EQR","SHW","LIN","APD","ECL","UNP",
    "CSX","NSC","UBER","SNAP","SQ","SHOP","PLTR","RBLX","COIN","MSTR","TSM","ASML",
    "SAP","TM","SONY","BP","SHEL","RIO","BHP","HSBC","NIO","BABA","LOW","TGT",
    "NOW","CRM","ORCL","IBM","ACN","F","GM","SBUX","COST","PM","MO","CL","WBA",
    "MPC","PSX","VLO","OXY","PXD","EOG","EQIX","DLR","AMT","NET","SNOW","DDOG",
    "ZS","PANW","CRWD","MDB","GTLB","OKTA","TEAM","WDAY","TWLO","ZM","DOCU",
}

def get_tv_symbol(yahoo_ticker):
    """
    Convert Yahoo Finance ticker to TradingView symbol.
    Rule: only specify exchange when we KNOW it 100%.
    For regular stocks, pass bare ticker — TradingView resolves automatically.
    """
    t = yahoo_ticker.upper().strip()

    # Direct map — only for tickers that need special exchange prefixes
    if t in TV_SYMBOL_MAP:
        return TV_SYMBOL_MAP[t]

    # Crypto
    if t.endswith("-USD"):
        base = t.replace("-USD", "")
        return f"BINANCE:{base}USDT"

    # Forex
    if t.endswith("=X"):
        pair = t.replace("=X", "")
        if len(pair) >= 6:
            return f"FX:{pair[:6]}"

    # Futures
    if t.endswith("=F"):
        base = t.replace("=F", "")
        futures_map = {
            "ES":"CME_MINI:ES1!","NQ":"CME_MINI:NQ1!","YM":"CBOT_MINI:YM1!",
            "RTY":"CME_MINI:RTY1!","GC":"COMEX:GC1!","SI":"COMEX:SI1!",
            "CL":"NYMEX:CL1!","BZ":"NYMEX:BB1!","NG":"NYMEX:NG1!",
            "HG":"COMEX:HG1!","ZW":"CBOT:ZW1!","ZC":"CBOT:ZC1!",
            "ZS":"CBOT:ZS1!","ZN":"CBOT:ZN1!","ZB":"CBOT:ZB1!",
            "PL":"NYMEX:PL1!","PA":"NYMEX:PA1!",
            "KC":"ICEUS:KC1!","CC":"ICEUS:CC1!","SB":"ICEUS:SB1!",
        }
        if base in futures_map:
            return futures_map[base]
        return f"CME:{base}1!"

    # Indices
    if t.startswith("^"):
        idx_map = {
            "^VIX":"CBOE:VIX","^GSPC":"SP:SPX","^DJI":"DJ:DJI",
            "^IXIC":"NASDAQ:COMP","^RUT":"RUSSELL:RUT",
            "^FTSE":"SPREADEX:FTSE","^DAX":"XETR:DAX",
            "^N225":"TVC:NI225","^HSI":"TVC:HSI",
            "^STOXX50E":"EURONEXT:SX5E",
        }
        return idx_map.get(t, f"TVC:{t[1:]}")

    # Regular stocks — NO exchange prefix, TradingView finds them automatically
    return t

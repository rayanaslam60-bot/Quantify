# modules/tradingview.py — TradingView widget integration

import streamlit.components.v1 as components

# Maps Yahoo Finance tickers to TradingView symbols
TV_SYMBOL_MAP = {
    # US Stocks
    "AAPL":"NASDAQ:AAPL","MSFT":"NASDAQ:MSFT","NVDA":"NASDAQ:NVDA",
    "AMZN":"NASDAQ:AMZN","GOOGL":"NASDAQ:GOOGL","GOOG":"NASDAQ:GOOG",
    "META":"NASDAQ:META","TSLA":"NASDAQ:TSLA","AMD":"NASDAQ:AMD",
    "NFLX":"NASDAQ:NFLX","INTC":"NASDAQ:INTC","QCOM":"NASDAQ:QCOM",
    "CSCO":"NASDAQ:CSCO","ADBE":"NASDAQ:ADBE","PYPL":"NASDAQ:PYPL",
    "COIN":"NASDAQ:COIN","HOOD":"NASDAQ:HOOD","PLTR":"NASDAQ:PLTR",
    "RBLX":"NYSE:RBLX","UBER":"NYSE:UBER","SNAP":"NYSE:SNAP",
    "JPM":"NYSE:JPM","GS":"NYSE:GS","MS":"NYSE:MS","BAC":"NYSE:BAC",
    "WFC":"NYSE:WFC","C":"NYSE:C","V":"NYSE:V","MA":"NYSE:MA",
    "JNJ":"NYSE:JNJ","UNH":"NYSE:UNH","PFE":"NYSE:PFE","ABBV":"NYSE:ABBV",
    "XOM":"NYSE:XOM","CVX":"NYSE:CVX","WMT":"NYSE:WMT","HD":"NYSE:HD",
    "MCD":"NYSE:MCD","KO":"NYSE:KO","PEP":"NYSE:PEP","NKE":"NYSE:NKE",
    "DIS":"NYSE:DIS","BA":"NYSE:BA","GE":"NYSE:GE","CAT":"NYSE:CAT",
    "IBM":"NYSE:IBM","CRM":"NYSE:CRM","MSTR":"NASDAQ:MSTR",
    "SMCI":"NASDAQ:SMCI","ARM":"NASDAQ:ARM","SHOP":"NYSE:SHOP",
    "TSM":"NYSE:TSM","BABA":"NYSE:BABA","NIO":"NYSE:NIO",
    # ETFs
    "SPY":"AMEX:SPY","QQQ":"NASDAQ:QQQ","DIA":"AMEX:DIA","IWM":"AMEX:IWM",
    "VTI":"AMEX:VTI","VOO":"AMEX:VOO","GLD":"AMEX:GLD","SLV":"AMEX:SLV",
    "TLT":"NASDAQ:TLT","HYG":"AMEX:HYG","XLK":"AMEX:XLK","XLF":"AMEX:XLF",
    "XLE":"AMEX:XLE","XLV":"AMEX:XLV","XLI":"AMEX:XLI","XLRE":"AMEX:XLRE",
    "XLU":"AMEX:XLU","ARKK":"AMEX:ARKK","TQQQ":"NASDAQ:TQQQ","SQQQ":"NASDAQ:SQQQ",
    "USO":"AMEX:USO","XLP":"AMEX:XLP",
    # Crypto
    "BTC-USD":"BINANCE:BTCUSDT","ETH-USD":"BINANCE:ETHUSDT",
    "SOL-USD":"BINANCE:SOLUSDT","XRP-USD":"BINANCE:XRPUSDT",
    "BNB-USD":"BINANCE:BNBUSDT","DOGE-USD":"BINANCE:DOGEUSDT",
    "ADA-USD":"BINANCE:ADAUSDT","AVAX-USD":"BINANCE:AVAXUSDT",
    "LINK-USD":"BINANCE:LINKUSDT","DOT-USD":"BINANCE:DOTUSDT",
    "MATIC-USD":"BINANCE:MATICUSDT","UNI-USD":"BINANCE:UNIUSDT",
    "LTC-USD":"BINANCE:LTCUSDT","BCH-USD":"BINANCE:BCHUSDT",
    "SHIB-USD":"BINANCE:SHIBUSDT","PEPE-USD":"BINANCE:PEPEUSDT",
    "ARB-USD":"BINANCE:ARBUSDT","OP-USD":"BINANCE:OPUSDT",
    "APT-USD":"BINANCE:APTUSDT","SUI-USD":"BINANCE:SUIUSDT",
    "INJ-USD":"BINANCE:INJUSDT","ATOM-USD":"BINANCE:ATOMUSDT",
    # Futures
    "ES=F":"CME_MINI:ES1!","NQ=F":"CME_MINI:NQ1!","YM=F":"CBOT_MINI:YM1!",
    "RTY=F":"CME_MINI:RTY1!","GC=F":"COMEX:GC1!","SI=F":"COMEX:SI1!",
    "CL=F":"NYMEX:CL1!","BZ=F":"NYMEX:BB1!","NG=F":"NYMEX:NG1!",
    "HG=F":"COMEX:HG1!","ZW=F":"CBOT:ZW1!","ZC=F":"CBOT:ZC1!",
    "ZN=F":"CBOT:ZN1!","ZB=F":"CBOT:ZB1!",
    # Forex
    "EURUSD=X":"FX:EURUSD","GBPUSD=X":"FX:GBPUSD","USDJPY=X":"FX:USDJPY",
    "AUDUSD=X":"FX:AUDUSD","USDCAD=X":"FX:USDCAD","USDCHF=X":"FX:USDCHF",
    "NZDUSD=X":"FX:NZDUSD","EURGBP=X":"FX:EURGBP","EURJPY=X":"FX:EURJPY",
    "GBPJPY=X":"FX:GBPJPY",
    # Indices
    "^VIX":"CBOE:VIX","^GSPC":"SP:SPX","^DJI":"DJ:DJI",
    "^IXIC":"NASDAQ:COMP","^FTSE":"SPREADEX:FTSE",
    "^DAX":"XETR:DAX","^N225":"TSE:NI225",
}

TV_INTERVALS = {
    "1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1D":"1D","1W":"1W",
}

def get_tv_symbol(yahoo_ticker):
    """Convert Yahoo Finance ticker to TradingView symbol"""
    return TV_SYMBOL_MAP.get(yahoo_ticker, f"NASDAQ:{yahoo_ticker}")

def tv_chart(ticker, interval="1D", theme="dark", height=650, studies=None):
    """
    Render a full TradingView chart widget.
    studies: list of built-in study names to add e.g. ["RSI","MACD"]
    """
    tv_sym = get_tv_symbol(ticker)
    tv_int = TV_INTERVALS.get(interval, "1D")
    bg = "#010408" if theme=="dark" else "#ffffff"

    # Build studies array
    studies_js = ""
    if studies:
        studies_list = ", ".join([f'"{s}"' for s in studies])
        studies_js = f'studies: [{studies_list}],'

    html = f"""
    <html>
    <head>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:{bg}; }}
        #tv_chart_container {{ height:{height}px; width:100%; }}
    </style>
    </head>
    <body>
        <div id="tv_chart_container"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            autosize: true,
            symbol: "{tv_sym}",
            interval: "{tv_int}",
            timezone: "Etc/UTC",
            theme: "{theme}",
            style: "1",
            locale: "en",
            toolbar_bg: "{bg}",
            enable_publishing: false,
            allow_symbol_change: true,
            hide_side_toolbar: false,
            hide_top_toolbar: false,
            withdateranges: true,
            save_image: true,
            container_id: "tv_chart_container",
            {studies_js}
            overrides: {{
                "paneProperties.background": "{bg}",
                "paneProperties.backgroundType": "solid",
                "scalesProperties.textColor": "#2a5070",
                "scalesProperties.lineColor": "#102035",
                "paneProperties.vertGridProperties.color": "#071525",
                "paneProperties.horzGridProperties.color": "#071525",
            }},
            studies_overrides: {{
                "volume.volume.color.0": "#ff3d5766",
                "volume.volume.color.1": "#00e67666",
            }},
        }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=height + 10)

def tv_mini_chart(ticker, theme="dark", height=220):
    """Compact TradingView mini chart — no toolbar"""
    tv_sym = get_tv_symbol(ticker)
    bg = "#010408" if theme=="dark" else "#ffffff"

    html = f"""
    <html>
    <head>
    <style>
        * {{ margin:0;padding:0; }}
        body {{ background:{bg}; }}
        #mini_{ticker.replace('-','').replace('=','').replace('^','')} {{ height:{height}px;width:100%; }}
    </style>
    </head>
    <body>
        <div id="mini_{ticker.replace('-','').replace('=','').replace('^','')}"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.MiniWidget({{
            symbol: "{tv_sym}",
            width: "100%",
            height: {height},
            locale: "en",
            dateRange: "1D",
            colorTheme: "{theme}",
            trendLineColor: "rgba(41,121,255,1)",
            underLineColor: "rgba(41,121,255,0.06)",
            isTransparent: true,
            container_id: "mini_{ticker.replace('-','').replace('=','').replace('^','')}"
        }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=height + 10)

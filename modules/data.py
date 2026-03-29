# modules/data.py — Enhanced data layer with maximum market coverage

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import (RSIIndicator, StochasticOscillator, WilliamsRIndicator,
                          ROCIndicator, StochasticRSIIndicator)
from ta.trend import (MACD, EMAIndicator, SMAIndicator, ADXIndicator,
                       CCIIndicator, IchimokuIndicator, PSARIndicator)
from ta.volatility import (BollingerBands, AverageTrueRange, KeltnerChannel,
                            DonchianChannel, UlcerIndex)
from ta.volume import (OnBalanceVolumeIndicator, MFIIndicator,
                        VolumeWeightedAveragePrice, ChaikinMoneyFlowIndicator,
                        AccDistIndexIndicator, ForceIndexIndicator)
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# All supported timeframes with proper period limits
TIMEFRAMES = {
    "1m":  ("1d",   "1m"),
    "3m":  ("5d",   "3m"),
    "5m":  ("60d",  "5m"),
    "15m": ("60d",  "15m"),
    "30m": ("60d",  "30m"),
    "1h":  ("730d", "1h"),
    "2h":  ("730d", "2h"),
    "4h":  ("730d", "1h"),   # yfinance has no 4h — use 1h data
    "1D":  ("max",  "1d"),
    "1W":  ("max",  "1wk"),
    "1M":  ("max",  "1mo"),
}

# Smart period selector — auto-picks best period for timeframe
SMART_PERIODS = {
    "1m":  ["1 Day","3 Days","5 Days","7 Days"],
    "3m":  ["1 Day","3 Days","5 Days","7 Days"],
    "5m":  ["7 Days","14 Days","30 Days","60 Days"],
    "15m": ["7 Days","14 Days","30 Days","60 Days"],
    "30m": ["7 Days","14 Days","30 Days","60 Days"],
    "1h":  ["1 Month","3 Months","6 Months","1 Year","2 Years"],
    "2h":  ["1 Month","3 Months","6 Months","1 Year","2 Years"],
    "4h":  ["1 Month","3 Months","6 Months","1 Year","2 Years"],
    "1D":  ["1 Month","3 Months","6 Months","1 Year","2 Years","5 Years","Max"],
    "1W":  ["3 Months","6 Months","1 Year","2 Years","5 Years","10 Years","Max"],
    "1M":  ["1 Year","2 Years","5 Years","10 Years","20 Years","Max"],
}

PERIOD_CODES = {
    "1 Day":"1d","3 Days":"3d","5 Days":"5d","7 Days":"7d",
    "14 Days":"14d","30 Days":"30d","60 Days":"60d",
    "1 Month":"1mo","3 Months":"3mo","6 Months":"6mo",
    "1 Year":"1y","2 Years":"2y","5 Years":"5y",
    "10 Years":"10y","20 Years":"20y","Max":"max",
}

@st.cache_data(ttl=30)
def get_data(ticker, period, interval):
    """Fetch OHLCV data with smart error handling"""
    try:
        # Handle 4h specially - fetch 1h then resample
        if interval == "2h":
            df = yf.download(ticker, period=period, interval="1h",
                             auto_adjust=True, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df[['Open','High','Low','Close','Volume']].copy().dropna()
                df = df.resample('2h').agg({
                    'Open':'first','High':'max','Low':'min',
                    'Close':'last','Volume':'sum'
                }).dropna()
            return df if not df.empty else None

        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[['Open','High','Low','Close','Volume']].copy().dropna()
        return df if len(df) > 0 else None
    except Exception as e:
        return None

@st.cache_data(ttl=30)
def price_info(ticker):
    try:
        i = yf.Ticker(ticker).fast_info
        p = i.last_price; prev = i.previous_close
        if not p or not prev: return None, None, None
        return round(p,4), round(p-prev,4), round((p-prev)/prev*100,2)
    except:
        return None, None, None

@st.cache_data(ttl=60)
def get_ticker_info(ticker):
    """Get detailed ticker info — fundamentals, description etc"""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            'name': info.get('longName', ticker),
            'sector': info.get('sector',''),
            'industry': info.get('industry',''),
            'market_cap': info.get('marketCap',0),
            'pe_ratio': info.get('trailingPE',0),
            'eps': info.get('trailingEps',0),
            'dividend': info.get('dividendYield',0),
            'beta': info.get('beta',0),
            '52w_high': info.get('fiftyTwoWeekHigh',0),
            '52w_low': info.get('fiftyTwoWeekLow',0),
            'avg_volume': info.get('averageVolume',0),
            'description': info.get('longBusinessSummary',''),
            'website': info.get('website',''),
            'country': info.get('country',''),
            'currency': info.get('currency','USD'),
        }
    except:
        return {}

@st.cache_data(ttl=60)
def get_multi_prices(tickers):
    """Fetch prices for multiple tickers at once"""
    results = {}
    for t in tickers:
        p, chg, pct = price_info(t)
        results[t] = (p, chg, pct)
    return results

@st.cache_data(ttl=600)
def fetch_news(ticker="SPY", limit=10):
    try:
        news = yf.Ticker(ticker).news or []
        from datetime import datetime
        out = []
        for n in news[:limit]:
            ts = n.get('providerPublishTime', 0)
            out.append({
                'title': n.get('title',''),
                'link': n.get('link','#'),
                'source': n.get('publisher',''),
                'time': datetime.fromtimestamp(ts).strftime('%b %d %H:%M') if ts else ''
            })
        return out
    except:
        return []

def add_indicators(df):
    """Add ALL indicators — comprehensive coverage"""
    if df is None or len(df) < 5:
        return df
    c = df['Close'].squeeze()
    h = df['High'].squeeze()
    l = df['Low'].squeeze()
    v = df['Volume'].squeeze()
    n = len(df)

    def safe(key, fn):
        try:
            result = fn()
            if result is not None:
                df[key] = result
        except:
            pass

    # ── TREND ─────────────────────────────────────────────────────────────────
    safe('e5',   lambda: EMAIndicator(c, window=min(5,n-1)).ema_indicator())
    safe('e9',   lambda: EMAIndicator(c, window=min(9,n-1)).ema_indicator())
    safe('e13',  lambda: EMAIndicator(c, window=min(13,n-1)).ema_indicator())
    safe('e21',  lambda: EMAIndicator(c, window=min(21,n-1)).ema_indicator())
    safe('e34',  lambda: EMAIndicator(c, window=min(34,n-1)).ema_indicator())
    safe('e50',  lambda: EMAIndicator(c, window=min(50,n-1)).ema_indicator())
    safe('e89',  lambda: EMAIndicator(c, window=min(89,n-1)).ema_indicator())
    safe('e100', lambda: EMAIndicator(c, window=min(100,n-1)).ema_indicator())
    safe('e200', lambda: EMAIndicator(c, window=min(200,n-1)).ema_indicator())
    safe('s10',  lambda: SMAIndicator(c, window=min(10,n-1)).sma_indicator())
    safe('s20',  lambda: SMAIndicator(c, window=min(20,n-1)).sma_indicator())
    safe('s50',  lambda: SMAIndicator(c, window=min(50,n-1)).sma_indicator())
    safe('s100', lambda: SMAIndicator(c, window=min(100,n-1)).sma_indicator())
    safe('s200', lambda: SMAIndicator(c, window=min(200,n-1)).sma_indicator())

    # Parabolic SAR
    try:
        psar = PSARIndicator(h, l, c, step=0.02, max_step=0.2)
        df['psar']     = psar.psar()
        df['psar_bull']= psar.psar_up()
        df['psar_bear']= psar.psar_down()
    except: pass

    # ADX with +DI -DI
    try:
        adx_ind = ADXIndicator(h, l, c, window=min(14,n-1))
        df['adx']  = adx_ind.adx()
        df['adx_p']= adx_ind.adx_pos()
        df['adx_n']= adx_ind.adx_neg()
    except: pass

    safe('cci', lambda: CCIIndicator(h, l, c, window=min(20,n-1)).cci())

    # Ichimoku
    try:
        ic = IchimokuIndicator(h, l, window1=9, window2=26, window3=52)
        df['ich_conv']= ic.ichimoku_conversion_line()
        df['ich_base']= ic.ichimoku_base_line()
        df['ich_a']   = ic.ichimoku_a()
        df['ich_b']   = ic.ichimoku_b()
    except: pass

    # Hull MA
    try:
        wma_half = c.rolling(int(min(20,n-1)/2)).mean() * 2
        wma_full = c.rolling(min(20,n-1)).mean()
        df['hma'] = (wma_half - wma_full).rolling(int(np.sqrt(min(20,n-1)))).mean()
    except: pass

    # ── VOLATILITY ────────────────────────────────────────────────────────────
    try:
        bb = BollingerBands(c, window=min(20,n-1), window_dev=2)
        df['bb_upper']= bb.bollinger_hband()
        df['bb_lower']= bb.bollinger_lband()
        df['bb_mid']  = bb.bollinger_mavg()
        df['bb_width']= (df['bb_upper']-df['bb_lower'])/df['bb_mid']
        df['bb_pct']  = bb.bollinger_pband()
        df['bb_hband_ind'] = bb.bollinger_hband_indicator()
        df['bb_lband_ind'] = bb.bollinger_lband_indicator()
    except: pass

    try:
        kc = KeltnerChannel(h, l, c, window=min(20,n-1))
        df['kc_upper']= kc.keltner_channel_hband()
        df['kc_lower']= kc.keltner_channel_lband()
        df['kc_mid']  = kc.keltner_channel_mband()
        df['kc_hband_ind']= kc.keltner_channel_hband_indicator()
        df['kc_lband_ind']= kc.keltner_channel_lband_indicator()
    except: pass

    try:
        dc = DonchianChannel(h, l, c, window=min(20,n-1))
        df['dc_upper']= dc.donchian_channel_hband()
        df['dc_lower']= dc.donchian_channel_lband()
        df['dc_mid']  = dc.donchian_channel_mband()
    except: pass

    safe('atr', lambda: AverageTrueRange(h, l, c, window=min(14,n-1)).average_true_range())
    safe('atr7',lambda: AverageTrueRange(h, l, c, window=min(7,n-1)).average_true_range())

    # ── MOMENTUM ──────────────────────────────────────────────────────────────
    safe('rsi',    lambda: RSIIndicator(c, window=min(14,n-1)).rsi())
    safe('rsi7',   lambda: RSIIndicator(c, window=min(7,n-1)).rsi())
    safe('rsi21',  lambda: RSIIndicator(c, window=min(21,n-1)).rsi())

    try:
        stoch_rsi = StochasticRSIIndicator(c, window=min(14,n-1),
                                            smooth1=3, smooth2=3)
        df['srsi_k'] = stoch_rsi.stochrsi_k()
        df['srsi_d'] = stoch_rsi.stochrsi_d()
    except: pass

    try:
        macd_ind = MACD(c, window_fast=12, window_slow=26, window_sign=9)
        df['macd']      = macd_ind.macd()
        df['macd_sig']  = macd_ind.macd_signal()
        df['macd_hist'] = macd_ind.macd_diff()
    except: pass

    try:
        macd_fast = MACD(c, window_fast=8, window_slow=17, window_sign=9)
        df['macd_f']    = macd_fast.macd()
        df['macd_fs']   = macd_fast.macd_signal()
        df['macd_fh']   = macd_fast.macd_diff()
    except: pass

    try:
        sk = StochasticOscillator(h, l, c, window=min(14,n-1), smooth_window=3)
        df['stoch_k'] = sk.stoch()
        df['stoch_d'] = sk.stoch_signal()
    except: pass

    safe('wr',    lambda: WilliamsRIndicator(h, l, c, lbp=min(14,n-1)).williams_r())
    safe('roc',   lambda: ROCIndicator(c, window=min(12,n-1)).roc())
    safe('roc5',  lambda: ROCIndicator(c, window=min(5,n-1)).roc())

    # Awesome Oscillator
    try:
        median = (h + l) / 2
        df['ao'] = median.rolling(5).mean() - median.rolling(34).mean()
    except: pass

    # ── VOLUME ────────────────────────────────────────────────────────────────
    safe('obv',  lambda: OnBalanceVolumeIndicator(c, v).on_balance_volume())
    safe('mfi',  lambda: MFIIndicator(h, l, c, v, window=min(14,n-1)).money_flow_index())
    safe('vwap', lambda: VolumeWeightedAveragePrice(h, l, c, v).volume_weighted_average_price())
    safe('cmf',  lambda: ChaikinMoneyFlowIndicator(h, l, c, v, window=min(20,n-1)).chaikin_money_flow())
    safe('adi',  lambda: AccDistIndexIndicator(h, l, c, v).acc_dist_index())
    safe('fi',   lambda: ForceIndexIndicator(c, v, window=min(13,n-1)).force_index())

    # ── DERIVED / CUSTOM ──────────────────────────────────────────────────────
    df['vma20']  = v.rolling(20).mean()
    df['vma10']  = v.rolling(10).mean()
    df['vol_ratio'] = v / df['vma20']  # volume vs average

    df['ret1']   = c.pct_change(1)
    df['ret3']   = c.pct_change(3)
    df['ret5']   = c.pct_change(5)
    df['ret10']  = c.pct_change(10)
    df['ret20']  = c.pct_change(20)

    df['hv10']   = c.pct_change().rolling(10).std() * np.sqrt(252)
    df['hv20']   = c.pct_change().rolling(20).std() * np.sqrt(252)
    df['hv50']   = c.pct_change().rolling(50).std() * np.sqrt(252)

    df['mom5']   = c - c.shift(5)
    df['mom10']  = c - c.shift(10)
    df['mom20']  = c - c.shift(20)

    df['zscore'] = (c - c.rolling(20).mean()) / c.rolling(20).std()

    # Price relative to MAs
    for ma_col in ['e9','e21','e50','e200','s20','s50','s200']:
        if ma_col in df.columns:
            df[f'pct_{ma_col}'] = (c - df[ma_col].squeeze()) / df[ma_col].squeeze() * 100

    # Candle body / wick analysis
    df['body']   = abs(c - df['Open'].squeeze())
    df['wick_up']= h - pd.concat([c, df['Open'].squeeze()], axis=1).max(axis=1)
    df['wick_dn']= pd.concat([c, df['Open'].squeeze()], axis=1).min(axis=1) - l
    df['body_pct']= df['body'] / (h - l + 1e-10)  # 0=doji, 1=full body

    # Squeeze (BB inside KC)
    if 'bb_upper' in df.columns and 'kc_upper' in df.columns:
        df['squeeze'] = (df['bb_upper'].squeeze() < df['kc_upper'].squeeze()) & \
                        (df['bb_lower'].squeeze() > df['kc_lower'].squeeze())

    # Higher High / Lower Low detection
    df['hh'] = h == h.rolling(5).max()
    df['ll'] = l == l.rolling(5).min()

    # Trend direction (simple)
    if 'e21' in df.columns and 'e50' in df.columns:
        df['trend'] = np.where(df['e21'].squeeze() > df['e50'].squeeze(), 1, -1)

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df

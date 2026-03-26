# modules/data.py — Data fetching, caching, indicators

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator, ROCIndicator
from ta.trend import MACD, EMAIndicator, SMAIndicator, ADXIndicator, CCIIndicator, IchimokuIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator, VolumeWeightedAveragePrice
from datetime import datetime

TIMEFRAMES = {
    "1m":("1d","1m"), "5m":("7d","5m"), "15m":("30d","15m"),
    "1h":("60d","1h"), "4h":("180d","1h"), "1D":("2y","1d"), "1W":("5y","1wk"),
}

@st.cache_data(ttl=300)
def get_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[['Open','High','Low','Close','Volume']].copy().dropna()
    except:
        return None

@st.cache_data(ttl=60)
def price_info(ticker):
    try:
        i = yf.Ticker(ticker).fast_info
        p = i.last_price
        prev = i.previous_close
        return round(p,4), round(p-prev,4), round((p-prev)/prev*100,2)
    except:
        return None, None, None

@st.cache_data(ttl=600)
def fetch_news(ticker="SPY", limit=10):
    try:
        news = yf.Ticker(ticker).news or []
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
    c=df['Close'].squeeze(); h=df['High'].squeeze()
    l=df['Low'].squeeze(); v=df['Volume'].squeeze(); n=len(df)
    def T(k, fn):
        try: df[k] = fn()
        except: pass
    T('e9',   lambda: EMAIndicator(c, window=min(9,n-1)).ema_indicator())
    T('e21',  lambda: EMAIndicator(c, window=min(21,n-1)).ema_indicator())
    T('e50',  lambda: EMAIndicator(c, window=min(50,n-1)).ema_indicator())
    T('e200', lambda: EMAIndicator(c, window=min(200,n-1)).ema_indicator())
    T('s20',  lambda: SMAIndicator(c, window=min(20,n-1)).sma_indicator())
    try:
        bb = BollingerBands(c, window=min(20,n-1))
        df['bbu'] = bb.bollinger_hband()
        df['bbl'] = bb.bollinger_lband()
        df['bbm'] = bb.bollinger_mavg()
        df['bbw'] = (df['bbu']-df['bbl'])/df['bbm']
        df['bbpct'] = bb.bollinger_pband()
    except: pass
    try:
        kc = KeltnerChannel(h, l, c, window=min(20,n-1))
        df['kcu'] = kc.keltner_channel_hband()
        df['kcl'] = kc.keltner_channel_lband()
    except: pass
    T('rsi',  lambda: RSIIndicator(c, window=min(14,n-1)).rsi())
    try:
        mc = MACD(c)
        df['mc'] = mc.macd()
        df['ms'] = mc.macd_signal()
        df['mh'] = mc.macd_diff()
    except: pass
    try:
        sk = StochasticOscillator(h, l, c, window=min(14,n-1))
        df['stk'] = sk.stoch()
        df['std'] = sk.stoch_signal()
    except: pass
    T('wr',   lambda: WilliamsRIndicator(h, l, c, lbp=min(14,n-1)).williams_r())
    T('roc',  lambda: ROCIndicator(c, window=min(12,n-1)).roc())
    T('cci',  lambda: CCIIndicator(h, l, c, window=min(20,n-1)).cci())
    T('adx',  lambda: ADXIndicator(h, l, c, window=min(14,n-1)).adx())
    T('atr',  lambda: AverageTrueRange(h, l, c, window=min(14,n-1)).average_true_range())
    T('obv',  lambda: OnBalanceVolumeIndicator(c, v).on_balance_volume())
    T('mfi',  lambda: MFIIndicator(h, l, c, v, window=min(14,n-1)).money_flow_index())
    T('vwap', lambda: VolumeWeightedAveragePrice(h, l, c, v).volume_weighted_average_price())
    try:
        ic = IchimokuIndicator(h, l)
        df['ia']  = ic.ichimoku_a()
        df['ib']  = ic.ichimoku_b()
        df['ibl'] = ic.ichimoku_base_line()
        df['icl'] = ic.ichimoku_conversion_line()
    except: pass
    df['vma']  = v.rolling(20).mean()
    df['ret']  = c.pct_change()
    df['ret5'] = c.pct_change(5)
    df['vol20']= c.pct_change().rolling(20).std() * np.sqrt(252)
    df['mom']  = c - c.shift(10)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df

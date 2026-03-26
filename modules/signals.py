# modules/signals.py — Signal computation and ML model

import streamlit as st
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from modules.data import get_data, add_indicators

FEAT = ['rsi','mc','mh','e9','e21','e50','bbw','bbpct','atr','adx',
        'stk','std','wr','cci','roc','mfi','vol20','mom','ret','ret5']

@st.cache_data(ttl=300)
def get_signals_cached(ticker, period, interval):
    df = get_data(ticker, period, interval)
    if df is None or len(df) < 30:
        return None, "NEUTRAL", 0
    df = add_indicators(df)
    sigs, ov, tot = compute_signals(df)
    return df, ov, tot

def compute_signals(df):
    if len(df) < 3:
        return [], "NEUTRAL", 0
    r = df.iloc[-1]; r2 = df.iloc[-2]
    sigs = []; sc = []
    def S(n, sig, d):
        sigs.append((n, sig, d))
        sc.append(1 if sig=="BUY" else -1 if sig=="SELL" else 0)

    if 'rsi' in df.columns:
        v = float(r['rsi'])
        if v < 30: S("RSI","BUY",f"Oversold {v:.1f}")
        elif v > 70: S("RSI","SELL",f"Overbought {v:.1f}")
        elif v < 45: S("RSI","BUY",f"Bullish {v:.1f}")
        elif v > 55: S("RSI","SELL",f"Bearish {v:.1f}")
        else: S("RSI","NEUTRAL",f"Neutral {v:.1f}")
    if 'mh' in df.columns:
        h, h2 = float(r['mh']), float(r2['mh'])
        if h>0 and h2<=0: S("MACD","BUY","Bullish cross")
        elif h<0 and h2>=0: S("MACD","SELL","Bearish cross")
        elif h>0: S("MACD","BUY","Positive hist")
        else: S("MACD","SELL","Negative hist")
    if 'e9' in df.columns and 'e21' in df.columns:
        e9,e21 = float(r['e9']), float(r['e21'])
        if e9>e21 and float(r2['e9'])<=float(r2['e21']): S("EMA 9/21","BUY","Golden cross")
        elif e9<e21 and float(r2['e9'])>=float(r2['e21']): S("EMA 9/21","SELL","Death cross")
        elif e9>e21: S("EMA 9/21","BUY","Short > Long")
        else: S("EMA 9/21","SELL","Short < Long")
    if 'e50' in df.columns and 'e200' in df.columns:
        e50,e200 = float(r['e50']), float(r['e200'])
        if not (np.isnan(e50) or np.isnan(e200)):
            S("EMA 50/200","BUY" if e50>e200 else "SELL","Uptrend" if e50>e200 else "Downtrend")
    if 'bbu' in df.columns:
        p2 = float(r['Close'])
        if p2 < float(r['bbl']): S("Bollinger","BUY","Below lower band")
        elif p2 > float(r['bbu']): S("Bollinger","SELL","Above upper band")
        elif p2 > float(r['bbm']): S("Bollinger","BUY","Above midline")
        else: S("Bollinger","SELL","Below midline")
    if 'stk' in df.columns:
        k,d = float(r['stk']), float(r['std'])
        if k<20 and k>d: S("Stochastic","BUY",f"Oversold cross {k:.1f}")
        elif k>80 and k<d: S("Stochastic","SELL",f"Overbought cross {k:.1f}")
        elif k>d: S("Stochastic","BUY",f"%K>{k:.1f}")
        else: S("Stochastic","SELL",f"%K<{k:.1f}")
    if 'adx' in df.columns:
        adx = float(r['adx'])
        ts = "BUY" if sum(sc)>0 else "SELL" if sum(sc)<0 else "NEUTRAL"
        S("ADX", ts if adx>25 else "NEUTRAL", f"{'Strong' if adx>25 else 'Weak'} {adx:.1f}")
    if 'cci' in df.columns:
        v = float(r['cci'])
        if v<-100: S("CCI","BUY",f"Oversold {v:.0f}")
        elif v>100: S("CCI","SELL",f"Overbought {v:.0f}")
        else: S("CCI","NEUTRAL",f"Neutral {v:.0f}")
    if 'wr' in df.columns:
        v = float(r['wr'])
        if v<-80: S("Williams %R","BUY",f"Oversold {v:.1f}")
        elif v>-20: S("Williams %R","SELL",f"Overbought {v:.1f}")
        else: S("Williams %R","NEUTRAL",f"{v:.1f}")
    if 'mfi' in df.columns:
        v = float(r['mfi'])
        if v<20: S("Money Flow","BUY",f"Oversold {v:.1f}")
        elif v>80: S("Money Flow","SELL",f"Overbought {v:.1f}")
        else: S("Money Flow","NEUTRAL",f"{v:.1f}")
    if 'obv' in df.columns:
        ov = df['obv'].squeeze()
        S("OBV","BUY" if float(ov.iloc[-1])>float(ov.iloc[-5]) else "SELL",
          "Rising" if float(ov.iloc[-1])>float(ov.iloc[-5]) else "Falling")
    if 'vwap' in df.columns:
        vw = float(r.get('vwap', float('nan')))
        if not np.isnan(vw):
            S("VWAP","BUY" if float(r['Close'])>vw else "SELL",
              f"{'Above' if float(r['Close'])>vw else 'Below'} VWAP")
    total = sum(sc)
    if total >= 6: ov = "STRONG BUY"
    elif total >= 2: ov = "BUY"
    elif total <= -6: ov = "STRONG SELL"
    elif total <= -2: ov = "SELL"
    else: ov = "NEUTRAL"
    return sigs, ov, total

def train_model(df):
    c = df['Close'].squeeze()
    df['target'] = (c.shift(-1) > c).astype(int)
    df.dropna(inplace=True)
    av = [f for f in FEAT if f in df.columns]
    if len(df) < 80 or not av:
        return None, None, 0, av
    X = df[av].astype(float).clip(-1e9, 1e9)
    y = df['target']
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, shuffle=False)
    sc = StandardScaler()
    m = GradientBoostingClassifier(n_estimators=200, learning_rate=0.04,
                                    max_depth=4, subsample=0.8, random_state=42)
    m.fit(sc.fit_transform(Xtr), ytr)
    return m, sc, accuracy_score(yte, m.predict(sc.transform(Xte))), av

def ml_predict(df, m, sc, feat):
    if m is None:
        return "NEUTRAL", 0.5
    lat = df[feat].iloc[-1:].astype(float).clip(-1e9, 1e9)
    p = m.predict(sc.transform(lat))[0]
    return ("BUY" if p==1 else "SELL"), m.predict_proba(sc.transform(lat))[0][p]

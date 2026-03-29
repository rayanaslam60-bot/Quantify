# modules/backtest.py — Maximum trade backtest engine

import pandas as pd
import numpy as np
from modules.data import add_indicators

STRATEGY_CATEGORIES = {
    "ICT / Smart Money": [
        "ICT Order Blocks","ICT Fair Value Gap","ICT Liquidity Sweep",
        "ICT OTE Fibonacci","ICT BOS/CHoCH","Smart Money Concepts",
        "ICT Power of 3","ICT Breaker Block",
    ],
    "Wyckoff": [
        "Wyckoff Accumulation","Wyckoff Distribution",
        "Wyckoff Spring","Composite Man Markup","Wyckoff Test",
    ],
    "Institutional / Wall Street": [
        "Turtle Trading (20/10)","Turtle Trading (55/20)",
        "Larry Williams %R","Triple Screen Elder",
        "VWAP Institutional","Opening Range Breakout",
        "Dark Pool Accumulation","Goldman Sachs Momentum",
        "Mean Reversion (Z-Score)","Donchian Breakout",
    ],
    "Trend Following": [
        "EMA Cross (9/21)","EMA Cross (21/50)","EMA Cross (50/200)",
        "Triple EMA Alignment","MACD Crossover","MACD Zero Cross",
        "ADX Trend Filter","Supertrend","Parabolic SAR Trend",
        "Hull MA Trend","Ichimoku Kumo Breakout","HMA + RSI",
    ],
    "Momentum": [
        "RSI Oversold/Overbought","RSI Divergence","Stochastic Cross",
        "Stochastic RSI","Williams %R Reversal","CCI Breakout",
        "Awesome Oscillator","Momentum Breakout","ROC Momentum",
        "Dual RSI (7/21)","RSI + EMA Filter","MACD + RSI Combined",
    ],
    "Volatility / Squeeze": [
        "Bollinger Band Bounce","Bollinger Band Breakout",
        "Bollinger Squeeze Breakout","Keltner Breakout",
        "BB + KC Squeeze (Lazybear)","ATR Breakout","Volatility Expansion",
        "Donchian Channel Breakout","Volatility Contraction Pattern",
    ],
    "Volume": [
        "Volume Surge Breakout","OBV Trend","Chaikin Money Flow",
        "Force Index","Accumulation/Distribution","Volume RSI",
        "VWAP Deviation Bounce","Volume Profile Breakout",
    ],
    "Price Action": [
        "Higher High Higher Low","Lower High Lower Low",
        "Support/Resistance Breakout","Inside Bar Breakout",
        "Pin Bar Reversal","Engulfing Pattern","Doji Reversal",
        "Three White Soldiers","Three Black Crows",
        "Morning Star","Evening Star","Hammer/Shooting Star",
    ],
    "Scalping": [
        "EMA Ribbon Scalp (5/9/13)","Stoch + EMA Scalp",
        "RSI + BB Scalp","MACD Fast (8/17/9)",
        "Momentum Scalp (ROC)","Volume Spike Scalp",
        "Bollinger Band Walk","EMA Bounce Scalp",
    ],
    "Multi-Indicator": [
        "Triple Confirmation (RSI+MACD+EMA)","Four Factor Signal",
        "Trend + Momentum + Volume","Full Signal Stack",
        "Conservative High-Confidence","Aggressive All-Signal",
    ],
}

ALL_STRATEGIES = [s for cats in STRATEGY_CATEGORIES.values() for s in cats]

STRATEGY_DESC = {
    # ICT
    "ICT Order Blocks":        "Last bearish/bullish candle before impulse move. Enter on return to OB zone.",
    "ICT Fair Value Gap":      "3-candle imbalance (FVG). Buy/sell when price returns to fill the gap.",
    "ICT Liquidity Sweep":     "Price sweeps above highs or below lows (stop hunt) then reverses sharply.",
    "ICT OTE Fibonacci":       "Optimal Trade Entry at 62-79% Fibonacci retracement of confirmed swing.",
    "ICT BOS/CHoCH":           "Break of Structure or Change of Character — structural shift signal.",
    "Smart Money Concepts":    "Combines BOS, order blocks and liquidity zones for institutional entries.",
    "ICT Power of 3":          "Accumulation, manipulation, distribution — 3-phase daily cycle.",
    "ICT Breaker Block":       "Failed order block that flips role — strong continuation signal.",
    # Wyckoff
    "Wyckoff Accumulation":    "Spring + low volume + sign of strength. Institutional bottom formation.",
    "Wyckoff Distribution":    "UTAD + high volume rejection. Institutional top formation.",
    "Wyckoff Spring":          "False break below support on low volume — buy the reversal.",
    "Composite Man Markup":    "Breakout of accumulation range on expanding volume.",
    "Wyckoff Test":            "Secondary test of spring on decreasing volume — final confirmation.",
    # Institutional
    "Turtle Trading (20/10)":  "Richard Dennis original: buy 20-day high, sell 10-day low.",
    "Turtle Trading (55/20)":  "Turtle System 2: buy 55-day high, exit on 20-day low.",
    "Larry Williams %R":       "Williams %R crosses from extreme oversold/overbought zone.",
    "Triple Screen Elder":     "Weekly trend + daily pullback + intraday entry filter.",
    "VWAP Institutional":      "Buy VWAP pullback in uptrend, sell VWAP rejection in downtrend.",
    "Opening Range Breakout":  "Buy above OR high, sell below OR low — strong institutional bias.",
    "Dark Pool Accumulation":  "Flat price + rising OBV = hidden institutional accumulation.",
    "Goldman Sachs Momentum":  "12-1 month momentum factor — buy top performers, avoid laggards.",
    "Mean Reversion (Z-Score)":"Buy when Z-score < -2, sell when > +2. Statistical mean reversion.",
    "Donchian Breakout":       "Donchian channel breakout — classic trend following entry.",
    # Trend
    "EMA Cross (9/21)":        "Fast cross — good for all timeframes. Buy golden cross, sell death cross.",
    "EMA Cross (21/50)":       "Medium cross — swing trading. Buy when 21 crosses above 50.",
    "EMA Cross (50/200)":      "Golden/death cross — long-term institutional signal.",
    "Triple EMA Alignment":    "All 3 EMAs aligned (9>21>50 bull / 9<21<50 bear) = strong trend.",
    "MACD Crossover":          "Buy MACD line crosses above signal. Classic momentum entry.",
    "MACD Zero Cross":         "Buy when MACD crosses above zero. Strong trend confirmation.",
    "ADX Trend Filter":        "Trade in direction of EMA trend only when ADX > 25 (strong trend).",
    "Supertrend":              "ATR-based trend indicator. Buy/sell on direction change.",
    "Parabolic SAR Trend":     "Parabolic SAR flip — trend reversal entry with built-in stop.",
    "Hull MA Trend":           "Hull Moving Average — faster, lower lag trend signal.",
    "Ichimoku Kumo Breakout":  "Price breaks above/below Ichimoku cloud — strong trend signal.",
    "HMA + RSI":               "Hull MA direction + RSI confirmation filter.",
    # Momentum
    "RSI Oversold/Overbought": "Buy RSI < 30, sell RSI > 70. Classic mean reversion.",
    "RSI Divergence":          "Price makes new high/low but RSI does not — reversal warning.",
    "Stochastic Cross":        "Buy %K crosses above %D in oversold. Sell in overbought.",
    "Stochastic RSI":          "StochRSI %K/%D cross — more sensitive RSI-based stochastic.",
    "Williams %R Reversal":    "Buy when %R crosses from below -80. Sell from above -20.",
    "CCI Breakout":            "Buy CCI breaks above +100 from below. Sell breaks below -100.",
    "Awesome Oscillator":      "AO histogram color change from negative to positive = buy.",
    "Momentum Breakout":       "Price momentum (10-period) crosses above/below zero.",
    "ROC Momentum":            "Rate of Change crosses above/below zero — momentum shift.",
    "Dual RSI (7/21)":         "Fast RSI(7) crosses above slow RSI(21) = buy signal.",
    "RSI + EMA Filter":        "RSI signal only taken when price is above/below EMA 50.",
    "MACD + RSI Combined":     "Both MACD and RSI must agree — higher confidence signal.",
    # Volatility
    "Bollinger Band Bounce":   "Buy at lower band, sell at upper band. Mean reversion.",
    "Bollinger Band Breakout": "Buy when price closes above upper band. Momentum breakout.",
    "Bollinger Squeeze Breakout":"Buy/sell first breakout after BB squeeze (low volatility).",
    "Keltner Breakout":        "Price breaks outside Keltner Channel — volatility expansion.",
    "BB + KC Squeeze (Lazybear)":"Classic squeeze: BB inside KC = coiling. Trade the breakout.",
    "ATR Breakout":            "Price moves > 1.5x ATR from previous close — momentum entry.",
    "Volatility Expansion":    "ATR expands above 20-period average — trade direction of expansion.",
    "Donchian Channel Breakout":"New 20-period high/low — classic breakout system.",
    "Volatility Contraction Pattern":"Low ATR + inside bars = coiling. Trade the breakout.",
    # Volume
    "Volume Surge Breakout":   "Price breakout + volume 2x+ average = institutional confirmation.",
    "OBV Trend":               "OBV rising with price = confirmed uptrend. Divergence = warning.",
    "Chaikin Money Flow":      "CMF > 0.25 = strong buying. < -0.25 = strong selling.",
    "Force Index":             "Elder's force index EMA crosses zero = momentum shift.",
    "Accumulation/Distribution":"A/D line trend divergence from price = smart money signal.",
    "Volume RSI":              "Volume RSI crosses 50 — confirms momentum with volume.",
    "VWAP Deviation Bounce":   "Price deviates > 1.5% from VWAP then snaps back.",
    "Volume Profile Breakout": "High volume + breakout above resistance = institutional buy.",
    # Price Action
    "Higher High Higher Low":  "HH+HL structure confirmed = uptrend entry.",
    "Lower High Lower Low":    "LH+LL structure = downtrend, sell entries.",
    "Support/Resistance Breakout":"Price closes above resistance or below support.",
    "Inside Bar Breakout":     "Inside bar consolidation followed by range breakout.",
    "Pin Bar Reversal":        "Long wick rejection candle at key level — reversal.",
    "Engulfing Pattern":       "Bullish/bearish engulfing candle — institutional reversal.",
    "Doji Reversal":           "Doji at extreme = indecision + potential reversal.",
    "Three White Soldiers":    "3 consecutive bullish candles = strong uptrend.",
    "Three Black Crows":       "3 consecutive bearish candles = strong downtrend.",
    "Morning Star":            "3-candle bullish reversal pattern at bottoms.",
    "Evening Star":            "3-candle bearish reversal pattern at tops.",
    "Hammer/Shooting Star":    "Hammer = bullish reversal. Shooting star = bearish.",
    # Scalping
    "EMA Ribbon Scalp (5/9/13)":"All 3 fast EMAs aligned = high-probability scalp entry.",
    "Stoch + EMA Scalp":       "Stochastic cross + price above EMA = scalp entry.",
    "RSI + BB Scalp":          "RSI oversold + at BB lower band = precise scalp.",
    "MACD Fast (8/17/9)":      "Faster MACD settings for intraday scalping.",
    "Momentum Scalp (ROC)":    "ROC(5) cross zero with volume confirmation.",
    "Volume Spike Scalp":      "Volume spike 3x average + price direction = scalp.",
    "Bollinger Band Walk":     "Price walks along BB upper/lower = strong trend scalp.",
    "EMA Bounce Scalp":        "Price pulls back to EMA and bounces with volume.",
    # Multi
    "Triple Confirmation (RSI+MACD+EMA)": "RSI + MACD + EMA all agree — high confidence.",
    "Four Factor Signal":      "EMA trend + RSI momentum + MACD + Volume all aligned.",
    "Trend + Momentum + Volume":"EMA trend + RSI momentum + volume confirmation.",
    "Full Signal Stack":       "All major indicators must agree — very selective but accurate.",
    "Conservative High-Confidence":"Only trades when 5+ indicators agree — low frequency, high win rate.",
    "Aggressive All-Signal":   "Takes signal whenever any indicator fires — maximum trades.",
}

def generate_signals(df, strat):
    """Generate buy/sell signals — returns pd.Series of 1/-1/0"""
    c = df['Close'].squeeze()
    h = df['High'].squeeze()
    l = df['Low'].squeeze()
    v = df['Volume'].squeeze()
    signals = pd.Series(0, index=df.index)

    def get(col, default=None):
        if col in df.columns:
            return df[col].squeeze()
        return default

    try:
        # ── ICT / SMART MONEY ──────────────────────────────────────────────────
        if strat == "ICT Order Blocks":
            body = abs(c - df['Open'].squeeze())
            body_avg = body.rolling(10).mean()
            big = body > body_avg * 1.2
            for i in range(2, len(df)-2):
                if (df['Close'].squeeze().iloc[i-1] < df['Open'].squeeze().iloc[i-1] and
                    df['Close'].squeeze().iloc[i] > df['Open'].squeeze().iloc[i] and big.iloc[i]):
                    ob_low = df['Low'].squeeze().iloc[i-1]
                    ob_high = df['High'].squeeze().iloc[i-1]
                    for j in range(i+1, min(i+15, len(df))):
                        if ob_low <= df['Low'].squeeze().iloc[j] <= ob_high:
                            signals.iloc[j] = 1; break
                if (df['Close'].squeeze().iloc[i-1] > df['Open'].squeeze().iloc[i-1] and
                    df['Close'].squeeze().iloc[i] < df['Open'].squeeze().iloc[i] and big.iloc[i]):
                    ob_low = df['Low'].squeeze().iloc[i-1]
                    ob_high = df['High'].squeeze().iloc[i-1]
                    for j in range(i+1, min(i+15, len(df))):
                        if ob_low <= df['High'].squeeze().iloc[j] <= ob_high:
                            signals.iloc[j] = -1; break

        elif strat == "ICT Fair Value Gap":
            for i in range(1, len(df)-1):
                if h.iloc[i-1] < l.iloc[i+1]:
                    for j in range(i+2, min(i+20, len(df))):
                        if h.iloc[i-1] <= c.iloc[j] <= l.iloc[i+1]:
                            signals.iloc[j] = 1; break
                if l.iloc[i-1] > h.iloc[i+1]:
                    for j in range(i+2, min(i+20, len(df))):
                        if h.iloc[i+1] <= c.iloc[j] <= l.iloc[i-1]:
                            signals.iloc[j] = -1; break

        elif strat == "ICT Liquidity Sweep":
            ph = h.rolling(20).max().shift(1)
            pl = l.rolling(20).min().shift(1)
            signals[(l < pl) & (c > pl)] = 1
            signals[(h > ph) & (c < ph)] = -1

        elif strat == "ICT OTE Fibonacci":
            sh = h.rolling(20).max(); sl = l.rolling(20).min()
            fib618 = sh - (sh-sl)*0.618
            fib786 = sh - (sh-sl)*0.786
            trend = get('trend', pd.Series(1, index=df.index))
            signals[(c >= fib786) & (c <= fib618) & (trend > 0)] = 1
            signals[(c >= fib786) & (c <= fib618) & (trend < 0)] = -1

        elif strat in ["ICT BOS/CHoCH","Smart Money Concepts"]:
            ph = h.rolling(10).max().shift(1)
            pl = l.rolling(10).min().shift(1)
            bos_bull = (c > ph) & (c.shift(1) <= ph.shift(1))
            bos_bear = (c < pl) & (c.shift(1) >= pl.shift(1))
            signals[bos_bull] = 1; signals[bos_bear] = -1

        elif strat == "ICT Power of 3":
            # Accumulation (low vol flat), then manipulation (fake move), then distribution
            vma = v.rolling(20).mean()
            price_range = h - l; range_ma = price_range.rolling(20).mean()
            acc = (v < vma * 0.7) & (price_range < range_ma * 0.7)
            manip_bull = (l < l.rolling(20).min().shift(1)) & acc.shift(3).fillna(False)
            signals[manip_bull & (c > l.rolling(20).min().shift(1))] = 1
            signals[h > h.rolling(20).max().shift(1)] = -1

        elif strat == "ICT Breaker Block":
            swing_h = h.rolling(5).max(); swing_l = l.rolling(5).min()
            signals[(c > swing_h) & (c.shift(1) <= swing_h.shift(1))] = 1
            signals[(c < swing_l) & (c.shift(1) >= swing_l.shift(1))] = -1

        # ── WYCKOFF ────────────────────────────────────────────────────────────
        elif strat == "Wyckoff Accumulation":
            vma = v.rolling(20).mean()
            low20 = l.rolling(20).min().shift(1)
            spring = (l < low20) & (c > low20) & (v < vma)
            signals[spring] = 1
            rsi = get('rsi'); signals[rsi > 70] = -1 if rsi is not None else signals

        elif strat == "Wyckoff Distribution":
            vma = v.rolling(20).mean()
            h20 = h.rolling(20).max().shift(1)
            ut = (h > h20) & (c < h20) & (v > vma*1.3)
            signals[ut] = -1
            rsi = get('rsi')
            if rsi is not None: signals[rsi < 30] = 1

        elif strat == "Wyckoff Spring":
            vma = v.rolling(20).mean()
            low20 = l.rolling(20).min().shift(1)
            signals[(l < low20) & (c > low20) & (v < vma*0.8)] = 1
            signals[c > h.rolling(20).max().shift(1)] = -1

        elif strat == "Composite Man Markup":
            vma = v.rolling(20).mean()
            h20 = h.rolling(20).max().shift(1)
            signals[(c > h20) & (v > vma*1.5)] = 1
            rsi = get('rsi')
            if rsi is not None: signals[rsi > 75] = -1

        elif strat == "Wyckoff Test":
            vma = v.rolling(20).mean()
            low20 = l.rolling(20).min()
            signals[(l.rolling(5).min() > low20.shift(10)) & (v < vma*0.6)] = 1
            signals[h > h.rolling(20).max().shift(1)] = -1

        # ── INSTITUTIONAL ─────────────────────────────────────────────────────
        elif strat == "Turtle Trading (20/10)":
            signals[c > h.rolling(20).max().shift(1)] = 1
            signals[c < l.rolling(10).min().shift(1)] = -1

        elif strat == "Turtle Trading (55/20)":
            signals[c > h.rolling(55).max().shift(1)] = 1
            signals[c < l.rolling(20).min().shift(1)] = -1

        elif strat == "Larry Williams %R":
            wr = get('wr')
            if wr is not None:
                signals[(wr > -50) & (wr.shift(1) <= -80)] = 1
                signals[(wr < -50) & (wr.shift(1) >= -20)] = -1

        elif strat == "Triple Screen Elder":
            macd_h = get('macd_hist'); stk = get('stoch_k'); std = get('stoch_d')
            e50 = get('e50')
            if macd_h is not None and stk is not None:
                signals[(macd_h > 0) & (stk < 30) & (stk > std)] = 1
                signals[(macd_h < 0) & (stk > 70) & (stk < std)] = -1

        elif strat == "VWAP Institutional":
            vwap = get('vwap'); rsi = get('rsi'); e50 = get('e50')
            if vwap is not None and rsi is not None:
                uptrend = c > e50 if e50 is not None else pd.Series(True, index=df.index)
                signals[(c < vwap) & (rsi < 45) & uptrend] = 1
                signals[(c > vwap) & (rsi > 55) & ~uptrend] = -1

        elif strat == "Opening Range Breakout":
            orh = h.rolling(5).max(); orl = l.rolling(5).min()
            signals[c > orh.shift(5)] = 1; signals[c < orl.shift(5)] = -1

        elif strat == "Dark Pool Accumulation":
            obv = get('obv')
            if obv is not None:
                pr = h - l; pr_ma = pr.rolling(20).mean()
                signals[(pr < pr_ma*0.6) & (obv > obv.shift(5)) & (c > c.shift(3))] = 1
                signals[(pr < pr_ma*0.6) & (obv < obv.shift(5)) & (c < c.shift(3))] = -1

        elif strat == "Goldman Sachs Momentum":
            ret60 = c.pct_change(min(60, len(c)-1))
            signals[ret60 > ret60.rolling(20).mean()] = 1
            signals[ret60 < ret60.rolling(20).mean()] = -1

        elif strat == "Mean Reversion (Z-Score)":
            zscore = get('zscore', (c - c.rolling(20).mean()) / c.rolling(20).std())
            signals[zscore < -2] = 1; signals[zscore > 2] = -1

        elif strat == "Donchian Breakout":
            dc_h = get('dc_upper', h.rolling(20).max().shift(1))
            dc_l = get('dc_lower', l.rolling(20).min().shift(1))
            signals[c > dc_h] = 1; signals[c < dc_l] = -1

        # ── TREND FOLLOWING ───────────────────────────────────────────────────
        elif strat == "EMA Cross (9/21)":
            e9 = get('e9'); e21 = get('e21')
            if e9 is not None and e21 is not None:
                signals[(e9 > e21) & (e9.shift(1) <= e21.shift(1))] = 1
                signals[(e9 < e21) & (e9.shift(1) >= e21.shift(1))] = -1

        elif strat == "EMA Cross (21/50)":
            e21 = get('e21'); e50 = get('e50')
            if e21 is not None and e50 is not None:
                signals[(e21 > e50) & (e21.shift(1) <= e50.shift(1))] = 1
                signals[(e21 < e50) & (e21.shift(1) >= e50.shift(1))] = -1

        elif strat == "EMA Cross (50/200)":
            e50 = get('e50'); e200 = get('e200')
            if e50 is not None and e200 is not None:
                signals[(e50 > e200) & (e50.shift(1) <= e200.shift(1))] = 1
                signals[(e50 < e200) & (e50.shift(1) >= e200.shift(1))] = -1

        elif strat == "Triple EMA Alignment":
            e9 = get('e9'); e21 = get('e21'); e50 = get('e50')
            if e9 is not None and e21 is not None and e50 is not None:
                signals[(e9 > e21) & (e21 > e50)] = 1
                signals[(e9 < e21) & (e21 < e50)] = -1

        elif strat == "MACD Crossover":
            mc = get('macd'); ms = get('macd_sig')
            if mc is not None and ms is not None:
                signals[(mc > ms) & (mc.shift(1) <= ms.shift(1))] = 1
                signals[(mc < ms) & (mc.shift(1) >= ms.shift(1))] = -1

        elif strat == "MACD Zero Cross":
            mc = get('macd')
            if mc is not None:
                signals[(mc > 0) & (mc.shift(1) <= 0)] = 1
                signals[(mc < 0) & (mc.shift(1) >= 0)] = -1

        elif strat == "ADX Trend Filter":
            adx = get('adx'); e21 = get('e21'); e50 = get('e50')
            if adx is not None and e21 is not None and e50 is not None:
                signals[(adx > 25) & (e21 > e50)] = 1
                signals[(adx > 25) & (e21 < e50)] = -1
                signals[adx < 20] = 0

        elif strat == "Supertrend":
            atr = get('atr')
            if atr is not None:
                hl2 = (h + l) / 2; mult = 3.0
                upper = hl2 + mult*atr; lower = hl2 - mult*atr
                st = pd.Series(float(lower.iloc[0]) if not pd.isna(lower.iloc[0]) else 0, index=df.index)
                for i in range(1, len(df)):
                    if float(c.iloc[i]) > float(st.iloc[i-1]):
                        st.iloc[i] = max(float(lower.iloc[i]) if not pd.isna(lower.iloc[i]) else 0, float(st.iloc[i-1]))
                    else:
                        st.iloc[i] = min(float(upper.iloc[i]) if not pd.isna(upper.iloc[i]) else 9999, float(st.iloc[i-1]))
                signals[(c > st) & (c.shift(1) <= st.shift(1))] = 1
                signals[(c < st) & (c.shift(1) >= st.shift(1))] = -1

        elif strat == "Parabolic SAR Trend":
            psar_bull = get('psar_bull'); psar_bear = get('psar_bear')
            if psar_bull is not None:
                signals[psar_bull.notna() & psar_bull.shift(1).isna()] = 1
                signals[psar_bear.notna() & psar_bear.shift(1).isna()] = -1
            else:
                atr = get('atr')
                if atr is not None:
                    af=0.02; maf=0.2
                    sar = pd.Series(float(l.iloc[0]), index=df.index)
                    ep = pd.Series(float(h.iloc[0]), index=df.index)
                    bull = True; caf = af
                    for i in range(1, len(df)):
                        ps = float(sar.iloc[i-1])
                        if bull:
                            sar.iloc[i] = ps + caf*(float(ep.iloc[i-1])-ps)
                            if float(l.iloc[i]) < float(sar.iloc[i]):
                                bull=False; sar.iloc[i]=float(ep.iloc[i-1])
                                ep.iloc[i]=float(l.iloc[i]); caf=af
                            else:
                                ep.iloc[i]=max(float(ep.iloc[i-1]),float(h.iloc[i]))
                                if float(h.iloc[i])>float(ep.iloc[i-1]): caf=min(caf+af,maf)
                        else:
                            sar.iloc[i]=ps-caf*(ps-float(ep.iloc[i-1]))
                            if float(h.iloc[i])>float(sar.iloc[i]):
                                bull=True; sar.iloc[i]=float(ep.iloc[i-1])
                                ep.iloc[i]=float(h.iloc[i]); caf=af
                            else:
                                ep.iloc[i]=min(float(ep.iloc[i-1]),float(l.iloc[i]))
                                if float(l.iloc[i])<float(ep.iloc[i-1]): caf=min(caf+af,maf)
                    signals[(c>sar)&(c.shift(1)<=sar.shift(1))]=1
                    signals[(c<sar)&(c.shift(1)>=sar.shift(1))]=-1

        elif strat == "Hull MA Trend":
            hma = get('hma')
            if hma is not None:
                signals[(hma > hma.shift(1)) & (hma.shift(1) <= hma.shift(2))] = 1
                signals[(hma < hma.shift(1)) & (hma.shift(1) >= hma.shift(2))] = -1

        elif strat == "Ichimoku Kumo Breakout":
            ia = get('ich_a'); ib = get('ich_b')
            if ia is not None and ib is not None:
                kumo_top = pd.concat([ia, ib], axis=1).max(axis=1)
                kumo_bot = pd.concat([ia, ib], axis=1).min(axis=1)
                signals[(c > kumo_top) & (c.shift(1) <= kumo_top.shift(1))] = 1
                signals[(c < kumo_bot) & (c.shift(1) >= kumo_bot.shift(1))] = -1

        elif strat == "HMA + RSI":
            hma = get('hma'); rsi = get('rsi')
            if hma is not None and rsi is not None:
                signals[(hma > hma.shift(1)) & (rsi > 50) & (rsi < 70)] = 1
                signals[(hma < hma.shift(1)) & (rsi < 50) & (rsi > 30)] = -1

        # ── MOMENTUM ──────────────────────────────────────────────────────────
        elif strat == "RSI Oversold/Overbought":
            rsi = get('rsi')
            if rsi is not None:
                signals[rsi < 30] = 1; signals[rsi > 70] = -1

        elif strat == "RSI Divergence":
            rsi = get('rsi')
            if rsi is not None:
                price_hh = c > c.rolling(10).max().shift(1)
                rsi_lh   = rsi < rsi.rolling(10).max().shift(1)
                price_ll = c < c.rolling(10).min().shift(1)
                rsi_hl   = rsi > rsi.rolling(10).min().shift(1)
                signals[price_hh & rsi_lh] = -1
                signals[price_ll & rsi_hl] = 1

        elif strat == "Stochastic Cross":
            sk = get('stoch_k'); sd = get('stoch_d')
            if sk is not None and sd is not None:
                signals[(sk > sd) & (sk.shift(1) <= sd.shift(1)) & (sk < 25)] = 1
                signals[(sk < sd) & (sk.shift(1) >= sd.shift(1)) & (sk > 75)] = -1

        elif strat == "Stochastic RSI":
            srsi_k = get('srsi_k'); srsi_d = get('srsi_d')
            if srsi_k is not None and srsi_d is not None:
                signals[(srsi_k > srsi_d) & (srsi_k.shift(1) <= srsi_d.shift(1)) & (srsi_k < 0.3)] = 1
                signals[(srsi_k < srsi_d) & (srsi_k.shift(1) >= srsi_d.shift(1)) & (srsi_k > 0.7)] = -1

        elif strat == "Williams %R Reversal":
            wr = get('wr')
            if wr is not None:
                signals[(wr > -80) & (wr.shift(1) <= -80)] = 1
                signals[(wr < -20) & (wr.shift(1) >= -20)] = -1

        elif strat == "CCI Breakout":
            cci = get('cci')
            if cci is not None:
                signals[(cci > 100) & (cci.shift(1) <= 100)] = 1
                signals[(cci < -100) & (cci.shift(1) >= -100)] = -1

        elif strat == "Awesome Oscillator":
            ao = get('ao')
            if ao is not None:
                signals[(ao > 0) & (ao.shift(1) <= 0)] = 1
                signals[(ao < 0) & (ao.shift(1) >= 0)] = -1

        elif strat == "Momentum Breakout":
            mom = get('mom10', c - c.shift(10))
            signals[(mom > 0) & (mom.shift(1) <= 0)] = 1
            signals[(mom < 0) & (mom.shift(1) >= 0)] = -1

        elif strat == "ROC Momentum":
            roc = get('roc', c.pct_change(12)*100)
            signals[(roc > 0) & (roc.shift(1) <= 0)] = 1
            signals[(roc < 0) & (roc.shift(1) >= 0)] = -1

        elif strat == "Dual RSI (7/21)":
            rsi7 = get('rsi7'); rsi21 = get('rsi21')
            if rsi7 is not None and rsi21 is not None:
                signals[(rsi7 > rsi21) & (rsi7.shift(1) <= rsi21.shift(1))] = 1
                signals[(rsi7 < rsi21) & (rsi7.shift(1) >= rsi21.shift(1))] = -1

        elif strat == "RSI + EMA Filter":
            rsi = get('rsi'); e50 = get('e50')
            if rsi is not None and e50 is not None:
                signals[(rsi < 35) & (c > e50)] = 1
                signals[(rsi > 65) & (c < e50)] = -1

        elif strat == "MACD + RSI Combined":
            mc = get('macd'); ms = get('macd_sig'); rsi = get('rsi')
            if mc is not None and rsi is not None:
                signals[(mc > ms) & (mc.shift(1) <= ms.shift(1)) & (rsi < 60)] = 1
                signals[(mc < ms) & (mc.shift(1) >= ms.shift(1)) & (rsi > 40)] = -1

        # ── VOLATILITY ────────────────────────────────────────────────────────
        elif strat == "Bollinger Band Bounce":
            bb_u = get('bb_upper'); bb_l = get('bb_lower')
            if bb_u is not None:
                signals[c <= bb_l] = 1; signals[c >= bb_u] = -1

        elif strat == "Bollinger Band Breakout":
            bb_u = get('bb_upper'); bb_l = get('bb_lower')
            if bb_u is not None:
                signals[(c > bb_u) & (c.shift(1) <= bb_u.shift(1))] = 1
                signals[(c < bb_l) & (c.shift(1) >= bb_l.shift(1))] = -1

        elif strat == "Bollinger Squeeze Breakout":
            bb_w = get('bb_width')
            if bb_w is not None:
                sq = bb_w < bb_w.rolling(20).mean() * 0.5
                bb_u = get('bb_upper'); bb_l = get('bb_lower')
                if bb_u is not None:
                    signals[sq.shift(1) & (c > bb_u)] = 1
                    signals[sq.shift(1) & (c < bb_l)] = -1

        elif strat == "Keltner Breakout":
            kc_u = get('kc_upper'); kc_l = get('kc_lower')
            if kc_u is not None:
                signals[c > kc_u] = 1; signals[c < kc_l] = -1

        elif strat == "BB + KC Squeeze (Lazybear)":
            bb_u = get('bb_upper'); kc_u = get('kc_upper')
            bb_l = get('bb_lower'); kc_l = get('kc_lower')
            if bb_u is not None and kc_u is not None:
                squeeze = (bb_u < kc_u) & (bb_l > kc_l)
                mom = get('mom10', c - c.shift(10))
                signals[squeeze.shift(1).fillna(False) & (mom > 0) & (mom.shift(1) <= 0)] = 1
                signals[squeeze.shift(1).fillna(False) & (mom < 0) & (mom.shift(1) >= 0)] = -1

        elif strat == "ATR Breakout":
            atr = get('atr')
            if atr is not None:
                signals[c > c.shift(1) + 1.5*atr] = 1
                signals[c < c.shift(1) - 1.5*atr] = -1

        elif strat == "Volatility Expansion":
            atr = get('atr')
            if atr is not None:
                atr_ma = atr.rolling(20).mean(); e21 = get('e21')
                expanding = atr > atr_ma * 1.5
                if e21 is not None:
                    signals[expanding & (c > e21)] = 1
                    signals[expanding & (c < e21)] = -1

        elif strat == "Donchian Channel Breakout":
            dc_u = get('dc_upper', h.rolling(20).max().shift(1))
            dc_l = get('dc_lower', l.rolling(20).min().shift(1))
            signals[(c > dc_u) & (c.shift(1) <= dc_u.shift(1))] = 1
            signals[(c < dc_l) & (c.shift(1) >= dc_l.shift(1))] = -1

        elif strat == "Volatility Contraction Pattern":
            atr = get('atr')
            if atr is not None:
                low_vol = atr < atr.rolling(20).mean() * 0.7
                inside = (h < h.shift(1)) & (l > l.shift(1))
                setup = low_vol & inside
                signals[setup.shift(1) & (c > h.shift(1))] = 1
                signals[setup.shift(1) & (c < l.shift(1))] = -1

        # ── VOLUME ────────────────────────────────────────────────────────────
        elif strat == "Volume Surge Breakout":
            vma = get('vma20', v.rolling(20).mean())
            h20 = h.rolling(20).max().shift(1)
            signals[(v > vma*2) & (c > h20)] = 1
            signals[(v > vma*2) & (c.pct_change() < -0.01)] = -1

        elif strat == "OBV Trend":
            obv = get('obv')
            if obv is not None:
                obv_ma = obv.rolling(20).mean()
                signals[(obv > obv_ma) & (obv.shift(1) <= obv_ma.shift(1))] = 1
                signals[(obv < obv_ma) & (obv.shift(1) >= obv_ma.shift(1))] = -1

        elif strat == "Chaikin Money Flow":
            cmf = get('cmf')
            if cmf is not None:
                signals[(cmf > 0.15) & (cmf.shift(1) <= 0.15)] = 1
                signals[(cmf < -0.15) & (cmf.shift(1) >= -0.15)] = -1

        elif strat == "Force Index":
            fi = get('fi')
            if fi is not None:
                fi_ema = fi.ewm(span=13).mean()
                signals[(fi_ema > 0) & (fi_ema.shift(1) <= 0)] = 1
                signals[(fi_ema < 0) & (fi_ema.shift(1) >= 0)] = -1

        elif strat == "Accumulation/Distribution":
            adi = get('adi')
            if adi is not None:
                adi_ma = adi.rolling(20).mean()
                signals[(adi > adi_ma) & (adi.shift(1) <= adi_ma.shift(1))] = 1
                signals[(adi < adi_ma) & (adi.shift(1) >= adi_ma.shift(1))] = -1

        elif strat == "Volume RSI":
            from ta.momentum import RSIIndicator
            vrsi = RSIIndicator(v.astype(float), window=14).rsi()
            signals[(vrsi > 50) & (vrsi.shift(1) <= 50) & (c > c.shift(1))] = 1
            signals[(vrsi < 50) & (vrsi.shift(1) >= 50) & (c < c.shift(1))] = -1

        elif strat == "VWAP Deviation Bounce":
            vwap = get('vwap')
            if vwap is not None:
                dev = (c - vwap) / vwap * 100
                signals[(dev < -1.5) & (dev.shift(1) < -1.5) & (c > c.shift(1))] = 1
                signals[(dev > 1.5) & (dev.shift(1) > 1.5) & (c < c.shift(1))] = -1

        elif strat == "Volume Profile Breakout":
            vma = get('vma20', v.rolling(20).mean())
            h20 = h.rolling(20).max().shift(1)
            l20 = l.rolling(20).min().shift(1)
            signals[(v > vma*1.5) & (c > h20)] = 1
            signals[(v > vma*1.5) & (c < l20)] = -1

        # ── PRICE ACTION ──────────────────────────────────────────────────────
        elif strat == "Higher High Higher Low":
            sh = h.rolling(5).max(); sl = l.rolling(5).min()
            signals[(sh > sh.shift(5)) & (sl > sl.shift(5))] = 1
            signals[(sh < sh.shift(5)) & (sl < sl.shift(5))] = -1

        elif strat == "Lower High Lower Low":
            sh = h.rolling(5).max(); sl = l.rolling(5).min()
            signals[(sh < sh.shift(5)) & (sl < sl.shift(5))] = -1
            signals[(sh > sh.shift(5)) & (sl > sl.shift(5))] = 1

        elif strat == "Support/Resistance Breakout":
            h20 = h.rolling(20).max().shift(1); l20 = l.rolling(20).min().shift(1)
            signals[(c > h20) & (c.shift(1) <= h20.shift(1))] = 1
            signals[(c < l20) & (c.shift(1) >= l20.shift(1))] = -1

        elif strat == "Inside Bar Breakout":
            inside = (h < h.shift(1)) & (l > l.shift(1))
            signals[inside.shift(1) & (c > h.shift(1))] = 1
            signals[inside.shift(1) & (c < l.shift(1))] = -1

        elif strat == "Pin Bar Reversal":
            body = abs(c - df['Open'].squeeze())
            wick_up = h - pd.concat([c, df['Open'].squeeze()], axis=1).max(axis=1)
            wick_dn = pd.concat([c, df['Open'].squeeze()], axis=1).min(axis=1) - l
            pin_bull = (wick_dn > body * 2) & (wick_up < body * 0.5)
            pin_bear = (wick_up > body * 2) & (wick_dn < body * 0.5)
            signals[pin_bull] = 1; signals[pin_bear] = -1

        elif strat == "Engulfing Pattern":
            o = df['Open'].squeeze()
            bull_eng = (c > o.shift(1)) & (o < c.shift(1)) & (c.shift(1) < o.shift(1))
            bear_eng = (c < o.shift(1)) & (o > c.shift(1)) & (c.shift(1) > o.shift(1))
            signals[bull_eng] = 1; signals[bear_eng] = -1

        elif strat == "Doji Reversal":
            body = abs(c - df['Open'].squeeze()); rng = h - l
            doji = (body / (rng + 1e-10)) < 0.1
            rsi = get('rsi')
            if rsi is not None:
                signals[doji & (rsi < 35)] = 1
                signals[doji & (rsi > 65)] = -1

        elif strat == "Three White Soldiers":
            o = df['Open'].squeeze()
            bull = c > o
            signals[(bull) & (bull.shift(1)) & (bull.shift(2)) & (c > c.shift(1)) & (c.shift(1) > c.shift(2))] = 1
            bear = c < o
            signals[(bear) & (bear.shift(1)) & (bear.shift(2)) & (c < c.shift(1)) & (c.shift(1) < c.shift(2))] = -1

        elif strat == "Three Black Crows":
            o = df['Open'].squeeze()
            bear = c < o
            signals[(bear) & (bear.shift(1)) & (bear.shift(2))] = -1
            bull = c > o
            signals[(bull) & (bull.shift(1)) & (bull.shift(2))] = 1

        elif strat == "Morning Star":
            o = df['Open'].squeeze()
            body = abs(c - o); rng = h - l
            small_body = (body / (rng + 1e-10)) < 0.3
            signals[(c > o) & (c.shift(2) < o.shift(2)) & small_body.shift(1)] = 1

        elif strat == "Evening Star":
            o = df['Open'].squeeze()
            body = abs(c - o); rng = h - l
            small_body = (body / (rng + 1e-10)) < 0.3
            signals[(c < o) & (c.shift(2) > o.shift(2)) & small_body.shift(1)] = -1

        elif strat == "Hammer/Shooting Star":
            o = df['Open'].squeeze()
            body = abs(c - o)
            wick_dn = pd.concat([c, o], axis=1).min(axis=1) - l
            wick_up = h - pd.concat([c, o], axis=1).max(axis=1)
            hammer = (wick_dn > body*2) & (wick_up < body*0.5)
            shoot  = (wick_up > body*2) & (wick_dn < body*0.5)
            signals[hammer] = 1; signals[shoot] = -1

        # ── SCALPING ──────────────────────────────────────────────────────────
        elif strat == "EMA Ribbon Scalp (5/9/13)":
            e5 = get('e5'); e9 = get('e9'); e13 = get('e13')
            if e5 is not None and e9 is not None and e13 is not None:
                signals[(e5 > e9) & (e9 > e13)] = 1
                signals[(e5 < e9) & (e9 < e13)] = -1

        elif strat == "Stoch + EMA Scalp":
            sk = get('stoch_k'); sd = get('stoch_d'); e21 = get('e21')
            if sk is not None and e21 is not None:
                signals[(sk > sd) & (sk.shift(1) <= sd.shift(1)) & (c > e21)] = 1
                signals[(sk < sd) & (sk.shift(1) >= sd.shift(1)) & (c < e21)] = -1

        elif strat == "RSI + BB Scalp":
            rsi = get('rsi'); bb_l = get('bb_lower'); bb_u = get('bb_upper')
            if rsi is not None and bb_l is not None:
                signals[(rsi < 35) & (c <= bb_l)] = 1
                signals[(rsi > 65) & (c >= bb_u)] = -1

        elif strat == "MACD Fast (8/17/9)":
            mc = get('macd_f'); ms = get('macd_fs')
            if mc is not None and ms is not None:
                signals[(mc > ms) & (mc.shift(1) <= ms.shift(1))] = 1
                signals[(mc < ms) & (mc.shift(1) >= ms.shift(1))] = -1

        elif strat == "Momentum Scalp (ROC)":
            roc = get('roc5', c.pct_change(5)*100)
            vma = get('vma10', v.rolling(10).mean())
            signals[(roc > 0) & (roc.shift(1) <= 0) & (v > vma)] = 1
            signals[(roc < 0) & (roc.shift(1) >= 0) & (v > vma)] = -1

        elif strat == "Volume Spike Scalp":
            vma = get('vma10', v.rolling(10).mean())
            signals[(v > vma*3) & (c > c.shift(1))] = 1
            signals[(v > vma*3) & (c < c.shift(1))] = -1

        elif strat == "Bollinger Band Walk":
            bb_u = get('bb_upper'); bb_l = get('bb_lower'); bb_m = get('bb_mid')
            if bb_u is not None:
                walk_up = (c > bb_u) & (c.shift(1) > bb_u.shift(1))
                walk_dn = (c < bb_l) & (c.shift(1) < bb_l.shift(1))
                signals[walk_up] = 1; signals[walk_dn] = -1

        elif strat == "EMA Bounce Scalp":
            e21 = get('e21'); vma = get('vma20', v.rolling(20).mean())
            rsi = get('rsi')
            if e21 is not None and rsi is not None:
                pullback_bull = (c < e21 * 1.005) & (c > e21 * 0.995) & (rsi > 45)
                signals[pullback_bull & (c > c.shift(1)) & (v > vma)] = 1

        # ── MULTI-INDICATOR ───────────────────────────────────────────────────
        elif strat == "Triple Confirmation (RSI+MACD+EMA)":
            rsi = get('rsi'); mc = get('macd'); ms = get('macd_sig')
            e21 = get('e21'); e50 = get('e50')
            if rsi is not None and mc is not None and e21 is not None:
                signals[(rsi < 40) & (mc > ms) & (c > e21)] = 1
                signals[(rsi > 60) & (mc < ms) & (c < e21)] = -1

        elif strat == "Four Factor Signal":
            rsi = get('rsi'); mc = get('macd'); ms = get('macd_sig')
            e50 = get('e50'); vma = get('vma20', v.rolling(20).mean())
            adx = get('adx')
            if rsi is not None and mc is not None and e50 is not None:
                bull = (rsi < 50) & (mc > ms) & (c > e50) & (v > vma) & (adx > 20 if adx is not None else True)
                bear = (rsi > 50) & (mc < ms) & (c < e50) & (v > vma)
                signals[bull & ~bull.shift(1).fillna(False)] = 1
                signals[bear & ~bear.shift(1).fillna(False)] = -1

        elif strat == "Trend + Momentum + Volume":
            e50 = get('e50'); rsi = get('rsi'); vma = get('vma20', v.rolling(20).mean())
            if e50 is not None and rsi is not None:
                signals[(c > e50) & (rsi < 60) & (rsi > 40) & (v > vma)] = 1
                signals[(c < e50) & (rsi > 40) & (rsi < 60) & (v > vma)] = -1

        elif strat == "Full Signal Stack":
            rsi = get('rsi'); mc = get('macd'); ms = get('macd_sig')
            e21 = get('e21'); e50 = get('e50'); obv = get('obv')
            if all(x is not None for x in [rsi, mc, e21, e50, obv]):
                obv_rising = obv > obv.shift(5)
                full_bull = (rsi < 45) & (mc > ms) & (c > e21) & (c > e50) & obv_rising
                full_bear = (rsi > 55) & (mc < ms) & (c < e21) & (c < e50) & ~obv_rising
                signals[full_bull & ~full_bull.shift(1).fillna(False)] = 1
                signals[full_bear & ~full_bear.shift(1).fillna(False)] = -1

        elif strat == "Conservative High-Confidence":
            # 5+ indicators must agree
            score = pd.Series(0, index=df.index)
            rsi = get('rsi')
            if rsi is not None:
                score += (rsi < 40).astype(int) - (rsi > 60).astype(int)
            mc = get('macd'); ms = get('macd_sig')
            if mc is not None: score += (mc > ms).astype(int) - (mc < ms).astype(int)
            e21 = get('e21'); e50 = get('e50')
            if e21 is not None and e50 is not None:
                score += (e21 > e50).astype(int) - (e21 < e50).astype(int)
                score += (c > e50).astype(int) - (c < e50).astype(int)
            obv = get('obv')
            if obv is not None: score += (obv > obv.shift(5)).astype(int) - (obv < obv.shift(5)).astype(int)
            adx = get('adx')
            if adx is not None: score += ((adx > 25) & (score > 0)).astype(int) - ((adx > 25) & (score < 0)).astype(int)
            signals[score >= 5] = 1; signals[score <= -5] = -1

        elif strat == "Aggressive All-Signal":
            # Buy on any bullish signal, sell on any bearish
            score = pd.Series(0, index=df.index)
            rsi = get('rsi')
            if rsi is not None:
                score += (rsi < 45).astype(int) - (rsi > 55).astype(int)
            mc = get('macd'); ms = get('macd_sig')
            if mc is not None: score += (mc > ms).astype(int) - (mc < ms).astype(int)
            e9 = get('e9'); e21 = get('e21')
            if e9 is not None and e21 is not None:
                score += (e9 > e21).astype(int) - (e9 < e21).astype(int)
            sk = get('stoch_k'); sd = get('stoch_d')
            if sk is not None: score += (sk > sd).astype(int) - (sk < sd).astype(int)
            signals[score >= 2] = 1; signals[score <= -2] = -1

    except Exception as e:
        pass

    return signals

def run_backtest(df, strat, capital=10000, commission=0.001, stop_loss_pct=None, take_profit_pct=None):
    """
    Full backtest engine with commission, stop loss, take profit.
    Maximizes trades while respecting risk management.
    """
    df = df.copy()
    df = add_indicators(df)
    df.dropna(subset=['Close'], inplace=True)

    if len(df) < 10:
        return None, f"Not enough data ({len(df)} rows)"

    c = df['Close'].squeeze()
    signals = generate_signals(df, strat)

    sig_count = int((signals != 0).sum())
    if sig_count == 0:
        return None, f"No signals generated. Strategy may need more data or different timeframe."

    # ── SIMULATION ────────────────────────────────────────────────────────────
    pos = 0; cash = capital; shares = 0
    trades = []; equity_curve = []
    ep = 0; ed = None
    sl_price = None; tp_price = None

    for i in range(len(df)):
        price = float(c.iloc[i])
        sig = int(signals.iloc[i])
        date = df.index[i]

        # Check stop loss / take profit
        if pos == 1 and sl_price and price <= sl_price:
            cash = shares * price * (1 - commission)
            pnl = round(shares*(price-ep), 2)
            trades.append({'entry_date':ed,'exit_date':date,
                'entry_price':round(ep,4),'exit_price':round(price,4),
                'return':round((price-ep)/ep*100,2),'pnl':pnl,'exit_reason':'SL'})
            shares=0; pos=0; sl_price=None; tp_price=None
            continue

        if pos == 1 and tp_price and price >= tp_price:
            cash = shares * price * (1 - commission)
            pnl = round(shares*(price-ep), 2)
            trades.append({'entry_date':ed,'exit_date':date,
                'entry_price':round(ep,4),'exit_price':round(price,4),
                'return':round((price-ep)/ep*100,2),'pnl':pnl,'exit_reason':'TP'})
            shares=0; pos=0; sl_price=None; tp_price=None
            continue

        if sig == 1 and pos == 0:
            cost = cash * commission
            shares = (cash - cost) / price
            ep = price; ed = date; cash = 0; pos = 1
            if stop_loss_pct: sl_price = ep * (1 - stop_loss_pct/100)
            if take_profit_pct: tp_price = ep * (1 + take_profit_pct/100)

        elif sig == -1 and pos == 1:
            cash = shares * price * (1 - commission)
            pnl = round(shares*(price-ep), 2)
            trades.append({'entry_date':ed,'exit_date':date,
                'entry_price':round(ep,4),'exit_price':round(price,4),
                'return':round((price-ep)/ep*100,2),'pnl':pnl,'exit_reason':'Signal'})
            shares=0; pos=0; sl_price=None; tp_price=None

        equity_curve.append({'date':date,'equity':cash+shares*price})

    # Close open position at end
    if pos == 1:
        p_f = float(c.iloc[-1])
        cash = shares * p_f * (1 - commission)
        trades.append({'entry_date':ed,'exit_date':df.index[-1],
            'entry_price':round(ep,4),'exit_price':round(p_f,4),
            'return':round((p_f-ep)/ep*100,2),
            'pnl':round(shares*(p_f-ep),2),'exit_reason':'EOD'})

    if not trades:
        return None, f"{sig_count} signals but no complete buy→sell pairs. Try longer period."

    eq_df = pd.DataFrame(equity_curve).set_index('date')
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    fe = cash if pos == 0 else shares * float(c.iloc[-1])
    peak = capital; mdd = 0
    for eq in eq_df['equity']:
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100
        if dd > mdd: mdd = dd

    pf_num = sum(t['pnl'] for t in wins)
    pf_den = abs(sum(t['pnl'] for t in losses))
    pf = pf_num / pf_den if pf_den > 0 else 99.0

    # Average holding period
    holding_times = []
    for t in trades:
        try:
            td = pd.Timestamp(t['exit_date']) - pd.Timestamp(t['entry_date'])
            holding_times.append(td.total_seconds() / 3600)
        except: pass
    avg_hold = sum(holding_times)/len(holding_times) if holding_times else 0

    stats = {
        'total_return':  round((fe-capital)/capital*100, 2),
        'win_rate':      round(len(wins)/len(trades)*100, 2) if trades else 0,
        'total_trades':  len(trades),
        'winning':       len(wins),
        'losing':        len(losses),
        'avg_win':       round(sum(t['return'] for t in wins)/len(wins), 2) if wins else 0,
        'avg_loss':      round(sum(t['return'] for t in losses)/len(losses), 2) if losses else 0,
        'best_trade':    round(max(t['return'] for t in trades), 2),
        'worst_trade':   round(min(t['return'] for t in trades), 2),
        'profit_factor': round(pf, 2),
        'max_drawdown':  round(mdd, 2),
        'final_equity':  round(fe, 2),
        'initial':       capital,
        'total_pnl':     round(fe - capital, 2),
        'signals_fired': sig_count,
        'avg_hold_hrs':  round(avg_hold, 1),
        'commission_paid': round(len(trades) * capital * commission * 0.01, 2),
    }

    return {'stats': stats, 'trades': trades, 'equity': eq_df}, None

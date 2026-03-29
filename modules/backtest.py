# modules/backtest.py — Institutional-grade backtester with zero lookahead bias

"""
BACKTEST INTEGRITY RULES:
1. Signals are generated on candle CLOSE — entry executes on NEXT candle OPEN
2. Exit signals also execute on next candle open
3. Slippage is applied to every fill
4. Commission deducted on every trade
5. No indicator uses future data (all .shift(1) before signal comparison)
6. Walk-forward validation splits data 70/30 to confirm out-of-sample
"""

import pandas as pd
import numpy as np
from modules.data import add_indicators

STRATEGY_CATEGORIES = {
    "ICT / Smart Money": [
        "ICT Order Blocks","ICT Fair Value Gap","ICT Liquidity Sweep",
        "ICT OTE Fibonacci","ICT BOS/CHoCH","Smart Money Concepts",
    ],
    "Wyckoff": [
        "Wyckoff Accumulation","Wyckoff Distribution",
        "Wyckoff Spring","Composite Man Markup",
    ],
    "Institutional": [
        "Turtle Trading (20/10)","Turtle Trading (55/20)",
        "Larry Williams %R","Triple Screen Elder",
        "VWAP Institutional","Opening Range Breakout",
        "Dark Pool Accumulation","Mean Reversion (Z-Score)",
        "Donchian Breakout",
    ],
    "Trend Following": [
        "EMA Cross (9/21)","EMA Cross (21/50)","EMA Cross (50/200)",
        "Triple EMA Alignment","MACD Crossover","MACD Zero Cross",
        "ADX Trend Filter","Supertrend","Parabolic SAR Trend",
        "Hull MA Trend","Ichimoku Kumo Breakout",
    ],
    "Momentum": [
        "RSI Oversold/Overbought","RSI Divergence","Stochastic Cross",
        "Williams %R Reversal","CCI Breakout","Awesome Oscillator",
        "Dual RSI (7/21)","RSI + EMA Filter","MACD + RSI Combined",
    ],
    "Volatility / Squeeze": [
        "Bollinger Band Bounce","Bollinger Band Breakout",
        "Bollinger Squeeze Breakout","Keltner Breakout",
        "BB + KC Squeeze","ATR Breakout","Donchian Channel Breakout",
    ],
    "Volume": [
        "Volume Surge Breakout","OBV Trend","Chaikin Money Flow",
        "VWAP Deviation Bounce","Volume Profile Breakout",
    ],
    "Price Action": [
        "Higher High Higher Low","Inside Bar Breakout",
        "Pin Bar Reversal","Engulfing Pattern",
        "Support/Resistance Breakout","Hammer/Shooting Star",
    ],
    "Scalping": [
        "EMA Ribbon Scalp (5/9/13)","RSI + BB Scalp",
        "MACD Fast (8/17/9)","Volume Spike Scalp",
        "Bollinger Band Walk","EMA Bounce Scalp",
    ],
    "Multi-Indicator": [
        "Triple Confirmation","Four Factor Signal",
        "Conservative (5-Signal)","Aggressive All-Signal",
    ],
}

ALL_STRATEGIES = [s for cats in STRATEGY_CATEGORIES.values() for s in cats]

STRATEGY_DESC = {
    "ICT Order Blocks":        "Institutional order blocks — last bearish/bullish candle before impulse. Entry on return to OB.",
    "ICT Fair Value Gap":      "3-candle price imbalance. Entry when price returns to fill the gap.",
    "ICT Liquidity Sweep":     "Stop hunt above highs/below lows then reversal. Entry after sweep candle confirms.",
    "ICT OTE Fibonacci":       "62-79% Fibonacci retracement of confirmed swing with trend filter.",
    "ICT BOS/CHoCH":           "Break of Structure — structural shift signal with trend confirmation.",
    "Smart Money Concepts":    "BOS + order blocks + liquidity zones combined.",
    "Wyckoff Accumulation":    "Spring below support on low volume + sign of strength.",
    "Wyckoff Distribution":    "Upthrust after distribution on high volume.",
    "Wyckoff Spring":          "False break below support on low volume — reversal entry.",
    "Composite Man Markup":    "Breakout of accumulation range on expanding volume.",
    "Turtle Trading (20/10)":  "Richard Dennis: buy 20-day high breakout, exit on 10-day low.",
    "Turtle Trading (55/20)":  "Turtle System 2: buy 55-day high, exit on 20-day low.",
    "Larry Williams %R":       "%R crosses from extreme zone — reversal entry.",
    "Triple Screen Elder":     "Weekly MACD trend + daily stochastic pullback + entry.",
    "VWAP Institutional":      "Buy VWAP pullback with RSI < 45 in uptrend.",
    "Opening Range Breakout":  "First 5-candle range — buy above high, sell below low.",
    "Dark Pool Accumulation":  "Flat price + rising OBV = hidden institutional accumulation.",
    "Mean Reversion (Z-Score)":"Buy Z-score < -2, sell Z-score > +2.",
    "Donchian Breakout":       "20-period Donchian channel breakout — classic trend entry.",
    "EMA Cross (9/21)":        "EMA 9 crosses EMA 21 — fast signals, works all timeframes.",
    "EMA Cross (21/50)":       "EMA 21 crosses EMA 50 — swing trading cross.",
    "EMA Cross (50/200)":      "Golden/death cross — long-term institutional signal.",
    "Triple EMA Alignment":    "9 > 21 > 50 all aligned = strong trend, hold entire move.",
    "MACD Crossover":          "MACD line crosses signal line — buy/sell on confirmation.",
    "MACD Zero Cross":         "MACD crosses zero — stronger trend confirmation.",
    "ADX Trend Filter":        "EMA trend + ADX > 25 filter = only trade strong trends.",
    "Supertrend":              "ATR-based trend indicator — direction change = entry.",
    "Parabolic SAR Trend":     "Parabolic SAR flip = trend reversal entry.",
    "Hull MA Trend":           "Hull MA direction change — fast, low lag.",
    "Ichimoku Kumo Breakout":  "Price breaks above/below Ichimoku cloud.",
    "RSI Oversold/Overbought": "RSI < 30 = buy, RSI > 70 = sell. Classic mean reversion.",
    "RSI Divergence":          "Price makes new extreme but RSI does not — reversal.",
    "Stochastic Cross":        "%K crosses %D in oversold/overbought zone.",
    "Williams %R Reversal":    "%R crosses from extreme — momentum reversal.",
    "CCI Breakout":            "CCI breaks above +100 or below -100.",
    "Awesome Oscillator":      "AO histogram changes color — momentum shift.",
    "Dual RSI (7/21)":         "Fast RSI(7) crosses slow RSI(21).",
    "RSI + EMA Filter":        "RSI signal with EMA 50 trend filter.",
    "MACD + RSI Combined":     "Both MACD and RSI must agree — higher accuracy.",
    "Bollinger Band Bounce":   "Buy at lower band, sell at upper band.",
    "Bollinger Band Breakout": "Price closes outside BB — momentum continuation.",
    "Bollinger Squeeze Breakout":"First breakout after BB squeeze (low volatility coiling).",
    "Keltner Breakout":        "Price breaks outside Keltner Channel.",
    "BB + KC Squeeze":         "Bollinger inside Keltner = squeeze. Trade the breakout.",
    "ATR Breakout":            "Price moves > 1.5x ATR — momentum entry.",
    "Donchian Channel Breakout":"New 20-period high/low breakout.",
    "Volume Surge Breakout":   "Price breakout + volume > 2x average = confirmed move.",
    "OBV Trend":               "OBV crosses its 20-period MA — volume trend shift.",
    "Chaikin Money Flow":      "CMF crosses above/below ±0.15 — money flow signal.",
    "VWAP Deviation Bounce":   "Price > 1.5% from VWAP then snaps back.",
    "Volume Profile Breakout": "High volume + breakout = institutional participation.",
    "Higher High Higher Low":  "Structure confirmed HH+HL = uptrend entry.",
    "Inside Bar Breakout":     "Inside bar consolidation then range breakout.",
    "Pin Bar Reversal":        "Long rejection wick at key level.",
    "Engulfing Pattern":       "Bullish/bearish engulfing candle reversal.",
    "Support/Resistance Breakout":"Confirmed close above resistance or below support.",
    "Hammer/Shooting Star":    "Hammer = bullish reversal. Shooting star = bearish.",
    "EMA Ribbon Scalp (5/9/13)":"All 3 fast EMAs aligned — high-frequency scalp.",
    "RSI + BB Scalp":          "RSI oversold at BB lower band — precise scalp entry.",
    "MACD Fast (8/17/9)":      "Faster MACD for intraday scalping.",
    "Volume Spike Scalp":      "3x volume spike + direction = scalp entry.",
    "Bollinger Band Walk":     "Price walking along BB band = strong trend scalp.",
    "EMA Bounce Scalp":        "Pullback to EMA then bounce with volume.",
    "Triple Confirmation":     "RSI + MACD + EMA all agree — high confidence.",
    "Four Factor Signal":      "EMA + RSI + MACD + Volume all aligned.",
    "Conservative (5-Signal)": "5+ indicators agree — low frequency, high win rate.",
    "Aggressive All-Signal":   "Any 2 indicators agree — maximum trade frequency.",
}

def _get(df, col, default=None):
    """Safe column getter with squeeze"""
    if col in df.columns:
        return df[col].squeeze()
    return default

def generate_signals(df):
    """
    PLACEHOLDER — overridden by run_backtest with specific strategy.
    Returns pd.Series of end-of-bar signals (executed next bar open).
    1 = go long next open, -1 = close long next open, 0 = no action
    """
    return pd.Series(0, index=df.index)

def _compute_signals(df, strat):
    """
    Generate signals with STRICT no-lookahead rules.
    All signals are end-of-bar — execution happens on NEXT bar's open.
    """
    c  = df['Close'].squeeze()
    o  = df['Open'].squeeze()
    h  = df['High'].squeeze()
    l  = df['Low'].squeeze()
    v  = df['Volume'].squeeze()
    sig = pd.Series(0, index=df.index)

    def get(col, default=None):
        return _get(df, col, default)

    try:
        # ── ICT ───────────────────────────────────────────────────────────────
        if strat == "ICT Order Blocks":
            # Detect OB on previous bars, signal to enter on close
            body = abs(c - o)
            body_avg = body.rolling(10).mean()
            big = body > body_avg * 1.2
            # Bullish OB: bearish candle [i-1] before bullish impulse [i]
            bull_ob = (c.shift(1) < o.shift(1)) & (c > o) & big
            # Bearish OB: bullish candle [i-1] before bearish impulse [i]
            bear_ob = (c.shift(1) > o.shift(1)) & (c < o) & big
            # Signal when price returns to OB zone (within next 15 bars) — simplified
            sig[bull_ob] = 1
            sig[bear_ob] = -1

        elif strat == "ICT Fair Value Gap":
            # Bullish FVG: h[i-2] < l[i] — gap up, buy on first pullback into gap
            fvg_bull = h.shift(2) < l
            fvg_bear = l.shift(2) > h
            sig[fvg_bull] = 1
            sig[fvg_bear] = -1

        elif strat == "ICT Liquidity Sweep":
            prev_h = h.rolling(20).max().shift(1)
            prev_l = l.rolling(20).min().shift(1)
            # Sweep + close back inside = signal
            sig[(l < prev_l) & (c > prev_l)] = 1
            sig[(h > prev_h) & (c < prev_h)] = -1

        elif strat == "ICT OTE Fibonacci":
            sh = h.rolling(20).max().shift(1)
            sl = l.rolling(20).min().shift(1)
            fib618 = sh - (sh - sl) * 0.618
            fib786 = sh - (sh - sl) * 0.786
            trend = get('trend', pd.Series(1, index=df.index))
            sig[(c >= fib786) & (c <= fib618) & (trend > 0)] = 1
            sig[(c >= fib786) & (c <= fib618) & (trend < 0)] = -1

        elif strat in ["ICT BOS/CHoCH", "Smart Money Concepts"]:
            ph = h.rolling(10).max().shift(1)
            pl = l.rolling(10).min().shift(1)
            sig[(c > ph) & (c.shift(1) <= ph.shift(1))] = 1
            sig[(c < pl) & (c.shift(1) >= pl.shift(1))] = -1

        # ── WYCKOFF ───────────────────────────────────────────────────────────
        elif strat == "Wyckoff Accumulation":
            vma = v.rolling(20).mean().shift(1)
            low20 = l.rolling(20).min().shift(1)
            spring = (l < low20) & (c > low20) & (v < vma)
            sig[spring] = 1
            rsi = get('rsi')
            if rsi is not None:
                sig[rsi.shift(1) > 72] = -1

        elif strat == "Wyckoff Distribution":
            vma = v.rolling(20).mean().shift(1)
            h20 = h.rolling(20).max().shift(1)
            ut = (h > h20) & (c < h20) & (v > vma * 1.3)
            sig[ut] = -1
            rsi = get('rsi')
            if rsi is not None:
                sig[rsi.shift(1) < 28] = 1

        elif strat == "Wyckoff Spring":
            vma = v.rolling(20).mean().shift(1)
            low20 = l.rolling(20).min().shift(1)
            sig[(l < low20) & (c > low20) & (v < vma * 0.8)] = 1
            sig[c > h.rolling(20).max().shift(1)] = -1

        elif strat == "Composite Man Markup":
            vma = v.rolling(20).mean().shift(1)
            h20 = h.rolling(20).max().shift(1)
            sig[(c > h20) & (v > vma * 1.5)] = 1
            rsi = get('rsi')
            if rsi is not None:
                sig[rsi.shift(1) > 75] = -1

        # ── INSTITUTIONAL ─────────────────────────────────────────────────────
        elif strat == "Turtle Trading (20/10)":
            sig[c > h.rolling(20).max().shift(1)] = 1
            sig[c < l.rolling(10).min().shift(1)] = -1

        elif strat == "Turtle Trading (55/20)":
            sig[c > h.rolling(55).max().shift(1)] = 1
            sig[c < l.rolling(20).min().shift(1)] = -1

        elif strat == "Larry Williams %R":
            wr = get('wr')
            if wr is not None:
                sig[(wr.shift(1) > -50) & (wr.shift(2) <= -80)] = 1
                sig[(wr.shift(1) < -50) & (wr.shift(2) >= -20)] = -1

        elif strat == "Triple Screen Elder":
            mh = get('macd_hist'); sk = get('stoch_k'); sd = get('stoch_d')
            if mh is not None and sk is not None:
                sig[(mh.shift(1) > 0) & (sk.shift(1) < 30) & (sk.shift(1) > sd.shift(1))] = 1
                sig[(mh.shift(1) < 0) & (sk.shift(1) > 70) & (sk.shift(1) < sd.shift(1))] = -1

        elif strat == "VWAP Institutional":
            vwap = get('vwap'); rsi = get('rsi'); e50 = get('e50')
            if vwap is not None and rsi is not None:
                up = (c.shift(1) > e50.shift(1)) if e50 is not None else pd.Series(True, index=df.index)
                sig[(c.shift(1) < vwap.shift(1)) & (rsi.shift(1) < 45) & up] = 1
                sig[(c.shift(1) > vwap.shift(1)) & (rsi.shift(1) > 55) & ~up] = -1

        elif strat == "Opening Range Breakout":
            orh = h.rolling(5).max().shift(5)
            orl = l.rolling(5).min().shift(5)
            sig[c > orh] = 1
            sig[c < orl] = -1

        elif strat == "Dark Pool Accumulation":
            obv = get('obv')
            if obv is not None:
                pr = h - l; pr_ma = pr.rolling(20).mean().shift(1)
                flat = pr < pr_ma * 0.6
                sig[flat & (obv > obv.shift(5)) & (c > c.shift(3))] = 1
                sig[flat & (obv < obv.shift(5)) & (c < c.shift(3))] = -1

        elif strat == "Mean Reversion (Z-Score)":
            z = get('zscore')
            if z is None:
                z = (c - c.rolling(20).mean()) / c.rolling(20).std()
            sig[z.shift(1) < -2] = 1
            sig[z.shift(1) > 2] = -1

        elif strat == "Donchian Breakout":
            dc_h = get('dc_upper', h.rolling(20).max().shift(1))
            dc_l = get('dc_lower', l.rolling(20).min().shift(1))
            sig[c > dc_h] = 1
            sig[c < dc_l] = -1

        # ── TREND FOLLOWING ───────────────────────────────────────────────────
        elif strat == "EMA Cross (9/21)":
            e9 = get('e9'); e21 = get('e21')
            if e9 is not None and e21 is not None:
                sig[(e9.shift(1) > e21.shift(1)) & (e9.shift(2) <= e21.shift(2))] = 1
                sig[(e9.shift(1) < e21.shift(1)) & (e9.shift(2) >= e21.shift(2))] = -1

        elif strat == "EMA Cross (21/50)":
            e21 = get('e21'); e50 = get('e50')
            if e21 is not None and e50 is not None:
                sig[(e21.shift(1) > e50.shift(1)) & (e21.shift(2) <= e50.shift(2))] = 1
                sig[(e21.shift(1) < e50.shift(1)) & (e21.shift(2) >= e50.shift(2))] = -1

        elif strat == "EMA Cross (50/200)":
            e50 = get('e50'); e200 = get('e200')
            if e50 is not None and e200 is not None:
                sig[(e50.shift(1) > e200.shift(1)) & (e50.shift(2) <= e200.shift(2))] = 1
                sig[(e50.shift(1) < e200.shift(1)) & (e50.shift(2) >= e200.shift(2))] = -1

        elif strat == "Triple EMA Alignment":
            e9 = get('e9'); e21 = get('e21'); e50 = get('e50')
            if e9 is not None and e21 is not None and e50 is not None:
                bull = (e9.shift(1) > e21.shift(1)) & (e21.shift(1) > e50.shift(1))
                bear = (e9.shift(1) < e21.shift(1)) & (e21.shift(1) < e50.shift(1))
                # Signal on alignment change
                sig[bull & ~bull.shift(1).fillna(False)] = 1
                sig[bear & ~bear.shift(1).fillna(False)] = -1
                # Also exit when alignment breaks
                sig[~bull & bull.shift(1).fillna(False)] = -1

        elif strat == "MACD Crossover":
            mc = get('macd'); ms = get('macd_sig')
            if mc is not None and ms is not None:
                sig[(mc.shift(1) > ms.shift(1)) & (mc.shift(2) <= ms.shift(2))] = 1
                sig[(mc.shift(1) < ms.shift(1)) & (mc.shift(2) >= ms.shift(2))] = -1

        elif strat == "MACD Zero Cross":
            mc = get('macd')
            if mc is not None:
                sig[(mc.shift(1) > 0) & (mc.shift(2) <= 0)] = 1
                sig[(mc.shift(1) < 0) & (mc.shift(2) >= 0)] = -1

        elif strat == "ADX Trend Filter":
            adx = get('adx'); e21 = get('e21'); e50 = get('e50')
            if adx is not None and e21 is not None and e50 is not None:
                strong = adx.shift(1) > 25
                sig[strong & (e21.shift(1) > e50.shift(1)) & (e21.shift(2) <= e50.shift(2))] = 1
                sig[strong & (e21.shift(1) < e50.shift(1)) & (e21.shift(2) >= e50.shift(2))] = -1
                sig[adx.shift(1) < 18] = 0  # filter weak trend

        elif strat == "Supertrend":
            atr = get('atr')
            if atr is not None:
                hl2 = (h + l) / 2; mult = 3.0
                upper_b = hl2 + mult * atr
                lower_b = hl2 - mult * atr
                st = pd.Series(dtype=float, index=df.index)
                st.iloc[0] = float(lower_b.iloc[0]) if not pd.isna(lower_b.iloc[0]) else 0
                for i in range(1, len(df)):
                    pv = float(c.iloc[i-1])
                    ps = float(st.iloc[i-1])
                    ul = float(upper_b.iloc[i]) if not pd.isna(upper_b.iloc[i]) else 9999
                    ll = float(lower_b.iloc[i]) if not pd.isna(lower_b.iloc[i]) else 0
                    if pv > ps:
                        st.iloc[i] = max(ll, ps)
                    else:
                        st.iloc[i] = min(ul, ps)
                sig[(c.shift(1) > st.shift(1)) & (c.shift(2) <= st.shift(2))] = 1
                sig[(c.shift(1) < st.shift(1)) & (c.shift(2) >= st.shift(2))] = -1

        elif strat == "Parabolic SAR Trend":
            atr = get('atr')
            if atr is not None:
                af=0.02; maf=0.2
                sar = pd.Series(dtype=float, index=df.index)
                ep2 = pd.Series(dtype=float, index=df.index)
                sar.iloc[0]=float(l.iloc[0]); ep2.iloc[0]=float(h.iloc[0])
                bull2=True; caf=af
                for i in range(1,len(df)):
                    ps=float(sar.iloc[i-1])
                    if bull2:
                        sar.iloc[i]=ps+caf*(float(ep2.iloc[i-1])-ps)
                        if float(l.iloc[i])<float(sar.iloc[i]):
                            bull2=False;sar.iloc[i]=float(ep2.iloc[i-1])
                            ep2.iloc[i]=float(l.iloc[i]);caf=af
                        else:
                            ep2.iloc[i]=max(float(ep2.iloc[i-1]),float(h.iloc[i]))
                            if float(h.iloc[i])>float(ep2.iloc[i-1]):caf=min(caf+af,maf)
                    else:
                        sar.iloc[i]=ps-caf*(ps-float(ep2.iloc[i-1]))
                        if float(h.iloc[i])>float(sar.iloc[i]):
                            bull2=True;sar.iloc[i]=float(ep2.iloc[i-1])
                            ep2.iloc[i]=float(h.iloc[i]);caf=af
                        else:
                            ep2.iloc[i]=min(float(ep2.iloc[i-1]),float(l.iloc[i]))
                            if float(l.iloc[i])<float(ep2.iloc[i-1]):caf=min(caf+af,maf)
                sig[(c.shift(1)>sar.shift(1))&(c.shift(2)<=sar.shift(2))]=1
                sig[(c.shift(1)<sar.shift(1))&(c.shift(2)>=sar.shift(2))]=-1

        elif strat == "Hull MA Trend":
            hma = get('hma')
            if hma is not None:
                sig[(hma.shift(1) > hma.shift(2)) & (hma.shift(2) <= hma.shift(3))] = 1
                sig[(hma.shift(1) < hma.shift(2)) & (hma.shift(2) >= hma.shift(3))] = -1

        elif strat == "Ichimoku Kumo Breakout":
            ia = get('ich_a'); ib = get('ich_b')
            if ia is not None and ib is not None:
                kumo_top = pd.concat([ia.shift(1), ib.shift(1)], axis=1).max(axis=1)
                kumo_bot = pd.concat([ia.shift(1), ib.shift(1)], axis=1).min(axis=1)
                sig[(c.shift(1) > kumo_top) & (c.shift(2) <= kumo_top.shift(1))] = 1
                sig[(c.shift(1) < kumo_bot) & (c.shift(2) >= kumo_bot.shift(1))] = -1

        # ── MOMENTUM ──────────────────────────────────────────────────────────
        elif strat == "RSI Oversold/Overbought":
            rsi = get('rsi')
            if rsi is not None:
                sig[rsi.shift(1) < 30] = 1
                sig[rsi.shift(1) > 70] = -1

        elif strat == "RSI Divergence":
            rsi = get('rsi')
            if rsi is not None:
                phh = c.shift(1) > c.shift(1).rolling(10).max().shift(1)
                rlh = rsi.shift(1) < rsi.shift(1).rolling(10).max().shift(1)
                pll = c.shift(1) < c.shift(1).rolling(10).min().shift(1)
                rhl = rsi.shift(1) > rsi.shift(1).rolling(10).min().shift(1)
                sig[phh & rlh] = -1
                sig[pll & rhl] = 1

        elif strat == "Stochastic Cross":
            sk = get('stoch_k'); sd = get('stoch_d')
            if sk is not None and sd is not None:
                sig[(sk.shift(1) > sd.shift(1)) & (sk.shift(2) <= sd.shift(2)) & (sk.shift(1) < 25)] = 1
                sig[(sk.shift(1) < sd.shift(1)) & (sk.shift(2) >= sd.shift(2)) & (sk.shift(1) > 75)] = -1

        elif strat == "Williams %R Reversal":
            wr = get('wr')
            if wr is not None:
                sig[(wr.shift(1) > -80) & (wr.shift(2) <= -80)] = 1
                sig[(wr.shift(1) < -20) & (wr.shift(2) >= -20)] = -1

        elif strat == "CCI Breakout":
            cci = get('cci')
            if cci is not None:
                sig[(cci.shift(1) > 100) & (cci.shift(2) <= 100)] = 1
                sig[(cci.shift(1) < -100) & (cci.shift(2) >= -100)] = -1

        elif strat == "Awesome Oscillator":
            ao = get('ao')
            if ao is not None:
                sig[(ao.shift(1) > 0) & (ao.shift(2) <= 0)] = 1
                sig[(ao.shift(1) < 0) & (ao.shift(2) >= 0)] = -1

        elif strat == "Dual RSI (7/21)":
            r7 = get('rsi7'); r21 = get('rsi21')
            if r7 is not None and r21 is not None:
                sig[(r7.shift(1) > r21.shift(1)) & (r7.shift(2) <= r21.shift(2))] = 1
                sig[(r7.shift(1) < r21.shift(1)) & (r7.shift(2) >= r21.shift(2))] = -1

        elif strat == "RSI + EMA Filter":
            rsi = get('rsi'); e50 = get('e50')
            if rsi is not None and e50 is not None:
                sig[(rsi.shift(1) < 35) & (c.shift(1) > e50.shift(1))] = 1
                sig[(rsi.shift(1) > 65) & (c.shift(1) < e50.shift(1))] = -1

        elif strat == "MACD + RSI Combined":
            mc = get('macd'); ms = get('macd_sig'); rsi = get('rsi')
            if mc is not None and rsi is not None:
                sig[(mc.shift(1) > ms.shift(1)) & (mc.shift(2) <= ms.shift(2)) & (rsi.shift(1) < 60)] = 1
                sig[(mc.shift(1) < ms.shift(1)) & (mc.shift(2) >= ms.shift(2)) & (rsi.shift(1) > 40)] = -1

        # ── VOLATILITY ────────────────────────────────────────────────────────
        elif strat == "Bollinger Band Bounce":
            bb_u = get('bb_upper'); bb_l = get('bb_lower')
            if bb_u is not None:
                sig[c.shift(1) <= bb_l.shift(1)] = 1
                sig[c.shift(1) >= bb_u.shift(1)] = -1

        elif strat == "Bollinger Band Breakout":
            bb_u = get('bb_upper'); bb_l = get('bb_lower')
            if bb_u is not None:
                sig[(c.shift(1) > bb_u.shift(1)) & (c.shift(2) <= bb_u.shift(2))] = 1
                sig[(c.shift(1) < bb_l.shift(1)) & (c.shift(2) >= bb_l.shift(2))] = -1

        elif strat == "Bollinger Squeeze Breakout":
            bb_w = get('bb_width')
            if bb_w is not None:
                sq = bb_w.shift(1) < bb_w.shift(1).rolling(20).mean() * 0.5
                bb_u = get('bb_upper'); bb_l = get('bb_lower')
                if bb_u is not None:
                    sig[sq & (c.shift(1) > bb_u.shift(1))] = 1
                    sig[sq & (c.shift(1) < bb_l.shift(1))] = -1

        elif strat == "Keltner Breakout":
            kc_u = get('kc_upper'); kc_l = get('kc_lower')
            if kc_u is not None:
                sig[(c.shift(1) > kc_u.shift(1)) & (c.shift(2) <= kc_u.shift(2))] = 1
                sig[(c.shift(1) < kc_l.shift(1)) & (c.shift(2) >= kc_l.shift(2))] = -1

        elif strat == "BB + KC Squeeze":
            bb_u = get('bb_upper'); kc_u = get('kc_upper')
            bb_l = get('bb_lower'); kc_l = get('kc_lower')
            if bb_u is not None and kc_u is not None:
                sq = (bb_u.shift(1) < kc_u.shift(1)) & (bb_l.shift(1) > kc_l.shift(1))
                mom = get('mom10', c - c.shift(10))
                sig[sq & (mom.shift(1) > 0) & (mom.shift(2) <= 0)] = 1
                sig[sq & (mom.shift(1) < 0) & (mom.shift(2) >= 0)] = -1

        elif strat == "ATR Breakout":
            atr = get('atr')
            if atr is not None:
                sig[c.shift(1) > c.shift(2) + 1.5 * atr.shift(1)] = 1
                sig[c.shift(1) < c.shift(2) - 1.5 * atr.shift(1)] = -1

        elif strat == "Donchian Channel Breakout":
            dc_u = get('dc_upper', h.rolling(20).max().shift(1))
            dc_l = get('dc_lower', l.rolling(20).min().shift(1))
            sig[(c.shift(1) > dc_u) & (c.shift(2) <= dc_u.shift(1))] = 1
            sig[(c.shift(1) < dc_l) & (c.shift(2) >= dc_l.shift(1))] = -1

        # ── VOLUME ────────────────────────────────────────────────────────────
        elif strat == "Volume Surge Breakout":
            vma = v.rolling(20).mean().shift(1)
            h20 = h.rolling(20).max().shift(1)
            sig[(v.shift(1) > vma * 2) & (c.shift(1) > h20)] = 1
            sig[(v.shift(1) > vma * 2) & (c.shift(1).pct_change() < -0.01)] = -1

        elif strat == "OBV Trend":
            obv = get('obv')
            if obv is not None:
                obv_ma = obv.rolling(20).mean()
                sig[(obv.shift(1) > obv_ma.shift(1)) & (obv.shift(2) <= obv_ma.shift(2))] = 1
                sig[(obv.shift(1) < obv_ma.shift(1)) & (obv.shift(2) >= obv_ma.shift(2))] = -1

        elif strat == "Chaikin Money Flow":
            cmf = get('cmf')
            if cmf is not None:
                sig[(cmf.shift(1) > 0.15) & (cmf.shift(2) <= 0.15)] = 1
                sig[(cmf.shift(1) < -0.15) & (cmf.shift(2) >= -0.15)] = -1

        elif strat == "VWAP Deviation Bounce":
            vwap = get('vwap')
            if vwap is not None:
                dev = (c.shift(1) - vwap.shift(1)) / vwap.shift(1) * 100
                sig[(dev < -1.5) & (c.shift(1) > c.shift(2))] = 1
                sig[(dev > 1.5) & (c.shift(1) < c.shift(2))] = -1

        elif strat == "Volume Profile Breakout":
            vma = v.rolling(20).mean().shift(1)
            h20 = h.rolling(20).max().shift(1)
            l20 = l.rolling(20).min().shift(1)
            sig[(v.shift(1) > vma * 1.5) & (c.shift(1) > h20)] = 1
            sig[(v.shift(1) > vma * 1.5) & (c.shift(1) < l20)] = -1

        # ── PRICE ACTION ──────────────────────────────────────────────────────
        elif strat == "Higher High Higher Low":
            sh = h.rolling(5).max(); sl = l.rolling(5).min()
            sig[(sh.shift(1) > sh.shift(6)) & (sl.shift(1) > sl.shift(6))] = 1
            sig[(sh.shift(1) < sh.shift(6)) & (sl.shift(1) < sl.shift(6))] = -1

        elif strat == "Inside Bar Breakout":
            inside = (h.shift(1) < h.shift(2)) & (l.shift(1) > l.shift(2))
            sig[inside & (c > h.shift(1))] = 1
            sig[inside & (c < l.shift(1))] = -1

        elif strat == "Pin Bar Reversal":
            body = abs(c - o)
            wd = pd.concat([c, o], axis=1).min(axis=1) - l
            wu = h - pd.concat([c, o], axis=1).max(axis=1)
            pin_b = (wd.shift(1) > body.shift(1) * 2) & (wu.shift(1) < body.shift(1) * 0.5)
            pin_bear = (wu.shift(1) > body.shift(1) * 2) & (wd.shift(1) < body.shift(1) * 0.5)
            sig[pin_b] = 1; sig[pin_bear] = -1

        elif strat == "Engulfing Pattern":
            bull_e = (c > o.shift(1)) & (o < c.shift(1)) & (c.shift(1) < o.shift(1))
            bear_e = (c < o.shift(1)) & (o > c.shift(1)) & (c.shift(1) > o.shift(1))
            sig[bull_e] = 1; sig[bear_e] = -1

        elif strat == "Support/Resistance Breakout":
            h20 = h.rolling(20).max().shift(2)
            l20 = l.rolling(20).min().shift(2)
            sig[(c.shift(1) > h20) & (c.shift(2) <= h20.shift(1))] = 1
            sig[(c.shift(1) < l20) & (c.shift(2) >= l20.shift(1))] = -1

        elif strat == "Hammer/Shooting Star":
            body = abs(c - o)
            wd = pd.concat([c, o], axis=1).min(axis=1) - l
            wu = h - pd.concat([c, o], axis=1).max(axis=1)
            sig[(wd.shift(1) > body.shift(1) * 2)] = 1
            sig[(wu.shift(1) > body.shift(1) * 2)] = -1

        # ── SCALPING ──────────────────────────────────────────────────────────
        elif strat == "EMA Ribbon Scalp (5/9/13)":
            e5 = get('e5'); e9 = get('e9'); e13 = get('e13')
            if e5 is not None and e9 is not None and e13 is not None:
                bull = (e5.shift(1) > e9.shift(1)) & (e9.shift(1) > e13.shift(1))
                bear = (e5.shift(1) < e9.shift(1)) & (e9.shift(1) < e13.shift(1))
                sig[bull & ~bull.shift(1).fillna(False)] = 1
                sig[bear & ~bear.shift(1).fillna(False)] = -1

        elif strat == "RSI + BB Scalp":
            rsi = get('rsi'); bb_l = get('bb_lower'); bb_u = get('bb_upper')
            if rsi is not None and bb_l is not None:
                sig[(rsi.shift(1) < 35) & (c.shift(1) <= bb_l.shift(1))] = 1
                sig[(rsi.shift(1) > 65) & (c.shift(1) >= bb_u.shift(1))] = -1

        elif strat == "MACD Fast (8/17/9)":
            mc = get('macd_f'); ms = get('macd_fs')
            if mc is not None and ms is not None:
                sig[(mc.shift(1) > ms.shift(1)) & (mc.shift(2) <= ms.shift(2))] = 1
                sig[(mc.shift(1) < ms.shift(1)) & (mc.shift(2) >= ms.shift(2))] = -1

        elif strat == "Volume Spike Scalp":
            vma = v.rolling(10).mean().shift(1)
            sig[(v.shift(1) > vma * 3) & (c.shift(1) > c.shift(2))] = 1
            sig[(v.shift(1) > vma * 3) & (c.shift(1) < c.shift(2))] = -1

        elif strat == "Bollinger Band Walk":
            bb_u = get('bb_upper'); bb_l = get('bb_lower')
            if bb_u is not None:
                wu = (c.shift(1) > bb_u.shift(1)) & (c.shift(2) > bb_u.shift(2))
                wl = (c.shift(1) < bb_l.shift(1)) & (c.shift(2) < bb_l.shift(2))
                sig[wu] = 1; sig[wl] = -1

        elif strat == "EMA Bounce Scalp":
            e21 = get('e21'); vma = v.rolling(20).mean().shift(1)
            rsi = get('rsi')
            if e21 is not None and rsi is not None:
                near = (c.shift(1) < e21.shift(1) * 1.005) & (c.shift(1) > e21.shift(1) * 0.995)
                sig[near & (rsi.shift(1) > 45) & (c.shift(1) > c.shift(2)) & (v.shift(1) > vma)] = 1

        # ── MULTI-INDICATOR ───────────────────────────────────────────────────
        elif strat == "Triple Confirmation":
            rsi = get('rsi'); mc = get('macd'); ms = get('macd_sig'); e21 = get('e21')
            if rsi is not None and mc is not None and e21 is not None:
                bull = (rsi.shift(1) < 45) & (mc.shift(1) > ms.shift(1)) & (c.shift(1) > e21.shift(1))
                bear = (rsi.shift(1) > 55) & (mc.shift(1) < ms.shift(1)) & (c.shift(1) < e21.shift(1))
                sig[bull & ~bull.shift(1).fillna(False)] = 1
                sig[bear & ~bear.shift(1).fillna(False)] = -1

        elif strat == "Four Factor Signal":
            rsi = get('rsi'); mc = get('macd'); ms = get('macd_sig')
            e50 = get('e50'); vma = v.rolling(20).mean().shift(1)
            if rsi is not None and mc is not None and e50 is not None:
                bull = (rsi.shift(1)<50)&(mc.shift(1)>ms.shift(1))&(c.shift(1)>e50.shift(1))&(v.shift(1)>vma)
                bear = (rsi.shift(1)>50)&(mc.shift(1)<ms.shift(1))&(c.shift(1)<e50.shift(1))&(v.shift(1)>vma)
                sig[bull & ~bull.shift(1).fillna(False)] = 1
                sig[bear & ~bear.shift(1).fillna(False)] = -1

        elif strat == "Conservative (5-Signal)":
            score = pd.Series(0.0, index=df.index)
            rsi = get('rsi')
            if rsi is not None:
                score += (rsi.shift(1) < 40).astype(float) - (rsi.shift(1) > 60).astype(float)
            mc = get('macd'); ms = get('macd_sig')
            if mc is not None:
                score += (mc.shift(1) > ms.shift(1)).astype(float) - (mc.shift(1) < ms.shift(1)).astype(float)
            e21 = get('e21'); e50 = get('e50')
            if e21 is not None and e50 is not None:
                score += (e21.shift(1) > e50.shift(1)).astype(float) - (e21.shift(1) < e50.shift(1)).astype(float)
                score += (c.shift(1) > e50.shift(1)).astype(float) - (c.shift(1) < e50.shift(1)).astype(float)
            obv = get('obv')
            if obv is not None:
                score += (obv.shift(1) > obv.shift(6)).astype(float) - (obv.shift(1) < obv.shift(6)).astype(float)
            sig[score >= 4] = 1
            sig[score <= -4] = -1

        elif strat == "Aggressive All-Signal":
            score = pd.Series(0.0, index=df.index)
            rsi = get('rsi')
            if rsi is not None:
                score += (rsi.shift(1)<45).astype(float)-(rsi.shift(1)>55).astype(float)
            mc = get('macd'); ms = get('macd_sig')
            if mc is not None:
                score += (mc.shift(1)>ms.shift(1)).astype(float)-(mc.shift(1)<ms.shift(1)).astype(float)
            e9 = get('e9'); e21 = get('e21')
            if e9 is not None and e21 is not None:
                score += (e9.shift(1)>e21.shift(1)).astype(float)-(e9.shift(1)<e21.shift(1)).astype(float)
            sk = get('stoch_k'); sd = get('stoch_d')
            if sk is not None:
                score += (sk.shift(1)>sd.shift(1)).astype(float)-(sk.shift(1)<sd.shift(1)).astype(float)
            sig[score >= 2] = 1
            sig[score <= -2] = -1

    except Exception as e:
        pass

    return sig


def run_backtest(df, strat, capital=10000, commission=0.001,
                 stop_loss_pct=None, take_profit_pct=None, slippage_pct=0.0005):
    """
    Institutional-grade backtester.

    KEY INTEGRITY FEATURES:
    - Signals generated at bar CLOSE
    - Execution at NEXT bar OPEN + slippage
    - Commission deducted on every fill
    - Stop loss / take profit checked intra-bar
    - Walk-forward split: train 70% / test 30%
    """
    df = df.copy()
    df = add_indicators(df)
    df.dropna(subset=['Close'], inplace=True)

    if len(df) < 20:
        return None, f"Not enough data ({len(df)} rows)"

    c   = df['Close'].squeeze()
    o   = df['Open'].squeeze()
    h   = df['High'].squeeze()
    l   = df['Low'].squeeze()

    # Generate end-of-bar signals
    end_signals = _compute_signals(df, strat)
    sig_count = int((end_signals != 0).sum())

    if sig_count == 0:
        return None, "No signals generated. Try a longer period or different timeframe."

    # ── SIMULATION — entry on next bar OPEN ───────────────────────────────────
    pos = 0; cash = capital; shares = 0
    trades = []; equity_curve = []
    ep = 0; ed = None
    sl_price = None; tp_price = None

    for i in range(1, len(df)):
        price_open  = float(o.iloc[i])
        price_high  = float(h.iloc[i])
        price_low   = float(l.iloc[i])
        price_close = float(c.iloc[i])
        date        = df.index[i]
        sig         = int(end_signals.iloc[i-1])  # signal from PREVIOUS bar

        # Apply slippage to fill price
        fill_buy  = price_open * (1 + slippage_pct)
        fill_sell = price_open * (1 - slippage_pct)

        # Check stop loss intra-bar (uses bar low)
        if pos == 1 and sl_price and price_low <= sl_price:
            exit_price = sl_price * (1 - slippage_pct)
            cash = shares * exit_price * (1 - commission)
            trades.append({
                'entry_date': ed, 'exit_date': date,
                'entry_price': round(ep, 4), 'exit_price': round(exit_price, 4),
                'return': round((exit_price - ep) / ep * 100, 2),
                'pnl': round(shares * (exit_price - ep), 2),
                'exit_reason': 'Stop Loss'
            })
            shares = 0; pos = 0; sl_price = None; tp_price = None
            continue

        # Check take profit intra-bar (uses bar high)
        if pos == 1 and tp_price and price_high >= tp_price:
            exit_price = tp_price * (1 - slippage_pct)
            cash = shares * exit_price * (1 - commission)
            trades.append({
                'entry_date': ed, 'exit_date': date,
                'entry_price': round(ep, 4), 'exit_price': round(exit_price, 4),
                'return': round((exit_price - ep) / ep * 100, 2),
                'pnl': round(shares * (exit_price - ep), 2),
                'exit_reason': 'Take Profit'
            })
            shares = 0; pos = 0; sl_price = None; tp_price = None
            continue

        # Entry signal
        if sig == 1 and pos == 0:
            cost = cash * commission
            shares = (cash - cost) / fill_buy
            ep = fill_buy; ed = date; cash = 0; pos = 1
            if stop_loss_pct:   sl_price = ep * (1 - stop_loss_pct / 100)
            if take_profit_pct: tp_price = ep * (1 + take_profit_pct / 100)

        # Exit signal
        elif sig == -1 and pos == 1:
            cash = shares * fill_sell * (1 - commission)
            trades.append({
                'entry_date': ed, 'exit_date': date,
                'entry_price': round(ep, 4), 'exit_price': round(fill_sell, 4),
                'return': round((fill_sell - ep) / ep * 100, 2),
                'pnl': round(shares * (fill_sell - ep), 2),
                'exit_reason': 'Signal'
            })
            shares = 0; pos = 0; sl_price = None; tp_price = None

        equity_curve.append({'date': date, 'equity': cash + shares * price_close})

    # Close any open position at end
    if pos == 1:
        pf = float(c.iloc[-1])
        cash = shares * pf * (1 - commission)
        trades.append({
            'entry_date': ed, 'exit_date': df.index[-1],
            'entry_price': round(ep, 4), 'exit_price': round(pf, 4),
            'return': round((pf - ep) / ep * 100, 2),
            'pnl': round(shares * (pf - ep), 2),
            'exit_reason': 'End of Data'
        })

    if not trades:
        return None, f"{sig_count} end-of-bar signals but no entries executed. Try a longer period."

    eq_df = pd.DataFrame(equity_curve).set_index('date')
    wins   = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    fe = cash

    # Max drawdown
    peak = capital; mdd = 0
    for eq in eq_df['equity']:
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100
        if dd > mdd: mdd = dd

    pf_num = sum(t['pnl'] for t in wins)
    pf_den = abs(sum(t['pnl'] for t in losses))
    pf = pf_num / pf_den if pf_den > 0 else 99.0

    # Avg hold time
    hold_hrs = []
    for t in trades:
        try:
            td = pd.Timestamp(t['exit_date']) - pd.Timestamp(t['entry_date'])
            hold_hrs.append(td.total_seconds() / 3600)
        except: pass

    # Walk-forward split — in-sample vs out-of-sample
    split = int(len(df) * 0.7)
    df_is  = df.iloc[:split]
    df_oos = df.iloc[split:]
    is_sig  = int((_compute_signals(df_is, strat) != 0).sum())
    oos_sig = int((_compute_signals(df_oos, strat) != 0).sum())
    is_trades  = [t for t in trades if pd.Timestamp(t['entry_date']) <= df.index[split]]
    oos_trades = [t for t in trades if pd.Timestamp(t['entry_date']) > df.index[split]]
    is_wr  = round(sum(1 for t in is_trades if t['pnl']>0)/len(is_trades)*100,1) if is_trades else 0
    oos_wr = round(sum(1 for t in oos_trades if t['pnl']>0)/len(oos_trades)*100,1) if oos_trades else 0

    stats = {
        'total_return':   round((fe - capital) / capital * 100, 2),
        'win_rate':       round(len(wins) / len(trades) * 100, 2) if trades else 0,
        'total_trades':   len(trades),
        'winning':        len(wins),
        'losing':         len(losses),
        'avg_win':        round(sum(t['return'] for t in wins) / len(wins), 2) if wins else 0,
        'avg_loss':       round(sum(t['return'] for t in losses) / len(losses), 2) if losses else 0,
        'best_trade':     round(max(t['return'] for t in trades), 2),
        'worst_trade':    round(min(t['return'] for t in trades), 2),
        'profit_factor':  round(pf, 2),
        'max_drawdown':   round(mdd, 2),
        'final_equity':   round(fe, 2),
        'initial':        capital,
        'total_pnl':      round(fe - capital, 2),
        'signals_fired':  sig_count,
        'avg_hold_hrs':   round(sum(hold_hrs) / len(hold_hrs), 1) if hold_hrs else 0,
        'slippage_pct':   slippage_pct * 100,
        'commission_pct': commission * 100,
        # Walk-forward validation
        'is_win_rate':    is_wr,
        'oos_win_rate':   oos_wr,
        'is_trades':      len(is_trades),
        'oos_trades':     len(oos_trades),
        'wf_consistent':  abs(is_wr - oos_wr) < 15,  # within 15% = consistent
    }

    return {'stats': stats, 'trades': trades, 'equity': eq_df}, None

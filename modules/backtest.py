# modules/backtest.py — Backtest engine and strategies

import pandas as pd
import numpy as np
from modules.data import add_indicators

STRATEGY_CATEGORIES = {
    "ICT / Smart Money": [
        "ICT Order Blocks","ICT Fair Value Gap","ICT Liquidity Sweep",
        "ICT OTE","Smart Money Concepts"],
    "Wyckoff": [
        "Wyckoff Accumulation","Wyckoff Distribution",
        "Wyckoff Spring","Composite Man Markup"],
    "Institutional": [
        "Turtle Trading","Larry Williams %R","Triple Screen Elder",
        "VWAP Institutional","Opening Range Breakout","Dark Pool Accumulation"],
    "Technical": [
        "RSI Oversold/Overbought","EMA Golden/Death Cross","MACD Crossover",
        "Bollinger Band Bounce","Stochastic Crossover","RSI+MACD Combined",
        "Breakout","Mean Reversion","Volume Surge","Bollinger Squeeze",
        "ATR Breakout","Keltner Breakout","Supertrend","Parabolic SAR"],
    "Momentum": [
        "Dual Momentum","Three MA System","Trend Exhaustion",
        "Higher High Higher Low","ADX Trend"],
}

ALL_STRATEGIES = [s for cats in STRATEGY_CATEGORIES.values() for s in cats]

STRATEGY_DESC = {
    "ICT Order Blocks":       "Last bearish candle before bullish impulse — enter on return.",
    "ICT Fair Value Gap":     "3-candle imbalance — buy/sell when price returns to fill.",
    "ICT Liquidity Sweep":    "Price sweeps above highs/below lows then reverses.",
    "ICT OTE":                "Enter at 62-79% Fibonacci retracement of confirmed swing.",
    "Smart Money Concepts":   "BOS/CHoCH structure breaks — buy after bullish BOS.",
    "Wyckoff Accumulation":   "Spring below support on low volume then sign of strength.",
    "Wyckoff Distribution":   "Upthrust after distribution on high volume — sell.",
    "Wyckoff Spring":         "False breakdown below support on low volume — buy.",
    "Composite Man Markup":   "Breakout of accumulation range on expanding volume.",
    "Turtle Trading":         "Richard Dennis: buy 20-day high, sell 10-day low.",
    "Larry Williams %R":      "Buy when %R crosses from -80 to -50.",
    "Triple Screen Elder":    "Weekly MACD + daily stochastic + intraday entry.",
    "VWAP Institutional":     "Buy pullback to VWAP with RSI<45 in uptrend.",
    "Opening Range Breakout": "Buy above first-period high, sell below low.",
    "Dark Pool Accumulation": "Flat price + rising OBV = institutional accumulation.",
    "RSI Oversold/Overbought":"Buy RSI<30, sell RSI>70.",
    "EMA Golden/Death Cross": "Buy EMA9/21 golden cross, sell death cross.",
    "MACD Crossover":         "Buy MACD cross above signal, sell below.",
    "Bollinger Band Bounce":  "Buy at lower band, sell at upper band.",
    "Stochastic Crossover":   "Buy %K cross above %D in oversold zone.",
    "RSI+MACD Combined":      "Buy RSI<40 AND positive MACD histogram.",
    "Breakout":               "Buy 20-period high breakout, sell 20-period low.",
    "Mean Reversion":         "Buy 2 std below SMA20, sell 2 std above.",
    "Volume Surge":           "Buy when volume 2x average and price rising.",
    "Bollinger Squeeze":      "Buy first breakout after BB squeeze.",
    "ATR Breakout":           "Buy when price moves 1.5x ATR above previous close.",
    "Keltner Breakout":       "Buy above upper Keltner Channel.",
    "Supertrend":             "Buy when price crosses above Supertrend line.",
    "Parabolic SAR":          "Buy when price crosses above Parabolic SAR.",
    "Dual Momentum":          "Buy top absolute and relative momentum assets.",
    "Three MA System":        "Buy when MA4>MA9>MA18 fully aligned.",
    "Trend Exhaustion":       "Sell RSI divergence — price HH but RSI LH.",
    "Higher High Higher Low": "Buy HH+HL structure, sell LL+LH.",
    "ADX Trend":              "Buy when ADX>25 and EMA9>EMA21.",
}

def run_backtest(df, strat, capital=10000):
    df = df.copy()
    df = add_indicators(df)
    df.dropna(inplace=True)
    if len(df) < 50:
        return None, f"Not enough data ({len(df)} rows). Try longer period or daily timeframe."

    c = df['Close'].squeeze()
    signals = pd.Series(0, index=df.index)

    try:
        if strat == "RSI Oversold/Overbought":
            if 'rsi' in df.columns:
                signals[df['rsi'].squeeze() < 30] = 1
                signals[df['rsi'].squeeze() > 70] = -1

        elif strat == "EMA Golden/Death Cross":
            if 'e9' in df.columns and 'e21' in df.columns:
                e9 = df['e9'].squeeze(); e21 = df['e21'].squeeze()
                signals[(e9>e21) & (e9.shift(1)<=e21.shift(1))] = 1
                signals[(e9<e21) & (e9.shift(1)>=e21.shift(1))] = -1

        elif strat == "MACD Crossover":
            if 'mc' in df.columns and 'ms' in df.columns:
                mc = df['mc'].squeeze(); ms = df['ms'].squeeze()
                signals[(mc>ms) & (mc.shift(1)<=ms.shift(1))] = 1
                signals[(mc<ms) & (mc.shift(1)>=ms.shift(1))] = -1

        elif strat == "Bollinger Band Bounce":
            if 'bbu' in df.columns:
                signals[c <= df['bbl'].squeeze()] = 1
                signals[c >= df['bbu'].squeeze()] = -1

        elif strat == "Stochastic Crossover":
            if 'stk' in df.columns:
                k = df['stk'].squeeze(); d = df['std'].squeeze()
                signals[(k>d) & (k.shift(1)<=d.shift(1)) & (k<20)] = 1
                signals[(k<d) & (k.shift(1)>=d.shift(1)) & (k>80)] = -1

        elif strat == "RSI+MACD Combined":
            if 'rsi' in df.columns and 'mh' in df.columns:
                signals[(df['rsi'].squeeze()<40) & (df['mh'].squeeze()>0)] = 1
                signals[df['rsi'].squeeze() > 60] = -1

        elif strat == "Breakout":
            h20 = df['High'].squeeze().rolling(20).max().shift(1)
            l20 = df['Low'].squeeze().rolling(20).min().shift(1)
            signals[c > h20] = 1
            signals[c < l20] = -1

        elif strat == "Mean Reversion":
            sma = c.rolling(20).mean(); std = c.rolling(20).std()
            signals[c < sma - 2*std] = 1
            signals[c > sma + 2*std] = -1

        elif strat == "Volume Surge":
            v = df['Volume'].squeeze(); vma = v.rolling(20).mean()
            signals[(v > 2*vma) & (c.pct_change() > 0)] = 1
            signals[(v > 2*vma) & (c.pct_change() < 0)] = -1

        elif strat == "Turtle Trading":
            signals[c > df['High'].squeeze().rolling(20).max().shift(1)] = 1
            signals[c < df['Low'].squeeze().rolling(10).min().shift(1)]  = -1

        elif strat == "Larry Williams %R":
            if 'wr' in df.columns:
                wr = df['wr'].squeeze()
                signals[(wr > -50) & (wr.shift(1) <= -80)] = 1
                signals[(wr < -50) & (wr.shift(1) >= -20)] = -1

        elif strat == "Triple Screen Elder":
            if 'mc' in df.columns and 'stk' in df.columns:
                bull = df['mc'].squeeze() > df['ms'].squeeze()
                signals[bull & (df['stk'].squeeze()<30) & (df['stk'].squeeze()>df['std'].squeeze())] = 1
                signals[~bull & (df['stk'].squeeze()>70) & (df['stk'].squeeze()<df['std'].squeeze())] = -1

        elif strat == "VWAP Institutional":
            if 'vwap' in df.columns and 'rsi' in df.columns:
                signals[(c < df['vwap'].squeeze()) & (df['rsi'].squeeze() < 45)] = 1
                signals[(c > df['vwap'].squeeze()) & (df['rsi'].squeeze() > 55)] = -1

        elif strat == "Opening Range Breakout":
            orh = df['High'].squeeze().rolling(5).max()
            orl = df['Low'].squeeze().rolling(5).min()
            signals[c > orh.shift(5)] = 1
            signals[c < orl.shift(5)] = -1

        elif strat == "Dark Pool Accumulation":
            if 'obv' in df.columns:
                obv = df['obv'].squeeze()
                rng = df['High'].squeeze() - df['Low'].squeeze()
                rng_ma = rng.rolling(20).mean()
                signals[(rng < rng_ma*0.6) & (obv > obv.shift(5)) & (c > c.shift(3))] = 1
                signals[(rng < rng_ma*0.6) & (obv < obv.shift(5)) & (c < c.shift(3))] = -1

        elif strat == "ICT Liquidity Sweep":
            prev_h = df['High'].squeeze().rolling(20).max().shift(1)
            prev_l = df['Low'].squeeze().rolling(20).min().shift(1)
            signals[(df['Low'].squeeze() < prev_l) & (c > prev_l)] = 1
            signals[(df['High'].squeeze() > prev_h) & (c < prev_h)] = -1

        elif strat == "ICT OTE":
            sh = df['High'].squeeze().rolling(20).max()
            sl = df['Low'].squeeze().rolling(20).min()
            fib618 = sh - (sh-sl)*0.618
            fib786 = sh - (sh-sl)*0.786
            signals[(c >= fib786) & (c <= fib618)] = 1

        elif strat == "ICT Fair Value Gap":
            h = df['High'].squeeze(); l = df['Low'].squeeze()
            for i in range(1, len(df)-1):
                if h.iloc[i-1] < l.iloc[i+1]:
                    fvg_low = h.iloc[i-1]; fvg_high = l.iloc[i+1]
                    for j in range(i+2, min(i+30, len(df))):
                        if fvg_low <= c.iloc[j] <= fvg_high:
                            signals.iloc[j] = 1; break
                if l.iloc[i-1] > h.iloc[i+1]:
                    fvg_high = l.iloc[i-1]; fvg_low = h.iloc[i+1]
                    for j in range(i+2, min(i+30, len(df))):
                        if fvg_low <= c.iloc[j] <= fvg_high:
                            signals.iloc[j] = -1; break

        elif strat == "Smart Money Concepts":
            ph = df['High'].squeeze().rolling(10).max().shift(1)
            pl = df['Low'].squeeze().rolling(10).min().shift(1)
            signals[c > ph] = 1
            signals[c < pl] = -1

        elif strat == "Wyckoff Accumulation":
            v = df['Volume'].squeeze(); vma = v.rolling(20).mean()
            low20 = df['Low'].squeeze().rolling(20).min().shift(1)
            spring = (df['Low'].squeeze() < low20) & (c > low20)
            acc = v < vma * 0.7
            signals[spring & acc.shift(1)] = 1
            if 'rsi' in df.columns:
                signals[df['rsi'].squeeze() > 70] = -1

        elif strat == "Wyckoff Distribution":
            v = df['Volume'].squeeze(); vma = v.rolling(20).mean()
            h20 = df['High'].squeeze().rolling(20).max().shift(1)
            ut = (df['High'].squeeze() > h20) & (c < h20) & (v > vma*1.3)
            signals[ut] = -1
            if 'rsi' in df.columns:
                signals[df['rsi'].squeeze() < 30] = 1

        elif strat == "Wyckoff Spring":
            v = df['Volume'].squeeze(); vma = v.rolling(20).mean()
            low20 = df['Low'].squeeze().rolling(20).min().shift(1)
            signals[(df['Low'].squeeze() < low20) & (c > low20) & (v < vma)] = 1
            signals[c > df['High'].squeeze().rolling(20).max().shift(1)] = -1

        elif strat == "Composite Man Markup":
            v = df['Volume'].squeeze(); vma = v.rolling(20).mean()
            h20 = df['High'].squeeze().rolling(20).max().shift(1)
            signals[(c > h20) & (v > vma*1.5)] = 1
            if 'rsi' in df.columns:
                signals[df['rsi'].squeeze() > 75] = -1

        elif strat == "Bollinger Squeeze":
            if 'bbw' in df.columns and 'bbu' in df.columns:
                sq = df['bbw'].squeeze() < df['bbw'].squeeze().rolling(20).mean()*0.5
                signals[sq.shift(1) & (c > df['bbu'].squeeze())] = 1
                signals[sq.shift(1) & (c < df['bbl'].squeeze())] = -1

        elif strat == "ATR Breakout":
            if 'atr' in df.columns:
                signals[c > c.shift(1) + 1.5*df['atr'].squeeze()] = 1
                signals[c < c.shift(1) - 1.5*df['atr'].squeeze()] = -1

        elif strat == "Keltner Breakout":
            if 'kcu' in df.columns:
                signals[c > df['kcu'].squeeze()] = 1
                signals[c < df['kcl'].squeeze()] = -1

        elif strat == "Supertrend":
            if 'atr' in df.columns:
                atr = df['atr'].squeeze()
                hl2 = (df['High'].squeeze() + df['Low'].squeeze()) / 2
                upper = hl2 + 3*atr; lower = hl2 - 3*atr
                st2 = pd.Series(float(lower.iloc[0]), index=df.index)
                for i in range(1, len(df)):
                    if float(c.iloc[i]) > float(st2.iloc[i-1]):
                        st2.iloc[i] = max(float(lower.iloc[i]), float(st2.iloc[i-1]))
                    else:
                        st2.iloc[i] = min(float(upper.iloc[i]), float(st2.iloc[i-1]))
                signals[(c>st2) & (c.shift(1)<=st2.shift(1))] = 1
                signals[(c<st2) & (c.shift(1)>=st2.shift(1))] = -1

        elif strat == "Parabolic SAR":
            if 'atr' in df.columns:
                af=0.02; maf=0.2
                sar = pd.Series(float(df['Low'].squeeze().iloc[0]), index=df.index)
                ep  = pd.Series(float(df['High'].squeeze().iloc[0]), index=df.index)
                bull = True; caf = af
                for i in range(1, len(df)):
                    ps = float(sar.iloc[i-1])
                    if bull:
                        sar.iloc[i] = ps + caf*(float(ep.iloc[i-1])-ps)
                        if float(df['Low'].squeeze().iloc[i]) < float(sar.iloc[i]):
                            bull=False; sar.iloc[i]=float(ep.iloc[i-1])
                            ep.iloc[i]=float(df['Low'].squeeze().iloc[i]); caf=af
                        else:
                            ep.iloc[i]=max(float(ep.iloc[i-1]),float(df['High'].squeeze().iloc[i]))
                            if float(df['High'].squeeze().iloc[i])>float(ep.iloc[i-1]):
                                caf=min(caf+af,maf)
                    else:
                        sar.iloc[i]=ps-caf*(ps-float(ep.iloc[i-1]))
                        if float(df['High'].squeeze().iloc[i])>float(sar.iloc[i]):
                            bull=True; sar.iloc[i]=float(ep.iloc[i-1])
                            ep.iloc[i]=float(df['High'].squeeze().iloc[i]); caf=af
                        else:
                            ep.iloc[i]=min(float(ep.iloc[i-1]),float(df['Low'].squeeze().iloc[i]))
                            if float(df['Low'].squeeze().iloc[i])<float(ep.iloc[i-1]):
                                caf=min(caf+af,maf)
                signals[(c>sar) & (c.shift(1)<=sar.shift(1))] = 1
                signals[(c<sar) & (c.shift(1)>=sar.shift(1))] = -1

        elif strat == "Dual Momentum":
            ret = c.pct_change(min(60, len(c)-1))
            signals[ret > ret.rolling(20).mean()] = 1
            signals[ret < ret.rolling(20).mean()] = -1

        elif strat == "Three MA System":
            ma4=c.rolling(4).mean(); ma9=c.rolling(9).mean(); ma18=c.rolling(18).mean()
            signals[(ma4>ma9) & (ma9>ma18)] = 1
            signals[(ma4<ma9) & (ma9<ma18)] = -1

        elif strat == "Trend Exhaustion":
            if 'rsi' in df.columns:
                rsi = df['rsi'].squeeze()
                signals[(c>c.rolling(10).max().shift(1)) & (rsi<rsi.rolling(10).max().shift(1))] = -1
                signals[(c<c.rolling(10).min().shift(1)) & (rsi>rsi.rolling(10).min().shift(1))] = 1

        elif strat == "Higher High Higher Low":
            sh = df['High'].squeeze().rolling(5).max()
            sl = df['Low'].squeeze().rolling(5).min()
            signals[(sh>sh.shift(5)) & (sl>sl.shift(5))] = 1
            signals[(sh<sh.shift(5)) & (sl<sl.shift(5))] = -1

        elif strat == "ADX Trend":
            if 'adx' in df.columns and 'e9' in df.columns and 'e21' in df.columns:
                adx = df['adx'].squeeze()
                signals[(adx>25) & (df['e9'].squeeze()>df['e21'].squeeze())] = 1
                signals[(adx>25) & (df['e9'].squeeze()<df['e21'].squeeze())] = -1
                signals[adx < 20] = 0

        elif strat == "ICT Order Blocks":
            body = abs(df['Close'].squeeze() - df['Open'].squeeze())
            body_avg = body.rolling(10).mean()
            big = body > body_avg * 1.2
            for i in range(2, len(df)-1):
                if (df['Close'].squeeze().iloc[i-1] < df['Open'].squeeze().iloc[i-1] and
                    df['Close'].squeeze().iloc[i] > df['Open'].squeeze().iloc[i] and big.iloc[i]):
                    ob_low = df['Low'].squeeze().iloc[i-1]
                    ob_high = df['High'].squeeze().iloc[i-1]
                    for j in range(i+1, min(i+20, len(df))):
                        if ob_low <= df['Low'].squeeze().iloc[j] <= ob_high:
                            signals.iloc[j] = 1; break

    except Exception as e:
        return None, f"Strategy error: {str(e)}"

    # Simulate trades
    pos=0; cash=capital; shares=0; trades=[]; equity_curve=[]; entry_price=0; entry_date=None
    for i in range(len(df)):
        price = float(c.iloc[i]); sig = int(signals.iloc[i]); date = df.index[i]
        if sig == 1 and pos == 0:
            shares=cash/price; entry_price=price; entry_date=date; cash=0; pos=1
        elif sig == -1 and pos == 1:
            cash = shares * price
            trades.append({
                'entry_date': entry_date, 'exit_date': date,
                'entry_price': round(entry_price,4), 'exit_price': round(price,4),
                'return': round((price-entry_price)/entry_price*100, 2),
                'pnl': round(shares*(price-entry_price), 2)
            })
            shares=0; pos=0
        equity_curve.append({'date': date, 'equity': cash + shares*price})

    if pos == 1:
        p = float(c.iloc[-1]); cash = shares * p
        trades.append({
            'entry_date': entry_date, 'exit_date': df.index[-1],
            'entry_price': round(entry_price,4), 'exit_price': round(p,4),
            'return': round((p-entry_price)/entry_price*100, 2),
            'pnl': round(shares*(p-entry_price), 2)
        })

    if not trades:
        sig_count = int((signals!=0).sum())
        return None, f"No complete trades. {sig_count} signals generated — try longer period (2 Years, 1D timeframe)."

    eq_df = pd.DataFrame(equity_curve).set_index('date')
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    fe = cash if pos==0 else shares*float(c.iloc[-1])
    peak=capital; max_dd=0
    for eq in eq_df['equity']:
        if eq > peak: peak = eq
        dd = (peak-eq)/peak*100
        if dd > max_dd: max_dd = dd
    pf = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) \
         if losses and sum(t['pnl'] for t in losses) != 0 else 99

    stats = {
        'total_return':   round((fe-capital)/capital*100, 2),
        'win_rate':       round(len(wins)/len(trades)*100, 2),
        'total_trades':   len(trades),
        'winning':        len(wins),
        'losing':         len(losses),
        'avg_win':        round(sum(t['return'] for t in wins)/len(wins), 2) if wins else 0,
        'avg_loss':       round(sum(t['return'] for t in losses)/len(losses), 2) if losses else 0,
        'profit_factor':  round(pf, 2),
        'max_drawdown':   round(max_dd, 2),
        'final_equity':   round(fe, 2),
        'initial':        capital,
    }
    return {'stats': stats, 'trades': trades, 'equity': eq_df}, None

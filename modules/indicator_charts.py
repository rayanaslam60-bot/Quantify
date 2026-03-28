# modules/indicator_charts.py — Advanced indicator charts for symbol pages

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

# ── ALL AVAILABLE CHARTS ──────────────────────────────────────────────────────
CHART_CATEGORIES = {
    "Momentum": [
        "RSI (14)", "Stochastic %K/%D", "MACD", "Williams %R",
        "Rate of Change (ROC)", "CCI (20)", "Money Flow Index (MFI)",
        "Awesome Oscillator", "Ultimate Oscillator", "Momentum (10)",
    ],
    "Trend": [
        "EMA Ribbon (9/21/50/200)", "MACD Histogram", "ADX + DI",
        "Parabolic SAR", "Supertrend", "Ichimoku Cloud",
        "Triple EMA (TEMA)", "Hull Moving Average",
    ],
    "Volatility": [
        "Bollinger Bands %B", "Bollinger Band Width", "ATR (14)",
        "Keltner Channel Width", "Historical Volatility (20)",
        "VIX-Style Volatility", "Donchian Channel Width",
    ],
    "Volume": [
        "Volume + MA", "OBV (On Balance Volume)", "Volume RSI",
        "VWAP Deviation", "Chaikin Money Flow", "Accumulation/Distribution",
        "Volume Profile (Approx)", "Force Index",
    ],
    "Price Action": [
        "Heikin Ashi", "Price vs EMA 200", "Price vs VWAP",
        "Daily Returns", "Drawdown from High", "Price Momentum",
        "Relative Strength vs SPY",
    ],
    "Statistical": [
        "Z-Score (Price)", "Correlation with SPY", "Rolling Sharpe",
        "Return Distribution", "Volatility Cone", "Beta Rolling",
    ],
}

ALL_CHARTS = [c for cats in CHART_CATEGORIES.values() for c in cats]

DEFAULT_CHARTS = ["RSI (14)", "MACD", "Volume + MA"]

def make_indicator_chart(df, chart_name, C, height=280):
    """Build any indicator chart from dataframe"""
    UP=C['UP']; DOWN=C['DOWN']; BLUE=C['BLUE']
    AMBER=C['AMBER']; PURP=C['PURP']; CYAN=C['CYAN']
    BG0=C['BG0']; BG1=C['BG1']; GRID=C['GRID']
    TXT3=C['TXT3']; TXT2=C['TXT2']

    def base(fig, title=""):
        fig.update_layout(
            paper_bgcolor=BG0, plot_bgcolor=BG1, height=height,
            font=dict(family='Space Mono', color=TXT3, size=9),
            margin=dict(l=2, r=58, t=32, b=16),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=8, color=TXT2),
                        orientation='h', y=1.08, x=0),
            hovermode='x unified',
            hoverlabel=dict(bgcolor=BG1, bordercolor=C['BOR'],
                            font=dict(family='Space Mono', size=9, color=C['TXT1'])),
            xaxis=dict(
                showgrid=True, gridcolor=GRID, gridwidth=0.4,
                tickfont=dict(size=8, color=TXT3), zeroline=False,
                rangeslider=dict(visible=False),
                showspikes=True, spikemode='across',
                spikesnap='cursor', spikethickness=0.5,
                spikecolor=TXT3, spikedash='dot',
            ),
            yaxis=dict(
                showgrid=True, gridcolor=GRID, gridwidth=0.4,
                tickfont=dict(size=8, color=TXT3), side='right', zeroline=False,
                showspikes=True, spikemode='across',
                spikethickness=0.5, spikecolor=TXT3, spikedash='dot',
            ),
            title=dict(
                text=f'<span style="font-family:Space Mono;font-size:9px;font-weight:700;color:{TXT3};letter-spacing:0.1em;text-transform:uppercase;">{title}</span>',
                x=0, y=0.98),
            dragmode='pan',
            selectdirection='h',
            modebar=dict(bgcolor='rgba(0,0,0,0)', color=TXT3),
        )
        fig.update_xaxes(fixedrange=False)
        fig.update_yaxes(fixedrange=False)
        return fig

    c = df['Close'].squeeze()
    h = df['High'].squeeze()
    l = df['Low'].squeeze()
    v = df['Volume'].squeeze()
    idx = df.index

    try:
        # ── MOMENTUM ──────────────────────────────────────────────────────────
        if chart_name == "RSI (14)":
            rsi = df.get('rsi', pd.Series(dtype=float))
            if rsi is None or (hasattr(rsi,'empty') and rsi.empty):
                from ta.momentum import RSIIndicator
                rsi = RSIIndicator(c, window=14).rsi()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=rsi.squeeze(), line=dict(color=PURP, width=1.4),
                fill='tozeroy', fillcolor='rgba(192,132,252,0.05)', name='RSI'))
            fig.add_hline(y=70, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=50, line=dict(color=TXT3, width=0.4))
            fig.add_hline(y=30, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[0,100])
            return base(fig, "RSI (14) — Relative Strength Index")

        elif chart_name == "Stochastic %K/%D":
            stk = df.get('stk'); std = df.get('std')
            if stk is None:
                from ta.momentum import StochasticOscillator
                sk = StochasticOscillator(h, l, c, window=14)
                stk = sk.stoch(); std = sk.stoch_signal()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=stk.squeeze(), line=dict(color=CYAN, width=1.3), name='%K'))
            fig.add_trace(go.Scatter(x=idx, y=std.squeeze(), line=dict(color=AMBER, width=1.3), name='%D'))
            fig.add_hline(y=80, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=20, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[0,100])
            return base(fig, "Stochastic Oscillator %K/%D")

        elif chart_name == "MACD":
            mc = df.get('mc'); ms = df.get('ms'); mh = df.get('mh')
            if mc is None:
                from ta.trend import MACD as MACDind
                m = MACDind(c); mc=m.macd(); ms=m.macd_signal(); mh=m.macd_diff()
            hist = mh.squeeze()
            bc = [UP if v>=0 else DOWN for v in hist.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=hist, marker_color=bc, name='Histogram', opacity=0.6))
            fig.add_trace(go.Scatter(x=idx, y=mc.squeeze(), line=dict(color=BLUE, width=1.3), name='MACD'))
            fig.add_trace(go.Scatter(x=idx, y=ms.squeeze(), line=dict(color=AMBER, width=1.3), name='Signal'))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "MACD (12,26,9) — Moving Average Convergence Divergence")

        elif chart_name == "Williams %R":
            wr = df.get('wr')
            if wr is None:
                from ta.momentum import WilliamsRIndicator
                wr = WilliamsRIndicator(h, l, c, lbp=14).williams_r()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=wr.squeeze(), line=dict(color=CYAN, width=1.3),
                fill='tozeroy', fillcolor='rgba(34,211,238,0.05)', name='%R'))
            fig.add_hline(y=-20, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=-80, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[-100,0])
            return base(fig, "Williams %R (14)")

        elif chart_name == "Rate of Change (ROC)":
            roc = df.get('roc', c.pct_change(12)*100)
            fig = go.Figure()
            colors = [UP if v>=0 else DOWN for v in roc.fillna(0)]
            fig.add_trace(go.Bar(x=idx, y=roc.squeeze(), marker_color=colors, name='ROC', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Rate of Change (12)")

        elif chart_name == "CCI (20)":
            cci = df.get('cci')
            if cci is None:
                from ta.trend import CCIIndicator
                cci = CCIIndicator(h, l, c, window=20).cci()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=cci.squeeze(), line=dict(color=AMBER, width=1.3),
                fill='tozeroy', fillcolor='rgba(255,171,0,0.05)', name='CCI'))
            fig.add_hline(y=100, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            fig.add_hline(y=-100, line=dict(color=UP, width=0.7, dash='dot'))
            return base(fig, "CCI (20) — Commodity Channel Index")

        elif chart_name == "Money Flow Index (MFI)":
            mfi = df.get('mfi')
            if mfi is None:
                from ta.volume import MFIIndicator
                mfi = MFIIndicator(h, l, c, v, window=14).money_flow_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=mfi.squeeze(), line=dict(color=CYAN, width=1.3),
                fill='tozeroy', fillcolor='rgba(34,211,238,0.05)', name='MFI'))
            fig.add_hline(y=80, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=20, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[0,100])
            return base(fig, "Money Flow Index (MFI 14)")

        elif chart_name == "Awesome Oscillator":
            median = (h + l) / 2
            ao = median.rolling(5).mean() - median.rolling(34).mean()
            colors = [UP if v>=0 else DOWN for v in ao.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=ao, marker_color=colors, name='AO', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Awesome Oscillator (5/34)")

        elif chart_name == "Ultimate Oscillator":
            bp = c - pd.concat([l, c.shift(1)], axis=1).min(axis=1)
            tr = pd.concat([h, c.shift(1)], axis=1).max(axis=1) - pd.concat([l, c.shift(1)], axis=1).min(axis=1)
            avg7  = bp.rolling(7).sum()  / tr.rolling(7).sum()
            avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
            avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
            uo = 100 * (4*avg7 + 2*avg14 + avg28) / 7
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=uo, line=dict(color=PURP, width=1.3),
                fill='tozeroy', fillcolor='rgba(192,132,252,0.05)', name='UO'))
            fig.add_hline(y=70, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=30, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[0,100])
            return base(fig, "Ultimate Oscillator (7/14/28)")

        elif chart_name == "Momentum (10)":
            mom = c - c.shift(10)
            colors = [UP if v>=0 else DOWN for v in mom.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=mom, marker_color=colors, name='Momentum', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Price Momentum (10)")

        # ── TREND ─────────────────────────────────────────────────────────────
        elif chart_name == "EMA Ribbon (9/21/50/200)":
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=c, line=dict(color='rgba(255,255,255,0.3)', width=0.8), name='Price'))
            for period, color, name in [(9,BLUE,'EMA9'),(21,CYAN,'EMA21'),
                                         (50,AMBER,'EMA50'),(200,'#fb7185','EMA200')]:
                ema = c.ewm(span=period).mean()
                fig.add_trace(go.Scatter(x=idx, y=ema, line=dict(color=color, width=1.2), name=name))
            return base(fig, "EMA Ribbon — 9 / 21 / 50 / 200")

        elif chart_name == "MACD Histogram":
            mh = df.get('mh', pd.Series(dtype=float))
            if hasattr(mh,'empty') and mh.empty:
                from ta.trend import MACD as MACDind
                mh = MACDind(c).macd_diff()
            hist = mh.squeeze()
            colors = [UP if v>=0 else DOWN for v in hist.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=hist, marker_color=colors, name='MACD Hist', opacity=0.8))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "MACD Histogram — Momentum Divergence")

        elif chart_name == "ADX + DI":
            adx = df.get('adx')
            if adx is None:
                from ta.trend import ADXIndicator
                adx_ind = ADXIndicator(h, l, c, window=14)
                adx = adx_ind.adx()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=adx.squeeze(), line=dict(color=AMBER, width=1.4), name='ADX'))
            fig.add_hline(y=25, line=dict(color=TXT3, width=0.7, dash='dot'))
            fig.add_hline(y=50, line=dict(color=DOWN, width=0.5, dash='dot'))
            return base(fig, "ADX (14) — Average Directional Index  |  >25 = Strong Trend")

        elif chart_name == "Ichimoku Cloud":
            period9  = (h.rolling(9).max()  + l.rolling(9).min())  / 2
            period26 = (h.rolling(26).max() + l.rolling(26).min()) / 2
            period52 = (h.rolling(52).max() + l.rolling(52).min()) / 2
            senkou_a = ((period9 + period26) / 2)
            senkou_b = period52
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=c, line=dict(color='rgba(255,255,255,0.4)', width=1), name='Price'))
            fig.add_trace(go.Scatter(x=idx, y=senkou_a, line=dict(color=UP, width=0.8), name='Senkou A', opacity=0.5))
            fig.add_trace(go.Scatter(x=idx, y=senkou_b, line=dict(color=DOWN, width=0.8), name='Senkou B',
                fill='tonexty', fillcolor='rgba(41,121,255,0.06)', opacity=0.5))
            fig.add_trace(go.Scatter(x=idx, y=period9, line=dict(color=BLUE, width=1), name='Tenkan'))
            fig.add_trace(go.Scatter(x=idx, y=period26, line=dict(color=AMBER, width=1), name='Kijun'))
            return base(fig, "Ichimoku Cloud")

        elif chart_name == "Supertrend":
            atr_val = df.get('atr')
            if atr_val is None:
                from ta.volatility import AverageTrueRange
                atr_val = AverageTrueRange(h, l, c, window=14).average_true_range()
            hl2 = (h + l) / 2
            mult = 3.0
            upper = hl2 + mult * atr_val
            lower = hl2 - mult * atr_val
            st_line = pd.Series(index=df.index, dtype=float)
            st_line.iloc[0] = float(lower.iloc[0])
            for i in range(1, len(df)):
                if float(c.iloc[i]) > float(st_line.iloc[i-1]):
                    st_line.iloc[i] = max(float(lower.iloc[i]), float(st_line.iloc[i-1]))
                else:
                    st_line.iloc[i] = min(float(upper.iloc[i]), float(st_line.iloc[i-1]))
            bull = c > st_line
            colors_st = [UP if b else DOWN for b in bull]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=c, line=dict(color='rgba(255,255,255,0.3)', width=0.8), name='Price'))
            fig.add_trace(go.Scatter(x=idx, y=st_line, mode='markers',
                marker=dict(color=colors_st, size=2), name='Supertrend'))
            return base(fig, "Supertrend (10, 3.0)")

        elif chart_name == "Hull Moving Average":
            wma1 = c.rolling(int(14/2)).mean() * 2
            wma2 = c.rolling(14).mean()
            hull = (wma1 - wma2).rolling(int(np.sqrt(14))).mean()
            colors_hma = [UP if hull.iloc[i]>hull.iloc[i-1] else DOWN for i in range(1,len(hull))]
            colors_hma = [colors_hma[0]] + colors_hma
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=hull, line=dict(color=CYAN, width=1.5), name='HMA(14)'))
            return base(fig, "Hull Moving Average (14) — Faster, Smoother Trend")

        elif chart_name == "Triple EMA (TEMA)":
            ema1 = c.ewm(span=14).mean()
            ema2 = ema1.ewm(span=14).mean()
            ema3 = ema2.ewm(span=14).mean()
            tema = 3*ema1 - 3*ema2 + ema3
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=c, line=dict(color='rgba(255,255,255,0.2)', width=0.8), name='Price'))
            fig.add_trace(go.Scatter(x=idx, y=tema, line=dict(color=AMBER, width=1.4), name='TEMA(14)'))
            return base(fig, "Triple EMA (TEMA 14) — Low Lag Trend")

        # ── VOLATILITY ────────────────────────────────────────────────────────
        elif chart_name == "Bollinger Bands %B":
            bbu = df.get('bbu'); bbl = df.get('bbl')
            if bbu is None:
                from ta.volatility import BollingerBands
                bb = BollingerBands(c, window=20)
                bbu = bb.bollinger_hband(); bbl = bb.bollinger_lband()
            pct_b = (c - bbl) / (bbu - bbl)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=pct_b, line=dict(color=BLUE, width=1.3),
                fill='tozeroy', fillcolor='rgba(41,121,255,0.05)', name='%B'))
            fig.add_hline(y=1.0, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=0.5, line=dict(color=TXT3, width=0.4))
            fig.add_hline(y=0.0, line=dict(color=UP, width=0.7, dash='dot'))
            return base(fig, "Bollinger Bands %B  |  >1 = Above Upper  |  <0 = Below Lower")

        elif chart_name == "Bollinger Band Width":
            bbw = df.get('bbw')
            if bbw is None:
                from ta.volatility import BollingerBands
                bb = BollingerBands(c, window=20)
                bbw = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=bbw.squeeze(), line=dict(color=PURP, width=1.3),
                fill='tozeroy', fillcolor='rgba(192,132,252,0.05)', name='BB Width'))
            squeeze = bbw.squeeze() < bbw.squeeze().rolling(20).mean() * 0.5
            fig.add_trace(go.Scatter(x=idx[squeeze], y=bbw.squeeze()[squeeze],
                mode='markers', marker=dict(color=AMBER, size=4), name='Squeeze'))
            return base(fig, "Bollinger Band Width — Squeeze Detection")

        elif chart_name == "ATR (14)":
            atr = df.get('atr')
            if atr is None:
                from ta.volatility import AverageTrueRange
                atr = AverageTrueRange(h, l, c, window=14).average_true_range()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=atr.squeeze(), line=dict(color=AMBER, width=1.3),
                fill='tozeroy', fillcolor='rgba(255,171,0,0.05)', name='ATR'))
            fig.add_trace(go.Scatter(x=idx, y=atr.squeeze().rolling(20).mean(),
                line=dict(color=TXT3, width=0.8, dash='dot'), name='ATR MA'))
            return base(fig, "ATR (14) — Average True Range  |  Volatility Measure")

        elif chart_name == "Historical Volatility (20)":
            hv = c.pct_change().rolling(20).std() * np.sqrt(252) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=hv, line=dict(color=CYAN, width=1.3),
                fill='tozeroy', fillcolor='rgba(34,211,238,0.05)', name='HV(20)'))
            fig.add_trace(go.Scatter(x=idx, y=hv.rolling(50).mean(),
                line=dict(color=AMBER, width=0.9, dash='dot'), name='HV MA(50)'))
            return base(fig, "Historical Volatility (20) — Annualized %")

        elif chart_name == "Keltner Channel Width":
            from ta.volatility import KeltnerChannel
            kc = KeltnerChannel(h, l, c, window=20)
            kcw = (kc.keltner_channel_hband() - kc.keltner_channel_lband()) / kc.keltner_channel_mband()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=kcw, line=dict(color=AMBER, width=1.3),
                fill='tozeroy', fillcolor='rgba(255,171,0,0.05)', name='KC Width'))
            return base(fig, "Keltner Channel Width")

        elif chart_name == "VIX-Style Volatility":
            vol = c.pct_change().rolling(10).std() * np.sqrt(252) * 100
            fig = go.Figure()
            high_vol = vol > vol.quantile(0.75)
            fig.add_trace(go.Scatter(x=idx, y=vol, line=dict(color=DOWN, width=1.3),
                fill='tozeroy', fillcolor='rgba(255,61,87,0.05)', name='Implied Vol'))
            return base(fig, "VIX-Style Volatility — Fear Gauge")

        elif chart_name == "Donchian Channel Width":
            period = 20
            dc_high = h.rolling(period).max()
            dc_low  = l.rolling(period).min()
            dc_width = (dc_high - dc_low) / c * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=dc_width, line=dict(color=PURP, width=1.3),
                fill='tozeroy', fillcolor='rgba(192,132,252,0.05)', name='DC Width %'))
            return base(fig, "Donchian Channel Width (20) — Breakout Range")

        # ── VOLUME ────────────────────────────────────────────────────────────
        elif chart_name == "Volume + MA":
            vma = v.rolling(20).mean()
            bar_colors = [DOWN if o>cl else UP for o,cl in zip(df['Open'].squeeze(), c)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=v, marker_color=bar_colors, name='Volume', opacity=0.4))
            fig.add_trace(go.Scatter(x=idx, y=vma, line=dict(color=AMBER, width=1.2), name='Vol MA(20)'))
            return base(fig, "Volume + 20-Period Moving Average")

        elif chart_name == "OBV (On Balance Volume)":
            obv = df.get('obv')
            if obv is None:
                from ta.volume import OnBalanceVolumeIndicator
                obv = OnBalanceVolumeIndicator(c, v).on_balance_volume()
            obv_s = obv.squeeze()
            obv_ma = obv_s.rolling(20).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=obv_s, line=dict(color=BLUE, width=1.3),
                fill='tozeroy', fillcolor='rgba(41,121,255,0.05)', name='OBV'))
            fig.add_trace(go.Scatter(x=idx, y=obv_ma, line=dict(color=AMBER, width=0.9, dash='dot'), name='OBV MA'))
            return base(fig, "OBV — On Balance Volume  |  Rising = Accumulation")

        elif chart_name == "Volume RSI":
            from ta.momentum import RSIIndicator
            vrsi = RSIIndicator(v.astype(float), window=14).rsi()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=vrsi, line=dict(color=CYAN, width=1.3),
                fill='tozeroy', fillcolor='rgba(34,211,238,0.05)', name='Vol RSI'))
            fig.add_hline(y=70, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=30, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[0,100])
            return base(fig, "Volume RSI (14) — Volume Momentum")

        elif chart_name == "VWAP Deviation":
            vwap = df.get('vwap')
            if vwap is None:
                from ta.volume import VolumeWeightedAveragePrice
                vwap = VolumeWeightedAveragePrice(h, l, c, v).volume_weighted_average_price()
            dev = ((c - vwap.squeeze()) / vwap.squeeze()) * 100
            colors_dev = [UP if v>=0 else DOWN for v in dev.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=dev, marker_color=colors_dev, name='VWAP Dev %', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "VWAP Deviation % — Distance from Fair Value")

        elif chart_name == "Chaikin Money Flow":
            clv = ((c - l) - (h - c)) / (h - l)
            clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
            cmf = (clv * v).rolling(20).sum() / v.rolling(20).sum()
            colors_cmf = [UP if v>=0 else DOWN for v in cmf.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=cmf, marker_color=colors_cmf, name='CMF', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            fig.add_hline(y=0.25, line=dict(color=UP, width=0.5, dash='dot'))
            fig.add_hline(y=-0.25, line=dict(color=DOWN, width=0.5, dash='dot'))
            return base(fig, "Chaikin Money Flow (20)  |  >0.25 Bullish  |  <-0.25 Bearish")

        elif chart_name == "Accumulation/Distribution":
            clv = ((c - l) - (h - c)) / (h - l)
            clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
            ad = (clv * v).cumsum()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=ad, line=dict(color=PURP, width=1.3),
                fill='tozeroy', fillcolor='rgba(192,132,252,0.05)', name='A/D'))
            return base(fig, "Accumulation/Distribution Line — Smart Money Flow")

        elif chart_name == "Force Index":
            fi = c.diff(1) * v
            fi_smooth = fi.ewm(span=13).mean()
            colors_fi = [UP if v>=0 else DOWN for v in fi_smooth.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=fi_smooth, marker_color=colors_fi, name='Force Index', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Force Index (13 EMA) — Elder's Buying/Selling Power")

        # ── PRICE ACTION ──────────────────────────────────────────────────────
        elif chart_name == "Heikin Ashi":
            ha_close = (df['Open'].squeeze() + h + l + c) / 4
            ha_open = pd.Series(index=idx, dtype=float)
            ha_open.iloc[0] = float(df['Open'].squeeze().iloc[0])
            for i in range(1, len(df)):
                ha_open.iloc[i] = (float(ha_open.iloc[i-1]) + float(ha_close.iloc[i-1])) / 2
            ha_high = pd.concat([h, ha_open, ha_close], axis=1).max(axis=1)
            ha_low  = pd.concat([l, ha_open, ha_close], axis=1).min(axis=1)
            fig = go.Figure(go.Candlestick(x=idx,
                open=ha_open, high=ha_high, low=ha_low, close=ha_close,
                increasing=dict(line=dict(color=UP, width=1), fillcolor=UP),
                decreasing=dict(line=dict(color=DOWN, width=1), fillcolor=DOWN),
                name='HA', showlegend=False))
            return base(fig, "Heikin Ashi — Smoothed Candles  |  No Wicks = Strong Trend")

        elif chart_name == "Price vs EMA 200":
            ema200 = c.ewm(span=200).mean()
            dev = ((c - ema200) / ema200) * 100
            colors_dev = [UP if v>=0 else DOWN for v in dev.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=dev, marker_color=colors_dev, name='% from EMA200', opacity=0.7))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.8))
            return base(fig, "Price Deviation from EMA 200 %  |  Reversion Signal")

        elif chart_name == "Daily Returns":
            ret = c.pct_change() * 100
            colors_ret = [UP if v>=0 else DOWN for v in ret.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=idx, y=ret, marker_color=colors_ret, name='Daily Return %', opacity=0.7))
            fig.add_trace(go.Scatter(x=idx, y=ret.rolling(20).mean(),
                line=dict(color=AMBER, width=1), name='20D Avg'))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Daily Returns %  |  20-Day Average")

        elif chart_name == "Drawdown from High":
            roll_max = c.cummax()
            dd = ((c - roll_max) / roll_max) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=dd, line=dict(color=DOWN, width=1.3),
                fill='tozeroy', fillcolor='rgba(255,61,87,0.1)', name='Drawdown %'))
            fig.add_hline(y=-10, line=dict(color=AMBER, width=0.5, dash='dot'))
            fig.add_hline(y=-20, line=dict(color=DOWN, width=0.5, dash='dot'))
            return base(fig, "Drawdown from All-Time High %  |  -10% Correction  |  -20% Bear Market")

        elif chart_name == "Price Momentum":
            mom10 = c.pct_change(10) * 100
            mom20 = c.pct_change(20) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=mom10, line=dict(color=BLUE, width=1.2), name='Momentum 10D'))
            fig.add_trace(go.Scatter(x=idx, y=mom20, line=dict(color=AMBER, width=1.2), name='Momentum 20D'))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Price Momentum — 10D vs 20D % Change")

        # ── STATISTICAL ───────────────────────────────────────────────────────
        elif chart_name == "Z-Score (Price)":
            zscore = (c - c.rolling(20).mean()) / c.rolling(20).std()
            colors_z = [UP if v<-2 else DOWN if v>2 else 'rgba(41,121,255,0.6)' for v in zscore.fillna(0)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=zscore, line=dict(color=BLUE, width=1.3),
                fill='tozeroy', fillcolor='rgba(41,121,255,0.05)', name='Z-Score'))
            fig.add_hline(y=2, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            fig.add_hline(y=-2, line=dict(color=UP, width=0.7, dash='dot'))
            return base(fig, "Z-Score (20)  |  >2 Overbought  |  <-2 Oversold  |  Mean Reversion Signal")

        elif chart_name == "Rolling Sharpe":
            ret = c.pct_change()
            roll_sharpe = (ret.rolling(60).mean() / ret.rolling(60).std()) * np.sqrt(252)
            fig = go.Figure()
            colors_sh = [UP if v>=1 else DOWN if v<0 else AMBER for v in roll_sharpe.fillna(0)]
            fig.add_trace(go.Scatter(x=idx, y=roll_sharpe, line=dict(color=CYAN, width=1.3),
                fill='tozeroy', fillcolor='rgba(34,211,238,0.05)', name='Sharpe(60)'))
            fig.add_hline(y=1, line=dict(color=UP, width=0.7, dash='dot'))
            fig.add_hline(y=0, line=dict(color=TXT3, width=0.5))
            return base(fig, "Rolling Sharpe Ratio (60D)  |  >1 = Good Risk-Adjusted Return")

        elif chart_name == "Historical Volatility (20)":
            hv = c.pct_change().rolling(20).std() * np.sqrt(252) * 100
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=hv, line=dict(color=AMBER, width=1.3),
                fill='tozeroy', fillcolor='rgba(255,171,0,0.05)', name='HV(20)'))
            fig.add_trace(go.Scatter(x=idx, y=hv.rolling(50).mean(),
                line=dict(color=PURP, width=0.9, dash='dot'), name='Long Avg'))
            return base(fig, "Historical Volatility (20) — Annualized")

        else:
            # Fallback — show RSI
            rsi = df.get('rsi', pd.Series(dtype=float))
            if hasattr(rsi,'empty') and rsi.empty:
                from ta.momentum import RSIIndicator
                rsi = RSIIndicator(c, window=14).rsi()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=idx, y=rsi.squeeze(), line=dict(color=PURP, width=1.4), name='RSI'))
            fig.add_hline(y=70, line=dict(color=DOWN, width=0.7, dash='dot'))
            fig.add_hline(y=30, line=dict(color=UP, width=0.7, dash='dot'))
            fig.update_yaxes(range=[0,100])
            return base(fig, f"{chart_name} — RSI Fallback")

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=BG0, plot_bgcolor=BG1, height=height,
            margin=dict(l=2,r=58,t=36,b=20),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text=f"Chart error: {str(e)[:80]}",
                x=0.5, y=0.5, xref='paper', yref='paper',
                font=dict(color=TXT3, size=11, family='Space Mono'), showarrow=False)])
        return fig

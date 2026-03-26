# modules/charts.py — All Plotly chart builders

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def base_layout(C, height=600, title=""):
    return dict(
        paper_bgcolor=C['BG0'], plot_bgcolor=C['BG1'], height=height,
        font=dict(family='Space Mono', color=C['TXT3'], size=10),
        margin=dict(l=2, r=58, t=40, b=20),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=9, color=C['TXT2']),
                    orientation='h', y=1.06, x=0),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=C['BG2'], bordercolor=C['BOR'],
                        font=dict(family='Space Mono', size=10, color=C['TXT1'])),
        xaxis=dict(showgrid=True, gridcolor=C['GRID'], gridwidth=0.4,
                   showline=False, tickfont=dict(size=9, color=C['TXT3']),
                   rangeslider=dict(visible=False), zeroline=False,
                   rangeselector=dict(
                       buttons=[
                           dict(count=1,  label='1D', step='day',   stepmode='backward'),
                           dict(count=5,  label='5D', step='day',   stepmode='backward'),
                           dict(count=1,  label='1M', step='month', stepmode='backward'),
                           dict(count=3,  label='3M', step='month', stepmode='backward'),
                           dict(count=6,  label='6M', step='month', stepmode='backward'),
                           dict(count=1,  label='1Y', step='year',  stepmode='backward'),
                           dict(step='all', label='All'),
                       ],
                       bgcolor=C['BG2'], activecolor=C['BLUE'],
                       font=dict(color=C['TXT2'], size=9, family='Space Mono'),
                       bordercolor=C['BOR'], borderwidth=1, x=0, y=1.02)),
        yaxis=dict(showgrid=True, gridcolor=C['GRID'], gridwidth=0.4,
                   showline=False, tickfont=dict(size=9, color=C['TXT3']),
                   side='right', zeroline=False),
        dragmode='pan',
        title=dict(
            text=f'<span style="font-family:Space Mono;font-size:11px;font-weight:700;color:{C["TXT3"]};letter-spacing:0.1em;">{title}</span>',
            x=0) if title else None,
        modebar=dict(bgcolor=C['BG0'], color=C['TXT3'], activecolor=C['BLUE']),
    )

CFG = {
    'displayModeBar': True, 'displaylogo': False,
    'modeBarButtonsToAdd': ['drawline','drawopenpath','drawclosedpath',
                             'drawcircle','drawrect','eraseshape'],
    'modeBarButtonsToRemove': ['autoScale2d','lasso2d'],
    'scrollZoom': True,
    'toImageButtonOptions': {'format':'png','filename':'quantify','height':800,'width':1800,'scale':2}
}
CFG0 = {'displayModeBar': False, 'scrollZoom': True}

def main_chart(df, ticker, tf, chart_type, show_ema, show_bb, show_kc,
               show_ichi, show_vwap, drawings, dc, dw, dd,
               show_rsi, show_macd, show_stoch, show_vol, C):
    rows = 1 + int(show_rsi) + int(show_macd) + int(show_stoch) + int(show_vol)
    rh = [0.55] + [0.15] * (rows-1)
    total = sum(rh); rh = [x/total for x in rh]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        row_heights=rh, vertical_spacing=0.008)
    c = df['Close'].squeeze()
    UP=C['UP']; DOWN=C['DOWN']

    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'].squeeze(), high=df['High'].squeeze(),
            low=df['Low'].squeeze(), close=c,
            increasing=dict(line=dict(color=UP, width=1), fillcolor=UP),
            decreasing=dict(line=dict(color=DOWN, width=1), fillcolor=DOWN),
            name='', showlegend=False), row=1, col=1)
    elif chart_type == 'OHLC':
        fig.add_trace(go.Ohlc(
            x=df.index, open=df['Open'].squeeze(), high=df['High'].squeeze(),
            low=df['Low'].squeeze(), close=c,
            increasing=dict(line=dict(color=UP)),
            decreasing=dict(line=dict(color=DOWN)),
            name='', showlegend=False), row=1, col=1)
    elif chart_type == 'Area':
        fig.add_trace(go.Scatter(x=df.index, y=c,
            line=dict(color=C['BLUE'], width=1.5), name='Price',
            fill='tozeroy', fillcolor='rgba(41,121,255,0.06)'), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(x=df.index, y=c,
            line=dict(color=C['BLUE'], width=1.5), name='Price'), row=1, col=1)

    if show_ema:
        for k,col,w,nm in [('e9',C['BLUE'],1,'EMA 9'),('e21',C['AMBER'],1,'EMA 21'),
                             ('e50',C['PURP'],1,'EMA 50'),('e200',C['ROSE'],1.5,'EMA 200')]:
            if k in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[k].squeeze(),
                    line=dict(color=col, width=w), name=nm, opacity=0.9), row=1, col=1)
    if show_bb and 'bbu' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['bbu'].squeeze(),
            line=dict(color=C['TXT3'], width=0.7, dash='dot'), name='BB', opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['bbl'].squeeze(),
            line=dict(color=C['TXT3'], width=0.7, dash='dot'), showlegend=False,
            fill='tonexty', fillcolor='rgba(41,121,255,0.03)', opacity=0.6), row=1, col=1)
    if show_kc and 'kcu' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['kcu'].squeeze(),
            line=dict(color=C['AMBER'], width=0.7, dash='dash'), name='KC', opacity=0.5), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['kcl'].squeeze(),
            line=dict(color=C['AMBER'], width=0.7, dash='dash'), showlegend=False,
            fill='tonexty', fillcolor='rgba(255,171,0,0.02)', opacity=0.5), row=1, col=1)
    if show_ichi and 'ia' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['ia'].squeeze(),
            line=dict(color=UP, width=0.5), name='Kumo A', opacity=0.35), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['ib'].squeeze(),
            line=dict(color=DOWN, width=0.5), name='Kumo B',
            fill='tonexty', fillcolor='rgba(41,121,255,0.04)',
            opacity=0.35, showlegend=False), row=1, col=1)
        if 'icl' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['icl'].squeeze(),
                line=dict(color=C['BLUE'], width=1), name='Tenkan'), row=1, col=1)
        if 'ibl' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['ibl'].squeeze(),
                line=dict(color=C['AMBER'], width=1), name='Kijun'), row=1, col=1)
    if show_vwap and 'vwap' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['vwap'].squeeze(),
            line=dict(color=C['CYAN'], width=1, dash='dash'), name='VWAP'), row=1, col=1)

    for d in drawings:
        col2=d.get('color',dc); w2=d.get('width',dw); da=d.get('dash',dd); lb=d.get('label','')
        if d['type'] == 'hline':
            fig.add_hline(y=d['y'], line=dict(color=col2, width=w2, dash=da),
                annotation_text=lb,
                annotation_font=dict(color=col2, size=9, family='Space Mono'),
                row=1, col=1)
        elif d['type'] == 'hrect':
            fig.add_hrect(y0=d['y0'], y1=d['y1'], fillcolor=col2,
                          opacity=0.07, line_width=0, row=1, col=1)

    cur = 2
    if show_rsi and 'rsi' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi'].squeeze(),
            line=dict(color=C['PURP'], width=1.1), name='RSI',
            fill='tozeroy', fillcolor='rgba(192,132,252,0.04)'), row=cur, col=1)
        fig.add_hline(y=70, line=dict(color=DOWN, width=0.5, dash='dot'), row=cur, col=1)
        fig.add_hline(y=30, line=dict(color=UP,   width=0.5, dash='dot'), row=cur, col=1)
        fig.add_hline(y=50, line=dict(color=C['TXT4'], width=0.4), row=cur, col=1)
        fig.update_yaxes(range=[0,100], row=cur, col=1)
        cur += 1
    if show_macd and 'mc' in df.columns:
        hist = df['mh'].squeeze()
        bc = [UP if v>=0 else DOWN for v in hist.fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=hist, marker_color=bc,
            name='Hist', opacity=0.55), row=cur, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['mc'].squeeze(),
            line=dict(color=C['BLUE'], width=1), name='MACD'), row=cur, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['ms'].squeeze(),
            line=dict(color=C['AMBER'], width=1), name='Signal'), row=cur, col=1)
        fig.add_hline(y=0, line=dict(color=C['TXT4'], width=0.4), row=cur, col=1)
        cur += 1
    if show_stoch and 'stk' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['stk'].squeeze(),
            line=dict(color=C['CYAN'], width=1), name='%K'), row=cur, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['std'].squeeze(),
            line=dict(color=C['AMBER'], width=1), name='%D'), row=cur, col=1)
        fig.add_hline(y=80, line=dict(color=DOWN, width=0.5, dash='dot'), row=cur, col=1)
        fig.add_hline(y=20, line=dict(color=UP,   width=0.5, dash='dot'), row=cur, col=1)
        cur += 1
    if show_vol and 'Volume' in df.columns:
        bc2 = [DOWN if o>cl else UP for o,cl in zip(df['Open'].squeeze(), c)]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'].squeeze(),
            marker_color=bc2, name='Vol', opacity=0.35, showlegend=False), row=cur, col=1)
        if 'vma' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['vma'].squeeze(),
                line=dict(color=C['AMBER'], width=0.8), name='Vol MA'), row=cur, col=1)

    lay = base_layout(C, height=720, title=f'{ticker} · {tf} · {chart_type}')
    lay['dragmode'] = 'pan'
    lay['newshape'] = dict(line=dict(color=dc, width=dw))
    fig.update_layout(**lay)
    fig.update_yaxes(showgrid=True, gridcolor=C['GRID'],
                     tickfont=dict(size=9, color=C['TXT3']),
                     side='right', zeroline=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=9, color=C['TXT3']))
    return fig

def mini_chart(df, C, height=180):
    if df is None or len(df) < 5:
        return None
    c = df['Close'].squeeze()
    is_up = float(c.iloc[-1]) >= float(c.iloc[0])
    color = C['UP'] if is_up else C['DOWN']
    rgb = "0,230,118" if is_up else "255,61,87"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(c))), y=c.values,
        line=dict(color=color, width=1.5),
        fill='tozeroy', fillcolor=f"rgba({rgb},0.06)",
        showlegend=False, hoverinfo='skip',
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        hovermode=False,
        xaxis=dict(visible=False, showgrid=False, zeroline=False,
                   fixedrange=True, rangeslider=dict(visible=False)),
        yaxis=dict(visible=False, showgrid=False, zeroline=False, fixedrange=True),
    )
    return fig

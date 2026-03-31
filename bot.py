import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Quantify", layout="wide",
                   initial_sidebar_state="expanded")

from modules.styles      import get_colors, inject_css, lbl
from modules.tickers     import TICKER_DB, TICKER_MAP, search_tickers
from modules.data        import TIMEFRAMES, SMART_PERIODS, PERIOD_CODES, get_data, price_info, fetch_news, add_indicators
from modules.signals     import get_signals_cached, compute_signals, train_model, ml_predict
from modules.charts      import base_layout, mini_chart, CFG, CFG0
from modules.moneyman    import call_mm, QUICK_ASKS
from modules.backtest    import STRATEGY_CATEGORIES, STRATEGY_DESC, run_backtest
from modules.tradingview import get_tv_symbol, TV_INTERVALS
from modules.financials  import (get_financials, get_info, render_key_stats,
                                  render_income_statement, render_balance_sheet,
                                  render_cashflow, render_dcf_model,
                                  render_comps, render_analyst_data, render_ownership,
                                  fmt_num, fmt_pct, fmt_ratio)
from modules.indicator_charts import make_indicator_chart, CHART_CATEGORIES, ALL_CHARTS, DEFAULT_CHARTS
from modules.news import fetch_live_news, get_source_color, ny_time

for k,v in [('theme','dark'),('chart_type','Candlestick'),
             ('watchlist',['SPY','AAPL','NVDA','BTC-USD','ETH-USD','GC=F']),
             ('portfolio',[]),('active_page','dashboard'),('active_symbol',None)]:
    if k not in st.session_state: st.session_state[k]=v

C = get_colors()
inject_css(C)
UP=C['UP']; DOWN=C['DOWN']; BLUE=C['BLUE']
AMBER=C['AMBER']; PURP=C['PURP']; CYAN=C['CYAN']; ROSE=C['ROSE']

def sig_color(s): return UP if "BUY" in s else DOWN if "SELL" in s else C['TXT2']
def sig_bg(s):    return 'rgba(0,230,118,0.06)' if "BUY" in s else 'rgba(255,61,87,0.06)' if "SELL" in s else C['BG2']
def sig_border(s):return UP if "BUY" in s else DOWN if "SELL" in s else C['BOR']

def price_badge(ticker):
    p,chg,pct=price_info(ticker)
    if not p: return ""
    col=UP if chg>=0 else DOWN; sign="+" if chg>=0 else ""
    name=TICKER_MAP.get(ticker,ticker)
    return f"""<div style="padding:16px 0 12px;border-bottom:1px solid {C['BOR']};margin-bottom:12px;">
        <div style="font-family:DM Sans,sans-serif;font-size:0.7rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:4px;">{name}</div>
        <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">
            <span style="font-family:DM Sans,sans-serif;font-size:2.2rem;font-weight:800;color:{C['TXT1']};letter-spacing:-0.02em;">{ticker}</span>
            <span style="font-family:IBM Plex Mono,monospace;font-size:1.8rem;font-weight:400;color:{C['TXT1']};">{p:,.4f}</span>
            <span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:{col};">{sign}{chg:.4f} ({sign}{pct:.2f}%)</span>
        </div>
    </div>"""

def render_tv_chart(ticker, tf="1D", theme="dark"):
    tv_sym = get_tv_symbol(ticker)
    tv_int = TV_INTERVALS.get(tf, "1D")
    bg = "#010408" if theme=="dark" else "#ffffff"
    safe_id = ticker.replace("-","").replace("=","").replace("^","")
    html = f"""<html><head>
    <style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{background:{bg};}}
    #tvchart_{safe_id}{{height:680px;width:100%;}}</style></head><body>
    <div id="tvchart_{safe_id}"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
        autosize:true, symbol:"{tv_sym}", interval:"{tv_int}",
        timezone:"Etc/UTC", theme:"{theme}", style:"1", locale:"en",
        toolbar_bg:"{bg}", enable_publishing:false, allow_symbol_change:true,
        hide_side_toolbar:false, withdateranges:true, save_image:true,
        container_id:"tvchart_{safe_id}",
        studies:["RSI@tv-basicstudies","MACD@tv-basicstudies","Volume@tv-basicstudies"],
        overrides:{{
            "paneProperties.background":"{bg}",
            "paneProperties.backgroundType":"solid",
            "scalesProperties.textColor":"#2a5070",
            "paneProperties.vertGridProperties.color":"#071525",
            "paneProperties.horzGridProperties.color":"#071525",
        }},
        studies_overrides:{{
            "volume.volume.color.0":"#ff3d5766",
            "volume.volume.color.1":"#00e67666",
        }},
    }});
    </script></body></html>"""
    components.html(html, height=700)

def render_tv_mini(ticker, theme="dark"):
    tv_sym = get_tv_symbol(ticker)
    safe_id = ticker.replace("-","").replace("=","").replace("^","")
    html = f"""<html><head><style>*{{margin:0;padding:0;}}body{{background:transparent;}}</style></head>
    <body><div id="mini_{safe_id}"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>new TradingView.MiniWidget({{
        symbol:"{tv_sym}",width:"100%",height:200,locale:"en",
        dateRange:"1D",colorTheme:"{theme}",
        trendLineColor:"rgba(41,121,255,1)",
        underLineColor:"rgba(41,121,255,0.06)",
        isTransparent:true,
        container_id:"mini_{safe_id}"
    }});</script></body></html>"""
    components.html(html, height=210)

PAGES=[("Dashboard","Dashboard"),("Equities","Equities"),("Crypto","Crypto"),
       ("Commodities","Commodities"),("Futures","Futures"),("Options","Options"),
       ("News","News"),("Backtest","Backtest"),("MoneyMan","MoneyMan"),("Portfolio","Portfolio")]

with st.sidebar:
    st.markdown(
        f'<div style="padding:18px 16px 14px;border-bottom:1px solid {C["BOR"]};">'
        f'<div style="font-family:DM Sans,sans-serif;font-size:1.3rem;font-weight:800;color:{C["TXT1"]};letter-spacing:-0.02em;">QUANTIFY</div>'
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;font-weight:500;letter-spacing:0.12em;color:{C["TXT3"]};text-transform:uppercase;margin-top:3px;">Market Intelligence Terminal</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown(f"<div style='padding:0 12px;margin-top:10px;'>", unsafe_allow_html=True)

    with st.expander("SETTINGS", expanded=False):
        t_choice=st.radio("Theme",["Dark","Light"],horizontal=True,
                          index=0 if C['DARK'] else 1,key="theme_radio")
        if t_choice=="Dark" and st.session_state.theme!='dark':
            st.session_state.theme='dark'; st.rerun()
        elif t_choice=="Light" and st.session_state.theme!='light':
            st.session_state.theme='light'; st.rerun()

    st.markdown(f"<div style='margin-top:8px;'>"+lbl("Search",C=C)+"</div>", unsafe_allow_html=True)
    sq=st.text_input("","",placeholder="Symbol or company...",key="sb_srch",label_visibility="collapsed")
    if sq:
        matches=search_tickers(sq)
        if matches:
            sel=st.selectbox("",["— select —"]+matches,key="sb_sel",label_visibility="collapsed")
            if sel and sel!="— select —":
                st.session_state.active_symbol=sel.split(" — ")[0]
                st.session_state.active_page="symbol"

    st.markdown(f"<div style='border-top:1px solid {C['BOR']};margin:12px 0;'></div>", unsafe_allow_html=True)
    st.markdown(lbl("Navigation",C=C), unsafe_allow_html=True)
    for _,page in PAGES:
        pg=page.lower()
        is_active = st.session_state.active_page == pg
        btn_style = "primary-btn" if is_active else ""
        if st.button(page, key=f"nav_{pg}", use_container_width=True):
            st.session_state.active_page=pg; st.rerun()

    st.markdown(f"<div style='border-top:1px solid {C['BOR']};margin:12px 0;'></div>", unsafe_allow_html=True)
    st.markdown(lbl("Watchlist",C=C), unsafe_allow_html=True)
    tv_theme_sb = "dark" if C['DARK'] else "light"
    for wt in st.session_state.watchlist:
        p2,chg2,pct2=price_info(wt)
        if p2:
            col2=UP if pct2>=0 else DOWN; sign2="+" if pct2>=0 else ""
            c1,c2=st.columns([1,1])
            with c1:
                st.markdown(f"""<div>
                    <div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;font-weight:700;color:{C['TXT1']};">{wt}</div>
                    <div style="font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:{C['TXT2']};">{p2:,.2f}</div>
                    <div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{col2};">{sign2}{pct2:.2f}%</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                df_mini=get_data(wt,"2d","30m")
                f=mini_chart(df_mini,C,height=50)
                if f: st.plotly_chart(f,use_container_width=True,config=CFG0)
            st.markdown(f"<div style='border-bottom:1px solid {C['BOR']};margin:4px 0;'></div>", unsafe_allow_html=True)

    now2=datetime.now(); mm=now2.hour*60+now2.minute; wd=now2.weekday()<5
    if wd and 570<=mm<960: ms="OPEN"; msc=UP
    elif wd and mm<570: ms="PRE"; msc=AMBER
    elif wd and mm>=960: ms="AFTER"; msc=AMBER
    else: ms="CLOSED"; msc=C['TXT3']
    st.markdown(f"""<div style="text-align:center;padding:8px 0 4px;">
        <span style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;font-weight:700;letter-spacing:0.12em;color:{msc};">NYSE {ms}</span>
        <span style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:{C['TXT4']};margin-left:8px;">{now2.strftime('%H:%M')}</span>
    </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_symbol_page(ticker):
    """Full institutional symbol workspace"""
    import streamlit.components.v1 as _components
    tv_theme = "dark" if C['DARK'] else "light"
    st.markdown("<div style='padding:0 1.5rem;'>", unsafe_allow_html=True)

    p,chg,pct=price_info(ticker)
    info = get_info(ticker)
    name = info.get('longName', info.get('shortName', ticker))
    exchange = info.get('exchange','')
    currency = info.get('currency','USD')
    sector = info.get('sector','')

    if p:
        col_p=C['UP'] if (chg or 0)>=0 else C['DOWN']
        sign="+" if (chg or 0)>=0 else ""
        s5_sig = get_signals_cached(ticker,"7d","5m")[1]
        s1d_sig = get_signals_cached(ticker,"2y","1d")[1]
        from modules.styles import signal_badge
        price_str = f"{p:,.4f}"
        chg_str = f"{chg:.4f}"
        pct_str = f"{pct:.2f}"
        badges = (
            f'<div style="text-align:center;"><div style="font-family:IBM Plex Mono,monospace;font-size:0.54rem;font-weight:600;letter-spacing:0.08em;color:{C["TXT3"]};margin-bottom:3px;">5M</div>'
            + signal_badge(s5_sig,C) + '</div>'
            + f'<div style="text-align:center;"><div style="font-family:IBM Plex Mono,monospace;font-size:0.54rem;font-weight:600;letter-spacing:0.08em;color:{C["TXT3"]};margin-bottom:3px;">1D</div>'
            + signal_badge(s1d_sig,C) + '</div>'
        )
        sector_part = (f'&nbsp;·&nbsp;{sector}') if sector else ''
        exch_part = (f'&nbsp;·&nbsp;{exchange}') if exchange else ''
        st.markdown(
            f'<div style="padding:16px 0 14px;border-bottom:1px solid {C["BOR"]};margin-bottom:14px;">'
            f'<div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;">'
            f'<div>'
            f'<div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">'
            f'<span style="font-family:DM Sans,sans-serif;font-size:1.6rem;font-weight:700;color:{C["TXT1"]};letter-spacing:-0.01em;">{ticker}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:1.4rem;font-weight:500;color:{C["TXT1"]};">{price_str}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:{col_p};">{sign}{chg_str} ({sign}{pct_str}%)</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{C["TXT3"]};background:{C["BG2"]};border:1px solid {C["BOR"]};padding:2px 7px;border-radius:3px;">{currency}</span>'
            f'</div>'
            f'<div style="font-family:Inter,sans-serif;font-size:0.8rem;color:{C["TXT3"]};margin-top:4px;">{name}{sector_part}{exch_part}</div>'
            f'</div>'
            f'<div style="display:flex;gap:10px;align-items:center;">{badges}</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

    ws_tabs = st.tabs(["Chart", "Overview", "Financials", "Valuation", "Analyst", "Ownership", "Options", "News"])

    # ── CHART ─────────────────────────────────────────────────────────────────
    with ws_tabs[0]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        ctrl=st.columns([1,1,1,1,4])
        tf_sel=ctrl[0].selectbox("TF",list(TV_INTERVALS.keys()),index=5,key="tf_"+ticker,label_visibility="collapsed")
        chart_style=ctrl[1].selectbox("Style",["Candles","Bars","Line","Area","Heikin Ashi"],key="cs_"+ticker,label_visibility="collapsed")
        show_rsi=ctrl[2].checkbox("RSI",value=True,key="rsi_"+ticker)
        show_macd=ctrl[3].checkbox("MACD",value=False,key="mac_"+ticker)
        STYLE_MAP={"Candles":"1","Bars":"0","Line":"2","Area":"3","Heikin Ashi":"8"}
        tv_style=STYLE_MAP.get(chart_style,"1")
        tv_int=TV_INTERVALS.get(tf_sel,"1D")
        tv_sym=get_tv_symbol(ticker)
        bg=C['BG0']
        safe_id=ticker.replace("-","").replace("=","").replace("^","")
        studies=["Volume@tv-basicstudies"]
        if show_rsi: studies.append("RSI@tv-basicstudies")
        if show_macd: studies.append("MACD@tv-basicstudies")
        sjs=", ".join(['"'+s+'"' for s in studies])
        chart_html=(
            '<html><head>'
            '<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:'+bg+';}'
            '#tvchart_'+safe_id+'{height:680px;width:100%;}</style></head><body>'
            '<div id="tvchart_'+safe_id+'"></div>'
            '<script src="https://s3.tradingview.com/tv.js"></script>'
            '<script>new TradingView.widget({'
            'autosize:true,symbol:"'+tv_sym+'",interval:"'+tv_int+'",'
            'timezone:"Etc/UTC",theme:"'+tv_theme+'",style:"'+tv_style+'",locale:"en",'
            'toolbar_bg:"'+bg+'",enable_publishing:false,allow_symbol_change:true,'
            'hide_side_toolbar:false,withdateranges:true,save_image:true,'
            'container_id:"tvchart_'+safe_id+'",'
            'studies:['+sjs+'],'
            'overrides:{"paneProperties.background":"'+bg+'","paneProperties.backgroundType":"solid",'
            '"scalesProperties.textColor":"#3d4452",'
            '"paneProperties.vertGridProperties.color":"#0d0f14",'
            '"paneProperties.horzGridProperties.color":"#0d0f14"},'
            'studies_overrides:{"volume.volume.color.0":"rgba(232,56,74,0.4)","volume.volume.color.1":"rgba(0,201,122,0.4)"},'
            '});</script></body></html>'
        )
        _components.html(chart_html, height=700)

        TF_DATA_MAP={"1m":("1d","1m"),"5m":("7d","5m"),"15m":("30d","15m"),"30m":("60d","30m"),
                     "1h":("60d","1h"),"2h":("120d","1h"),"4h":("180d","1h"),
                     "1D":("2y","1d"),"1W":("5y","1wk"),"1M":("10y","1mo")}
        per2,inv2=TF_DATA_MAP.get(tf_sel,("2y","1d"))
        with st.spinner(""):
            df=get_data(ticker,per2,inv2)
        if df is not None and len(df)>=20:
            df=add_indicators(df)
            st.markdown("<hr>", unsafe_allow_html=True)
            sleft,sright=st.columns([3,2])
            with sleft:
                sigs,ov,tot=compute_signals(df)
                model,scaler,acc,features=train_model(df.copy())
                ml_sig,ml_conf=ml_predict(df,model,scaler,features)
                buys=sum(1 for _,s,_ in sigs if s=="BUY")
                sells=sum(1 for _,s,_ in sigs if s=="SELL")
                c3=sig_color(ov);bg3=sig_bg(ov);bl3=sig_border(ov);ml_c=sig_color(ml_sig)
                st.markdown(
                    f'<div style="background:{bg3};border:1px solid {bl3};border-radius:6px;padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
                    f'<div><div style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{C["TXT3"]};margin-bottom:4px;">Consensus</div>'
                    f'<div style="font-family:DM Sans,sans-serif;font-size:1.8rem;font-weight:700;color:{c3};line-height:1;">{ov}</div></div>'
                    f'<div style="text-align:right;font-family:IBM Plex Mono,monospace;font-size:0.66rem;line-height:2;color:{C["TXT3"]};">'
                    f'<div><span style="color:{C["UP"]};">{buys} Buy</span> / <span style="color:{C["DOWN"]};">{sells} Sell</span></div>'
                    f'<div>Score <span style="color:{c3};font-weight:600;">{tot:+d}</span></div>'
                    f'<div>ML <span style="color:{ml_c};font-weight:600;">{ml_sig}</span> {ml_conf:.0%} · {acc:.0%} acc</div>'
                    f'</div></div></div>',
                    unsafe_allow_html=True
                )
                rows=""
                for nm,sg,det in sigs:
                    c4=sig_color(sg);bg4=sig_bg(sg);bl4=sig_border(sg)
                    rows+=(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                           f'background:{bg4};border-left:2px solid {bl4};padding:6px 12px;margin:1px 0;border-radius:0 4px 4px 0;">'
                           f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;color:{C["TXT2"]};">{nm}</span>'
                           f'<span style="font-family:Inter,sans-serif;font-size:0.7rem;color:{C["TXT3"]};">{det}</span>'
                           f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.68rem;font-weight:600;color:{c4};">{sg}</span></div>')
                st.markdown(rows, unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(lbl("Multi-Timeframe",C=C), unsafe_allow_html=True)
                tf_mc=st.columns(5)
                for i2,(lb2,pr3,iv3) in enumerate([("5M","7d","5m"),("15M","30d","15m"),("1H","60d","1h"),("4H","180d","1h"),("1D","2y","1d")]):
                    with tf_mc[i2]:
                        _,ov2,sc2=get_signals_cached(ticker,pr3,iv3)
                        c5=sig_color(ov2);bg5=sig_bg(ov2);bl5=sig_border(ov2)
                        st.markdown(
                            f'<div style="background:{bg5};border:1px solid {bl5};border-radius:4px;padding:9px 5px;text-align:center;">'
                            f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.54rem;font-weight:600;letter-spacing:0.08em;color:{C["TXT3"]};margin-bottom:3px;">{lb2}</div>'
                            f'<div style="font-family:DM Sans,sans-serif;font-size:0.75rem;font-weight:700;color:{c5};">{ov2}</div>'
                            f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.54rem;color:{C["TXT3"]};margin-top:2px;">{sc2:+d}</div></div>',
                            unsafe_allow_html=True
                        )
            with sright:
                r=df.iloc[-1]
                def gv(k):
                    try: return r.get(k, float('nan'))
                    except: return float('nan')
                stats_list=[
                    ("Open", f"{float(r['Open']):.4f}"),
                    ("H20", f"{df['High'].squeeze().tail(20).max():.4f}"),
                    ("L20", f"{df['Low'].squeeze().tail(20).min():.4f}"),
                    ("Volume", f"{int(r['Volume']):,}"),
                    ("ATR", f"{gv('atr'):.4f}"),
                    ("HV20", f"{gv('hv20'):.2%}"),
                    ("RSI", f"{gv('rsi'):.1f}"),
                    ("ADX", f"{gv('adx'):.1f}"),
                    ("CCI", f"{gv('cci'):.0f}"),
                    ("Williams %R", f"{gv('wr'):.1f}"),
                    ("MFI", f"{gv('mfi'):.1f}"),
                    ("VWAP", f"{gv('vwap'):.4f}"),
                    ("Z-Score", f"{gv('zscore'):.2f}"),
                ]
                rows2="".join(
                    f'<div style="display:flex;justify-content:space-between;border-bottom:1px solid {C["BOR"]};padding:4px 0;">'
                    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;color:{C["TXT3"]};">{k}</span>'
                    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{C["TXT2"]};">{v}</span></div>'
                    for k,v in stats_list
                )
                st.markdown(
                    f'<div style="background:{C["BG2"]};border:1px solid {C["BOR"]};border-radius:6px;padding:14px;">'
                    + lbl("Statistics",C=C) + rows2 + '</div>',
                    unsafe_allow_html=True
                )
                p2=float(r['Close']); ma_html=""
                for lb3,k3 in [("E9","e9"),("E21","e21"),("E50","e50"),("E200","e200")]:
                    try:
                        fv=float(r.get(k3,float('nan')))
                        if not np.isnan(fv):
                            mc3=C['UP'] if p2>fv else C['DOWN']
                            pct_m=(p2-fv)/fv*100
                            ma_html+=(
                                f'<div style="background:{C["BG0"]};border:1px solid {C["BOR"]};border-radius:4px;padding:8px 6px;flex:1;text-align:center;">'
                                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.54rem;font-weight:600;letter-spacing:0.08em;color:{C["TXT3"]};margin-bottom:2px;">{lb3}</div>'
                                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;font-weight:600;color:{mc3};">{fv:.2f}</div>'
                                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.54rem;color:{mc3};">{pct_m:+.1f}%</div></div>'
                            )
                    except: pass
                if ma_html:
                    st.markdown(f'<div style="display:flex;gap:4px;margin-top:8px;">{ma_html}</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.markdown(lbl("Indicator Charts",C=C), unsafe_allow_html=True)
            pin_key="pinned_"+ticker
            if pin_key not in st.session_state: st.session_state[pin_key]=DEFAULT_CHARTS.copy()
            ic1,ic2,ic3=st.columns([3,1,1])
            with ic1:
                cat_s=st.selectbox("Category",["All"]+list(CHART_CATEGORIES.keys()),key="icat_"+ticker,label_visibility="collapsed")
                opts=ALL_CHARTS if cat_s=="All" else CHART_CATEGORIES[cat_s]
                ch_s=st.selectbox("Indicator",opts,key="isel_"+ticker,label_visibility="collapsed")
            if ic2.button("Add",key="iadd_"+ticker):
                if ch_s not in st.session_state[pin_key]: st.session_state[pin_key].append(ch_s); st.rerun()
            if ic3.button("Reset",key="irst_"+ticker):
                st.session_state[pin_key]=DEFAULT_CHARTS.copy(); st.rerun()
            if st.session_state[pin_key]:
                chips='<div style="display:flex;flex-wrap:wrap;gap:5px;padding:5px 0 10px;">'
                for cn in st.session_state[pin_key]:
                    chips+=f'<span style="background:{C["BG2"]};border:1px solid {C["BOR2"]};border-radius:3px;padding:3px 9px;font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:500;color:{C["TXT2"]};">{cn}</span>'
                chips+='</div>'
                st.markdown(chips, unsafe_allow_html=True)
            pinned=st.session_state[pin_key]
            CFG_IND={'displayModeBar':False,'scrollZoom':True,'displaylogo':False,'doubleClick':'reset'}
            if pinned:
                first3=pinned[:3]; extra=pinned[3:]
                if len(first3)==3: ind_cols=st.columns(3)
                elif len(first3)==2: ind_cols=list(st.columns(2))+[None]
                else: ind_cols=[st.columns(1)[0],None,None]
                for i3,ch_n in enumerate(first3):
                    if ind_cols[i3]:
                        with ind_cols[i3]:
                            fig_i=make_indicator_chart(df,ch_n,C,height=230)
                            if fig_i: st.plotly_chart(fig_i,use_container_width=True,config=CFG_IND)
                            if st.button("Remove",key=f"rmi_{ticker}_{i3}"): st.session_state[pin_key].remove(ch_n); st.rerun()
                for j3,ch_n in enumerate(extra):
                    ec1,ec2=st.columns([5,1])
                    with ec1:
                        fig_i=make_indicator_chart(df,ch_n,C,height=240)
                        if fig_i: st.plotly_chart(fig_i,use_container_width=True,config=CFG_IND)
                    with ec2:
                        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
                        if st.button("Remove",key=f"rmie_{ticker}_{j3}"): st.session_state[pin_key].remove(ch_n); st.rerun()

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    with ws_tabs[1]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if not info:
            st.info("Company information not available.")
        else:
            o1,o2=st.columns([2,1])
            with o1:
                desc=info.get('longBusinessSummary','')
                if desc:
                    st.markdown(
                        f'<div style="background:{C["BG2"]};border:1px solid {C["BOR"]};border-radius:6px;padding:16px;margin-bottom:14px;">'
                        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{C["TXT3"]};margin-bottom:8px;">About</div>'
                        f'<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:{C["TXT2"]};line-height:1.6;">{desc[:600]}{"..." if len(desc)>600 else ""}</div></div>',
                        unsafe_allow_html=True
                    )
                render_key_stats(info,C)
            with o2:
                render_analyst_data(ticker,info,C)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(lbl("News",C=C), unsafe_allow_html=True)
                from modules.news import fetch_live_news as _fln
                for nn in _fln(ticker,6):
                    st.markdown(
                        f'<a href="{nn["link"]}" target="_blank" style="text-decoration:none;display:block;">'
                        f'<div style="border-bottom:1px solid {C["BOR"]};padding:8px 0;">'
                        f'<div style="font-family:Inter,sans-serif;font-size:0.78rem;font-weight:500;color:{C["TXT2"]};line-height:1.4;margin-bottom:2px;">{nn["title"]}</div>'
                        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;color:{C["TXT3"]};">{nn["source"]} · {nn["time"]}</div>'
                        f'</div></a>',
                        unsafe_allow_html=True
                    )

    # ── FINANCIALS ────────────────────────────────────────────────────────────
    with ws_tabs[2]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        fin=get_financials(ticker)
        if not fin:
            st.info("Financial data not available.")
        else:
            fp=st.radio("Period",["Annual","Quarterly"],horizontal=True,key="fp_"+ticker,label_visibility="collapsed")
            ftabs=st.tabs(["Income Statement","Balance Sheet","Cash Flow"])
            with ftabs[0]: render_income_statement(fin,C,fp)
            with ftabs[1]: render_balance_sheet(fin,C,fp)
            with ftabs[2]: render_cashflow(fin,C,fp)

    # ── VALUATION ─────────────────────────────────────────────────────────────
    with ws_tabs[3]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        vtabs=st.tabs(["DCF Model","Comparable Companies","Key Multiples"])
        with vtabs[0]: render_dcf_model(info,C)
        with vtabs[1]: render_comps(ticker,info,C)
        with vtabs[2]: render_key_stats(info,C)

    # ── ANALYST ───────────────────────────────────────────────────────────────
    with ws_tabs[4]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        render_analyst_data(ticker,info,C)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        try:
            fin4=get_financials(ticker); recs=fin4.get('recommendations')
            if recs is not None and not recs.empty:
                st.markdown(lbl("Recommendation History",C=C), unsafe_allow_html=True)
                st.dataframe(recs.head(20),use_container_width=True)
        except: pass

    # ── OWNERSHIP ─────────────────────────────────────────────────────────────
    with ws_tabs[5]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        fin5=get_financials(ticker)
        render_ownership(fin5,C)

    # ── OPTIONS ───────────────────────────────────────────────────────────────
    with ws_tabs[6]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        try:
            tk_opt=yf.Ticker(ticker); exps=tk_opt.options
            if not exps:
                st.info("No options data available.")
            else:
                exp_sel=st.selectbox("Expiration",exps[:15],key="opt_exp_"+ticker,label_visibility="collapsed")
                chain=tk_opt.option_chain(exp_sel); calls,puts=chain.calls,chain.puts
                cv=calls['volume'].sum(); pv=puts['volume'].sum(); pcr=pv/cv if cv>0 else 0
                om1,om2,om3,om4,om5,om6=st.columns(6)
                om1.metric("Call Vol",f"{cv:,.0f}"); om2.metric("Put Vol",f"{pv:,.0f}")
                om3.metric("P/C Ratio",f"{pcr:.2f}","Bearish" if pcr>1 else "Bullish")
                om4.metric("Call OI",f"{calls['openInterest'].sum():,.0f}")
                om5.metric("Put OI",f"{puts['openInterest'].sum():,.0f}")
                om6.metric("Avg IV",f"{calls['impliedVolatility'].mean()*100:.1f}%")
                s_flow="BEARISH" if pcr>1.3 else "BULLISH" if pcr<0.7 else "NEUTRAL"
                sf_c=C['DOWN'] if s_flow=="BEARISH" else C['UP'] if s_flow=="BULLISH" else C['TXT2']
                st.markdown(
                    f'<div style="background:{C["BG2"]};border:1px solid {C["BOR"]};border-radius:6px;padding:12px 16px;margin:12px 0;display:flex;align-items:center;gap:14px;">'
                    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{C["TXT3"]};">Options Flow</span>'
                    f'<span style="font-family:DM Sans,sans-serif;font-size:1.2rem;font-weight:700;color:{sf_c};">{s_flow}</span>'
                    f'<span style="font-family:Inter,sans-serif;font-size:0.8rem;color:{C["TXT2"]};"> P/C {pcr:.2f}</span></div>',
                    unsafe_allow_html=True
                )
                oc1,oc2=st.columns(2)
                for co,da,tt in [(oc1,calls,"Top Calls"),(oc2,puts,"Top Puts")]:
                    with co:
                        st.markdown(lbl(tt,C=C), unsafe_allow_html=True)
                        td_o=da[['strike','lastPrice','bid','ask','volume','openInterest','impliedVolatility']].copy()
                        td_o.columns=['Strike','Last','Bid','Ask','Vol','OI','IV']
                        td_o['IV']=(td_o['IV']*100).round(1).astype(str)+'%'
                        st.dataframe(td_o.sort_values('Vol',ascending=False).head(12),use_container_width=True,hide_index=True)
                import plotly.graph_objects as _go2
                fig_iv2=_go2.Figure()
                fig_iv2.add_trace(_go2.Scatter(x=calls['strike'],y=calls['impliedVolatility']*100,mode='lines',name='Calls',line=dict(color=C['UP'],width=1.4)))
                fig_iv2.add_trace(_go2.Scatter(x=puts['strike'],y=puts['impliedVolatility']*100,mode='lines',name='Puts',line=dict(color=C['DOWN'],width=1.4)))
                fig_iv2.update_layout(**base_layout(C,260,"IV Skew"))
                st.plotly_chart(fig_iv2,use_container_width=True,config=CFG0)
        except Exception as e:
            st.error(f"Options error: {e}")

    # ── NEWS ──────────────────────────────────────────────────────────────────
    with ws_tabs[7]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        from modules.news import fetch_live_news as _fln2, get_source_color as _gsc
        with st.spinner("Loading..."):
            sym_news=_fln2(ticker,20)
        if not sym_news:
            st.info("No news found.")
        else:
            nc1,nc2=st.columns(2)
            for ni,nn in enumerate(sym_news):
                sc_col=_gsc(nn['source'])
                with nc1 if ni%2==0 else nc2:
                    st.markdown(
                        f'<a href="{nn["link"]}" target="_blank" style="text-decoration:none;display:block;">'
                        f'<div style="background:{C["BG2"]};border:1px solid {C["BOR"]};border-top:2px solid {sc_col};border-radius:6px;padding:12px;margin-bottom:8px;">'
                        f'<div style="font-family:Inter,sans-serif;font-size:0.83rem;font-weight:500;color:{C["TXT1"]};line-height:1.45;margin-bottom:7px;">{nn["title"]}</div>'
                        f'<div style="display:flex;justify-content:space-between;">'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;font-weight:600;color:{sc_col};letter-spacing:0.06em;">{nn["source"].upper()}</span>'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;color:{C["TXT3"]};">{nn["time"]}</span>'
                        f'</div></div></a>',
                        unsafe_allow_html=True
                    )

    st.markdown("</div>", unsafe_allow_html=True)



page=st.session_state.active_page
now=datetime.now()
mkt_min=now.hour*60+now.minute; is_wd=now.weekday()<5
if is_wd and 570<=mkt_min<960: ms2="MARKET OPEN"; msc2=UP
elif is_wd and mkt_min<570: ms2="PRE-MARKET"; msc2=AMBER
elif is_wd and mkt_min>=960: ms2="AFTER HOURS"; msc2=AMBER
else: ms2="MARKET CLOSED"; msc2=C['TXT3']

st.markdown(
    f'<div style="background:{C["BG1"]};border-bottom:1px solid {C["BOR"]};padding:12px 20px;">'
    f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">'
    f'<div style="display:flex;align-items:center;gap:16px;">'
    f'<span style="font-family:DM Sans,sans-serif;font-size:1.1rem;font-weight:800;color:{C["TXT1"]};letter-spacing:-0.01em;">QUANTIFY</span>'
    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:500;letter-spacing:0.1em;color:{C["TXT3"]};text-transform:uppercase;">Market Intelligence Terminal</span>'
    f'</div>'
    f'<div style="display:flex;align-items:center;gap:20px;">'
    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;font-weight:600;color:{msc2};letter-spacing:0.06em;">{ms2}</span>'
    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.64rem;color:{C["TXT3"]};">{now.strftime("%a %d %b %Y")} &nbsp;·&nbsp; {ny_time()}</span>'
    f'</div></div></div>',
    unsafe_allow_html=True
)

if page=="symbol" and st.session_state.active_symbol:
    render_symbol_page(st.session_state.active_symbol)

elif page=="dashboard":
    tv_theme=("dark" if C['DARK'] else "light")
    st.markdown(f"<div style='padding:14px 1.5rem 0;'>", unsafe_allow_html=True)
    IDXS=[("S&P 500","SPY"),("NASDAQ","QQQ"),("DOW","DIA"),("RUSSELL","IWM"),
          ("VIX","^VIX"),("GOLD","GC=F"),("OIL","CL=F"),("BTC","BTC-USD"),("ETH","ETH-USD")]
    idx_cols=st.columns(len(IDXS))
    for i,(nm,tk) in enumerate(IDXS):
        p,chg,pct=price_info(tk)
        if p:
            col=UP if chg>=0 else DOWN; sign="+" if chg>=0 else ""
            idx_cols[i].markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;padding:12px 8px;text-align:center;">
                <div style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:5px;">{nm}</div>
                <div style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;font-weight:700;color:{C['TXT1']};">{p:,.2f}</div>
                <div style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;font-weight:600;color:{col};margin-top:3px;">{sign}{pct:.2f}%</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    wl_c1,wl_c2,wl_c3=st.columns([3,2,1])
    with wl_c1: st.markdown(lbl("My Watchlist",C=C), unsafe_allow_html=True)
    with wl_c2:
        wl_add=st.text_input("",placeholder="Add ticker...",key="wl_add",label_visibility="collapsed")
        if wl_add:
            wl_m=search_tickers(wl_add)
            if wl_m:
                ws=st.selectbox("",["— select —"]+wl_m,key="wl_sel",label_visibility="collapsed")
                if ws and ws!="— select —":
                    nt=ws.split(" — ")[0]
                    if nt not in st.session_state.watchlist:
                        st.session_state.watchlist.append(nt); st.rerun()
    with wl_c3:
        if st.button("Clear",key="clr_wl"): st.session_state.watchlist=[]; st.rerun()

    wl=st.session_state.watchlist
    if not wl:
        st.markdown(f"""<div style="text-align:center;padding:30px;background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;margin-bottom:16px;">
            <div style="font-family:Inter,sans-serif;font-size:0.9rem;color:{C['TXT3']};">Add tickers using the search above.</div>
        </div>""", unsafe_allow_html=True)
    else:
        hdr=f'<div style="display:grid;grid-template-columns:100px 1fr 110px 90px 120px 120px;gap:4px;padding:8px 12px;border-bottom:2px solid {C["BOR"]};">'
        for h2 in ["TICKER","NAME","PRICE","CHG %","5M","1D"]:
            al="text-align:right;" if h2 in ["PRICE","CHG %"] else "text-align:center;" if h2 in ["5M","1D"] else ""
            hdr+=f'<span style="font-family:Space Mono;font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C["TXT3"]};{al}">{h2}</span>'
        hdr+="</div>"; st.markdown(hdr, unsafe_allow_html=True)
        for tk in wl:
            p2,chg2,pct2=price_info(tk)
            if not p2: continue
            pc=UP if pct2>=0 else DOWN; sign2="+" if pct2>=0 else ""
            _,s5,_=get_signals_cached(tk,"7d","5m")
            _,s1d,_=get_signals_cached(tk,"2y","1d")
            def badge(s):
                c2=sig_color(s);bg2=sig_bg(s);bl2=sig_border(s)
                return f'<span style="background:{bg2};color:{c2};border:1px solid {bl2};font-family:Outfit;font-size:0.75rem;font-weight:800;padding:3px 10px;border-radius:6px;">{s}</span>'
            name=TICKER_MAP.get(tk,tk)
            st.markdown(f"""<div style="display:grid;grid-template-columns:100px 1fr 110px 90px 120px 120px;
                gap:4px;padding:9px 12px;border-bottom:1px solid {C['BOR']};align-items:center;">
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.82rem;font-weight:700;color:{C['TXT1']};">{tk}</span>
                <span style="font-family:Inter,sans-serif;font-size:0.82rem;color:{C['TXT2']};">{name}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.82rem;font-weight:600;color:{C['TXT2']};text-align:right;">{p2:,.4f}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;font-weight:600;color:{pc};text-align:right;">{sign2}{pct2:.2f}%</span>
                <span style="text-align:center;">{badge(s5)}</span>
                <span style="text-align:center;">{badge(s1d)}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    left,right=st.columns([2.4,1])
    with left:
        st.markdown(lbl("Market Charts",C=C), unsafe_allow_html=True)
        CHARTS=[("SPY","S&P 500"),("QQQ","Nasdaq"),("BTC-USD","Bitcoin"),("GC=F","Gold")]
        ch_cols=st.columns(2)
        for i,(ct2,cn) in enumerate(CHARTS):
            with ch_cols[i%2]:
                p2,chg2,pct2=price_info(ct2)
                col2=UP if (chg2 or 0)>=0 else DOWN
                sign2="+" if (chg2 or 0)>=0 else ""
                pct_str=f"{sign2}{(pct2 or 0):.2f}%"
                price_str=f"{p2:,.2f}" if p2 else "—"
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">'
                    f'<div>'
                    f'<span style="font-family:DM Sans,sans-serif;font-size:0.95rem;font-weight:700;color:{C["TXT1"]};">{cn}</span>'
                    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{C["TXT3"]};margin-left:8px;">{price_str}</span>'
                    f'</div>'
                    f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;font-weight:600;color:{col2};">{pct_str}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                df_dash=get_data(ct2,"5d","5m")
                if df_dash is not None and len(df_dash)>5:
                    from modules.charts import mini_chart as _mc
                    fig_d=_mc(df_dash,C,height=180)
                    if fig_d: st.plotly_chart(fig_d,use_container_width=True,config={'displayModeBar':False,'scrollZoom':False})

    with right:
        st.markdown(lbl("Headlines",C=C), unsafe_allow_html=True)
        for n in fetch_live_news("SPY",10):
            st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;display:block;">
            <div style="border-bottom:1px solid {C['BOR']};padding:9px 0;">
                <div style="font-family:Inter,sans-serif;font-size:0.82rem;font-weight:500;color:{C['TXT2']};line-height:1.4;margin-bottom:4px;">{n['title']}</div>
                <div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:{C['TXT3']};">{n['source'].upper()} · {n['time']}</div>
            </div></a>""", unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(lbl("Sectors",C=C), unsafe_allow_html=True)
        for st_t,st_n in [("XLK","TECH"),("XLF","FINANCE"),("XLE","ENERGY"),
                           ("XLV","HEALTH"),("XLI","INDUSTRIAL")]:
            _,ov3,_=get_signals_cached(st_t,"60d","1h")
            p3,_,pct3=price_info(st_t)
            c3=sig_color(ov3); sign3="+" if (pct3 or 0)>=0 else ""
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {C['BOR']};">
                <div><span style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;font-weight:700;color:{C['TXT1']};">{st_t}</span>
                     <span style="font-family:Inter,sans-serif;font-size:0.68rem;color:{C['TXT3']};margin-left:6px;">{st_n}</span></div>
                <span style="font-family:DM Sans,sans-serif;font-size:0.82rem;font-weight:800;color:{c3};">{ov3}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{'#00e676' if (pct3 or 0)>=0 else '#ff3d57'};">{sign3}{(pct3 or 0):.2f}%</span>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page in ["equities","crypto","commodities","futures"]:
    LISTS={
        "equities": {"AAPL":"AAPL","NVDA":"NVDA","TSLA":"TSLA","MSFT":"MSFT","AMZN":"AMZN",
                     "META":"META","GOOGL":"GOOGL","AMD":"AMD","NFLX":"NFLX","JPM":"JPM","GS":"GS"},
        "crypto":   {"BTC-USD":"BTC-USD","ETH-USD":"ETH-USD","SOL-USD":"SOL-USD","XRP-USD":"XRP-USD",
                     "BNB-USD":"BNB-USD","DOGE-USD":"DOGE-USD","ADA-USD":"ADA-USD","AVAX-USD":"AVAX-USD"},
        "commodities":{"Gold":"GC=F","Silver":"SI=F","Crude Oil":"CL=F","Nat Gas":"NG=F",
                       "Copper":"HG=F","Wheat":"ZW=F","Corn":"ZC=F"},
        "futures":  {"S&P 500":"ES=F","Nasdaq":"NQ=F","Dow":"YM=F","Russell":"RTY=F",
                     "10Y Bond":"ZN=F","30Y Bond":"ZB=F"},
    }
    lst=LISTS[page]
    ch=st.selectbox("",list(lst.keys()),key=f"{page}_sel",label_visibility="collapsed")
    render_symbol_page(lst[ch])

elif page=="options":
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)
    opt_t=st.selectbox("",["SPY","QQQ","AAPL","TSLA","NVDA","META","MSFT","AMZN","AMD"],
                        key="op_s",label_visibility="collapsed")
    st.markdown(price_badge(opt_t), unsafe_allow_html=True)
    try:
        tk2=yf.Ticker(opt_t); exps=tk2.options
        if not exps: st.info("No options data.")
        else:
            exp=st.selectbox("Expiration",exps[:12],key="op_exp",label_visibility="collapsed")
            chain=tk2.option_chain(exp); calls,puts=chain.calls,chain.puts
            cv=calls['volume'].sum(); pv=puts['volume'].sum(); pcr=pv/cv if cv>0 else 0
            m1,m2,m3,m4,m5,m6=st.columns(6)
            m1.metric("CALL VOL",f"{cv:,.0f}"); m2.metric("PUT VOL",f"{pv:,.0f}")
            m3.metric("P/C RATIO",f"{pcr:.2f}","Bearish" if pcr>1 else "Bullish")
            m4.metric("CALL OI",f"{calls['openInterest'].sum():,.0f}")
            m5.metric("PUT OI",f"{puts['openInterest'].sum():,.0f}")
            m6.metric("AVG IV",f"{calls['impliedVolatility'].mean()*100:.1f}%")
            s="BEARISH" if pcr>1.3 else "BULLISH" if pcr<0.7 else "NEUTRAL"
            sc2=sig_color(s)
            st.markdown(f"""<div style="background:{sig_bg(s)};border:1px solid {sig_border(s)};border-radius:12px;
                padding:14px 20px;margin:14px 0;display:flex;align-items:center;gap:16px;">
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};">Options Flow</span>
                <span style="font-family:DM Sans,sans-serif;font-size:1.6rem;font-weight:900;color:{sc2};">{s}</span>
                <span style="font-family:Inter,sans-serif;font-size:0.85rem;color:{C['TXT2']};">
                    {"Heavy put buying" if pcr>1.3 else "Heavy call buying" if pcr<0.7 else "Balanced flow"} · P/C = {pcr:.2f}
                </span></div>""", unsafe_allow_html=True)
            oc1,oc2=st.columns(2)
            for col_obj,data,title in [(oc1,calls,"Top Calls"),(oc2,puts,"Top Puts")]:
                with col_obj:
                    st.markdown(lbl(title,C=C), unsafe_allow_html=True)
                    td=data[['strike','lastPrice','bid','ask','volume','openInterest','impliedVolatility']].copy()
                    td.columns=['Strike','Last','Bid','Ask','Vol','OI','IV']
                    td['IV']=(td['IV']*100).round(1).astype(str)+'%'
                    st.dataframe(td.sort_values('Vol',ascending=False).head(12),use_container_width=True,hide_index=True)
            fig_iv=go.Figure()
            fig_iv.add_trace(go.Scatter(x=calls['strike'],y=calls['impliedVolatility']*100,mode='lines',name='Calls',line=dict(color=UP,width=1.4)))
            fig_iv.add_trace(go.Scatter(x=puts['strike'],y=puts['impliedVolatility']*100,mode='lines',name='Puts',line=dict(color=DOWN,width=1.4)))
            fig_iv.update_layout(**base_layout(C,280,"IV Skew"))
            st.plotly_chart(fig_iv,use_container_width=True,config=CFG0)
    except Exception as e: st.error(f"Options error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="news":
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)

    # Header with live NY clock
    st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;">
        <div style="font-family:DM Sans,sans-serif;font-size:1.8rem;font-weight:900;color:{C['TXT1']};">Live News Feed</div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;font-weight:700;color:{AMBER};">
            {ny_time()} · Auto-refreshes every 60s
        </div>
    </div>""", unsafe_allow_html=True)

    n_c1, n_c2, n_c3 = st.columns([2,2,2])
    with n_c1:
        nt = st.selectbox("Asset",
            ["SPY","QQQ","AAPL","NVDA","TSLA","MSFT","META","AMZN","GOOGL",
             "BTC-USD","ETH-USD","SOL-USD","XRP-USD",
             "GC=F","CL=F","SI=F","NG=F",
             "ES=F","NQ=F","EURUSD=X","GBPUSD=X"],
            key="news_tkr", label_visibility="collapsed")
    with n_c2:
        nl = st.selectbox("Count",
            ["20 articles","40 articles","60 articles"],
            key="news_lim", label_visibility="collapsed")
        lim2 = int(nl.split()[0])
    with n_c3:
        layout_mode = st.radio("Layout", ["Grid","List"], horizontal=True,
                                key="news_layout", label_visibility="collapsed")

    st.markdown(f"""<div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:{C['TXT3']};
        padding:4px 0 12px;">
        Sources: Reuters · CNBC · MarketWatch · Yahoo Finance · Google News · CoinDesk · Seeking Alpha · Barrons
    </div>""", unsafe_allow_html=True)

    with st.spinner("Loading live news..."):
        news_items = fetch_live_news(nt, lim2)

    if not news_items:
        st.markdown(f"""<div style="text-align:center;padding:40px;background:{C['BG2']};
            border:1px solid {C['BOR']};border-radius:12px;">
            <div style="font-family:Inter,sans-serif;font-size:0.95rem;color:{C['TXT3']};">
                No news found. Markets may be closed or RSS feeds temporarily unavailable.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{C['TXT3']};
            padding:4px 0 8px;">{len(news_items)} articles loaded</div>""",
            unsafe_allow_html=True)

        if layout_mode == "Grid":
            nc1, nc2 = st.columns(2)
            for i, n in enumerate(news_items):
                src_color = get_source_color(n['source'])
                with nc1 if i%2==0 else nc2:
                    st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;display:block;">
                    <div style="background:{C['BG2']};border:1px solid {C['BOR']};border-top:2px solid {src_color};
                        border-radius:12px;padding:16px;margin-bottom:10px;transition:all 0.15s;">
                        <div style="font-family:Inter,sans-serif;font-size:0.9rem;font-weight:600;
                                     color:{C['TXT1']};line-height:1.45;margin-bottom:10px;">{n['title']}</div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:700;
                                          color:{src_color};letter-spacing:0.06em;">{n['source'].upper()}</span>
                            <span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:{C['TXT3']};">
                                {n['time']}</span>
                        </div>
                    </div></a>""", unsafe_allow_html=True)
        else:
            for n in news_items:
                src_color = get_source_color(n['source'])
                st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;display:block;">
                <div style="background:{C['BG2']};border-bottom:1px solid {C['BOR']};
                    border-left:3px solid {src_color};padding:12px 16px;margin-bottom:4px;">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;">
                        <div style="font-family:Inter,sans-serif;font-size:0.88rem;font-weight:500;
                                     color:{C['TXT1']};line-height:1.4;flex:1;">{n['title']}</div>
                        <div style="text-align:right;white-space:nowrap;">
                            <div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:700;
                                         color:{src_color};">{n['source'].upper()}</div>
                            <div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:{C['TXT3']};">{n['time']}</div>
                        </div>
                    </div>
                </div></a>""", unsafe_allow_html=True)

    if st.button("🔄 Refresh News", key="refresh_news"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

elif page=="backtest":
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-family:DM Sans,sans-serif;font-size:1.8rem;font-weight:900;color:{C['TXT1']};margin-bottom:4px;">Backtest Terminal</div>
    <div style="font-family:IBM Plex Mono,monospace;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:16px;">No-Code Strategy Testing · Any Symbol · Any Timeframe · AI Quant Analysis</div>""", unsafe_allow_html=True)

    # Mode selector
    bt_mode = st.radio("", ["Built-in Strategies", "AI Quant Backtester"],
                        horizontal=True, key="bt_mode", label_visibility="collapsed")

    bc1,bc2,bc3,bc4=st.columns([2,1,1,1])
    with bc1:
        bt_q=st.text_input("Symbol","SPY",placeholder="Type symbol...",key="bt_q",label_visibility="collapsed")
        bt_m=search_tickers(bt_q)
        if bt_m and bt_q:
            bt_s=st.selectbox("",["— select —"]+bt_m,key="bt_sel",label_visibility="collapsed")
            bt_ticker=bt_s.split(" — ")[0] if bt_s and bt_s!="— select —" else bt_q.strip().upper()
        else: bt_ticker=bt_q.strip().upper() if bt_q else "SPY"
    ALL_TFS=["1m","5m","15m","30m","1h","4h","1D","1W","1M"]
    bt_tf=bc2.selectbox("Timeframe",ALL_TFS,index=6,key="bt_tf",label_visibility="collapsed")
    smart_opts=SMART_PERIODS.get(bt_tf,["1 Month","3 Months","1 Year","2 Years","5 Years"])
    bt_per=bc3.selectbox("Period",smart_opts,index=min(2,len(smart_opts)-1),key="bt_per",label_visibility="collapsed")
    bt_cap=bc4.number_input("Capital ($)",value=10000,min_value=100,step=1000,key="bt_cap",label_visibility="collapsed")
    rm1,rm2,rm3,rm4,rm5=st.columns([1,1,1,1,2])
    use_sl=rm1.checkbox("Stop Loss %",value=False,key="bt_use_sl")
    sl_pct=rm2.number_input("SL",value=2.0,min_value=0.1,max_value=50.0,step=0.5,key="bt_sl",label_visibility="collapsed") if use_sl else None
    use_tp=rm3.checkbox("Take Profit %",value=False,key="bt_use_tp")
    tp_pct=rm4.number_input("TP",value=4.0,min_value=0.1,max_value=200.0,step=0.5,key="bt_tp",label_visibility="collapsed") if use_tp else None
    bt_comm=rm5.slider("Commission %",min_value=0.0,max_value=0.5,value=0.1,step=0.01,key="bt_comm")/100
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if bt_mode == "Built-in Strategies":
        sc1,sc2=st.columns([2,3])
        with sc1:
            cat=st.selectbox("Category",list(STRATEGY_CATEGORIES.keys()),key="bt_cat",label_visibility="collapsed")
            sel_strat=st.selectbox("Strategy",STRATEGY_CATEGORIES[cat],key="bt_strat",label_visibility="collapsed")
        with sc2:
            st.markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;padding:14px 16px;margin-top:4px;">
                <div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:6px;">Strategy Description</div>
                <div style="font-family:Inter,sans-serif;font-size:0.88rem;color:{C['TXT2']};line-height:1.5;">{STRATEGY_DESC.get(sel_strat,'')}</div>
            </div>""", unsafe_allow_html=True)

        if st.button("RUN BACKTEST", key="run_bt"):
            pc = PERIOD_CODES.get(bt_per, '1y')
            tf_inv_map = {"1m":"1m","3m":"5m","5m":"5m","15m":"15m","30m":"30m",
                          "1h":"1h","2h":"2h","4h":"1h","1D":"1d","1W":"1wk","1M":"1mo"}
            inv = tf_inv_map.get(bt_tf, "1d")
            with st.spinner(f"Fetching {bt_ticker} {bt_tf} data..."):
                df_bt=get_data(bt_ticker,pc,inv)
            if df_bt is None or len(df_bt)<10:
                st.error(f"No data for {bt_ticker} on {bt_tf} / {bt_per}. Try a longer period.")
            else:
                st.markdown(f"""<div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{C['TXT3']};padding:4px 0;">
                    {len(df_bt)} candles loaded · Running {sel_strat}...</div>""", unsafe_allow_html=True)
                with st.spinner(f"Running {sel_strat}..."):
                    result,err=run_backtest(df_bt,sel_strat,bt_cap,
                                            commission=bt_comm if 'bt_comm' in dir() else 0.001,
                                            stop_loss_pct=sl_pct,
                                            take_profit_pct=tp_pct)
                if result is None: st.error(err)
                else:
                    stats=result['stats']; trades=result['trades']; eq_df=result['equity']
                    rc=UP if stats['total_return']>=0 else DOWN
                    st.markdown(f"""<div style="background:{'rgba(0,230,118,0.06)' if stats['total_return']>=0 else 'rgba(255,61,87,0.06)'};
                        border:1px solid {rc};border-radius:12px;padding:18px 20px;margin:16px 0;">
                        <div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:6px;">
                            {bt_ticker} · {bt_tf} · {bt_per} · {sel_strat}</div>
                        <div style="font-family:DM Sans,sans-serif;font-size:2.6rem;font-weight:900;color:{rc};line-height:1;">
                            {'+' if stats['total_return']>=0 else ''}{stats['total_return']}%</div>
                        <div style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;color:{C['TXT2']};margin-top:4px;">
                            ${stats['initial']:,} → ${stats['final_equity']:,} · {stats['total_trades']} trades</div>
                    </div>""", unsafe_allow_html=True)
                    si=[
                        ("TOTAL RETURN",f"{'+' if stats['total_return']>=0 else ''}{stats['total_return']}%",UP if stats['total_return']>=0 else DOWN),
                        ("WIN RATE",f"{stats['win_rate']}%",UP if stats['win_rate']>=50 else DOWN),
                        ("TRADES",str(stats['total_trades']),C['TXT1']),
                        ("PROFIT FACTOR",str(stats['profit_factor']),UP if stats['profit_factor']>=1 else DOWN),
                        ("MAX DRAWDOWN",f"-{stats['max_drawdown']}%",DOWN),
                        ("EXPECTANCY",f"{stats.get('expectancy',0):+.2f}%",UP if stats.get('expectancy',0)>=0 else DOWN),
                        ("AVG WIN",f"+{stats['avg_win']}%",UP),
                        ("SIGNALS",str(stats.get('signals_found','—')),AMBER),
                    ]
                    sc_cols=st.columns(8)
                    for i2,(lbl2,val,col2) in enumerate(si):
                        sc_cols[i2].markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;padding:12px;text-align:center;">
                            <div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:4px;">{lbl2}</div>
                            <div style="font-family:IBM Plex Mono,monospace;font-size:0.95rem;font-weight:700;color:{col2};">{val}</div>
                        </div>""", unsafe_allow_html=True)
                    fig_eq=go.Figure(go.Scatter(x=eq_df.index,y=eq_df['equity'],
                        line=dict(color=rc,width=1.5),fill='tozeroy',
                        fillcolor=f"rgba({'0,230,118' if stats['total_return']>=0 else '255,61,87'},0.05)"))
                    fig_eq.add_hline(y=stats['initial'],line=dict(color=C['TXT3'],width=0.7,dash='dot'))
                    fig_eq.update_layout(**base_layout(C,280,"Equity Curve"))
                    st.plotly_chart(fig_eq,use_container_width=True,config=CFG0)
                    buy_d=[t['entry_date'] for t in trades]; buy_p=[t['entry_price'] for t in trades]
                    sell_d=[t['exit_date'] for t in trades]; sell_p=[t['exit_price'] for t in trades]
                    fig_tr=go.Figure()
                    fig_tr.add_trace(go.Scatter(x=df_bt.index,y=df_bt['Close'].squeeze(),line=dict(color=BLUE,width=1.2),name='Price'))
                    fig_tr.add_trace(go.Scatter(x=buy_d,y=buy_p,mode='markers',name='BUY',marker=dict(color=UP,size=8,symbol='triangle-up')))
                    fig_tr.add_trace(go.Scatter(x=sell_d,y=sell_p,mode='markers',name='SELL',marker=dict(color=DOWN,size=8,symbol='triangle-down')))
                    fig_tr.update_layout(**base_layout(C,320,"Trade Entries & Exits"))
                    st.plotly_chart(fig_tr,use_container_width=True,config=CFG0)
                    st.markdown(lbl("Trade Log",C=C), unsafe_allow_html=True)
                    tdf=pd.DataFrame(trades)
                    tdf['entry_date']=pd.to_datetime(tdf['entry_date']).dt.strftime('%Y-%m-%d')
                    tdf['exit_date']=pd.to_datetime(tdf['exit_date']).dt.strftime('%Y-%m-%d')
                    exit_col = tdf.pop('exit_reason') if 'exit_reason' in tdf.columns else None
                    tdf.columns=['Entry','Exit','Entry $','Exit $','Return %','P&L $']
                    if exit_col is not None:
                        tdf['Exit Reason'] = exit_col.values
                    st.dataframe(tdf,use_container_width=True,hide_index=True)

    else:
        # ── AI QUANT BACKTESTER ────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(41,121,255,0.08),rgba(0,230,118,0.04));
            border:1px solid {BLUE}44;border-radius:12px;padding:16px 20px;margin-bottom:16px;">
            <div style="font-family:DM Sans,sans-serif;font-size:1.2rem;font-weight:800;color:{C['TXT1']};margin-bottom:4px;">AI Quant Analyst</div>
            <div style="font-family:Inter,sans-serif;font-size:0.85rem;color:{C['TXT2']};line-height:1.5;">
                Describe any trading strategy in plain English. The AI will analyse the market data,
                evaluate your strategy's technical validity, generate signals, run the backtest,
                and give you a full institutional-grade report — even on short timeframes.
            </div>
        </div>""", unsafe_allow_html=True)

        ai_strat = st.text_area("",
            placeholder="""Describe your strategy. Examples:
• Buy when RSI drops below 35 and the price is above the 200 EMA. Exit when RSI goes above 65 or price drops 3% from entry.
• ICT strategy: buy after a liquidity sweep below the previous day low when price is in a bullish order block. Sell at the next resistance.
• Buy when the MACD histogram turns positive AND volume is 1.5x the 20-day average. Use a 2% stop loss and 4% target.
• Wyckoff spring setup: flat accumulation + low volume + price dips below support and recovers quickly.""",
            height=130, key="ai_strat_input", label_visibility="collapsed")

        ai_col1, ai_col2 = st.columns([3,1])
        with ai_col2:
            include_backtest = st.checkbox("Run backtest on signals", value=True, key="ai_run_bt")
            show_code = st.checkbox("Show generated code", value=False, key="ai_show_code")

        if st.button("ANALYSE WITH AI QUANT", key="ai_bt_run"):
            if not ai_strat or len(ai_strat.strip()) < 10:
                st.warning("Please describe your strategy first.")
            else:
                secret_key = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
                if not secret_key:
                    st.error("API key needed. Add ANTHROPIC_API_KEY to Streamlit secrets.")
                    st.stop()

                pc=PERIOD_CODES.get(bt_per,"1y")
                tmap={"1D":"1d","1h":"1h","4h":"1h","1W":"1wk","15m":"15m","1m":"1m","5m":"5m"}
                inv=tmap[bt_tf]
                if inv in ["1m","5m"] and pc in ["5y","2y","1y","6mo"]: pc="60d"
                elif inv=="15m" and pc in ["5y","2y"]: pc="60d"

                with st.spinner(f"Downloading {bt_ticker} data..."):
                    df_ai = get_data(bt_ticker, pc, inv)

                if df_ai is None or len(df_ai) < 20:
                    st.error(f"No data for {bt_ticker}. Try a different symbol or longer period.")
                    st.stop()

                df_ai = add_indicators(df_ai)
                df_ai.dropna(inplace=True)

                avail_cols = [col for col in df_ai.columns if col not in ['Open','High','Low','Close','Volume']]
                latest = df_ai.iloc[-1]
                price = float(latest['Close'])
                rsi_val = float(latest.get('rsi', 0))
                macd_val = float(latest.get('mc', 0))
                adx_val = float(latest.get('adx', 0))
                vol_ratio = float(df_ai['Volume'].squeeze().iloc[-1] / df_ai['Volume'].squeeze().rolling(20).mean().iloc[-1]) if 'Volume' in df_ai else 1.0

                market_context = f"""
Symbol: {bt_ticker}
Timeframe: {bt_tf} | Period: {bt_per} | Data points: {len(df_ai)}
Current Price: {price:.4f}
RSI(14): {rsi_val:.1f}
MACD: {macd_val:.4f}
ADX: {adx_val:.1f}
Volume vs 20MA: {vol_ratio:.2f}x
Available indicators: {', '.join(avail_cols[:20])}
"""
                import json, urllib.request as ur

                # Step 1: AI Analysis
                analysis_prompt = f"""You are a senior quantitative analyst at a top hedge fund with 20 years experience.

A trader wants to backtest this strategy:
"{ai_strat}"

Market data context:
{market_context}

Provide a COMPLETE institutional-grade analysis:

1. STRATEGY INTERPRETATION
   - What is this strategy actually doing (in precise technical terms)?
   - What market conditions does it work best in?
   - What indicators/signals are required?

2. TECHNICAL VALIDITY SCORE (0-10)
   - Rate the strategy's technical soundness
   - Explain edge (why should this work?)
   - Risk of overfitting?

3. MARKET CONDITION ASSESSMENT
   - Is current market favorable for this strategy?
   - Current RSI={rsi_val:.1f}, ADX={adx_val:.1f} — what does this mean for the strategy?

4. ENTRY/EXIT RULES (precise)
   - Exact entry conditions
   - Exact exit conditions (profit target + stop loss)
   - Position sizing recommendation

5. EXPECTED PERFORMANCE
   - Realistic win rate range
   - Expected profit factor
   - Max drawdown expectation
   - Best timeframes for this strategy

6. RISKS & WEAKNESSES
   - When does this strategy fail?
   - What to watch out for?

7. IMPROVEMENTS
   - How would you enhance this strategy?
   - What additional filters would you add?

Be specific, quantitative, and blunt. No fluff."""

                with st.spinner("AI Quant is analysing your strategy..."):
                    try:
                        payload = json.dumps({
                            "model": "claude-haiku-4-5-20251001",
                            "max_tokens": 2000,
                            "messages": [{"role": "user", "content": analysis_prompt}]
                        }).encode()
                        req = ur.Request("https://api.anthropic.com/v1/messages", data=payload,
                            headers={"Content-Type":"application/json","x-api-key":secret_key,
                                     "anthropic-version":"2023-06-01"}, method="POST")
                        with ur.urlopen(req, timeout=45) as resp:
                            analysis = json.loads(resp.read())["content"][0]["text"]
                    except Exception as e:
                        st.error(f"AI error: {e}")
                        st.stop()

                # Display analysis
                st.markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};
                    border-radius:12px;padding:20px;margin:12px 0;">
                    <div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;font-weight:700;
                                 letter-spacing:0.14em;text-transform:uppercase;color:{BLUE};margin-bottom:12px;">
                        AI QUANT ANALYSIS — {bt_ticker} · {bt_tf}</div>
                    <div style="font-family:Inter,sans-serif;font-size:0.88rem;color:{C['TXT2']};
                                 line-height:1.7;white-space:pre-wrap;">{analysis}</div>
                </div>""", unsafe_allow_html=True)

                # Step 2: Generate and run backtest signals
                if include_backtest:
                    code_prompt = f"""Convert this trading strategy to Python signal generation code.

Strategy: {ai_strat}

DataFrame 'df' has these columns: Close, Open, High, Low, Volume, {', '.join(avail_cols[:15])}
All columns accessed as: df['rsi'].squeeze(), df['Close'].squeeze() etc.

Write ONLY this function, no imports, no markdown, no explanation:

def generate_signals(df):
    import pandas as pd
    import numpy as np
    signals = pd.Series(0, index=df.index)
    c = df['Close'].squeeze()
    # add your signal logic here
    # signals = 1 for BUY, -1 for SELL, 0 for hold
    return signals

Rules:
- Use .squeeze() on every column access
- Return pd.Series with same index as df
- Handle NaN values with .fillna(0)
- Keep it simple and robust"""

                    with st.spinner("AI generating backtest signals..."):
                        try:
                            payload2 = json.dumps({
                                "model": "claude-haiku-4-5-20251001",
                                "max_tokens": 800,
                                "messages": [{"role": "user", "content": code_prompt}]
                            }).encode()
                            req2 = ur.Request("https://api.anthropic.com/v1/messages", data=payload2,
                                headers={"Content-Type":"application/json","x-api-key":secret_key,
                                         "anthropic-version":"2023-06-01"}, method="POST")
                            with ur.urlopen(req2, timeout=30) as resp2:
                                code = json.loads(resp2.read())["content"][0]["text"]
                            code = code.replace("```python","").replace("```","").strip()

                            if show_code:
                                st.code(code, language='python')

                            # Execute the generated signals
                            ns = {'df': df_ai, 'pd': pd, 'np': np}
                            exec(code, ns)
                            raw_signals = ns['generate_signals'](df_ai)
                            if not isinstance(raw_signals, pd.Series):
                                raw_signals = pd.Series(raw_signals, index=df_ai.index)
                            signals_clean = raw_signals.fillna(0).astype(int)

                            # Run simulation
                            c2 = df_ai['Close'].squeeze()
                            pos=0; cash=bt_cap; shares=0; trades=[]; equity_curve=[]; ep=0; ed=None
                            for i in range(len(df_ai)):
                                price2=float(c2.iloc[i]); sig=int(signals_clean.iloc[i]); date=df_ai.index[i]
                                if sig==1 and pos==0:
                                    shares=cash/price2; ep=price2; ed=date; cash=0; pos=1
                                elif sig==-1 and pos==1:
                                    cash=shares*price2
                                    trades.append({'entry_date':ed,'exit_date':date,
                                        'entry_price':round(ep,4),'exit_price':round(price2,4),
                                        'return':round((price2-ep)/ep*100,2),
                                        'pnl':round(shares*(price2-ep),2)})
                                    shares=0; pos=0
                                equity_curve.append({'date':date,'equity':cash+shares*price2})

                            if pos==1:
                                p_f=float(c2.iloc[-1]); cash=shares*p_f
                                trades.append({'entry_date':ed,'exit_date':df_ai.index[-1],
                                    'entry_price':round(ep,4),'exit_price':round(p_f,4),
                                    'return':round((p_f-ep)/ep*100,2),'pnl':round(shares*(p_f-ep),2)})

                            sig_count = int((signals_clean!=0).sum())
                            st.markdown(f"""<div style="font-family:IBM Plex Mono,monospace;font-size:0.65rem;color:{C['TXT3']};padding:6px 0;">
                                {sig_count} signals generated on {len(df_ai)} candles</div>""",
                                unsafe_allow_html=True)

                            if not trades:
                                st.warning(f"No complete trades from {sig_count} signals. The strategy may need more data or different parameters.")
                            else:
                                eq_df2 = pd.DataFrame(equity_curve).set_index('date')
                                wins=[t for t in trades if t['pnl']>0]
                                losses=[t for t in trades if t['pnl']<=0]
                                fe=cash if pos==0 else shares*float(c2.iloc[-1])
                                peak=bt_cap; mdd=0
                                for eq in eq_df2['equity']:
                                    if eq>peak: peak=eq
                                    dd=(peak-eq)/peak*100
                                    if dd>mdd: mdd=dd
                                total_ret=(fe-bt_cap)/bt_cap*100
                                wr=len(wins)/len(trades)*100 if trades else 0
                                pf_num=sum(t['pnl'] for t in wins)
                                pf_den=abs(sum(t['pnl'] for t in losses))
                                pf=pf_num/pf_den if pf_den>0 else 99

                                rc2=UP if total_ret>=0 else DOWN
                                st.markdown(f"""<div style="background:{'rgba(0,230,118,0.06)' if total_ret>=0 else 'rgba(255,61,87,0.06)'};
                                    border:1px solid {rc2};border-radius:12px;padding:18px 20px;margin:12px 0;">
                                    <div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:6px;">
                                        AI STRATEGY BACKTEST — {bt_ticker} · {bt_tf} · {bt_per}</div>
                                    <div style="font-family:DM Sans,sans-serif;font-size:2.4rem;font-weight:900;color:{rc2};line-height:1;">
                                        {'+' if total_ret>=0 else ''}{total_ret:.2f}%</div>
                                    <div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;color:{C['TXT2']};margin-top:4px;">
                                        ${bt_cap:,} → ${fe:,.2f} · {len(trades)} trades · Win Rate {wr:.1f}%</div>
                                </div>""", unsafe_allow_html=True)

                                si2=[("WIN RATE",f"{wr:.1f}%",UP),
                                     ("TRADES",str(len(trades)),C['TXT1']),
                                     ("WINS",str(len(wins)),UP),
                                     ("LOSSES",str(len(losses)),DOWN),
                                     ("PROFIT FACTOR",f"{pf:.2f}",UP if pf>=1 else DOWN),
                                     ("MAX DD",f"-{mdd:.1f}%",DOWN),
                                     ("FINAL EQ",f"${fe:,.0f}",rc2),
                                     ("SIGNALS",str(sig_count),AMBER)]
                                sc2_cols=st.columns(8)
                                for i3,(lbl3,val3,col3) in enumerate(si2):
                                    sc2_cols[i3].markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;padding:10px;text-align:center;">
                                        <div style="font-family:IBM Plex Mono,monospace;font-size:0.55rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:3px;">{lbl3}</div>
                                        <div style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;font-weight:700;color:{col3};">{val3}</div>
                                    </div>""", unsafe_allow_html=True)

                                fig_eq2=go.Figure(go.Scatter(x=eq_df2.index,y=eq_df2['equity'],
                                    line=dict(color=rc2,width=1.5),fill='tozeroy',
                                    fillcolor=f"rgba({'0,230,118' if total_ret>=0 else '255,61,87'},0.05)"))
                                fig_eq2.add_hline(y=bt_cap,line=dict(color=C['TXT3'],width=0.7,dash='dot'))
                                fig_eq2.update_layout(**base_layout(C,280,"AI Strategy Equity Curve"))
                                st.plotly_chart(fig_eq2,use_container_width=True,config=CFG0)

                                buy_d2=[t['entry_date'] for t in trades]
                                buy_p2=[t['entry_price'] for t in trades]
                                sell_d2=[t['exit_date'] for t in trades]
                                sell_p2=[t['exit_price'] for t in trades]
                                fig_tr2=go.Figure()
                                fig_tr2.add_trace(go.Scatter(x=df_ai.index,y=df_ai['Close'].squeeze(),
                                    line=dict(color=BLUE,width=1.2),name='Price'))
                                fig_tr2.add_trace(go.Scatter(x=buy_d2,y=buy_p2,mode='markers',
                                    name='BUY',marker=dict(color=UP,size=8,symbol='triangle-up')))
                                fig_tr2.add_trace(go.Scatter(x=sell_d2,y=sell_p2,mode='markers',
                                    name='SELL',marker=dict(color=DOWN,size=8,symbol='triangle-down')))
                                fig_tr2.update_layout(**base_layout(C,300,"AI Strategy — Trade Entries & Exits"))
                                st.plotly_chart(fig_tr2,use_container_width=True,config=CFG0)

                                st.markdown(lbl("Trade Log",C=C), unsafe_allow_html=True)
                                tdf2=pd.DataFrame(trades)
                                tdf2['entry_date']=pd.to_datetime(tdf2['entry_date']).dt.strftime('%Y-%m-%d %H:%M')
                                tdf2['exit_date']=pd.to_datetime(tdf2['exit_date']).dt.strftime('%Y-%m-%d %H:%M')
                                if 'exit_reason' in tdf2.columns:
                                    tdf2 = tdf2.drop(columns=['exit_reason'])
                                tdf2.columns=['Entry','Exit','Entry $','Exit $','Return %','P&L $']
                                st.dataframe(tdf2,use_container_width=True,hide_index=True)

                        except Exception as e:
                            st.error(f"Backtest generation error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

elif page=="portfolio":
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-family:DM Sans,sans-serif;font-size:1.8rem;font-weight:900;color:{C['TXT1']};margin-bottom:16px;">Portfolio</div>""", unsafe_allow_html=True)
    pc1,pc2,pc3,pc4,pc5=st.columns([2,1,1,1,1])
    port_q=pc1.text_input("Symbol","",placeholder="Symbol...",key="port_q",label_visibility="collapsed")
    port_m=search_tickers(port_q) if port_q else []
    if port_m:
        ps=pc1.selectbox("",["— select —"]+port_m,key="port_sel",label_visibility="collapsed")
        port_ticker=ps.split(" — ")[0] if ps and ps!="— select —" else port_q.strip().upper()
    else: port_ticker=port_q.strip().upper() if port_q else ""
    port_qty=pc2.number_input("Qty",value=1.0,min_value=0.0001,format="%.4f",key="port_qty",label_visibility="collapsed")
    port_cost=pc3.number_input("Avg Cost",value=0.0,min_value=0.0,format="%.4f",key="port_cost",label_visibility="collapsed")
    port_type=pc4.selectbox("Type",["Stock","Crypto","ETF","Futures","Forex"],key="port_type",label_visibility="collapsed")
    if pc5.button("Add",key="port_add") and port_ticker and port_cost>0:
        st.session_state.portfolio.append({'ticker':port_ticker,'qty':port_qty,'cost':port_cost,'type':port_type})
        st.rerun()
    if not st.session_state.portfolio:
        st.markdown(f"""<div style="text-align:center;padding:40px;background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;margin:16px 0;">
            <div style="font-family:Inter,sans-serif;font-size:1rem;color:{C['TXT3']};">Add positions above to track your portfolio.</div>
        </div>""", unsafe_allow_html=True)
    else:
        total_val=0;total_cost=0;positions=[]
        for pos in st.session_state.portfolio:
            p,_,_=price_info(pos['ticker'])
            if p:
                val=p*pos['qty'];cost=pos['cost']*pos['qty'];pnl=val-cost
                pnl_pct=(pnl/cost)*100 if cost>0 else 0
                total_val+=val;total_cost+=cost
                positions.append({**pos,'price':p,'value':val,'pnl':pnl,'pnl_pct':pnl_pct})
        total_pnl=total_val-total_cost
        total_pnl_pct=(total_pnl/total_cost)*100 if total_cost>0 else 0
        pm1,pm2,pm3,pm4=st.columns(4)
        pm1.metric("Portfolio Value",f"${total_val:,.2f}")
        pm2.metric("Total Cost",f"${total_cost:,.2f}")
        pm3.metric("Total P&L",f"${total_pnl:+,.2f}",f"{total_pnl_pct:+.2f}%")
        pm4.metric("Positions",str(len(positions)))
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        hdr=f'<div style="display:grid;grid-template-columns:90px 80px 90px 100px 110px 110px 130px 60px;gap:4px;padding:8px 12px;border-bottom:2px solid {C["BOR"]};">'
        for h2 in ["TICKER","TYPE","QTY","AVG COST","CUR PRICE","VALUE","P&L","DEL"]:
            hdr+=f'<span style="font-family:Space Mono;font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{C["TXT3"]};">{h2}</span>'
        hdr+="</div>"; st.markdown(hdr, unsafe_allow_html=True)
        for idx2,pos in enumerate(positions):
            pc2=UP if pos['pnl']>=0 else DOWN; sign2="+" if pos['pnl']>=0 else ""
            st.markdown(f"""<div style="display:grid;grid-template-columns:90px 80px 90px 100px 110px 110px 130px 60px;
                gap:4px;padding:8px 12px;border-bottom:1px solid {C['BOR']};align-items:center;">
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.8rem;font-weight:700;color:{C['TXT1']};">{pos['ticker']}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{C['TXT3']};">{pos['type']}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;color:{C['TXT2']};">{pos['qty']}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;color:{C['TXT2']};">${pos['cost']:.4f}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;font-weight:600;color:{C['TXT1']};">${pos['price']:.4f}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;color:{C['TXT2']};">${pos['value']:,.2f}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;font-weight:700;color:{pc2};">{sign2}${pos['pnl']:,.2f} ({sign2}{pos['pnl_pct']:.2f}%)</span>
            </div>""", unsafe_allow_html=True)
            if st.button("Remove",key=f"rm_{idx2}"):
                st.session_state.portfolio.pop(idx2); st.rerun()
        if len(positions)>1:
            COLORS=[BLUE,UP,AMBER,PURP,CYAN,ROSE,DOWN,'#94a3b8']
            fig_pie=go.Figure(go.Pie(
                labels=[p['ticker'] for p in positions],
                values=[p['value'] for p in positions],
                hole=0.55,marker=dict(colors=COLORS[:len(positions)]),
                textfont=dict(family='Space Mono',size=10)))
            fig_pie.update_layout(paper_bgcolor=C['BG0'],height=300,
                font=dict(family='Space Mono',color=C['TXT2'],size=10),
                margin=dict(l=0,r=0,t=20,b=0),
                legend=dict(font=dict(size=9,color=C['TXT2']),bgcolor='rgba(0,0,0,0)'))
            st.plotly_chart(fig_pie,use_container_width=True,config=CFG0)
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="moneyman":
    if "mm_msgs" not in st.session_state: st.session_state.mm_msgs=[]
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)

    # Header
    st.markdown(
        f'<div style="padding:0 0 14px;border-bottom:1px solid {C["BOR"]};margin-bottom:16px;display:flex;align-items:baseline;justify-content:space-between;">'
        f'<div>'
        f'<div style="font-family:DM Sans,sans-serif;font-size:1.4rem;font-weight:700;color:{C["TXT1"]};">MoneyMan</div>'
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:{C["TXT3"]};margin-top:3px;">AI Hedge Fund Manager · Macro · Equities · Options</div>'
        f'</div>'
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:{C["TXT3"]};">Powered by Claude · API key from Streamlit secrets</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    mm_left, mm_right = st.columns([3, 1])

    with mm_left:
        # Chat history container
        chat_html = (
            f'<div id="mm-chat" style="background:{C["BG2"]};border:1px solid {C["BOR"]};'
            f'border-radius:6px;padding:16px;height:480px;overflow-y:auto;margin-bottom:10px;">'
        )
        if not st.session_state.mm_msgs:
            chat_html += (
                f'<div style="display:flex;align-items:center;justify-content:center;height:100%;">'
                f'<div style="text-align:center;">'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.65rem;font-weight:600;'
                f'letter-spacing:0.12em;text-transform:uppercase;color:{C["TXT3"]};margin-bottom:8px;">MONEYMAN ONLINE</div>'
                f'<div style="font-family:Inter,sans-serif;font-size:0.85rem;color:{C["TXT3"]};line-height:1.8;">'
                f'Ask about any market, strategy, trade idea, or analysis.</div>'
                f'</div></div>'
            )
        for msg in st.session_state.mm_msgs:
            if msg["role"] == "user":
                chat_html += (
                    f'<div style="background:{C["BG3"]};border-left:2px solid {BLUE};'
                    f'padding:10px 14px;margin:6px 0;border-radius:0 4px 4px 0;">'
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;font-weight:600;'
                    f'letter-spacing:0.1em;text-transform:uppercase;color:{BLUE};margin-bottom:5px;">YOU</div>'
                    f'<div style="font-family:Inter,sans-serif;font-size:0.85rem;color:{C["TXT2"]};line-height:1.55;">'
                    f'{msg["content"]}</div></div>'
                )
            else:
                chat_html += (
                    f'<div style="background:{C["BG1"]};border-left:2px solid {C["UP"]};'
                    f'padding:10px 14px;margin:6px 0;border-radius:0 4px 4px 0;">'
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.56rem;font-weight:600;'
                    f'letter-spacing:0.1em;text-transform:uppercase;color:{C["UP"]};margin-bottom:5px;">MONEYMAN</div>'
                    f'<div style="font-family:Inter,sans-serif;font-size:0.85rem;color:{C["TXT2"]};line-height:1.6;white-space:pre-wrap;">'
                    f'{msg["content"]}</div></div>'
                )
        chat_html += (
            '</div>'
            '<script>var c=document.getElementById("mm-chat");if(c)c.scrollTop=c.scrollHeight;</script>'
        )
        st.markdown(chat_html, unsafe_allow_html=True)

        # Input row — text_input + send button side by side
        inp_c1, inp_c2 = st.columns([5, 1])
        with inp_c1:
            user_in = st.text_input(
                "", placeholder="Ask MoneyMan anything about markets...",
                key="mm_input", label_visibility="collapsed"
            )
        with inp_c2:
            send = st.button("Send", key="mm_send", use_container_width=True)

        if (send or user_in) and user_in.strip():
            msg_text = user_in.strip()
            st.session_state.mm_msgs.append({"role":"user","content":msg_text})
            with st.spinner(""):
                reply = call_mm(st.session_state.mm_msgs, st.session_state.get("mm_key",""))
            st.session_state.mm_msgs.append({"role":"assistant","content":reply})
            st.rerun()

    with mm_right:
        st.markdown(lbl("Settings",C=C), unsafe_allow_html=True)
        api_key = st.text_input(
            "API Key", "", placeholder="sk-ant-...",
            key="mm_key", type="password", label_visibility="collapsed"
        )
        st.markdown(
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:{C["TXT3"]};'
            f'line-height:1.8;padding:4px 0 12px;">console.anthropic.com<br>Session only.</div>',
            unsafe_allow_html=True
        )
        if st.button("Clear Chat", key="mm_clr", use_container_width=True):
            st.session_state.mm_msgs = []; st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(lbl("Quick Prompts",C=C), unsafe_allow_html=True)
        for qp in QUICK_ASKS:
            if st.button(qp, key=f"qp_{hash(qp)}", use_container_width=True):
                st.session_state.mm_msgs.append({"role":"user","content":qp})
                with st.spinner(""):
                    reply = call_mm(st.session_state.mm_msgs, st.session_state.get("mm_key",""))
                st.session_state.mm_msgs.append({"role":"assistant","content":reply})
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

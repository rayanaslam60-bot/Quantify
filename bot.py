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
from modules.data        import TIMEFRAMES, get_data, price_info, fetch_news, add_indicators
from modules.signals     import get_signals_cached, compute_signals, train_model, ml_predict
from modules.charts      import base_layout, mini_chart, CFG, CFG0
from modules.moneyman    import call_mm, QUICK_ASKS
from modules.backtest    import STRATEGY_CATEGORIES, STRATEGY_DESC, run_backtest
from modules.tradingview import get_tv_symbol, TV_INTERVALS

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
        <div style="font-family:'Outfit';font-size:0.7rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:4px;">{name}</div>
        <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">
            <span style="font-family:'Outfit';font-size:2.2rem;font-weight:800;color:{C['TXT1']};letter-spacing:-0.02em;">{ticker}</span>
            <span style="font-family:'Space Mono';font-size:1.8rem;font-weight:400;color:{C['TXT1']};">{p:,.4f}</span>
            <span style="font-family:'Space Mono';font-size:0.9rem;color:{col};">{sign}{chg:.4f} ({sign}{pct:.2f}%)</span>
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

PAGES=[("📊","Dashboard"),("📈","Equities"),("₿","Crypto"),
       ("🛢","Commodities"),("📦","Futures"),("⚙","Options"),
       ("📰","News"),("🔬","Backtest"),("💬","MoneyMan"),("💼","Portfolio")]

with st.sidebar:
    st.markdown(f"""<div style="padding:20px 20px 16px;border-bottom:1px solid {C['BOR']};">
        <div style="font-family:'Outfit';font-size:1.8rem;font-weight:900;color:{C['TXT1']};letter-spacing:-0.03em;">Quantify</div>
        <div style="font-family:'Space Mono';font-size:0.58rem;font-weight:700;letter-spacing:0.16em;color:{C['TXT3']};text-transform:uppercase;margin-top:2px;">Market Intelligence</div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"<div style='padding:0 12px;margin-top:10px;'>", unsafe_allow_html=True)

    with st.expander("⚙  Settings", expanded=False):
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
    for icon,page in PAGES:
        pg=page.lower()
        if st.button(f"{icon}  {page}",key=f"nav_{pg}",use_container_width=True):
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
                    <div style="font-family:'Space Mono';font-size:0.75rem;font-weight:700;color:{C['TXT1']};">{wt}</div>
                    <div style="font-family:'Space Mono';font-size:0.68rem;color:{C['TXT2']};">{p2:,.2f}</div>
                    <div style="font-family:'Space Mono';font-size:0.62rem;color:{col2};">{sign2}{pct2:.2f}%</div>
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
        <span style="font-family:'Space Mono';font-size:0.62rem;font-weight:700;letter-spacing:0.12em;color:{msc};">NYSE {ms}</span>
        <span style="font-family:'Space Mono';font-size:0.58rem;color:{C['TXT4']};margin-left:8px;">{now2.strftime('%H:%M')}</span>
    </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_symbol_page(ticker):
    tv_theme = "dark" if C['DARK'] else "light"
    st.markdown(f"<div style='padding:0 1.5rem;'>", unsafe_allow_html=True)
    st.markdown(price_badge(ticker), unsafe_allow_html=True)

    TFS=[("5M","7d","5m"),("15M","30d","15m"),("1H","60d","1h"),("4H","180d","1h"),("1D","2y","1d")]
    st.markdown(lbl("Timeframe Signals",C=C), unsafe_allow_html=True)
    tf_cols=st.columns(len(TFS))
    for i,(lab,per,inv) in enumerate(TFS):
        with tf_cols[i]:
            _,ov,sc=get_signals_cached(ticker,per,inv)
            c2=sig_color(ov);bg2=sig_bg(ov);bl2=sig_border(ov)
            st.markdown(f"""<div style="background:{bg2};border:1px solid {bl2};border-radius:8px;padding:12px 8px;text-align:center;">
                <div style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.12em;color:{C['TXT3']};margin-bottom:5px;">{lab}</div>
                <div style="font-family:'Outfit';font-size:0.95rem;font-weight:800;color:{c2};">{ov}</div>
                <div style="font-family:'Space Mono';font-size:0.6rem;color:{C['TXT3']};margin-top:2px;">{sc:+d}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Chart controls
    ctrl=st.columns([1,1,1,1,4])
    tf_sel=ctrl[0].selectbox("TF",list(TV_INTERVALS.keys()),index=5,
                               key=f"tf_{ticker}",label_visibility="collapsed")
    chart_style=ctrl[1].selectbox("Style",["Candles","Bars","Line","Area","Heikin Ashi"],
                                   key=f"cs_{ticker}",label_visibility="collapsed")
    show_rsi =ctrl[2].checkbox("RSI",value=True,key=f"rsi_{ticker}")
    show_macd=ctrl[3].checkbox("MACD",value=True,key=f"mac_{ticker}")

    STYLE_MAP={"Candles":"1","Bars":"0","Line":"2","Area":"3","Heikin Ashi":"8"}
    tv_style=STYLE_MAP.get(chart_style,"1")
    tv_int=TV_INTERVALS.get(tf_sel,"1D")
    tv_sym=get_tv_symbol(ticker)
    bg=C['BG0']
    safe_id=ticker.replace("-","").replace("=","").replace("^","")

    studies=["Volume@tv-basicstudies"]
    if show_rsi:  studies.append("RSI@tv-basicstudies")
    if show_macd: studies.append("MACD@tv-basicstudies")
    studies_js=", ".join([f'"{s}"' for s in studies])

    chart_html=f"""<html><head>
    <style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{background:{bg};}}
    #tvchart_{safe_id}{{height:680px;width:100%;}}</style></head><body>
    <div id="tvchart_{safe_id}"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
        autosize:true, symbol:"{tv_sym}", interval:"{tv_int}",
        timezone:"Etc/UTC", theme:"{tv_theme}", style:"{tv_style}", locale:"en",
        toolbar_bg:"{bg}", enable_publishing:false, allow_symbol_change:true,
        hide_side_toolbar:false, withdateranges:true, save_image:true,
        container_id:"tvchart_{safe_id}",
        studies:[{studies_js}],
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
    components.html(chart_html, height=700)

    # Signal analysis using data
    per2,inv2=TIMEFRAMES.get(tf_sel,("2y","1d"))
    with st.spinner(""):
        df=get_data(ticker,per2,inv2)
    if df is None or len(df)<20:
        st.markdown("</div>",unsafe_allow_html=True); return
    df=add_indicators(df)

    st.markdown("<hr>", unsafe_allow_html=True)
    left,right=st.columns([3,2])
    with left:
        sigs,ov,tot=compute_signals(df)
        model,scaler,acc,features=train_model(df.copy())
        ml_sig,ml_conf=ml_predict(df,model,scaler,features)
        buys=sum(1 for _,s,_ in sigs if s=="BUY")
        sells=sum(1 for _,s,_ in sigs if s=="SELL")
        c3=sig_color(ov);bg3=sig_bg(ov);bl3=sig_border(ov);ml_c=sig_color(ml_sig)
        st.markdown(f"""<div style="background:{bg3};border:1px solid {bl3};border-radius:12px;padding:18px 20px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                <div>
                    <div style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:6px;">Consensus Signal</div>
                    <div style="font-family:'Outfit';font-size:2.4rem;font-weight:900;color:{c3};line-height:1;letter-spacing:-0.02em;">{ov}</div>
                </div>
                <div style="text-align:right;font-family:'Space Mono';font-size:0.72rem;line-height:2;color:{C['TXT3']};">
                    <div><span style="color:{UP};">{buys} BUY</span> / <span style="color:{DOWN};">{sells} SELL</span></div>
                    <div>Score <span style="color:{c3};font-weight:700;">{tot:+d}</span></div>
                    <div>ML <span style="color:{ml_c};font-weight:700;">{ml_sig}</span> {ml_conf:.0%} · {acc:.0%} acc</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        rows=""
        for name,sig,detail in sigs:
            c4=sig_color(sig);bg4=sig_bg(sig);bl4=sig_border(sig)
            rows+=f"""<div style="display:flex;justify-content:space-between;align-items:center;
                background:{bg4};border-left:3px solid {bl4};padding:8px 14px;margin:2px 0;border-radius:0 8px 8px 0;">
                <span style="font-family:'Space Mono';font-size:0.65rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{C['TXT2']};">{name}</span>
                <span style="font-family:'Plus Jakarta Sans';font-size:0.75rem;color:{C['TXT3']};">{detail}</span>
                <span style="font-family:'Outfit';font-size:0.85rem;font-weight:800;color:{c4};">{sig}</span>
            </div>"""
        st.markdown(rows, unsafe_allow_html=True)

    with right:
        r=df.iloc[-1]
        stats=[("OPEN",f"{float(r['Open']):.4f}"),
               ("HIGH 20",f"{df['High'].squeeze().tail(20).max():.4f}"),
               ("LOW 20",f"{df['Low'].squeeze().tail(20).min():.4f}"),
               ("VOLUME",f"{int(r['Volume']):,}"),
               ("VOL MA",f"{int(r.get('vma',0)):,}"),
               ("ATR",f"{r.get('atr',float('nan')):.4f}"),
               ("VOLATILITY",f"{r.get('vol20',float('nan')):.2%}"),
               ("RSI",f"{r.get('rsi',float('nan')):.1f}"),
               ("ADX",f"{r.get('adx',float('nan')):.1f}"),
               ("CCI",f"{r.get('cci',float('nan')):.0f}"),
               ("WILLIAMS %R",f"{r.get('wr',float('nan')):.1f}"),
               ("MFI",f"{r.get('mfi',float('nan')):.1f}"),
               ("STOCH %K",f"{r.get('stk',float('nan')):.1f}"),
               ("BB WIDTH",f"{r.get('bbw',float('nan')):.4f}"),
               ("VWAP",f"{r.get('vwap',float('nan')):.4f}")]
        rows2="".join(f"""<div style="display:flex;justify-content:space-between;border-bottom:1px solid {C['BOR']};padding:5px 0;">
            <span style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.08em;color:{C['TXT3']};">{k}</span>
            <span style="font-family:'Space Mono';font-size:0.78rem;color:{C['TXT2']};">{v}</span>
        </div>""" for k,v in stats)
        st.markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;padding:16px;">
            {lbl("Statistics",C=C)}{rows2}</div>""", unsafe_allow_html=True)
        p2=float(r['Close']); ma_html=""
        for lb2,key2 in [("EMA 9","e9"),("EMA 21","e21"),("EMA 50","e50"),("EMA 200","e200")]:
            val=r.get(key2,float('nan'))
            if not np.isnan(float(val)):
                mc2=UP if p2>float(val) else DOWN
                ma_html+=f"""<div style="background:{C['BG0']};border:1px solid {C['BOR']};border-radius:8px;padding:10px 8px;flex:1;text-align:center;">
                    <div style="font-family:'Space Mono';font-size:0.58rem;font-weight:700;color:{C['TXT3']};margin-bottom:4px;">{lb2}</div>
                    <div style="font-family:'Space Mono';font-size:0.8rem;font-weight:700;color:{mc2};">{float(val):.2f}</div>
                </div>"""
        if ma_html:
            st.markdown(f'<div style="display:flex;gap:6px;margin-top:8px;">{ma_html}</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(lbl(f"News — {ticker}",C=C), unsafe_allow_html=True)
        for n in fetch_news(ticker,5):
            st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;display:block;">
            <div style="border-bottom:1px solid {C['BOR']};padding:9px 0;">
                <div style="font-family:'Plus Jakarta Sans';font-size:0.82rem;font-weight:500;color:{C['TXT2']};line-height:1.4;margin-bottom:4px;">{n['title']}</div>
                <div style="font-family:'Space Mono';font-size:0.58rem;color:{C['TXT3']};">{n['source'].upper()} · {n['time']}</div>
            </div></a>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

page=st.session_state.active_page
now=datetime.now()
mkt_min=now.hour*60+now.minute; is_wd=now.weekday()<5
if is_wd and 570<=mkt_min<960: ms2="MARKET OPEN"; msc2=UP
elif is_wd and mkt_min<570: ms2="PRE-MARKET"; msc2=AMBER
elif is_wd and mkt_min>=960: ms2="AFTER HOURS"; msc2=AMBER
else: ms2="MARKET CLOSED"; msc2=C['TXT3']

st.markdown(f"""<div style="background:{C['BG1']};border-bottom:2px solid {C['BOR']};padding:14px 1.5rem 12px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
    <div style="display:flex;align-items:baseline;gap:16px;">
      <span style="font-family:'Outfit';font-size:1.8rem;font-weight:900;color:{C['TXT1']};letter-spacing:-0.02em;">QUANTIFY</span>
      <span style="font-family:'Space Mono';font-size:0.65rem;font-weight:700;letter-spacing:0.14em;color:{C['TXT3']};text-transform:uppercase;">Professional Market Intelligence</span>
    </div>
    <div style="display:flex;align-items:center;gap:20px;">
      <span style="font-family:'Space Mono';font-size:0.82rem;font-weight:700;color:{msc2};letter-spacing:0.08em;">{ms2}</span>
      <span style="font-family:'Space Mono';font-size:0.68rem;color:{C['TXT3']};">{now.strftime('%a %b %d %Y · %H:%M')}</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

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
                <div style="font-family:'Space Mono';font-size:0.56rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:5px;">{nm}</div>
                <div style="font-family:'Space Mono';font-size:0.9rem;font-weight:700;color:{C['TXT1']};">{p:,.2f}</div>
                <div style="font-family:'Space Mono';font-size:0.7rem;font-weight:600;color:{col};margin-top:3px;">{sign}{pct:.2f}%</div>
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
            <div style="font-family:'Plus Jakarta Sans';font-size:0.9rem;color:{C['TXT3']};">Add tickers using the search above.</div>
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
                <span style="font-family:'Space Mono';font-size:0.82rem;font-weight:700;color:{C['TXT1']};">{tk}</span>
                <span style="font-family:'Plus Jakarta Sans';font-size:0.82rem;color:{C['TXT2']};">{name}</span>
                <span style="font-family:'Space Mono';font-size:0.82rem;font-weight:600;color:{C['TXT2']};text-align:right;">{p2:,.4f}</span>
                <span style="font-family:'Space Mono';font-size:0.78rem;font-weight:600;color:{pc};text-align:right;">{sign2}{pct2:.2f}%</span>
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
                col2=UP if (chg2 or 0)>=0 else DOWN; sign2="+" if (chg2 or 0)>=0 else ""
                st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
                    <span style="font-family:'Outfit';font-size:1rem;font-weight:800;color:{C['TXT1']};">{cn}</span>
                    <span style="font-family:'Space Mono';font-size:0.78rem;color:{col2};">{sign2}{(pct2 or 0):.2f}%</span>
                </div>""", unsafe_allow_html=True)
                render_tv_mini(ct2, tv_theme)

    with right:
        st.markdown(lbl("Headlines",C=C), unsafe_allow_html=True)
        for n in fetch_news("SPY",10):
            st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;display:block;">
            <div style="border-bottom:1px solid {C['BOR']};padding:9px 0;">
                <div style="font-family:'Plus Jakarta Sans';font-size:0.82rem;font-weight:500;color:{C['TXT2']};line-height:1.4;margin-bottom:4px;">{n['title']}</div>
                <div style="font-family:'Space Mono';font-size:0.58rem;color:{C['TXT3']};">{n['source'].upper()} · {n['time']}</div>
            </div></a>""", unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(lbl("Sectors",C=C), unsafe_allow_html=True)
        for st_t,st_n in [("XLK","TECH"),("XLF","FINANCE"),("XLE","ENERGY"),
                           ("XLV","HEALTH"),("XLI","INDUSTRIAL")]:
            _,ov3,_=get_signals_cached(st_t,"60d","1h")
            p3,_,pct3=price_info(st_t)
            c3=sig_color(ov3); sign3="+" if (pct3 or 0)>=0 else ""
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {C['BOR']};">
                <div><span style="font-family:'Space Mono';font-size:0.75rem;font-weight:700;color:{C['TXT1']};">{st_t}</span>
                     <span style="font-family:'Plus Jakarta Sans';font-size:0.68rem;color:{C['TXT3']};margin-left:6px;">{st_n}</span></div>
                <span style="font-family:'Outfit';font-size:0.82rem;font-weight:800;color:{c3};">{ov3}</span>
                <span style="font-family:'Space Mono';font-size:0.7rem;color:{'#00e676' if (pct3 or 0)>=0 else '#ff3d57'};">{sign3}{(pct3 or 0):.2f}%</span>
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
                <span style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};">Options Flow</span>
                <span style="font-family:'Outfit';font-size:1.6rem;font-weight:900;color:{sc2};">{s}</span>
                <span style="font-family:'Plus Jakarta Sans';font-size:0.85rem;color:{C['TXT2']};">
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
    st.markdown(f"""<div style="font-family:'Outfit';font-size:1.8rem;font-weight:900;color:{C['TXT1']};margin-bottom:4px;">News Feed</div>""", unsafe_allow_html=True)
    n_c1,n_c2=st.columns([2,4])
    with n_c1:
        nt=st.selectbox("",["SPY","AAPL","NVDA","TSLA","MSFT","META","BTC-USD","ETH-USD","GC=F","CL=F"],
                         key="news_tkr",label_visibility="collapsed")
        nl=st.selectbox("",["20 articles","40 articles","60 articles"],key="news_lim",label_visibility="collapsed")
        lim2=int(nl.split()[0])
    with n_c2:
        st.markdown(f"""<div style="font-family:'Space Mono';font-size:0.65rem;color:{C['TXT3']};padding:10px 0;">Yahoo Finance · Reuters · Bloomberg · CNBC · WSJ</div>""", unsafe_allow_html=True)
    with st.spinner("Loading..."):
        news_items=fetch_news(nt,lim2)
    if not news_items: st.warning("No news found.")
    else:
        nc1,nc2=st.columns(2)
        for i,n in enumerate(news_items):
            with nc1 if i%2==0 else nc2:
                st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;display:block;">
                <div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;padding:16px;margin-bottom:10px;">
                    <div style="font-family:'Plus Jakarta Sans';font-size:0.9rem;font-weight:600;color:{C['TXT1']};line-height:1.45;margin-bottom:8px;">{n['title']}</div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;color:{BLUE};">{n['source'].upper()}</span>
                        <span style="font-family:'Space Mono';font-size:0.6rem;color:{C['TXT3']};">{n['time']}</span>
                    </div>
                </div></a>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="backtest":
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-family:'Outfit';font-size:1.8rem;font-weight:900;color:{C['TXT1']};margin-bottom:4px;">Backtest Terminal</div>
    <div style="font-family:'Space Mono';font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:16px;">No-Code Strategy Testing · Any Symbol · Any Timeframe</div>""", unsafe_allow_html=True)
    bc1,bc2,bc3,bc4=st.columns([2,1,1,1])
    with bc1:
        bt_q=st.text_input("Symbol","SPY",placeholder="Type symbol...",key="bt_q",label_visibility="collapsed")
        bt_m=search_tickers(bt_q)
        if bt_m and bt_q:
            bt_s=st.selectbox("",["— select —"]+bt_m,key="bt_sel",label_visibility="collapsed")
            bt_ticker=bt_s.split(" — ")[0] if bt_s and bt_s!="— select —" else bt_q.strip().upper()
        else: bt_ticker=bt_q.strip().upper() if bt_q else "SPY"
    bt_tf=bc2.selectbox("TF",["1D","1h","4h","1W","15m"],key="bt_tf",label_visibility="collapsed")
    PERIODS={"1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y","2 Years":"2y","5 Years":"5y"}
    bt_per=bc3.selectbox("Period",list(PERIODS.keys()),index=3,key="bt_per",label_visibility="collapsed")
    bt_cap=bc4.number_input("Capital",value=10000,min_value=100,step=1000,key="bt_cap",label_visibility="collapsed")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    sc1,sc2=st.columns([2,3])
    with sc1:
        cat=st.selectbox("Category",list(STRATEGY_CATEGORIES.keys()),key="bt_cat",label_visibility="collapsed")
        sel_strat=st.selectbox("Strategy",STRATEGY_CATEGORIES[cat],key="bt_strat",label_visibility="collapsed")
    with sc2:
        st.markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;padding:14px 16px;margin-top:4px;">
            <div style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:6px;">Strategy</div>
            <div style="font-family:'Plus Jakarta Sans';font-size:0.88rem;color:{C['TXT2']};line-height:1.5;">{STRATEGY_DESC.get(sel_strat,'')}</div>
        </div>""", unsafe_allow_html=True)
    if st.button("RUN BACKTEST",key="run_bt"):
        pc=PERIODS[bt_per]; tmap={"1D":"1d","1h":"1h","4h":"1h","1W":"1wk","15m":"15m"}
        inv=tmap[bt_tf]
        if inv=="15m" and pc in ["5y","2y","1y"]: pc="60d"
        elif inv=="1h" and pc=="5y": pc="2y"
        with st.spinner(f"Running {sel_strat} on {bt_ticker}..."):
            df_bt=get_data(bt_ticker,pc,inv)
        if df_bt is None or len(df_bt)<50:
            st.error("Not enough data. Try longer period or 1D timeframe.")
        else:
            result,err=run_backtest(df_bt,sel_strat,bt_cap)
            if result is None: st.error(err)
            else:
                stats=result['stats']; trades=result['trades']; eq_df=result['equity']
                rc=UP if stats['total_return']>=0 else DOWN
                st.markdown(f"""<div style="background:{'rgba(0,230,118,0.06)' if stats['total_return']>=0 else 'rgba(255,61,87,0.06)'};
                    border:1px solid {rc};border-radius:12px;padding:18px 20px;margin:16px 0;">
                    <div style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:6px;">
                        {bt_ticker} · {bt_tf} · {bt_per} · {sel_strat}</div>
                    <div style="font-family:'Outfit';font-size:2.6rem;font-weight:900;color:{rc};line-height:1;">
                        {'+' if stats['total_return']>=0 else ''}{stats['total_return']}%</div>
                    <div style="font-family:'Space Mono';font-size:0.78rem;color:{C['TXT2']};margin-top:4px;">
                        ${stats['initial']:,} → ${stats['final_equity']:,}</div>
                </div>""", unsafe_allow_html=True)
                si=[("WIN RATE",f"{stats['win_rate']}%",UP),
                    ("TRADES",str(stats['total_trades']),C['TXT1']),
                    ("WINS",str(stats['winning']),UP),("LOSSES",str(stats['losing']),DOWN),
                    ("AVG WIN",f"+{stats['avg_win']}%",UP),("AVG LOSS",f"{stats['avg_loss']}%",DOWN),
                    ("PROFIT FACTOR",str(stats['profit_factor']),UP if stats['profit_factor']>=1 else DOWN),
                    ("MAX DRAWDOWN",f"-{stats['max_drawdown']}%",DOWN)]
                sc_cols=st.columns(8)
                for i2,(lbl2,val,col2) in enumerate(si):
                    sc_cols[i2].markdown(f"""<div style="background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;padding:12px;text-align:center;">
                        <div style="font-family:'Space Mono';font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{C['TXT3']};margin-bottom:4px;">{lbl2}</div>
                        <div style="font-family:'Space Mono';font-size:0.95rem;font-weight:700;color:{col2};">{val}</div>
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
                tdf.columns=['Entry','Exit','Entry $','Exit $','Return %','P&L $']
                st.dataframe(tdf,use_container_width=True,hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="portfolio":
    st.markdown(f"<div style='padding:16px 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-family:'Outfit';font-size:1.8rem;font-weight:900;color:{C['TXT1']};margin-bottom:16px;">Portfolio</div>""", unsafe_allow_html=True)
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
            <div style="font-family:'Plus Jakarta Sans';font-size:1rem;color:{C['TXT3']};">Add positions above to track your portfolio.</div>
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
                <span style="font-family:'Space Mono';font-size:0.8rem;font-weight:700;color:{C['TXT1']};">{pos['ticker']}</span>
                <span style="font-family:'Space Mono';font-size:0.7rem;color:{C['TXT3']};">{pos['type']}</span>
                <span style="font-family:'Space Mono';font-size:0.78rem;color:{C['TXT2']};">{pos['qty']}</span>
                <span style="font-family:'Space Mono';font-size:0.78rem;color:{C['TXT2']};">${pos['cost']:.4f}</span>
                <span style="font-family:'Space Mono';font-size:0.78rem;font-weight:600;color:{C['TXT1']};">${pos['price']:.4f}</span>
                <span style="font-family:'Space Mono';font-size:0.78rem;color:{C['TXT2']};">${pos['value']:,.2f}</span>
                <span style="font-family:'Space Mono';font-size:0.78rem;font-weight:700;color:{pc2};">{sign2}${pos['pnl']:,.2f} ({sign2}{pos['pnl_pct']:.2f}%)</span>
            </div>""", unsafe_allow_html=True)
            if st.button("✕",key=f"rm_{idx2}"):
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
    left2,right2=st.columns([3,1])
    with right2:
        st.markdown(lbl("API Key",C=C), unsafe_allow_html=True)
        api_key=st.text_input("","",placeholder="sk-ant-...",key="mm_key",type="password",label_visibility="collapsed")
        st.markdown(f"""<div style="font-family:'Space Mono';font-size:0.62rem;color:{C['TXT3']};line-height:1.8;padding:6px 0 14px;">
            console.anthropic.com<br>Session only. Never saved.</div>""", unsafe_allow_html=True)
        st.markdown(lbl("Quick Prompts",C=C), unsafe_allow_html=True)
        for qp in QUICK_ASKS:
            if st.button(qp,key=f"qp_{hash(qp)}"):
                st.session_state.mm_msgs.append({"role":"user","content":qp})
                with st.spinner(""):
                    reply=call_mm(st.session_state.mm_msgs,api_key)
                st.session_state.mm_msgs.append({"role":"assistant","content":reply})
                st.rerun()
        if st.button("CLEAR",key="mm_clr"): st.session_state.mm_msgs=[]; st.rerun()
    with left2:
        st.markdown(f"""<div style="padding:0 0 14px;border-bottom:1px solid {C['BOR']};margin-bottom:14px;">
            <div style="font-family:'Outfit';font-size:2rem;font-weight:900;color:{C['TXT1']};letter-spacing:-0.02em;">MoneyMan</div>
            <div style="font-family:'Space Mono';font-size:0.6rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{C['TXT3']};margin-top:3px;">
                30-Year Veteran · Goldman Sachs · Macro & Equities</div>
        </div>""", unsafe_allow_html=True)
        chat_html=f'<div style="background:{C["BG2"]};border:1px solid {C["BOR"]};border-radius:12px;padding:16px;height:520px;overflow-y:auto;margin-bottom:12px;">'
        if not st.session_state.mm_msgs:
            chat_html+=f"""<div style="padding:50px 0;text-align:center;">
                <div style="font-family:'Plus Jakarta Sans';font-size:1rem;font-weight:500;color:{C['TXT3']};line-height:2.4;">
                    MoneyMan is online.<br>Ask about any market, trade, or strategy.</div></div>"""
        for msg in st.session_state.mm_msgs:
            if msg['role']=='user':
                chat_html+=f"""<div style="background:{C['BG1']};border-left:3px solid {BLUE};padding:12px 16px;margin:8px 0;border-radius:0 12px 12px 0;">
                    <div style="font-family:'Space Mono';font-size:0.58rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{BLUE};margin-bottom:6px;">YOU</div>
                    <div style="font-family:'Plus Jakarta Sans';font-size:0.88rem;color:{C['TXT2']};line-height:1.55;">{msg['content']}</div>
                </div>"""
            else:
                chat_html+=f"""<div style="background:{C['BG1']};border-left:3px solid {UP};padding:12px 16px;margin:8px 0;border-radius:0 12px 12px 0;">
                    <div style="font-family:'Space Mono';font-size:0.58rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{UP};margin-bottom:6px;">MONEYMAN</div>
                    <div style="font-family:'Plus Jakarta Sans';font-size:0.88rem;color:{C['TXT2']};line-height:1.6;">{msg['content'].replace(chr(10),'<br>')}</div>
                </div>"""
        chat_html+='</div>'; st.markdown(chat_html, unsafe_allow_html=True)
        user_in=st.chat_input("Ask MoneyMan...")
        if user_in:
            st.session_state.mm_msgs.append({"role":"user","content":user_in})
            with st.spinner(""):
                reply=call_mm(st.session_state.mm_msgs,st.session_state.get("mm_key",""))
            st.session_state.mm_msgs.append({"role":"assistant","content":reply})
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

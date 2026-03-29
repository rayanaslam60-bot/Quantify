# modules/styles.py — Institutional dark terminal theme

import streamlit as st

def get_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    return st.session_state.theme

def get_colors():
    DARK = get_theme() == 'dark'
    return dict(
        DARK=DARK,
        BG0  = '#08090c' if DARK else '#f4f5f7',
        BG1  = '#0d0f14' if DARK else '#ffffff',
        BG2  = '#111318' if DARK else '#f8f9fa',
        BG3  = '#16191f' if DARK else '#eef0f3',
        BOR  = '#1e2128' if DARK else '#dde0e6',
        BOR2 = '#262b35' if DARK else '#c8ccd4',
        TXT1 = '#e8eaf0' if DARK else '#111318',
        TXT2 = '#8892a4' if DARK else '#3d4452',
        TXT3 = '#3d4452' if DARK else '#8892a4',
        TXT4 = '#262b35' if DARK else '#c8ccd4',
        UP   = '#00c97a',
        DOWN = '#e8384a',
        BLUE = '#3b82f6',
        AMBER= '#f59e0b',
        PURP = '#a78bfa',
        CYAN = '#06b6d4',
        ROSE = '#f43f5e',
        TEAL = '#14b8a6',
        GRID = '#0d0f14' if DARK else '#f0f2f5',
    )

def inject_css(C):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=IBM+Plex+Mono:wght@300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700;800&display=swap');

*{{box-sizing:border-box;margin:0;padding:0;}}

html,body,[class*="css"]{{
    font-family:'Inter',sans-serif;
    background:{C['BG0']};
    color:{C['TXT2']};
    font-size:13px;
    -webkit-font-smoothing:antialiased;
}}
.stApp{{background:{C['BG0']};}}
.main .block-container{{padding:0;max-width:100%;}}

/* Scrollbars */
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-track{{background:{C['BG0']};}}
::-webkit-scrollbar-thumb{{background:{C['BOR2']};border-radius:2px;}}
::-webkit-scrollbar-thumb:hover{{background:{C['TXT3']};}}

/* Sidebar */
section[data-testid="stSidebar"]{{
    background:{C['BG1']};
    border-right:1px solid {C['BOR']};
    width:260px!important;
    min-height:100vh;
}}
section[data-testid="stSidebar"] .block-container{{padding:0;}}
section[data-testid="stSidebar"] > div{{padding:0!important;}}

/* Hide Streamlit chrome */
#MainMenu{{display:none;}}
footer{{display:none;}}
header{{display:none;}}
.stDeployButton{{display:none;}}
[data-testid="stToolbar"]{{display:none;}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{{
    background:transparent;
    border-bottom:1px solid {C['BOR']};
    gap:0;padding:0 20px;
}}
.stTabs [data-baseweb="tab"]{{
    font-family:'IBM Plex Mono',monospace;
    font-size:0.68rem;font-weight:500;
    letter-spacing:0.06em;text-transform:uppercase;
    color:{C['TXT3']};padding:12px 16px;
    border-radius:0;background:transparent;
    border:none;border-bottom:2px solid transparent;
    transition:color 0.15s,border-color 0.15s;
}}
.stTabs [data-baseweb="tab"]:hover{{color:{C['TXT2']};}}
.stTabs [aria-selected="true"]{{
    color:{C['TXT1']}!important;
    border-bottom:2px solid {C['BLUE']}!important;
}}

/* Metrics */
div[data-testid="stMetricValue"]{{
    font-family:'IBM Plex Mono',monospace;
    font-size:1.05rem;font-weight:600;color:{C['TXT1']};
}}
div[data-testid="stMetricLabel"]{{
    font-family:'IBM Plex Mono',monospace;
    font-size:0.6rem;font-weight:500;
    letter-spacing:0.1em;text-transform:uppercase;color:{C['TXT3']};
}}
div[data-testid="metric-container"]{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;padding:14px 16px;
    transition:border-color 0.15s;
}}
div[data-testid="metric-container"]:hover{{border-color:{C['BOR2']};}}

/* Inputs */
.stSelectbox>div>div,.stMultiSelect>div>div{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;font-family:'IBM Plex Mono',monospace;
    font-size:0.78rem;color:{C['TXT2']};
    transition:border-color 0.15s;
}}
.stSelectbox>div>div:focus-within{{border-color:{C['BLUE']};}}
.stTextInput>div>div>input{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;font-family:'Inter',sans-serif;
    font-size:0.85rem;color:{C['TXT1']};padding:9px 12px;
    transition:border-color 0.15s;
}}
.stTextInput>div>div>input:focus{{border-color:{C['BLUE']};outline:none;}}
.stTextInput>div>div>input::placeholder{{color:{C['TXT3']};}}
.stNumberInput>div>div>input{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;font-family:'IBM Plex Mono',monospace;
    font-size:0.78rem;color:{C['TXT1']};
}}
.stTextArea>div>div>textarea{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;font-family:'Inter',sans-serif;
    font-size:0.85rem;color:{C['TXT1']};
    transition:border-color 0.15s;
}}
.stTextArea>div>div>textarea:focus{{border-color:{C['BLUE']};}}

/* Checkboxes and radios */
.stCheckbox label p{{
    font-family:'IBM Plex Mono',monospace;
    font-size:0.68rem;font-weight:500;
    letter-spacing:0.05em;text-transform:uppercase;color:{C['TXT3']};
}}
.stRadio label{{
    font-family:'Inter',sans-serif;
    font-size:0.82rem;font-weight:400;color:{C['TXT2']};
}}

/* Buttons */
.stButton>button{{
    background:{C['BG2']};
    border:1px solid {C['BOR']};
    color:{C['TXT2']};
    font-family:'IBM Plex Mono',monospace;
    font-size:0.68rem;font-weight:500;
    letter-spacing:0.06em;
    padding:8px 16px;border-radius:6px;
    text-transform:uppercase;
    transition:all 0.15s ease;
    cursor:pointer;
}}
.stButton>button:hover{{
    background:{C['BG3']};
    border-color:{C['BOR2']};
    color:{C['TXT1']};
    transform:translateY(-1px);
    box-shadow:0 4px 12px rgba(0,0,0,0.3);
}}
.stButton>button:active{{transform:translateY(0);}}

/* Primary button variant via container class */
.primary-btn .stButton>button{{
    background:{C['BLUE']};
    border-color:{C['BLUE']};
    color:#ffffff;
}}
.primary-btn .stButton>button:hover{{
    background:#2563eb;
    border-color:#2563eb;
    color:#ffffff;
}}

/* Expander */
.streamlit-expanderHeader{{
    font-family:'IBM Plex Mono',monospace;
    font-size:0.68rem;font-weight:500;
    letter-spacing:0.08em;text-transform:uppercase;
    color:{C['TXT3']};background:{C['BG1']};
    border:1px solid {C['BOR']};border-radius:6px;
    padding:10px 14px;
    transition:all 0.15s;
}}
.streamlit-expanderHeader:hover{{color:{C['TXT2']};border-color:{C['BOR2']};}}

/* DataFrames */
.stDataFrame{{border:1px solid {C['BOR']};border-radius:6px;overflow:hidden;}}
.stDataFrame th{{
    background:{C['BG2']};
    font-family:'IBM Plex Mono',monospace;
    font-size:0.65rem;font-weight:600;
    letter-spacing:0.08em;text-transform:uppercase;
    color:{C['TXT3']};
}}
.stDataFrame td{{
    font-family:'IBM Plex Mono',monospace;
    font-size:0.75rem;color:{C['TXT2']};
    border-color:{C['BOR']};
}}

/* Chat */
.stChatInput>div{{
    background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;
}}
.stChatInput textarea{{
    font-family:'Inter',sans-serif;
    font-size:0.85rem;color:{C['TXT1']};background:{C['BG2']};
}}

/* Dividers */
hr{{border:none;border-top:1px solid {C['BOR']};margin:16px 0;}}

/* Slider */
.stSlider>div>div>div{{background:{C['BLUE']};}}

/* Plotly chart container */
.js-plotly-plot{{border-radius:0;}}

/* Progress bars */
.stProgress>div>div{{background:{C['BLUE']};}}

/* Spinner */
.stSpinner>div{{border-color:{C['BLUE']} transparent transparent transparent;}}

/* Alerts */
.stAlert{{border-radius:6px;font-family:'Inter',sans-serif;font-size:0.82rem;}}

/* Status dots */
.status-dot{{
    display:inline-block;width:6px;height:6px;border-radius:50%;
    background:{C['UP']};margin-right:6px;
    animation:pulse 2s infinite;
}}
@keyframes pulse{{
    0%{{opacity:1;}}
    50%{{opacity:0.4;}}
    100%{{opacity:1;}}
}}

/* Card styles */
.card{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;padding:16px;
    transition:border-color 0.15s,box-shadow 0.15s;
}}
.card:hover{{
    border-color:{C['BOR2']};
    box-shadow:0 4px 20px rgba(0,0,0,0.2);
}}

/* Table rows */
.data-row{{
    padding:8px 12px;border-bottom:1px solid {C['BOR']};
    transition:background 0.1s;
}}
.data-row:hover{{background:{C['BG2']};}}

/* Sidebar nav items */
.nav-item{{
    padding:8px 16px;cursor:pointer;
    border-left:2px solid transparent;
    transition:all 0.15s;
    font-family:'Inter',sans-serif;
    font-size:0.82rem;font-weight:500;
    color:{C['TXT2']};
}}
.nav-item:hover{{
    background:{C['BG2']};
    color:{C['TXT1']};
    border-left-color:{C['BOR2']};
}}
.nav-item.active{{
    background:{C['BG2']};
    color:{C['TXT1']};
    border-left-color:{C['BLUE']};
}}
</style>
""", unsafe_allow_html=True)

def lbl(t, size="0.62rem", C=None):
    color = C['TXT3'] if C else '#3d4452'
    return f'<div style="font-family:IBM Plex Mono,monospace;font-size:{size};font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{color};margin-bottom:8px;">{t}</div>'

def section_header(title, subtitle="", C=None):
    C = C or {}
    t1 = C.get('TXT1','#e8eaf0'); t3 = C.get('TXT3','#3d4452')
    sub_html = f'<div style="font-family:Inter,sans-serif;font-size:0.78rem;color:{t3};margin-top:3px;">{subtitle}</div>' if subtitle else ''
    return f'''<div style="padding:0 0 16px;">
        <div style="font-family:DM Sans,sans-serif;font-size:1.4rem;font-weight:700;color:{t1};letter-spacing:-0.01em;">{title}</div>
        {sub_html}
    </div>'''

def stat_card(label, value, change=None, change_pct=None, C=None):
    C = C or {}
    UP=C.get('UP','#00c97a'); DOWN=C.get('DOWN','#e8384a')
    t1=C.get('TXT1','#e8eaf0'); t3=C.get('TXT3','#3d4452')
    bg=C.get('BG2','#111318'); bor=C.get('BOR','#1e2128')
    chg_html=""
    if change is not None:
        col = UP if change >= 0 else DOWN
        sign = "+" if change >= 0 else ""
        chg_html = f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{col};margin-top:2px;">{sign}{change:,.4f}'
        if change_pct is not None:
            chg_html += f' ({sign}{change_pct:.2f}%)'
        chg_html += '</div>'
    return f'''<div style="background:{bg};border:1px solid {bor};border-radius:6px;padding:14px 16px;">
        <div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{t3};margin-bottom:5px;">{label}</div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:1rem;font-weight:600;color:{t1};">{value}</div>
        {chg_html}
    </div>'''

def signal_badge(signal, C=None):
    C = C or {}
    UP=C.get('UP','#00c97a'); DOWN=C.get('DOWN','#e8384a')
    TXT2=C.get('TXT2','#8892a4'); BG2=C.get('BG2','#111318'); BOR=C.get('BOR','#1e2128')
    if "BUY" in signal:
        col,bg,border="#ffffff",f"rgba(0,201,122,0.15)","rgba(0,201,122,0.4)"
    elif "SELL" in signal:
        col,bg,border="#ffffff",f"rgba(232,56,74,0.15)","rgba(232,56,74,0.4)"
    else:
        col,bg,border=TXT2,BG2,BOR
    return f'<span style="background:{bg};color:{col};border:1px solid {border};font-family:IBM Plex Mono,monospace;font-size:0.65rem;font-weight:600;padding:3px 9px;border-radius:4px;letter-spacing:0.06em;">{signal}</span>'

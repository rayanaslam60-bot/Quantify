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
    background:{C['BG0']};color:{C['TXT2']};
    font-size:13px;-webkit-font-smoothing:antialiased;
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
    background:{C['BG1']};border-right:1px solid {C['BOR']};
    width:260px!important;min-height:100vh;
}}
section[data-testid="stSidebar"] .block-container{{padding:0;}}
section[data-testid="stSidebar"] > div{{padding:0!important;}}

/* Hide Streamlit chrome */
#MainMenu{{display:none;}}footer{{display:none;}}header{{display:none;}}
.stDeployButton{{display:none;}}[data-testid="stToolbar"]{{display:none;}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{{
    background:transparent;border-bottom:1px solid {C['BOR']};
    gap:0;padding:0 20px;
}}
.stTabs [data-baseweb="tab"]{{
    font-family:'IBM Plex Mono',monospace;font-size:0.68rem;font-weight:500;
    letter-spacing:0.06em;text-transform:uppercase;color:{C['TXT3']};
    padding:12px 16px;border-radius:0;background:transparent;
    border:none;border-bottom:2px solid transparent;transition:color 0.15s;
}}
.stTabs [data-baseweb="tab"]:hover{{color:{C['TXT2']};}}
.stTabs [aria-selected="true"]{{
    color:{C['TXT1']}!important;border-bottom:2px solid {C['BLUE']}!important;
}}

/* Metrics */
div[data-testid="stMetricValue"]{{
    font-family:'IBM Plex Mono',monospace;font-size:1.05rem;font-weight:600;color:{C['TXT1']};
}}
div[data-testid="stMetricLabel"]{{
    font-family:'IBM Plex Mono',monospace;font-size:0.6rem;font-weight:500;
    letter-spacing:0.1em;text-transform:uppercase;color:{C['TXT3']};
}}
div[data-testid="metric-container"]{{
    background:{C['BG2']};border:1px solid {C['BOR']};
    border-radius:6px;padding:14px 16px;transition:border-color 0.15s;
}}
div[data-testid="metric-container"]:hover{{border-color:{C['BOR2']};}}

/* Inputs */
.stSelectbox>div>div,.stMultiSelect>div>div{{
    background:{C['BG2']};border:1px solid {C['BOR']};border-radius:6px;
    font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:{C['TXT2']};
}}
.stTextInput>div>div>input{{
    background:{C['BG2']};border:1px solid {C['BOR']};border-radius:6px;
    font-family:'Inter',sans-serif;font-size:0.85rem;color:{C['TXT1']};padding:9px 12px;
    transition:border-color 0.15s;
}}
.stTextInput>div>div>input:focus{{border-color:{C['BLUE']};outline:none;}}
.stTextInput>div>div>input::placeholder{{color:{C['TXT3']};}}
.stNumberInput>div>div>input{{
    background:{C['BG2']};border:1px solid {C['BOR']};border-radius:6px;
    font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:{C['TXT1']};
}}
.stTextArea>div>div>textarea{{
    background:{C['BG2']};border:1px solid {C['BOR']};border-radius:6px;
    font-family:'Inter',sans-serif;font-size:0.85rem;color:{C['TXT1']};
}}

/* Checkboxes and radios */
.stCheckbox label p{{
    font-family:'IBM Plex Mono',monospace;font-size:0.68rem;font-weight:500;
    letter-spacing:0.05em;text-transform:uppercase;color:{C['TXT3']};
}}
.stRadio label{{font-family:'Inter',sans-serif;font-size:0.82rem;color:{C['TXT2']};}}

/* ── SLIDER — clean, no blue highlights on numbers ── */
.stSlider {{padding:0 2px;}}
/* Track */
.stSlider [data-baseweb="slider"] [role="slider"] ~ div:first-of-type {{
    background:{C['BOR2']}!important;
}}
/* Filled track */
.stSlider [data-baseweb="slider"] div[class*="Track"] > div {{
    background:{C['BLUE']}!important;
}}
/* Thumb */
.stSlider [data-baseweb="slider"] [role="slider"] {{
    background:{C['BG1']}!important;
    border:2px solid {C['BLUE']}!important;
    box-shadow:0 0 0 3px {C['BG0']}!important;
    width:16px!important;height:16px!important;
    transition:border-color 0.15s,box-shadow 0.15s;
}}
.stSlider [data-baseweb="slider"] [role="slider"]:hover {{
    border-color:{C['CYAN']}!important;
    box-shadow:0 0 0 4px rgba(6,182,212,0.15)!important;
}}
/* Value labels — plain text, NO blue highlight box */
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {{
    color:{C['TXT3']}!important;
    font-family:'IBM Plex Mono',monospace!important;
    font-size:0.65rem!important;
    background:transparent!important;
    padding:0!important;
    border:none!important;
}}
/* The floating value tooltip above thumb */
.stSlider [data-baseweb="tooltip"] {{
    background:{C['BG2']}!important;
    border:1px solid {C['BOR']}!important;
    color:{C['TXT2']}!important;
    font-family:'IBM Plex Mono',monospace!important;
    font-size:0.68rem!important;
    padding:3px 8px!important;
    border-radius:4px!important;
    box-shadow:none!important;
}}
/* Remove blue background from slider label/value display */
.stSlider > label {{
    color:{C['TXT3']}!important;
    font-family:'IBM Plex Mono',monospace!important;
    font-size:0.65rem!important;font-weight:500!important;
    letter-spacing:0.06em!important;text-transform:uppercase!important;
}}
div[data-testid="stSliderTickBarContainer"] span {{
    color:{C['TXT3']}!important;
    background:transparent!important;
    font-family:'IBM Plex Mono',monospace!important;
    font-size:0.64rem!important;
}}
/* Kill any blue-highlight spans inside slider */
.stSlider span[style*="background"],
.stSlider div[style*="background-color: rgb(49, 130, 206)"],
.stSlider div[style*="background-color: rgb(11, 97, 167)"] {{
    background:transparent!important;
    color:{C['TXT2']}!important;
}}

/* Buttons */
.stButton>button{{
    background:{C['BG2']};border:1px solid {C['BOR']};color:{C['TXT2']};
    font-family:'IBM Plex Mono',monospace;font-size:0.68rem;font-weight:500;
    letter-spacing:0.06em;padding:8px 16px;border-radius:6px;
    text-transform:uppercase;transition:all 0.15s ease;cursor:pointer;
}}
.stButton>button:hover{{
    background:{C['BG3']};border-color:{C['BOR2']};color:{C['TXT1']};
    transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,0.3);
}}
.stButton>button:active{{transform:translateY(0);}}

/* Expander */
.streamlit-expanderHeader{{
    font-family:'IBM Plex Mono',monospace;font-size:0.68rem;font-weight:500;
    letter-spacing:0.08em;text-transform:uppercase;color:{C['TXT3']};
    background:{C['BG1']};border:1px solid {C['BOR']};border-radius:6px;
    padding:10px 14px;transition:all 0.15s;
}}
.streamlit-expanderHeader:hover{{color:{C['TXT2']};border-color:{C['BOR2']};}}

/* DataFrames */
.stDataFrame{{border:1px solid {C['BOR']};border-radius:6px;overflow:hidden;}}
.stDataFrame th{{
    background:{C['BG2']};font-family:'IBM Plex Mono',monospace;
    font-size:0.65rem;font-weight:600;letter-spacing:0.08em;
    text-transform:uppercase;color:{C['TXT3']};
}}
.stDataFrame td{{
    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;
    color:{C['TXT2']};border-color:{C['BOR']};
}}

/* Chat */
.stChatInput>div{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;}}
.stChatInput textarea{{font-family:'Inter',sans-serif;font-size:0.85rem;color:{C['TXT1']};background:{C['BG2']};}}

/* Dividers */
hr{{border:none;border-top:1px solid {C['BOR']};margin:16px 0;}}

/* Plotly charts — pan cursor */
.js-plotly-plot .plotly .drag{{cursor:grab!important;}}
.js-plotly-plot .plotly .drag:active{{cursor:grabbing!important;}}
.js-plotly-plot .plotly{{user-select:none;}}
.modebar,.modebar-container{{display:none!important;}}

/* Progress */
.stProgress>div>div{{background:{C['BLUE']};}}
.stSpinner>div{{border-color:{C['BLUE']} transparent transparent transparent;}}

/* ── MOBILE ── */
@media (max-width:768px) {{
    /* Sidebar slides in from left */
    section[data-testid="stSidebar"] {{
        transform:translateX(-100%);
        transition:transform 0.25s ease;
        position:fixed!important;
        top:0!important;left:0!important;
        height:100vh!important;
        width:85vw!important;
        min-width:260px!important;
        max-width:320px!important;
        z-index:1000!important;
        box-shadow:4px 0 32px rgba(0,0,0,0.6)!important;
    }}
    section[data-testid="stSidebar"][aria-expanded="true"] {{
        transform:translateX(0)!important;
    }}
    /* Make main content full width */
    .main .block-container {{
        padding:0 10px!important;
    }}
    /* Stack metric columns */
    [data-testid="column"] {{
        min-width:45%!important;
    }}
    /* Scrollable tabs */
    .stTabs [data-baseweb="tab-list"] {{
        overflow-x:auto!important;
        flex-wrap:nowrap!important;
        padding:0 6px!important;
        -webkit-overflow-scrolling:touch!important;
    }}
    .stTabs [data-baseweb="tab"] {{
        white-space:nowrap!important;
        padding:10px 10px!important;
        font-size:0.6rem!important;
    }}
    /* Smaller header text */
    div[data-testid="stMetricValue"] {{
        font-size:0.85rem!important;
    }}
}}
hr{{border:none;border-top:1px solid {C['BOR']};margin:16px 0;}}

/* ── Mobile ── */
@media (max-width:768px) {{
    section[data-testid="stSidebar"] {{
        width:280px!important;min-width:280px!important;
        position:fixed!important;top:0!important;left:0!important;
        height:100vh!important;z-index:999!important;
        overflow-y:auto!important;box-shadow:4px 0 20px rgba(0,0,0,0.5)!important;
    }}
    [data-testid="collapsedControl"] {{
        display:flex!important;position:fixed!important;
        top:8px!important;left:8px!important;z-index:1000!important;
        background:{C['BG1']}!important;border:1px solid {C['BOR']}!important;
        border-radius:6px!important;padding:8px 10px!important;
        color:{C['TXT2']}!important;cursor:pointer!important;
    }}
    .main .block-container {{
        padding-left:6px!important;padding-right:6px!important;
        padding-top:8px!important;
    }}
    html,body,[class*="css"] {{font-size:12px!important;}}
    .stTabs [data-baseweb="tab"] {{
        font-size:0.58rem!important;padding:9px 8px!important;
    }}
    div[data-testid="metric-container"] {{padding:10px 12px!important;}}
    div[data-testid="stMetricValue"] {{font-size:0.9rem!important;}}
}}
</style>
""", unsafe_allow_html=True)

def lbl(t, size="0.62rem", C=None):
    color = C['TXT3'] if C else '#3d4452'
    return f'<div style="font-family:IBM Plex Mono,monospace;font-size:{size};font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{color};margin-bottom:8px;">{t}</div>'

def signal_badge(signal, C=None):
    C = C or {}
    UP=C.get('UP','#00c97a'); DOWN=C.get('DOWN','#e8384a')
    TXT2=C.get('TXT2','#8892a4'); BG2=C.get('BG2','#111318'); BOR=C.get('BOR','#1e2128')
    if "BUY" in signal:
        col,bg,border="#ffffff","rgba(0,201,122,0.15)","rgba(0,201,122,0.4)"
    elif "SELL" in signal:
        col,bg,border="#ffffff","rgba(232,56,74,0.15)","rgba(232,56,74,0.4)"
    else:
        col,bg,border=TXT2,BG2,BOR
    return f'<span style="background:{bg};color:{col};border:1px solid {border};font-family:IBM Plex Mono,monospace;font-size:0.65rem;font-weight:600;padding:3px 9px;border-radius:4px;letter-spacing:0.06em;">{signal}</span>'

def section_header(title, subtitle="", C=None):
    C = C or {}
    t1=C.get('TXT1','#e8eaf0'); t3=C.get('TXT3','#3d4452')
    sub = f'<div style="font-family:Inter,sans-serif;font-size:0.78rem;color:{t3};margin-top:3px;">{subtitle}</div>' if subtitle else ''
    return f'<div style="padding:0 0 16px;"><div style="font-family:DM Sans,sans-serif;font-size:1.4rem;font-weight:700;color:{t1};letter-spacing:-0.01em;">{title}</div>{sub}</div>'

def stat_card(label, value, change=None, change_pct=None, C=None):
    C = C or {}
    UP=C.get('UP','#00c97a'); DOWN=C.get('DOWN','#e8384a')
    t1=C.get('TXT1','#e8eaf0'); t3=C.get('TXT3','#3d4452')
    bg=C.get('BG2','#111318'); bor=C.get('BOR','#1e2128')
    chg=""
    if change is not None:
        col=UP if change>=0 else DOWN; sign="+" if change>=0 else ""
        chg=f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:{col};margin-top:2px;">{sign}{change:,.4f}'
        if change_pct is not None: chg+=f' ({sign}{change_pct:.2f}%)'
        chg+='</div>'
    return f'<div style="background:{bg};border:1px solid {bor};border-radius:6px;padding:14px 16px;"><div style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{t3};margin-bottom:5px;">{label}</div><div style="font-family:IBM Plex Mono,monospace;font-size:1rem;font-weight:600;color:{t1};">{value}</div>{chg}</div>'

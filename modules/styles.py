# modules/styles.py — Theme colors and CSS injection

import streamlit as st

def get_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    return st.session_state.theme

def get_colors():
    DARK = get_theme() == 'dark'
    return dict(
        DARK=DARK,
        BG0  = '#010408' if DARK else '#f0f4f8',
        BG1  = '#040d14' if DARK else '#ffffff',
        BG2  = '#071220' if DARK else '#f8fafc',
        BG3  = '#0a1929' if DARK else '#f1f5f9',
        BOR  = '#102035' if DARK else '#e2e8f0',
        BOR2 = '#1a3050' if DARK else '#cbd5e1',
        TXT1 = '#f0f8ff' if DARK else '#0f172a',
        TXT2 = '#7aaccc' if DARK else '#334155',
        TXT3 = '#2a5070' if DARK else '#94a3b8',
        TXT4 = '#1a3048' if DARK else '#cbd5e1',
        UP   = '#00e676',
        DOWN = '#ff3d57',
        BLUE = '#2979ff',
        AMBER= '#ffab00',
        PURP = '#c084fc',
        CYAN = '#22d3ee',
        ROSE = '#fb7185',
        GRID = '#071525' if DARK else '#f1f5f9',
    )

def inject_css(C):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
*{{box-sizing:border-box;}}
html,body,[class*="css"]{{font-family:'Plus Jakarta Sans',sans-serif;background:{C['BG0']};color:{C['TXT2']};}}
.stApp{{background:{C['BG0']};}}
.main .block-container{{padding:0;max-width:100%;}}
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:{C['BOR2']};border-radius:10px;}}
section[data-testid="stSidebar"]{{background:{C['BG1']};border-right:1px solid {C['BOR']};width:280px!important;min-height:100vh;}}
section[data-testid="stSidebar"] .block-container{{padding:0;}}
section[data-testid="stSidebar"] > div{{padding:0!important;}}
#MainMenu{{display:none;}}footer{{display:none;}}header{{display:none;}}
.stDeployButton{{display:none;}}
.stTabs [data-baseweb="tab-list"]{{background:transparent;border-bottom:1px solid {C['BOR']};gap:0;padding:0 1.5rem;}}
.stTabs [data-baseweb="tab"]{{font-family:'Space Mono',monospace;font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{C['TXT3']};padding:14px 18px;border-radius:0;background:transparent;border:none;border-bottom:2px solid transparent;}}
.stTabs [aria-selected="true"]{{color:{C['TXT1']}!important;border-bottom:2px solid {C['BLUE']}!important;}}
div[data-testid="stMetricValue"]{{font-family:'Space Mono';font-size:1.1rem;font-weight:700;color:{C['TXT1']};}}
div[data-testid="stMetricLabel"]{{font-family:'Space Mono';font-size:0.58rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{C['TXT3']};}}
div[data-testid="metric-container"]{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;padding:14px 16px;}}
.stSelectbox>div>div,.stMultiSelect>div>div{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;font-family:'Space Mono';font-size:0.78rem;color:{C['TXT2']};}}
.stTextInput>div>div>input{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;font-family:'Plus Jakarta Sans';font-size:0.9rem;color:{C['TXT1']};padding:10px 14px;}}
.stTextInput>div>div>input::placeholder{{color:{C['TXT4']};}}
.stNumberInput>div>div>input{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;font-family:'Space Mono';font-size:0.8rem;color:{C['TXT1']};}}
.stCheckbox label p{{font-family:'Space Mono';font-size:0.68rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:{C['TXT3']};}}
.stRadio label{{font-family:'Plus Jakarta Sans';font-size:0.85rem;font-weight:500;color:{C['TXT2']};}}
.stButton>button{{background:linear-gradient(135deg,{C['BLUE']}22,{C['BLUE']}11);border:1px solid {C['BLUE']}44;color:{C['TXT2']};font-family:'Space Mono';font-size:0.68rem;font-weight:700;letter-spacing:0.08em;padding:9px 18px;border-radius:8px;text-transform:uppercase;transition:all 0.2s;}}
.stButton>button:hover{{background:linear-gradient(135deg,{C['BLUE']}44,{C['BLUE']}22);border-color:{C['BLUE']};color:{C['TXT1']};transform:translateY(-1px);}}
hr{{border:none;border-top:1px solid {C['BOR']};margin:1rem 0;}}
.stDataFrame{{border:1px solid {C['BOR']};border-radius:8px;overflow:hidden;}}
.stChatInput>div{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:12px;}}
.stChatInput textarea{{font-family:'Plus Jakarta Sans';font-size:0.9rem;color:{C['TXT1']};background:{C['BG2']};}}
.stTextArea>div>div>textarea{{background:{C['BG2']};border:1px solid {C['BOR']};border-radius:8px;font-family:'Plus Jakarta Sans';font-size:0.85rem;color:{C['TXT1']};}}
</style>
""", unsafe_allow_html=True)

def lbl(t, size="0.65rem", C=None):
    color = C['TXT3'] if C else '#2a5070'
    return f'<div style="font-family:Space Mono;font-size:{size};font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{color};margin-bottom:8px;">{t}</div>'

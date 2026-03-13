"""
Fitness Tracker Dashboard - Entry point
"""
import streamlit as st
from datetime import datetime
from calendar import monthrange

from goals_setup import get_user_goals, has_goals, show_goals_setup
from data_loader import get_monthly_data
import views.mes_actual as view_mes
import views.historico as view_historico

st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide"
)

# ============ DARK NEON THEME (matching mockup) ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=Space+Mono:wght@400;700&display=swap');

    /* Main background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0a0a0f !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0f0f18 !important;
    }

    /* Hide default Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}

    /* ---- Typography ---- */
    .dn-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 6px;
        background: linear-gradient(135deg, #06b6d4, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 0 0 4px 0;
    }
    .dn-subtitle {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #64748b;
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 20px;
    }
    .dn-section {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #06b6d4;
        letter-spacing: 3px;
        margin: 28px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #06b6d420;
    }

    /* ---- Summary Cards ---- */
    .dn-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #06b6d420;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .dn-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #06b6d4, #8b5cf6);
    }
    .dn-card .value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: #f1f5f9;
        margin: 8px 0 2px 0;
    }
    .dn-card .label {
        font-family: 'Space Mono', monospace;
        font-size: 0.55rem;
        color: #64748b;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    /* ---- Metric Rows ---- */
    .dn-metric {
        background: #1a1a2e;
        border: 1px solid #ffffff08;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .dn-metric .name {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    .dn-metric .val {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #f1f5f9;
    }
    .dn-bar-bg {
        width: 120px;
        height: 6px;
        background: #1e293b;
        border-radius: 3px;
        overflow: hidden;
        display: inline-block;
        margin: 0 10px;
    }
    .dn-bar-fill {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #06b6d4, #8b5cf6);
    }
    .dn-pct {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #06b6d4;
        min-width: 40px;
        text-align: right;
    }
    .dn-status {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .dn-status.green { background: #10b981; box-shadow: 0 0 8px #10b98180; }
    .dn-status.yellow { background: #f59e0b; box-shadow: 0 0 8px #f59e0b80; }
    .dn-status.red { background: #ef4444; box-shadow: 0 0 8px #ef444480; }

    /* ---- Navigation ---- */
    .stButton > button {
        background-color: #1a1a2e !important;
        color: #94a3b8 !important;
        border: 1px solid #06b6d430 !important;
        border-radius: 12px !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 0.65rem !important;
        font-weight: 600 !important;
        letter-spacing: 2px !important;
        transition: all 0.2s ease !important;
        padding: 10px 20px !important;
    }
    .stButton > button:hover {
        background-color: #06b6d410 !important;
        color: #06b6d4 !important;
        border-color: #06b6d4 !important;
    }

    /* ---- Dividers ---- */
    hr {
        border-color: rgba(6, 182, 212, 0.15) !important;
    }

    /* ---- Tables (custom HTML) ---- */
    .dn-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: #1a1a2e;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #ffffff08;
        margin: 8px 0;
    }
    .dn-table th {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #64748b;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid #ffffff10;
        background: #151525;
    }
    .dn-table td {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #e2e8f0;
        padding: 10px 16px;
        border-bottom: 1px solid #ffffff06;
    }
    .dn-table tr:last-child td {
        border-bottom: none;
    }
    .dn-table td.val {
        font-weight: 700;
        color: #f1f5f9;
    }

    /* ---- Dataframes (fallback styling) ---- */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* ---- Expanders ---- */
    [data-testid="stExpander"] {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(6, 182, 212, 0.15) !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary * {
        color: #06b6d4 !important;
    }

    /* ---- Alerts ---- */
    [data-testid="stAlert"] {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(6, 182, 212, 0.3) !important;
        border-radius: 8px !important;
    }

    /* ---- Caption ---- */
    .stApp [data-testid="stCaptionContainer"] * {
        color: #64748b !important;
    }

    /* ---- Spinner ---- */
    .stSpinner > div {
        border-top-color: #06b6d4 !important;
    }

    /* ---- Footer text ---- */
    .dn-footer {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #475569;
        text-align: center;
        margin-top: 24px;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ============ GLOBAL STATE ============
today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day
progress_pct = (days_elapsed / days_in_month * 100)

# ============ GOALS GATE ============
if not has_goals():
    show_goals_setup(first_time=True)
    st.stop()

metas = get_user_goals()

if 'vista' not in st.session_state:
    st.session_state.vista = "mes"

# ============ NAVIGATION ============
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)

with col_nav1:
    if st.button("MES ACTUAL", use_container_width=True):
        st.session_state.vista = "mes"
        st.rerun()

with col_nav2:
    if st.button("HISTORICO", use_container_width=True):
        st.session_state.vista = "historico"
        st.rerun()

with col_nav3:
    if st.button("METAS", use_container_width=True):
        st.session_state.vista = "metas"
        st.rerun()

with col_nav4:
    if st.button("ACTUALIZAR", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ============ ROUTING ============
if st.session_state.vista == "metas":
    show_goals_setup(first_time=False)

elif st.session_state.vista == "mes":
    with st.spinner(''):
        data = get_monthly_data(current_year, current_month)
    view_mes.show(data, metas, days_elapsed, days_in_month, progress_pct, current_month, current_year)

elif st.session_state.vista == "historico":
    view_historico.show(metas, current_month, current_year)

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

# ============ DARK NEON THEME ============
st.markdown("""
<style>
    /* Main background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0a0a0f !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0f0f18 !important;
    }

    /* Text colors */
    .stApp h1 {
        color: #06b6d4 !important;
        font-weight: 800 !important;
        letter-spacing: 2px;
    }
    .stApp h2, .stApp h3 {
        color: #06b6d4 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        letter-spacing: 1px;
    }
    .stApp p, .stApp span, .stApp label, .stApp div {
        color: #e2e8f0 !important;
    }
    .stApp [data-testid="stCaptionContainer"] * {
        color: #64748b !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(6, 182, 212, 0.25) !important;
        border-top: 3px solid #06b6d4 !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] * {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] * {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
    }
    [data-testid="stMetricDelta"] * {
        font-size: 0.8rem !important;
    }

    /* Progress bars */
    [data-testid="stProgress"] > div > div {
        background-color: #1e293b !important;
        border-radius: 8px !important;
    }
    [data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #06b6d4, #22d3ee) !important;
        border-radius: 8px !important;
    }

    /* Buttons - navigation */
    .stButton > button {
        background-color: #1a1a2e !important;
        color: #06b6d4 !important;
        border: 1px solid #06b6d4 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #06b6d4 !important;
        color: #0a0a0f !important;
    }

    /* Dividers */
    [data-testid="stHorizontalBlock"] hr, hr {
        border-color: rgba(6, 182, 212, 0.15) !important;
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] * {
        background-color: #1a1a2e !important;
        color: #e2e8f0 !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(6, 182, 212, 0.15) !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary * {
        color: #06b6d4 !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #06b6d4 !important;
    }

    /* Info boxes */
    [data-testid="stAlert"] {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(6, 182, 212, 0.3) !important;
        border-radius: 8px !important;
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

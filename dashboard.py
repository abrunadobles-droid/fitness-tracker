"""
Fitness Tracker Dashboard - Entry point
"""
import streamlit as st
from datetime import datetime
from calendar import monthrange

from auth import show_auth_page, show_logout_button
from goals_setup import get_user_goals, has_goals, show_goals_setup
from data_loader import get_monthly_data
import views.mes_actual as view_mes
import views.historico as view_historico

st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide"
)

# ============ AUTH GATE ============
if not show_auth_page():
    st.stop()

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
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 1, 1, 1])

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

with col_nav5:
    show_logout_button()

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

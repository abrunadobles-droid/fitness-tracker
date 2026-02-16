"""
Fitness & Wellness Dashboard - Clean & Minimal
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from calendar import monthrange

st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para diseño limpio
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #10b981;
    }
    h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        margin-bottom: 2rem !important;
    }
    h2 {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day

st.title("🏃‍♂️ Fitness Tracker")
st.caption(f"{today.strftime('%B %Y')} • Día {days_elapsed}/{days_in_month}")

@st.cache_data(ttl=3600, show_spinner=False)
def get_monthly_data(year, month):
    data = {
        'steps_avg': 0, 'activities': 0, 'strength': 0,
        'days_before_930': 0, 'sleep_hours_avg': 0,
        'hr_zone_1_3': 0, 'hr_zone_4_5': 0
    }
    
    try:
        import config
        from garmin_client import GarminClient
        from whoop_client_v2 import WhoopClientV2
        
        garmin = GarminClient()
        garmin.login()
        
        start_date = datetime(year, month, 1)
        end_date = today if (year == current_year and month == current_month) else datetime(year, month, monthrange(year, month)[1])
        
        total_steps = 0
        days_with_steps = 0
        activities = []
        strength_count = 0
        
        current_date = start_date
        while current_date <= end_date:
            try:
                stats = garmin.get_stats_for_date(current_date)
                if stats and stats.get('totalSteps'):
                    total_steps += stats['totalSteps']
                    days_with_steps += 1
            except:
                pass
            current_date += timedelta(days=1)
        
        all_activities = garmin.get_activities(start_date, end_date, limit=100)
        for activity in all_activities:
            activity_date_str = activity.get('startTimeLocal', '')
            if activity_date_str:
                activity_date = datetime.strptime(activity_date_str[:10], '%Y-%m-%d')
                if activity_date.year == year and activity_date.month == month:
                    activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
                    if 'breath' not in activity_type and 'meditation' not in activity_type:
                        activities.append(activity)
                        if any(kw in activity_type for kw in ['strength', 'training', 'gym', 'weight']):
                            strength_count += 1
        
        data['steps_avg'] = round(total_steps / days_with_steps) if days_with_steps > 0 else 0
        data['activities'] = len(activities)
        data['strength'] = strength_count
        
        whoop = WhoopClientV2()
        summary = whoop.get_monthly_summary(year, month)
        
        data['days_before_930'] = summary['days_sleep_before_930pm']
        data['sleep_hours_avg'] = round(summary['avg_sleep_hours'], 1)
        
        total_zone_1_3 = 0
        total_zone_4_5 = 0
        for workout in summary['workouts']:
            if workout.get('score') and workout['score'].get('zone_durations'):
                zones = workout['score']['zone_durations']
                total_zone_1_3 += (zones.get('zone_one_milli', 0) + zones.get('zone_two_milli', 0) + zones.get('zone_three_milli', 0))
                total_zone_4_5 += (zones.get('zone_four_milli', 0) + zones.get('zone_five_milli', 0))
        
        data['hr_zone_1_3'] = round(total_zone_1_3 / 3600000, 1)
        data['hr_zone_4_5'] = round(total_zone_4_5 / 3600000, 1)
        
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
    
    return data

with st.spinner('Cargando...'):
    data = get_monthly_data(current_year, current_month)

metas = {
    'steps_avg': 10000, 'activities': 28, 'strength': 10,
    'days_before_930': 15, 'sleep_hours_avg': 7.5,
    'hr_zone_1_3': 19.3, 'hr_zone_4_5': 2.9
}

def calcular_progreso(valor, meta, tipo='total'):
    if tipo == 'promedio':
        pct = (valor / meta * 100) if meta > 0 else 0
    else:
        esperado = (meta / days_in_month) * days_elapsed
        pct = (valor / esperado * 100) if esperado > 0 else 0
    return min(pct, 100)

def mostrar_metrica(titulo, valor, meta, unidad="", tipo='total'):
    pct = calcular_progreso(valor, meta, tipo)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{titulo}**")
        st.progress(pct / 100)
    with col2:
        if unidad:
            st.metric("", f"{valor}{unidad}")
        else:
            st.metric("", f"{valor:,}" if valor >= 1000 else valor)
    st.caption(f"Meta: {meta:,}{unidad} • {pct:.0f}%")
    st.markdown("---")

st.markdown("## 🎯 Hábitos")

col1, col2 = st.columns(2)

with col1:
    mostrar_metrica("Steps (Promedio Diario)", data['steps_avg'], metas['steps_avg'], tipo='promedio')
    mostrar_metrica("Strength Training", data['strength'], metas['strength'])
    mostrar_metrica("Sleep Duration", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", tipo='promedio')
    mostrar_metrica("HR Zones 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")

with col2:
    mostrar_metrica("Activities del Mes", data['activities'], metas['activities'])
    mostrar_metrica("Días dormido antes 9:30 PM", data['days_before_930'], metas['days_before_930'])
    mostrar_metrica("HR Zones 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")

st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

"""
Fitness & Wellness Dashboard - Dark Mode + Historical
"""

import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange
import pandas as pd

st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide"
)

# Dark theme CSS
st.markdown("""
<style>
    /* Dark background */
    .stApp {
        background-color: #0f1419;
        color: #e1e8ed;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #e1e8ed !important;
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
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #10b981 0%, #34d399 100%) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #10b981 !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }
    
    /* Caption text */
    .stCaption {
        color: #8899a6 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #15202b;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #8899a6;
    }
    
    /* Radio buttons */
    [data-testid="stRadio"] label {
        color: #e1e8ed !important;
    }
    
    /* Dividers */
    hr {
        border-color: #38444d !important;
    }
    
    /* Tables */
    [data-testid="stDataFrame"] {
        background-color: #15202b !important;
    }
    
    /* Success/Error boxes */
    .stSuccess {
        background-color: #0d3b2e !important;
        color: #10b981 !important;
    }
    
    .stError {
        background-color: #3d1818 !important;
        color: #ef4444 !important;
    }
</style>
""", unsafe_allow_html=True)

today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    vista = st.radio(
        "Vista:",
        ["📈 Mes Actual", "📊 Histórico"],
        index=0
    )
    
    if vista == "📈 Mes Actual":
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    st.markdown(f"📅 **Fecha:** {today.strftime('%d/%m/%Y')}")
    st.markdown(f"📆 **Mes:** {today.strftime('%B %Y')}")
    st.markdown(f"⏱️ **Días:** {days_elapsed}/{days_in_month}")
    st.markdown(f"📊 **Progreso:** {(days_elapsed/days_in_month*100):.0f}%")

@st.cache_data(ttl=3600, show_spinner=False)
def get_monthly_data(year, month):
    data = {
        'month': month,
        'year': year,
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
        
        # Si es mes actual: hasta hoy, si es cerrado: hasta último día
        if year == current_year and month == current_month:
            end_date = today
        else:
            last_day = monthrange(year, month)[1]
            end_date = datetime(year, month, last_day)
        
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

if vista == "📈 Mes Actual":
    # VISTA: MES ACTUAL
    st.title("🏃‍♂️ Fitness Tracker")
    st.caption(f"{today.strftime('%B %Y')} • Día {days_elapsed}/{days_in_month}")
    
    with st.spinner('Cargando...'):
        data = get_monthly_data(current_year, current_month)
    
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

else:
    # VISTA: HISTÓRICO
    st.title("📊 Histórico Mensual 2026")
    
    with st.spinner('Cargando datos históricos...'):
        meses_data = []
        
        # Obtener todos los meses hasta el actual
        for mes in range(1, current_month):
            meses_data.append(get_monthly_data(2026, mes))
        
        if not meses_data:
            st.info("ℹ️ Aún no hay meses cerrados. El histórico se mostrará cuando finalice febrero.")
        else:
            df = pd.DataFrame(meses_data)
            
            meses_nombres = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            df['Mes'] = df['month'].map(meses_nombres)
            
            df_display = df[[
                'Mes', 'steps_avg', 'activities', 'strength',
                'days_before_930', 'sleep_hours_avg',
                'hr_zone_1_3', 'hr_zone_4_5'
            ]]
            
            df_display.columns = [
                'Mes', 'Steps (Ave)', 'Activities', 'Strength',
                'Días <9:30PM', 'Sleep (H)', 'HR Z1-3 (H)', 'HR Z4-5 (H)'
            ]
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            st.subheader("📈 Comparación con Metas")
            
            for idx, row in df_display.iterrows():
                mes = row['Mes']
                st.markdown(f"### {mes}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if row['Steps (Ave)'] >= metas['steps_avg']:
                        st.success(f"✅ Steps: {row['Steps (Ave)']:,}")
                    else:
                        st.error(f"❌ Steps: {row['Steps (Ave)']:,}")
                
                with col2:
                    if row['Activities'] >= metas['activities']:
                        st.success(f"✅ Activities: {row['Activities']}")
                    else:
                        st.error(f"❌ Activities: {row['Activities']}")
                
                with col3:
                    if row['Strength'] >= metas['strength']:
                        st.success(f"✅ Strength: {row['Strength']}")
                    else:
                        st.error(f"❌ Strength: {row['Strength']}")
                
                with col4:
                    if row['Sleep (H)'] >= metas['sleep_hours_avg']:
                        st.success(f"✅ Sleep: {row['Sleep (H)']}h")
                    else:
                        st.error(f"❌ Sleep: {row['Sleep (H)']}h")
                
                st.markdown("---")

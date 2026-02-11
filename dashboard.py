"""
Fitness & Wellness Dashboard - Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from calendar import monthrange

st.set_page_config(
    page_title="Fitness Dashboard",
    page_icon="🏃‍♂️",
    layout="wide"
)

st.title("🏃‍♂️ FITNESS & WELLNESS DASHBOARD")
st.markdown("---")

today = datetime.now()
current_month = today.month
current_year = today.year

# Sidebar
st.sidebar.header("📊 Vista")
vista = st.sidebar.radio(
    "Selecciona:",
    ["📈 Mes en Curso", "📊 Histórico Mensual"],
    index=0
)

st.sidebar.markdown("---")

if vista == "📈 Mes en Curso":
    days_in_month = monthrange(current_year, current_month)[1]
    days_elapsed = today.day
    
    st.sidebar.markdown(f"📅 **Fecha:** {today.strftime('%d/%m/%Y')}")
    st.sidebar.markdown(f"📆 **Mes:** {today.strftime('%B %Y')}")
    st.sidebar.markdown(f"⏱️ **Días transcurridos:** {days_elapsed}/{days_in_month}")

# Función para obtener datos
@st.cache_data(ttl=3600, show_spinner=False)
def get_monthly_data(year, month):
    data = {
        'steps_avg': 0,
        'activities': 0,
        'strength': 0,
        'days_before_930': 0,
        'sleep_hours_avg': 0,
        'hr_zone_1_3': 0,
        'hr_zone_4_5': 0,
        'sleep_performance': 0,
        'sleep_consistency': 0,
        'recovery_score': 0,
        'hrv': 0
    }
    
    try:
        # Importar dentro de try/except
        import config
        from garmin_client import GarminClient
        from whoop_client_v2 import WhoopClientV2
        
        # Garmin
        try:
            garmin = GarminClient()
            garmin.login()
            
            start_date = datetime(year, month, 1)
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
            
        except Exception as e:
            st.error(f"⚠️ Error conectando con Garmin: {str(e)}")
        
        # WHOOP
        try:
            whoop = WhoopClientV2()
            summary = whoop.get_monthly_summary(year, month)
            
            data['days_before_930'] = summary['days_sleep_before_930pm']
            data['sleep_hours_avg'] = round(summary['avg_sleep_hours'], 1)
            data['sleep_performance'] = round(summary['avg_sleep_performance'], 1)
            data['sleep_consistency'] = round(summary['avg_sleep_consistency'], 1)
            data['recovery_score'] = round(summary['avg_recovery_score'], 1)
            data['hrv'] = round(summary['avg_hrv'], 1)
            
            total_zone_1_3 = 0
            total_zone_4_5 = 0
            for workout in summary['workouts']:
                if workout.get('score') and workout['score'].get('zone_durations'):
                    zones = workout['score']['zone_durations']
                    total_zone_1_3 += (
                        zones.get('zone_one_milli', 0) +
                        zones.get('zone_two_milli', 0) +
                        zones.get('zone_three_milli', 0)
                    )
                    total_zone_4_5 += (
                        zones.get('zone_four_milli', 0) +
                        zones.get('zone_five_milli', 0)
                    )
            
            data['hr_zone_1_3'] = round(total_zone_1_3 / 3600000, 1)
            data['hr_zone_4_5'] = round(total_zone_4_5 / 3600000, 1)
            
        except Exception as e:
            st.error(f"⚠️ Error conectando con WHOOP: {str(e)}")
    
    except Exception as e:
        st.error(f"⚠️ Error general: {str(e)}")
        st.info("💡 Verifica que los Secrets estén configurados correctamente en Settings → Secrets")
    
    return data

metas = {
    'steps_avg': 10000,
    'activities': 28,
    'strength': 10,
    'days_before_930': 15,
    'sleep_hours_avg': 7.5,
    'hr_zone_1_3': 19.3,
    'hr_zone_4_5': 2.9
}

if vista == "📈 Mes en Curso":
    with st.spinner('Cargando datos...'):
        data = get_monthly_data(current_year, current_month)
    
    days_in_month = monthrange(current_year, current_month)[1]
    days_elapsed = today.day
    
    def calcular_progreso(valor_actual, meta_mensual, metrica_tipo='total'):
        if metrica_tipo == 'promedio':
            esperado = meta_mensual
            real = valor_actual
            progreso_pct = (real / esperado * 100) if esperado > 0 else 0
        else:
            esperado = (meta_mensual / days_in_month) * days_elapsed
            real = valor_actual
            progreso_pct = (real / esperado * 100) if esperado > 0 else 0
        
        return esperado, real, progreso_pct
    
    st.header("🎯 HÁBITOS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Steps (Ave Daily)")
        esperado, real, pct = calcular_progreso(data['steps_avg'], metas['steps_avg'], 'promedio')
        st.metric("Actual", f"{real:,}", f"{pct:.0f}% de meta")
        if pct >= 100:
            st.success("✅ On track!")
        else:
            st.error(f"⚠️ Necesitas {int(esperado - real):,} más")
    
    with col2:
        st.subheader("Activities Mes")
        esperado, real, pct = calcular_progreso(data['activities'], metas['activities'], 'total')
        st.metric("Actual", real, f"{pct:.0f}% de meta")
        if pct >= 100:
            st.success("✅ On track!")
        else:
            st.error(f"⚠️ Necesitas {int(esperado - real)} más")
    
    with col3:
        st.subheader("Strength Training")
        esperado, real, pct = calcular_progreso(data['strength'], metas['strength'], 'total')
        st.metric("Actual", real, f"{pct:.0f}% de meta")
        if pct >= 100:
            st.success("✅ On track!")
        else:
            st.error(f"⚠️ Necesitas {int(esperado - real)} más")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Ave Sleep (H)")
        st.metric("Promedio", f"{data['sleep_hours_avg']}h", f"Meta: {metas['sleep_hours_avg']}h")
    
    with col2:
        st.subheader("Días <9:30 PM")
        st.metric("Este mes", data['days_before_930'], f"Meta: {metas['days_before_930']}")
    
    with col3:
        st.subheader("HR Zones 1-3")
        st.metric("Total (H)", f"{data['hr_zone_1_3']}h", f"Meta: {metas['hr_zone_1_3']}h")
    
    st.markdown("---")
    st.header("📊 RESULTADOS")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sleep Performance", f"{data['sleep_performance']}%")
    
    with col2:
        st.metric("Sleep Consistency", f"{data['sleep_consistency']}%")
    
    with col3:
        st.metric("Recovery Score", f"{data['recovery_score']}")
    
    with col4:
        st.metric("HRV", f"{data['hrv']} ms")

else:
    st.header("📊 HISTÓRICO MENSUAL 2026")
    st.info("ℹ️ El histórico se mostrará cuando finalice el mes actual.")

st.markdown("---")
st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

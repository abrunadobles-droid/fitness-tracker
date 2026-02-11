"""
Fitness & Wellness Dashboard
Dashboard interactivo con histórico mensual
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from calendar import monthrange
from garmin_client import GarminClient
from whoop_client_v2 import WhoopClientV2

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

# SIDEBAR - Selector de vista
st.sidebar.header("📊 Vista")
vista = st.sidebar.radio(
    "Selecciona:",
    ["📈 Mes en Curso", "📊 Histórico Mensual"],
    index=0
)

st.sidebar.markdown("---")

if vista == "📈 Mes en Curso":
    st.sidebar.header("⚙️ Configuración")
    if st.sidebar.button("🔄 Actualizar Datos", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    days_in_month = monthrange(current_year, current_month)[1]
    days_elapsed = today.day
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"📅 **Fecha:** {today.strftime('%d/%m/%Y')}")
    st.sidebar.markdown(f"📆 **Mes:** {today.strftime('%B %Y')}")
    st.sidebar.markdown(f"⏱️ **Días transcurridos:** {days_elapsed}/{days_in_month}")
    st.sidebar.markdown(f"📊 **Progreso mes:** {(days_elapsed/days_in_month*100):.0f}%")

# Función para obtener datos de un mes completo
@st.cache_data(ttl=3600)
def get_monthly_data(year, month):
    """Obtiene datos de un mes específico (puede ser mes actual o cerrado)"""
    
    data = {
        'month': month,
        'year': year,
        'steps_avg': 0,
        'activities': 0,
        'strength': 0,
        'days_before_930': 0,
        'sleep_hours_avg': 0,
        'sleep_performance': 0,
        'sleep_consistency': 0,
        'recovery_score': 0,
        'hrv': 0,
        'hr_zone_1_3': 0,
        'hr_zone_4_5': 0
    }
    
    try:
        garmin = GarminClient()
        garmin.login()
        
        start_date = datetime(year, month, 1)
        
        # Si es el mes actual, hasta hoy; si es mes cerrado, hasta el último día
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
        st.error(f"Error Garmin mes {month}: {e}")
    
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
        st.error(f"Error WHOOP mes {month}: {e}")
    
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
    # ========== VISTA: MES EN CURSO ==========
    
    with st.spinner('Cargando datos del mes actual...'):
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
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = real,
            delta = {'reference': esperado, 'relative': False},
            gauge = {
                'axis': {'range': [None, metas['steps_avg'] * 1.2]},
                'bar': {'color': "darkgreen" if pct >= 100 else "red"},
                'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': esperado}
            },
            title = {'text': f"Meta: {metas['steps_avg']:,}"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        if pct >= 100:
            st.success(f"✅ {pct:.0f}% - ¡On track!")
        else:
            st.error(f"⚠️ {pct:.0f}% - Necesitas {int(esperado - real):,} más")
    
    with col2:
        st.subheader("Activities Mes")
        esperado, real, pct = calcular_progreso(data['activities'], metas['activities'], 'total')
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = real,
            delta = {'reference': esperado, 'relative': False},
            gauge = {
                'axis': {'range': [None, metas['activities'] * 1.2]},
                'bar': {'color': "darkgreen" if pct >= 100 else "red"},
                'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': esperado}
            },
            title = {'text': f"Meta: {metas['activities']}"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        if pct >= 100:
            st.success(f"✅ {pct:.0f}% - ¡On track!")
        else:
            st.error(f"⚠️ {pct:.0f}% - Necesitas {int(esperado - real)} más")
    
    with col3:
        st.subheader("Strength Training")
        esperado, real, pct = calcular_progreso(data['strength'], metas['strength'], 'total')
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = real,
            delta = {'reference': esperado, 'relative': False},
            gauge = {
                'axis': {'range': [None, metas['strength'] * 1.2]},
                'bar': {'color': "darkgreen" if pct >= 100 else "red"},
                'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': esperado}
            },
            title = {'text': f"Meta: {metas['strength']}"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        if pct >= 100:
            st.success(f"✅ {pct:.0f}% - ¡On track!")
        else:
            st.error(f"⚠️ {pct:.0f}% - Necesitas {int(esperado - real)} más")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Ave Sleep Duration (H)")
        esperado, real, pct = calcular_progreso(data['sleep_hours_avg'], metas['sleep_hours_avg'], 'promedio')
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = real,
            delta = {'reference': esperado, 'relative': False},
            gauge = {
                'axis': {'range': [None, 9]},
                'bar': {'color': "darkgreen" if pct >= 100 else "red"},
                'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': esperado}
            },
            title = {'text': f"Meta: {metas['sleep_hours_avg']}h"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        if pct >= 100:
            st.success(f"✅ {pct:.0f}% - ¡On track!")
        else:
            st.error(f"⚠️ {pct:.0f}% - Necesitas {(esperado - real):.1f}h más")
    
    with col2:
        st.subheader("Días antes 9:30 PM")
        esperado, real, pct = calcular_progreso(data['days_before_930'], metas['days_before_930'], 'total')
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = real,
            delta = {'reference': esperado, 'relative': False},
            gauge = {
                'axis': {'range': [None, metas['days_before_930'] * 1.2]},
                'bar': {'color': "darkgreen" if pct >= 100 else "red"},
                'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': esperado}
            },
            title = {'text': f"Meta: {metas['days_before_930']}"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        if pct >= 100:
            st.success(f"✅ {pct:.0f}% - ¡On track!")
        else:
            st.error(f"⚠️ {pct:.0f}% - Necesitas {int(esperado - real)} más")
    
    with col3:
        st.subheader("HR Zones 1-3 (H total)")
        esperado, real, pct = calcular_progreso(data['hr_zone_1_3'], metas['hr_zone_1_3'], 'total')
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = real,
            delta = {'reference': esperado, 'relative': False},
            gauge = {
                'axis': {'range': [None, metas['hr_zone_1_3'] * 1.2]},
                'bar': {'color': "darkgreen" if pct >= 100 else "red"},
                'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': esperado}
            },
            title = {'text': f"Meta: {metas['hr_zone_1_3']}h"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        if pct >= 100:
            st.success(f"✅ {pct:.0f}% - ¡On track!")
        else:
            st.error(f"⚠️ {pct:.0f}% - Necesitas {(esperado - real):.1f}h más")
    
    st.markdown("---")
    
    st.header("📊 RESULTADOS")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sleep Performance", f"{data['sleep_performance']}%", 
                  delta=f"{data['sleep_performance'] - 85:.0f}% vs meta")
    
    with col2:
        st.metric("Sleep Consistency", f"{data['sleep_consistency']}%",
                  delta=f"{data['sleep_consistency'] - 85:.0f}% vs meta")
    
    with col3:
        st.metric("Recovery Score", f"{data['recovery_score']:.0f}",
                  delta=f"{data['recovery_score'] - 70:.0f} vs meta")
    
    with col4:
        st.metric("HRV", f"{data['hrv']:.0f} ms")

else:
    # ========== VISTA: HISTÓRICO MENSUAL ==========
    
    st.header("📊 HISTÓRICO MENSUAL 2026")
    
    with st.spinner('Cargando datos históricos...'):
        # Obtener datos de enero (único mes cerrado por ahora)
        meses_data = []
        
        # Solo enero está completo
        if current_month > 1:
            enero_data = get_monthly_data(2026, 1)
            meses_data.append(enero_data)
        
        if not meses_data:
            st.info("ℹ️ Aún no hay meses cerrados. El histórico se mostrará cuando finalice el mes actual.")
        else:
            # Crear DataFrame
            df = pd.DataFrame(meses_data)
            
            # Mapear números de mes a nombres
            meses_nombres = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            df['Mes'] = df['month'].map(meses_nombres)
            
            # Reorganizar columnas
            df_display = df[[
                'Mes',
                'steps_avg',
                'activities',
                'strength',
                'days_before_930',
                'sleep_hours_avg',
                'hr_zone_1_3',
                'hr_zone_4_5',
                'sleep_performance',
                'sleep_consistency',
                'recovery_score',
                'hrv'
            ]]
            
            # Renombrar columnas
            df_display.columns = [
                'Mes',
                'Steps (Ave)',
                'Activities',
                'Strength',
                'Días <9:30PM',
                'Sleep (H)',
                'HR Z1-3 (H)',
                'HR Z4-5 (H)',
                'Sleep Perf %',
                'Sleep Cons %',
                'Recovery',
                'HRV'
            ]
            
            # Mostrar tabla
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Comparación con metas
            st.markdown("---")
            st.subheader("📈 Comparación con Metas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 HÁBITOS**")
                for idx, row in df_display.iterrows():
                    mes = row['Mes']
                    st.markdown(f"**{mes}:**")
                    
                    if row['Steps (Ave)'] >= metas['steps_avg']:
                        st.success(f"✅ Steps: {row['Steps (Ave)']:,}")
                    else:
                        st.error(f"❌ Steps: {row['Steps (Ave)']:,}")
                    
                    if row['Activities'] >= metas['activities']:
                        st.success(f"✅ Activities: {row['Activities']}")
                    else:
                        st.error(f"❌ Activities: {row['Activities']}")
                    
                    if row['Strength'] >= metas['strength']:
                        st.success(f"✅ Strength: {row['Strength']}")
                    else:
                        st.error(f"❌ Strength: {row['Strength']}")
            
            with col2:
                st.markdown("**📊 RESULTADOS**")
                for idx, row in df_display.iterrows():
                    mes = row['Mes']
                    st.markdown(f"**{mes}:**")
                    st.info(f"Sleep Perf: {row['Sleep Perf %']}%")
                    st.info(f"Sleep Cons: {row['Sleep Cons %']}%")
                    st.info(f"Recovery: {row['Recovery']}")
                    st.info(f"HRV: {row['HRV']} ms")

st.markdown("---")
st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


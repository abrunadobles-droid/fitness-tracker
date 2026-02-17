"""
Fitness Tracker - Sport HUD Design
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

* { font-family: 'DM Sans', sans-serif; }

.stApp {
    background-color: #050505 !important;
    color: #e1e8ed !important;
}

[data-testid="stSidebar"] {
    background-color: #0a0a0a !important;
    border-right: 1px solid #1a1a1a !important;
}

[data-testid="stSidebar"] * { color: #888 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #fff !important; }

.top-bar {
    height: 3px;
    background: linear-gradient(90deg, #00ff87, #00d4ff, #ff0080);
    margin-bottom: 32px;
    border-radius: 0 0 2px 2px;
}

.hud-title {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 3rem !important;
    letter-spacing: 4px !important;
    color: #fff !important;
    line-height: 1 !important;
    margin: 0 !important;
}

.date-badge {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #00ff87;
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 6px;
    padding: 6px 14px;
    display: inline-block;
    letter-spacing: 2px;
    margin-bottom: 32px;
}

.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 4px;
    margin-bottom: 20px;
    margin-top: 8px;
}

.metric-wrap {
    margin-bottom: 20px;
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.metric-name {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
}

.val-green { color: #00ff87; }
.val-yellow { color: #ffd700; }
.val-red { color: #ff4444; }

.metric-bar-bg {
    height: 3px;
    background: #111;
    border-radius: 2px;
    overflow: hidden;
}

.metric-bar-fill-green {
    height: 3px;
    background: linear-gradient(90deg, #00ff87, #00d4ff);
    border-radius: 2px;
}

.metric-bar-fill-yellow {
    height: 3px;
    background: linear-gradient(90deg, #ffd700, #ff8c00);
    border-radius: 2px;
}

.metric-bar-fill-red {
    height: 3px;
    background: linear-gradient(90deg, #ff0080, #ff4444);
    border-radius: 2px;
}

.metric-pct {
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    color: #333;
    margin-top: 4px;
    text-align: right;
}

.big-stats-row {
    display: flex;
    gap: 12px;
    margin-top: 8px;
}

.big-stat-box {
    flex: 1;
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 10px;
    padding: 16px;
}

.big-stat-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    letter-spacing: 2px;
    line-height: 1;
}

.big-stat-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.5rem;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 6px;
}

.divider {
    height: 1px;
    background: #111;
    margin: 24px 0;
}

/* Ocultar elementos default de streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

[data-testid="stMetricValue"] { color: #fff !important; }
[data-testid="stMetricLabel"] { color: #444 !important; }

.stRadio label { color: #888 !important; }
.stRadio [data-testid="stMarkdownContainer"] p { color: #888 !important; }

button[kind="primary"] {
    background: #00ff87 !important;
    color: #000 !important;
    border: none !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
}

/* Tablas en modo oscuro */
[data-testid="stDataFrame"] {
    background: #0d0d0d !important;
}

.historical-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 3px;
    color: #fff;
}

.historical-month {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    color: #333;
    letter-spacing: 2px;
    margin: 20px 0 12px;
}
</style>
""", unsafe_allow_html=True)

today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day
progress_pct = (days_elapsed / days_in_month * 100)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ CONTROL")
    
    vista = st.radio(
        "",
        ["📈 MES ACTUAL", "📊 HISTÓRICO"],
        index=0
    )
    
    st.markdown("---")
    
    if vista == "📈 MES ACTUAL":
        if st.button("🔄 ACTUALIZAR", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown(f"""
    <div style='margin-top: 20px;'>
        <div style='font-family: Space Mono, monospace; font-size: 0.55rem; color: #333; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;'>STATUS</div>
        <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #555;'>📅 {today.strftime('%d/%m/%Y')}</div>
        <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #555; margin-top: 4px;'>⏱ DÍA {days_elapsed}/{days_in_month}</div>
        <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #00ff87; margin-top: 4px;'>▶ {progress_pct:.0f}% DEL MES</div>
    </div>
    """, unsafe_allow_html=True)

# Función de datos
@st.cache_data(ttl=3600, show_spinner=False)
def get_monthly_data(year, month):
    data = {
        'month': month, 'year': year,
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

metas = {
    'steps_avg': 10000, 'activities': 28, 'strength': 10,
    'days_before_930': 15, 'sleep_hours_avg': 7.5,
    'hr_zone_1_3': 19.3, 'hr_zone_4_5': 2.9
}

def get_color(pct):
    if pct >= 100: return "green"
    elif pct >= 70: return "yellow"
    else: return "red"

def render_metric(nombre, valor, meta, unidad="", tipo='total'):
    if tipo == 'promedio':
        esperado = meta
    else:
        esperado = (meta / days_in_month) * days_elapsed
    
    pct = min((valor / esperado * 100) if esperado > 0 else 0, 100)
    color = get_color(pct)
    
    if unidad:
        val_display = f"{valor}{unidad}"
    elif valor >= 1000:
        val_display = f"{valor:,}"
    else:
        val_display = str(valor)
    
    bar_width = int(pct)
    
    st.markdown(f"""
    <div class="metric-wrap">
        <div class="metric-header">
            <span class="metric-name">{nombre}</span>
            <span class="metric-value val-{color}">{val_display}</span>
        </div>
        <div class="metric-bar-bg">
            <div class="metric-bar-fill-{color}" style="width:{bar_width}%"></div>
        </div>
        <div class="metric-pct">{pct:.0f}% — META: {meta:,}{unidad}</div>
    </div>
    """, unsafe_allow_html=True)

if vista == "📈 MES ACTUAL":
    # Header
    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hud-title">FITNESS TRACKER</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">FEB 2026 · DÍA {days_elapsed}/{days_in_month} · {progress_pct:.0f}% DEL MES</div>', unsafe_allow_html=True)
    
    with st.spinner(''):
        data = get_monthly_data(current_year, current_month)
    
    # Métricas en 2 columnas
    st.markdown('<div class="section-label">// HÁBITOS</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_metric("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'], tipo='promedio')
        render_metric("STRENGTH TRAINING", data['strength'], metas['strength'])
        render_metric("SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", tipo='promedio')
        render_metric("HR ZONES 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")
    
    with col2:
        render_metric("ACTIVITIES MES", data['activities'], metas['activities'])
        render_metric("DÍAS ANTES 9:30 PM", data['days_before_930'], metas['days_before_930'])
        render_metric("HR ZONES 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Big stats abajo
    habitos_ok = sum([
        data['steps_avg'] >= metas['steps_avg'],
        data['activities'] >= (metas['activities'] / days_in_month) * days_elapsed,
        data['strength'] >= (metas['strength'] / days_in_month) * days_elapsed,
        data['days_before_930'] >= (metas['days_before_930'] / days_in_month) * days_elapsed,
        data['sleep_hours_avg'] >= metas['sleep_hours_avg'],
        data['hr_zone_1_3'] >= (metas['hr_zone_1_3'] / days_in_month) * days_elapsed,
        data['hr_zone_4_5'] >= (metas['hr_zone_4_5'] / days_in_month) * days_elapsed,
    ])
    
    steps_color = "#00ff87" if data['steps_avg'] >= metas['steps_avg'] else "#ff4444"
    habitos_color = "#00ff87" if habitos_ok >= 5 else "#ffd700" if habitos_ok >= 3 else "#ff4444"
    
    st.markdown(f"""
    <div class="big-stats-row">
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:{steps_color}">{data['steps_avg']:,}</div>
            <div class="big-stat-label">STEPS HOY AVG</div>
        </div>
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:{habitos_color}">{habitos_ok}/7</div>
            <div class="big-stat-label">HÁBITOS EN META</div>
        </div>
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:#00d4ff">{progress_pct:.0f}%</div>
            <div class="big-stat-label">PROGRESO MES</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='font-family: Space Mono, monospace; font-size: 0.55rem; color: #222; text-align: right; margin-top: 20px; letter-spacing: 2px;'>
    LAST UPDATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    """, unsafe_allow_html=True)

else:
    # HISTÓRICO
    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown('<div class="historical-title">HISTÓRICO 2026</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">MESES CERRADOS</div>', unsafe_allow_html=True)
    
    meses_nombres = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
        9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
    }
    
    meses_cerrados = list(range(1, current_month))
    
    if not meses_cerrados:
        st.markdown("""
        <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #333; margin-top: 40px; text-align: center; letter-spacing: 2px;'>
        // NO HAY MESES CERRADOS AÚN
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner('Cargando histórico...'):
            for mes in meses_cerrados:
                data = get_monthly_data(2026, mes)
                
                st.markdown(f'<div class="historical-month">// {meses_nombres[mes]}</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    def render_hist(nombre, valor, meta, unidad=""):
                        pct = min((valor / meta * 100) if meta > 0 else 0, 100)
                        color = get_color(pct)
                        val_display = f"{valor:,}{unidad}" if valor >= 1000 else f"{valor}{unidad}"
                        st.markdown(f"""
                        <div class="metric-wrap">
                            <div class="metric-header">
                                <span class="metric-name">{nombre}</span>
                                <span class="metric-value val-{color}">{val_display}</span>
                            </div>
                            <div class="metric-bar-bg">
                                <div class="metric-bar-fill-{color}" style="width:{int(pct)}%"></div>
                            </div>
                            <div class="metric-pct">{pct:.0f}% — META: {meta:,}{unidad}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    render_hist("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'])
                    render_hist("STRENGTH TRAINING", data['strength'], metas['strength'])
                    render_hist("SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h")
                    render_hist("HR ZONES 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")
                
                with col2:
                    render_hist("ACTIVITIES MES", data['activities'], metas['activities'])
                    render_hist("DÍAS ANTES 9:30 PM", data['days_before_930'], metas['days_before_930'])
                    render_hist("HR ZONES 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")
                
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

"""
Fitness Tracker - Sport HUD - Mobile Friendly v2
"""

import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange

st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

* { font-family: 'DM Sans', sans-serif; }

.stApp { background-color: #050505 !important; color: #e1e8ed !important; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.top-bar {
    height: 3px;
    background: linear-gradient(90deg, #00ff87, #00d4ff, #ff0080);
    margin-bottom: 24px;
    border-radius: 2px;
}

.hud-title {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2.8rem !important;
    letter-spacing: 4px !important;
    color: #fff !important;
    line-height: 1 !important;
    margin: 0 !important;
}

.date-badge {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #00ff87;
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 6px;
    padding: 6px 14px;
    display: inline-block;
    letter-spacing: 2px;
    margin-bottom: 28px;
}

.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 4px;
    margin-bottom: 20px;
    margin-top: 8px;
}

.metric-wrap { margin-bottom: 20px; }

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.metric-name {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #888;
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
    background: #1a1a1a;
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
    color: #888;
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
    font-size: 2rem;
    letter-spacing: 2px;
    line-height: 1;
}

.big-stat-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.5rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 6px;
}

.divider { height: 1px; background: #1a1a1a; margin: 24px 0; }

.historical-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 3px;
    color: #fff;
}

.historical-month {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    color: #888;
    letter-spacing: 2px;
    margin: 20px 0 12px;
}

.avg-section {
    background: #0d0d0d;
    border: 1px solid #00ff87;
    border-radius: 10px;
    padding: 20px;
    margin-top: 8px;
}

.avg-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 3px;
    color: #00ff87;
    margin-bottom: 16px;
}

.avg-metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #1a1a1a;
}

.avg-metric-row:last-child { border-bottom: none; }

.avg-metric-name {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.avg-metric-val {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
}

.avg-metric-vs {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    padding: 2px 8px;
    border-radius: 4px;
}

.vs-good { background: #052e16; color: #00ff87; }
.vs-warn { background: #1c1008; color: #ffd700; }
.vs-bad { background: #1c0808; color: #ff4444; }

.stButton button {
    background: #0d0d0d !important;
    color: #888 !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 6px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 1px !important;
    width: 100% !important;
}

.stButton button:hover {
    border-color: #00ff87 !important;
    color: #00ff87 !important;
}
</style>
""", unsafe_allow_html=True)

today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day
progress_pct = (days_elapsed / days_in_month * 100)

if 'vista' not in st.session_state:
    st.session_state.vista = "mes"

# NAVEGACIÓN
col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])

with col_nav1:
    if st.button("📈 MES ACTUAL", use_container_width=True):
        st.session_state.vista = "mes"
        st.rerun()

with col_nav2:
    if st.button("📊 HISTÓRICO", use_container_width=True):
        st.session_state.vista = "historico"
        st.rerun()

with col_nav3:
    if st.button("🔄 ACTUALIZAR", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

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
        from garmin_metrics import GarminMetrics
        
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
        
        # Usar Garmin para TODAS las métricas (sin WHOOP)
        from config import GARMIN_EMAIL, GARMIN_PASSWORD
        from garmin_metrics import GarminMetrics
        
        garmin_metrics = GarminMetrics(GARMIN_EMAIL, GARMIN_PASSWORD)
        garmin_summary = garmin_metrics.get_monthly_summary(year, month)
        
        # Sobrescribir con datos de Garmin
        data['steps_avg'] = garmin_summary['steps_avg']
        data['activities'] = garmin_summary['activities']
        data['strength'] = garmin_summary['strength']
        data['days_before_930'] = garmin_summary['days_before_930']
        data['sleep_hours_avg'] = garmin_summary['sleep_hours_avg']
        data['hr_zones_1_3'] = garmin_summary['hr_zones_1_3_hours']
        data['hr_zones_4_5'] = garmin_summary['hr_zones_4_5_hours']
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
    val_display = f"{valor:,}" if (not unidad and valor >= 1000) else f"{valor}{unidad}"
    
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

def render_metric_hist(nombre, valor, meta, unidad=""):
    pct = min((valor / meta * 100) if meta > 0 else 0, 100)
    color = get_color(pct)
    val_display = f"{valor:,}" if (not unidad and valor >= 1000) else f"{valor}{unidad}"
    
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

# ============ VISTA MES ACTUAL ============
if st.session_state.vista == "mes":
    
    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hud-title">FITNESS TRACKER</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">FEB 2026 · DÍA {days_elapsed}/{days_in_month} · {progress_pct:.0f}% DEL MES</div>', unsafe_allow_html=True)
    
    with st.spinner(''):
        data = get_monthly_data(current_year, current_month)
    
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
            <div class="big-stat-label">STEPS DAILY AVG</div>
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
    <div style='font-family: Space Mono, monospace; font-size: 0.55rem; color: #444; text-align: right; margin-top: 20px; letter-spacing: 2px;'>
    LAST UPDATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    """, unsafe_allow_html=True)

# ============ VISTA HISTÓRICO ============
else:
    
    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown('<div class="historical-title">HISTÓRICO 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="date-badge">MESES CERRADOS</div>', unsafe_allow_html=True)
    
    meses_nombres = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
        9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'
    }
    
    meses_cerrados = list(range(1, current_month))
    
    if not meses_cerrados:
        st.markdown("""
        <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #888; margin-top: 40px; text-align: center; letter-spacing: 2px;'>
        // NO HAY MESES CERRADOS AÚN
        </div>
        """, unsafe_allow_html=True)
    else:
        all_data = []
        
        with st.spinner('Cargando histórico...'):
            for mes in meses_cerrados:
                data = get_monthly_data(2026, mes)
                all_data.append(data)
                
                st.markdown(f'<div class="historical-month">// {meses_nombres[mes]}</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    render_metric_hist("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'])
                    render_metric_hist("STRENGTH TRAINING", data['strength'], metas['strength'])
                    render_metric_hist("SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h")
                    render_metric_hist("HR ZONES 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")
                
                with col2:
                    render_metric_hist("ACTIVITIES MES", data['activities'], metas['activities'])
                    render_metric_hist("DÍAS ANTES 9:30 PM", data['days_before_930'], metas['days_before_930'])
                    render_metric_hist("HR ZONES 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")
                
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # SECCIÓN DE PROMEDIO ANUAL
        if all_data:
            n = len(all_data)
            avg_data = {
                'steps_avg': round(sum(d['steps_avg'] for d in all_data) / n),
                'activities': round(sum(d['activities'] for d in all_data) / n, 1),
                'strength': round(sum(d['strength'] for d in all_data) / n, 1),
                'days_before_930': round(sum(d['days_before_930'] for d in all_data) / n, 1),
                'sleep_hours_avg': round(sum(d['sleep_hours_avg'] for d in all_data) / n, 1),
                'hr_zone_1_3': round(sum(d['hr_zone_1_3'] for d in all_data) / n, 1),
                'hr_zone_4_5': round(sum(d['hr_zone_4_5'] for d in all_data) / n, 1),
            }
            
            def avg_vs_meta(valor, meta):
                pct = (valor / meta * 100) if meta > 0 else 0
                if pct >= 100:
                    return "vs-good", f"✓ {pct:.0f}%"
                elif pct >= 70:
                    return "vs-warn", f"~ {pct:.0f}%"
                else:
                    return "vs-bad", f"✗ {pct:.0f}%"
            
            metricas_avg = [
                ("STEPS DAILY AVG", avg_data['steps_avg'], metas['steps_avg'], ""),
                ("ACTIVITIES / MES", avg_data['activities'], metas['activities'], ""),
                ("STRENGTH TRAINING", avg_data['strength'], metas['strength'], ""),
                ("DÍAS ANTES 9:30 PM", avg_data['days_before_930'], metas['days_before_930'], ""),
                ("SLEEP DURATION", avg_data['sleep_hours_avg'], metas['sleep_hours_avg'], "h"),
                ("HR ZONES 1-3", avg_data['hr_zone_1_3'], metas['hr_zone_1_3'], "h"),
                ("HR ZONES 4-5", avg_data['hr_zone_4_5'], metas['hr_zone_4_5'], "h"),
            ]
            
            rows_html = ""
            for nombre, valor, meta, unidad in metricas_avg:
                css_class, label = avg_vs_meta(valor, meta)
                val_display = f"{valor:,}" if (not unidad and valor >= 1000) else f"{valor}{unidad}"
                rows_html += f"""
                <div class="avg-metric-row">
                    <span class="avg-metric-name">{nombre}</span>
                    <span class="avg-metric-val" style="color:#fff">{val_display}</span>
                    <span class="avg-metric-vs {css_class}">{label}</span>
                </div>
                """
            
            avg_html = f"""
            <div class="avg-section">
                <div class="avg-title">// PROMEDIO ANUAL ({n} MESES)</div>
                {rows_html}
            </div>
            """
            st.markdown(avg_html, unsafe_allow_html=True)  # Force refresh
            
            st.markdown(f"""
            <div style='font-family: Space Mono, monospace; font-size: 0.55rem; color: #444; text-align: right; margin-top: 20px; letter-spacing: 2px;'>
            LAST UPDATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
            """, unsafe_allow_html=True)


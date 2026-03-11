"""
Habit Tracker - Neon Glass - Multi-usuario
"""

import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange
import math

st.set_page_config(
    page_title="Habit Tracker",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: #0a0e1a !important;
    color: #e2e8f0 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.top-gradient {
    height: 3px;
    background: linear-gradient(90deg, #7c3aed, #06b6d4, #22c55e);
    margin-bottom: 20px;
    border-radius: 2px;
}

.hud-title {
    font-family: 'Inter', sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    letter-spacing: 6px !important;
    background: linear-gradient(135deg, #c4b5fd, #7c3aed, #06b6d4) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    line-height: 1.1 !important;
    margin: 0 !important;
}

.date-badge {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #cbd5e1;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 8px 16px;
    display: inline-block;
    letter-spacing: 2px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
}

.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 4px;
    margin-bottom: 16px;
    margin-top: 8px;
}

.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 14px;
    backdrop-filter: blur(20px);
    transition: border-color 0.3s ease;
}

.glass-card:hover {
    border-color: rgba(255,255,255,0.15);
}

.metric-card-name {
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 14px;
}

.metric-card-body {
    display: flex;
    align-items: center;
    gap: 18px;
}

.metric-ring-wrap {
    width: 80px;
    height: 80px;
    flex-shrink: 0;
}

.metric-ring-svg {
    width: 80px;
    height: 80px;
    filter: drop-shadow(0 0 6px rgba(0,0,0,0.3));
}

.metric-card-info {
    flex: 1;
}

.metric-card-value {
    font-family: 'Inter', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 6px;
}

.metric-card-goal {
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    color: #94a3b8;
    letter-spacing: 1px;
}

.metric-bar-bg {
    height: 3px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
    margin-top: 14px;
}

.metric-bar-fill {
    height: 3px;
    border-radius: 3px;
    transition: width 0.5s ease;
}

.summary-row {
    display: flex;
    gap: 14px;
    margin-top: 20px;
}

.summary-card {
    flex: 1;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(20px);
    text-align: center;
}

.summary-val {
    font-family: 'Inter', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
}

.summary-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.5rem;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 8px;
}

.divider {
    height: 1px;
    background: rgba(255,255,255,0.06);
    margin: 24px 0;
}

.stButton button {
    background: rgba(255,255,255,0.05) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.55rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    width: 100% !important;
    padding: 10px 8px !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    background: rgba(124, 58, 237, 0.15) !important;
    border-color: rgba(124, 58, 237, 0.4) !important;
    color: #e2e8f0 !important;
}

.stButton button:active, .stButton button:focus {
    background: rgba(124, 58, 237, 0.2) !important;
    border-color: #7c3aed !important;
    color: #c4b5fd !important;
}

.user-badge {
    font-family: 'Space Mono', monospace;
    font-size: 0.5rem;
    color: #94a3b8;
    letter-spacing: 1px;
    text-align: right;
    margin-bottom: 8px;
}

.timestamp {
    font-family: 'Space Mono', monospace;
    font-size: 0.5rem;
    color: #94a3b8;
    text-align: right;
    margin-top: 24px;
    letter-spacing: 2px;
}

.hist-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: 4px;
    background: linear-gradient(135deg, #c4b5fd, #7c3aed, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.no-data-msg {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #94a3b8;
    margin-top: 40px;
    text-align: center;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)

# ============ AUTH GATE ============
from auth import show_auth_page, show_logout_button, get_user_id, get_user_email
from garmin_setup import show_garmin_connect_form
from goals_setup import show_goals_setup, get_user_goals

if not show_auth_page():
    st.stop()

if not show_garmin_connect_form():
    st.stop()

if not show_goals_setup(first_time=True):
    st.stop()

# ============ USUARIO AUTENTICADO + GARMIN CONECTADO + METAS LISTAS ============

user_id = get_user_id()
user_email = get_user_email()

today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day
progress_pct = (days_elapsed / days_in_month * 100)

meses_nombres_upper = {
    1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR',
    5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO',
    9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'
}

if 'vista' not in st.session_state:
    st.session_state.vista = "mes"

# NAVEGACION
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
    if st.button("REFRESH", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_nav5:
    show_logout_button()

st.markdown(f'<div class="user-badge">{user_email}</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

@st.cache_data(ttl=60, show_spinner=False)
def get_monthly_data(_user_id, year, month):
    data = {
        'month': month, 'year': year,
        'steps_avg': 0, 'activities': 0, 'strength': 0,
        'sleep_hours_avg': 0,
        'hr_zone_1_3': 0, 'hr_zone_4_5': 0
    }

    try:
        from garmin_client import GarminClient

        garmin = GarminClient(_user_id)
        garmin.login()

        _today = datetime.now()
        _current_year = _today.year
        _current_month = _today.month

        start_date = datetime(year, month, 1)
        end_date = _today if (year == _current_year and month == _current_month) else datetime(year, month, monthrange(year, month)[1])

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

        # Calcular HR zones
        total_zone_1_3_secs = 0
        total_zone_4_5_secs = 0

        for activity in activities:
            activity_id = activity.get('activityId')
            if activity_id:
                try:
                    hr_zones = garmin.client.get_activity_hr_in_timezones(activity_id)
                    if hr_zones:
                        for zone in hr_zones:
                            zone_num = zone.get('zoneNumber', 0)
                            secs = zone.get('secsInZone', 0)
                            if zone_num in [1, 2, 3]:
                                total_zone_1_3_secs += secs
                            elif zone_num in [4, 5]:
                                total_zone_4_5_secs += secs
                except:
                    pass

        data['hr_zone_1_3'] = round(total_zone_1_3_secs / 3600, 1)
        data['hr_zone_4_5'] = round(total_zone_4_5_secs / 3600, 1)

        # Sleep data
        total_sleep_secs = 0
        sleep_days = 0

        current_date = start_date
        while current_date <= end_date:
            try:
                sleep_data = garmin.client.get_sleep_data(current_date.strftime('%Y-%m-%d'))
                if sleep_data and 'dailySleepDTO' in sleep_data:
                    dto = sleep_data['dailySleepDTO']
                    sleep_secs = dto.get('sleepTimeSeconds', 0)
                    total_sleep_secs += sleep_secs
                    sleep_days += 1
            except:
                pass
            current_date += timedelta(days=1)

        data['sleep_hours_avg'] = round(total_sleep_secs / sleep_days / 3600, 1) if sleep_days > 0 else 0
    except Exception as e:
        st.error(f"Error: {str(e)}")

    return data

# Cargar metas personalizadas del usuario
metas = get_user_goals()

# ============ COLORES Y RENDERING ============

def get_color(pct):
    """Verde >= 100%, Amarillo >= 70%, Rojo < 70%"""
    if pct >= 100:
        return "#22c55e"
    elif pct >= 70:
        return "#f59e0b"
    else:
        return "#ef4444"

def get_glow(color):
    """Retorna un color de glow para el SVG ring"""
    if color == "#22c55e":
        return "rgba(34,197,94,0.3)"
    elif color == "#f59e0b":
        return "rgba(245,158,11,0.3)"
    else:
        return "rgba(239,68,68,0.3)"

def render_metric(nombre, valor, meta, unidad="", tipo='total'):
    if tipo == 'promedio':
        esperado = meta
    else:
        esperado = (meta / days_in_month) * days_elapsed

    pct = min((valor / esperado * 100) if esperado > 0 else 0, 100)
    color = get_color(pct)
    glow = get_glow(color)

    val_display = f"{valor:,}" if (not unidad and isinstance(valor, int) and valor >= 1000) else f"{valor}{unidad}"
    meta_display = f"{meta:,}" if (not unidad and isinstance(meta, int) and meta >= 1000) else f"{meta}{unidad}"

    # SVG ring
    r = 36
    circumference = 2 * math.pi * r
    offset = circumference * (1 - pct / 100)

    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-card-name">{nombre}</div>
        <div class="metric-card-body">
            <div class="metric-ring-wrap">
                <svg viewBox="0 0 100 100" class="metric-ring-svg">
                    <circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="4.5"/>
                    <circle cx="50" cy="50" r="{r}" fill="none" stroke="{color}" stroke-width="4.5"
                        stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
                        transform="rotate(-90 50 50)" stroke-linecap="round"
                        style="filter: drop-shadow(0 0 4px {glow});"/>
                    <text x="50" y="50" text-anchor="middle" dy=".35em" fill="{color}"
                        font-family="Space Mono, monospace" font-size="15" font-weight="700">{pct:.0f}%</text>
                </svg>
            </div>
            <div class="metric-card-info">
                <div class="metric-card-value" style="color:{color}">{val_display}</div>
                <div class="metric-card-goal">META: {meta_display}</div>
            </div>
        </div>
        <div class="metric-bar-bg">
            <div class="metric-bar-fill" style="width:{int(pct)}%; background:{color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============ VISTA MES ACTUAL ============
if st.session_state.vista == "mes":

    st.markdown('<div class="top-gradient"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hud-title">HABIT TRACKER</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">{meses_nombres_upper[current_month]} {current_year} &middot; DIA {days_elapsed}/{days_in_month} &middot; {progress_pct:.0f}% DEL MES</div>', unsafe_allow_html=True)

    with st.spinner(''):
        data = get_monthly_data(user_id, current_year, current_month)

    st.markdown('<div class="section-label">// HABITOS</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        render_metric("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'], tipo='promedio')
        render_metric("STRENGTH TRAINING", data['strength'], metas['strength'])
        render_metric("SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", tipo='promedio')
        render_metric("HR ZONES 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")

    with col2:
        render_metric("ACTIVITIES", data['activities'], metas['activities'])
        render_metric("HR ZONES 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Summary stats
    habitos_ok = sum([
        data['steps_avg'] >= metas['steps_avg'],
        data['activities'] >= (metas['activities'] / days_in_month) * days_elapsed,
        data['strength'] >= (metas['strength'] / days_in_month) * days_elapsed,
        data['sleep_hours_avg'] >= metas['sleep_hours_avg'],
        data['hr_zone_1_3'] >= (metas['hr_zone_1_3'] / days_in_month) * days_elapsed,
        data['hr_zone_4_5'] >= (metas['hr_zone_4_5'] / days_in_month) * days_elapsed,
    ])

    steps_color = "#22c55e" if data['steps_avg'] >= metas['steps_avg'] else "#ef4444"
    habitos_color = "#22c55e" if habitos_ok >= 4 else "#f59e0b" if habitos_ok >= 3 else "#ef4444"

    st.markdown(f"""
    <div class="summary-row">
        <div class="summary-card">
            <div class="summary-val" style="color:{steps_color}">{data['steps_avg']:,}</div>
            <div class="summary-label">STEPS DAILY AVG</div>
        </div>
        <div class="summary-card">
            <div class="summary-val" style="color:{habitos_color}">{habitos_ok}/6</div>
            <div class="summary-label">HABITOS ON TRACK</div>
        </div>
        <div class="summary-card">
            <div class="summary-val" style="color:#7c3aed">{progress_pct:.0f}%</div>
            <div class="summary-label">PROGRESO MES</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="timestamp">LAST UPDATE: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)

# ============ VISTA METAS ============
elif st.session_state.vista == "metas":
    show_goals_setup(first_time=False)

# ============ VISTA HISTORICO ============
elif st.session_state.vista == "historico":

    st.markdown('<div class="top-gradient"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hist-title">HISTORICO {current_year}</div>', unsafe_allow_html=True)

    meses_nombres = {
        1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR',
        5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO',
        9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'
    }

    meses_cerrados = list(range(1, current_month))

    if not meses_cerrados:
        st.markdown('<div class="no-data-msg">// NO HAY MESES CERRADOS AUN</div>', unsafe_allow_html=True)
    else:
        all_data = []

        with st.spinner('Cargando historico...'):
            for mes in meses_cerrados:
                d = get_monthly_data(user_id, current_year, mes)
                all_data.append(d)

        # ---- PROMEDIO ANUAL ----
        n = len(all_data)
        avg_data = {
            'steps_avg': round(sum(d['steps_avg'] for d in all_data) / n),
            'activities': round(sum(d['activities'] for d in all_data) / n, 1),
            'strength': round(sum(d['strength'] for d in all_data) / n, 1),
            'sleep_hours_avg': round(sum(d['sleep_hours_avg'] for d in all_data) / n, 1),
            'hr_zone_1_3': round(sum(d['hr_zone_1_3'] for d in all_data) / n, 1),
            'hr_zone_4_5': round(sum(d['hr_zone_4_5'] for d in all_data) / n, 1),
        }

        def hist_color(valor, meta):
            pct = (valor / meta * 100) if meta > 0 else 0
            if pct >= 100: return "#22c55e"
            elif pct >= 70: return "#f59e0b"
            else: return "#ef4444"

        metricas_avg = [
            ("STEPS AVG", avg_data['steps_avg'], metas['steps_avg'], ""),
            ("ACTIVITIES", avg_data['activities'], metas['activities'], ""),
            ("STRENGTH", avg_data['strength'], metas['strength'], ""),
            ("SLEEP", avg_data['sleep_hours_avg'], metas['sleep_hours_avg'], "h"),
            ("HR Z1-3", avg_data['hr_zone_1_3'], metas['hr_zone_1_3'], "h"),
            ("HR Z4-5", avg_data['hr_zone_4_5'], metas['hr_zone_4_5'], "h"),
        ]

        rows_html = ""
        for nombre, valor, meta, unidad in metricas_avg:
            color = hist_color(valor, meta)
            val_display = f"{valor:,}" if (not unidad and isinstance(valor, int) and valor >= 1000) else f"{valor}{unidad}"
            pct_raw = (valor / meta * 100) if meta > 0 else 0
            bar_w = min(int(pct_raw), 100)
            rows_html += f'<div style="display:flex;align-items:center;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);">'
            rows_html += f'<span style="font-family:Space Mono,monospace;font-size:0.6rem;color:#cbd5e1;text-transform:uppercase;letter-spacing:1px;width:28%;">{nombre}</span>'
            rows_html += f'<span style="font-family:Inter,sans-serif;font-size:0.9rem;font-weight:700;color:{color};width:18%;text-align:right;">{val_display}</span>'
            rows_html += f'<div style="width:34%;margin:0 14px;"><div style="height:4px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden;"><div style="height:4px;background:{color};border-radius:4px;width:{bar_w}%;"></div></div></div>'
            rows_html += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:{color};width:10%;text-align:right;">{pct_raw:.0f}%</span>'
            rows_html += '</div>'

        avg_html = f'<div class="glass-card" style="border-color:rgba(124,58,237,0.3);">'
        avg_html += f'<div style="font-family:Inter,sans-serif;font-size:1.1rem;font-weight:700;letter-spacing:3px;background:linear-gradient(135deg,#c4b5fd,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:16px;">// PROMEDIO ANUAL ({n} MESES)</div>'
        avg_html += rows_html
        avg_html += '</div>'
        st.markdown(avg_html, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ---- METAS AJUSTADAS ----
        remaining = 12 - n
        if remaining > 0:
            adjusted_metrics = [
                ("STEPS AVG", avg_data['steps_avg'], metas['steps_avg'], "", True),
                ("ACTIVITIES", avg_data['activities'], metas['activities'], "", False),
                ("STRENGTH", avg_data['strength'], metas['strength'], "", False),
                ("SLEEP", avg_data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", True),
                ("HR Z1-3", avg_data['hr_zone_1_3'], metas['hr_zone_1_3'], "h", False),
                ("HR Z4-5", avg_data['hr_zone_4_5'], metas['hr_zone_4_5'], "h", False),
            ]

            adj_rows = ""
            any_behind = False
            for nombre, avg_val, goal, unidad, is_avg in adjusted_metrics:
                # Calcular meta ajustada para los meses restantes
                adjusted = (goal * 12 - avg_val * n) / remaining
                adjusted = max(adjusted, 0)  # No puede ser negativa

                if is_avg:
                    adjusted_r = round(adjusted, 1)
                else:
                    adjusted_r = round(adjusted, 1)

                # Diferencia vs meta original
                diff_pct = ((adjusted - goal) / goal * 100) if goal > 0 else 0

                if diff_pct <= 0:
                    color = "#22c55e"
                    arrow = "&#9660;"  # down arrow (easier)
                    status = "ON TRACK"
                elif diff_pct <= 30:
                    color = "#f59e0b"
                    arrow = "&#9650;"  # up arrow
                    status = f"+{diff_pct:.0f}%"
                    any_behind = True
                else:
                    color = "#ef4444"
                    arrow = "&#9650;"
                    status = f"+{diff_pct:.0f}%"
                    any_behind = True

                adj_display = f"{adjusted_r:,}" if (not unidad and isinstance(adjusted_r, (int, float)) and adjusted_r >= 1000) else f"{adjusted_r}{unidad}"
                goal_display = f"{goal:,}" if (not unidad and isinstance(goal, (int, float)) and goal >= 1000) else f"{goal}{unidad}"

                adj_rows += f'<div style="display:flex;align-items:center;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);">'
                adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:#cbd5e1;text-transform:uppercase;letter-spacing:1px;width:24%;">{nombre}</span>'
                adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:#94a3b8;width:18%;text-align:center;">META: {goal_display}</span>'
                adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:#94a3b8;width:6%;text-align:center;">&#8594;</span>'
                adj_rows += f'<span style="font-family:Inter,sans-serif;font-size:0.9rem;font-weight:700;color:{color};width:22%;text-align:center;">{adj_display}</span>'
                adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:{color};width:18%;text-align:right;">{arrow} {status}</span>'
                adj_rows += '</div>'

            border_color = "rgba(245,158,11,0.3)" if any_behind else "rgba(34,197,94,0.3)"
            title_color = "#f59e0b" if any_behind else "#22c55e"

            adj_html = f'<div class="glass-card" style="border-color:{border_color};">'
            adj_html += f'<div style="font-family:Inter,sans-serif;font-size:1.1rem;font-weight:700;letter-spacing:3px;color:{title_color};margin-bottom:6px;">// METAS AJUSTADAS</div>'
            adj_html += f'<div style="font-family:Space Mono,monospace;font-size:0.5rem;color:#94a3b8;letter-spacing:1px;margin-bottom:16px;line-height:1.6;">PARA CUMPLIR TUS METAS ANUALES, ESTOS SON LOS OBJETIVOS<br>MENSUALES QUE NECESITAS EN LOS {remaining} MESES RESTANTES</div>'
            adj_html += adj_rows
            adj_html += '</div>'
            st.markdown(adj_html, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ---- TABLA COMPACTA POR MES ----
        st.markdown('<div class="section-label">// DETALLE POR MES</div>', unsafe_allow_html=True)

        metric_keys = [
            ("STEPS AVG", 'steps_avg', metas['steps_avg'], ""),
            ("ACTIVITIES", 'activities', metas['activities'], ""),
            ("STRENGTH", 'strength', metas['strength'], ""),
            ("SLEEP", 'sleep_hours_avg', metas['sleep_hours_avg'], "h"),
            ("HR Z1-3", 'hr_zone_1_3', metas['hr_zone_1_3'], "h"),
            ("HR Z4-5", 'hr_zone_4_5', metas['hr_zone_4_5'], "h"),
        ]

        header = '<div style="display:flex;gap:0;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.1);">'
        header += '<div style="font-family:Space Mono,monospace;font-size:0.55rem;color:#94a3b8;letter-spacing:1px;width:25%;text-transform:uppercase;">METRICA</div>'
        for mes in meses_cerrados:
            header += f'<div style="font-family:Space Mono,monospace;font-size:0.55rem;color:#64748b;letter-spacing:1px;flex:1;text-align:center;">{meses_nombres[mes]}</div>'
        header += '</div>'

        table_rows = ""
        for label, key, meta, unidad in metric_keys:
            table_rows += '<div style="display:flex;gap:0;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
            table_rows += f'<div style="font-family:Space Mono,monospace;font-size:0.55rem;color:#94a3b8;letter-spacing:1px;width:25%;text-transform:uppercase;display:flex;align-items:center;">{label}</div>'
            for d in all_data:
                valor = d[key]
                pct = (valor / meta * 100) if meta > 0 else 0
                color = hist_color(valor, meta)
                val_display = f"{valor:,}" if (not unidad and isinstance(valor, int) and valor >= 1000) else f"{valor}{unidad}"
                table_rows += f'<div style="font-family:Inter,sans-serif;font-size:0.75rem;font-weight:700;color:{color};flex:1;text-align:center;">{val_display}</div>'
            table_rows += '</div>'

        table_html = f'<div class="glass-card">{header}{table_rows}</div>'
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown(f'<div class="timestamp">LAST UPDATE: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)

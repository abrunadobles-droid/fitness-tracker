"""
Fitness Tracker - Sport HUD Dashboard v3
- Fixed: HR zones key mismatch (always showed 0)
- Fixed: Double cache decorator
- Fixed: Hardcoded month name
- Fixed: Activity date filtering
- Improved: Historical dashboard with overall averages, scores, comparison table
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

.month-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 20px 0 12px;
}

.month-score {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    padding: 4px 12px;
    border-radius: 6px;
    letter-spacing: 1px;
}

.score-good { background: #052e16; color: #00ff87; border: 1px solid #00ff87; }
.score-mid { background: #1c1008; color: #ffd700; border: 1px solid #ffd700; }
.score-bad { background: #1c0808; color: #ff4444; border: 1px solid #ff4444; }

.comparison-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    margin-top: 12px;
}

.comparison-table th {
    color: #00d4ff;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding: 10px 8px;
    border-bottom: 2px solid #1a1a1a;
    text-align: center;
    font-size: 0.55rem;
}

.comparison-table th:first-child {
    text-align: left;
}

.comparison-table td {
    padding: 8px;
    border-bottom: 1px solid #111;
    text-align: center;
    color: #ccc;
}

.comparison-table td:first-child {
    text-align: left;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.comparison-table tr:last-child td {
    border-bottom: none;
}

.td-good { color: #00ff87 !important; font-weight: 700; }
.td-warn { color: #ffd700 !important; }
.td-bad { color: #ff4444 !important; }

.trend-up { color: #00ff87; }
.trend-down { color: #ff4444; }
.trend-flat { color: #888; }
</style>
""", unsafe_allow_html=True)

# ============ GLOBAL STATE ============
today = datetime.now()
current_month = today.month
current_year = today.year
days_in_month = monthrange(current_year, current_month)[1]
days_elapsed = today.day
progress_pct = (days_elapsed / days_in_month * 100)

MESES_NOMBRES = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}

MESES_CORTOS = {
    1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR',
    5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO',
    9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'
}

metas = {
    'steps_avg': 10000, 'activities': 28, 'strength': 10,
    'days_before_930': 15, 'sleep_hours_avg': 7.5,
    'hr_zones_1_3': 19.3, 'hr_zones_4_5': 2.9
}

# Metric display configuration: (label, unit, type for current month)
METRIC_CONFIG = {
    'steps_avg': ('STEPS DAILY AVG', '', 'promedio'),
    'activities': ('ACTIVITIES / MES', '', 'total'),
    'strength': ('STRENGTH TRAINING', '', 'total'),
    'days_before_930': ('DIAS ANTES 9:30 PM', '', 'total'),
    'sleep_hours_avg': ('SLEEP DURATION AVG', 'h', 'promedio'),
    'hr_zones_1_3': ('HR ZONES 1-3', 'h', 'total'),
    'hr_zones_4_5': ('HR ZONES 4-5', 'h', 'total'),
}

# Order for display
METRIC_ORDER = [
    'steps_avg', 'activities', 'strength', 'days_before_930',
    'sleep_hours_avg', 'hr_zones_1_3', 'hr_zones_4_5'
]

if 'vista' not in st.session_state:
    st.session_state.vista = "mes"

# ============ NAVIGATION ============
col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])

with col_nav1:
    if st.button("MES ACTUAL", use_container_width=True):
        st.session_state.vista = "mes"
        st.rerun()

with col_nav2:
    if st.button("HISTORICO", use_container_width=True):
        st.session_state.vista = "historico"
        st.rerun()

with col_nav3:
    if st.button("ACTUALIZAR", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ============ DATA FETCHING (FIXED) ============
@st.cache_data(ttl=60)
def get_monthly_data(year, month):
    data = {
        'month': month, 'year': year,
        'steps_avg': 0, 'activities': 0, 'strength': 0,
        'days_before_930': 0, 'sleep_hours_avg': 0,
        'hr_zones_1_3': 0, 'hr_zones_4_5': 0
    }

    try:
        import config
        from garmin_client import GarminClient

        garmin = GarminClient()
        garmin.login()

        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        is_current = (year == current_year and month == current_month)
        end_date = today if is_current else datetime(year, month, last_day)

        # --- Steps ---
        total_steps = 0
        days_with_steps = 0

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

        data['steps_avg'] = round(total_steps / days_with_steps) if days_with_steps > 0 else 0

        # --- Activities ---
        all_activities = garmin.get_activities(start_date, end_date, limit=100)
        filtered_activities = []
        strength_count = 0

        for activity in all_activities:
            activity_date_str = activity.get('startTimeLocal', '')
            if activity_date_str:
                activity_date = datetime.strptime(activity_date_str[:10], '%Y-%m-%d')
                if activity_date.year == year and activity_date.month == month:
                    activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
                    if 'breath' not in activity_type and 'meditation' not in activity_type:
                        filtered_activities.append(activity)
                        if any(kw in activity_type for kw in ['strength', 'training', 'gym', 'weight']):
                            strength_count += 1

        data['activities'] = len(filtered_activities)
        data['strength'] = strength_count

        # --- HR Zones ---
        total_zone_1_3_secs = 0
        total_zone_4_5_secs = 0

        for activity in filtered_activities:
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

        data['hr_zones_1_3'] = round(total_zone_1_3_secs / 3600, 1)
        data['hr_zones_4_5'] = round(total_zone_4_5_secs / 3600, 1)

        # --- Sleep ---
        total_sleep_secs = 0
        days_before_930 = 0
        sleep_days = 0

        current_date = start_date
        while current_date <= end_date:
            try:
                sleep_data = garmin.client.get_sleep_data(current_date.strftime('%Y-%m-%d'))
                if sleep_data and 'dailySleepDTO' in sleep_data:
                    dto = sleep_data['dailySleepDTO']
                    total_sleep_secs += dto.get('sleepTimeSeconds', 0)
                    sleep_days += 1

                    sleep_start_ts = dto.get('sleepStartTimestampLocal')
                    if sleep_start_ts:
                        sleep_start = datetime.fromtimestamp(sleep_start_ts / 1000)
                        if sleep_start.hour < 21 or (sleep_start.hour == 21 and sleep_start.minute <= 30):
                            days_before_930 += 1
            except:
                pass
            current_date += timedelta(days=1)

        data['sleep_hours_avg'] = round(total_sleep_secs / sleep_days / 3600, 1) if sleep_days > 0 else 0
        data['days_before_930'] = days_before_930
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")

    return data


# ============ HELPER FUNCTIONS ============
def get_color(pct):
    if pct >= 100: return "green"
    elif pct >= 70: return "yellow"
    else: return "red"


def format_value(key, value):
    """Format a metric value for display."""
    _, unit, _ = METRIC_CONFIG[key]
    if not unit and value >= 1000:
        return f"{value:,}"
    return f"{value}{unit}"


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


def calculate_score(data):
    """Calculate how many of the 7 goals are met for a closed month."""
    score = 0
    for key in METRIC_ORDER:
        if data[key] >= metas[key]:
            score += 1
    return score


def score_css_class(score):
    if score >= 5: return "score-good"
    elif score >= 3: return "score-mid"
    else: return "score-bad"


def avg_vs_meta(valor, meta):
    pct = (valor / meta * 100) if meta > 0 else 0
    if pct >= 100:
        return "vs-good", f"{pct:.0f}%"
    elif pct >= 70:
        return "vs-warn", f"~ {pct:.0f}%"
    else:
        return "vs-bad", f"{pct:.0f}%"


def value_color_class(valor, meta):
    pct = (valor / meta * 100) if meta > 0 else 0
    if pct >= 100: return "td-good"
    elif pct >= 70: return "td-warn"
    else: return "td-bad"


def calculate_averages(all_data):
    """Calculate averages across multiple months of data."""
    n = len(all_data)
    if n == 0:
        return {}
    avg = {}
    for key in METRIC_ORDER:
        total = sum(d[key] for d in all_data)
        if key in ('steps_avg',):
            avg[key] = round(total / n)
        else:
            avg[key] = round(total / n, 1)
    return avg


# ============ VIEW: MES ACTUAL ============
if st.session_state.vista == "mes":

    month_name = MESES_CORTOS[current_month]

    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hud-title">FITNESS TRACKER</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="date-badge">{month_name} {current_year} · DIA {days_elapsed}/{days_in_month} · {progress_pct:.0f}% DEL MES</div>',
        unsafe_allow_html=True
    )

    with st.spinner(''):
        data = get_monthly_data(current_year, current_month)

    st.markdown('<div class="section-label">// HABITOS</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        render_metric("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'], tipo='promedio')
        render_metric("STRENGTH TRAINING", data['strength'], metas['strength'])
        render_metric("SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", tipo='promedio')
        render_metric("HR ZONES 1-3", data['hr_zones_1_3'], metas['hr_zones_1_3'], "h")

    with col2:
        render_metric("ACTIVITIES MES", data['activities'], metas['activities'])
        render_metric("DIAS ANTES 9:30 PM", data['days_before_930'], metas['days_before_930'])
        render_metric("HR ZONES 4-5", data['hr_zones_4_5'], metas['hr_zones_4_5'], "h")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    habitos_ok = sum([
        data['steps_avg'] >= metas['steps_avg'],
        data['activities'] >= (metas['activities'] / days_in_month) * days_elapsed,
        data['strength'] >= (metas['strength'] / days_in_month) * days_elapsed,
        data['days_before_930'] >= (metas['days_before_930'] / days_in_month) * days_elapsed,
        data['sleep_hours_avg'] >= metas['sleep_hours_avg'],
        data['hr_zones_1_3'] >= (metas['hr_zones_1_3'] / days_in_month) * days_elapsed,
        data['hr_zones_4_5'] >= (metas['hr_zones_4_5'] / days_in_month) * days_elapsed,
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
            <div class="big-stat-label">HABITOS EN META</div>
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

# ============ VIEW: HISTORICO ============
else:

    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="historical-title">HISTORICO {current_year}</div>', unsafe_allow_html=True)
    st.markdown('<div class="date-badge">MESES CERRADOS</div>', unsafe_allow_html=True)

    meses_cerrados = list(range(1, current_month))

    if not meses_cerrados:
        st.markdown("""
        <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #888; margin-top: 40px; text-align: center; letter-spacing: 2px;'>
        // NO HAY MESES CERRADOS AUN
        </div>
        """, unsafe_allow_html=True)
    else:
        all_data = []

        with st.spinner('Cargando historico...'):
            for mes in meses_cerrados:
                data = get_monthly_data(current_year, mes)
                all_data.append(data)

        # ---- SECTION 1: OVERALL AVERAGE ----
        avg_data = calculate_averages(all_data)
        n = len(all_data)
        avg_score = 0
        for key in METRIC_ORDER:
            if avg_data[key] >= metas[key]:
                avg_score += 1

        avg_score_class = score_css_class(avg_score)

        rows_html = ""
        for key in METRIC_ORDER:
            label, unit, _ = METRIC_CONFIG[key]
            valor = avg_data[key]
            meta = metas[key]
            css_class, pct_label = avg_vs_meta(valor, meta)
            val_display = f"{valor:,}" if (not unit and valor >= 1000) else f"{valor}{unit}"
            meta_display = f"{meta:,}" if (not unit and meta >= 1000) else f"{meta}{unit}"

            rows_html += f"""
            <div class="avg-metric-row">
                <span class="avg-metric-name">{label}</span>
                <span class="avg-metric-val" style="color:#fff">{val_display}</span>
                <span style="font-family: Space Mono, monospace; font-size: 0.55rem; color: #555;">{meta_display}</span>
                <span class="avg-metric-vs {css_class}">{pct_label}</span>
            </div>
            """

        st.markdown(f"""
        <div class="avg-section">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div class="avg-title">// PROMEDIO GENERAL ({n} {'MES' if n == 1 else 'MESES'})</div>
                <span class="month-score {avg_score_class}">{avg_score}/7</span>
            </div>
            {rows_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ---- SECTION 2: PER-MONTH DETAILS ----
        st.markdown('<div class="section-label">// DETALLE POR MES</div>', unsafe_allow_html=True)

        for i, (mes, data) in enumerate(zip(meses_cerrados, all_data)):
            score = calculate_score(data)
            s_class = score_css_class(score)

            st.markdown(f"""
            <div class="month-header-row">
                <span class="historical-month">// {MESES_NOMBRES[mes]} {current_year}</span>
                <span class="month-score {s_class}">{score}/7 METAS</span>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                render_metric_hist("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'])
                render_metric_hist("STRENGTH TRAINING", data['strength'], metas['strength'])
                render_metric_hist("SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h")
                render_metric_hist("HR ZONES 1-3", data['hr_zones_1_3'], metas['hr_zones_1_3'], "h")

            with col2:
                render_metric_hist("ACTIVITIES MES", data['activities'], metas['activities'])
                render_metric_hist("DIAS ANTES 9:30 PM", data['days_before_930'], metas['days_before_930'])
                render_metric_hist("HR ZONES 4-5", data['hr_zones_4_5'], metas['hr_zones_4_5'], "h")

            # Trend vs previous month
            if i > 0:
                prev = all_data[i - 1]
                trends = []
                for key in METRIC_ORDER:
                    label, unit, _ = METRIC_CONFIG[key]
                    curr_val = data[key]
                    prev_val = prev[key]
                    if prev_val > 0:
                        change_pct = ((curr_val - prev_val) / prev_val) * 100
                    elif curr_val > 0:
                        change_pct = 100
                    else:
                        change_pct = 0

                    if change_pct > 2:
                        arrow = "&#9650;"  # up triangle
                        css = "trend-up"
                    elif change_pct < -2:
                        arrow = "&#9660;"  # down triangle
                        css = "trend-down"
                    else:
                        arrow = "&#9644;"  # dash
                        css = "trend-flat"

                    short_label = label.split('/')[0].strip()[:12]
                    trends.append(
                        f'<span style="margin-right:16px;">'
                        f'<span class="{css}" style="font-family:Space Mono,monospace;font-size:0.55rem;">'
                        f'{arrow} {short_label} {change_pct:+.0f}%</span></span>'
                    )

                st.markdown(
                    f'<div style="margin: 8px 0 4px; overflow-x: auto; white-space: nowrap;">{"".join(trends)}</div>',
                    unsafe_allow_html=True
                )

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ---- SECTION 3: COMPARISON TABLE ----
        if len(all_data) >= 1:
            st.markdown('<div class="section-label">// COMPARATIVA MENSUAL</div>', unsafe_allow_html=True)

            # Build table header
            month_headers = "".join(
                f'<th>{MESES_CORTOS[m]}</th>' for m in meses_cerrados
            )
            header_html = f"<tr><th>METRICA</th>{month_headers}<th>PROMEDIO</th><th>META</th></tr>"

            # Build table rows
            body_html = ""
            for key in METRIC_ORDER:
                label, unit, _ = METRIC_CONFIG[key]
                meta = metas[key]

                cells = ""
                for data in all_data:
                    val = data[key]
                    color_class = value_color_class(val, meta)
                    if not unit and val >= 1000:
                        val_str = f"{val:,}"
                    else:
                        val_str = f"{val}{unit}"
                    cells += f'<td class="{color_class}">{val_str}</td>'

                # Average column
                avg_val = avg_data[key]
                avg_color = value_color_class(avg_val, meta)
                if not unit and avg_val >= 1000:
                    avg_str = f"{avg_val:,}"
                else:
                    avg_str = f"{avg_val}{unit}"

                # Meta column
                if not unit and meta >= 1000:
                    meta_str = f"{meta:,}"
                else:
                    meta_str = f"{meta}{unit}"

                body_html += f"<tr><td>{label}</td>{cells}<td class='{avg_color}' style='font-weight:700;'>{avg_str}</td><td>{meta_str}</td></tr>"

            # Score row
            score_cells = ""
            for data in all_data:
                s = calculate_score(data)
                s_color = "td-good" if s >= 5 else "td-warn" if s >= 3 else "td-bad"
                score_cells += f'<td class="{s_color}" style="font-weight:700;">{s}/7</td>'

            avg_s_color = "td-good" if avg_score >= 5 else "td-warn" if avg_score >= 3 else "td-bad"
            body_html += f'<tr><td style="color:#00d4ff;">SCORE</td>{score_cells}<td class="{avg_s_color}" style="font-weight:700;">{avg_score}/7</td><td>7/7</td></tr>'

            st.markdown(f"""
            <div style="background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 10px; padding: 16px; overflow-x: auto;">
                <table class="comparison-table">
                    {header_html}
                    {body_html}
                </table>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='font-family: Space Mono, monospace; font-size: 0.55rem; color: #444; text-align: right; margin-top: 20px; letter-spacing: 2px;'>
        LAST UPDATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
        """, unsafe_allow_html=True)

"""
Fitness Tracker - Sport HUD Dashboard v4
- Split into Fitness Habits & Sleep Habits sections
- HR Zones from WHOOP (total monthly hours)
- Sleep metrics from WHOOP (duration, recovery, resting HR, consistency)
- Steps, Activities, Strength from Garmin
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

.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #1a1a1a, #333, #1a1a1a, transparent);
    margin: 28px 0 20px;
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

.metric-source {
    font-family: 'Space Mono', monospace;
    font-size: 0.45rem;
    color: #444;
    letter-spacing: 1px;
    margin-left: 6px;
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

.comparison-table th:first-child { text-align: left; }

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

.comparison-table tr:last-child td { border-bottom: none; }

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

# Default goals (used if no DB goals available)
metas = {
    'steps_avg': 10000, 'activities': 28, 'strength': 10,
    'sleep_hours_avg': 7.5,
    'hr_zone_1_3': 19.3, 'hr_zone_4_5': 2.9,
    'recovery_score': 50.0, 'resting_hr': 55.0, 'sleep_consistency': 80.0,
}

# Fitness Habits metrics (Garmin + WHOOP HR zones)
FITNESS_METRICS = [
    # (key, label, unit, type)
    ('steps_avg', 'STEPS DAILY AVG', '', 'promedio'),
    ('activities', 'ACTIVITIES / MES', '', 'total'),
    ('strength', 'STRENGTH TRAINING', '', 'total'),
    ('hr_zone_1_3', 'HR ZONES 1-3', 'h', 'total'),
    ('hr_zone_4_5', 'HR ZONES 4-5', 'h', 'total'),
]

# Sleep Habits metrics (all WHOOP)
SLEEP_METRICS = [
    ('sleep_hours_avg', 'AVE SLEEP DURATION', 'h', 'promedio'),
    ('recovery_score', 'RECOVERY SCORE', '%', 'promedio'),
    ('resting_hr', 'RESTING HR', ' bpm', 'promedio_inverted'),
    ('sleep_consistency', 'SLEEP CONSISTENCY', '%', 'promedio'),
]

ALL_METRIC_KEYS = [m[0] for m in FITNESS_METRICS + SLEEP_METRICS]

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

# ============ DATA FETCHING ============
from whoop_streamlit import get_whoop_data


@st.cache_data(ttl=60)
def get_monthly_data(year, month):
    data = {
        'month': month, 'year': year,
        'steps_avg': 0, 'activities': 0, 'strength': 0,
        'sleep_hours_avg': 0,
        'hr_zone_1_3': 0, 'hr_zone_4_5': 0,
        'recovery_score': 0, 'resting_hr': 0, 'sleep_consistency': 0,
        'whoop_source': 'NO DATA',
    }

    # --- GARMIN: Steps, Activities, Strength ---
    try:
        from garmin_client import GarminClient

        garmin = GarminClient()
        garmin.login()

        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        is_current = (year == current_year and month == current_month)
        end_date = today if is_current else datetime(year, month, last_day)

        # Steps
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

        # Activities & Strength
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

    except Exception as e:
        st.error(f"Error cargando Garmin: {str(e)}")

    # --- WHOOP: Live API with cache fallback ---
    whoop, source = get_whoop_data(year, month)
    data['whoop_source'] = source

    if whoop:
        try:
            raw_1_3 = whoop.get('hr_zones_1_3_hours', 0)
            data['hr_zone_1_3'] = round(float(raw_1_3), 1) if raw_1_3 is not None else 0
        except (TypeError, ValueError):
            data['hr_zone_1_3'] = 0
        try:
            raw_4_5 = whoop.get('hr_zones_4_5_hours', 0)
            data['hr_zone_4_5'] = round(float(raw_4_5), 1) if raw_4_5 is not None else 0
        except (TypeError, ValueError):
            data['hr_zone_4_5'] = 0

        data['sleep_hours_avg'] = round(whoop.get('sleep_hours_avg', 0), 1)
        data['recovery_score'] = round(whoop.get('avg_recovery_score', 0), 1)
        data['resting_hr'] = round(whoop.get('avg_resting_hr', 0), 1)
        data['sleep_consistency'] = round(whoop.get('avg_sleep_consistency', 0), 1)

    return data


# ============ HELPER FUNCTIONS ============
def get_color(pct):
    if pct >= 100: return "green"
    elif pct >= 70: return "yellow"
    else: return "red"


def render_metric(nombre, valor, meta, unidad="", tipo='total'):
    """Render a metric bar. tipo='promedio_inverted' means lower is better (e.g. resting HR)."""
    inverted = tipo == 'promedio_inverted'

    if inverted:
        # For inverted metrics (lower is better): at or below goal = 100%
        pct = min((meta / valor * 100) if valor > 0 else 100, 100)
    elif tipo == 'promedio' or tipo == 'promedio_inverted':
        esperado = meta
        pct = min((valor / esperado * 100) if esperado > 0 else 0, 100)
    else:
        esperado = (meta / days_in_month) * days_elapsed
        pct = min((valor / esperado * 100) if esperado > 0 else 0, 100)

    color = get_color(pct)

    if isinstance(valor, float):
        val_display = f"{valor}{unidad}"
    elif not unidad and isinstance(valor, int) and valor >= 1000:
        val_display = f"{valor:,}"
    else:
        val_display = f"{valor}{unidad}"

    meta_label = f"{'MAX' if inverted else 'META'}: {meta}{unidad}"

    st.markdown(f"""
    <div class="metric-wrap">
        <div class="metric-header">
            <span class="metric-name">{nombre}</span>
            <span class="metric-value val-{color}">{val_display}</span>
        </div>
        <div class="metric-bar-bg">
            <div class="metric-bar-fill-{color}" style="width:{int(pct)}%"></div>
        </div>
        <div class="metric-pct">{pct:.0f}% — {meta_label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_hist(nombre, valor, meta, unidad="", inverted=False):
    if inverted:
        pct = min((meta / valor * 100) if valor > 0 else 100, 100)
    else:
        pct = min((valor / meta * 100) if meta > 0 else 0, 100)
    color = get_color(pct)

    if isinstance(valor, float):
        val_display = f"{valor}{unidad}"
    elif not unidad and isinstance(valor, int) and valor >= 1000:
        val_display = f"{valor:,}"
    else:
        val_display = f"{valor}{unidad}"

    meta_label = f"{'MAX' if inverted else 'META'}: {meta}{unidad}"

    st.markdown(f"""
    <div class="metric-wrap">
        <div class="metric-header">
            <span class="metric-name">{nombre}</span>
            <span class="metric-value val-{color}">{val_display}</span>
        </div>
        <div class="metric-bar-bg">
            <div class="metric-bar-fill-{color}" style="width:{int(pct)}%"></div>
        </div>
        <div class="metric-pct">{pct:.0f}% — {meta_label}</div>
    </div>
    """, unsafe_allow_html=True)


def is_metric_on_track(key, valor, meta):
    """Check if a metric is on track (for current month with prorated totals)."""
    metric_type = dict((m[0], m[3]) for m in FITNESS_METRICS + SLEEP_METRICS).get(key, 'total')
    if metric_type == 'promedio_inverted':
        return valor <= meta
    elif metric_type == 'promedio':
        return valor >= meta
    else:
        esperado = (meta / days_in_month) * days_elapsed
        return valor >= esperado


def is_metric_met(key, valor, meta):
    """Check if a metric met its goal (for closed months)."""
    metric_type = dict((m[0], m[3]) for m in FITNESS_METRICS + SLEEP_METRICS).get(key, 'total')
    if metric_type == 'promedio_inverted':
        return valor <= meta
    else:
        return valor >= meta


def calculate_score(data):
    """Calculate how many goals are met."""
    score = 0
    for key in ALL_METRIC_KEYS:
        if is_metric_met(key, data[key], metas[key]):
            score += 1
    return score


def score_css_class(score):
    total = len(ALL_METRIC_KEYS)
    if score >= total - 2: return "score-good"
    elif score >= total // 2: return "score-mid"
    else: return "score-bad"


def avg_vs_meta(key, valor, meta):
    """Get CSS class and label for average vs meta comparison."""
    metric_type = dict((m[0], m[3]) for m in FITNESS_METRICS + SLEEP_METRICS).get(key, 'total')
    if metric_type == 'promedio_inverted':
        # Lower is better
        pct = (meta / valor * 100) if valor > 0 else 100
    else:
        pct = (valor / meta * 100) if meta > 0 else 0

    if pct >= 100:
        return "vs-good", f"{pct:.0f}%"
    elif pct >= 70:
        return "vs-warn", f"~ {pct:.0f}%"
    else:
        return "vs-bad", f"{pct:.0f}%"


def value_color_class(key, valor, meta):
    metric_type = dict((m[0], m[3]) for m in FITNESS_METRICS + SLEEP_METRICS).get(key, 'total')
    if metric_type == 'promedio_inverted':
        pct = (meta / valor * 100) if valor > 0 else 100
    else:
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
    for key in ALL_METRIC_KEYS:
        total = sum(d[key] for d in all_data)
        if key == 'steps_avg':
            avg[key] = round(total / n)
        else:
            avg[key] = round(total / n, 1)
    return avg


def format_val(valor, unidad):
    if isinstance(valor, float):
        return f"{valor}{unidad}"
    elif not unidad and isinstance(valor, int) and valor >= 1000:
        return f"{valor:,}"
    return f"{valor}{unidad}"


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

    # ---- FITNESS HABITS ----
    st.markdown('<div class="section-label">// FITNESS HABITS</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        render_metric("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'], tipo='promedio')
        render_metric("STRENGTH TRAINING", data['strength'], metas['strength'])
        render_metric("HR ZONES 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")

    with col2:
        render_metric("ACTIVITIES / MES", data['activities'], metas['activities'])
        render_metric("HR ZONES 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")

    # ---- SLEEP HABITS ----
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">// SLEEP HABITS</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        render_metric("AVE SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", tipo='promedio')
        render_metric("RESTING HR", data['resting_hr'], metas['resting_hr'], " bpm", tipo='promedio_inverted')

    with col4:
        render_metric("RECOVERY SCORE", data['recovery_score'], metas['recovery_score'], "%", tipo='promedio')
        render_metric("SLEEP CONSISTENCY", data['sleep_consistency'], metas['sleep_consistency'], "%", tipo='promedio')

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ---- SUMMARY STATS ----
    fitness_ok = sum(
        is_metric_on_track(k, data[k], metas[k])
        for k, _, _, _ in FITNESS_METRICS
    )
    sleep_ok = sum(
        is_metric_on_track(k, data[k], metas[k])
        for k, _, _, _ in SLEEP_METRICS
    )
    total_ok = fitness_ok + sleep_ok
    total_metrics = len(ALL_METRIC_KEYS)

    steps_color = "#00ff87" if data['steps_avg'] >= metas['steps_avg'] else "#ff4444"
    habitos_color = "#00ff87" if total_ok >= total_metrics - 2 else "#ffd700" if total_ok >= total_metrics // 2 else "#ff4444"
    recovery_color = "#00ff87" if data['recovery_score'] >= metas['recovery_score'] else "#ffd700" if data['recovery_score'] >= metas['recovery_score'] * 0.7 else "#ff4444"

    st.markdown(f"""
    <div class="big-stats-row">
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:{steps_color}">{data['steps_avg']:,}</div>
            <div class="big-stat-label">STEPS DAILY AVG</div>
        </div>
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:{habitos_color}">{total_ok}/{total_metrics}</div>
            <div class="big-stat-label">HABITOS EN META</div>
        </div>
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:{recovery_color}">{data['recovery_score']}%</div>
            <div class="big-stat-label">RECOVERY</div>
        </div>
        <div class="big-stat-box">
            <div class="big-stat-val" style="color:#00d4ff">{progress_pct:.0f}%</div>
            <div class="big-stat-label">PROGRESO MES</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- MONTHLY STATS: PROJECTIONS ----
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">// PROYECCION FIN DE MES</div>', unsafe_allow_html=True)

    projection_rows = ""
    for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
        valor = data[key]
        meta = metas[key]

        if tipo in ('promedio', 'promedio_inverted'):
            # Averages don't project — current value is the projection
            projected = valor
        else:
            # Accumulative metrics: project based on daily rate
            daily_rate = valor / days_elapsed if days_elapsed > 0 else 0
            projected = round(daily_rate * days_in_month, 1)

        # Determine if projection meets goal
        if tipo == 'promedio_inverted':
            meets_goal = projected <= meta
            pct = (meta / projected * 100) if projected > 0 else 100
        else:
            meets_goal = projected >= meta
            pct = (projected / meta * 100) if meta > 0 else 0

        if pct >= 100:
            status_css = "vs-good"
            status_icon = "&#10003;"
        elif pct >= 70:
            status_css = "vs-warn"
            status_icon = "~"
        else:
            status_css = "vs-bad"
            status_icon = "&#10007;"

        proj_display = format_val(projected if isinstance(projected, float) else int(projected), unit)
        meta_display = format_val(meta, unit)

        projection_rows += f"""
        <div class="avg-metric-row">
            <span class="avg-metric-name">{label}</span>
            <span class="avg-metric-val" style="color:#fff">{proj_display}</span>
            <span style="font-family: Space Mono, monospace; font-size: 0.55rem; color: #555;">META {meta_display}</span>
            <span class="avg-metric-vs {status_css}">{status_icon} {pct:.0f}%</span>
        </div>
        """

    # Count projected goals met
    proj_met = 0
    for key, _, _, tipo in FITNESS_METRICS + SLEEP_METRICS:
        valor = data[key]
        meta = metas[key]
        if tipo in ('promedio', 'promedio_inverted'):
            projected = valor
        else:
            daily_rate = valor / days_elapsed if days_elapsed > 0 else 0
            projected = daily_rate * days_in_month
        if tipo == 'promedio_inverted':
            if projected <= meta:
                proj_met += 1
        else:
            if projected >= meta:
                proj_met += 1

    proj_score_class = score_css_class(proj_met)

    st.markdown(f"""
    <div class="avg-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div class="avg-title">// PROYECCION AL {days_in_month} DE {MESES_NOMBRES[current_month]}</div>
            <span class="month-score {proj_score_class}">{proj_met}/{total_metrics} METAS</span>
        </div>
        {projection_rows}
    </div>
    """, unsafe_allow_html=True)

    # ---- MONTH-OVER-MONTH COMPARISON ----
    if current_month > 1:
        prev_month = current_month - 1
        prev_year = current_year
        prev_data = get_monthly_data(prev_year, prev_month)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-label">// VS {MESES_NOMBRES[prev_month]} {prev_year}</div>', unsafe_allow_html=True)

        comparison_items = ""
        for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
            curr_val = data[key]
            prev_val = prev_data[key]

            if prev_val > 0:
                change_pct = ((curr_val - prev_val) / prev_val) * 100
            elif curr_val > 0:
                change_pct = 100
            else:
                change_pct = 0

            is_inverted = tipo == 'promedio_inverted'

            if change_pct > 2:
                arrow = "&#9650;"
                trend_css = "trend-down" if is_inverted else "trend-up"
            elif change_pct < -2:
                arrow = "&#9660;"
                trend_css = "trend-up" if is_inverted else "trend-down"
            else:
                arrow = "&#9644;"
                trend_css = "trend-flat"

            curr_display = format_val(curr_val, unit)
            prev_display = format_val(prev_val, unit)

            comparison_items += f"""
            <div class="avg-metric-row">
                <span class="avg-metric-name">{label}</span>
                <span class="avg-metric-val" style="color:#fff">{curr_display}</span>
                <span style="font-family: Space Mono, monospace; font-size: 0.55rem; color: #555;">{prev_display}</span>
                <span class="{trend_css}" style="font-family: Space Mono, monospace; font-size: 0.65rem;">{arrow} {change_pct:+.0f}%</span>
            </div>
            """

        st.markdown(f"""
        <div style="background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 10px; padding: 20px; margin-top: 8px;">
            <div style="font-family: Bebas Neue, sans-serif; font-size: 1.2rem; letter-spacing: 3px; color: #00d4ff; margin-bottom: 16px;">
                // {MESES_CORTOS[current_month]} VS {MESES_CORTOS[prev_month]}
            </div>
            {comparison_items}
        </div>
        """, unsafe_allow_html=True)

    # WHOOP data source indicator
    whoop_src = data.get('whoop_source', '?')
    src_color = '#00ff87' if whoop_src == 'LIVE' else '#ffd700' if 'CACHE' in whoop_src else '#ff4444'
    st.markdown(f"""
    <div style='font-family: Space Mono, monospace; font-size: 0.55rem; color: #444; text-align: right; margin-top: 20px; letter-spacing: 2px;'>
    WHOOP: <span style="color:{src_color}">{whoop_src}</span> · LAST UPDATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}
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
                d = get_monthly_data(current_year, mes)
                all_data.append(d)

        # ---- SECTION 1: OVERALL AVERAGE ----
        avg_data = calculate_averages(all_data)
        n = len(all_data)
        avg_score = sum(
            is_metric_met(key, avg_data[key], metas[key])
            for key in ALL_METRIC_KEYS
        )

        avg_score_class = score_css_class(avg_score)
        total_metrics = len(ALL_METRIC_KEYS)

        # Build avg rows - Fitness first, then Sleep
        rows_html = ""
        for section_metrics, section_label in [(FITNESS_METRICS, "FITNESS"), (SLEEP_METRICS, "SLEEP")]:
            rows_html += f"""
            <div style="font-family: Space Mono, monospace; font-size: 0.5rem; color: #00d4ff;
                        letter-spacing: 2px; padding: 12px 0 4px; text-transform: uppercase;">// {section_label}</div>
            """
            for key, label, unit, _ in section_metrics:
                valor = avg_data[key]
                meta = metas[key]
                css_class, pct_label = avg_vs_meta(key, valor, meta)
                val_display = format_val(valor, unit)
                meta_display = format_val(meta, unit)

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
                <span class="month-score {avg_score_class}">{avg_score}/{total_metrics}</span>
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
                <span class="month-score {s_class}">{score}/{total_metrics} METAS</span>
            </div>
            """, unsafe_allow_html=True)

            # Fitness Habits
            st.markdown('<div class="section-label" style="margin-top:4px;">// FITNESS</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                render_metric_hist("STEPS DAILY AVG", data['steps_avg'], metas['steps_avg'])
                render_metric_hist("STRENGTH TRAINING", data['strength'], metas['strength'])
                render_metric_hist("HR ZONES 1-3", data['hr_zone_1_3'], metas['hr_zone_1_3'], "h")
            with col2:
                render_metric_hist("ACTIVITIES / MES", data['activities'], metas['activities'])
                render_metric_hist("HR ZONES 4-5", data['hr_zone_4_5'], metas['hr_zone_4_5'], "h")

            # Sleep Habits
            st.markdown('<div class="section-label" style="margin-top:4px;">// SLEEP</div>', unsafe_allow_html=True)
            col3, col4 = st.columns(2)
            with col3:
                render_metric_hist("AVE SLEEP DURATION", data['sleep_hours_avg'], metas['sleep_hours_avg'], "h")
                render_metric_hist("RESTING HR", data['resting_hr'], metas['resting_hr'], " bpm", inverted=True)
            with col4:
                render_metric_hist("RECOVERY SCORE", data['recovery_score'], metas['recovery_score'], "%")
                render_metric_hist("SLEEP CONSISTENCY", data['sleep_consistency'], metas['sleep_consistency'], "%")

            # Trend vs previous month
            if i > 0:
                prev = all_data[i - 1]
                trends = []
                for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
                    curr_val = data[key]
                    prev_val = prev[key]
                    if prev_val > 0:
                        change_pct = ((curr_val - prev_val) / prev_val) * 100
                    elif curr_val > 0:
                        change_pct = 100
                    else:
                        change_pct = 0

                    # For inverted metrics, flip the arrow meaning
                    is_inverted = tipo == 'promedio_inverted'

                    if change_pct > 2:
                        arrow = "&#9650;"
                        css = "trend-down" if is_inverted else "trend-up"
                    elif change_pct < -2:
                        arrow = "&#9660;"
                        css = "trend-up" if is_inverted else "trend-down"
                    else:
                        arrow = "&#9644;"
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

            month_headers = "".join(
                f'<th>{MESES_CORTOS[m]}</th>' for m in meses_cerrados
            )
            header_html = f"<tr><th>METRICA</th>{month_headers}<th>PROMEDIO</th><th>META</th></tr>"

            body_html = ""
            for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
                meta = metas[key]

                cells = ""
                for d in all_data:
                    val = d[key]
                    color_class = value_color_class(key, val, meta)
                    val_str = format_val(val, unit)
                    cells += f'<td class="{color_class}">{val_str}</td>'

                avg_val = avg_data[key]
                avg_color = value_color_class(key, avg_val, meta)
                avg_str = format_val(avg_val, unit)
                meta_str = format_val(meta, unit)

                body_html += f"<tr><td>{label}</td>{cells}<td class='{avg_color}' style='font-weight:700;'>{avg_str}</td><td>{meta_str}</td></tr>"

            # Score row
            score_cells = ""
            for d in all_data:
                s = calculate_score(d)
                s_color = "td-good" if s >= total_metrics - 2 else "td-warn" if s >= total_metrics // 2 else "td-bad"
                score_cells += f'<td class="{s_color}" style="font-weight:700;">{s}/{total_metrics}</td>'

            avg_s_color = "td-good" if avg_score >= total_metrics - 2 else "td-warn" if avg_score >= total_metrics // 2 else "td-bad"
            body_html += f'<tr><td style="color:#00d4ff;">SCORE</td>{score_cells}<td class="{avg_s_color}" style="font-weight:700;">{avg_score}/{total_metrics}</td><td>{total_metrics}/{total_metrics}</td></tr>'

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

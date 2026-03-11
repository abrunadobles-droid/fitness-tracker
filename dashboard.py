"""
Fitness Tracker Dashboard - Pure Streamlit (no custom HTML)
Data from Garmin + WHOOP
"""

import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange
from auth import show_auth_page, show_logout_button, get_user_email
from goals_setup import get_user_goals, has_goals, show_goals_setup

st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide"
)

# ============ AUTH GATE ============
if not show_auth_page():
    st.stop()

user_email = get_user_email()

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

# Goals gate
if not has_goals():
    show_goals_setup(first_time=True)
    st.stop()

metas = get_user_goals()

# Metric definitions: (key, label, unit, type)
FITNESS_METRICS = [
    ('steps_avg', 'Steps Daily Avg', '', 'promedio'),
    ('activities', 'Activities / Mes', '', 'total'),
    ('strength', 'Strength Training', '', 'total'),
    ('hr_zone_1_3', 'HR Zones 1-3', 'h', 'total'),
    ('hr_zone_4_5', 'HR Zones 4-5', 'h', 'total'),
]

SLEEP_METRICS = [
    ('sleep_hours_avg', 'Sleep Duration', 'h', 'promedio'),
    ('recovery_score', 'Recovery Score', '%', 'promedio'),
    ('resting_hr', 'Resting HR', 'bpm', 'promedio_inverted'),
    ('sleep_consistency', 'Sleep Consistency', '%', 'promedio'),
]

ALL_METRIC_KEYS = [m[0] for m in FITNESS_METRICS + SLEEP_METRICS]

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

    # --- GARMIN ---
    try:
        from garmin_client import GarminClient

        garmin = GarminClient()
        garmin.login()

        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        is_current = (year == current_year and month == current_month)
        end_date = today if is_current else datetime(year, month, last_day)

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

    # --- WHOOP ---
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


# ============ HELPERS ============
def fmt(valor, unit):
    if isinstance(valor, float):
        return f"{valor} {unit}".strip()
    elif not unit and isinstance(valor, int) and valor >= 1000:
        return f"{valor:,}"
    return f"{valor} {unit}".strip()


def get_pct(key, valor, meta, tipo, for_current_month=False):
    """Get percentage of goal achieved."""
    if tipo == 'promedio_inverted':
        return min((meta / valor * 100) if valor > 0 else 100, 100)
    elif tipo == 'promedio':
        return min((valor / meta * 100) if meta > 0 else 0, 100)
    else:
        if for_current_month:
            esperado = (meta / days_in_month) * days_elapsed
            return min((valor / esperado * 100) if esperado > 0 else 0, 100)
        else:
            return min((valor / meta * 100) if meta > 0 else 0, 100)


def get_status(pct):
    if pct >= 100:
        return "🟢"
    elif pct >= 70:
        return "🟡"
    else:
        return "🔴"


def is_metric_met(key, valor, meta):
    tipo = dict((m[0], m[3]) for m in FITNESS_METRICS + SLEEP_METRICS).get(key, 'total')
    if tipo == 'promedio_inverted':
        return valor <= meta
    else:
        return valor >= meta


def calculate_score(data):
    return sum(is_metric_met(k, data[k], metas[k]) for k in ALL_METRIC_KEYS)


def calculate_averages(all_data):
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


def render_metric_row(label, valor, meta, unit, tipo, for_current_month=False):
    """Render a single metric as st.metric + st.progress in columns."""
    pct = get_pct(None, valor, meta, tipo, for_current_month)
    status = get_status(pct)

    inverted = tipo == 'promedio_inverted'
    meta_label = f"Max: {fmt(meta, unit)}" if inverted else f"Meta: {fmt(meta, unit)}"

    delta_val = None
    delta_color = "normal"
    if inverted:
        diff = meta - valor
        if diff >= 0:
            delta_val = f"{abs(diff):.1f} below max"
            delta_color = "normal"
        else:
            delta_val = f"{abs(diff):.1f} over max"
            delta_color = "inverse"
    else:
        if for_current_month and tipo == 'total':
            esperado = (meta / days_in_month) * days_elapsed
            diff = valor - esperado
            delta_val = f"{diff:+.0f} vs expected"
        else:
            diff = valor - meta
            if isinstance(diff, float):
                delta_val = f"{diff:+.1f} vs meta"
            else:
                delta_val = f"{diff:+.0f} vs meta"

    c1, c2 = st.columns([3, 1])
    with c1:
        st.metric(
            label=f"{status} {label}",
            value=fmt(valor, unit),
            delta=delta_val,
            delta_color=delta_color,
        )
    with c2:
        st.caption(meta_label)
        st.progress(min(pct / 100, 1.0))
        st.caption(f"{pct:.0f}%")


# ============ VIEW: METAS ============
if st.session_state.vista == "metas":
    show_goals_setup(first_time=False)

# ============ VIEW: MES ACTUAL ============
elif st.session_state.vista == "mes":

    month_name = MESES_CORTOS[current_month]

    st.title("FITNESS TRACKER")
    st.caption(f"{month_name} {current_year}  ·  DIA {days_elapsed}/{days_in_month}  ·  {progress_pct:.0f}% DEL MES")

    with st.spinner(''):
        data = get_monthly_data(current_year, current_month)

    # ---- SUMMARY ----
    total_ok = sum(
        1 for k, _, _, t in FITNESS_METRICS + SLEEP_METRICS
        if get_pct(k, data[k], metas[k], t, True) >= 100
    )
    total_metrics = len(ALL_METRIC_KEYS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Steps Avg", f"{data['steps_avg']:,}")
    c2.metric("Habitos en Meta", f"{total_ok}/{total_metrics}")
    c3.metric("Recovery", f"{data['recovery_score']}%")
    c4.metric("Progreso Mes", f"{progress_pct:.0f}%")

    st.divider()

    # ---- FITNESS HABITS ----
    st.subheader("// FITNESS HABITS")

    for key, label, unit, tipo in FITNESS_METRICS:
        render_metric_row(label, data[key], metas[key], unit, tipo, for_current_month=True)

    st.divider()

    # ---- SLEEP HABITS ----
    st.subheader("// SLEEP HABITS")

    for key, label, unit, tipo in SLEEP_METRICS:
        render_metric_row(label, data[key], metas[key], unit, tipo, for_current_month=True)

    st.divider()

    # ---- PROJECTIONS ----
    st.subheader("// PROYECCION FIN DE MES")

    proj_met = 0
    proj_rows = []
    for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
        valor = data[key]
        meta = metas[key]

        if tipo in ('promedio', 'promedio_inverted'):
            projected = valor
        else:
            daily_rate = valor / days_elapsed if days_elapsed > 0 else 0
            projected = round(daily_rate * days_in_month, 1)

        if tipo == 'promedio_inverted':
            meets = projected <= meta
            pct = (meta / projected * 100) if projected > 0 else 100
        else:
            meets = projected >= meta
            pct = (projected / meta * 100) if meta > 0 else 0

        if meets:
            proj_met += 1

        status = get_status(min(pct, 100))
        proj_rows.append({
            'Metrica': f"{status} {label}",
            'Proyeccion': fmt(projected if isinstance(projected, float) else int(projected), unit),
            'Meta': fmt(meta, unit),
            '%': f"{min(pct, 999):.0f}%",
        })

    st.caption(f"Proyeccion: {proj_met}/{total_metrics} metas cumplidas al {days_in_month} de {MESES_NOMBRES[current_month]}")
    st.dataframe(proj_rows, use_container_width=True, hide_index=True)

    # ---- VS PREVIOUS MONTH ----
    if current_month > 1:
        prev_month = current_month - 1
        prev_year = current_year
        prev_data = get_monthly_data(prev_year, prev_month)

        st.divider()
        st.subheader(f"// VS {MESES_NOMBRES[prev_month]} {prev_year}")

        comp_rows = []
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
                trend = "⬇️" if is_inverted else "⬆️"
            elif change_pct < -2:
                trend = "⬆️" if is_inverted else "⬇️"
            else:
                trend = "➡️"

            comp_rows.append({
                'Metrica': label,
                f'{MESES_CORTOS[current_month]}': fmt(curr_val, unit),
                f'{MESES_CORTOS[prev_month]}': fmt(prev_val, unit),
                'Cambio': f"{trend} {change_pct:+.0f}%",
            })

        st.dataframe(comp_rows, use_container_width=True, hide_index=True)

    # WHOOP source
    whoop_src = data.get('whoop_source', '?')
    st.caption(f"WHOOP: {whoop_src}  ·  Last update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ============ VIEW: HISTORICO ============
elif st.session_state.vista == "historico":

    st.title(f"HISTORICO {current_year}")
    st.caption("MESES CERRADOS")

    meses_cerrados = list(range(1, current_month))

    if not meses_cerrados:
        st.info("No hay meses cerrados aun.")
    else:
        all_data = []

        with st.spinner('Cargando historico...'):
            for mes in meses_cerrados:
                d = get_monthly_data(current_year, mes)
                all_data.append(d)

        # ---- OVERALL AVERAGE ----
        avg_data = calculate_averages(all_data)
        n = len(all_data)
        avg_score = sum(
            is_metric_met(key, avg_data[key], metas[key])
            for key in ALL_METRIC_KEYS
        )
        total_metrics = len(ALL_METRIC_KEYS)

        st.subheader(f"// PROMEDIO GENERAL ({n} {'MES' if n == 1 else 'MESES'})  —  {avg_score}/{total_metrics} metas")

        avg_rows = []
        for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
            valor = avg_data[key]
            meta = metas[key]
            pct = get_pct(key, valor, meta, tipo)
            status = get_status(pct)
            avg_rows.append({
                'Metrica': f"{status} {label}",
                'Promedio': fmt(valor, unit),
                'Meta': fmt(meta, unit),
                '%': f"{pct:.0f}%",
            })

        st.dataframe(avg_rows, use_container_width=True, hide_index=True)

        st.divider()

        # ---- METAS AJUSTADAS ----
        remaining = 12 - n
        if remaining > 0:
            st.subheader("// METAS AJUSTADAS")
            st.caption(f"Para cumplir tus metas anuales, necesitas estos objetivos mensuales en los {remaining} meses restantes.")

            adj_rows = []
            for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
                avg_val = avg_data[key]
                goal = metas[key]
                is_inverted = tipo == 'promedio_inverted'

                adjusted = (goal * 12 - avg_val * n) / remaining
                adjusted = max(adjusted, 0)

                if is_inverted:
                    diff_pct = ((goal - adjusted) / goal * 100) if goal > 0 else 0
                    diff_pct = -diff_pct
                else:
                    diff_pct = ((adjusted - goal) / goal * 100) if goal > 0 else 0

                adjusted_r = round(adjusted, 1)

                if diff_pct <= 0:
                    status = "🟢 ON TRACK"
                elif diff_pct <= 30:
                    status = f"🟡 +{diff_pct:.0f}%"
                else:
                    status = f"🔴 +{diff_pct:.0f}%"

                adj_rows.append({
                    'Metrica': label,
                    'Meta Original': fmt(goal, unit),
                    'Meta Ajustada': fmt(adjusted_r, unit),
                    'Estado': status,
                })

            st.dataframe(adj_rows, use_container_width=True, hide_index=True)
            st.divider()

        # ---- PER-MONTH DETAILS ----
        st.subheader("// DETALLE POR MES")

        for i, (mes, data) in enumerate(zip(meses_cerrados, all_data)):
            score = calculate_score(data)

            with st.expander(f"{MESES_NOMBRES[mes]} {current_year}  —  {score}/{total_metrics} metas"):

                st.caption("FITNESS HABITS")
                for key, label, unit, tipo in FITNESS_METRICS:
                    pct = get_pct(key, data[key], metas[key], tipo)
                    status = get_status(pct)
                    st.text(f"{status} {label}: {fmt(data[key], unit)}  (meta: {fmt(metas[key], unit)}, {pct:.0f}%)")

                st.caption("SLEEP HABITS")
                for key, label, unit, tipo in SLEEP_METRICS:
                    pct = get_pct(key, data[key], metas[key], tipo)
                    status = get_status(pct)
                    st.text(f"{status} {label}: {fmt(data[key], unit)}  (meta: {fmt(metas[key], unit)}, {pct:.0f}%)")

                # Trend vs previous month
                if i > 0:
                    prev = all_data[i - 1]
                    st.caption(f"VS {MESES_NOMBRES[meses_cerrados[i-1]]}")
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

                        is_inv = tipo == 'promedio_inverted'
                        if change_pct > 2:
                            arrow = "⬇️" if is_inv else "⬆️"
                        elif change_pct < -2:
                            arrow = "⬆️" if is_inv else "⬇️"
                        else:
                            arrow = "➡️"

                        short = label.split('/')[0].strip()[:14]
                        trends.append(f"{arrow} {short} {change_pct:+.0f}%")

                    st.text("  |  ".join(trends))

        st.divider()

        # ---- COMPARISON TABLE ----
        if len(all_data) >= 1:
            st.subheader("// COMPARATIVA MENSUAL")

            comp_data = []
            for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
                row = {'Metrica': label}
                for mes_idx, d in zip(meses_cerrados, all_data):
                    row[MESES_CORTOS[mes_idx]] = fmt(d[key], unit)
                row['Promedio'] = fmt(avg_data[key], unit)
                row['Meta'] = fmt(metas[key], unit)
                comp_data.append(row)

            # Score row
            score_row = {'Metrica': 'SCORE'}
            for mes_idx, d in zip(meses_cerrados, all_data):
                s = calculate_score(d)
                score_row[MESES_CORTOS[mes_idx]] = f"{s}/{total_metrics}"
            score_row['Promedio'] = f"{avg_score}/{total_metrics}"
            score_row['Meta'] = f"{total_metrics}/{total_metrics}"
            comp_data.append(score_row)

            st.dataframe(comp_data, use_container_width=True, hide_index=True)

        st.caption(f"Last update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

"""
Vista: Mes Actual
"""
import streamlit as st
from datetime import datetime
from constants import MESES_NOMBRES, MESES_CORTOS, FITNESS_METRICS, SLEEP_METRICS, ALL_METRIC_KEYS
from helpers import fmt, get_pct, get_status, get_status_class, render_metric_row
from data_loader import get_monthly_data


def show(data, metas, days_elapsed, days_in_month, progress_pct, current_month, current_year):
    # ---- HEADER ----
    st.markdown('<div class="dn-header">FITNESS TRACKER</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dn-subtitle">{MESES_CORTOS[current_month]} {current_year} &middot; '
        f'DIA {days_elapsed}/{days_in_month} &middot; {progress_pct:.0f}% DEL MES</div>',
        unsafe_allow_html=True
    )

    # ---- SUMMARY CARDS ----
    total_ok = sum(
        1 for k, _, _, t in FITNESS_METRICS + SLEEP_METRICS
        if get_pct(k, data[k], metas[k], t, days_elapsed, days_in_month, True) >= 100
    )
    total_metrics = len(ALL_METRIC_KEYS)

    steps_display = f"{data['steps_avg']:,}" if data['steps_avg'] >= 1000 else str(data['steps_avg'])

    c1, c2, c3, c4 = st.columns(4)
    for col, (val, lbl) in zip([c1, c2, c3, c4], [
        (steps_display, "STEPS AVG"),
        (f"{total_ok} / {total_metrics}", "METAS OK"),
        (f"{data['recovery_score']}%", "RECOVERY"),
        (f"{progress_pct:.0f}%", "PROGRESO MES"),
    ]):
        col.markdown(f'''<div class="dn-card">
            <div class="value">{val}</div>
            <div class="label">{lbl}</div>
        </div>''', unsafe_allow_html=True)

    # ---- FITNESS HABITS ----
    st.markdown('<div class="dn-section">// FITNESS HABITS</div>', unsafe_allow_html=True)
    for key, label, unit, tipo in FITNESS_METRICS:
        render_metric_row(label, data[key], metas[key], unit, tipo, days_elapsed, days_in_month, for_current_month=True)

    # ---- SLEEP HABITS ----
    st.markdown('<div class="dn-section">// SLEEP HABITS</div>', unsafe_allow_html=True)
    for key, label, unit, tipo in SLEEP_METRICS:
        render_metric_row(label, data[key], metas[key], unit, tipo, days_elapsed, days_in_month, for_current_month=True)

    # ---- VS MES ANTERIOR ----
    if current_month > 1:
        prev_month = current_month - 1
        prev_data = get_monthly_data(current_year, prev_month)

        st.markdown(
            f'<div class="dn-section">// VS {MESES_NOMBRES[prev_month]} {current_year}</div>',
            unsafe_allow_html=True
        )

        # Build HTML table
        rows_html = ""
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

            rows_html += f"""<tr>
                <td>{label}</td>
                <td class="val">{fmt(curr_val, unit)}</td>
                <td class="val">{fmt(prev_val, unit)}</td>
                <td>{trend} {change_pct:+.0f}%</td>
            </tr>"""

        st.markdown(f'''<table class="dn-table">
            <thead><tr>
                <th>Metrica</th>
                <th>{MESES_CORTOS[current_month]}</th>
                <th>{MESES_CORTOS[prev_month]}</th>
                <th>Cambio</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>''', unsafe_allow_html=True)

    whoop_src = data.get('whoop_source', '?')
    garmin_src = data.get('garmin_source', '?')
    st.markdown(
        f'<div class="dn-footer">GARMIN: {garmin_src} &middot; WHOOP: {whoop_src} &middot; '
        f'Last update: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',
        unsafe_allow_html=True
    )

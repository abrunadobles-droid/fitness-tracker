"""
Vista: Mes Actual
"""
import streamlit as st
from datetime import datetime
from constants import MESES_NOMBRES, MESES_CORTOS, FITNESS_METRICS, SLEEP_METRICS, ALL_METRIC_KEYS
from helpers import fmt, get_pct, get_status, render_metric_row, is_metric_met
from data_loader import get_monthly_data


def show(data, metas, days_elapsed, days_in_month, progress_pct, current_month, current_year):
    st.title("FITNESS TRACKER")
    st.caption(
        f"{MESES_CORTOS[current_month]} {current_year}  ·  "
        f"DIA {days_elapsed}/{days_in_month}  ·  {progress_pct:.0f}% DEL MES"
    )

    # ---- SUMMARY ----
    total_ok = sum(
        1 for k, _, _, t in FITNESS_METRICS + SLEEP_METRICS
        if get_pct(k, data[k], metas[k], t, days_elapsed, days_in_month, True) >= 100
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
        render_metric_row(label, data[key], metas[key], unit, tipo, days_elapsed, days_in_month, for_current_month=True)

    st.divider()

    # ---- SLEEP HABITS ----
    st.subheader("// SLEEP HABITS")
    for key, label, unit, tipo in SLEEP_METRICS:
        render_metric_row(label, data[key], metas[key], unit, tipo, days_elapsed, days_in_month, for_current_month=True)

    st.divider()

    # ---- PROYECCION FIN DE MES ----
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

    st.caption(
        f"Proyeccion: {proj_met}/{total_metrics} metas cumplidas "
        f"al {days_in_month} de {MESES_NOMBRES[current_month]}"
    )
    st.dataframe(proj_rows, use_container_width=True, hide_index=True)

    # ---- VS MES ANTERIOR ----
    if current_month > 1:
        prev_month = current_month - 1
        prev_data = get_monthly_data(current_year, prev_month)

        st.divider()
        st.subheader(f"// VS {MESES_NOMBRES[prev_month]} {current_year}")

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

    whoop_src = data.get('whoop_source', '?')
    st.caption(f"WHOOP: {whoop_src}  ·  Last update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

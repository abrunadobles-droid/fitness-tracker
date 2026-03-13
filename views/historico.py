"""
Vista: Histórico anual
"""
import streamlit as st
from datetime import datetime
from constants import MESES_NOMBRES, MESES_CORTOS, FITNESS_METRICS, SLEEP_METRICS, ALL_METRIC_KEYS
from helpers import fmt, get_pct, get_status, is_metric_met, calculate_score, calculate_averages
from data_loader import get_monthly_data


def show(metas, current_month, current_year):
    st.title(f"HISTORICO {current_year}")
    st.caption("MESES CERRADOS")

    meses_cerrados = list(range(1, current_month))
    total_metrics = len(ALL_METRIC_KEYS)

    if not meses_cerrados:
        st.info("No hay meses cerrados aun.")
        return

    all_data = []
    with st.spinner('Cargando historico...'):
        for mes in meses_cerrados:
            all_data.append(get_monthly_data(current_year, mes))

    avg_data = calculate_averages(all_data)
    n = len(all_data)
    avg_score = sum(is_metric_met(key, avg_data[key], metas[key]) for key in ALL_METRIC_KEYS)

    # ---- PROMEDIO GENERAL ----
    st.subheader(f"PROMEDIO GENERAL ({n} {'MES' if n == 1 else 'MESES'})  —  {avg_score}/{total_metrics} metas")

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
        st.subheader("METAS AJUSTADAS")
        st.caption(
            f"Para cumplir tus metas anuales, necesitas estos objetivos "
            f"mensuales en los {remaining} meses restantes."
        )

        adj_rows = []
        for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
            avg_val = avg_data[key]
            goal = metas[key]
            is_inverted = tipo == 'promedio_inverted'

            adjusted = (goal * 12 - avg_val * n) / remaining
            adjusted = max(adjusted, 0)
            adjusted_r = round(adjusted, 1)

            if is_inverted:
                diff_pct = -((goal - adjusted) / goal * 100) if goal > 0 else 0
            else:
                diff_pct = ((adjusted - goal) / goal * 100) if goal > 0 else 0

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

    # ---- DETALLE POR MES ----
    st.subheader("DETALLE POR MES")

    for i, (mes, data) in enumerate(zip(meses_cerrados, all_data)):
        score = calculate_score(data, metas)
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

    # ---- COMPARATIVA MENSUAL ----
    if len(all_data) >= 1:
        st.subheader("COMPARATIVA MENSUAL")

        comp_data = []
        for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
            row = {'Metrica': label}
            for mes_idx, d in zip(meses_cerrados, all_data):
                row[MESES_CORTOS[mes_idx]] = fmt(d[key], unit)
            row['Promedio'] = fmt(avg_data[key], unit)
            row['Meta'] = fmt(metas[key], unit)
            comp_data.append(row)

        score_row = {'Metrica': 'SCORE'}
        for mes_idx, d in zip(meses_cerrados, all_data):
            s = calculate_score(d, metas)
            score_row[MESES_CORTOS[mes_idx]] = f"{s}/{total_metrics}"
        score_row['Promedio'] = f"{avg_score}/{total_metrics}"
        score_row['Meta'] = f"{total_metrics}/{total_metrics}"
        comp_data.append(score_row)

        st.dataframe(comp_data, use_container_width=True, hide_index=True)

    st.caption(f"Last update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

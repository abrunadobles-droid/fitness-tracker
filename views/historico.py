"""
Vista: Histórico anual
"""
import streamlit as st
from datetime import datetime
from constants import MESES_NOMBRES, MESES_CORTOS, FITNESS_METRICS, SLEEP_METRICS, ALL_METRIC_KEYS
from helpers import fmt, get_pct, get_status, get_status_class, is_metric_met, calculate_score, calculate_averages
from data_loader import get_monthly_data
from pdf_export import generate_historico_pdf


def _html_table(headers, rows):
    """Build an HTML table with dn-table styling."""
    ths = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = ""
        for i, cell in enumerate(row):
            cls = ' class="val"' if i > 0 else ""
            tds += f"<td{cls}>{cell}</td>"
        trs += f"<tr>{tds}</tr>"
    return f'''<table class="dn-table">
        <thead><tr>{ths}</tr></thead>
        <tbody>{trs}</tbody>
    </table>'''


def show(metas, current_month, current_year):
    st.markdown('<div class="dn-header">HISTORICO</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dn-subtitle">{current_year} &middot; MESES CERRADOS</div>',
        unsafe_allow_html=True
    )

    meses_cerrados = list(range(1, current_month))
    historico_metrics = FITNESS_METRICS + SLEEP_METRICS
    historico_keys = [m[0] for m in historico_metrics]
    total_metrics = len(historico_metrics)

    if not meses_cerrados:
        st.info("No hay meses cerrados aun.")
        return

    all_data = []
    with st.spinner('Cargando historico...'):
        for mes in meses_cerrados:
            all_data.append(get_monthly_data(current_year, mes))

    avg_data = calculate_averages(all_data)
    n = len(all_data)
    avg_score = sum(is_metric_met(key, avg_data[key], metas[key]) for key in historico_keys)

    # ---- EXPORTAR PDF ----
    pdf_bytes = generate_historico_pdf(all_data, metas, meses_cerrados, current_year)
    st.download_button(
        "EXPORTAR PDF",
        data=pdf_bytes,
        file_name=f"fitness_tracker_{current_year}.pdf",
        mime="application/pdf",
    )

    # ---- PROMEDIO GENERAL ----
    st.markdown(
        f'<div class="dn-section">// PROMEDIO GENERAL ({n} {"MES" if n == 1 else "MESES"}) '
        f'&mdash; {avg_score}/{total_metrics} metas</div>',
        unsafe_allow_html=True
    )

    headers = ["Metrica", "Promedio", "Meta", "%"]
    rows = []
    for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
        valor = avg_data[key]
        meta = metas[key]
        pct = get_pct(key, valor, meta, tipo)
        status_cls = get_status_class(pct)
        dot = f'<span class="dn-status {status_cls}" style="vertical-align:middle;"></span>'
        rows.append([
            f"{dot} {label}",
            fmt(valor, unit),
            fmt(meta, unit),
            f"{pct:.0f}%",
        ])

    st.markdown(_html_table(headers, rows), unsafe_allow_html=True)

    # ---- METAS AJUSTADAS ----
    remaining = 12 - n
    if remaining > 0:
        st.markdown(
            '<div class="dn-section">// METAS AJUSTADAS</div>',
            unsafe_allow_html=True
        )
        st.caption(
            f"Para cumplir tus metas anuales, necesitas estos objetivos "
            f"mensuales en los {remaining} meses restantes."
        )

        headers = ["Metrica", "Meta Original", "Meta Ajustada", "Estado"]
        rows = []
        for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
            avg_val = avg_data[key]
            goal = metas[key]
            is_inverted = tipo == 'promedio_inverted'

            adjusted = (goal * 12 - avg_val * n) / remaining
            adjusted = max(adjusted, 0)
            adjusted_r = round(adjusted, 1)

            if is_inverted:
                # For inverted metrics (lower is better): adjusted > goal means ON TRACK
                # (you've earned headroom — can afford worse values going forward)
                diff_pct = ((goal - adjusted) / goal * 100) if goal > 0 else 0
            else:
                diff_pct = ((adjusted - goal) / goal * 100) if goal > 0 else 0

            if diff_pct <= 0:
                status = '<span class="dn-status green" style="vertical-align:middle;"></span> ON TRACK'
            elif diff_pct <= 30:
                status = f'<span class="dn-status yellow" style="vertical-align:middle;"></span> +{diff_pct:.0f}%'
            else:
                status = f'<span class="dn-status red" style="vertical-align:middle;"></span> +{diff_pct:.0f}%'

            rows.append([label, fmt(goal, unit), fmt(adjusted_r, unit), status])

        st.markdown(_html_table(headers, rows), unsafe_allow_html=True)

    # ---- DETALLE POR MES ----
    st.markdown('<div class="dn-section">// DETALLE POR MES</div>', unsafe_allow_html=True)

    for i, (mes, data) in enumerate(zip(meses_cerrados, all_data)):
        score = sum(is_metric_met(k, data[k], metas[k]) for k in historico_keys if k in data and k in metas)
        with st.expander(f"{MESES_NOMBRES[mes]} {current_year}  —  {score}/{total_metrics} metas"):
            rows = []
            for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
                pct = get_pct(key, data[key], metas[key], tipo)
                status_cls = get_status_class(pct)
                dot = f'<span class="dn-status {status_cls}" style="vertical-align:middle;"></span>'
                rows.append([f"{dot} {label}", fmt(data[key], unit), fmt(metas[key], unit), f"{pct:.0f}%"])

            st.markdown(
                _html_table(["Metrica", "Valor", "Meta", "%"], rows),
                unsafe_allow_html=True
            )

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
                    is_inv = tipo == 'promedio_inverted'
                    if change_pct > 2:
                        arrow = "⬇️" if is_inv else "⬆️"
                    elif change_pct < -2:
                        arrow = "⬆️" if is_inv else "⬇️"
                    else:
                        arrow = "➡️"
                    short = label.split('/')[0].strip()[:14]
                    trends.append(f"{arrow} {short} {change_pct:+.0f}%")
                st.caption("  |  ".join(trends))

    # ---- COMPARATIVA MENSUAL ----
    if len(all_data) >= 1:
        st.markdown('<div class="dn-section">// COMPARATIVA MENSUAL</div>', unsafe_allow_html=True)

        month_headers = [MESES_CORTOS[m] for m in meses_cerrados]
        headers = ["Metrica"] + month_headers + ["Promedio", "Meta"]

        rows = []
        for key, label, unit, tipo in FITNESS_METRICS + SLEEP_METRICS:
            row = [label]
            for d in all_data:
                row.append(fmt(d[key], unit))
            row.append(fmt(avg_data[key], unit))
            row.append(fmt(metas[key], unit))
            rows.append(row)

        # Score row
        score_row = ["<strong>SCORE</strong>"]
        for d in all_data:
            s = sum(is_metric_met(k, d[k], metas[k]) for k in historico_keys if k in d and k in metas)
            score_row.append(f"{s}/{total_metrics}")
        score_row.append(f"{avg_score}/{total_metrics}")
        score_row.append(f"{total_metrics}/{total_metrics}")
        rows.append(score_row)

        st.markdown(_html_table(headers, rows), unsafe_allow_html=True)

    st.markdown(
        f'<div class="dn-footer">Last update: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',
        unsafe_allow_html=True
    )

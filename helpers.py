"""
Funciones auxiliares: formato, cálculo de porcentajes, métricas.
"""
import streamlit as st
from constants import FITNESS_METRICS, SLEEP_METRICS, ALL_METRIC_KEYS

_TIPO_MAP = {m[0]: m[3] for m in FITNESS_METRICS + SLEEP_METRICS}


def fmt(valor, unit):
    if isinstance(valor, float):
        return f"{valor} {unit}".strip()
    elif not unit and isinstance(valor, int) and valor >= 1000:
        return f"{valor:,}"
    return f"{valor} {unit}".strip()


def get_pct(key, valor, meta, tipo, days_elapsed=1, days_in_month=30, for_current_month=False):
    """Devuelve el porcentaje de cumplimiento de una meta (0-100)."""
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
    return "🔴"


def is_metric_met(key, valor, meta):
    tipo = _TIPO_MAP.get(key, 'total')
    if tipo == 'promedio_inverted':
        return valor <= meta
    return valor >= meta


def calculate_score(data, metas):
    return sum(is_metric_met(k, data[k], metas[k]) for k in ALL_METRIC_KEYS if k in data and k in metas)


def calculate_averages(all_data):
    n = len(all_data)
    if n == 0:
        return {}
    avg = {}
    for key in ALL_METRIC_KEYS:
        total = sum(d.get(key, 0) for d in all_data)
        avg[key] = round(total / n) if key == 'steps_avg' else round(total / n, 1)
    return avg


def render_metric_row(label, valor, meta, unit, tipo, days_elapsed=1, days_in_month=30, for_current_month=False):
    """Renderiza una métrica con st.metric + barra de progreso."""
    pct = get_pct(None, valor, meta, tipo, days_elapsed, days_in_month, for_current_month)
    status = get_status(pct)
    inverted = tipo == 'promedio_inverted'
    meta_label = f"Max: {fmt(meta, unit)}" if inverted else f"Meta: {fmt(meta, unit)}"

    delta_val = None
    delta_color = "normal"
    if inverted:
        diff = meta - valor
        if diff >= 0:
            delta_val = f"{abs(diff):.1f} below max"
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
            delta_val = f"{diff:+.1f} vs meta" if isinstance(diff, float) else f"{diff:+.0f} vs meta"

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

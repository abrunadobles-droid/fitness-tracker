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


def get_status_class(pct):
    """Returns CSS class for status dot."""
    if pct >= 100:
        return "green"
    elif pct >= 70:
        return "yellow"
    return "red"


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
    """Renderiza una métrica como fila custom HTML (Dark Neon style)."""
    pct = get_pct(None, valor, meta, tipo, days_elapsed, days_in_month, for_current_month)
    status_cls = get_status_class(pct)

    if isinstance(valor, float):
        display_val = f"{valor:.1f} {unit}".strip()
    elif isinstance(valor, int) and valor >= 1000:
        display_val = f"{valor:,}"
    else:
        display_val = f"{valor} {unit}".strip()

    bar_w = min(pct, 100)

    st.markdown(f'''<div class="dn-metric">
        <div style="display:flex;align-items:center;">
            <span class="dn-status {status_cls}"></span>
            <span class="name">{label}</span>
        </div>
        <div style="display:flex;align-items:center;">
            <span class="val">{display_val}</span>
            <div class="dn-bar-bg"><div class="dn-bar-fill" style="width:{bar_w}%"></div></div>
            <span class="dn-pct">{min(pct, 100):.0f}%</span>
        </div>
    </div>''', unsafe_allow_html=True)

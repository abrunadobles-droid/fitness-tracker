"""
Configuracion de metas personalizadas - almacenamiento local (JSON)
"""
import json
import streamlit as st
from pathlib import Path

GOALS_FILE = Path(__file__).parent / "goals.json"

# Metas por defecto
DEFAULT_GOALS = {
    'steps_avg': 10000,
    'activities': 28,
    'strength': 10,
    'sleep_hours_avg': 7.5,
    'hr_zone_1_3': 19.3,
    'hr_zone_4_5': 2.9,
    'recovery_score': 50.0,
    'resting_hr': 55.0,
    'sleep_consistency': 80.0,
    'meditation_sessions': 20,
    'meditation_minutes': 240,
}


def _load_goals():
    """Lee metas del archivo local."""
    if GOALS_FILE.exists():
        with open(GOALS_FILE) as f:
            return json.load(f)
    return None


def _save_goals(goals):
    """Guarda metas en archivo local."""
    with open(GOALS_FILE, "w") as f:
        json.dump(goals, f, indent=2)


def get_user_goals():
    """Obtiene las metas. Prioridad: session_state > goals.json > defaults."""
    # Session state persists within a Streamlit Cloud session
    if 'user_goals' in st.session_state:
        return dict(st.session_state.user_goals)

    saved = _load_goals()
    if saved:
        result = dict(DEFAULT_GOALS)
        result.update(saved)
        # Asegurar floats
        for key in ('sleep_hours_avg', 'hr_zone_1_3', 'hr_zone_4_5',
                     'recovery_score', 'resting_hr', 'sleep_consistency'):
            result[key] = float(result[key])
        return result
    return dict(DEFAULT_GOALS)


def has_goals():
    """Verifica si ya hay metas configuradas.
    Siempre retorna True para usar defaults cuando no hay archivo."""
    return True


def show_goals_setup(first_time=True):
    """Muestra formulario para configurar metas."""
    if first_time and has_goals():
        return True

    st.markdown("""
    <style>
    .goals-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        letter-spacing: 4px !important;
        background: linear-gradient(135deg, #c4b5fd, #7c3aed, #06b6d4) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center;
        margin-bottom: 8px;
    }
    .goals-subtitle {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #cbd5e1;
        text-align: center;
        letter-spacing: 1px;
        margin-bottom: 24px;
        line-height: 1.6;
    }
    .goal-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-gradient"></div>', unsafe_allow_html=True)

    if first_time:
        st.markdown('<div class="goals-title">CONFIGURA TUS METAS</div>', unsafe_allow_html=True)
        st.markdown('<div class="goals-subtitle">Define tus objetivos mensuales de fitness y sueno.<br>Puedes cambiarlos en cualquier momento.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="goals-title">EDITAR METAS</div>', unsafe_allow_html=True)

    current = get_user_goals()

    # ---- FITNESS HABITS ----
    st.markdown('<div class="section-label">// FITNESS HABITS</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        steps = st.number_input(
            "Steps diarios promedio",
            min_value=1000, max_value=50000, value=current['steps_avg'], step=1000,
            help="Promedio de pasos diarios que quieres alcanzar"
        )
        strength = st.number_input(
            "Sesiones de fuerza / mes",
            min_value=0, max_value=31, value=current['strength'], step=1,
            help="Dias de entrenamiento de fuerza al mes"
        )
        hr_13 = st.number_input(
            "Horas en HR Zones 1-3 / mes",
            min_value=0.0, max_value=100.0, value=current['hr_zone_1_3'], step=0.5,
            help="Horas totales en zonas de baja-media intensidad (WHOOP)"
        )

    with col2:
        activities = st.number_input(
            "Dias de ejercicio / mes",
            min_value=0, max_value=31, value=current['activities'], step=1,
            help="Total de actividades fisicas al mes"
        )
        hr_45 = st.number_input(
            "Horas en HR Zones 4-5 / mes",
            min_value=0.0, max_value=50.0, value=current['hr_zone_4_5'], step=0.5,
            help="Horas totales en zonas de alta intensidad (WHOOP)"
        )

    # ---- SLEEP HABITS ----
    st.markdown('<div class="section-label">// SLEEP HABITS</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        sleep_hours = st.number_input(
            "Horas de sueno promedio",
            min_value=4.0, max_value=12.0, value=current['sleep_hours_avg'], step=0.5,
            help="Promedio de horas de sueno por noche (WHOOP)"
        )
        resting_hr = st.number_input(
            "Resting HR maximo (bpm)",
            min_value=30.0, max_value=100.0, value=current['resting_hr'], step=1.0,
            help="Frecuencia cardiaca en reposo objetivo (menor es mejor)"
        )

    with col4:
        recovery = st.number_input(
            "Recovery Score promedio (%)",
            min_value=10.0, max_value=100.0, value=current['recovery_score'], step=5.0,
            help="Score de recuperacion promedio mensual (WHOOP)"
        )
        sleep_consistency = st.number_input(
            "Sleep Consistency promedio (%)",
            min_value=10.0, max_value=100.0, value=current['sleep_consistency'], step=5.0,
            help="Consistencia de sueno promedio mensual (WHOOP)"
        )

    # ---- MIND HABITS (MBAT - Amishi Jha) ----
    st.markdown('<div class="section-label">// MIND HABITS</div>', unsafe_allow_html=True)

    col5, col6 = st.columns(2)

    with col5:
        meditation_sessions = st.number_input(
            "Sesiones de meditacion / mes",
            min_value=0, max_value=31, value=int(current.get('meditation_sessions', 20)), step=1,
            help="Total de sesiones MBAT (12 min) al mes"
        )

    with col6:
        meditation_minutes = st.number_input(
            "Minutos de meditacion / mes",
            min_value=0, max_value=1500, value=int(current.get('meditation_minutes', 240)), step=12,
            help="Minutos totales de meditacion al mes (12 min x sesiones)"
        )

    if st.button("GUARDAR METAS", use_container_width=True):
        goals_data = {
            "steps_avg": steps,
            "activities": activities,
            "strength": strength,
            "sleep_hours_avg": sleep_hours,
            "hr_zone_1_3": hr_13,
            "hr_zone_4_5": hr_45,
            "recovery_score": recovery,
            "resting_hr": resting_hr,
            "sleep_consistency": sleep_consistency,
            "meditation_sessions": meditation_sessions,
            "meditation_minutes": meditation_minutes,
        }

        try:
            _save_goals(goals_data)
            st.session_state.user_goals = goals_data
            st.cache_data.clear()
            st.success("Metas guardadas!")
            st.rerun()
        except Exception as e:
            st.error(f"Error guardando metas: {str(e)}")

    return False

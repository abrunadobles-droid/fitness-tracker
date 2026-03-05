"""
Configuracion de metas personalizadas por usuario
"""
import streamlit as st
from auth import get_supabase, get_user_id

# Metas por defecto
DEFAULT_GOALS = {
    'steps_avg': 10000,
    'activities': 28,
    'strength': 10,
    'sleep_75_days': 15,
    'sleep_hours_avg': 7.5,
    'hr_zone_1_3': 19.3,
    'hr_zone_4_5': 2.9,
}


def get_user_goals():
    """Obtiene las metas del usuario. Si no tiene, retorna las default."""
    supabase = get_supabase()
    user_id = get_user_id()

    result = supabase.table("user_goals").select("*").eq(
        "user_id", user_id
    ).execute()

    if result.data:
        row = result.data[0]
        return {
            'steps_avg': row.get('steps_avg', DEFAULT_GOALS['steps_avg']),
            'activities': row.get('activities', DEFAULT_GOALS['activities']),
            'strength': row.get('strength', DEFAULT_GOALS['strength']),
            'days_before_930': row.get('sleep_75_days', DEFAULT_GOALS['sleep_75_days']),
            'sleep_hours_avg': float(row.get('sleep_hours_avg', DEFAULT_GOALS['sleep_hours_avg'])),
            'hr_zone_1_3': float(row.get('hr_zone_1_3', DEFAULT_GOALS['hr_zone_1_3'])),
            'hr_zone_4_5': float(row.get('hr_zone_4_5', DEFAULT_GOALS['hr_zone_4_5'])),
        }

    return {
        'steps_avg': DEFAULT_GOALS['steps_avg'],
        'activities': DEFAULT_GOALS['activities'],
        'strength': DEFAULT_GOALS['strength'],
        'days_before_930': DEFAULT_GOALS['sleep_75_days'],
        'sleep_hours_avg': DEFAULT_GOALS['sleep_hours_avg'],
        'hr_zone_1_3': DEFAULT_GOALS['hr_zone_1_3'],
        'hr_zone_4_5': DEFAULT_GOALS['hr_zone_4_5'],
    }


def has_goals():
    """Verifica si el usuario ya configuro sus metas."""
    supabase = get_supabase()
    user_id = get_user_id()

    result = supabase.table("user_goals").select("id").eq(
        "user_id", user_id
    ).execute()

    return bool(result.data)


def show_goals_setup(first_time=True):
    """Muestra formulario para configurar metas. Retorna True si ya tiene metas."""
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
        color: #94a3b8;
        text-align: center;
        letter-spacing: 1px;
        margin-bottom: 24px;
        line-height: 1.6;
    }
    .goal-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-gradient"></div>', unsafe_allow_html=True)

    if first_time:
        st.markdown('<div class="goals-title">CONFIGURA TUS METAS</div>', unsafe_allow_html=True)
        st.markdown('<div class="goals-subtitle">Define tus objetivos mensuales de fitness.<br>Puedes cambiarlos en cualquier momento.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="goals-title">EDITAR METAS</div>', unsafe_allow_html=True)

    # Cargar metas actuales (o defaults)
    current = get_user_goals()

    st.markdown('<div class="section-label">// ACTIVIDAD</div>', unsafe_allow_html=True)

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

    with col2:
        activities = st.number_input(
            "Dias de ejercicio / mes",
            min_value=0, max_value=31, value=current['activities'], step=1,
            help="Total de actividades fisicas al mes"
        )

    st.markdown('<div class="section-label">// SUEÑO</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        sleep_hours = st.number_input(
            "Horas de sueño promedio",
            min_value=4.0, max_value=12.0, value=current['sleep_hours_avg'], step=0.5,
            help="Promedio de horas de sueño por noche"
        )

    with col4:
        sleep_days = st.number_input(
            "Dias con 7.5+ hrs sueño / mes",
            min_value=0, max_value=31, value=current['days_before_930'], step=1,
            help="Dias al mes donde duermes 7.5 horas o mas"
        )

    st.markdown('<div class="section-label">// HEART RATE ZONES</div>', unsafe_allow_html=True)

    col5, col6 = st.columns(2)

    with col5:
        hr_13 = st.number_input(
            "Horas en HR Zones 1-3 / mes",
            min_value=0.0, max_value=100.0, value=current['hr_zone_1_3'], step=0.5,
            help="Horas totales en zonas de baja-media intensidad"
        )

    with col6:
        hr_45 = st.number_input(
            "Horas en HR Zones 4-5 / mes",
            min_value=0.0, max_value=50.0, value=current['hr_zone_4_5'], step=0.5,
            help="Horas totales en zonas de alta intensidad"
        )

    if st.button("GUARDAR METAS", use_container_width=True):
        supabase = get_supabase()
        user_id = get_user_id()

        goals_data = {
            "user_id": user_id,
            "steps_avg": steps,
            "activities": activities,
            "strength": strength,
            "sleep_75_days": sleep_days,
            "sleep_hours_avg": sleep_hours,
            "hr_zone_1_3": hr_13,
            "hr_zone_4_5": hr_45,
        }

        try:
            if has_goals():
                # Actualizar
                supabase.table("user_goals").update({
                    k: v for k, v in goals_data.items() if k != "user_id"
                }).eq("user_id", user_id).execute()
            else:
                # Insertar
                supabase.table("user_goals").insert(goals_data).execute()

            st.success("Metas guardadas!")
            st.rerun()
        except Exception as e:
            st.error(f"Error guardando metas: {str(e)}")

    return False

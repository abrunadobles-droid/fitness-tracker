"""
Curriculo MBAT (Mindfulness-Based Attention Training) de Amishi Jha.
Programa de 28 dias / 4 semanas, 12 minutos por sesion.

Cada semana entrena un subsistema atencional distinto:
  Sem 1 - Flashlight (atencion focalizada en respiracion)
  Sem 2 - Floodlight aplicada al cuerpo (body scan)
  Sem 3 - Open monitoring (observar pensamientos y sensaciones)
  Sem 4 - Conexion e integracion (atencion interpersonal)

Cada sesion sigue la mecanica core de MBAT: Focus -> Sustain -> Notice -> Redirect.
"""

SESSION_MINUTES = 12

# Cada fase: (segundos_inicio, titulo, instruccion_texto)
# La duracion total siempre suma 12 min = 720 s.
# Las campanas suenan al inicio de cada fase y al final.

# Anclajes de fase comunes (4 bloques de 3 minutos)
def _build_phases(sustain_text, notice_text, redirect_text, focus_text):
    return [
        (0,   "FOCUS",    focus_text),
        (180, "SUSTAIN",  sustain_text),
        (360, "NOTICE",   notice_text),
        (540, "REDIRECT", redirect_text),
        (720, "FIN",      "Sesion completada. Tomate un momento antes de moverte."),
    ]


# Texto introductorio comun a cada semana
WEEK_THEMES = {
    1: {
        "name": "Semana 1 - FLASHLIGHT",
        "subtitle": "Atencion focalizada en la respiracion",
        "intro": (
            "Esta semana entrenas el subsistema **Flashlight**: tu capacidad de dirigir "
            "y mantener la atencion en un objeto especifico. La respiracion es el ancla. "
            "Cada vez que la mente se distraiga, redirige sin juicio. Esa redireccion ES "
            "el push-up mental."
        ),
    },
    2: {
        "name": "Semana 2 - BODY SCAN",
        "subtitle": "Atencion al cuerpo sin juzgar",
        "intro": (
            "Esta semana mueves el flashlight sistematicamente por el cuerpo. Entrenas "
            "el **Floodlight** sobre sensaciones corporales: notar lo que esta presente "
            "(tension, calor, hormigueo, vacio) sin etiquetarlo como bueno o malo."
        ),
    },
    3: {
        "name": "Semana 3 - OPEN MONITORING",
        "subtitle": "Observar pensamientos y sensaciones que aparecen",
        "intro": (
            "Esta semana entrenas el **Juggler**: en vez de fijar la atencion en un objeto, "
            "te conviertes en observador de lo que aparece en tu campo mental. Pensamientos, "
            "emociones, sonidos. Los notas y los dejas pasar como nubes."
        ),
    },
    4: {
        "name": "Semana 4 - CONEXION",
        "subtitle": "Atencion interpersonal y practica integrada",
        "intro": (
            "Ultima semana. Integras los 3 subsistemas y extiendes la atencion hacia "
            "otros (compasion, escucha). Esto consolida lo entrenado y lo aterriza "
            "en la vida diaria."
        ),
    },
}


def _session_template(week, day_in_week):
    """
    Genera la sesion del dia segun la semana del programa.
    Cada sesion tiene 4 fases de 3 min con instrucciones especificas.
    """
    if week == 1:
        # FLASHLIGHT - respiracion
        focus = (
            "Sientate comodo, espalda erguida. Cierra los ojos suavemente. "
            "Lleva la atencion a la respiracion: el aire entrando y saliendo por la nariz, "
            "o el subir y bajar del abdomen. Eso es el flashlight."
        )
        sustain = (
            "Manten la atencion en la respiracion. No la fuerces, no la cambies. "
            "Solo observa. Si notas que la mente se fue, eso ya es atencion. "
            "Vuelve gentilmente al ancla."
        )
        notice = (
            "Sigue con la respiracion, pero ahora nota *como* es esta respiracion: "
            "fria, calida, larga, corta. Etiqueta brevemente: 'inhalando... exhalando...' "
            "y suelta la etiqueta."
        )
        redirect = (
            "Ultima parte. Cada distraccion es un rep mas. Cuando notes que te fuiste, "
            "no te frustres: vuelve. Esa es la unica instruccion. Focus -> Sustain -> "
            "Notice -> Redirect."
        )
        # Variacion sutil por dia
        if day_in_week >= 5:
            sustain = (
                "Esta vez, cuenta las respiraciones del 1 al 10, luego empieza de nuevo. "
                "Si pierdes la cuenta, no pasa nada. Reinicia desde 1 sin juicio."
            )
        return focus, sustain, notice, redirect

    elif week == 2:
        # BODY SCAN
        focus = (
            "Sientate o acuestate. Toma 3 respiraciones profundas. Lleva la atencion a "
            "la coronilla: nota cualquier sensacion presente (calor, tension, nada). "
            "No cambies nada, solo observa."
        )
        sustain = (
            "Baja lentamente: frente, ojos, mandibula, cuello, hombros. Pausa 10-15 "
            "segundos en cada zona. Cuando notes tension, respira hacia ahi sin "
            "intentar disolverla."
        )
        notice = (
            "Continua: brazos, manos, pecho, abdomen, espalda baja. Algunas zonas no "
            "tendran sensacion clara - eso tambien es informacion. Solo nota."
        )
        redirect = (
            "Caderas, piernas, pies. Cuando llegues a los pies, expande la atencion "
            "a todo el cuerpo a la vez como un floodlight. Mantente ahi hasta la campana."
        )
        return focus, sustain, notice, redirect

    elif week == 3:
        # OPEN MONITORING
        focus = (
            "Comienza anclando en la respiracion 2-3 minutos como en semana 1. "
            "Esto estabiliza el sistema."
        )
        sustain = (
            "Ahora suelta el ancla. Permite que cualquier cosa entre a tu campo de "
            "atencion: un sonido, un pensamiento, una sensacion. No la persigas, "
            "no la rechaces. Notala y dejala pasar."
        )
        notice = (
            "Cuando aparezca un pensamiento, etiquetalo brevemente: 'pensando', "
            "'recordando', 'planeando'. Luego sueltalo. No es tu pensamiento, es "
            "*un* pensamiento que paso por aqui."
        )
        redirect = (
            "Si te enredas en una historia mental, vuelve a la respiracion como "
            "ancla de emergencia, y reabre. Ese ir y venir es el entrenamiento."
        )
        return focus, sustain, notice, redirect

    else:  # week == 4
        # CONEXION / INTEGRACION
        focus = (
            "Comienza con respiracion como ancla. Una vez estable, trae a la mente "
            "a una persona por la que sientes aprecio sincero (familia, amigo, mentor)."
        )
        sustain = (
            "Manteniendo su imagen, repite mentalmente: 'Que estes bien. Que estes "
            "en paz. Que estes libre de sufrimiento.' Nota lo que aparece en tu cuerpo "
            "al hacerlo."
        )
        notice = (
            "Ahora extiende lo mismo a alguien neutral (un vecino, un compañero "
            "lejano). Las mismas frases. Si surge resistencia, simplemente notala."
        )
        redirect = (
            "Ultima fase: extiende el deseo a ti mismo. 'Que yo este bien. Que yo "
            "este en paz.' Cierra anclando de vuelta en la respiracion 1 minuto."
        )
        return focus, sustain, notice, redirect


def get_session(day_number):
    """
    Devuelve la sesion del dia (1-28) con todas las fases.
    day_number: int, 1-28
    """
    if day_number < 1 or day_number > 28:
        raise ValueError(f"day_number debe ser 1-28, recibido {day_number}")

    week = ((day_number - 1) // 7) + 1
    day_in_week = ((day_number - 1) % 7) + 1

    focus, sustain, notice, redirect = _session_template(week, day_in_week)
    phases = _build_phases(sustain, notice, redirect, focus)

    theme = WEEK_THEMES[week]

    return {
        "day": day_number,
        "week": week,
        "day_in_week": day_in_week,
        "title": f"Dia {day_number} - {theme['name']}",
        "subtitle": theme["subtitle"],
        "intro": theme["intro"],
        "phases": phases,
        "duration_seconds": SESSION_MINUTES * 60,
        "duration_minutes": SESSION_MINUTES,
    }


def get_week_overview(week):
    """Devuelve metadata de una semana."""
    return WEEK_THEMES.get(week)

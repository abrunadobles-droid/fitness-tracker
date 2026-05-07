"""
Vista: Mente (MBAT - Mindfulness-Based Attention Training de Amishi Jha)

Tres secciones:
  1. Programa - sesion del dia con timer + campanas
  2. Tracking - metricas mensuales y calendario de adherencia
  3. Correlacion - dias con/sin meditacion vs WHOOP (Recovery, Sleep, Resting HR)
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta
from calendar import monthrange

from constants import MIND_METRICS, MESES_NOMBRES, MESES_CORTOS
from helpers import render_metric_row
import meditation_log as mlog
import meditation_program as mprog


# ============ TIMER + VOZ + CAMPANAS ============
def _render_timer(phases, total_seconds):
    """
    Componente HTML con timer, campanas (Web Audio API) y voz dictada
    (Web Speech API en espanol). En cada cambio de fase suena una campana
    suave y se dicta la instruccion de la fase. El resto es silencio.

    phases: list of (start_seconds, title, instruction)
    """
    import json as _json
    phases_js = _json.dumps(phases, ensure_ascii=False)
    html = f"""
    <div id="timer-root" style="
        font-family: 'Inter', -apple-system, sans-serif;
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #06b6d440;
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        color: #e2e8f0;
    ">
        <div id="timer-phase-title" style="
            font-family: 'Space Mono', monospace;
            font-size: 0.7rem;
            color: #06b6d4;
            letter-spacing: 4px;
            margin-bottom: 8px;
        ">PRESIONA INICIAR</div>

        <div id="timer-display" style="
            font-family: 'Space Mono', monospace;
            font-size: 3.5rem;
            font-weight: 700;
            color: #f1f5f9;
            margin: 8px 0;
            letter-spacing: 2px;
        ">12:00</div>

        <div id="timer-instruction" style="
            font-size: 0.95rem;
            color: #cbd5e1;
            margin: 16px auto;
            max-width: 600px;
            line-height: 1.6;
            min-height: 80px;
        ">Al iniciar, una voz en espanol dictara la instruccion de cada fase.<br>Las campanas marcan el inicio, los cambios de fase, y el cierre.</div>

        <div style="margin-top: 16px;">
            <button id="timer-start" style="
                background: linear-gradient(135deg, #06b6d4, #8b5cf6);
                color: #fff;
                border: none;
                padding: 12px 32px;
                border-radius: 12px;
                font-family: 'Space Mono', monospace;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 3px;
                cursor: pointer;
            ">INICIAR</button>
            <button id="timer-stop" style="
                background: transparent;
                color: #94a3b8;
                border: 1px solid #475569;
                padding: 12px 32px;
                border-radius: 12px;
                font-family: 'Space Mono', monospace;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 3px;
                cursor: pointer;
                margin-left: 8px;
                display: none;
            ">DETENER</button>
        </div>

        <div style="margin-top: 14px;">
            <select id="voice-select" style="
                background: #1a1a2e;
                color: #e2e8f0;
                border: 1px solid #06b6d430;
                border-radius: 8px;
                padding: 6px 10px;
                font-family: 'Space Mono', monospace;
                font-size: 0.65rem;
                letter-spacing: 1px;
            ">
                <option value="">VOZ ESPANOL (auto)</option>
            </select>
            <label style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#94a3b8; margin-left:14px; letter-spacing:1px;">
                <input type="checkbox" id="voice-enabled" checked style="vertical-align:middle;"> VOZ ACTIVA
            </label>
        </div>

        <div id="timer-progress-bar" style="
            margin: 20px auto 0 auto;
            max-width: 480px;
            height: 4px;
            background: #1e293b;
            border-radius: 2px;
            overflow: hidden;
        ">
            <div id="timer-progress-fill" style="
                width: 0%;
                height: 100%;
                background: linear-gradient(90deg, #06b6d4, #8b5cf6);
                transition: width 1s linear;
            "></div>
        </div>
    </div>

    <script>
    (function() {{
        const phases = {phases_js};
        const totalSec = {total_seconds};
        let elapsed = 0;
        let interval = null;
        let currentPhaseIdx = -1;
        let audioCtx = null;
        let chosenVoice = null;

        const titleEl = document.getElementById('timer-phase-title');
        const dispEl = document.getElementById('timer-display');
        const instrEl = document.getElementById('timer-instruction');
        const startBtn = document.getElementById('timer-start');
        const stopBtn = document.getElementById('timer-stop');
        const fillEl = document.getElementById('timer-progress-fill');
        const voiceSelect = document.getElementById('voice-select');
        const voiceEnabled = document.getElementById('voice-enabled');

        // ---- Voz: cargar voces espanolas y poblar el selector ----
        function loadVoices() {{
            try {{
                const all = window.speechSynthesis.getVoices();
                const esVoices = all.filter(v => v.lang && v.lang.toLowerCase().startsWith('es'));
                voiceSelect.innerHTML = '<option value="">VOZ ESPANOL (auto)</option>';
                esVoices.forEach((v, i) => {{
                    const opt = document.createElement('option');
                    opt.value = v.name;
                    opt.textContent = v.name + ' (' + v.lang + ')';
                    voiceSelect.appendChild(opt);
                }});
                if (!chosenVoice && esVoices.length > 0) {{
                    // Preferencias macOS / iOS: Monica, Paulina, Jorge, Diego
                    const preferred = ['Monica','Paulina','Jorge','Diego','Marisol'];
                    chosenVoice = esVoices.find(v => preferred.some(p => v.name.includes(p))) || esVoices[0];
                }}
            }} catch(e) {{ console.error('Voice load error', e); }}
        }}
        if (typeof speechSynthesis !== 'undefined') {{
            loadVoices();
            speechSynthesis.onvoiceschanged = loadVoices;
        }}
        voiceSelect.addEventListener('change', () => {{
            const all = window.speechSynthesis.getVoices();
            chosenVoice = all.find(v => v.name === voiceSelect.value) || null;
        }});

        function speak(text) {{
            if (!voiceEnabled.checked) return;
            if (typeof speechSynthesis === 'undefined') return;
            try {{
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.lang = 'es-ES';
                u.rate = 0.88;  // un poco lento, tono meditativo
                u.pitch = 1;
                u.volume = 0.9;
                if (chosenVoice) u.voice = chosenVoice;
                window.speechSynthesis.speak(u);
            }} catch(e) {{ console.error('Speak error', e); }}
        }}

        function fmt(s) {{
            const m = Math.floor(s / 60);
            const r = s % 60;
            return String(m).padStart(2,'0') + ':' + String(r).padStart(2,'0');
        }}

        function bell(freq, duration) {{
            try {{
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.value = freq || 528;
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                gain.gain.setValueAtTime(0, audioCtx.currentTime);
                gain.gain.linearRampToValueAtTime(0.32, audioCtx.currentTime + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + (duration || 2.5));
                osc.start();
                osc.stop(audioCtx.currentTime + (duration || 2.5));
            }} catch(e) {{ console.error('Audio error', e); }}
        }}

        function bellSequence(times) {{
            times.forEach((t) => setTimeout(() => bell(528, 2.5), t));
        }}

        function updatePhase() {{
            let idx = 0;
            for (let i = 0; i < phases.length; i++) {{
                if (elapsed >= phases[i][0]) idx = i;
            }}
            if (idx !== currentPhaseIdx) {{
                currentPhaseIdx = idx;
                const p = phases[idx];
                titleEl.textContent = p[1];
                instrEl.textContent = p[2];
                if (p[1] === 'FIN') {{
                    bellSequence([0, 700, 1400]);
                    setTimeout(() => speak('Sesion completada. Tomate un momento antes de moverte.'), 2200);
                    stop(true);
                    return;
                }}
                // Cambio de fase: campana suave + dictar instruccion
                bell(528, 2.5);
                setTimeout(() => speak(p[2]), 2200);
            }}
        }}

        function tick() {{
            elapsed += 1;
            const remaining = Math.max(totalSec - elapsed, 0);
            dispEl.textContent = fmt(remaining);
            fillEl.style.width = ((elapsed / totalSec) * 100) + '%';
            updatePhase();
            if (elapsed >= totalSec) {{
                stop(true);
            }}
        }}

        function start() {{
            elapsed = 0;
            currentPhaseIdx = -1;
            // Cargar voces JIT en caso de que aun no esten
            if (typeof speechSynthesis !== 'undefined') {{
                loadVoices();
            }}
            updatePhase();
            interval = setInterval(tick, 1000);
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
        }}

        function stop(completed) {{
            if (interval) {{
                clearInterval(interval);
                interval = null;
            }}
            if (typeof speechSynthesis !== 'undefined') {{
                // No cancelamos si esta el speak final del FIN
                if (!completed) speechSynthesis.cancel();
            }}
            startBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
            if (completed) {{
                titleEl.textContent = 'COMPLETADA';
                dispEl.textContent = '00:00';
                instrEl.textContent = 'Sesion finalizada. Marca como completada abajo para registrarla.';
            }} else {{
                titleEl.textContent = 'DETENIDA';
                dispEl.textContent = fmt(totalSec);
                fillEl.style.width = '0%';
            }}
        }}

        startBtn.addEventListener('click', start);
        stopBtn.addEventListener('click', () => stop(false));
    }})();
    </script>
    """
    components.html(html, height=470)


# ============ MAIN VIEW ============
def show(metas, current_month, current_year, days_elapsed, days_in_month):
    st.markdown('<div class="dn-header">MENTE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dn-subtitle">MBAT &middot; AMISHI JHA &middot; 12 MIN/DIA</div>',
        unsafe_allow_html=True
    )

    # Sub-navegacion interna
    if 'mente_tab' not in st.session_state:
        st.session_state.mente_tab = 'programa'

    tcol1, tcol2, tcol3 = st.columns(3)
    with tcol1:
        if st.button("PROGRAMA", use_container_width=True, key="m_prog"):
            st.session_state.mente_tab = 'programa'
            st.rerun()
    with tcol2:
        if st.button("TRACKING", use_container_width=True, key="m_track"):
            st.session_state.mente_tab = 'tracking'
            st.rerun()
    with tcol3:
        if st.button("CORRELACION", use_container_width=True, key="m_corr"):
            st.session_state.mente_tab = 'correlacion'
            st.rerun()

    if st.session_state.mente_tab == 'programa':
        _show_programa()
    elif st.session_state.mente_tab == 'tracking':
        _show_tracking(metas, current_month, current_year, days_elapsed, days_in_month)
    elif st.session_state.mente_tab == 'correlacion':
        _show_correlacion()


# ============ SECCION 1: PROGRAMA ============
def _show_programa():
    current_day = mlog.get_current_day()

    if current_day > 28:
        st.markdown('<div class="dn-section">// PROGRAMA COMPLETADO</div>', unsafe_allow_html=True)
        st.success("Completaste el programa MBAT de 4 semanas. Puedes reiniciarlo o seguir con sesiones libres.")
        if st.button("REINICIAR PROGRAMA", key="reset_prog"):
            mlog.reset_program()
            st.rerun()
        return

    session = mprog.get_session(current_day)

    st.markdown(
        f'<div class="dn-section">// {session["title"]}</div>',
        unsafe_allow_html=True
    )

    # Card con tema de la semana
    st.markdown(f'''<div class="dn-card" style="text-align:left; padding:24px;">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#06b6d4; letter-spacing:3px; margin-bottom:8px;">
            DIA {current_day} / 28 &middot; {session["subtitle"].upper()}
        </div>
        <div style="font-size:0.95rem; color:#cbd5e1; line-height:1.6;">
            {session["intro"]}
        </div>
    </div>''', unsafe_allow_html=True)

    # Resumen de fases (texto previo a iniciar)
    st.markdown('<div class="dn-section">// FASES DE LA SESION</div>', unsafe_allow_html=True)

    phases_to_show = [p for p in session["phases"] if p[1] != "FIN"]
    for start_s, title, instr in phases_to_show:
        m = start_s // 60
        st.markdown(f'''<div class="dn-metric" style="flex-direction:column; align-items:flex-start;">
            <div style="display:flex; justify-content:space-between; width:100%; margin-bottom:6px;">
                <span class="name" style="color:#06b6d4;">{title}</span>
                <span class="dn-pct">min {m}-{m+3}</span>
            </div>
            <div style="font-size:0.85rem; color:#94a3b8; line-height:1.5;">{instr}</div>
        </div>''', unsafe_allow_html=True)

    # Timer
    st.markdown('<div class="dn-section">// SESION GUIADA (12 MIN)</div>', unsafe_allow_html=True)
    _render_timer(session["phases"], session["duration_seconds"])

    st.caption(
        "Voz en espanol dictara la instruccion al inicio de cada fase. "
        "Campanas: inicial, en cada cambio de fase (cada 3 min), y triple al cierre. "
        "Si no escuchas voz, revisa el selector y permite audio en el navegador."
    )

    # Marcar completada
    st.markdown('<div class="dn-section">// REGISTRAR</div>', unsafe_allow_html=True)
    notes = st.text_area("Notas de la sesion (opcional)", key="med_notes",
                          placeholder="Que noto? Que distrajo? Como me siento?")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("MARCAR COMPLETADA", use_container_width=True, key="mark_done"):
            mlog.log_session(current_day, mprog.SESSION_MINUTES, completed=True, notes=notes)
            st.session_state.last_completed_minutes = mprog.SESSION_MINUTES
            st.success(f"Dia {current_day} registrado. Manana toca dia {current_day + 1}.")
            st.rerun()
    with col_b:
        if st.button("OMITIR DIA", use_container_width=True, key="skip_day"):
            mlog.log_session(current_day, 0, completed=False, notes=f"OMITIDO: {notes}")
            data = mlog._load()
            data["current_day"] = min(current_day + 1, 29)
            mlog._save(data)
            st.info("Dia omitido. Avanzas al siguiente.")
            st.rerun()

    _render_apple_health_section()


# ============ APPLE HEALTH (via Atajos / Shortcuts) ============
APPLE_SHORTCUT_NAME = "AddMindfulMinutes"


def _render_apple_health_section():
    """
    Boton para enviar minutos a Apple Health via Shortcut URL scheme.
    Solo funciona desde Safari en iPhone/iPad/Mac con el Atajo configurado.
    """
    st.markdown('<div class="dn-section">// APPLE HEALTH</div>', unsafe_allow_html=True)

    last_min = st.session_state.get("last_completed_minutes", mprog.SESSION_MINUTES)
    shortcut_name = st.session_state.get("apple_shortcut_name", APPLE_SHORTCUT_NAME)

    url = f"shortcuts://run-shortcut?name={shortcut_name}&input=text&text={last_min}"

    st.markdown(f'''
    <a href="{url}" style="
        display: block;
        background: linear-gradient(135deg, #06b6d4, #8b5cf6);
        color: #fff;
        text-decoration: none;
        text-align: center;
        padding: 14px;
        border-radius: 12px;
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 3px;
    ">ANADIR {last_min} MIN A APPLE HEALTH</a>
    ''', unsafe_allow_html=True)

    st.caption(
        "Abrir este boton desde Safari en iPhone/iPad/Mac dispara el Atajo "
        f"'{shortcut_name}' que escribe los minutos en Apple Health (categoria Mindful Minutes)."
    )

    with st.expander("Como configurar el Atajo (una sola vez)"):
        st.markdown(f'''
**En tu iPhone, app Atajos (Shortcuts):**

1. Crea un nuevo atajo y nombralo exactamente: **`{shortcut_name}`**
2. Anade la accion **"Recibir entrada del atajo"** y selecciona tipo **Texto**
3. Anade la accion **"Obtener numeros de entrada"** (Get Numbers from Input)
4. Anade la accion **"Registrar muestra de salud"** (Log Health Sample) con:
   - **Tipo:** *Atencion plena* / *Mindful Minutes*
   - **Cantidad:** la salida del paso anterior
   - **Unidad:** Minutos
   - **Fecha:** Ahora
5. (Opcional) Compartir > "Anadir a la pantalla de inicio" para acceso rapido.

Una vez creado, el boton de arriba abrira Atajos automaticamente al pulsarlo desde Safari.
Si usas otro nombre, cambialo en el campo de abajo.
''')

        new_name = st.text_input(
            "Nombre del atajo (sin espacios)",
            value=shortcut_name,
            key="shortcut_name_input"
        )
        if new_name and new_name != shortcut_name:
            st.session_state.apple_shortcut_name = new_name
            st.rerun()


# ============ SECCION 2: TRACKING ============
def _show_tracking(metas, current_month, current_year, days_elapsed, days_in_month):
    st.markdown(
        f'<div class="dn-section">// {MESES_NOMBRES[current_month]} {current_year}</div>',
        unsafe_allow_html=True
    )

    stats = mlog.monthly_stats(current_year, current_month)

    # Cards resumen
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (str(stats["sessions_count"]), "SESIONES"),
        (f"{stats['minutes_total']}", "MINUTOS"),
        (f"{mlog.get_current_day()}/28", "DIA PROGRAMA"),
        (f"{int(stats['sessions_count'] / max(days_elapsed,1) * 100)}%", "ADHERENCIA"),
    ]
    for col, (val, lbl) in zip([c1, c2, c3, c4], cards):
        col.markdown(f'''<div class="dn-card">
            <div class="value">{val}</div>
            <div class="label">{lbl}</div>
        </div>''', unsafe_allow_html=True)

    # Metricas vs metas
    st.markdown('<div class="dn-section">// METAS DEL MES</div>', unsafe_allow_html=True)
    data = {
        'meditation_sessions': stats['sessions_count'],
        'meditation_minutes': stats['minutes_total'],
    }
    for key, label, unit, tipo in MIND_METRICS:
        render_metric_row(label, data[key], metas.get(key, 0), unit, tipo,
                          days_elapsed, days_in_month, for_current_month=True)

    # Calendario simple del mes (heatmap basico)
    st.markdown('<div class="dn-section">// CALENDARIO MES</div>', unsafe_allow_html=True)
    sessions = mlog.sessions_in_month(current_year, current_month)
    days_with_session = {datetime.strptime(s["date"], "%Y-%m-%d").day for s in sessions}

    # Render grid de 7 columnas
    days_in_m = monthrange(current_year, current_month)[1]
    first_dow = datetime(current_year, current_month, 1).weekday()  # 0=lun

    cells_html = ""
    # Espacios vacios al inicio
    for _ in range(first_dow):
        cells_html += '<div style="width:36px;height:36px;"></div>'

    for d in range(1, days_in_m + 1):
        if d in days_with_session:
            bg = "linear-gradient(135deg, #06b6d4, #8b5cf6)"
            color = "#0a0a0f"
            border = "1px solid #06b6d4"
        elif d <= days_elapsed:
            bg = "#1a1a2e"
            color = "#475569"
            border = "1px solid #ffffff10"
        else:
            bg = "transparent"
            color = "#334155"
            border = "1px dashed #ffffff08"
        cells_html += (
            f'<div style="width:36px;height:36px;border-radius:8px;background:{bg};'
            f'color:{color};border:{border};display:flex;align-items:center;justify-content:center;'
            f'font-family:\'Space Mono\',monospace;font-size:0.7rem;font-weight:700;">{d}</div>'
        )

    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(7,36px);gap:6px;justify-content:center;margin-top:12px;">{cells_html}</div>',
        unsafe_allow_html=True
    )
    st.caption("Cyan = sesion completada. Gris = sin sesion. Punteado = aun no.")


# ============ SECCION 3: CORRELACION ============
def _show_correlacion():
    st.markdown('<div class="dn-section">// EFECTO BIOMETRICO (60 DIAS)</div>', unsafe_allow_html=True)
    st.caption(
        "Compara dias **siguientes** a una sesion de meditacion vs dias siguientes sin meditacion. "
        "Hipotesis MBAT: HRV / Recovery / Sleep mejoran tras la practica."
    )

    # Traer datos diarios de WHOOP de los ultimos 60 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    try:
        from whoop_streamlit import _get_all_records
        recoveries = _get_all_records('recovery', start_date, end_date)
        sleeps = _get_all_records('activity/sleep', start_date, end_date)
    except Exception as e:
        st.warning(f"No se pudo obtener datos de WHOOP en vivo: {e}")
        st.info("La correlacion requiere acceso a la API de WHOOP (no usa cache mensual).")
        return

    # Mapear por fecha (YYYY-MM-DD): cada cycle/sleep tiene 'created_at' o 'start'
    daily = {}  # date_str -> {'recovery': X, 'rhr': Y, 'sleep_consistency': Z, 'sleep_h': W}
    for r in recoveries:
        try:
            cstr = r.get('created_at', '')[:10] or r.get('updated_at', '')[:10]
            if not cstr:
                continue
            score = r.get('score') or {}
            rs = score.get('recovery_score')
            rhr = score.get('resting_heart_rate')
            if rs and rs > 0:
                daily.setdefault(cstr, {})['recovery'] = rs
            if rhr and rhr > 0:
                daily.setdefault(cstr, {})['rhr'] = rhr
        except Exception:
            continue

    for s in sleeps:
        if s.get('nap'):
            continue
        try:
            cstr = s.get('start', '')[:10]
            if not cstr:
                continue
            score = s.get('score') or {}
            sc = score.get('sleep_consistency_percentage')
            stages = score.get('stage_summary') or {}
            actual_ms = (
                stages.get('total_light_sleep_time_milli', 0) +
                stages.get('total_slow_wave_sleep_time_milli', 0) +
                stages.get('total_rem_sleep_time_milli', 0)
            )
            if sc:
                daily.setdefault(cstr, {})['sleep_consistency'] = sc
            if actual_ms > 0:
                daily.setdefault(cstr, {})['sleep_h'] = round(actual_ms / 3600000, 2)
        except Exception:
            continue

    if not daily:
        st.warning("Sin datos de WHOOP en los ultimos 60 dias.")
        return

    med_dates = mlog.get_meditation_dates(days_back=60)
    if not med_dates:
        st.info("Aun no hay sesiones de meditacion registradas. Completa al menos 5 sesiones para ver correlaciones significativas.")
        return

    # Para cada dia con meditacion, busca el dia SIGUIENTE en daily
    after_med = {'recovery': [], 'rhr': [], 'sleep_consistency': [], 'sleep_h': []}
    after_no_med = {'recovery': [], 'rhr': [], 'sleep_consistency': [], 'sleep_h': []}

    for d_str, metrics in daily.items():
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        prev = (d - timedelta(days=1)).isoformat()
        target = after_med if prev in med_dates else after_no_med
        for k in target:
            if k in metrics:
                target[k].append(metrics[k])

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else None

    rows = [
        ("Recovery Score (%)", avg(after_med['recovery']), avg(after_no_med['recovery']), False),
        ("HRV proxy (RHR bpm)", avg(after_med['rhr']), avg(after_no_med['rhr']), True),
        ("Sleep Consistency (%)", avg(after_med['sleep_consistency']), avg(after_no_med['sleep_consistency']), False),
        ("Sleep Hours", avg(after_med['sleep_h']), avg(after_no_med['sleep_h']), False),
    ]

    rows_html = ""
    for label, with_med, no_med, inverted in rows:
        if with_med is None or no_med is None:
            delta_str = "—"
            trend = "—"
        else:
            delta = with_med - no_med
            if inverted:
                better = delta < 0  # menor RHR = mejor
            else:
                better = delta > 0
            trend = "🟢" if better and abs(delta) > 0.3 else ("🔴" if (not better) and abs(delta) > 0.3 else "⚪")
            delta_str = f"{delta:+.1f}"

        wm = f"{with_med}" if with_med is not None else "—"
        nm = f"{no_med}" if no_med is not None else "—"
        rows_html += f"""<tr>
            <td>{label}</td>
            <td class="val">{wm}</td>
            <td class="val">{nm}</td>
            <td>{trend} {delta_str}</td>
        </tr>"""

    n_med = len(med_dates)
    n_no = len([d for d in daily if (datetime.strptime(d, '%Y-%m-%d').date() - timedelta(days=1)).isoformat() not in med_dates])

    st.markdown(f'''<table class="dn-table">
        <thead><tr>
            <th>Metrica (dia siguiente)</th>
            <th>Tras meditar</th>
            <th>Sin meditar</th>
            <th>Delta</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>''', unsafe_allow_html=True)

    st.caption(f"n = {n_med} dias post-meditacion, {n_no} dias post-sin-meditacion. Necesitas mas datos para significancia estadistica real.")

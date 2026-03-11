"""
Style Demo - Preview 4 design options for the Fitness Tracker
Run: streamlit run style_demo.py
"""
import streamlit as st

st.set_page_config(page_title="Style Demo", page_icon="🎨", layout="wide")

# ---- Sample data for preview ----
SAMPLE = {
    'steps_avg': 12450, 'activities': 22, 'strength': 8,
    'hr_zone_1_3': 15.2, 'hr_zone_4_5': 2.1,
    'sleep_hours_avg': 7.8, 'recovery_score': 62,
    'resting_hr': 52, 'sleep_consistency': 85,
}
METAS = {
    'steps_avg': 10000, 'activities': 28, 'strength': 10,
    'hr_zone_1_3': 19.3, 'hr_zone_4_5': 2.9,
    'sleep_hours_avg': 7.5, 'recovery_score': 50,
    'resting_hr': 55, 'sleep_consistency': 80,
}
FITNESS = [
    ('steps_avg', 'Steps Daily Avg', '', 85),
    ('activities', 'Activities', '', 78),
    ('strength', 'Strength', '', 80),
    ('hr_zone_1_3', 'HR Zones 1-3', 'h', 78),
    ('hr_zone_4_5', 'HR Zones 4-5', 'h', 72),
]
SLEEP = [
    ('sleep_hours_avg', 'Sleep Duration', 'h', 104),
    ('recovery_score', 'Recovery Score', '%', 124),
    ('resting_hr', 'Resting HR', 'bpm', 106),
    ('sleep_consistency', 'Sleep Consistency', '%', 106),
]

style = st.radio("ELIGE UN ESTILO:", [
    "1. Dark Neon Sports",
    "2. Clean Minimal",
    "3. Gradient Bold",
    "4. Terminal Hacker",
], horizontal=True)

st.divider()

# ==============================================================
# STYLE 1: DARK NEON SPORTS
# ==============================================================
if style.startswith("1"):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=Space+Mono:wght@400;700&display=swap');

    .stApp {
        background: #0a0a0f !important;
    }
    section[data-testid="stSidebar"] { display: none; }

    .dark-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 6px;
        background: linear-gradient(135deg, #06b6d4, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0 0 4px 0;
    }
    .dark-subtitle {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #64748b;
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 28px;
    }
    .dark-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #06b6d420;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .dark-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #06b6d4, #8b5cf6);
    }
    .dark-card .value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: #f1f5f9;
        margin: 8px 0 2px 0;
    }
    .dark-card .label {
        font-family: 'Space Mono', monospace;
        font-size: 0.55rem;
        color: #64748b;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    .dark-section {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #06b6d4;
        letter-spacing: 3px;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #06b6d420;
    }
    .dark-metric {
        background: #1a1a2e;
        border: 1px solid #ffffff08;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .dark-metric .name {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    .dark-metric .val {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #f1f5f9;
    }
    .dark-bar-bg {
        width: 120px;
        height: 6px;
        background: #1e293b;
        border-radius: 3px;
        overflow: hidden;
        display: inline-block;
        margin: 0 10px;
    }
    .dark-bar-fill {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #06b6d4, #8b5cf6);
    }
    .dark-pct {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #06b6d4;
        min-width: 40px;
        text-align: right;
    }
    .dark-status {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
    }
    .dark-status.green { background: #10b981; box-shadow: 0 0 8px #10b98180; }
    .dark-status.yellow { background: #f59e0b; box-shadow: 0 0 8px #f59e0b80; }
    .dark-status.red { background: #ef4444; box-shadow: 0 0 8px #ef444480; }
    .dark-nav {
        background: #1a1a2e;
        border: 1px solid #06b6d430;
        border-radius: 12px;
        padding: 10px 20px;
        text-align: center;
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        color: #94a3b8;
        letter-spacing: 2px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .dark-nav.active {
        border-color: #06b6d4;
        color: #06b6d4;
        background: #06b6d410;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="dark-header">FITNESS TRACKER</div>', unsafe_allow_html=True)
    st.markdown('<div class="dark-subtitle">MAR 2026 &middot; DIA 11/31 &middot; 35% DEL MES</div>', unsafe_allow_html=True)

    # Nav
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="dark-nav active">MES ACTUAL</div>', unsafe_allow_html=True)
    c2.markdown('<div class="dark-nav">HISTORICO</div>', unsafe_allow_html=True)
    c3.markdown('<div class="dark-nav">METAS</div>', unsafe_allow_html=True)
    c4.markdown('<div class="dark-nav">ACTUALIZAR</div>', unsafe_allow_html=True)

    # Summary cards
    st.markdown("", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, (val, lbl) in zip([c1, c2, c3, c4], [
        ("12,450", "STEPS AVG"), ("7 / 9", "METAS OK"), ("62%", "RECOVERY"), ("35%", "PROGRESO MES")
    ]):
        col.markdown(f'''<div class="dark-card">
            <div class="value">{val}</div>
            <div class="label">{lbl}</div>
        </div>''', unsafe_allow_html=True)

    # Fitness habits
    st.markdown('<div class="dark-section">// FITNESS HABITS</div>', unsafe_allow_html=True)
    for key, label, unit, pct in FITNESS:
        val = SAMPLE[key]
        display_val = f"{val:,}" if isinstance(val, int) and val >= 1000 else f"{val} {unit}".strip()
        status_cls = "green" if pct >= 100 else "yellow" if pct >= 70 else "red"
        bar_w = min(pct, 100)
        st.markdown(f'''<div class="dark-metric">
            <div style="display:flex;align-items:center;">
                <span class="dark-status {status_cls}"></span>
                <span class="name">{label}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <span class="val">{display_val}</span>
                <div class="dark-bar-bg"><div class="dark-bar-fill" style="width:{bar_w}%"></div></div>
                <span class="dark-pct">{pct}%</span>
            </div>
        </div>''', unsafe_allow_html=True)

    # Sleep habits
    st.markdown('<div class="dark-section">// SLEEP HABITS</div>', unsafe_allow_html=True)
    for key, label, unit, pct in SLEEP:
        val = SAMPLE[key]
        display_val = f"{val} {unit}".strip()
        status_cls = "green" if pct >= 100 else "yellow" if pct >= 70 else "red"
        bar_w = min(pct, 100)
        st.markdown(f'''<div class="dark-metric">
            <div style="display:flex;align-items:center;">
                <span class="dark-status {status_cls}"></span>
                <span class="name">{label}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <span class="val">{display_val}</span>
                <div class="dark-bar-bg"><div class="dark-bar-fill" style="width:{bar_w}%"></div></div>
                <span class="dark-pct">{min(pct,100)}%</span>
            </div>
        </div>''', unsafe_allow_html=True)


# ==============================================================
# STYLE 2: CLEAN MINIMAL
# ==============================================================
elif style.startswith("2"):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background: #fafbfc !important;
    }

    .clean-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.6rem;
        font-weight: 300;
        letter-spacing: 8px;
        color: #1f2937;
        text-align: center;
        margin: 0 0 4px 0;
    }
    .clean-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #9ca3af;
        text-align: center;
        letter-spacing: 1px;
        margin-bottom: 28px;
        font-weight: 400;
    }
    .clean-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
        border: 1px solid #f3f4f6;
    }
    .clean-card .value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #111827;
        margin: 4px 0;
    }
    .clean-card .label {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        color: #9ca3af;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 500;
    }
    .clean-section {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: #6b7280;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 500;
        margin: 32px 0 16px 0;
    }
    .clean-metric {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        border: 1px solid #f3f4f6;
    }
    .clean-metric .name {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: #374151;
    }
    .clean-metric .val {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #111827;
    }
    .clean-bar-bg {
        width: 100px;
        height: 4px;
        background: #f3f4f6;
        border-radius: 2px;
        overflow: hidden;
        display: inline-block;
        margin: 0 12px;
    }
    .clean-bar-fill {
        height: 100%;
        border-radius: 2px;
        background: #34d399;
    }
    .clean-bar-fill.warn { background: #fbbf24; }
    .clean-bar-fill.danger { background: #f87171; }
    .clean-pct {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: #9ca3af;
        min-width: 36px;
        text-align: right;
        font-weight: 500;
    }
    .clean-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
    }
    .clean-dot.green { background: #34d399; }
    .clean-dot.yellow { background: #fbbf24; }
    .clean-dot.red { background: #f87171; }
    .clean-nav {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px 20px;
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        color: #6b7280;
        letter-spacing: 1px;
        font-weight: 500;
    }
    .clean-nav.active {
        border-color: #34d399;
        color: #059669;
        background: #ecfdf5;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="clean-header">F I T N E S S   T R A C K E R</div>', unsafe_allow_html=True)
    st.markdown('<div class="clean-subtitle">Marzo 2026 &middot; Dia 11 de 31</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="clean-nav active">MES ACTUAL</div>', unsafe_allow_html=True)
    c2.markdown('<div class="clean-nav">HISTORICO</div>', unsafe_allow_html=True)
    c3.markdown('<div class="clean-nav">METAS</div>', unsafe_allow_html=True)
    c4.markdown('<div class="clean-nav">ACTUALIZAR</div>', unsafe_allow_html=True)

    st.markdown("", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, (val, lbl) in zip([c1, c2, c3, c4], [
        ("12,450", "STEPS AVG"), ("7 / 9", "METAS OK"), ("62%", "RECOVERY"), ("35%", "PROGRESO")
    ]):
        col.markdown(f'''<div class="clean-card">
            <div class="label">{lbl}</div>
            <div class="value">{val}</div>
        </div>''', unsafe_allow_html=True)

    st.markdown('<div class="clean-section">Fitness</div>', unsafe_allow_html=True)
    for key, label, unit, pct in FITNESS:
        val = SAMPLE[key]
        display_val = f"{val:,}" if isinstance(val, int) and val >= 1000 else f"{val} {unit}".strip()
        dot_cls = "green" if pct >= 100 else "yellow" if pct >= 70 else "red"
        bar_cls = "" if pct >= 100 else "warn" if pct >= 70 else "danger"
        bar_w = min(pct, 100)
        st.markdown(f'''<div class="clean-metric">
            <div style="display:flex;align-items:center;">
                <span class="clean-dot {dot_cls}"></span>
                <span class="name">{label}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <span class="val">{display_val}</span>
                <div class="clean-bar-bg"><div class="clean-bar-fill {bar_cls}" style="width:{bar_w}%"></div></div>
                <span class="clean-pct">{pct}%</span>
            </div>
        </div>''', unsafe_allow_html=True)

    st.markdown('<div class="clean-section">Sleep</div>', unsafe_allow_html=True)
    for key, label, unit, pct in SLEEP:
        val = SAMPLE[key]
        display_val = f"{val} {unit}".strip()
        dot_cls = "green" if pct >= 100 else "yellow" if pct >= 70 else "red"
        bar_cls = "" if pct >= 100 else "warn" if pct >= 70 else "danger"
        bar_w = min(pct, 100)
        st.markdown(f'''<div class="clean-metric">
            <div style="display:flex;align-items:center;">
                <span class="clean-dot {dot_cls}"></span>
                <span class="name">{label}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <span class="val">{display_val}</span>
                <div class="clean-bar-bg"><div class="clean-bar-fill {bar_cls}" style="width:{bar_w}%"></div></div>
                <span class="clean-pct">{min(pct,100)}%</span>
            </div>
        </div>''', unsafe_allow_html=True)


# ==============================================================
# STYLE 3: GRADIENT BOLD
# ==============================================================
elif style.startswith("3"):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');

    .stApp {
        background: #0f0f1a !important;
    }

    .bold-header-wrap {
        background: linear-gradient(135deg, #f97316, #ec4899, #8b5cf6);
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        margin-bottom: 24px;
    }
    .bold-header {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: white;
        letter-spacing: 4px;
        margin: 0;
    }
    .bold-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: rgba(255,255,255,0.8);
        letter-spacing: 2px;
        margin-top: 4px;
    }
    .bold-card {
        background: linear-gradient(145deg, #1e1e2f, #2a2a40);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .bold-card .emoji { font-size: 1.5rem; margin-bottom: 4px; }
    .bold-card .value {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 900;
        color: #ffffff;
    }
    .bold-card .label {
        font-family: 'Inter', sans-serif;
        font-size: 0.55rem;
        color: #8b8ba0;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .bold-section {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 800;
        color: #e2e8f0;
        letter-spacing: 2px;
        margin: 28px 0 14px 0;
    }
    .bold-metric {
        background: linear-gradient(145deg, #1e1e2f, #2a2a40);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .bold-metric-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .bold-metric .name {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    .bold-metric .val {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #ffffff;
    }
    .bold-bar-bg {
        width: 100%;
        height: 8px;
        background: #1a1a2e;
        border-radius: 4px;
        overflow: hidden;
    }
    .bold-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s;
    }
    .bold-bar-fill.green { background: linear-gradient(90deg, #10b981, #34d399); }
    .bold-bar-fill.yellow { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .bold-bar-fill.red { background: linear-gradient(90deg, #ef4444, #f87171); }
    .bold-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.6rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .bold-badge.green { background: #10b98120; color: #34d399; }
    .bold-badge.yellow { background: #f59e0b20; color: #fbbf24; }
    .bold-badge.red { background: #ef444420; color: #f87171; }
    .bold-nav {
        background: #1e1e2f;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 0.6rem;
        font-weight: 700;
        color: #8b8ba0;
        letter-spacing: 2px;
    }
    .bold-nav.active {
        background: linear-gradient(135deg, #f9731640, #ec489940);
        border-color: #f97316;
        color: #f97316;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('''<div class="bold-header-wrap">
        <div class="bold-header">FITNESS TRACKER</div>
        <div class="bold-subtitle">MARZO 2026 &middot; DIA 11/31</div>
    </div>''', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="bold-nav active">MES ACTUAL</div>', unsafe_allow_html=True)
    c2.markdown('<div class="bold-nav">HISTORICO</div>', unsafe_allow_html=True)
    c3.markdown('<div class="bold-nav">METAS</div>', unsafe_allow_html=True)
    c4.markdown('<div class="bold-nav">ACTUALIZAR</div>', unsafe_allow_html=True)

    st.markdown("", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, (emoji, val, lbl) in zip([c1, c2, c3, c4], [
        ("🔥", "12,450", "STEPS AVG"), ("🎯", "7 / 9", "METAS OK"),
        ("💚", "62%", "RECOVERY"), ("📊", "35%", "PROGRESO")
    ]):
        col.markdown(f'''<div class="bold-card">
            <div class="emoji">{emoji}</div>
            <div class="value">{val}</div>
            <div class="label">{lbl}</div>
        </div>''', unsafe_allow_html=True)

    st.markdown('<div class="bold-section">🏋️ FITNESS HABITS</div>', unsafe_allow_html=True)
    for key, label, unit, pct in FITNESS:
        val = SAMPLE[key]
        display_val = f"{val:,}" if isinstance(val, int) and val >= 1000 else f"{val} {unit}".strip()
        color = "green" if pct >= 100 else "yellow" if pct >= 70 else "red"
        bar_w = min(pct, 100)
        st.markdown(f'''<div class="bold-metric">
            <div class="bold-metric-top">
                <span class="name">{label}</span>
                <div><span class="val">{display_val}</span> <span class="bold-badge {color}">{pct}%</span></div>
            </div>
            <div class="bold-bar-bg"><div class="bold-bar-fill {color}" style="width:{bar_w}%"></div></div>
        </div>''', unsafe_allow_html=True)

    st.markdown('<div class="bold-section">😴 SLEEP HABITS</div>', unsafe_allow_html=True)
    for key, label, unit, pct in SLEEP:
        val = SAMPLE[key]
        display_val = f"{val} {unit}".strip()
        color = "green" if pct >= 100 else "yellow" if pct >= 70 else "red"
        bar_w = min(pct, 100)
        st.markdown(f'''<div class="bold-metric">
            <div class="bold-metric-top">
                <span class="name">{label}</span>
                <div><span class="val">{display_val}</span> <span class="bold-badge {color}">{min(pct,100)}%</span></div>
            </div>
            <div class="bold-bar-bg"><div class="bold-bar-fill {color}" style="width:{bar_w}%"></div></div>
        </div>''', unsafe_allow_html=True)


# ==============================================================
# STYLE 4: TERMINAL / HACKER
# ==============================================================
elif style.startswith("4"):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    .stApp {
        background: #000000 !important;
    }

    .term-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #00ff41;
        margin: 0;
        line-height: 1.8;
    }
    .term-header .prompt { color: #00ff4180; }
    .term-header .cmd { color: #00ff41; font-weight: 700; }
    .term-divider {
        border: none;
        border-top: 1px solid #00ff4130;
        margin: 16px 0;
    }
    .term-section {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #00ff4180;
        letter-spacing: 2px;
        margin: 20px 0 12px 0;
    }
    .term-metric {
        font-family: 'JetBrains Mono', monospace;
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #00ff4108;
    }
    .term-metric .bracket {
        color: #00ff4160;
        font-size: 0.7rem;
        min-width: 120px;
    }
    .term-metric .val {
        color: #00ff41;
        font-size: 0.85rem;
        font-weight: 700;
        min-width: 80px;
    }
    .term-bar {
        display: inline-flex;
        margin: 0 12px;
    }
    .term-bar-char {
        font-size: 0.8rem;
        width: 8px;
    }
    .term-bar-char.filled { color: #00ff41; }
    .term-bar-char.empty { color: #00ff4120; }
    .term-pct {
        color: #00ff4190;
        font-size: 0.7rem;
        min-width: 45px;
        text-align: right;
    }
    .term-summary {
        font-family: 'JetBrains Mono', monospace;
        background: #00ff4108;
        border: 1px solid #00ff4120;
        border-radius: 4px;
        padding: 16px;
        margin-top: 20px;
    }
    .term-summary-line {
        font-size: 0.7rem;
        color: #00ff41;
        line-height: 2;
    }
    .term-nav {
        font-family: 'JetBrains Mono', monospace;
        background: transparent;
        border: 1px solid #00ff4130;
        border-radius: 0;
        padding: 8px;
        text-align: center;
        font-size: 0.6rem;
        color: #00ff4160;
        letter-spacing: 1px;
    }
    .term-nav.active {
        border-color: #00ff41;
        color: #00ff41;
        background: #00ff4110;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('''<div class="term-header">
        <span class="prompt">$</span> <span class="cmd">./fitness_tracker --status</span><br>
        <span class="prompt">></span> FITNESS_TRACKER v2.0<br>
        <span class="prompt">></span> DATE: 2026-03-11 | DAY: 11/31 | PROGRESS: 35%<br>
        <span class="prompt">></span> STATUS: ACTIVE
    </div>''', unsafe_allow_html=True)

    st.markdown('<hr class="term-divider">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="term-nav active">[ MES ACTUAL ]</div>', unsafe_allow_html=True)
    c2.markdown('<div class="term-nav">[ HISTORICO ]</div>', unsafe_allow_html=True)
    c3.markdown('<div class="term-nav">[ METAS ]</div>', unsafe_allow_html=True)
    c4.markdown('<div class="term-nav">[ REFRESH ]</div>', unsafe_allow_html=True)

    def term_bar(pct):
        filled = int(min(pct, 100) / 10)
        empty = 10 - filled
        bar = ""
        for _ in range(filled):
            bar += '<span class="term-bar-char filled">█</span>'
        for _ in range(empty):
            bar += '<span class="term-bar-char empty">░</span>'
        return bar

    st.markdown('<div class="term-section">--- FITNESS ---</div>', unsafe_allow_html=True)
    for key, label, unit, pct in FITNESS:
        val = SAMPLE[key]
        display_val = f"{val:,}" if isinstance(val, int) and val >= 1000 else f"{val}{unit}"
        short = label[:14].ljust(14)
        bar = term_bar(pct)
        st.markdown(f'''<div class="term-metric">
            <span class="bracket">[{short}]</span>
            <span class="val">{display_val}</span>
            <span class="term-bar">{bar}</span>
            <span class="term-pct">{min(pct,100)}%</span>
        </div>''', unsafe_allow_html=True)

    st.markdown('<div class="term-section">--- SLEEP ---</div>', unsafe_allow_html=True)
    for key, label, unit, pct in SLEEP:
        val = SAMPLE[key]
        display_val = f"{val}{unit}"
        short = label[:14].ljust(14)
        bar = term_bar(min(pct, 100))
        st.markdown(f'''<div class="term-metric">
            <span class="bracket">[{short}]</span>
            <span class="val">{display_val}</span>
            <span class="term-bar">{bar}</span>
            <span class="term-pct">{min(pct,100)}%</span>
        </div>''', unsafe_allow_html=True)

    st.markdown('''<div class="term-summary">
        <div class="term-summary-line">> SCORE: 7/9 GOALS MET</div>
        <div class="term-summary-line">> WHOOP: cache | GARMIN: api</div>
        <div class="term-summary-line">> EOF</div>
    </div>''', unsafe_allow_html=True)

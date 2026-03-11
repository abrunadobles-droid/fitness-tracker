"""
Configuración - Compatible con Streamlit Secrets y GitHub Actions (env vars)
"""

import os

# Prioridad: env vars > Streamlit secrets > valores por defecto

# 1. Intentar desde variables de entorno (GitHub Actions)
if os.environ.get('WHOOP_CLIENT_ID'):
    WHOOP_CLIENT_ID = os.environ['WHOOP_CLIENT_ID']
    WHOOP_CLIENT_SECRET = os.environ.get('WHOOP_CLIENT_SECRET', '')
    WHOOP_ACCESS_TOKEN = os.environ.get('WHOOP_ACCESS_TOKEN', '')
    WHOOP_REFRESH_TOKEN = os.environ.get('WHOOP_REFRESH_TOKEN', '')
    GARMIN_EMAIL = os.environ.get('GARMIN_EMAIL', '')
    GARMIN_PASSWORD = os.environ.get('GARMIN_PASSWORD', '')
else:
    try:
        # 2. Streamlit Secrets
        import streamlit as st
        WHOOP_CLIENT_ID = st.secrets["whoop"]["client_id"]
        WHOOP_CLIENT_SECRET = st.secrets["whoop"]["client_secret"]
        WHOOP_ACCESS_TOKEN = st.secrets.get("whoop", {}).get("access_token", "")
        WHOOP_REFRESH_TOKEN = st.secrets.get("whoop", {}).get("refresh_token", "")
        GARMIN_EMAIL = st.secrets["garmin"]["email"]
        GARMIN_PASSWORD = st.secrets["garmin"]["password"]
    except:
        # 3. Fallback para desarrollo local (configurar via .streamlit/secrets.toml)
        WHOOP_CLIENT_ID = ""
        WHOOP_CLIENT_SECRET = ""
        WHOOP_ACCESS_TOKEN = ""
        WHOOP_REFRESH_TOKEN = ""
        GARMIN_EMAIL = ""
        GARMIN_PASSWORD = ""

WHOOP_REDIRECT_URI = 'http://localhost:8000/callback'

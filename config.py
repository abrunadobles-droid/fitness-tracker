"""
Configuración - Compatible con Streamlit Secrets y GitHub Actions (env vars)
"""

import os

def _load_secrets_toml():
    """Lee .streamlit/secrets.toml directamente (sin depender de Streamlit)."""
    secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'secrets.toml')
    if not os.path.exists(secrets_path):
        return {}
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            # Python < 3.11 sin tomli: parseo manual básico
            result = {}
            current_section = None
            with open(secrets_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        result[current_section] = {}
                    elif '=' in line and current_section:
                        key, val = line.split('=', 1)
                        val = val.strip().strip('"')
                        result[current_section][key.strip()] = val
            return result
    with open(secrets_path, 'rb') as f:
        return tomllib.load(f)

# Prioridad: env vars > Streamlit secrets > secrets.toml directo

# 1. Intentar WHOOP desde variables de entorno (GitHub Actions)
if os.environ.get('WHOOP_CLIENT_ID'):
    WHOOP_CLIENT_ID = os.environ['WHOOP_CLIENT_ID']
    WHOOP_CLIENT_SECRET = os.environ.get('WHOOP_CLIENT_SECRET', '')
    WHOOP_ACCESS_TOKEN = os.environ.get('WHOOP_ACCESS_TOKEN', '')
    WHOOP_REFRESH_TOKEN = os.environ.get('WHOOP_REFRESH_TOKEN', '')
else:
    try:
        # 2. Streamlit Secrets (cuando corre dentro de Streamlit)
        import streamlit as st
        WHOOP_CLIENT_ID = st.secrets["whoop"]["client_id"]
        WHOOP_CLIENT_SECRET = st.secrets["whoop"]["client_secret"]
        WHOOP_ACCESS_TOKEN = st.secrets.get("whoop", {}).get("access_token", "")
        WHOOP_REFRESH_TOKEN = st.secrets.get("whoop", {}).get("refresh_token", "")
    except Exception:
        # 3. Leer secrets.toml directamente (para scripts de terminal)
        _secrets = _load_secrets_toml()
        _whoop = _secrets.get('whoop', {})
        WHOOP_CLIENT_ID = _whoop.get('client_id', '')
        WHOOP_CLIENT_SECRET = _whoop.get('client_secret', '')
        WHOOP_ACCESS_TOKEN = _whoop.get('access_token', '')
        WHOOP_REFRESH_TOKEN = _whoop.get('refresh_token', '')

# Garmin: env vars tienen prioridad, luego Streamlit secrets, luego secrets.toml
GARMIN_EMAIL = os.environ.get('GARMIN_EMAIL', '')
GARMIN_PASSWORD = os.environ.get('GARMIN_PASSWORD', '')
if not GARMIN_EMAIL or not GARMIN_PASSWORD:
    try:
        import streamlit as st
        GARMIN_EMAIL = GARMIN_EMAIL or st.secrets["garmin"]["email"]
        GARMIN_PASSWORD = GARMIN_PASSWORD or st.secrets["garmin"]["password"]
    except Exception:
        _garmin_secrets = _load_secrets_toml()
        _garmin = _garmin_secrets.get('garmin', {})
        GARMIN_EMAIL = GARMIN_EMAIL or _garmin.get('email', '')
        GARMIN_PASSWORD = GARMIN_PASSWORD or _garmin.get('password', '')

WHOOP_REDIRECT_URI = 'http://localhost:8000/callback'

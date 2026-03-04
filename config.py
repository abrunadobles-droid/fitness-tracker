"""
Configuración - Compatible con Streamlit Secrets
"""
import streamlit as st

# Leer de Streamlit Secrets si está disponible, sino usar valores por defecto
try:
    # WHOOP - Credenciales
    WHOOP_CLIENT_ID = st.secrets["whoop"]["client_id"]
    WHOOP_CLIENT_SECRET = st.secrets["whoop"]["client_secret"]
    
    # WHOOP - Tokens (si existen en secrets)
    WHOOP_ACCESS_TOKEN = st.secrets.get("whoop", {}).get("access_token", "")
    WHOOP_REFRESH_TOKEN = st.secrets.get("whoop", {}).get("refresh_token", "")
    
    # Garmin
    GARMIN_EMAIL = st.secrets["garmin"]["email"]
    GARMIN_PASSWORD = st.secrets["garmin"]["password"]
except:
    # Fallback para desarrollo local - configurar via variables de entorno
    import os
    WHOOP_CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID", "")
    WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")
    WHOOP_ACCESS_TOKEN = ""
    WHOOP_REFRESH_TOKEN = ""
    GARMIN_EMAIL = os.environ.get("GARMIN_EMAIL", "")
    GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD", "")

WHOOP_REDIRECT_URI = 'http://localhost:8000/callback'
EXCEL_PATH = '/Users/AntonioXBruna/Desktop/Data_Fitness___Wellness_Tracker.xlsx'

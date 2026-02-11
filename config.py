"""
Configuración - Compatible con Streamlit Secrets
"""
import streamlit as st

# Leer de Streamlit Secrets si está disponible, sino usar valores por defecto
try:
    # WHOOP
    WHOOP_CLIENT_ID = st.secrets["whoop"]["client_id"]
    WHOOP_CLIENT_SECRET = st.secrets["whoop"]["client_secret"]
    
    # Garmin
    GARMIN_EMAIL = st.secrets["garmin"]["email"]
    GARMIN_PASSWORD = st.secrets["garmin"]["password"]
except:
    # Fallback para desarrollo local
    WHOOP_CLIENT_ID = "2c927896-2dd0-4cdc-8a99-f6a3af89992a"
    WHOOP_CLIENT_SECRET = "e7437b1e2200374dd59d01f3f69b613f427f61481d689a866816af369501785b"
    GARMIN_EMAIL = ""
    GARMIN_PASSWORD = ""

WHOOP_REDIRECT_URI = 'http://localhost:8000/callback'
EXCEL_PATH = '/Users/AntonioXBruna/Desktop/Data_Fitness___Wellness_Tracker.xlsx'

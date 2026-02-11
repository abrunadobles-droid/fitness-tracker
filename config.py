"""
Configuración del Fitness Tracker
Actualizar con tus credenciales reales
"""

# ==================== WHOOP API ====================
WHOOP_CONFIG = {
    'client_id': '2c927896-2dd0-4cdc-8a99-f6a3af89992a',
    'client_secret': 'e7437b1e2200374dd59d01f3f69b613f427f61481d689a866816af369501785b',
    'redirect_uri': 'http://localhost:8000/callback',
    'scopes': [
        'offline',
        'read:recovery',
        'read:sleep',
        'read:workout',
        'read:cycles',
        'read:profile'
    ]
}

# Archivo donde se guardarán los tokens
WHOOP_TOKENS_FILE = 'whoop_tokens.json'

# ==================== GARMIN CONNECT ====================
# Garmin no tiene API oficial pública, usaremos la librería garminconnect
GARMIN_CONFIG = {
    'email': 'abruna.dobles@gmail.com',  # TU EMAIL DE GARMIN
    'password': '080987CamDie!'  # TU PASSWORD DE GARMIN
}

# ==================== ARCHIVOS ====================
EXCEL_FILE = '/Users/AntonioXBruna/Desktop/Data_Fitness___Wellness_Tracker.xlsx'
SHEET_NAME = 'Data Fitness & Wellness Tracker'

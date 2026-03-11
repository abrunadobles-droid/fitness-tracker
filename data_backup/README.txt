DATA BACKUP - Garmin + WHOOP integration code
==============================================
Copia de seguridad de todo el codigo de datos.
Estos archivos son los que hacen que la data funcione.

== GARMIN (Steps, Activities, Strength) ==

garmin_client.py      - Cliente principal. Usa garth para tokens.
                        GarminClient.login(), .get_stats_for_date(), .get_activities()
                        Busca tokens en .garmin_tokens/ o st.secrets

garmin_auth.py        - Autenticacion SSO de Garmin (2 fases + MFA)
                        Solo se usa si garth falla

garmin_metrics.py     - Calculador de metricas mensuales desde Garmin

garmin_setup.py       - Formulario Streamlit para conectar cuenta Garmin
                        (guarda credenciales encriptadas en Supabase)

garmin_token_setup.py - Script local para generar tokens de Garmin
                        Se corre una vez: python3 garmin_token_setup.py


== WHOOP (HR Zones, Sleep, Recovery, Resting HR, Consistency) ==

whoop_streamlit.py    - CLIENTE PRINCIPAL para Streamlit Cloud.
                        get_whoop_data(year, month) -> (data_dict, source)
                        Intenta API live primero, si falla usa whoop_cache.json
                        Tokens desde st.secrets["whoop"]

whoop_auth.py         - OAuth2 para WHOOP (refresh preventivo)

whoop_sync.py         - Script local para sincronizar data de WHOOP a cache
                        Se corre: python3 whoop_sync.py
                        Genera/actualiza whoop_cache.json

whoop_client_v2_corrected.py - Cliente WHOOP v2 con timezone corregido

debug_whoop.py        - Script para debug de datos WHOOP

whoop_cache.json      - Cache con datos ENE y FEB 2026 ya descargados


== AUTH + GOALS ==

auth.py               - Login/registro con Supabase
goals_setup.py        - Configuracion de metas por usuario (Supabase)


== COMO SE USA EN EL DASHBOARD ==

El dashboard llama:

1. from garmin_client import GarminClient
   garmin = GarminClient()
   garmin.login()
   stats = garmin.get_stats_for_date(date)     # -> steps
   activities = garmin.get_activities(start, end) # -> activities, strength

2. from whoop_streamlit import get_whoop_data
   whoop, source = get_whoop_data(year, month)
   whoop['hr_zones_1_3_hours']     # horas en zonas 1-3
   whoop['hr_zones_4_5_hours']     # horas en zonas 4-5
   whoop['sleep_hours_avg']        # promedio sueno
   whoop['avg_recovery_score']     # recovery score
   whoop['avg_resting_hr']         # resting HR
   whoop['avg_sleep_consistency']  # consistencia sueno

import requests
import time
from datetime import datetime, timedelta
import streamlit as st
import os
import json

class WhoopClientV2:
    def __init__(self):
        self.base_url = "https://api.whoop.com/v2"
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.client_id = None
        self.client_secret = None
        self._load_credentials()
        self._check_and_refresh_token()  # 🔥 NUEVO: Check preventivo
    
    def _load_credentials(self):
        """Cargar credenciales desde Streamlit secrets o variables de entorno"""
        try:
            # Intentar desde Streamlit secrets primero
            self.access_token = st.secrets["whoop"]["access_token"]
            self.refresh_token = st.secrets["whoop"]["refresh_token"]
            self.client_id = st.secrets["whoop"]["client_id"]
            self.client_secret = st.secrets["whoop"]["client_secret"]
            
            # Token expiry (si existe)
            token_expiry = st.secrets.get("WHOOP_TOKEN_EXPIRES_AT")
            if token_expiry:
                self.token_expires_at = datetime.fromisoformat(token_expiry)
            
            print(f"✅ [WHOOP] Credenciales cargadas desde Streamlit secrets")
            
        except Exception as e:
            print(f"❌ [WHOOP] Error loading from secrets: {str(e)}")
            print(f"❌ [WHOOP] Exception type: {type(e).__name__}")
            # Fallback a variables de entorno
            self.access_token = os.getenv('WHOOP_ACCESS_TOKEN')
            self.refresh_token = os.getenv('WHOOP_REFRESH_TOKEN')
            self.client_id = os.getenv('WHOOP_CLIENT_ID')
            self.client_secret = os.getenv('WHOOP_CLIENT_SECRET')
            
            if not all([self.access_token, self.refresh_token, self.client_id, self.client_secret]):
                raise Exception("WHOOP credentials not found in Streamlit secrets or env vars")
            
            print(f"⚠️ [WHOOP] Credenciales cargadas desde variables de entorno (fallback)")
    
    def _check_and_refresh_token(self):
        """🔥 NUEVO: Verificar edad del token y refrescar preventivamente"""
        try:
            # Si no tenemos timestamp, asumir que está viejo
            if not self.token_expires_at:
                print(f"⚠️ [WHOOP] No hay timestamp - refrescando por seguridad")
                self._refresh_access_token()
                return
            
            # Calcular tiempo restante
            now = datetime.now()
            time_remaining = (self.token_expires_at - now).total_seconds() / 60  # minutos
            
            print(f"🕐 [WHOOP] Token expira en {time_remaining:.1f} minutos")
            
            # Si quedan menos de 10 minutos → refresh preventivo
            if time_remaining < 10:
                print(f"🔄 [WHOOP] REFRESH PREVENTIVO (quedan {time_remaining:.1f} min)")
                self._refresh_access_token()
            else:
                print(f"✅ [WHOOP] Token OK (quedan {time_remaining:.1f} min)")
                
        except Exception as e:
            print(f"⚠️ [WHOOP] Error verificando token: {e}")
            print(f"🔄 [WHOOP] Intentando refresh por seguridad...")
            try:
                self._refresh_access_token()
            except Exception as refresh_error:
                print(f"❌ [WHOOP] Refresh falló: {refresh_error}")
    
    def _refresh_access_token(self):
        """Refrescar el access token usando el refresh token"""
        print(f"🔄 [WHOOP] Iniciando refresh de token...")
        print(f"🔑 [WHOOP] Refresh token: {self.refresh_token[:20]}...")
        
        url = "https://api.whoop.com/oauth/token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            print(f"📡 [WHOOP] Respuesta refresh: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Actualizar tokens
                old_access = self.access_token[:20] if self.access_token else "None"
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data.get("refresh_token", self.refresh_token)
                
                # Calcular expiración (1 hora por defecto)
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                print(f"✅ [WHOOP] Tokens actualizados exitosamente")
                print(f"   Old access: {old_access}...")
                print(f"   New access: {self.access_token[:20]}...")
                print(f"   Expira: {self.token_expires_at.isoformat()}")
                
                # 🔥 CRÍTICO: Guardar nuevos tokens
                self._save_tokens_to_file()
                
            else:
                print(f"❌ [WHOOP] Error {response.status_code}: {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ [WHOOP] Exception durante refresh: {str(e)}")
            raise
    
    def _save_tokens_to_file(self):
        """🔥 NUEVO: Guardar tokens en archivo local para persistencia"""
        try:
            token_file = os.path.expanduser("~/.whoop_tokens.json")
            token_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at.isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"💾 [WHOOP] Tokens guardados en {token_file}")
            print(f"   ⚠️ IMPORTANTE: Copiar estos tokens a Streamlit Secrets:")
            print(f"   WHOOP_ACCESS_TOKEN = {self.access_token}")
            print(f"   WHOOP_REFRESH_TOKEN = {self.refresh_token}")
            print(f"   WHOOP_TOKEN_EXPIRES_AT = {self.token_expires_at.isoformat()}")
            
        except Exception as e:
            print(f"⚠️ [WHOOP] No se pudieron guardar tokens: {e}")
    
    def _make_request(self, endpoint, params=None):
        """Realizar petición a la API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 401:
                print(f"🔄 [WHOOP] 401 detectado - token expirado, refrescando...")
                self._refresh_access_token()
                # Reintentar con nuevo token
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.get(url, headers=headers, params=params, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"❌ [WHOOP] Error en petición a {endpoint}: {str(e)}")
            raise
    
    def get_sleep_data(self, start_date, end_date):
        """Obtener datos de sueño"""
        print(f"📊 [WHOOP] Obteniendo sleep data: {start_date} a {end_date}")
        params = {
            "start": start_date,
            "end": end_date
        }
        return self._make_request("activity/sleep", params)
    
    def get_cycle_data(self, start_date, end_date):
        """Obtener datos de ciclos (recovery, strain, etc)"""
        print(f"📊 [WHOOP] Obteniendo cycle data: {start_date} a {end_date}")
        params = {
            "start": start_date,
            "end": end_date
        }
        return self._make_request("cycle", params)
    
    def get_workout_data(self, start_date, end_date):
        """Obtener datos de entrenamientos"""
        print(f"📊 [WHOOP] Obteniendo workout data: {start_date} a {end_date}")
        params = {
            "start": start_date,
            "end": end_date
        }
        return self._make_request("activity/workout", params)

    def get_monthly_summary(self, year, month):
        """Obtener resumen mensual con métricas calculadas"""
        print(f"📊 [WHOOP] Calculando resumen mensual: {year}-{month:02d}")
        
        from datetime import datetime
        import calendar
        
        # Calcular fechas del mes
        first_day = datetime(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num, 23, 59, 59)
        
        start_date = first_day.isoformat() + "Z"
        end_date = last_day.isoformat() + "Z"
        
        # Obtener datos
        sleep_data = self.get_sleep_data(start_date, end_date)
        cycle_data = self.get_cycle_data(start_date, end_date)
        workout_data = self.get_workout_data(start_date, end_date)
        
        # Calcular métricas
        total_sleep_hours = 0
        days_before_930 = 0
        sleep_count = 0
        
        for sleep in sleep_data.get('records', []):
            # Sleep duration en horas
            duration_ms = sleep.get('score', {}).get('sleepNeeded', 0)
            hours = duration_ms / (1000 * 60 * 60)
            total_sleep_hours += hours
            sleep_count += 1
            
            # Check si durmió antes de 9:30 PM
            sleep_start = sleep.get('start', '')
            if sleep_start:
                from datetime import datetime
                start_time = datetime.fromisoformat(sleep_start.replace('Z', '+00:00'))
                # Considerar que durmió "antes de 9:30 PM" si se durmió entre 6 PM y 9:30 PM
                hour = start_time.hour
                minute = start_time.minute
                if (hour == 18 and minute >= 0) or (hour == 19) or (hour == 20) or (hour == 21 and minute <= 30):
                    days_before_930 += 1
        
        avg_sleep_hours = total_sleep_hours / sleep_count if sleep_count > 0 else 0
        
        # Calcular HR zones de los workouts
        total_zone_1_3_seconds = 0
        total_zone_4_5_seconds = 0
        
        for workout in workout_data.get('records', []):
            score = workout.get('score', {})
            zones = score.get('zone_duration', {})
            
            # Zones 0-2 son zonas bajas (1-3)
            zone_0 = zones.get('zone_zero_milli', 0) / 1000
            zone_1 = zones.get('zone_one_milli', 0) / 1000
            zone_2 = zones.get('zone_two_milli', 0) / 1000
            total_zone_1_3_seconds += zone_0 + zone_1 + zone_2
            
            # Zones 3-4 son zonas altas (4-5)
            zone_3 = zones.get('zone_three_milli', 0) / 1000
            zone_4 = zones.get('zone_four_milli', 0) / 1000
            zone_5 = zones.get('zone_five_milli', 0) / 1000
            total_zone_4_5_seconds += zone_3 + zone_4 + zone_5
        
        summary = {
            'avg_sleep_hours': avg_sleep_hours,
            'days_sleep_before_930pm': days_before_930,
            'hr_zones_1_3_hours': total_zone_1_3_seconds / 3600,
            'hr_zones_4_5_hours': total_zone_4_5_seconds / 3600
        }
        
        print(f"✅ [WHOOP] Resumen calculado: {summary}")
        return summary


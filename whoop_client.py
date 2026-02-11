"""
Cliente para obtener datos de WHOOP API
"""

import requests
from datetime import datetime, timedelta
from whoop_auth import WhoopAuth


class WhoopClient:
    def __init__(self):
        self.auth = WhoopAuth()
        self.base_url = 'https://api.prod.whoop.com/developer/v1'
    
    def _get_headers(self):
        """Genera headers con token de autenticación"""
        token = self.auth.get_access_token()
        return {'Authorization': f'Bearer {token}'}
    
    def _make_request(self, endpoint, params=None):
        """Realiza request a la API con manejo de errores"""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # Si es 401, intentar refrescar token
            if response.status_code == 401:
                print("Token expirado, refrescando...")
                self.auth.refresh_access_token()
                headers = self._get_headers()
                response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP {response.status_code} en {endpoint}")
            print(f"Response: {response.text}")
            raise
    
    def get_profile(self):
        """Obtiene información del perfil del usuario"""
        return self._make_request('user/profile/basic')
    
    def get_recovery_for_date(self, date=None):
        """
        Obtiene datos de recuperación para una fecha específica
        date: datetime object o None para hoy
        """
        if date is None:
            date = datetime.now()
        
        # WHOOP API usa formato: YYYY-MM-DD
        start_date = date.strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            'start': start_date,
            'end': end_date
        }
        
        data = self._make_request('recovery', params=params)
        return data.get('records', [])
    
    def get_sleep_for_date(self, date=None):
        """
        Obtiene datos de sueño para una fecha específica
        """
        if date is None:
            date = datetime.now()
        
        start_date = date.strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            'start': start_date,
            'end': end_date
        }
        
        data = self._make_request('activity/sleep', params=params)
        return data.get('records', [])
    
    def get_workouts_for_date(self, date=None):
        """
        Obtiene workouts para una fecha específica
        """
        if date is None:
            date = datetime.now()
        
        start_date = date.strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            'start': start_date,
            'end': end_date
        }
        
        data = self._make_request('activity/workout', params=params)
        return data.get('records', [])
    
    def get_cycle_for_date(self, date=None):
        """
        Obtiene el ciclo (día completo de datos) para una fecha específica
        """
        if date is None:
            date = datetime.now()
        
        start_date = date.strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            'start': start_date,
            'end': end_date
        }
        
        data = self._make_request('cycle', params=params)
        return data.get('records', [])
    
    def get_monthly_summary(self, year, month):
        """
        Obtiene resumen mensual de datos WHOOP
        
        Returns:
            dict con promedios mensuales
        """
        # Construir rango de fechas del mes
        from calendar import monthrange
        
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)
        
        params = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
        }
        
        # Obtener datos
        recovery_data = self._make_request('recovery', params=params)
        sleep_data = self._make_request('activity/sleep', params=params)
        workout_data = self._make_request('activity/workout', params=params)
        
        # Procesar datos
        summary = {
            'total_workouts': 0,
            'avg_recovery_score': 0,
            'avg_sleep_hours': 0,
            'avg_hrv': 0,
            'avg_resting_hr': 0,
            'total_strain': 0
        }
        
        # Recovery
        if recovery_data.get('records'):
            recoveries = recovery_data['records']
            summary['avg_recovery_score'] = sum(r['score']['recovery_score'] for r in recoveries if r.get('score')) / len(recoveries)
            summary['avg_hrv'] = sum(r['score']['hrv_rmssd_milli'] for r in recoveries if r.get('score')) / len(recoveries)
            summary['avg_resting_hr'] = sum(r['score']['resting_heart_rate'] for r in recoveries if r.get('score')) / len(recoveries)
        
        # Sleep
        if sleep_data.get('records'):
            sleeps = sleep_data['records']
            # Convertir milisegundos a horas
            summary['avg_sleep_hours'] = sum(s['score']['stage_summary']['total_in_bed_time_milli'] for s in sleeps if s.get('score')) / len(sleeps) / 3600000
        
        # Workouts
        if workout_data.get('records'):
            summary['total_workouts'] = len(workout_data['records'])
        
        return summary


def test_whoop_connection():
    """Función de prueba para verificar conexión con WHOOP"""
    print("\n" + "="*60)
    print("PRUEBA DE CONEXIÓN WHOOP")
    print("="*60)
    
    client = WhoopClient()
    
    # Verificar autenticación
    if not client.auth.is_authenticated():
        print("\n⚠️  No hay autenticación. Iniciando proceso...\n")
        client.auth.authorize()
    
    # Obtener perfil
    print("\n1. Obteniendo perfil...")
    try:
        profile = client.get_profile()
        print(f"   ✅ Usuario: {profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')}")
        print(f"   ✅ User ID: {profile.get('user_id', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Obtener recovery de hoy
    print("\n2. Obteniendo datos de recuperación...")
    try:
        recovery = client.get_recovery_for_date()
        if recovery:
            rec = recovery[0]
            print(f"   ✅ Recovery Score: {rec['score']['recovery_score']}")
            print(f"   ✅ HRV: {rec['score']['hrv_rmssd_milli']} ms")
            print(f"   ✅ Resting HR: {rec['score']['resting_heart_rate']} bpm")
        else:
            print("   ⚠️  No hay datos de recovery para hoy")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Obtener sleep
    print("\n3. Obteniendo datos de sueño...")
    try:
        sleep = client.get_sleep_for_date()
        if sleep:
            slp = sleep[0]
            hours = slp['score']['stage_summary']['total_in_bed_time_milli'] / 3600000
            print(f"   ✅ Horas de sueño: {hours:.1f}h")
            print(f"   ✅ Sleep Performance: {slp['score']['sleep_performance_percentage']}%")
        else:
            print("   ⚠️  No hay datos de sueño para hoy")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ PRUEBA COMPLETADA")
    print("="*60 + "\n")
    
    return True


if __name__ == '__main__':
    test_whoop_connection()

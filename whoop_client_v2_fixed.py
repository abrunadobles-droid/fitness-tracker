"""
Cliente WHOOP API v2 - Con paginación correcta
"""

import requests
from datetime import datetime, timedelta
from whoop_auth import WhoopAuth


class WhoopClientV2:
    def __init__(self):
        self.auth = WhoopAuth()
        self.base_url = 'https://api.prod.whoop.com/developer/v2'
    
    def _get_headers(self):
        token = self.auth.get_access_token()
        return {'Authorization': f'Bearer {token}'}
    
    def _make_request(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                print("      Token expirado, refrescando...")
                self.auth.refresh_access_token()
                headers = self._get_headers()
                response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            print(f"      Error HTTP {response.status_code} en {endpoint}")
            print(f"      Response: {response.text}")
            raise
    
    def get_profile(self):
        return self._make_request('user/profile/basic')
    
    def get_body_measurements(self):
        return self._make_request('user/measurement/body')
    
    def get_all_records(self, endpoint, start_date, end_date):
        """
        Obtiene TODOS los registros paginando automáticamente
        """
        all_records = []
        next_token = None
        page = 1
        
        params = {
            'start': start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'end': end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'limit': 25  # Máximo permitido
        }
        
        while True:
            if next_token:
                params['nextToken'] = next_token
            
            try:
                data = self._make_request(endpoint, params=params)
                
                if 'records' in data and data['records']:
                    all_records.extend(data['records'])
                    print(f"         Página {page}: {len(data['records'])} registros")
                    page += 1
                
                # Si hay más páginas, continuar
                if 'next_token' in data and data['next_token']:
                    next_token = data['next_token']
                else:
                    break
                    
            except Exception as e:
                print(f"         Error en paginación: {e}")
                break
        
        return all_records
    
    def get_monthly_summary(self, year, month):
        """
        Obtiene resumen mensual completo con paginación
        """
        from calendar import monthrange
        
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        summary = {
            'sleep': [],
            'recovery': [],
            'workouts': [],
            'avg_sleep_hours': 0,
            'avg_weight_kg': 0,
            'days_sleep_before_930pm': 0
        }
        
        # Sleep (con paginación)
        print("      🛌 Obteniendo datos de sueño...")
        try:
            summary['sleep'] = self.get_all_records('activity/sleep', start_date, end_date)
            
            if summary['sleep']:
                total_sleep_ms = 0
                days_before_930 = 0
                
                for sleep in summary['sleep']:
                    if sleep.get('score') and sleep['score'].get('stage_summary'):
                        total_in_bed = sleep['score']['stage_summary'].get('total_in_bed_time_milli', 0)
                        total_sleep_ms += total_in_bed
                        
                        # Hora de dormir
                        start_time_str = sleep.get('start', '')
                        if start_time_str:
                            # Formato: "2026-01-15T21:30:00.000Z"
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                            # Verificar si es antes de 9:30 PM (21:30)
                            if start_time.hour < 21 or (start_time.hour == 21 and start_time.minute < 30):
                                days_before_930 += 1
                
                summary['avg_sleep_hours'] = (total_sleep_ms / len(summary['sleep'])) / 3600000
                summary['days_sleep_before_930pm'] = days_before_930
                
                print(f"         ✅ {len(summary['sleep'])} noches procesadas")
        
        except Exception as e:
            print(f"         ⚠️  Error: {e}")
        
        # Recovery
        print("      💪 Obteniendo datos de recovery...")
        try:
            summary['recovery'] = self.get_all_records('recovery', start_date, end_date)
            print(f"         ✅ {len(summary['recovery'])} registros")
        except Exception as e:
            print(f"         ⚠️  Error: {e}")
        
        # Workouts
        print("      🏃 Obteniendo workouts...")
        try:
            summary['workouts'] = self.get_all_records('activity/workout', start_date, end_date)
            print(f"         ✅ {len(summary['workouts'])} workouts")
        except Exception as e:
            print(f"         ⚠️  Error: {e}")
        
        # Peso
        print("      ⚖️  Obteniendo peso...")
        try:
            body = self.get_body_measurements()
            if body and 'weight_kilogram' in body:
                summary['avg_weight_kg'] = body['weight_kilogram']
                print(f"         ✅ Peso: {body['weight_kilogram']} kg")
        except Exception as e:
            print(f"         ⚠️  No disponible")
        
        return summary

"""
Cliente WHOOP API v2 - CORREGIDO con zona horaria y sleep real
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
        all_records = []
        next_token = None
        page = 1
        
        params = {
            'start': start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'end': end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'limit': 25
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
                
                if 'next_token' in data and data['next_token']:
                    next_token = data['next_token']
                else:
                    break
                    
            except Exception as e:
                print(f"         Error en paginación: {e}")
                break
        
        return all_records
    
    def get_monthly_summary(self, year, month):
        from calendar import monthrange
        
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        summary = {
            'sleep': [],
            'recovery': [],
            'workouts': [],
            'avg_sleep_hours': 0,
            'avg_sleep_performance': 0,
            'avg_sleep_consistency': 0,
            'avg_hrv': 0,
            'avg_recovery_score': 0,
            'days_sleep_before_930pm': 0,
            'avg_time_hr_zone_1_3': 0,
            'avg_time_hr_zone_4_5': 0
        }
        
        # Sleep
        print("      🛌 Obteniendo datos de sueño...")
        try:
            summary['sleep'] = self.get_all_records('activity/sleep', start_date, end_date)
            
            if summary['sleep']:
                total_sleep_ms = 0
                total_performance = 0
                total_consistency = 0
                days_before_930 = 0
                
                for sleep in summary['sleep']:
                    if sleep.get('score') and sleep['score'].get('stage_summary'):
                        stages = sleep['score']['stage_summary']
                        
                        # CORRECCIÓN 1: Usar tiempo REAL dormido (no in bed)
                        actual_sleep_ms = (
                            stages.get('total_light_sleep_time_milli', 0) +
                            stages.get('total_slow_wave_sleep_time_milli', 0) +
                            stages.get('total_rem_sleep_time_milli', 0)
                        )
                        total_sleep_ms += actual_sleep_ms
                        
                        # Sleep performance y consistency
                        total_performance += sleep['score'].get('sleep_performance_percentage', 0)
                        total_consistency += sleep['score'].get('sleep_consistency_percentage', 0)
                        
                        # CORRECCIÓN 2: Convertir a hora local correctamente
                        start_time_str = sleep.get('start', '')
                        timezone_offset = sleep.get('timezone_offset', '-06:00')
                        
                        if start_time_str:
                            # Parse UTC time
                            utc_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                            
                            # Aplicar offset (ej: -06:00)
                            offset_hours = int(timezone_offset.split(':')[0])
                            offset_minutes = int(timezone_offset.split(':')[1]) if ':' in timezone_offset else 0
                            offset = timedelta(hours=offset_hours, minutes=offset_minutes)
                            
                            local_time = utc_time + offset
                            
                            # Verificar si es antes de 9:30 PM (21:30)
                            if local_time.hour < 21 or (local_time.hour == 21 and local_time.minute < 30):
                                days_before_930 += 1
                
                num_sleeps = len(summary['sleep'])
                summary['avg_sleep_hours'] = (total_sleep_ms / num_sleeps) / 3600000
                summary['avg_sleep_performance'] = total_performance / num_sleeps
                summary['avg_sleep_consistency'] = total_consistency / num_sleeps
                summary['days_sleep_before_930pm'] = days_before_930
                
                print(f"         ✅ {num_sleeps} noches procesadas")
        
        except Exception as e:
            print(f"         ⚠️  Error: {e}")
        
        # Recovery
        print("      💪 Obteniendo datos de recovery...")
        try:
            summary['recovery'] = self.get_all_records('recovery', start_date, end_date)
            
            if summary['recovery']:
                total_hrv = 0
                total_recovery = 0
                
                for rec in summary['recovery']:
                    if rec.get('score'):
                        total_hrv += rec['score'].get('hrv_rmssd_milli', 0)
                        total_recovery += rec['score'].get('recovery_score', 0)
                
                num_recovery = len(summary['recovery'])
                summary['avg_hrv'] = total_hrv / num_recovery
                summary['avg_recovery_score'] = total_recovery / num_recovery
                
            print(f"         ✅ {len(summary['recovery'])} registros")
        except Exception as e:
            print(f"         ⚠️  Error: {e}")
        
        # Workouts (con HR zones)
        print("      🏃 Obteniendo workouts...")
        try:
            summary['workouts'] = self.get_all_records('activity/workout', start_date, end_date)
            
            if summary['workouts']:
                total_zone_1_3 = 0
                total_zone_4_5 = 0
                
                for workout in summary['workouts']:
                    if workout.get('score') and workout['score'].get('zone_durations'):
                        zones = workout['score']['zone_durations']
                        
                        # Zones 1-3 (low-moderate intensity)
                        total_zone_1_3 += (
                            zones.get('zone_one_milli', 0) +
                            zones.get('zone_two_milli', 0) +
                            zones.get('zone_three_milli', 0)
                        )
                        
                        # Zones 4-5 (high intensity)
                        total_zone_4_5 += (
                            zones.get('zone_four_milli', 0) +
                            zones.get('zone_five_milli', 0)
                        )
                
                num_workouts = len(summary['workouts'])
                # Convertir a minutos
                summary['avg_time_hr_zone_1_3'] = (total_zone_1_3 / num_workouts) / 60000
                summary['avg_time_hr_zone_4_5'] = (total_zone_4_5 / num_workouts) / 60000
                
            print(f"         ✅ {len(summary['workouts'])} workouts")
        except Exception as e:
            print(f"         ⚠️  Error: {e}")
        
        return summary

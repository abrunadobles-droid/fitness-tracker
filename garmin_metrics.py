"""
Garmin Metrics Calculator
Calcula todas las métricas del dashboard usando solo datos de Garmin
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
import calendar

class GarminMetrics:
    def __init__(self, email, password):
        self.garmin = Garmin(email, password)
        self.garmin.login()
        print("✅ [GARMIN] Login exitoso")
    
    def get_monthly_summary(self, year, month):
        """Calcular resumen mensual completo"""
        print(f"📊 [GARMIN] Calculando métricas para {year}-{month:02d}")
        
        # Fechas del mes
        first_day = datetime(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        
        total_steps = 0
        total_sleep_seconds = 0
        days_before_930 = 0
        days_with_data = 0
        
        # Iterar por cada día del mes
        for day in range(1, last_day_num + 1):
            date = datetime(year, month, day)
            date_str = date.strftime("%Y-%m-%d")
            
            # Si es fecha futura, saltar
            if date > datetime.now():
                continue
            
            try:
                # 1. USER SUMMARY (steps)
                summary = self.garmin.get_user_summary(date_str)
                if summary:
                    total_steps += summary.get('totalSteps', 0)
                    days_with_data += 1
                
                # 2. SLEEP DATA
                sleep = self.garmin.get_sleep_data(date_str)
                if sleep and 'dailySleepDTO' in sleep:
                    sleep_dto = sleep['dailySleepDTO']
                    
                    # Sleep duration
                    sleep_seconds = sleep_dto.get('sleepTimeSeconds', 0)
                    total_sleep_seconds += sleep_seconds
                    
                    # Sleep before 9:30 PM
                    sleep_start_ts = sleep_dto.get('sleepStartTimestampLocal')
                    if sleep_start_ts:
                        # Convertir timestamp a hora local
                        sleep_start = datetime.fromtimestamp(sleep_start_ts / 1000)
                        hour = sleep_start.hour
                        minute = sleep_start.minute
                        
                        # Contar si se durmió antes de 21:30
                        if hour < 21 or (hour == 21 and minute <= 30):
                            days_before_930 += 1
                
            except Exception as e:
                print(f"⚠️ [GARMIN] Error día {date_str}: {e}")
                continue
        
        # 3. ACTIVITIES del mes
        activities = self.garmin.get_activities_by_date(
            first_day.strftime("%Y-%m-%d"),
            datetime(year, month, last_day_num).strftime("%Y-%m-%d")
        )
        
        total_activities = len(activities)
        strength_count = 0
        
        # HR Zones calculation
        total_zone_1_3_seconds = 0
        total_zone_4_5_seconds = 0
        
        for activity in activities:
            # Contar strength training
            activity_type = activity.get('activityType', {}).get('typeKey', '')
            if 'strength' in activity_type.lower() or 'training' in activity_type.lower():
                strength_count += 1
            
            # Obtener HR zones detallados de Garmin
            activity_id = activity.get('activityId')
            if activity_id:
                try:
                    hr_zones = self.garmin.get_activity_hr_in_timezones(activity_id)
                    
                    print(f"  Activity {activity_id}: {len(hr_zones) if hr_zones else 0} zones")
                    if hr_zones and isinstance(hr_zones, list):
                        for zone in hr_zones:
                            zone_num = zone.get('zoneNumber', 0)
                            secs_in_zone = zone.get('secsInZone', 0)
                            
                            # Zonas 1-3 → total_zone_1_3
                            # Zonas 4-5 → total_zone_4_5
                            if zone_num in [1, 2, 3]:
                                total_zone_1_3_seconds += secs_in_zone
                            elif zone_num in [4, 5]:
                                total_zone_4_5_seconds += secs_in_zone
                except Exception as e:
                    print(f"⚠️ [GARMIN] Error obteniendo HR zones para actividad {activity_id}: {e}")
                    continue
        
        # Calcular promedios
        steps_avg = round(total_steps / days_with_data) if days_with_data > 0 else 0
        sleep_hours_avg = round(total_sleep_seconds / days_with_data / 3600, 1) if days_with_data > 0 else 0
        hr_zones_1_3_hours = round(total_zone_1_3_seconds / 3600, 1)
        hr_zones_4_5_hours = round(total_zone_4_5_seconds / 3600, 1)
        
        summary = {
            'steps_avg': steps_avg,
            'activities': total_activities,
            'strength': strength_count,
            'sleep_hours_avg': sleep_hours_avg,
            'days_before_930': days_before_930,
            'hr_zones_1_3_hours': hr_zones_1_3_hours,
            'hr_zones_4_5_hours': hr_zones_4_5_hours
        }
        
        print(f"✅ [GARMIN] Resumen calculado: {summary}")
        print(f"   Zone 1-3: {total_zone_1_3_seconds}s = {hr_zones_1_3_hours}h")
        print(f"   Zone 4-5: {total_zone_4_5_seconds}s = {hr_zones_4_5_hours}h")
        return summary

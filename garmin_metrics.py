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
            
            # Calcular HR zones usando MAX HR PERSONAL (~185 bpm)
            avg_hr = activity.get('averageHR')
            duration = activity.get('duration', 0)  # en segundos
            
            # Usar el max HR más alto observado como referencia personal
            MAX_HR_PERSONAL = 195
            
            if avg_hr and duration > 0:
                # Calcular % del max HR personal
                hr_percentage = (avg_hr / MAX_HR_PERSONAL) * 100
                
                # Clasificar en zonas
                # Zona 1-3: 50-80% del max HR personal (98-156 bpm)
                # Zona 4-5: 80-100% del max HR personal (157-195 bpm)
                if hr_percentage <= 80:
                    total_zone_1_3_seconds += duration
                else:
                    total_zone_4_5_seconds += duration
        
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
        return summary

"""
Cliente de Garmin Connect
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
from calendar import monthrange
import os
import config

TOKENSTORE = os.path.join(os.path.dirname(__file__), '.garmin_tokens')

class GarminClient:
    def __init__(self):
        self.client = None

    def login(self):
        self.client = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)
        try:
            # Intentar usar tokens guardados primero
            if os.path.exists(TOKENSTORE):
                self.client.login(tokenstore=TOKENSTORE)
            else:
                self.client.login()
                self.client.garth.dump(TOKENSTORE)
        except Exception:
            # Si los tokens expiraron, hacer login fresco
            self.client.login()
            self.client.garth.dump(TOKENSTORE)

    def get_stats_for_date(self, date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        return self.client.get_stats(date_str)

    def get_sleep_data(self, date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        return self.client.get_sleep_data(date_str)

    def get_sleep_duration_hours(self, date=None):
        """Obtiene las horas de sueño para una fecha"""
        try:
            sleep = self.get_sleep_data(date)
            if sleep and 'dailySleepDTO' in sleep:
                secs = sleep['dailySleepDTO'].get('sleepTimeSeconds', 0)
                return round(secs / 3600, 1)
        except Exception:
            pass
        return 0.0

    def get_activities(self, start_date=None, end_date=None, limit=10):
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        start = 0
        activities = self.client.get_activities(start, limit)
        return activities

    def get_monthly_summary(self, year, month):
        """Calcula resumen mensual de métricas Garmin"""
        first_day = datetime(year, month, 1)
        last_day_num = monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num)

        total_steps = 0
        total_sleep_secs = 0
        days_with_data = 0
        strength_count = 0

        current_date = first_day
        while current_date <= min(last_day, datetime.now()):
            try:
                stats = self.get_stats_for_date(current_date)
                if stats and stats.get('totalSteps'):
                    total_steps += stats['totalSteps']
                    days_with_data += 1
            except Exception:
                pass

            try:
                sleep = self.client.get_sleep_data(current_date.strftime('%Y-%m-%d'))
                if sleep and 'dailySleepDTO' in sleep:
                    total_sleep_secs += sleep['dailySleepDTO'].get('sleepTimeSeconds', 0)
            except Exception:
                pass

            current_date += timedelta(days=1)

        # Actividades del mes
        activities = self.client.get_activities_by_date(
            first_day.strftime('%Y-%m-%d'),
            last_day.strftime('%Y-%m-%d')
        )

        for activity in activities:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            if 'strength' in activity_type or 'training' in activity_type:
                strength_count += 1

        return {
            'avg_daily_steps': round(total_steps / days_with_data) if days_with_data > 0 else 0,
            'total_active_calories': 0,
            'avg_sleep_hours': round(total_sleep_secs / days_with_data / 3600, 1) if days_with_data > 0 else 0,
            'strength_training_sessions': strength_count,
        }


def test_garmin_connection():
    """Prueba la conexión con Garmin Connect"""
    try:
        client = GarminClient()
        client.login()
        stats = client.get_stats_for_date()
        if stats:
            print(f"✅ Garmin Connect OK - Steps hoy: {stats.get('totalSteps', 0):,}")
            return True
        else:
            print("⚠️  Garmin conectado pero sin datos hoy")
            return True
    except Exception as e:
        print(f"❌ Error conectando a Garmin: {e}")
        return False

"""
Cliente de Garmin Connect - Multi-usuario
Lee credenciales y tokens de Supabase por usuario.
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
from calendar import monthrange
from crypto import decrypt
from auth import get_supabase


class GarminClient:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = None

    def login(self):
        """Login usando tokens cacheados (rapido) o password (lento)."""
        supabase = get_supabase()
        result = supabase.table("garmin_connections").select("*").eq(
            "user_id", self.user_id
        ).execute()

        if not result.data:
            raise Exception("No hay cuenta de Garmin conectada")

        conn = result.data[0]
        garmin_email = conn["garmin_email"]
        garmin_password = decrypt(conn["garmin_password_encrypted"])
        stored_tokens = conn.get("garmin_tokens")

        self.client = Garmin(garmin_email, garmin_password)

        # Intentar tokens cacheados primero (rapido)
        if stored_tokens:
            try:
                self.client.garth.loads(stored_tokens)
                # Verificar que los tokens funcionan
                self.client.display_name = self.client.garth.profile["displayName"]
                self.client.full_name = self.client.garth.profile["fullName"]
                return  # Exito con tokens
            except Exception:
                pass  # Tokens expiraron, hacer login con password

        # Login con password (lento) - usar garth directamente para evitar
        # que prompt_mfa=input() falle en el servidor
        self.client.garth.login(
            garmin_email,
            garmin_password,
            prompt_mfa=lambda: (_ for _ in ()).throw(
                Exception("MFA requerido - reconecta Garmin desde la app")
            ),
        )
        self.client.display_name = self.client.garth.profile["displayName"]
        self.client.full_name = self.client.garth.profile["fullName"]

        # Guardar tokens nuevos en Supabase
        new_tokens = self.client.garth.dumps()
        supabase.table("garmin_connections").update({
            "garmin_tokens": new_tokens,
            "tokens_updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", self.user_id).execute()

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
        """Obtiene las horas de sueno para una fecha"""
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
        """Calcula resumen mensual de metricas Garmin"""
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

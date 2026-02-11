"""
Cliente para obtener datos de Garmin Connect
Usa la librería garminconnect (no oficial)
"""

from datetime import datetime, timedelta
from garminconnect import Garmin, GarminConnectConnectionError, GarminConnectAuthenticationError
from config import GARMIN_CONFIG
import json


class GarminClient:
    def __init__(self):
        self.email = GARMIN_CONFIG.get('email')
        self.password = GARMIN_CONFIG.get('password')
        self.client = None
        
        if not self.email or not self.password:
            raise ValueError("Debes configurar GARMIN_CONFIG en config.py con tu email y password")
    
    def login(self):
        """Inicia sesión en Garmin Connect"""
        try:
            self.client = Garmin(self.email, self.password)
            self.client.login()
            print("✅ Login exitoso en Garmin Connect")
            return True
        except GarminConnectAuthenticationError as e:
            print(f"❌ Error de autenticación: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_stats_for_date(self, date=None):
        """
        Obtiene estadísticas para una fecha específica
        date: datetime object o None para hoy
        """
        if not self.client:
            self.login()
        
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        try:
            stats = self.client.get_stats(date_str)
            return stats
        except Exception as e:
            print(f"Error obteniendo stats de Garmin: {e}")
            return None
    
    def get_steps(self, date=None):
        """Obtiene pasos para una fecha"""
        stats = self.get_stats_for_date(date)
        if stats:
            return stats.get('totalSteps', 0)
        return 0
    
    def get_active_calories(self, date=None):
        """Obtiene calorías activas para una fecha"""
        stats = self.get_stats_for_date(date)
        if stats:
            return stats.get('activeKilocalories', 0)
        return 0
    
    def get_sleep_data(self, date=None):
        """
        Obtiene datos de sueño para una fecha
        Nota: Garmin mide el sueño de la noche anterior
        """
        if not self.client:
            self.login()
        
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        try:
            sleep_data = self.client.get_sleep_data(date_str)
            return sleep_data
        except Exception as e:
            print(f"Error obteniendo sleep data: {e}")
            return None
    
    def get_sleep_duration_hours(self, date=None):
        """Obtiene duración del sueño en horas"""
        sleep_data = self.get_sleep_data(date)
        if sleep_data and 'dailySleepDTO' in sleep_data:
            # Convertir segundos a horas
            seconds = sleep_data['dailySleepDTO'].get('sleepTimeSeconds', 0)
            return seconds / 3600
        return 0
    
    def get_activities(self, start_date=None, end_date=None, limit=10):
        """
        Obtiene actividades (workouts) en un rango de fechas
        """
        if not self.client:
            self.login()
        
        try:
            # Por defecto, últimos 10 días
            if start_date is None:
                start_date = datetime.now() - timedelta(days=10)
            if end_date is None:
                end_date = datetime.now()
            
            activities = self.client.get_activities(0, limit)
            return activities
        except Exception as e:
            print(f"Error obteniendo actividades: {e}")
            return []
    
    def count_strength_training(self, start_date, end_date):
        """
        Cuenta sesiones de entrenamiento de fuerza en un rango
        """
        activities = self.get_activities(start_date, end_date, limit=100)
        
        strength_count = 0
        for activity in activities:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            
            # Ignorar breathwork (meditación)
            if 'breath' in activity_type or 'meditation' in activity_type:
                continue
            
            # Buscar actividades de tipo fuerza/resistencia
            if any(keyword in activity_type for keyword in ['strength', 'training', 'gym', 'weights', 'weight']):
                strength_count += 1
        
        return strength_count
    
    def get_monthly_summary(self, year, month):
        """
        Obtiene resumen mensual de datos Garmin
        """
        from calendar import monthrange
        
        # Rango del mes
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)
        
        total_steps = 0
        total_calories = 0
        total_sleep_hours = 0
        days_with_data = 0
        
        # Iterar por cada día del mes
        current_date = start_date
        while current_date <= end_date:
            stats = self.get_stats_for_date(current_date)
            if stats:
                total_steps += stats.get('totalSteps', 0)
                total_calories += stats.get('activeKilocalories', 0)
                days_with_data += 1
            
            # Sleep
            sleep_hours = self.get_sleep_duration_hours(current_date)
            if sleep_hours > 0:
                total_sleep_hours += sleep_hours
            
            current_date += timedelta(days=1)
        
        # Promedios
        avg_steps = total_steps / days_with_data if days_with_data > 0 else 0
        avg_sleep = total_sleep_hours / days_with_data if days_with_data > 0 else 0
        
        # Contar strength training
        strength_count = self.count_strength_training(start_date, end_date)
        
        return {
            'total_steps': total_steps,
            'avg_daily_steps': avg_steps,
            'total_active_calories': total_calories,
            'avg_sleep_hours': avg_sleep,
            'strength_training_sessions': strength_count,
            'days_tracked': days_with_data
        }


def test_garmin_connection():
    """Función de prueba para verificar conexión con Garmin"""
    print("\n" + "="*60)
    print("PRUEBA DE CONEXIÓN GARMIN CONNECT")
    print("="*60)
    
    try:
        client = GarminClient()
        
        # Login
        print("\n1. Iniciando sesión...")
        if not client.login():
            print("❌ No se pudo iniciar sesión")
            return False
        
        # Obtener stats de hoy
        print("\n2. Obteniendo estadísticas de hoy...")
        stats = client.get_stats_for_date()
        if stats:
            print(f"   ✅ Pasos: {stats.get('totalSteps', 0):,}")
            print(f"   ✅ Calorías activas: {stats.get('activeKilocalories', 0):,}")
            print(f"   ✅ Distancia: {stats.get('totalDistanceMeters', 0)/1000:.2f} km")
        
        # Obtener datos de sueño
        print("\n3. Obteniendo datos de sueño...")
        sleep_hours = client.get_sleep_duration_hours()
        if sleep_hours > 0:
            print(f"   ✅ Duración del sueño: {sleep_hours:.1f} horas")
        else:
            print("   ⚠️  No hay datos de sueño disponibles")
        
        # Actividades recientes
        print("\n4. Obteniendo actividades recientes...")
        activities = client.get_activities(limit=5)
        if activities:
            print(f"   ✅ Encontradas {len(activities)} actividades recientes:")
            for act in activities[:3]:
                print(f"      - {act.get('activityName', 'N/A')} ({act.get('activityType', {}).get('typeKey', 'N/A')})")
        
        print("\n" + "="*60)
        print("✅ PRUEBA COMPLETADA")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en prueba: {e}")
        return False


if __name__ == '__main__':
    test_garmin_connection()

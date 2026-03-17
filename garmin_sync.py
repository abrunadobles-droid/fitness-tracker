"""
Garmin Local Sync - Corre este script en tu computadora local para bajar datos de Garmin.

Uso:
    python3 garmin_sync.py              # Sincroniza mes actual
    python3 garmin_sync.py --all        # Sincroniza todos los meses del año
    python3 garmin_sync.py --month 1    # Sincroniza enero

Los datos se guardan en garmin_cache.json y el dashboard los lee de ahi.
Requiere tokens en ~/.garmin_tokens/ o credenciales en variables de entorno.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from calendar import monthrange

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'garmin_cache.json')


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"\n>> Cache guardado en: {CACHE_FILE}")


def sync_month(garmin, year, month, cache):
    key = f"{year}-{month:02d}"
    print(f"\n{'='*50}")
    print(f"   Sincronizando Garmin {key}...")
    print(f"{'='*50}")

    today = datetime.now()
    last_day = monthrange(year, month)[1]
    is_current = (year == today.year and month == today.month)
    start_date = datetime(year, month, 1)
    end_date = today if is_current else datetime(year, month, last_day)

    # --- Steps ---
    print(f"      👣 Obteniendo pasos diarios...")
    total_steps = 0
    days_with_steps = 0
    current_date = start_date
    while current_date <= end_date:
        try:
            stats = garmin.get_stats_for_date(current_date)
            if stats and stats.get('totalSteps'):
                total_steps += stats['totalSteps']
                days_with_steps += 1
        except Exception as e:
            print(f"         Error dia {current_date.strftime('%d')}: {e}")
        current_date += timedelta(days=1)

    steps_avg = round(total_steps / days_with_steps) if days_with_steps > 0 else 0

    # --- Activities ---
    print(f"      🏃 Obteniendo actividades...")
    activities_count = 0
    strength_count = 0
    try:
        all_activities = garmin.get_activities(start_date, end_date)
        for activity in all_activities:
            activity_date_str = activity.get('startTimeLocal', '')
            if activity_date_str:
                activity_date = datetime.strptime(activity_date_str[:10], '%Y-%m-%d')
                if activity_date.year == year and activity_date.month == month:
                    activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
                    if 'breath' not in activity_type and 'meditation' not in activity_type:
                        activities_count += 1
                        if any(kw in activity_type for kw in ['strength', 'training', 'gym', 'weight']):
                            strength_count += 1
    except Exception as e:
        print(f"         Error obteniendo actividades: {e}")

    new_data = {
        'year': year,
        'month': month,
        'synced_at': datetime.now().isoformat(),
        'steps_avg': steps_avg,
        'activities': activities_count,
        'strength': strength_count,
        'days_with_data': days_with_steps,
    }

    # Protect cache: don't overwrite existing data with empty results (API failure)
    if new_data['days_with_data'] == 0 and new_data['activities'] == 0 and key in cache:
        print(f"\n   ⚠️  API devolvió datos vacíos para {key}. Manteniendo cache anterior.")
        print(f"   (Cache actual: {cache[key].get('steps_avg', 0)} steps avg, synced {cache[key].get('synced_at', '?')})")
        return cache

    cache[key] = new_data

    d = cache[key]
    print(f"   Steps avg:     {d['steps_avg']:,} ({d['days_with_data']} dias)")
    print(f"   Activities:    {d['activities']}")
    print(f"   Strength:      {d['strength']}")

    return cache


def main():
    args = sys.argv[1:]
    now = datetime.now()

    # Initialize Garmin client
    try:
        from garmin_client import GarminClient
        garmin = GarminClient()
        print("Conectando a Garmin...")
        garmin.login()
        print("   ✅ Conectado a Garmin")
    except Exception as e:
        print(f"Error conectando a Garmin: {e}")
        print("\nVerifica que tienes tokens en ~/.garmin_tokens/ o credenciales configuradas.")
        print("Para generar tokens, corre el dashboard localmente y logueate via Garmin.")
        return

    cache = load_cache()

    if '--all' in args:
        for month in range(1, now.month + 1):
            cache = sync_month(garmin, now.year, month, cache)
    elif '--month' in args:
        idx = args.index('--month')
        if idx + 1 < len(args):
            month = int(args[idx + 1])
            year = now.year
            if '--year' in args:
                y_idx = args.index('--year')
                if y_idx + 1 < len(args):
                    year = int(args[y_idx + 1])
            cache = sync_month(garmin, year, month, cache)
        else:
            print("Uso: python3 garmin_sync.py --month 3")
            return
    else:
        cache = sync_month(garmin, now.year, now.month, cache)

    save_cache(cache)
    print("\nListo! El dashboard usara estos datos automaticamente.")


if __name__ == '__main__':
    main()

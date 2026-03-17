"""
WHOOP Local Sync - Corre este script en tu computadora local para bajar datos de WHOOP.

Uso:
    python whoop_sync.py              # Sincroniza mes actual
    python whoop_sync.py --all        # Sincroniza todos los meses del año
    python whoop_sync.py --month 1    # Sincroniza enero
    python whoop_sync.py --auth       # Re-autorizar (obtener nuevos tokens)

Los datos se guardan en whoop_cache.json y el dashboard los lee de ahi.
Esto resuelve el problema de que Streamlit Cloud no puede conectarse a WHOOP.
"""

import json
import sys
import os
from datetime import datetime
from calendar import monthrange

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whoop_cache.json')


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"\n>> Cache guardado en: {CACHE_FILE}")


def sync_month(whoop, year, month, cache):
    key = f"{year}-{month:02d}"
    print(f"\n{'='*50}")
    print(f"   Sincronizando {key}...")
    print(f"{'='*50}")

    summary = whoop.get_monthly_summary(year, month)

    new_data = {
        'year': year,
        'month': month,
        'synced_at': datetime.now().isoformat(),
        'sleep_hours_avg': round(summary.get('avg_sleep_hours', 0), 2),
        'days_before_930': summary.get('days_sleep_before_930pm', 0),
        'hr_zones_1_3_hours': round(summary.get('hr_zones_1_3_hours', 0), 2),
        'hr_zones_4_5_hours': round(summary.get('hr_zones_4_5_hours', 0), 2),
        'avg_hrv': round(summary.get('avg_hrv', 0), 1),
        'avg_recovery_score': round(summary.get('avg_recovery_score', 0), 1),
        'avg_resting_hr': round(summary.get('avg_resting_hr', 0), 1),
        'avg_sleep_consistency': round(summary.get('avg_sleep_consistency', 0), 1),
        'num_sleeps': len(summary.get('sleep', [])),
        'num_workouts': len(summary.get('workouts', [])),
    }

    # Protect cache: don't overwrite existing data with empty results (API failure)
    if new_data['num_sleeps'] == 0 and new_data['avg_recovery_score'] == 0 and key in cache:
        print(f"\n   ⚠️  API devolvió datos vacíos para {key}. Manteniendo cache anterior.")
        print(f"   (Cache actual: {cache[key].get('num_sleeps', 0)} noches, synced {cache[key].get('synced_at', '?')})")
        return cache

    cache[key] = new_data

    d = cache[key]
    print(f"   Sleep avg:     {d['sleep_hours_avg']}h ({d['num_sleeps']} noches)")
    print(f"   Before 9:30:   {d['days_before_930']} dias")
    print(f"   HR Zones 1-3:  {d['hr_zones_1_3_hours']}h")
    print(f"   HR Zones 4-5:  {d['hr_zones_4_5_hours']}h")
    print(f"   HRV avg:       {d['avg_hrv']}ms")
    print(f"   Recovery avg:  {d['avg_recovery_score']}%")
    print(f"   Resting HR:    {d['avg_resting_hr']} bpm")
    print(f"   Sleep Consist: {d['avg_sleep_consistency']}%")

    return cache


def main():
    args = sys.argv[1:]
    now = datetime.now()

    # Handle --auth flag
    if '--auth' in args:
        from whoop_auth import WhoopAuth
        auth = WhoopAuth()
        auth.authorize()
        print("\nTokens guardados. Ahora puedes sincronizar con: python whoop_sync.py")
        return

    # Initialize WHOOP client
    try:
        from whoop_client_v2_corrected import WhoopClientV2
        whoop = WhoopClientV2()

        if not whoop.auth.is_authenticated():
            print("❌ No hay tokens de WHOOP. Ejecuta primero:")
            print("   python3 whoop_sync.py --auth")
            return

        # Quick auth check: try to get profile to verify tokens work
        try:
            whoop.get_profile()
            print("   ✅ Conectado a WHOOP")
        except Exception:
            print("❌ Tokens de WHOOP expirados o inválidos.")
            print("   Ejecuta: python3 whoop_sync.py --auth")
            print("   (Esto abrirá el navegador para re-autorizar)")
            return
    except Exception as e:
        print(f"Error inicializando WHOOP: {e}")
        print("Ejecuta primero: python3 whoop_sync.py --auth")
        return

    cache = load_cache()

    if '--all' in args:
        # Sync all months of current year up to current month
        for month in range(1, now.month + 1):
            cache = sync_month(whoop, now.year, month, cache)
    elif '--month' in args:
        idx = args.index('--month')
        if idx + 1 < len(args):
            month = int(args[idx + 1])
            year = now.year
            if '--year' in args:
                y_idx = args.index('--year')
                if y_idx + 1 < len(args):
                    year = int(args[y_idx + 1])
            cache = sync_month(whoop, year, month, cache)
        else:
            print("Uso: python whoop_sync.py --month 3")
            return
    else:
        # Default: sync current month
        cache = sync_month(whoop, now.year, now.month, cache)

    save_cache(cache)

    # Verificar que el mes actual tiene datos recientes
    current_key = f"{now.year}-{now.month:02d}"
    if current_key in cache:
        synced = cache[current_key].get('synced_at', 'desconocido')
        sleeps = cache[current_key].get('num_sleeps', 0)
        print(f"\n>> Mes actual ({current_key}): {sleeps} noches, ultimo sync: {synced}")

    print("\nListo! El dashboard usara estos datos automaticamente.")


if __name__ == '__main__':
    main()

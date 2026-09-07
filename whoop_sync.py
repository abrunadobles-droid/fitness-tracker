"""
WHOOP Local Sync - Corre este script en tu computadora local para bajar datos de WHOOP.

Uso:
    python whoop_sync.py              # Sincroniza mes actual
    python whoop_sync.py --all        # Sincroniza todos los meses del año
    python whoop_sync.py --month 1    # Sincroniza enero
    python whoop_sync.py --auth       # Re-autorizar (obtener nuevos tokens)
    python whoop_sync.py --sports     # Lista los sport_name de tus workouts del año
    python whoop_sync.py --zones      # Diagnóstico HR zones: por mes y deporte (todo el año)
    python whoop_sync.py --zones --month 8   # Detalle workout por workout de agosto

Los datos se guardan en whoop_cache.json y el dashboard los lee de ahi.
Esto resuelve el problema de que Streamlit Cloud no puede conectarse a WHOOP.
"""

import json
import sys
import os
from datetime import datetime, timedelta
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
        'meditation_days': summary.get('meditation_days', 0),
        'sauna_days': summary.get('sauna_days', 0),
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


def _zone_ms(workout, keys):
    """Suma de milisegundos en las zonas indicadas (0 si el workout no tiene score)."""
    score = workout.get('score') or {}
    zones = score.get('zone_durations') or {}
    return sum(zones.get(k, 0) or 0 for k in keys)


Z13 = ('zone_one_milli', 'zone_two_milli', 'zone_three_milli')
Z45 = ('zone_four_milli', 'zone_five_milli')


def zones_report(whoop, year, month=None):
    """Desglose de HR zones para entender de dónde salen (o dejaron de salir) las horas.

    Sin --month: tabla por mes (zonas, workouts, HR máx alcanzado) + top deportes por zona 4-5.
    Con --month: cada workout del mes con su tiempo en zona 4-5, HR promedio y HR máx.
    """
    from collections import defaultdict
    from whoop_client_v2_corrected import workout_local_date

    # WHOOP calcula las zonas con reserva cardíaca (Karvonen): zona = RHR + %·(MaxHR − RHR),
    # con Z1 40%, Z2 60%, Z3 70%, Z4 80%, Z5 90%. El RHR baseline y el MaxHR del perfil
    # se ajustan solos con el tiempo, así que los umbrales se mueven un poco mes a mes.
    now = datetime.now()
    max_hr, rhr = None, None
    try:
        body = whoop.get_body_measurements() or {}
        max_hr = body.get('max_heart_rate')
    except Exception as e:
        print(f"   ⚠️  No se pudo leer el perfil corporal: {e}")
    try:
        recent = whoop.get_all_records('recovery', now - timedelta(days=30), now)
        rhrs = [r['score']['resting_heart_rate'] for r in recent
                if r.get('score') and r['score'].get('resting_heart_rate')]
        rhr = sum(rhrs) / len(rhrs) if rhrs else None
    except Exception as e:
        print(f"   ⚠️  No se pudo leer el RHR reciente: {e}")
    if max_hr and rhr:
        hrr = max_hr - rhr
        z4, z5 = rhr + 0.8 * hrr, rhr + 0.9 * hrr
        print(f"\n   Perfil WHOOP: HR máx {max_hr} bpm, RHR ~{rhr:.0f} bpm (promedio 30 días)")
        print(f"   Zonas por reserva cardíaca: Zona 4 desde ~{z4:.0f} bpm, Zona 5 desde ~{z5:.0f} bpm")
        print("   (los workouts viejos conservan los umbrales de su momento; no se recalculan)")
    elif max_hr:
        print(f"\n   HR máximo configurado en WHOOP: {max_hr} bpm (no pude estimar el RHR baseline)")

    if month:
        start = datetime(year, month, 1)
        end = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
    else:
        start = datetime(year, 1, 1)
        end = now if year == now.year else datetime(year, 12, 31, 23, 59, 59)

    workouts = whoop.get_all_records('activity/workout', start, end)
    print(f"\n   {len(workouts)} workouts entre {start.date()} y {end.date()}")

    def hrs(ms):
        return ms / 3600000

    def mins(ms):
        return ms / 60000

    if month:
        # ---- Detalle workout por workout ----
        rows = []
        for w in workouts:
            d = workout_local_date(w)
            if not d or d.year != year or d.month != month:
                continue
            score = w.get('score') or {}
            rows.append({
                'date': d,
                'sport': w.get('sport_name') or f"sport_id={w.get('sport_id', '?')}",
                'z45': _zone_ms(w, Z45),
                'z13': _zone_ms(w, Z13),
                'avg_hr': score.get('average_heart_rate'),
                'max_hr': score.get('max_heart_rate'),
                'strain': score.get('strain'),
                'scored': w.get('score_state') == 'SCORED',
            })
        rows.sort(key=lambda r: r['z45'], reverse=True)
        print(f"\n   {'fecha':11}{'deporte':24}{'z4-5':>7}{'z1-3':>7}{'HRavg':>7}{'HRmax':>7}{'strain':>8}")
        print("   " + "-" * 71)
        for r in rows:
            flag = "" if r['scored'] else "  (sin score)"
            print(f"   {str(r['date']):11}{r['sport'][:23]:24}{mins(r['z45']):6.0f}m{mins(r['z13']):6.0f}m"
                  f"{r['avg_hr'] or 0:7}{r['max_hr'] or 0:7}{(r['strain'] or 0):8.1f}{flag}")
        tot45 = sum(r['z45'] for r in rows)
        tot13 = sum(r['z13'] for r in rows)
        print("   " + "-" * 71)
        print(f"   TOTAL {len(rows)} workouts: zona 4-5 = {hrs(tot45):.2f}h | zona 1-3 = {hrs(tot13):.2f}h")
        if max_hr and rhr:
            z4 = rhr + 0.8 * (max_hr - rhr)
            hit = [r for r in rows if (r['max_hr'] or 0) >= z4]
            print(f"   Workouts que llegaron a HR de zona 4 (≥{z4:.0f} bpm): {len(hit)} de {len(rows)}")
        return

    # ---- Resumen por mes + por deporte ----
    by_month = defaultdict(lambda: {'n': 0, 'z45': 0, 'z13': 0, 'max_hrs': [], 'sports': defaultdict(int)})
    by_sport_year = defaultdict(lambda: {'n': 0, 'z45': 0, 'z13': 0})
    for w in workouts:
        d = workout_local_date(w)
        if not d or d.year != year:
            continue
        sport = w.get('sport_name') or f"sport_id={w.get('sport_id', '?')}"
        z45, z13 = _zone_ms(w, Z45), _zone_ms(w, Z13)
        m = by_month[d.month]
        m['n'] += 1
        m['z45'] += z45
        m['z13'] += z13
        m['sports'][sport] += z45
        mh = (w.get('score') or {}).get('max_heart_rate')
        if mh:
            m['max_hrs'].append(mh)
        s = by_sport_year[sport]
        s['n'] += 1
        s['z45'] += z45
        s['z13'] += z13

    print(f"\n   {'mes':6}{'wk':>4}{'z1-3':>8}{'z4-5':>8}{'HRmax prom':>12}{'HRmax pico':>12}   top deportes por zona 4-5")
    print("   " + "-" * 95)
    for mo in sorted(by_month):
        m = by_month[mo]
        avg_max = sum(m['max_hrs']) / len(m['max_hrs']) if m['max_hrs'] else 0
        peak = max(m['max_hrs']) if m['max_hrs'] else 0
        top = sorted(m['sports'].items(), key=lambda kv: kv[1], reverse=True)[:3]
        top_txt = ", ".join(f"{name} {mins(ms):.0f}m" for name, ms in top if ms > 0) or "—"
        print(f"   {year}-{mo:02d}{m['n']:4}{hrs(m['z13']):7.2f}h{hrs(m['z45']):7.2f}h"
              f"{avg_max:12.0f}{peak:12}   {top_txt}")

    print(f"\n   Por deporte ({year}):")
    print(f"   {'deporte':26}{'wk':>4}{'z1-3':>8}{'z4-5':>8}{'z4-5/wk':>9}")
    print("   " + "-" * 55)
    for sport, s in sorted(by_sport_year.items(), key=lambda kv: kv[1]['z45'], reverse=True):
        per = mins(s['z45']) / s['n'] if s['n'] else 0
        print(f"   {sport[:25]:26}{s['n']:4}{hrs(s['z13']):7.2f}h{hrs(s['z45']):7.2f}h{per:8.1f}m")
    print("\n   Tip: python whoop_sync.py --zones --month N  → detalle workout por workout de ese mes")


def main():
    args = sys.argv[1:]
    now = datetime.now()

    # Sin client_secret ni el --auth ni el refresh de tokens funcionan (401).
    # En CI: falta el secret WHOOP_CLIENT_SECRET de GitHub.
    import config
    if not config.WHOOP_CLIENT_SECRET:
        print("❌ WHOOP_CLIENT_SECRET está vacío.")
        if os.environ.get('GITHUB_ACTIONS'):
            print("   Crea el secret WHOOP_CLIENT_SECRET en GitHub (Settings → Secrets → Actions).")
            print("   Valor: .streamlit/secrets.toml → [whoop] client_secret")
        else:
            print("   Agrega client_secret en .streamlit/secrets.toml, sección [whoop].")
        sys.exit(1)

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

        # WHOOP rota el refresh token en cada refresh: si este run lo rota,
        # el secret WHOOP_TOKENS_JSON de GitHub queda inválido y el cron muere.
        refresh_token_inicial = (whoop.auth.tokens or {}).get('refresh_token')

        if not whoop.auth.is_authenticated():
            print("❌ No hay tokens de WHOOP. Ejecuta primero:")
            print("   python3 whoop_sync.py --auth")
            sys.exit(1)

        # Quick auth check: try to get profile to verify tokens work
        try:
            whoop.get_profile()
            print("   ✅ Conectado a WHOOP")
        except Exception:
            print("❌ Tokens de WHOOP expirados o inválidos.")
            print("   Ejecuta: python3 whoop_sync.py --auth")
            print("   (Esto abrirá el navegador para re-autorizar)")
            sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error inicializando WHOOP: {e}")
        print("Ejecuta primero: python3 whoop_sync.py --auth")
        sys.exit(1)

    # Debug: listar los sport_name que WHOOP devuelve para tus workouts del año
    # (útil para verificar cómo se llaman Meditación y Sauna en la API)
    if '--sports' in args:
        from collections import Counter
        workouts = whoop.get_all_records(
            'activity/workout', datetime(now.year, 1, 1), now
        )
        counts = Counter(
            (w.get('sport_name') or f"sport_id={w.get('sport_id', '?')}")
            for w in workouts
        )
        print(f"\n   Actividades {now.year} ({len(workouts)} workouts):")
        for name, count in counts.most_common():
            print(f"      {name}: {count}")
        return

    # Diagnóstico de HR zones (por qué subieron/bajaron las horas en zona 4-5)
    if '--zones' in args:
        year = now.year
        month = None
        if '--year' in args:
            year = int(args[args.index('--year') + 1])
        if '--month' in args:
            month = int(args[args.index('--month') + 1])
        zones_report(whoop, year, month)
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

    refresh_token_final = (whoop.auth.tokens or {}).get('refresh_token')
    if refresh_token_inicial != refresh_token_final and not os.environ.get('GITHUB_ACTIONS'):
        print("\n⚠️  Los tokens de WHOOP rotaron durante este sync.")
        print("   El secret de GitHub quedó desactualizado. Actualízalo con:")
        print('   gh secret set WHOOP_TOKENS_JSON --body "$(cat whoop_tokens.json)"')

    print("\nListo! El dashboard usara estos datos automaticamente.")


if __name__ == '__main__':
    main()

"""
Carga de datos mensuales: Garmin + WHOOP.
Intenta API live primero, luego cae a cache local.
"""
import json
import os
import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange


def _load_garmin_cache():
    """Load Garmin data from local cache file (fallback)."""
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'garmin_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return {}


def _garmin_has_tokens():
    """Check if Garmin tokens exist before attempting login (avoids 429)."""
    import os
    tokenstore = os.path.expanduser("~/.garmin_tokens")
    return os.path.isdir(tokenstore) and len(os.listdir(tokenstore)) > 0


def _get_garmin_live(year, month, start_date, end_date):
    """Fetch Garmin data live from API. Raises on failure."""
    if not _garmin_has_tokens():
        raise Exception("No Garmin tokens saved. Run: source .venv/bin/activate && python garmin_sync.py")
    from garmin_client import GarminClient
    garmin = GarminClient()
    garmin.login()

    total_steps = 0
    days_with_steps = 0
    current_date = start_date
    while current_date <= end_date:
        try:
            stats = garmin.get_stats_for_date(current_date)
            if stats and stats.get('totalSteps'):
                total_steps += stats['totalSteps']
                days_with_steps += 1
        except Exception:
            pass
        current_date += timedelta(days=1)

    steps_avg = round(total_steps / days_with_steps) if days_with_steps > 0 else 0

    all_activities = garmin.get_activities(start_date, end_date)
    activities_count = 0
    strength_count = 0

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

    return steps_avg, activities_count, strength_count


@st.cache_data(ttl=60)
def get_monthly_data(year, month):
    today = datetime.now()
    current_year = today.year
    current_month = today.month

    last_day = monthrange(year, month)[1]
    is_current = (year == current_year and month == current_month)
    start_date = datetime(year, month, 1)
    end_date = today if is_current else datetime(year, month, last_day)

    data = {
        'month': month, 'year': year,
        'steps_avg': 0, 'activities': 0, 'strength': 0,
        'sleep_hours_avg': 0,
        'hr_zone_1_3': 0, 'hr_zone_4_5': 0,
        'recovery_score': 0, 'resting_hr': 0, 'sleep_consistency': 0,
        'meditation_sessions': 0, 'meditation_minutes': 0,
        'whoop_source': 'NO DATA',
        'garmin_source': 'NO DATA',
    }

    try:
        import meditation_log as _mlog
        _mstats = _mlog.monthly_stats(year, month)
        data['meditation_sessions'] = _mstats['sessions_count']
        data['meditation_minutes'] = _mstats['minutes_total']
    except Exception as e:
        print(f"[MEDITATION] Failed to load monthly stats: {e}")

    # --- GARMIN ---
    cache_key = f"{year}-{month:02d}"

    # Historical months: prefer cache (data won't change, avoids ~30 API calls per month)
    # Current month: try live first, fall back to cache
    if not is_current:
        garmin_cache = _load_garmin_cache()
        if cache_key in garmin_cache:
            cached = garmin_cache[cache_key]
            data['steps_avg'] = cached.get('steps_avg', 0)
            data['activities'] = cached.get('activities', 0)
            data['strength'] = cached.get('strength', 0)
            data['garmin_source'] = f"CACHE ({cached.get('synced_at', '?')})"
            print(f"[GARMIN] {cache_key} loaded from CACHE (historical)")
        else:
            try:
                steps_avg, activities, strength = _get_garmin_live(year, month, start_date, end_date)
                data['steps_avg'] = steps_avg
                data['activities'] = activities
                data['strength'] = strength
                data['garmin_source'] = 'LIVE'
                print(f"[GARMIN] {cache_key} fetched LIVE (no cache)")
            except Exception as e:
                print(f"[GARMIN] No data for {cache_key}: {e}")
    else:
        try:
            steps_avg, activities, strength = _get_garmin_live(year, month, start_date, end_date)
            data['steps_avg'] = steps_avg
            data['activities'] = activities
            data['strength'] = strength
            data['garmin_source'] = 'LIVE'
            print(f"[GARMIN] {cache_key} fetched LIVE")
        except Exception as e:
            print(f"[GARMIN] Live fetch failed for {cache_key}: {e}")
            try:
                garmin_cache = _load_garmin_cache()
                if cache_key in garmin_cache:
                    cached = garmin_cache[cache_key]
                    data['steps_avg'] = cached.get('steps_avg', 0)
                    data['activities'] = cached.get('activities', 0)
                    data['strength'] = cached.get('strength', 0)
                    data['garmin_source'] = f"CACHE ({cached.get('synced_at', '?')})"
                    print(f"[GARMIN] {cache_key} loaded from CACHE")
                else:
                    print(f"[GARMIN] No cache data for {cache_key}")
            except Exception as cache_err:
                print(f"[GARMIN] Cache load failed: {cache_err}")

    # --- WHOOP ---
    from whoop_streamlit import get_whoop_data
    whoop, source = get_whoop_data(year, month)
    data['whoop_source'] = source

    if whoop:
        for raw_key, data_key in [('hr_zones_1_3_hours', 'hr_zone_1_3'), ('hr_zones_4_5_hours', 'hr_zone_4_5')]:
            try:
                raw = whoop.get(raw_key, 0)
                data[data_key] = round(float(raw), 1) if raw is not None else 0
            except (TypeError, ValueError):
                data[data_key] = 0

        data['sleep_hours_avg'] = round(whoop.get('sleep_hours_avg', 0), 1)
        data['recovery_score'] = round(whoop.get('avg_recovery_score', 0), 1)
        data['resting_hr'] = round(whoop.get('avg_resting_hr', 0), 1)
        data['sleep_consistency'] = round(whoop.get('avg_sleep_consistency', 0), 1)

    return data

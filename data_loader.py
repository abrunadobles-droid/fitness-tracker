"""
Carga de datos mensuales: Garmin + WHOOP.
"""
import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange


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
        'whoop_source': 'NO DATA',
    }

    # --- GARMIN ---
    try:
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

        data['steps_avg'] = round(total_steps / days_with_steps) if days_with_steps > 0 else 0

        all_activities = garmin.get_activities(start_date, end_date)
        filtered_activities = []
        strength_count = 0

        for activity in all_activities:
            activity_date_str = activity.get('startTimeLocal', '')
            if activity_date_str:
                activity_date = datetime.strptime(activity_date_str[:10], '%Y-%m-%d')
                if activity_date.year == year and activity_date.month == month:
                    activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
                    if 'breath' not in activity_type and 'meditation' not in activity_type:
                        filtered_activities.append(activity)
                        if any(kw in activity_type for kw in ['strength', 'training', 'gym', 'weight']):
                            strength_count += 1

        data['activities'] = len(filtered_activities)
        data['strength'] = strength_count

    except Exception as e:
        st.error(f"Error cargando Garmin: {str(e)}")

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

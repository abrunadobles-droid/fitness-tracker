"""
WHOOP Live Client for Streamlit Cloud.

Loads tokens from Streamlit secrets, refreshes them in-session via st.session_state,
and calls the WHOOP API directly. Falls back to whoop_cache.json if API fails.
"""

import requests
import time
import json
import os
import streamlit as st
from datetime import datetime, timedelta
from calendar import monthrange


WHOOP_API = 'https://api.prod.whoop.com/developer/v2'
WHOOP_TOKEN_URL = 'https://api.prod.whoop.com/oauth/oauth2/token'


def _get_tokens():
    """Get current tokens from session_state or initialize from secrets."""
    if 'whoop_tokens' not in st.session_state:
        try:
            tokens = {
                'access_token': st.secrets["whoop"]["access_token"],
                'refresh_token': st.secrets["whoop"]["refresh_token"],
                'expires_at': st.secrets["whoop"].get("expires_at", 0),
            }
            st.session_state.whoop_tokens = tokens
        except Exception:
            # Try loading from WHOOP_TOKENS_JSON env var (CI/local)
            tokens_json = os.environ.get('WHOOP_TOKENS_JSON')
            if tokens_json:
                st.session_state.whoop_tokens = json.loads(tokens_json)
            else:
                # Try local file
                token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whoop_tokens.json')
                if os.path.exists(token_file):
                    with open(token_file, 'r') as f:
                        st.session_state.whoop_tokens = json.load(f)
                else:
                    return None
    return st.session_state.whoop_tokens


def _save_tokens(tokens):
    """Save refreshed tokens to session_state."""
    if 'expires_in' in tokens and 'expires_at' not in tokens:
        tokens['expires_at'] = time.time() + tokens['expires_in']
    st.session_state.whoop_tokens = tokens


def _get_client_credentials():
    """Get client_id and client_secret from secrets or env."""
    try:
        return st.secrets["whoop"]["client_id"], st.secrets["whoop"]["client_secret"]
    except Exception:
        client_id = os.environ.get('WHOOP_CLIENT_ID', '')
        client_secret = os.environ.get('WHOOP_CLIENT_SECRET', '')
        return client_id, client_secret


def _refresh_tokens(tokens):
    """Refresh the access token using the refresh token."""
    client_id, client_secret = _get_client_credentials()

    response = requests.post(WHOOP_TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': tokens['refresh_token'],
        'client_id': client_id,
        'client_secret': client_secret,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
    response.raise_for_status()

    new_tokens = response.json()
    _save_tokens(new_tokens)
    return new_tokens


def _get_headers():
    """Get authorization headers, refreshing token if needed."""
    tokens = _get_tokens()
    if not tokens:
        raise Exception("No WHOOP tokens available")

    # Preventive refresh: if token expires in < 5 minutes
    expires_at = tokens.get('expires_at', 0)
    if expires_at and time.time() > (expires_at - 300):
        try:
            tokens = _refresh_tokens(tokens)
        except Exception as e:
            print(f"[WHOOP] Token refresh failed: {e}")

    return {'Authorization': f'Bearer {tokens["access_token"]}'}


def _api_request(endpoint, params=None):
    """Make an API request with automatic retry on 401."""
    url = f"{WHOOP_API}/{endpoint}"
    headers = _get_headers()

    response = requests.get(url, headers=headers, params=params, timeout=15)

    if response.status_code == 401:
        # Token expired, try refresh
        tokens = _get_tokens()
        if tokens:
            tokens = _refresh_tokens(tokens)
            headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
            response = requests.get(url, headers=headers, params=params, timeout=15)

    response.raise_for_status()
    return response.json()


def _get_all_records(endpoint, start_date, end_date):
    """Paginate through all records for a date range."""
    all_records = []
    next_token = None

    params = {
        'start': start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'end': end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'limit': 25
    }

    while True:
        if next_token:
            params['nextToken'] = next_token

        data = _api_request(endpoint, params=params)

        if 'records' in data and data['records']:
            all_records.extend(data['records'])

        if data.get('next_token'):
            next_token = data['next_token']
        else:
            break

    return all_records


def get_whoop_monthly_live(year, month):
    """
    Fetch WHOOP monthly data live from API.
    Returns dict with same keys as whoop_cache.json entries.
    Raises exception if API call fails.
    """
    start_date = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    result = {
        'sleep_hours_avg': 0,
        'hr_zones_1_3_hours': 0,
        'hr_zones_4_5_hours': 0,
        'avg_recovery_score': 0,
        'avg_resting_hr': 0,
        'avg_sleep_consistency': 0,
        'synced_at': datetime.now().isoformat(),
        'live': True,
    }

    # --- Sleep ---
    sleeps = _get_all_records('activity/sleep', start_date, end_date)
    if sleeps:
        total_sleep_ms = 0
        total_consistency = 0

        for sleep in sleeps:
            if sleep.get('score') and sleep['score'].get('stage_summary'):
                stages = sleep['score']['stage_summary']
                actual_sleep_ms = (
                    stages.get('total_light_sleep_time_milli', 0) +
                    stages.get('total_slow_wave_sleep_time_milli', 0) +
                    stages.get('total_rem_sleep_time_milli', 0)
                )
                total_sleep_ms += actual_sleep_ms
                total_consistency += sleep['score'].get('sleep_consistency_percentage', 0)

        num_sleeps = len(sleeps)
        result['sleep_hours_avg'] = round((total_sleep_ms / num_sleeps) / 3600000, 2)
        result['avg_sleep_consistency'] = round(total_consistency / num_sleeps, 1)

    # --- Recovery ---
    recoveries = _get_all_records('recovery', start_date, end_date)
    if recoveries:
        total_recovery = 0
        total_resting_hr = 0
        rhr_count = 0

        for rec in recoveries:
            if rec.get('score'):
                total_recovery += rec['score'].get('recovery_score', 0)
                rhr = rec['score'].get('resting_heart_rate', 0)
                if rhr > 0:
                    total_resting_hr += rhr
                    rhr_count += 1

        result['avg_recovery_score'] = round(total_recovery / len(recoveries), 1)
        result['avg_resting_hr'] = round(total_resting_hr / rhr_count, 1) if rhr_count > 0 else 0

    # --- Cycles (HR Zones from full-day strain, not just workouts) ---
    cycles = _get_all_records('cycle', start_date, end_date)
    if cycles:
        total_zone_1_3 = 0
        total_zone_4_5 = 0

        for cycle in cycles:
            if cycle.get('score') and cycle['score'].get('zone_durations'):
                zones = cycle['score']['zone_durations']
                total_zone_1_3 += (
                    zones.get('zone_one_milli', 0) +
                    zones.get('zone_two_milli', 0) +
                    zones.get('zone_three_milli', 0)
                )
                total_zone_4_5 += (
                    zones.get('zone_four_milli', 0) +
                    zones.get('zone_five_milli', 0)
                )

        result['hr_zones_1_3_hours'] = round(total_zone_1_3 / 3600000, 2)
        result['hr_zones_4_5_hours'] = round(total_zone_4_5 / 3600000, 2)

    return result


def load_whoop_cache():
    """Load WHOOP data from local cache file (fallback)."""
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whoop_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return {}


def get_whoop_data(year, month):
    """
    Get WHOOP data: try live API first, fall back to cache.
    Returns (data_dict, source_string).
    """
    cache_key = f"{year}-{month:02d}"

    # Try live API first
    try:
        data = get_whoop_monthly_live(year, month)
        print(f"[WHOOP] {cache_key} fetched LIVE")
        return data, "LIVE"
    except Exception as e:
        print(f"[WHOOP] Live fetch failed for {cache_key}: {e}")

    # Fall back to cache
    try:
        cache = load_whoop_cache()
        if cache_key in cache:
            print(f"[WHOOP] {cache_key} loaded from CACHE")
            return cache[cache_key], f"CACHE ({cache[cache_key].get('synced_at', '?')})"
    except Exception as e:
        print(f"[WHOOP] Cache load failed: {e}")

    print(f"[WHOOP] No data available for {cache_key}")
    return None, "NO DATA"

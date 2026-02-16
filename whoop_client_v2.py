"""
Cliente WHOOP API v2 - Compatible con Streamlit Secrets
"""

import requests
from datetime import datetime, timedelta
import json

try:
    import streamlit as st
    WHOOP_ACCESS_TOKEN = st.secrets["whoop"]["access_token"]
    WHOOP_REFRESH_TOKEN = st.secrets["whoop"]["refresh_token"]
    WHOOP_CLIENT_ID = st.secrets["whoop"]["client_id"]
    WHOOP_CLIENT_SECRET = st.secrets["whoop"]["client_secret"]
except:
    # Fallback para desarrollo local
    import os
    if os.path.exists('whoop_tokens.json'):
        with open('whoop_tokens.json', 'r') as f:
            tokens = json.load(f)
            WHOOP_ACCESS_TOKEN = tokens['access_token']
            WHOOP_REFRESH_TOKEN = tokens['refresh_token']
    from config import WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET

class WhoopClientV2:
    def __init__(self):
        self.access_token = WHOOP_ACCESS_TOKEN
        self.base_url = "https://api.prod.whoop.com/developer"
    
    def _make_request(self, endpoint, params=None):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
        
        if response.status_code == 401:
            self._refresh_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
        
        response.raise_for_status()
        return response.json()
    
    def _refresh_token(self):
        url = 'https://api.prod.whoop.com/oauth/oauth2/token'
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': WHOOP_REFRESH_TOKEN,
            'client_id': WHOOP_CLIENT_ID,
            'client_secret': WHOOP_CLIENT_SECRET
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        tokens = response.json()
        self.access_token = tokens['access_token']
    
    def get_all_records(self, endpoint, start_date, end_date):
        all_records = []
        params = {
            'start': start_date.strftime('%Y-%m-%dT00:00:00.000Z'),
            'end': end_date.strftime('%Y-%m-%dT23:59:59.999Z'),
            'limit': 25
        }
        
        while True:
            data = self._make_request(endpoint, params)
            records = data.get('records', [])
            all_records.extend(records)
            
            next_token = data.get('next_token')
            if not next_token:
                break
            params['nextToken'] = next_token
        
        return all_records
    
    def get_monthly_summary(self, year, month):
        from calendar import monthrange
        
        last_day = monthrange(year, month)[1]
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        sleep_records = self.get_all_records('/v2/activity/sleep', start_date, end_date)
        recovery_records = self.get_all_records('/v2/recovery', start_date, end_date)
        workout_records = self.get_all_records('/v2/activity/workout', start_date, end_date)
        
        total_sleep = 0
        total_performance = 0
        total_consistency = 0
        days_before_930 = 0
        sleep_count = 0
        
        for sleep in sleep_records:
            if sleep.get('score'):
                sleep_start = datetime.fromisoformat(sleep['start'].replace('Z', '+00:00'))
                timezone_offset = sleep.get('timezone_offset', '-06:00')
                offset_hours = int(timezone_offset.split(':')[0])
                local_time = sleep_start + timedelta(hours=offset_hours)
                
                if local_time.hour < 12:
                    local_time = local_time - timedelta(days=1)
                
                if local_time.hour <= 21 and local_time.minute <= 30:
                    days_before_930 += 1
                
                stage_summary = sleep['score']['stage_summary']
                actual_sleep_ms = (
                    stage_summary.get('total_light_sleep_time_milli', 0) +
                    stage_summary.get('total_slow_wave_sleep_time_milli', 0) +
                    stage_summary.get('total_rem_sleep_time_milli', 0)
                )
                
                total_sleep += actual_sleep_ms / 3600000
                total_performance += sleep['score'].get('sleep_performance_percentage', 0)
                total_consistency += sleep['score'].get('sleep_consistency_percentage', 0)
                sleep_count += 1
        
        total_recovery = 0
        total_hrv = 0
        recovery_count = 0
        
        for recovery in recovery_records:
            if recovery.get('score'):
                total_recovery += recovery['score'].get('recovery_score', 0)
                total_hrv += recovery['score'].get('hrv_rmssd_milli', 0) / 1000
                recovery_count += 1
        
        return {
            'avg_sleep_hours': total_sleep / sleep_count if sleep_count > 0 else 0,
            'avg_sleep_performance': total_performance / sleep_count if sleep_count > 0 else 0,
            'avg_sleep_consistency': total_consistency / sleep_count if sleep_count > 0 else 0,
            'days_sleep_before_930pm': days_before_930,
            'avg_recovery_score': total_recovery / recovery_count if recovery_count > 0 else 0,
            'avg_hrv': total_hrv / recovery_count if recovery_count > 0 else 0,
            'workouts': workout_records
        }

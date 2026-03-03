"""
Cliente de Garmin Connect
- Uses garth token persistence to avoid repeated login failures
- Falls back to email/password only when tokens are missing or expired
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
import os
import config

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")


class GarminClient:
    def __init__(self):
        self.client = None

    def login(self):
        # Try saved tokens first (avoids Garmin rate-limiting/blocking)
        if os.path.isdir(TOKENSTORE):
            try:
                self.client = Garmin()
                self.client.login(TOKENSTORE)
                return
            except Exception:
                pass

        # Fall back to email/password login
        self.client = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)
        self.client.login()

        # Save tokens for future use
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

    def get_activities(self, start_date=None, end_date=None, limit=10):
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        activities = self.client.get_activities_by_date(start_str, end_str)
        return activities

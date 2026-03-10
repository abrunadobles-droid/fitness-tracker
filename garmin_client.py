"""
Cliente de Garmin Connect
- Uses garth token persistence to avoid repeated login failures
- Auto-refreshes and re-saves tokens to keep the session alive
- Falls back to custom SSO flow (garmin_auth.py) when library login fails
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
                # Re-save tokens so refreshed tokens are persisted
                self.client.garth.dump(TOKENSTORE)
                return
            except Exception:
                pass

        # Try library's built-in email/password login
        try:
            self.client = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)
            self.client.login()
            self.client.garth.dump(TOKENSTORE)
            return
        except Exception:
            pass

        # Fall back to custom SSO flow (handles Garmin SSO page changes)
        from garmin_auth import garmin_login, garmin_connect_with_ticket
        result = garmin_login(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)

        if result.get('mfa_required'):
            raise Exception(
                "Garmin requiere MFA. Usa la pagina de setup para conectar tu cuenta."
            )

        ticket = result['ticket']
        self.client = garmin_connect_with_ticket(
            config.GARMIN_EMAIL, config.GARMIN_PASSWORD, ticket
        )
        self.client.garth.dump(TOKENSTORE)

    def _call_with_retry(self, func, *args, **kwargs):
        """Call a Garmin API function, retry with re-login if token expired."""
        try:
            return func(*args, **kwargs)
        except Exception:
            # Token likely expired, re-login and retry once
            self.login()
            return func(*args, **kwargs)

    def get_stats_for_date(self, date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        return self._call_with_retry(self.client.get_stats, date_str)

    def get_sleep_data(self, date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        return self._call_with_retry(self.client.get_sleep_data, date_str)

    def get_activities(self, start_date=None, end_date=None, limit=10):
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        return self._call_with_retry(
            self.client.get_activities_by_date, start_str, end_str
        )

"""
Cliente de Garmin Connect
- Uses garth token persistence to avoid repeated login failures
- Auto-refreshes and re-saves tokens to keep the session alive
- Supports CI via GARMIN_TOKENS_DIR env var or GARMIN_TOKENS_JSON secret
- Falls back to custom SSO flow (garmin_auth.py) when library login fails
- Falls back to email/password only when tokens are missing or expired
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os
import sys
import tempfile
import config

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")


def _restore_tokens_from_env():
    """In CI, restore garth tokens from GARMIN_TOKENS_JSON env var to a temp dir."""
    tokens_json = os.environ.get('GARMIN_TOKENS_JSON')
    if not tokens_json:
        return None
    try:
        tokens = json.loads(tokens_json)
        tmpdir = os.path.join(tempfile.gettempdir(), 'garmin_tokens')
        os.makedirs(tmpdir, exist_ok=True)
        for filename, content in tokens.items():
            with open(os.path.join(tmpdir, filename), 'w') as f:
                json.dump(content, f)
        return tmpdir
    except Exception as e:
        print(f"[GARMIN] Error restaurando tokens desde env: {e}")
        return None


def _export_tokens_json(tokendir):
    """Export garth token files as a single JSON string (for saving back to GitHub Secrets)."""
    tokens = {}
    if not os.path.isdir(tokendir):
        return None
    for filename in os.listdir(tokendir):
        filepath = os.path.join(tokendir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r') as f:
                    tokens[filename] = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return json.dumps(tokens) if tokens else None


class GarminClient:
    def __init__(self):
        self.client = None
        self._tokendir = TOKENSTORE

    def login(self):
        # Try tokens from env var first (CI/GitHub Actions)
        env_tokendir = _restore_tokens_from_env()
        if env_tokendir:
            try:
                self.client = Garmin()
                self.client.login(env_tokendir)
                self.client.garth.dump(env_tokendir)
                self._tokendir = env_tokendir
                return
            except Exception as e:
                print(f"[GARMIN] Tokens de env fallaron: {e}")

        # Try saved tokens first (avoids Garmin rate-limiting/blocking)
        if os.path.isdir(TOKENSTORE):
            try:
                self.client = Garmin()
                self.client.login(TOKENSTORE)
                # Re-save tokens so refreshed tokens are persisted
                self.client.garth.dump(TOKENSTORE)
                self._tokendir = TOKENSTORE
                return
            except Exception:
                pass

        # Try library's built-in email/password login
        try:
            self.client = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)
            self.client.login()
            self.client.garth.dump(TOKENSTORE)
            self._tokendir = TOKENSTORE
            return
        except Exception:
            pass

        # Fall back to custom SSO flow (handles Garmin SSO page changes)
        from garmin_auth import garmin_login, garmin_verify_mfa, garmin_connect_with_ticket
        result = garmin_login(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)

        if result.get('mfa_required'):
            # Interactive MFA: prompt user for code if running in a terminal
            if not sys.stdin.isatty():
                raise Exception(
                    "Garmin requiere MFA. Corre el sync desde terminal para ingresar el codigo."
                )
            print("\n🔐 Garmin requiere verificacion MFA.")
            print("   Revisa tu app de autenticacion o SMS.")
            mfa_code = input("   Ingresa el codigo MFA: ").strip()
            if not mfa_code:
                raise Exception("No se ingreso codigo MFA.")
            ticket = garmin_verify_mfa(result['session'], mfa_code)
        else:
            ticket = result['ticket']

        self.client = garmin_connect_with_ticket(
            config.GARMIN_EMAIL, config.GARMIN_PASSWORD, ticket
        )
        self.client.garth.dump(TOKENSTORE)
        self._tokendir = TOKENSTORE

    def get_tokens_json(self):
        """Return current tokens as JSON string (for saving to GitHub Secrets)."""
        return _export_tokens_json(self._tokendir)

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

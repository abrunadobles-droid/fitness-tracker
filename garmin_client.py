"""
Cliente de Garmin Connect
- Uses garth token persistence to avoid repeated login failures
- Auto-refreshes and re-saves tokens to keep the session alive
- Supports CI via GARMIN_TOKENS_DIR env var or GARMIN_TOKENS_JSON secret
- Falls back to custom SSO flow (garmin_auth.py) when library login fails
- Falls back to email/password only when tokens are missing or expired
- Use GARMIN_DEBUG=1 env var for verbose logging
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os
import sys
import tempfile
import config

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")
DEBUG = os.environ.get('GARMIN_DEBUG', '') == '1'


def _debug(msg):
    """Print debug message if GARMIN_DEBUG=1."""
    if DEBUG:
        print(f"[GARMIN DEBUG] {msg}")


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
        """
        Login to Garmin Connect. Tries methods in order:
        1. Tokens from GARMIN_TOKENS_JSON env var (CI)
        2. Saved tokens in ~/.garmin_tokens/
        3. Email/password via garminconnect library
        4. Custom SSO flow with MFA support

        Each step logs the failure reason so auth issues can be diagnosed.
        """
        errors = []

        # Step 1: Try tokens from env var (CI/GitHub Actions)
        env_tokendir = _restore_tokens_from_env()
        if env_tokendir:
            try:
                _debug("Intentando login con tokens de env...")
                self.client = Garmin()
                self.client.login(env_tokendir)
                self.client.garth.dump(env_tokendir)
                self._tokendir = env_tokendir
                print("[GARMIN] Login exitoso con tokens de CI")
                return
            except Exception as e:
                errors.append(f"Tokens CI: {e}")
                _debug(f"Tokens de env fallaron: {e}")

        # Step 2: Try saved tokens (avoids Garmin rate-limiting/blocking)
        if os.path.isdir(TOKENSTORE):
            try:
                _debug(f"Intentando login con tokens guardados en {TOKENSTORE}...")
                self.client = Garmin()
                self.client.login(TOKENSTORE)
                self.client.garth.dump(TOKENSTORE)
                self._tokendir = TOKENSTORE
                print("[GARMIN] Login exitoso con tokens guardados")
                return
            except Exception as e:
                errors.append(f"Tokens guardados: {e}")
                _debug(f"Tokens guardados fallaron: {e}")

        # Step 3: Try library's built-in email/password login
        email = config.GARMIN_EMAIL
        password = config.GARMIN_PASSWORD
        if not email or not password:
            errors.append("Credenciales: GARMIN_EMAIL o GARMIN_PASSWORD no configurados")
            _debug("Sin credenciales configuradas, saltando login con email/password")
        else:
            try:
                _debug(f"Intentando login con email/password ({email})...")
                self.client = Garmin(email, password)
                self.client.login()
                self.client.garth.dump(TOKENSTORE)
                self._tokendir = TOKENSTORE
                print("[GARMIN] Login exitoso con email/password")
                return
            except Exception as e:
                errors.append(f"Email/password: {e}")
                _debug(f"Email/password fallo: {e}")

        # Step 4: Fall back to custom SSO flow (handles Garmin SSO page changes)
        if not email or not password:
            self._raise_auth_error(errors)

        try:
            _debug("Intentando login via SSO custom...")
            from garmin_auth import garmin_login, garmin_verify_mfa, garmin_connect_with_ticket
            result = garmin_login(email, password)

            if result.get('mfa_required'):
                self._handle_mfa(result, email, password, errors)
            else:
                ticket = result['ticket']
                _debug(f"SSO retorno ticket: {ticket[:20]}...")
                self.client = garmin_connect_with_ticket(email, password, ticket)
                self.client.garth.dump(TOKENSTORE)
                self._tokendir = TOKENSTORE
                print("[GARMIN] Login exitoso via SSO")
                return
        except Exception as e:
            if "MFA" not in str(e):
                errors.append(f"SSO custom: {e}")
                _debug(f"SSO custom fallo: {e}")

        self._raise_auth_error(errors)

    def _handle_mfa(self, result, email, password, errors):
        """Handle MFA challenge from SSO flow."""
        from garmin_auth import garmin_verify_mfa, garmin_connect_with_ticket

        if not sys.stdin.isatty():
            raise Exception(
                "Garmin requiere verificacion MFA pero no hay terminal interactiva.\n"
                "Corre el sync desde terminal: python3 garmin_sync.py"
            )

        print("\n" + "=" * 50)
        print("  Garmin requiere verificacion adicional (MFA)")
        print("=" * 50)
        print()
        print("  Esto puede pasar si:")
        print("  - Tienes MFA/2FA activado en tu cuenta Garmin")
        print("  - Garmin detecto un login desde un dispositivo nuevo")
        print("  - Garmin envio un codigo a tu email o SMS")
        print()
        print("  Revisa tu email, SMS, o app de autenticacion.")
        print()

        mfa_code = input("  Ingresa el codigo de verificacion (o 'skip' para cancelar): ").strip()
        if not mfa_code or mfa_code.lower() == 'skip':
            errors.append("MFA: usuario cancelo la verificacion")
            self._raise_auth_error(errors)

        try:
            ticket = garmin_verify_mfa(result['session'], mfa_code)
            self.client = garmin_connect_with_ticket(email, password, ticket)
            self.client.garth.dump(TOKENSTORE)
            self._tokendir = TOKENSTORE
            print("[GARMIN] Login exitoso via MFA")
        except Exception as e:
            raise Exception(f"Codigo MFA invalido o expirado: {e}")

    def _raise_auth_error(self, errors):
        """Raise a detailed auth error with all attempted methods."""
        msg = "No se pudo conectar a Garmin Connect.\n"
        msg += "\nMetodos intentados:\n"
        for i, err in enumerate(errors, 1):
            msg += f"  {i}. {err}\n"
        msg += "\nSoluciones:\n"
        msg += "  - Verifica email/password en .streamlit/secrets.toml seccion [garmin]\n"
        msg += "  - O exporta: GARMIN_EMAIL='tu@email' GARMIN_PASSWORD='tupass'\n"
        msg += "  - Si ya tienes tokens, revisa ~/.garmin_tokens/\n"
        msg += "  - Para diagnostico: GARMIN_DEBUG=1 python3 garmin_sync.py\n"
        raise Exception(msg)

    def get_tokens_json(self):
        """Return current tokens as JSON string (for saving to GitHub Secrets)."""
        return _export_tokens_json(self._tokendir)

    def _call_with_retry(self, func, *args, **kwargs):
        """Call a Garmin API function, retry with re-login if token expired."""
        try:
            return func(*args, **kwargs)
        except Exception:
            _debug("API call fallo, re-intentando con re-login...")
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

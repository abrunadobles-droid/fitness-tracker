"""
Cliente de Garmin Connect
- Uses garth token persistence to avoid repeated login failures
- Auto-refreshes and re-saves tokens to keep the session alive
- Supports CI via GARMIN_TOKENS_DIR env var or GARMIN_TOKENS_JSON secret
- Falls back to email/password with MFA support
- Use GARMIN_DEBUG=1 env var for verbose logging
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os
import sys
import tempfile
import inspect
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


def _prompt_mfa():
    """Prompt for MFA code from terminal, or raise if not interactive."""
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
    code = input("  Ingresa el codigo de verificacion (o 'skip' para cancelar): ").strip()
    if not code or code.lower() == 'skip':
        raise Exception("MFA: usuario cancelo la verificacion")
    return code


def _garmin_with_mfa(email, password):
    """Create Garmin client with MFA support, compatible with old and new versions."""
    # Check if garminconnect supports prompt_mfa
    sig = inspect.signature(Garmin.__init__)
    if 'prompt_mfa' in sig.parameters:
        return Garmin(email, password, prompt_mfa=_prompt_mfa)
    else:
        return Garmin(email, password)


def _login_via_garth_direct(email, password):
    """
    Login using garth.login() directly, bypassing garminconnect.
    This can work when garminconnect's login fails due to version issues.
    Returns an authenticated Garmin client.
    """
    import garth

    _debug("Intentando login via garth.login() directo...")
    garth.login(email, password, prompt_mfa=_prompt_mfa)
    garth.save(TOKENSTORE)
    _debug(f"garth tokens guardados en {TOKENSTORE}")

    # Now create Garmin client and load the saved tokens
    client = Garmin()
    client.login(TOKENSTORE)
    return client


def _debug_oauth1_exchange(ticket):
    """Debug the OAuth1 token exchange to understand 401 errors."""
    try:
        import requests
        from requests_oauthlib import OAuth1Session

        # Fetch consumer credentials
        consumer = requests.get('https://thegarth.s3.amazonaws.com/oauth_consumer.json', timeout=10).json()
        _debug(f"OAuth consumer key: {consumer['consumer_key'][:12]}...")

        # Create OAuth1 session
        sess = OAuth1Session(consumer['consumer_key'], consumer['consumer_secret'])
        url = (
            f"https://connectapi.garmin.com/oauth-service/oauth/"
            f"preauthorized?ticket={ticket}"
            f"&login-url=https://sso.garmin.com/sso/embed"
            f"&accepts-mfa-tokens=true"
        )
        headers = {'User-Agent': 'com.garmin.android.apps.connectmobile'}

        resp = sess.get(url, headers=headers, timeout=15)
        _debug(f"OAuth1 exchange status: {resp.status_code}")
        _debug(f"OAuth1 exchange response: {resp.text[:300]}")
        if resp.status_code == 200:
            _debug("OAuth1 exchange EXITOSO con llamada manual!")
        return resp
    except Exception as e:
        _debug(f"OAuth1 debug exchange error: {e}")
        return None


class GarminClient:
    def __init__(self):
        self.client = None
        self._tokendir = TOKENSTORE

    def login(self):
        """
        Login to Garmin Connect. Tries methods in order:
        1. Tokens from GARMIN_TOKENS_JSON env var (CI)
        2. Saved tokens in ~/.garmin_tokens/
        3. garth.login() directly (bypasses garminconnect version issues)
        4. Email/password via garminconnect library

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
                _debug(f"Borrando tokens corruptos en {TOKENSTORE}...")
                import shutil
                shutil.rmtree(TOKENSTORE, ignore_errors=True)

        # Need credentials for steps 3-4
        email = config.GARMIN_EMAIL
        password = config.GARMIN_PASSWORD
        if not email or not password:
            errors.append("Credenciales: GARMIN_EMAIL o GARMIN_PASSWORD no configurados")
            _debug("Sin credenciales configuradas")
            self._raise_auth_error(errors)

        # Step 3: Try garth.login() directly (most reliable, bypasses garminconnect)
        try:
            self.client = _login_via_garth_direct(email, password)
            self.client.garth.dump(TOKENSTORE)
            self._tokendir = TOKENSTORE
            print("[GARMIN] Login exitoso via garth directo")
            return
        except Exception as e:
            errors.append(f"garth directo: {e}")
            _debug(f"garth directo fallo: {e}")

        # Step 4: Try garminconnect library login (with MFA support if available)
        try:
            _debug(f"Intentando login con garminconnect ({email})...")
            self.client = _garmin_with_mfa(email, password)
            self.client.login()
            self.client.garth.dump(TOKENSTORE)
            self._tokendir = TOKENSTORE
            print("[GARMIN] Login exitoso con garminconnect")
            return
        except Exception as e:
            errors.append(f"garminconnect: {e}")
            _debug(f"garminconnect fallo: {e}")

            # Debug the OAuth1 exchange if ticket-related 401
            if '401' in str(e) and 'preauthorized' in str(e):
                _debug("=== Diagnostico OAuth1 ===")
                _debug("El ticket SSO se obtuvo correctamente pero el intercambio OAuth1 falla.")
                _debug("Esto puede ser un problema temporal de Garmin o de la version de garth.")
                _debug(f"garth version: {_get_garth_version()}")
                _debug(f"garminconnect version: {_get_garminconnect_version()}")

        self._raise_auth_error(errors)

    def _raise_auth_error(self, errors):
        """Raise a detailed auth error with all attempted methods."""
        msg = "No se pudo conectar a Garmin Connect.\n"
        msg += "\nMetodos intentados:\n"
        for i, err in enumerate(errors, 1):
            msg += f"  {i}. {err}\n"
        msg += "\nSoluciones:\n"
        msg += "  - Actualiza dependencias: pip3 install --upgrade garth garminconnect\n"
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


def _get_garth_version():
    try:
        import garth
        return getattr(garth, '__version__', 'unknown')
    except Exception:
        return 'not installed'


def _get_garminconnect_version():
    try:
        import garminconnect
        return getattr(garminconnect, '__version__', 'unknown')
    except Exception:
        return 'not installed'

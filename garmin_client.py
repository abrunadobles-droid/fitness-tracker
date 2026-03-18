"""
Cliente de Garmin Connect
- Token persistence via garth (evita login repetido y rate-limiting)
- CI: restaura tokens desde GARMIN_TOKENS_JSON env var
- Local: tokens en ~/.garmin_tokens/
- Fallback: email/password con soporte MFA
- Diagnóstico: GARMIN_DEBUG=1
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
    if DEBUG:
        print(f"[GARMIN DEBUG] {msg}")


def _restore_tokens_from_env():
    """En CI, restaurar garth tokens desde GARMIN_TOKENS_JSON a un dir temporal."""
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
    """Exportar tokens como JSON string para GitHub Secrets."""
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
    """Prompt MFA desde terminal."""
    if not sys.stdin.isatty():
        raise Exception(
            "Garmin requiere verificacion MFA pero no hay terminal interactiva.\n"
            "Corre: python3 garmin_setup_auth.py"
        )
    print("\n" + "=" * 50)
    print("  Garmin requiere verificacion adicional (MFA)")
    print("=" * 50)
    print("\n  Revisa tu email, SMS, o app de autenticacion.\n")
    code = input("  Codigo de verificacion (o 'skip' para cancelar): ").strip()
    if not code or code.lower() == 'skip':
        raise Exception("MFA: usuario cancelo la verificacion")
    return code


class GarminClient:
    def __init__(self):
        self.client = None
        self._tokendir = TOKENSTORE

    def login(self):
        """
        Login a Garmin Connect. Orden de prioridad:
        1. Tokens desde GARMIN_TOKENS_JSON env var (CI)
        2. Tokens guardados en ~/.garmin_tokens/
        3. Email/password via garminconnect (con soporte MFA)
        """
        errors = []

        # Step 1: Tokens desde env var (CI/GitHub Actions)
        env_tokendir = _restore_tokens_from_env()
        if env_tokendir:
            try:
                _debug("Login con tokens de CI...")
                self.client = Garmin()
                self.client.login(env_tokendir)
                self.client.garth.dump(env_tokendir)
                self._tokendir = env_tokendir
                print("[GARMIN] Login exitoso con tokens de CI")
                return
            except Exception as e:
                errors.append(f"Tokens CI: {e}")
                _debug(f"Tokens de env fallaron: {e}")

        # Step 2: Tokens guardados localmente
        if os.path.isdir(TOKENSTORE):
            try:
                _debug(f"Login con tokens en {TOKENSTORE}...")
                self.client = Garmin()
                self.client.login(TOKENSTORE)
                self.client.garth.dump(TOKENSTORE)
                self._tokendir = TOKENSTORE
                print("[GARMIN] Login exitoso con tokens guardados")
                return
            except Exception as e:
                errors.append(f"Tokens guardados: {e}")
                _debug(f"Tokens guardados fallaron: {e}")
                import shutil
                shutil.rmtree(TOKENSTORE, ignore_errors=True)

        # Step 3: Email/password
        email = config.GARMIN_EMAIL
        password = config.GARMIN_PASSWORD
        if not email or not password:
            errors.append("GARMIN_EMAIL o GARMIN_PASSWORD no configurados")
            self._raise_auth_error(errors)

        try:
            _debug(f"Login con email/password ({email})...")
            self.client = Garmin(email, password, prompt_mfa=_prompt_mfa)
            self.client.login()
            self.client.garth.dump(TOKENSTORE)
            self._tokendir = TOKENSTORE
            print("[GARMIN] Login exitoso con email/password")
            return
        except Exception as e:
            errors.append(f"Email/password: {e}")
            _debug(f"Login fallo: {e}")

        self._raise_auth_error(errors)

    def _raise_auth_error(self, errors):
        msg = "No se pudo conectar a Garmin Connect.\n"
        msg += "\nMetodos intentados:\n"
        for i, err in enumerate(errors, 1):
            msg += f"  {i}. {err}\n"
        msg += "\nSoluciones:\n"
        msg += "  - Correr: python3.12 garmin_setup_auth.py\n"
        msg += "  - Verificar garth >= 0.7.9: pip3 show garth\n"
        msg += "  - Verificar credenciales en .streamlit/secrets.toml\n"
        msg += "  - Diagnostico: GARMIN_DEBUG=1 python3 garmin_sync.py\n"
        raise Exception(msg)

    def get_tokens_json(self):
        """Tokens como JSON string para GitHub Secrets."""
        return _export_tokens_json(self._tokendir)

    def _call_with_retry(self, func, *args, **kwargs):
        """Llamar API con retry si el token expiró."""
        try:
            return func(*args, **kwargs)
        except Exception:
            _debug("API call fallo, re-login...")
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

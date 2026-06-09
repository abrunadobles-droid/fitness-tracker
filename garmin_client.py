"""
Cliente de Garmin Connect (garminconnect >= 0.3.1)

Token persistence: una vez logueado, tokens se guardan en TOKENSTORE.
Los refreshes no tocan SSO, así que no hay 429.
Solo el primer login (o tokens completamente expirados) requiere SSO.

Uso:
    from garmin_client import GarminClient
    garmin = GarminClient()
    garmin.login()
    stats = garmin.get_stats_for_date(datetime.now())
"""

from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os
import sys
import config

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")


def _restore_tokens_from_env():
    """En CI: si GARMIN_TOKENS_JSON existe, escribe los tokens a TOKENSTORE.

    Mismo patrón que WHOOP (WHOOP_TOKENS_JSON). NO es un método de auth nuevo:
    es la misma persistencia basada en tokens, solo que la fuente es una env var
    en vez de un archivo local. Evita tocar SSO (sin 429) en el cron.
    """
    tokens_json = os.environ.get("GARMIN_TOKENS_JSON")
    if not tokens_json:
        return
    try:
        files = json.loads(tokens_json)
    except json.JSONDecodeError:
        print("[GARMIN] Error parseando GARMIN_TOKENS_JSON")
        return
    if not isinstance(files, dict) or not files:
        return
    os.makedirs(TOKENSTORE, exist_ok=True)
    for filename, content in files.items():
        filepath = os.path.join(TOKENSTORE, filename)
        with open(filepath, "w") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                json.dump(content, f)
    print(f"[GARMIN] Tokens restaurados desde env a {TOKENSTORE}")


def _prompt_mfa():
    if not sys.stdin.isatty():
        raise Exception("Garmin requiere MFA pero no hay terminal interactiva.")
    print("\n  Garmin requiere verificación MFA.")
    print("  Revisa tu email o app de autenticación.\n")
    code = input("  Código: ").strip()
    if not code or code.lower() == 'skip':
        raise Exception("MFA cancelado")
    return code


class GarminClient:
    def __init__(self):
        self.client = None

    def login(self):
        """Login con token persistence. Intenta tokens guardados primero."""
        # En CI, materializar tokens del env antes de intentar login
        _restore_tokens_from_env()

        email = config.GARMIN_EMAIL
        password = config.GARMIN_PASSWORD

        # Crear cliente con credenciales (se usan solo si no hay tokens)
        self.client = Garmin(
            email=email or None,
            password=password or None,
            prompt_mfa=_prompt_mfa,
        )

        # login() intenta cargar tokens de TOKENSTORE primero.
        # Solo toca SSO si no hay tokens guardados.
        self.client.login(tokenstore=TOKENSTORE)

        # Guardar tokens actualizados
        os.makedirs(TOKENSTORE, exist_ok=True)
        self.client.client.dump(TOKENSTORE)

    def get_stats_for_date(self, date=None):
        if date is None:
            date = datetime.now()
        return self.client.get_stats(date.strftime('%Y-%m-%d'))

    def get_activities(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
        return self.client.get_activities_by_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
        )

    def get_tokens_json(self):
        """Exportar tokens como JSON string para GitHub Secrets."""
        if not os.path.isdir(TOKENSTORE):
            return None
        tokens = {}
        for filename in os.listdir(TOKENSTORE):
            filepath = os.path.join(TOKENSTORE, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath) as f:
                        tokens[filename] = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
        return json.dumps(tokens) if tokens else None

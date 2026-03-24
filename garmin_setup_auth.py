#!/usr/bin/env python3
"""
Garmin Connect - Setup de autenticación.

Hace login a Garmin Connect, guarda tokens localmente (~/.garmin_tokens/),
y opcionalmente exporta los tokens como JSON para GitHub Secrets.

Requisitos:
    brew install python@3.12
    python3.12 -m pip install garth>=0.7.9 garminconnect requests

Uso:
    python3.12 garmin_setup_auth.py
    python3.12 garmin_setup_auth.py --export  # También exporta JSON para CI
"""
import json
import os
import sys

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")


def check_requirements():
    """Verificar versión de Python y garth."""
    print(f"Python: {sys.version}")

    if sys.version_info < (3, 10):
        print(
            "\n[ERROR] Se requiere Python 3.10+. Tenés Python "
            f"{sys.version_info.major}.{sys.version_info.minor}."
        )
        print("Solución:")
        print("  brew install python@3.12")
        print("  python3.12 -m pip install garth>=0.7.9 garminconnect")
        print("  python3.12 garmin_setup_auth.py")
        sys.exit(1)

    try:
        import garth
        version = getattr(garth, '__version__', '0.0.0')
        print(f"garth: {version}")
        major, minor, patch = [int(x) for x in version.split('.')[:3]]
        if (major, minor, patch) < (0, 7, 9):
            print(f"\n[WARN] garth {version} tiene un bug de OAuth1 (iOS→Android mismatch).")
            print("Actualizar: python3.12 -m pip install garth>=0.7.9")
    except ImportError:
        print("\n[ERROR] garth no está instalado.")
        print("  python3.12 -m pip install garth>=0.7.9 garminconnect")
        sys.exit(1)

    try:
        import garminconnect
        print(f"garminconnect: {getattr(garminconnect, '__version__', 'unknown')}")
    except ImportError:
        print("\n[ERROR] garminconnect no está instalado.")
        print("  python3.12 -m pip install garminconnect")
        sys.exit(1)


def get_credentials():
    """Obtener credenciales de Garmin."""
    # Intentar desde secrets.toml
    secrets_path = os.path.join(
        os.path.dirname(__file__), '.streamlit', 'secrets.toml'
    )
    email = os.environ.get('GARMIN_EMAIL', '')
    password = os.environ.get('GARMIN_PASSWORD', '')

    if not email and os.path.exists(secrets_path):
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                tomllib = None

        if tomllib:
            with open(secrets_path, 'rb') as f:
                secrets = tomllib.load(f)
            garmin = secrets.get('garmin', {})
            email = garmin.get('email', '')
            password = garmin.get('password', '')

    if not email:
        email = input("Email de Garmin Connect: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Password de Garmin Connect: ")

    return email, password


def login_and_save(email, password):
    """Hacer login y guardar tokens. Reintenta automáticamente en caso de 429."""
    import garth
    import time

    def prompt_mfa():
        print("\n" + "=" * 50)
        print("  Garmin requiere verificación MFA")
        print("=" * 50)
        print("  Revisá tu email, SMS, o app de autenticación.")
        return input("  Código de verificación: ").strip()

    max_retries = 5
    # Backoff: 2min, 5min, 10min, 20min, 30min
    wait_times = [120, 300, 600, 1200, 1800]

    for attempt in range(1, max_retries + 1):
        print(f"\nConectando a Garmin Connect... (intento {attempt}/{max_retries})")
        try:
            garth.login(email, password, prompt_mfa=prompt_mfa)
            garth.save(TOKENSTORE)
            print(f"\n[OK] Tokens guardados en {TOKENSTORE}/")

            # Verificar que funcionan
            from garminconnect import Garmin
            client = Garmin()
            client.login(TOKENSTORE)
            name = client.get_full_name()
            print(f"[OK] Conectado como: {name}")
            return client

        except Exception as e:
            error_str = str(e)
            if '429' in error_str:
                if attempt < max_retries:
                    wait = wait_times[attempt - 1]
                    mins = wait // 60
                    print(f"\n[429] Garmin te bloqueó por rate limiting.")
                    print(f"      Reintentando en {mins} minutos... (dejá el script corriendo)")
                    print(f"      Podés cancelar con Ctrl+C y reintentar mañana.")
                    time.sleep(wait)
                else:
                    print(f"\n[429] Garmin sigue bloqueando después de {max_retries} intentos.")
                    print("      Esperá varias horas (o hasta mañana) e intentá de nuevo.")
                    raise
            else:
                raise


def export_tokens():
    """Exportar tokens como JSON para GitHub Secrets."""
    tokens = {}
    for filename in os.listdir(TOKENSTORE):
        filepath = os.path.join(TOKENSTORE, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r') as f:
                    tokens[filename] = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    if not tokens:
        print("[ERROR] No se encontraron tokens para exportar.")
        return

    tokens_json = json.dumps(tokens)
    print("\n" + "=" * 60)
    print("  GARMIN_TOKENS_JSON para GitHub Secrets:")
    print("=" * 60)
    print(tokens_json)
    print("=" * 60)
    print("\nPara configurar en GitHub:")
    print("  1. Ir a tu repo → Settings → Secrets and variables → Actions")
    print("  2. Crear/actualizar secret: GARMIN_TOKENS_JSON")
    print("  3. Pegar el JSON de arriba")


def main():
    print("=" * 60)
    print("  Garmin Connect - Setup de Autenticación")
    print("=" * 60)

    check_requirements()
    email, password = get_credentials()
    login_and_save(email, password)

    if '--export' in sys.argv:
        export_tokens()
    else:
        print("\nTip: Corré con --export para obtener el JSON de GitHub Secrets:")
        print(f"  python3 {sys.argv[0]} --export")

    print("\n[LISTO] Ahora podés correr:")
    print("  python3 garmin_sync.py")


if __name__ == '__main__':
    main()

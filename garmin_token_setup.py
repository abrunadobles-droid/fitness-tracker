"""
Garmin Token Setup - Run this locally to generate auth tokens.

Usage:
    python3 garmin_token_setup.py

This will:
1. Log into Garmin SSO with your credentials
2. Ask for MFA code if needed
3. Save garth tokens to .garmin_tokens/
4. Commit and push so Streamlit Cloud can use them

After running this, the dashboard will use saved tokens
instead of logging in each time.
"""
import os
import sys
import json

# Add project dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # Load credentials from .streamlit/secrets.toml or ask user
    email = None
    password = None

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            tomllib = None

    secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'secrets.toml')
    if tomllib and os.path.exists(secrets_path):
        with open(secrets_path, 'rb') as f:
            secrets = tomllib.load(f)
            email = secrets.get('garmin', {}).get('email', '')
            password = secrets.get('garmin', {}).get('password', '')

    if not email:
        email = input("Email de Garmin: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Password de Garmin: ").strip()

    print(f"\nLogueando como {email}...")

    from garmin_auth import garmin_login, garmin_verify_mfa, garmin_connect_with_ticket

    # Phase 1: Login
    result = garmin_login(email, password)

    if result.get('mfa_required'):
        print("\nGarmin requiere codigo MFA.")
        mfa_code = input("Ingresa el codigo de 6 digitos: ").strip()

        # Phase 2: Verify MFA
        ticket = garmin_verify_mfa(result['session'], mfa_code)
        print("MFA verificado!")
    else:
        ticket = result['ticket']
        print("Login exitoso (sin MFA)!")

    # Phase 3: Get authenticated client with tokens
    print("Obteniendo tokens OAuth...")
    client = garmin_connect_with_ticket(email, password, ticket)

    # Save tokens in project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    token_dir = os.path.join(project_dir, '.garmin_tokens')
    client.garth.dump(token_dir)
    print(f"\nTokens guardados en: {token_dir}/")

    # Also save to home directory as backup
    home_token_dir = os.path.expanduser("~/.garmin_tokens")
    client.garth.dump(home_token_dir)

    # Verify tokens work
    try:
        display_name = client.garth.profile.get("displayName", "?")
        print(f"Conectado como: {display_name}")
    except Exception:
        print("Tokens guardados (no se pudo verificar perfil)")

    print("\nAhora commitea y pushea los tokens:")
    print("  git add .garmin_tokens/")
    print('  git commit -m "Add Garmin auth tokens"')
    print("  git push origin main")
    print("\nDespues de eso, la app usa los tokens sin necesitar login.")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Garmin Browser Auth — login via browser real para evitar el bloqueo 429.

Desde ~17 marzo 2026, Garmin bloqueó el endpoint /mobile/api/login para
scripts. Este workaround abre un browser real (Chromium via Playwright),
te deja loguearte normalmente, y captura el ticket SSO. Luego usa garth
directamente para intercambiar el ticket por tokens OAuth.

Requisitos:
    pip3 install playwright garth garminconnect
    python3 -m playwright install chromium

Uso:
    python3 garmin_browser_auth.py
    python3 garmin_browser_auth.py --export  # También muestra JSON para GitHub Secrets
"""

import json
import os
import re
import sys
import time

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")


def browser_login():
    """Abrir browser real, esperar login del usuario, capturar ticket SSO."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n[ERROR] Playwright no está instalado.")
        print("  Correr:")
        print("    pip3 install playwright")
        print("    python3 -m playwright install chromium")
        sys.exit(1)

    ticket = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Usar el mismo SSO embed URL que garth usa internamente
        sso_url = (
            "https://sso.garmin.com/sso/embed"
            "?id=gauth-widget"
            "&embedWidget=true"
            "&gauthHost=https://sso.garmin.com/sso"
            "&clientId=GarminConnect"
            "&locale=en_US"
            "&redirectAfterAccountLoginUrl=https://sso.garmin.com/sso/embed"
            "&service=https://sso.garmin.com/sso/embed"
        )
        page.goto(sso_url)

        print()
        print("=" * 50)
        print("  Se abrió el browser — logueate con tu")
        print("  cuenta de Garmin. La ventana se cierra")
        print("  automáticamente cuando termine.")
        print("=" * 50)
        print()

        max_wait = 300  # 5 minutos
        start = time.time()
        while time.time() - start < max_wait:
            try:
                content = page.content()
                m = re.search(r'ticket=(ST-[A-Za-z0-9\-]+)', content)
                if m:
                    ticket = m.group(1)
                    break

                url = page.url
                if "ticket=" in url:
                    m = re.search(r'ticket=(ST-[A-Za-z0-9\-]+)', url)
                    if m:
                        ticket = m.group(1)
                        break
            except Exception:
                pass

            page.wait_for_timeout(500)

        browser.close()

    if not ticket:
        print("[ERROR] Timeout esperando login (5 min). Intentá de nuevo.")
        sys.exit(1)

    return ticket


def exchange_ticket(ticket):
    """Usar garth internamente para intercambiar ticket por OAuth1+OAuth2."""
    import garth
    from garth.sso import get_oauth1_token, exchange

    # Crear un client de garth configurado
    client = garth.Client(domain="garmin.com")

    # Intercambiar ticket → OAuth1 (usa garth's GarminOAuth1Session)
    print("  Intercambiando ticket por OAuth1 (via garth)...")
    oauth1 = get_oauth1_token(ticket, client)
    print(f"  OAuth1 OK: {oauth1.oauth_token[:20]}...")

    # Intercambiar OAuth1 → OAuth2
    print("  Intercambiando OAuth1 por OAuth2 (via garth)...")
    oauth2 = exchange(oauth1, client)
    print(f"  OAuth2 OK (expira en {oauth2.expires_in // 3600}h)")

    # Guardar en el client global de garth
    client.oauth1_token = oauth1
    client.oauth2_token = oauth2

    return client


def export_tokens():
    """Mostrar tokens como JSON para GitHub Secrets."""
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
    print("  1. Ir a tu repo → Settings → Secrets → Actions")
    print("  2. Crear/actualizar: GARMIN_TOKENS_JSON")
    print("  3. Pegar el JSON de arriba")


def main():
    print("=" * 60)
    print("  Garmin Connect - Auth via Browser")
    print("  (Workaround para bloqueo 429 de marzo 2026)")
    print("=" * 60)

    # Step 1: Browser login → capturar ticket SSO
    print("\nAbriendo browser...")
    ticket = browser_login()
    print(f"  Ticket obtenido: {ticket[:30]}...")

    # Step 2: Usar garth para intercambiar ticket → OAuth1 → OAuth2
    print("\nIntercambiando tokens (via garth)...")
    client = exchange_ticket(ticket)

    # Step 3: Guardar tokens via garth (formato 100% compatible)
    client.dump(TOKENSTORE)
    print(f"\n[OK] Tokens guardados en {TOKENSTORE}/")

    # Step 4: Verificar con garminconnect
    print("\nVerificando con garminconnect...")
    try:
        from garminconnect import Garmin
        gc = Garmin()
        gc.login(TOKENSTORE)
        name = gc.get_full_name()
        print(f"[OK] Conectado como: {name}")
    except Exception as e:
        print(f"[WARN] Verificación falló: {e}")
        print("  Los tokens se guardaron — probá: python3 garmin_sync.py --all")

    if '--export' in sys.argv:
        export_tokens()
    else:
        print("\nTip: Corré con --export para el JSON de GitHub Secrets")

    print("\n[LISTO] Ahora corré:")
    print("  python3 garmin_sync.py --all")


if __name__ == "__main__":
    main()

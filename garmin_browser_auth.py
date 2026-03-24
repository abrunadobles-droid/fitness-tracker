#!/usr/bin/env python3
"""
Garmin Browser Auth — login via browser real para evitar el bloqueo 429.

Desde ~17 marzo 2026, Garmin bloqueó el endpoint /mobile/api/login para
scripts. Este workaround abre un browser real (Chromium via Playwright),
te deja loguearte normalmente, y captura los tokens OAuth.

Requisitos:
    pip3 install playwright requests requests-oauthlib
    python3 -m playwright install chromium

Uso:
    python3 garmin_browser_auth.py
    python3 garmin_browser_auth.py --export  # También muestra JSON para GitHub Secrets

Basado en: https://gist.github.com/coleman8er/5c8e192d2aa3c8a3a6220c5702e8a5e6
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs

import requests
from requests_oauthlib import OAuth1Session

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")
OAUTH_CONSUMER_URL = "https://thegarth.s3.amazonaws.com/oauth_consumer.json"
ANDROID_UA = "com.garmin.android.apps.connectmobile"


def get_oauth_consumer():
    """Fetch OAuth consumer key/secret (mismos que usa garth)."""
    resp = requests.get(OAUTH_CONSUMER_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_oauth1_token(ticket, consumer):
    """Intercambiar ticket SSO por token OAuth1."""
    sess = OAuth1Session(
        consumer["consumer_key"],
        consumer["consumer_secret"],
    )
    url = (
        f"https://connectapi.garmin.com/oauth-service/oauth/"
        f"preauthorized?ticket={ticket}"
        f"&login-url=https://sso.garmin.com/sso/embed"
        f"&accepts-mfa-tokens=true"
    )
    resp = sess.get(url, headers={"User-Agent": ANDROID_UA}, timeout=15)
    resp.raise_for_status()
    parsed = parse_qs(resp.text)
    token = {k: v[0] for k, v in parsed.items()}
    token["domain"] = "garmin.com"
    return token


def exchange_oauth2(oauth1, consumer):
    """Intercambiar token OAuth1 por OAuth2."""
    sess = OAuth1Session(
        consumer["consumer_key"],
        consumer["consumer_secret"],
        resource_owner_key=oauth1["oauth_token"],
        resource_owner_secret=oauth1["oauth_token_secret"],
    )
    url = "https://connectapi.garmin.com/oauth-service/oauth/exchange/user/2.0"
    data = {}
    if oauth1.get("mfa_token"):
        data["mfa_token"] = oauth1["mfa_token"]
    resp = sess.post(
        url,
        headers={
            "User-Agent": ANDROID_UA,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=data,
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json()
    token["expires_at"] = int(time.time() + token["expires_in"])
    token["refresh_token_expires_at"] = int(
        time.time() + token["refresh_token_expires_in"]
    )
    return token


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


def save_tokens(oauth1, oauth2):
    """Guardar tokens via garth para formato 100% compatible con garminconnect."""
    import garth
    from garth import sso as garth_sso

    # Guardar tokens usando garth (garantiza formato correcto)
    garth.configure(domain="garmin.com")
    garth.client.oauth1_token = garth_sso.OAuth1Token(**oauth1)
    garth.client.oauth2_token = garth.OAuth2Token(**oauth2)
    garth.save(TOKENSTORE)
    print(f"\n[OK] Tokens guardados en {TOKENSTORE}/ (via garth)")

    # Verificar que garminconnect los puede leer
    try:
        from garminconnect import Garmin
        client = Garmin()
        client.login(TOKENSTORE)
        name = client.get_full_name()
        print(f"[OK] Verificado con garminconnect: {name}")
    except Exception as e:
        # Fallback: guardar manualmente si garth no coopera
        print(f"[WARN] garth save no fue compatible, guardando manualmente...")
        os.makedirs(TOKENSTORE, exist_ok=True)
        with open(os.path.join(TOKENSTORE, "oauth1_token.json"), "w") as f:
            json.dump(oauth1, f, indent=2)
        with open(os.path.join(TOKENSTORE, "oauth2_token.json"), "w") as f:
            json.dump(oauth2, f, indent=2)
        print(f"[OK] Tokens guardados manualmente en {TOKENSTORE}/")


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

    # Step 1: OAuth consumer credentials
    print("\nObteniendo credenciales OAuth...")
    consumer = get_oauth_consumer()

    # Step 2: Browser login
    print("Abriendo browser...")
    ticket = browser_login()
    print(f"  Ticket obtenido: {ticket[:30]}...")

    # Step 3: OAuth1
    print("Intercambiando ticket por OAuth1...")
    oauth1 = get_oauth1_token(ticket, consumer)
    print(f"  OAuth1 OK")

    # Step 4: OAuth2
    print("Intercambiando OAuth1 por OAuth2...")
    oauth2 = exchange_oauth2(oauth1, consumer)
    print(f"  OAuth2 OK (expira en {oauth2['expires_in'] // 3600}h)")

    # Step 5: Verificar
    print("Verificando tokens...")
    verify = requests.get(
        "https://connectapi.garmin.com/userprofile-service/socialProfile",
        headers={
            "User-Agent": "GCM-iOS-5.7.2.1",
            "Authorization": f"Bearer {oauth2['access_token']}",
        },
        timeout=15,
    )
    verify.raise_for_status()
    profile = verify.json()
    print(f"  Conectado como: {profile.get('displayName', 'unknown')}")

    # Step 6: Guardar (save_tokens ya verifica con garminconnect)
    save_tokens(oauth1, oauth2)

    if '--export' in sys.argv:
        export_tokens()
    else:
        print("\nTip: Corré con --export para el JSON de GitHub Secrets")

    print("\n[LISTO] Ahora corré:")
    print("  python3 garmin_sync.py --all")


if __name__ == "__main__":
    main()

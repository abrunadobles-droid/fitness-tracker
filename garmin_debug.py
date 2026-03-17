"""
Diagnostic script for Garmin OAuth1 exchange 401 issue.
Run: GARMIN_EMAIL='...' GARMIN_PASSWORD='...' python3 garmin_debug.py
"""
import os
import sys
import json
import requests
from requests_oauthlib import OAuth1Session
from urllib.parse import parse_qs

email = os.environ.get('GARMIN_EMAIL', '')
password = os.environ.get('GARMIN_PASSWORD', '')
if not email or not password:
    print("Set GARMIN_EMAIL and GARMIN_PASSWORD env vars")
    sys.exit(1)

print("=" * 60)
print("  Garmin OAuth1 Exchange Diagnostic")
print("=" * 60)

# Check versions
print("\n--- Versions ---")
try:
    import garth
    print(f"  garth: {getattr(garth, '__version__', 'unknown')}")
except ImportError:
    print("  garth: NOT INSTALLED")

try:
    import garminconnect
    print(f"  garminconnect: {getattr(garminconnect, '__version__', 'unknown')}")
except ImportError:
    print("  garminconnect: NOT INSTALLED")

try:
    import oauthlib
    print(f"  oauthlib: {oauthlib.__version__}")
except Exception:
    print("  oauthlib: unknown")

try:
    import requests_oauthlib as ro
    print(f"  requests_oauthlib: {ro.__version__}")
except Exception:
    print("  requests_oauthlib: unknown")

print(f"  requests: {requests.__version__}")
print(f"  Python: {sys.version}")

# Step 1: Fetch OAuth consumer credentials
print("\n--- Step 1: OAuth Consumer Credentials ---")
try:
    resp = requests.get('https://thegarth.s3.amazonaws.com/oauth_consumer.json', timeout=10)
    consumer = resp.json()
    print(f"  Status: {resp.status_code}")
    print(f"  Consumer key: {consumer['consumer_key'][:16]}...")
    print(f"  Consumer secret: {consumer['consumer_secret'][:8]}...")
except Exception as e:
    print(f"  FALLO: {e}")
    sys.exit(1)

# Step 2: SSO Login to get ticket
print("\n--- Step 2: SSO Login ---")
SSO = "https://sso.garmin.com/sso"
SSO_EMBED = f"{SSO}/embed"

EMBED_PARAMS = {
    "id": "gauth-widget",
    "embedWidget": "true",
    "gauthHost": SSO,
}
SIGNIN_PARAMS = {
    "id": "gauth-widget",
    "embedWidget": "true",
    "gauthHost": SSO_EMBED,
    "service": SSO_EMBED,
    "source": SSO_EMBED,
    "redirectAfterAccountLoginUrl": SSO_EMBED,
    "redirectAfterAccountCreationUrl": SSO_EMBED,
}

import re

session = requests.Session()
session.headers.update({"User-Agent": "com.garmin.android.apps.connectmobile"})

# Get cookies
session.get(f"{SSO}/embed", params=EMBED_PARAMS)

# Get CSRF
resp = session.get(f"{SSO}/signin", params=SIGNIN_PARAMS)
m = re.search(r'name="_csrf"\s+value="(.+?)"', resp.text)
csrf = m.group(1) if m else None
print(f"  CSRF: {'found' if csrf else 'NOT FOUND'}")

if not csrf:
    print("  Cannot continue without CSRF token")
    sys.exit(1)

# POST credentials
from urllib.parse import urlencode
resp = session.post(
    f"{SSO}/signin",
    params=SIGNIN_PARAMS,
    data={
        "username": email,
        "password": password,
        "embed": "true",
        "_csrf": csrf,
    },
    headers={
        "Origin": "https://sso.garmin.com",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    allow_redirects=True,
)

html = resp.text
print(f"  SSO Status: {resp.status_code}")

# Find ticket
ticket = None
m = re.search(r'ticket=([^"&\s]+)', html)
if m:
    ticket = m.group(1)
    print(f"  Ticket: {ticket[:25]}...")
else:
    # Check redirects
    for r in resp.history:
        loc = r.headers.get("Location", "")
        m = re.search(r'ticket=([^"&\s]+)', loc)
        if m:
            ticket = m.group(1)
            print(f"  Ticket (from redirect): {ticket[:25]}...")
            break

if not ticket:
    print("  NO TICKET FOUND - login may have failed")
    # Check for errors
    if "incorrectCredentials" in html or "invalidCredentials" in html:
        print("  >> Credenciales incorrectas")
    elif "AccountLocked" in html:
        print("  >> Cuenta bloqueada")
    else:
        title_m = re.search(r'<title>(.+?)</title>', html)
        if title_m:
            print(f"  >> Page title: {title_m.group(1)}")
    sys.exit(1)

# Step 3: OAuth1 exchange - MANUAL (no garth)
print("\n--- Step 3: OAuth1 Exchange (manual, sin garth) ---")
oauth1_sess = OAuth1Session(consumer['consumer_key'], consumer['consumer_secret'])
url = (
    f"https://connectapi.garmin.com/oauth-service/oauth/"
    f"preauthorized?ticket={ticket}"
    f"&login-url=https://sso.garmin.com/sso/embed"
    f"&accepts-mfa-tokens=true"
)

# Show what we're sending
prepped = oauth1_sess.prepare_request(requests.Request('GET', url, headers={'User-Agent': 'com.garmin.android.apps.connectmobile'}))
print(f"  URL: {prepped.url}")
auth_header = prepped.headers.get('Authorization', 'NONE')
print(f"  Authorization: {auth_header[:80]}...")
print(f"  User-Agent: {prepped.headers.get('User-Agent', 'NONE')}")

resp = oauth1_sess.get(url, headers={'User-Agent': 'com.garmin.android.apps.connectmobile'}, timeout=15)
print(f"  Status: {resp.status_code}")
print(f"  Response headers: {dict(resp.headers)}")
print(f"  Response body: {resp.text[:500]}")

if resp.status_code == 200:
    parsed = parse_qs(resp.text)
    token = {k: v[0] for k, v in parsed.items()}
    print(f"\n  SUCCESS! OAuth1 token obtained")
    print(f"  oauth_token: {token.get('oauth_token', 'N/A')[:20]}...")

    # Step 4: Exchange for OAuth2
    print("\n--- Step 4: OAuth2 Exchange ---")
    oauth1_full = OAuth1Session(
        consumer['consumer_key'],
        consumer['consumer_secret'],
        resource_owner_key=token['oauth_token'],
        resource_owner_secret=token['oauth_token_secret'],
    )
    exchange_url = "https://connectapi.garmin.com/oauth-service/oauth/exchange/user/2.0"
    data = {}
    if 'mfa_token' in token and token['mfa_token']:
        data['mfa_token'] = token['mfa_token']

    resp2 = oauth1_full.post(
        exchange_url,
        headers={
            'User-Agent': 'com.garmin.android.apps.connectmobile',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data=data,
        timeout=15,
    )
    print(f"  Status: {resp2.status_code}")
    if resp2.status_code == 200:
        oauth2 = resp2.json()
        print(f"  SUCCESS! OAuth2 token obtained")
        print(f"  access_token: {oauth2.get('access_token', 'N/A')[:20]}...")
        print(f"  expires_in: {oauth2.get('expires_in', 'N/A')}")

        # Save tokens using garth
        print("\n--- Step 5: Saving tokens ---")
        try:
            import garth
            from garth.auth_tokens import OAuth1Token, OAuth2Token
            import time

            o1 = OAuth1Token(
                oauth_token=token['oauth_token'],
                oauth_token_secret=token['oauth_token_secret'],
                mfa_token=token.get('mfa_token'),
                domain='garmin.com',
            )
            oauth2['expires_at'] = int(time.time() + oauth2['expires_in'])
            oauth2['refresh_token_expires_at'] = int(time.time() + oauth2['refresh_token_expires_in'])
            o2 = OAuth2Token(**oauth2)

            garth.client.oauth1_token = o1
            garth.client.oauth2_token = o2
            tokendir = os.path.expanduser("~/.garmin_tokens")
            garth.save(tokendir)
            print(f"  Tokens guardados en {tokendir}")
            print("\n  >>> LISTO! Ahora corre: python3 garmin_sync.py")
        except Exception as e:
            print(f"  Error guardando tokens: {e}")
            print("  Pero el login funciono! El problema es guardar los tokens.")
    else:
        print(f"  Response: {resp2.text[:300]}")
else:
    print(f"\n  FALLO con {resp.status_code}")

    # Step 3b: Try with garth's method for comparison
    print("\n--- Step 3b: OAuth1 Exchange (via garth) ---")
    try:
        import garth
        from garth.sso import get_oauth1_token

        # Get a fresh ticket
        print("  Getting fresh ticket for garth test...")
        session2 = requests.Session()
        session2.headers.update({"User-Agent": "com.garmin.android.apps.connectmobile"})
        session2.get(f"{SSO}/embed", params=EMBED_PARAMS)
        resp2 = session2.get(f"{SSO}/signin", params=SIGNIN_PARAMS)
        m2 = re.search(r'name="_csrf"\s+value="(.+?)"', resp2.text)
        csrf2 = m2.group(1) if m2 else csrf
        resp2 = session2.post(
            f"{SSO}/signin",
            params=SIGNIN_PARAMS,
            data={"username": email, "password": password, "embed": "true", "_csrf": csrf2},
            headers={"Origin": "https://sso.garmin.com", "Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True,
        )
        m2 = re.search(r'ticket=([^"&\s]+)', resp2.text)
        ticket2 = m2.group(1) if m2 else None
        if ticket2:
            print(f"  Fresh ticket: {ticket2[:25]}...")
            oauth1 = get_oauth1_token(ticket2, garth.client)
            print(f"  garth exchange SUCCESS: {oauth1}")
        else:
            print("  Could not get fresh ticket")
    except Exception as e:
        print(f"  garth exchange also FAILED: {e}")

    print("\n--- Possible causes ---")
    print("  1. Garmin may have changed OAuth consumer credentials")
    print("  2. OAuth1 signing issue with your oauthlib version")
    print("  3. Garmin rate-limiting your IP/account")
    print("  4. Try: pip3 install --upgrade oauthlib requests-oauthlib")

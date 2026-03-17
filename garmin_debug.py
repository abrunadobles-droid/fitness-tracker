"""
Diagnostic script for Garmin OAuth1 exchange 401 issue.
Tests with BOTH requests-oauthlib AND pure manual OAuth1 signing.
Run: GARMIN_EMAIL='...' GARMIN_PASSWORD='...' python3 garmin_debug.py
"""
import os
import sys
import re
import json
import time
import hmac
import hashlib
import base64
import secrets
import requests
from urllib.parse import quote, urlencode, parse_qs, urlparse, parse_qsl

email = os.environ.get('GARMIN_EMAIL', '')
password = os.environ.get('GARMIN_PASSWORD', '')
if not email or not password:
    print("Set GARMIN_EMAIL and GARMIN_PASSWORD env vars")
    sys.exit(1)

print("=" * 60)
print("  Garmin OAuth1 Exchange Diagnostic v2")
print("=" * 60)

# Versions
print("\n--- Versions ---")
print(f"  Python: {sys.version}")
for mod_name in ('garth', 'garminconnect', 'oauthlib', 'requests_oauthlib', 'requests'):
    try:
        mod = __import__(mod_name)
        print(f"  {mod_name}: {getattr(mod, '__version__', 'unknown')}")
    except Exception:
        print(f"  {mod_name}: not installed")

import ssl
print(f"  SSL: {ssl.OPENSSL_VERSION}")


# --- Pure manual OAuth1 signing (no oauthlib) ---
def oauth1_sign(method, url, consumer_key, consumer_secret,
                token_key=None, token_secret=None, extra_params=None):
    """Generate OAuth1 HMAC-SHA1 Authorization header from scratch."""
    # Parse URL to separate base URL from query params
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Collect all params: query string + OAuth + extra
    params = dict(parse_qsl(parsed.query))
    if extra_params:
        params.update(extra_params)

    # OAuth params
    oauth_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': secrets.token_hex(16),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
    }
    if token_key:
        oauth_params['oauth_token'] = token_key

    all_params = {**params, **oauth_params}

    # Sort and encode params for base string
    sorted_params = '&'.join(
        f"{quote(k, safe='')}"
        f"={quote(v, safe='')}"
        for k, v in sorted(all_params.items())
    )

    # Base string
    base_string = (
        f"{method.upper()}&"
        f"{quote(base_url, safe='')}&"
        f"{quote(sorted_params, safe='')}"
    )

    # Signing key
    signing_key = f"{quote(consumer_secret, safe='')}&{quote(token_secret or '', safe='')}"

    # HMAC-SHA1 signature
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')

    oauth_params['oauth_signature'] = signature

    # Build Authorization header
    auth_header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return auth_header, base_string


# Step 1: Consumer credentials
print("\n--- Step 1: OAuth Consumer ---")
consumer = requests.get('https://thegarth.s3.amazonaws.com/oauth_consumer.json', timeout=10).json()
print(f"  Key: {consumer['consumer_key'][:16]}...")
print(f"  Secret: {consumer['consumer_secret'][:8]}...")

# Step 2: SSO Login
print("\n--- Step 2: SSO Login ---")
SSO = "https://sso.garmin.com/sso"
SSO_EMBED = f"{SSO}/embed"
EMBED_PARAMS = {"id": "gauth-widget", "embedWidget": "true", "gauthHost": SSO}
SIGNIN_PARAMS = {
    "id": "gauth-widget", "embedWidget": "true",
    "gauthHost": SSO_EMBED, "service": SSO_EMBED, "source": SSO_EMBED,
    "redirectAfterAccountLoginUrl": SSO_EMBED,
    "redirectAfterAccountCreationUrl": SSO_EMBED,
}

session = requests.Session()
session.headers.update({"User-Agent": "com.garmin.android.apps.connectmobile"})
session.get(f"{SSO}/embed", params=EMBED_PARAMS)
resp = session.get(f"{SSO}/signin", params=SIGNIN_PARAMS)
csrf = re.search(r'name="_csrf"\s+value="(.+?)"', resp.text)
csrf = csrf.group(1) if csrf else None
print(f"  CSRF: {'found' if csrf else 'NOT FOUND'}")
if not csrf:
    sys.exit(1)

resp = session.post(
    f"{SSO}/signin", params=SIGNIN_PARAMS,
    data={"username": email, "password": password, "embed": "true", "_csrf": csrf},
    headers={"Origin": "https://sso.garmin.com", "Content-Type": "application/x-www-form-urlencoded"},
    allow_redirects=True,
)
ticket = re.search(r'ticket=([^"&\s]+)', resp.text)
if not ticket:
    for r in resp.history:
        ticket = re.search(r'ticket=([^"&\s]+)', r.headers.get("Location", "") + (r.text or ""))
        if ticket:
            break
ticket = ticket.group(1) if ticket else None
print(f"  Ticket: {ticket[:25]}..." if ticket else "  NO TICKET")
if not ticket:
    sys.exit(1)

# Step 3A: OAuth1 via requests-oauthlib
print("\n--- Step 3A: OAuth1 via requests-oauthlib ---")
try:
    from requests_oauthlib import OAuth1Session
    oauth1_sess = OAuth1Session(consumer['consumer_key'], consumer['consumer_secret'])
    url = (
        f"https://connectapi.garmin.com/oauth-service/oauth/"
        f"preauthorized?ticket={ticket}"
        f"&login-url=https://sso.garmin.com/sso/embed"
        f"&accepts-mfa-tokens=true"
    )
    prepped = oauth1_sess.prepare_request(
        requests.Request('GET', url, headers={'User-Agent': 'com.garmin.android.apps.connectmobile'})
    )
    print(f"  Full Auth Header: {prepped.headers.get('Authorization')}")
    resp = oauth1_sess.get(url, headers={'User-Agent': 'com.garmin.android.apps.connectmobile'}, timeout=15)
    print(f"  Status: {resp.status_code}")
    print(f"  Body: {resp.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")

# Get a fresh ticket for the manual test
print("\n  Getting fresh ticket for manual test...")
session2 = requests.Session()
session2.headers.update({"User-Agent": "com.garmin.android.apps.connectmobile"})
session2.get(f"{SSO}/embed", params=EMBED_PARAMS)
resp2 = session2.get(f"{SSO}/signin", params=SIGNIN_PARAMS)
csrf2 = re.search(r'name="_csrf"\s+value="(.+?)"', resp2.text)
csrf2 = csrf2.group(1) if csrf2 else csrf
resp2 = session2.post(
    f"{SSO}/signin", params=SIGNIN_PARAMS,
    data={"username": email, "password": password, "embed": "true", "_csrf": csrf2},
    headers={"Origin": "https://sso.garmin.com", "Content-Type": "application/x-www-form-urlencoded"},
    allow_redirects=True,
)
ticket2 = re.search(r'ticket=([^"&\s]+)', resp2.text)
ticket2 = ticket2.group(1) if ticket2 else None
print(f"  Fresh ticket: {ticket2[:25]}..." if ticket2 else "  NO TICKET")

# Step 3B: OAuth1 MANUAL (pure Python, no oauthlib)
print("\n--- Step 3B: OAuth1 MANUAL (pure hmac, no oauthlib) ---")
if ticket2:
    url2 = (
        f"https://connectapi.garmin.com/oauth-service/oauth/"
        f"preauthorized?ticket={ticket2}"
        f"&login-url=https://sso.garmin.com/sso/embed"
        f"&accepts-mfa-tokens=true"
    )
    auth_header, base_string = oauth1_sign(
        'GET', url2,
        consumer['consumer_key'], consumer['consumer_secret']
    )
    print(f"  Base string (first 200): {base_string[:200]}...")
    print(f"  Auth header: {auth_header}")

    resp3 = requests.get(
        url2,
        headers={
            'User-Agent': 'com.garmin.android.apps.connectmobile',
            'Authorization': auth_header,
        },
        timeout=15,
    )
    print(f"  Status: {resp3.status_code}")
    print(f"  Body: {resp3.text[:300]}")

    if resp3.status_code == 200:
        parsed = parse_qs(resp3.text)
        oauth1_token = {k: v[0] for k, v in parsed.items()}
        print(f"\n  >>> SUCCESS! OAuth1 token: {oauth1_token.get('oauth_token', 'N/A')[:20]}...")

        # Step 4: OAuth2 exchange
        print("\n--- Step 4: OAuth2 Exchange ---")
        exchange_url = "https://connectapi.garmin.com/oauth-service/oauth/exchange/user/2.0"
        data = {}
        if oauth1_token.get('mfa_token'):
            data['mfa_token'] = oauth1_token['mfa_token']

        auth4, _ = oauth1_sign(
            'POST', exchange_url,
            consumer['consumer_key'], consumer['consumer_secret'],
            token_key=oauth1_token['oauth_token'],
            token_secret=oauth1_token['oauth_token_secret'],
            extra_params=data,
        )
        resp4 = requests.post(
            exchange_url,
            headers={
                'User-Agent': 'com.garmin.android.apps.connectmobile',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': auth4,
            },
            data=data,
            timeout=15,
        )
        print(f"  Status: {resp4.status_code}")
        if resp4.status_code == 200:
            oauth2 = resp4.json()
            print(f"  >>> SUCCESS! OAuth2 access_token: {oauth2.get('access_token', 'N/A')[:20]}...")

            # Save tokens
            print("\n--- Step 5: Saving tokens ---")
            try:
                import garth
                from garth.auth_tokens import OAuth1Token, OAuth2Token

                o1 = OAuth1Token(
                    oauth_token=oauth1_token['oauth_token'],
                    oauth_token_secret=oauth1_token['oauth_token_secret'],
                    mfa_token=oauth1_token.get('mfa_token'),
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
                print("\n  ============================")
                print("  >>> LISTO! Ahora corre:")
                print("  >>> python3 garmin_sync.py")
                print("  ============================")
            except Exception as e:
                print(f"  Error guardando: {e}")
                # Save raw tokens as JSON fallback
                raw_tokens = {
                    'oauth1': oauth1_token,
                    'oauth2': oauth2,
                }
                tokendir = os.path.expanduser("~/.garmin_tokens")
                os.makedirs(tokendir, exist_ok=True)
                with open(os.path.join(tokendir, 'raw_tokens.json'), 'w') as f:
                    json.dump(raw_tokens, f, indent=2)
                print(f"  Raw tokens guardados en {tokendir}/raw_tokens.json")
        else:
            print(f"  Body: {resp4.text[:300]}")
    else:
        print(f"\n  MANUAL OAuth1 also FAILED with {resp3.status_code}")
        print("\n--- Conclusion ---")
        print("  Both oauthlib AND manual OAuth1 fail with 401.")
        print("  This means the issue is NOT with the Python libraries.")
        print("  Possible causes:")
        print("  1. Garmin changed their OAuth consumer credentials (S3 bucket stale)")
        print("  2. Your account/IP is blocked for OAuth1 exchanges")
        print("  3. Garmin requires a new auth flow (OAuth2 PKCE instead of OAuth1)")
        print()
        print("  Try from a different network (e.g., phone hotspot) to rule out IP blocking.")
else:
    print("  Skipped (no fresh ticket)")

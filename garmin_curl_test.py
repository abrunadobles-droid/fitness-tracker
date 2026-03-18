"""
Test OAuth1 exchange via curl (bypasses Python's TLS stack).
If curl works but Python doesn't, it's a TLS fingerprinting issue.
Run: GARMIN_EMAIL='...' GARMIN_PASSWORD='...' python3 garmin_curl_test.py
"""
import os
import sys
import re
import time
import hmac
import hashlib
import base64
import secrets
import subprocess
import requests
from urllib.parse import quote, urlparse, parse_qsl

email = os.environ.get('GARMIN_EMAIL', '')
password = os.environ.get('GARMIN_PASSWORD', '')
if not email or not password:
    print("Set GARMIN_EMAIL and GARMIN_PASSWORD env vars")
    sys.exit(1)

print("=" * 60)
print("  Garmin OAuth1 - curl vs Python TLS test")
print("=" * 60)

# Check curl's TLS
print("\n--- curl TLS info ---")
result = subprocess.run(['curl', '--version'], capture_output=True, text=True)
for line in result.stdout.split('\n')[:2]:
    print(f"  {line}")


def oauth1_header(method, url, consumer_key, consumer_secret):
    """Generate OAuth1 HMAC-SHA1 Authorization header."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    params = dict(parse_qsl(parsed.query))

    oauth_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': secrets.token_hex(16),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
    }
    all_params = {**params, **oauth_params}

    sorted_params = '&'.join(
        f"{quote(k, safe='')}"
        f"={quote(v, safe='')}"
        for k, v in sorted(all_params.items())
    )
    base_string = (
        f"{method.upper()}&"
        f"{quote(base_url, safe='')}&"
        f"{quote(sorted_params, safe='')}"
    )
    signing_key = f"{quote(consumer_secret, safe='')}&"
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')

    oauth_params['oauth_signature'] = signature
    auth_header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return auth_header


# Step 1: Get consumer credentials
print("\n--- Step 1: Consumer credentials ---")
consumer = requests.get('https://thegarth.s3.amazonaws.com/oauth_consumer.json', timeout=10).json()
print(f"  Key: {consumer['consumer_key'][:16]}...")

# Step 2: SSO Login (Python - this works fine)
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

resp = session.post(
    f"{SSO}/signin", params=SIGNIN_PARAMS,
    data={"username": email, "password": password, "embed": "true", "_csrf": csrf},
    headers={"Origin": "https://sso.garmin.com", "Content-Type": "application/x-www-form-urlencoded"},
    allow_redirects=True,
)
ticket = re.search(r'ticket=([^"&\s]+)', resp.text)
ticket = ticket.group(1) if ticket else None
print(f"  Ticket: {ticket[:25]}..." if ticket else "  NO TICKET")
if not ticket:
    sys.exit(1)

# Step 3: Try OAuth1 exchange with CURL
print("\n--- Step 3: OAuth1 via CURL ---")
url = (
    f"https://connectapi.garmin.com/oauth-service/oauth/"
    f"preauthorized?ticket={ticket}"
    f"&login-url=https://sso.garmin.com/sso/embed"
    f"&accepts-mfa-tokens=true"
)
auth_header = oauth1_header('GET', url, consumer['consumer_key'], consumer['consumer_secret'])

curl_cmd = [
    'curl', '-s', '-w', '\n%{http_code}',
    '-H', f'Authorization: {auth_header}',
    '-H', 'User-Agent: com.garmin.android.apps.connectmobile',
    url,
]

print(f"  Running curl...")
result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
output = result.stdout.strip()
lines = output.rsplit('\n', 1)
body = lines[0] if len(lines) > 1 else ''
status = lines[-1] if lines else '???'

print(f"  curl status: {status}")
print(f"  curl body: {body[:200]}")

if status == '200':
    print(f"\n  >>> CURL WORKS! The issue is Python's TLS (LibreSSL 2.8.3)")
    print(f"  >>> Solution: Install Python 3.12 via Homebrew")
    print(f"  >>>   brew install python@3.12")
    print(f"  >>>   python3.12 -m pip install garth garminconnect")

    # Parse the OAuth1 token from curl response
    from urllib.parse import parse_qs
    parsed = parse_qs(body)
    oauth1_token = {k: v[0] for k, v in parsed.items()}
    print(f"\n  OAuth1 token: {oauth1_token.get('oauth_token', 'N/A')[:20]}...")

    # Step 4: OAuth2 exchange via curl too
    print("\n--- Step 4: OAuth2 exchange via curl ---")
    exchange_url = "https://connectapi.garmin.com/oauth-service/oauth/exchange/user/2.0"
    # For OAuth2 exchange, need OAuth1 with resource owner key/secret
    parsed_url = urlparse(exchange_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    mfa_data = {}
    if oauth1_token.get('mfa_token'):
        mfa_data['mfa_token'] = oauth1_token['mfa_token']

    # Build OAuth1 with token
    oauth_params = {
        'oauth_consumer_key': consumer['consumer_key'],
        'oauth_nonce': secrets.token_hex(16),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': oauth1_token['oauth_token'],
        'oauth_version': '1.0',
    }
    all_params = {**mfa_data, **oauth_params}
    sorted_params = '&'.join(
        f"{quote(k, safe='')}"
        f"={quote(v, safe='')}"
        for k, v in sorted(all_params.items())
    )
    base_string = (
        f"POST&{quote(base_url, safe='')}&{quote(sorted_params, safe='')}"
    )
    signing_key = (
        f"{quote(consumer['consumer_secret'], safe='')}&"
        f"{quote(oauth1_token['oauth_token_secret'], safe='')}"
    )
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    oauth_params['oauth_signature'] = signature

    auth2 = 'OAuth ' + ', '.join(
        f'{quote(k, safe="")}="{quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )

    curl_data = '&'.join(f'{k}={v}' for k, v in mfa_data.items()) if mfa_data else ''
    curl_cmd2 = [
        'curl', '-s', '-w', '\n%{http_code}',
        '-X', 'POST',
        '-H', f'Authorization: {auth2}',
        '-H', 'User-Agent: com.garmin.android.apps.connectmobile',
        '-H', 'Content-Type: application/x-www-form-urlencoded',
    ]
    if curl_data:
        curl_cmd2.extend(['-d', curl_data])
    else:
        curl_cmd2.extend(['-d', ''])
    curl_cmd2.append(exchange_url)

    result2 = subprocess.run(curl_cmd2, capture_output=True, text=True, timeout=30)
    output2 = result2.stdout.strip()
    lines2 = output2.rsplit('\n', 1)
    body2 = lines2[0] if len(lines2) > 1 else ''
    status2 = lines2[-1] if lines2 else '???'

    print(f"  curl status: {status2}")
    if status2 == '200':
        import json
        oauth2 = json.loads(body2)
        print(f"  >>> SUCCESS! OAuth2 access_token: {oauth2.get('access_token', 'N/A')[:20]}...")

        # Save tokens using garth
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
            oauth2['refresh_token_expires_at'] = int(
                time.time() + oauth2['refresh_token_expires_in']
            )
            o2 = OAuth2Token(**oauth2)

            garth.client.oauth1_token = o1
            garth.client.oauth2_token = o2
            tokendir = os.path.expanduser("~/.garmin_tokens")
            garth.save(tokendir)
            print(f"  Tokens guardados en {tokendir}")
            print("\n  ====================================")
            print("  >>> LISTO! Ahora corre:")
            print("  >>> python3 garmin_sync.py")
            print("  ====================================")
        except Exception as e:
            print(f"  Error guardando tokens: {e}")
            # Save as raw JSON
            import json
            tokendir = os.path.expanduser("~/.garmin_tokens")
            os.makedirs(tokendir, exist_ok=True)
            with open(os.path.join(tokendir, 'oauth1_token.json'), 'w') as f:
                json.dump({
                    'oauth_token': oauth1_token['oauth_token'],
                    'oauth_token_secret': oauth1_token['oauth_token_secret'],
                    'mfa_token': oauth1_token.get('mfa_token'),
                    'domain': 'garmin.com',
                }, f, indent=2)
            with open(os.path.join(tokendir, 'oauth2_token.json'), 'w') as f:
                oauth2['expires_at'] = int(time.time() + oauth2['expires_in'])
                oauth2['refresh_token_expires_at'] = int(
                    time.time() + oauth2['refresh_token_expires_in']
                )
                json.dump(oauth2, f, indent=2)
            print(f"  Raw tokens guardados en {tokendir}/")
            print("\n  ====================================")
            print("  >>> LISTO! Ahora corre:")
            print("  >>> python3 garmin_sync.py")
            print("  ====================================")
    else:
        print(f"  Body: {body2[:300]}")

elif status == '401':
    # Step 3b: Also try Python for comparison
    print(f"\n  curl also got 401. Trying Python for comparison...")

    auth_py = oauth1_header('GET', url, consumer['consumer_key'], consumer['consumer_secret'])
    resp_py = requests.get(
        url,
        headers={
            'User-Agent': 'com.garmin.android.apps.connectmobile',
            'Authorization': auth_py,
        },
        timeout=15,
    )
    print(f"  Python status: {resp_py.status_code}")

    if resp_py.status_code == 401:
        print(f"\n  Both curl AND Python fail with 401.")
        print(f"  The issue is NOT TLS fingerprinting.")
        print(f"  Possible causes:")
        print(f"  1. Your IP/network is blocked by Garmin")
        print(f"  2. Garmin consumer credentials are stale for your region")
        print(f"  3. Try from phone hotspot to test different network")
    else:
        print(f"\n  Interesting: curl={status} but Python={resp_py.status_code}")

else:
    print(f"\n  Unexpected status: {status}")
    print(f"  stderr: {result.stderr[:200]}")

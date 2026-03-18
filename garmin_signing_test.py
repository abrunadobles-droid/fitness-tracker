"""
Deterministic OAuth1 signing comparison test.
Generates OAuth1 signature with FIXED parameters to compare across Python versions.
Run on BOTH machines and compare output.

Run: python3 garmin_signing_test.py
"""
import hmac
import hashlib
import base64
import sys
from urllib.parse import quote, urlparse, parse_qsl

print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")
import ssl
print(f"SSL: {ssl.OPENSSL_VERSION}")
print()

# Fixed test parameters
CONSUMER_KEY = "fc3e99d2-118c-44b8-8ae3-03370dde24c0"
CONSUMER_SECRET = "E08WAR897WEy2knn7aFBrvegVAf0AFdWBBF"
NONCE = "test_nonce_12345"
TIMESTAMP = "1773786095"
TICKET = "ST-0361106-VilKqHyRMwCtest"

URL = (
    f"https://connectapi.garmin.com/oauth-service/oauth/"
    f"preauthorized?ticket={TICKET}"
    f"&login-url=https://sso.garmin.com/sso/embed"
    f"&accepts-mfa-tokens=true"
)

# Parse URL
parsed = urlparse(URL)
base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
query_params = dict(parse_qsl(parsed.query))

print("=== URL Parsing ===")
print(f"base_url: {base_url}")
print(f"query_params: {query_params}")
print()

# OAuth params
oauth_params = {
    'oauth_consumer_key': CONSUMER_KEY,
    'oauth_nonce': NONCE,
    'oauth_signature_method': 'HMAC-SHA1',
    'oauth_timestamp': TIMESTAMP,
    'oauth_version': '1.0',
}

all_params = {**query_params, **oauth_params}

print("=== All Params (sorted) ===")
for k in sorted(all_params.keys()):
    v = all_params[k]
    print(f"  {k} = {v}")
    print(f"    encoded: {quote(k, safe='')}={quote(v, safe='')}")
print()

# Build sorted params string
sorted_params = '&'.join(
    f"{quote(k, safe='')}"
    f"={quote(v, safe='')}"
    for k, v in sorted(all_params.items())
)
print(f"=== Sorted Params String ===")
print(f"  {sorted_params}")
print()

# Build base string
base_string = (
    f"GET&"
    f"{quote(base_url, safe='')}&"
    f"{quote(sorted_params, safe='')}"
)
print(f"=== Base String ===")
print(f"  {base_string}")
print()

# Check individual encodings
print(f"=== Key Encodings ===")
test_strings = [
    "https://sso.garmin.com/sso/embed",
    "https://connectapi.garmin.com/oauth-service/oauth/preauthorized",
    CONSUMER_KEY,
    CONSUMER_SECRET,
]
for s in test_strings:
    print(f"  quote({s!r}, safe='') = {quote(s, safe='')}")
print()

# Signing key
signing_key = f"{quote(CONSUMER_SECRET, safe='')}&"
print(f"=== Signing Key ===")
print(f"  {signing_key}")
print()

# HMAC-SHA1
raw_sig = hmac.new(
    signing_key.encode('utf-8'),
    base_string.encode('utf-8'),
    hashlib.sha1
).digest()
signature = base64.b64encode(raw_sig).decode('utf-8')

print(f"=== Signature ===")
print(f"  raw bytes: {raw_sig.hex()}")
print(f"  base64: {signature}")
print(f"  url-encoded: {quote(signature, safe='')}")
print()

# Now test with oauthlib/requests_oauthlib for comparison
print("=== oauthlib comparison ===")
try:
    from oauthlib.oauth1 import Client as OAuthClient
    oc = OAuthClient(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        nonce=NONCE,
        timestamp=TIMESTAMP,
    )
    # oauthlib sign method
    uri, headers, body = oc.sign(URL, http_method='GET')
    print(f"  oauthlib signed URI: {uri}")
    print(f"  oauthlib headers: {headers}")

    # Extract signature from header
    import re
    sig_match = re.search(r'oauth_signature="([^"]+)"', headers.get('Authorization', ''))
    if sig_match:
        oauthlib_sig = sig_match.group(1)
        print(f"  oauthlib signature (raw): {oauthlib_sig}")
        from urllib.parse import unquote
        print(f"  oauthlib signature (decoded): {unquote(oauthlib_sig)}")
        print(f"  manual signature: {signature}")
        if unquote(oauthlib_sig) == signature:
            print("  >>> MATCH! Manual and oauthlib produce same signature")
        else:
            print("  >>> MISMATCH! Signatures differ - check base strings")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== requests URL normalization ===")
try:
    import requests
    req = requests.Request('GET', URL)
    prepped = req.prepare()
    print(f"  Original URL: {URL}")
    print(f"  Prepared URL: {prepped.url}")
    if URL != prepped.url:
        print("  >>> URL WAS MODIFIED by requests! This could cause signature mismatch!")
        parsed_orig = urlparse(URL)
        parsed_prep = urlparse(prepped.url)
        if parsed_orig.query != parsed_prep.query:
            print(f"  Original query: {parsed_orig.query}")
            print(f"  Prepared query: {parsed_prep.query}")
    else:
        print("  >>> URL unchanged")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== requests_oauthlib full flow (what actually gets sent) ===")
try:
    from requests_oauthlib import OAuth1Session
    import re
    from urllib.parse import unquote

    # Create session with FIXED nonce/timestamp to compare
    from oauthlib.oauth1 import Client as OAuthClient
    from requests_oauthlib import OAuth1
    auth = OAuth1(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        nonce=NONCE,
        timestamp=TIMESTAMP,
    )
    req = requests.Request('GET', URL, auth=auth,
                           headers={'User-Agent': 'com.garmin.android.apps.connectmobile'})
    prepped = req.prepare()
    print(f"  Final URL sent: {prepped.url}")
    print(f"  Final Auth header: {prepped.headers.get('Authorization')}")
    auth_h = prepped.headers.get('Authorization', '')
    if isinstance(auth_h, bytes):
        auth_h = auth_h.decode('utf-8')
    sig_m = re.search(r'oauth_signature="([^"]+)"', auth_h)
    if sig_m:
        final_sig = unquote(sig_m.group(1))
        print(f"  Final signature: {final_sig}")
        print(f"  Expected sig:    {signature}")
        if final_sig == signature:
            print("  >>> MATCH! requests_oauthlib flow produces correct signature")
        else:
            print("  >>> MISMATCH! The full requests_oauthlib flow produces WRONG signature!")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== urllib3 version ===")
try:
    import urllib3
    print(f"  urllib3: {urllib3.__version__}")
except Exception:
    print("  urllib3: unknown")

"""
Garmin SSO Authentication - Two-phase flow with MFA support.

Phase 1: Email/password login via SSO → returns ticket or MFA session
Phase 2: MFA code submission (if needed) → returns ticket
Phase 3: OAuth token exchange via garth → returns authenticated client

Based on Garmin Connect SSO flow documentation.
"""
import re
import requests
from urllib.parse import urlencode
from garminconnect import Garmin
from garth.sso import get_oauth1_token, exchange


# ---- Constants ----
SSO = "https://sso.garmin.com/sso"
SSO_EMBED = f"{SSO}/embed"

EMBED_PARAMS = {
    "clientId": "GarminConnect",
    "locale": "en",
    "service": "https://connect.garmin.com/modern",
}

SIGNIN_PARAMS = {
    "id": "gauth-widget",
    "embedWidget": "true",
    "clientId": "GarminConnect",
    "locale": "en",
    "gauthHost": SSO_EMBED,
    "service": SSO_EMBED,
    "source": SSO_EMBED,
    "redirectAfterAccountLoginUrl": SSO_EMBED,
    "redirectAfterAccountCreationUrl": SSO_EMBED,
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# ---- Helpers ----

def _get_csrf(html):
    """Extract CSRF token from HTML."""
    m = re.search(r'name="_csrf"\s+value="(.+?)"', html)
    return m.group(1) if m else None


def _find_ticket(text):
    """Find SSO ticket in HTML or URL string."""
    m = re.search(r'ticket=([^"&\s]+)', text)
    return m.group(1) if m else None


# ---- Phase 1: Login ----

def garmin_login(email, password):
    """
    Phase 1: SSO login with email/password.

    Returns dict with either:
    - {"ticket": "ST-xxx"} → login succeeded, no MFA
    - {"mfa_required": True, "session": {...}} → MFA needed

    Raises Exception for invalid credentials, locked account, etc.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # Step 1: GET embed page (establish cookies)
    session.get(f"{SSO}/embed", params=EMBED_PARAMS)

    # Step 2: GET signin page (get CSRF token)
    resp = session.get(f"{SSO}/signin", params=SIGNIN_PARAMS)
    csrf = _get_csrf(resp.text)
    if not csrf:
        raise Exception("No se pudo conectar con Garmin (CSRF)")

    # Step 3: POST credentials
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
            "Referer": f"{SSO}/signin?" + urlencode(SIGNIN_PARAMS),
        },
        allow_redirects=True,
    )

    html = resp.text

    # Step 4: Check response
    if "AccountLocked" in html or "account has been locked" in html.lower():
        raise Exception("Tu cuenta de Garmin esta bloqueada. Contacta soporte de Garmin.")

    if "incorrectCredentials" in html or "Invalid credentials" in html or "invalidCredentials" in html:
        raise Exception("Email o password de Garmin incorrecto.")

    # Check for ticket in response body
    ticket = _find_ticket(html)
    if ticket:
        return {"ticket": ticket}

    # Check in redirect chain
    for r in resp.history:
        loc = r.headers.get("Location", "")
        ticket = _find_ticket(loc)
        if ticket:
            return {"ticket": ticket}
        ticket = _find_ticket(r.text or "")
        if ticket:
            return {"ticket": ticket}

    # No ticket → MFA required
    new_csrf = _get_csrf(html) or csrf

    # Try to find MFA form action
    form_action = None
    fa_match = re.search(r'action="([^"]*(?:verifyMFA|mfa)[^"]*)"', html, re.IGNORECASE)
    if fa_match:
        form_action = fa_match.group(1)

    return {
        "mfa_required": True,
        "session": {
            "cookies": dict(session.cookies),
            "csrf": new_csrf,
            "form_action": form_action,
        },
    }


# ---- Phase 2: MFA Verification ----

def garmin_verify_mfa(mfa_session, mfa_code):
    """
    Phase 2: Submit MFA code using saved session.

    Args:
        mfa_session: dict from Phase 1 with cookies, csrf, form_action
        mfa_code: 6-digit code from authenticator app

    Returns:
        SSO ticket string

    Raises Exception if code is invalid.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # Restore cookies from Phase 1
    for name, value in mfa_session["cookies"].items():
        session.cookies.set(name, value)

    # Determine verify URL
    form_action = mfa_session.get("form_action")
    if form_action:
        if form_action.startswith("/"):
            verify_url = f"https://sso.garmin.com{form_action}"
        else:
            verify_url = form_action
    else:
        verify_url = f"{SSO}/verifyMFA/loginEnterMfaCode"

    # Submit MFA code (send both field names to cover Garmin variants)
    resp = session.post(
        verify_url,
        params=SIGNIN_PARAMS,
        data={
            "verificationCode": mfa_code,
            "mfa-code": mfa_code,
            "embed": "true",
            "_csrf": mfa_session["csrf"],
            "fromPage": "setupEnterMfaCode",
        },
        headers={
            "Origin": "https://sso.garmin.com",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        allow_redirects=False,
    )

    # Follow redirects looking for ticket (up to 10)
    for _ in range(10):
        # Check response body
        html = resp.text or ""
        ticket = _find_ticket(html)
        if ticket:
            return ticket

        # Check Location header
        location = resp.headers.get("Location", "")
        ticket = _find_ticket(location)
        if ticket:
            return ticket

        # Follow redirect
        if location and resp.status_code in (301, 302, 303, 307):
            if location.startswith("/"):
                location = f"https://sso.garmin.com{location}"
            resp = session.get(location, allow_redirects=False)
        else:
            break

    raise Exception("Codigo MFA invalido o expirado. Intenta de nuevo.")


# ---- Phase 3: OAuth Exchange ----

def garmin_connect_with_ticket(email, password, ticket):
    """
    Phase 3: Exchange SSO ticket for OAuth tokens and create
    an authenticated garminconnect client.

    Uses garth's get_oauth1_token + exchange for the OAuth flow.
    """
    client = Garmin(email, password)

    # Exchange ticket → OAuth1 → OAuth2 via garth
    oauth1 = get_oauth1_token(ticket, client.garth)
    oauth2 = exchange(oauth1, client.garth)

    # Set tokens on the garth client
    client.garth.oauth1_token = oauth1
    client.garth.oauth2_token = oauth2

    # Get profile info
    client.display_name = client.garth.profile["displayName"]
    client.full_name = client.garth.profile["fullName"]

    return client

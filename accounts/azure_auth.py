"""
accounts app — Azure AD (Entra ID) OAuth2 authentication.

Implements the server-side authorization-code flow via MSAL. The client
secret stays on the server; tokens never reach the browser.

Flow:
    1. build_auth_url()  → redirect the user to Microsoft
    2. Microsoft redirects back to the callback with a `code`
    3. acquire_user_claims(code)  → exchange code for the user's identity
"""

from typing import Any

import msal
from django.conf import settings

_SCOPES = ["User.Read"]


def _build_msal_app() -> msal.ConfidentialClientApplication:
    """Construct the MSAL confidential client from settings."""
    tenant_id = settings.AZURE_AD["TENANT_ID"]
    return msal.ConfidentialClientApplication(
        client_id=settings.AZURE_AD["CLIENT_ID"],
        client_credential=settings.AZURE_AD["CLIENT_SECRET"],
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )


def build_auth_url(state: str) -> str:
    """
    Return the Microsoft sign-in URL to redirect the user to.

    Args:
        state: A random anti-CSRF token stored in the session.

    Returns:
        The full authorization-request URL.
    """
    app = _build_msal_app()
    return app.get_authorization_request_url(
        scopes=_SCOPES,
        state=state,
        redirect_uri=settings.AZURE_AD["REDIRECT_URI"],
    )


def acquire_user_claims(code: str) -> dict[str, Any] | None:
    """
    Exchange the authorization code for the signed-in user's claims.

    Args:
        code: The authorization code returned by Microsoft.

    Returns:
        A dict of ID-token claims (oid, email, name, ...), or None on failure.
    """
    app = _build_msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=_SCOPES,
        redirect_uri=settings.AZURE_AD["REDIRECT_URI"],
    )
    if "id_token_claims" not in result:
        return None
    return result["id_token_claims"]




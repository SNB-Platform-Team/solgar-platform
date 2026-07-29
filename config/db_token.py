"""
Azure MySQL — Entra ID token injection.

Azure MySQL runs in Entra-ID-only auth mode: there is no static password.
Each connection authenticates with a short-lived (60 min) access token obtained
through the App Service's Managed Identity.

The token must be present *before* the connection is opened, so we wrap the
database wrapper's get_new_connection to inject a fresh token into the
connection params each time a new connection is created. azure-identity caches
and renews the token internally.

Active only when USE_AZURE_MYSQL=True (imported from settings under that guard).
"""

from typing import Any

from django.db.backends.mysql.base import DatabaseWrapper

_TOKEN_RESOURCE = "https://ossrdbms-aad.database.windows.net/.default"
_credential = None


def _get_token() -> str:
    """Return a fresh Entra ID access token via Managed Identity."""
    global _credential
    if _credential is None:
        from azure.identity import DefaultAzureCredential

        _credential = DefaultAzureCredential()
    return _credential.get_token(_TOKEN_RESOURCE).token


# Keep a reference to the original method.
_original_get_new_connection = DatabaseWrapper.get_new_connection


def _patched_get_new_connection(self, conn_params: dict[str, Any]):
    """Inject a fresh token as the password before opening the connection."""
    conn_params["passwd"] = _get_token()
    return _original_get_new_connection(self, conn_params)


# Apply the patch once at import time.
DatabaseWrapper.get_new_connection = _patched_get_new_connection
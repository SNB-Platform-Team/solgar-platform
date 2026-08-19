"""
Azure MySQL — Entra ID token injection + TLS.

Azure MySQL runs in Entra-ID-only auth mode (no static password) and requires
TLS. Each connection authenticates with a short-lived token from the App
Service's Managed Identity, and must use a secure transport.

We wrap the MySQL backend's get_new_connection to inject a fresh token as the
password and enable SSL, before the connection is opened.

IMPORTANT: the token/SSL injection applies ONLY to the 'default' connection
(Azure MySQL). The 'refdb' connection (external MySQL on Olga's server) uses a
normal username/password and must be left untouched — otherwise its real
password would be overwritten with an Azure token it does not understand,
causing "Access denied".

Active only when USE_AZURE_MYSQL=True.
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


_original_get_new_connection = DatabaseWrapper.get_new_connection


def _patched_get_new_connection(self, conn_params: dict[str, Any]):
    """
    Inject a fresh token and enable TLS before opening the connection, but
    ONLY for the Azure MySQL ('default') connection. Any other connection
    (e.g. 'refdb') is opened as-is with its configured password.
    """
    if getattr(self, "alias", None) == "default":
        conn_params["passwd"] = _get_token()
        # Azure MySQL requires a secure transport. Enable SSL without a CA file
        # (server certificate is trusted via the platform CA bundle).
        conn_params["ssl_mode"] = "REQUIRED"
        conn_params["ssl"] = {"ca": None}
    return _original_get_new_connection(self, conn_params)


DatabaseWrapper.get_new_connection = _patched_get_new_connection

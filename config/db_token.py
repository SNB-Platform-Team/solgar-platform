"""
Azure MySQL — Entra ID token injection.

Azure MySQL runs in Entra-ID-only auth mode: there is no static password.
Each connection uses a short-lived (60 min) access token obtained through the
App Service's Managed Identity.

Django reads settings once at startup, so a token placed in DATABASES would go
stale. This module hooks the `connection_created` signal and sets a fresh token
as the connection password each time, letting azure-identity cache and renew it.

Active only when USE_AZURE_MYSQL=True (imported from settings under that guard).
"""

from typing import Any

from django.conf import settings
from django.db.backends.signals import connection_created
from django.dispatch import receiver

_TOKEN_RESOURCE = "https://ossrdbms-aad.database.windows.net/.default"


def _get_credential():
    """Return a cached Managed Identity credential."""
    from azure.identity import DefaultAzureCredential

    if not hasattr(_get_credential, "_cred"):
        _get_credential._cred = DefaultAzureCredential()
    return _get_credential._cred


@receiver(connection_created)
def inject_token(sender: Any, connection: Any, **kwargs: Any) -> None:
    """Refresh the Entra ID token used as the DB password on each connection."""
    if not getattr(settings, "USE_AZURE_MYSQL", False):
        return
    if connection.vendor != "mysql":
        return

    token = _get_credential().get_token(_TOKEN_RESOURCE)
    connection.settings_dict["PASSWORD"] = token.token
"""
accounts app — authentication signal handlers.

Records login and logout events into LoginLog automatically.
"""

from typing import Any

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest

from .models import LoginLog


def _client_ip(request: HttpRequest) -> str | None:
    """Extract the client IP, honoring a proxy header if present."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def log_login(sender: Any, request: HttpRequest, user: Any, **kwargs: Any) -> None:
    """Write a LOGIN record when a user signs in."""
    LoginLog.objects.create(
        user=user,
        event_type=LoginLog.EventType.LOGIN,
        ip_address=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )


@receiver(user_logged_out)
def log_logout(sender: Any, request: HttpRequest, user: Any, **kwargs: Any) -> None:
    """Write a LOGOUT record when a user signs out."""
    if user is None:
        return
    LoginLog.objects.create(
        user=user,
        event_type=LoginLog.EventType.LOGOUT,
        ip_address=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )
"""
accounts app — authentication signal handlers.

Records login and logout events into LoginLog automatically.
"""

from typing import Any

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.http import HttpRequest

from .models import LoginLog, User


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


@receiver(user_login_failed)
def log_login_failed(
    sender: Any, credentials: dict | None = None,
    request: HttpRequest | None = None, **kwargs: Any,
) -> None:
    """Write a FAILED record on a failed authentication attempt.

    Django bu sinyali authenticate() basarisiz oldugunda gonderir. credentials
    girilen kullanici adini icerir (sifre Django tarafindan zaten maskelenir).
    Denenen kullanici adi mevcut bir kullaniciya karsilik geliyorsa onu user'a
    baglariz; yoksa user=None kalir ve sadece denenen ad saklanir."""
    creds = credentials or {}
    tried = (creds.get("username") or creds.get("email") or "")
    tried = str(tried)[:254]

    matched_user = None
    if tried:
        try:
            matched_user = User.objects.filter(username__iexact=tried).first()
        except Exception:
            matched_user = None

    ip = None
    ua = ""
    if request is not None:
        ip = _client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")[:300]

    try:
        LoginLog.objects.create(
            user=matched_user,
            username_tried=tried,
            event_type=LoginLog.EventType.LOGIN_FAILED,
            ip_address=ip,
            user_agent=ua,
        )
    except Exception:
        # Loglama hicbir zaman giris akisini bozmamali.
        pass
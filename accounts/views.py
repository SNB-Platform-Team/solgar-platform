"""
accounts app — authentication views.

Local username/password login with optional reCAPTCHA v3 verification,
logout, and a minimal authenticated landing page. Azure AD SSO is stubbed
until app registration is available.
"""

import json
import urllib.parse
import urllib.request
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm


def verify_recaptcha(token: str, remote_ip: str | None = None) -> bool:
    """
    Verify a reCAPTCHA v3 token with Google's siteverify endpoint.

    Returns True automatically when no secret key is configured, so local
    development is not blocked before keys exist.

    Args:
        token: Client-side reCAPTCHA token.
        remote_ip: Optional client IP address.

    Returns:
        True if verification passes or is skipped, False otherwise.
    """
    secret: str = settings.RECAPTCHA["SECRET_KEY"]
    if not secret:
        return True

    payload: dict[str, str] = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    data = urllib.parse.urlencode(payload).encode()
    try:
        with urllib.request.urlopen(
            "https://www.google.com/recaptcha/api/siteverify", data=data, timeout=5
        ) as response:
            result: dict[str, Any] = json.loads(response.read().decode())
    except Exception:
        return False

    min_score = float(settings.RECAPTCHA["MIN_SCORE"])
    return bool(result.get("success")) and result.get("score", 0) >= min_score


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """Render the login page and process credential submissions."""
    if request.user.is_authenticated:
        return redirect("accounts:home")

    form = LoginForm(request.POST or None)
    context: dict[str, Any] = {
        "form": form,
        "recaptcha_site_key": settings.RECAPTCHA["SITE_KEY"],
    }

    if request.method == "POST" and form.is_valid():
        token: str = form.cleaned_data["recaptcha_token"]
        if not verify_recaptcha(token, request.META.get("REMOTE_ADDR")):
            messages.error(request, "reCAPTCHA verification failed. Please try again.")
            return render(request, "accounts/login.html", context)

        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )

        if user is None:
            messages.error(request, "Invalid username or password.")
            return render(request, "accounts/login.html", context)

        if not user.is_enabled:
            messages.error(request, "This account is disabled.")
            return render(request, "accounts/login.html", context)

        login(request, user)
        return redirect("accounts:home")

    return render(request, "accounts/login.html", context)


@require_http_methods(["GET"])
def azure_login_view(request: HttpRequest) -> HttpResponse:
    """Placeholder for Azure AD SSO until app registration is completed."""
    messages.info(request, "Microsoft sign-in will be enabled soon.")
    return redirect("accounts:login")


@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the current user out and return to the login page."""
    logout(request)
    return redirect("accounts:login")


@login_required
def home_view(request: HttpRequest) -> HttpResponse:
    """Minimal authenticated landing page."""
    return render(request, "accounts/home.html")
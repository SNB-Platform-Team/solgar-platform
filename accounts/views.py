"""
accounts app — authentication views.

Local username/password login with optional reCAPTCHA v3 verification,
Microsoft SSO (Azure AD authorization-code flow), logout, and a dashboard.
"""

import json
import secrets
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

from authorization.decorators import require_screen

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
    """Start the Microsoft SSO flow by redirecting to the identity provider."""
    if not settings.AZURE_AD["CLIENT_ID"]:
        messages.info(request, "Microsoft sign-in will be enabled soon.")
        return redirect("accounts:login")

    from . import azure_auth

    state = secrets.token_urlsafe(24)
    request.session["azure_auth_state"] = state
    return redirect(azure_auth.build_auth_url(state))


@require_http_methods(["GET"])
def azure_callback_view(request: HttpRequest) -> HttpResponse:
    """Handle Microsoft's redirect: verify state, sign the user in."""
    from . import azure_auth
    from .models import User, UserType

    # CSRF protection: the returned state must match what we stored.
    expected_state = request.session.pop("azure_auth_state", None)
    if not expected_state or request.GET.get("state") != expected_state:
        messages.error(request, "Authentication failed. Please try again.")
        return redirect("accounts:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Authentication was cancelled.")
        return redirect("accounts:login")

    claims = azure_auth.acquire_user_claims(code)
    if claims is None:
        messages.error(request, "Could not verify your Microsoft account.")
        return redirect("accounts:login")

    oid = claims.get("oid")
    email = claims.get("email") or claims.get("preferred_username", "")
    name = claims.get("name", "")

    if not oid:
        messages.error(request, "Microsoft account is missing required information.")
        return redirect("accounts:login")

    # Match by Azure object ID; create the account on first sign-in.
    user, created = User.objects.get_or_create(
        azure_object_id=oid,
        defaults={
            "username": email or oid,
            "email": email,
            "first_name": name.split(" ")[0] if name else "",
            "last_name": " ".join(name.split(" ")[1:]) if " " in name else "",
            "user_type": UserType.EMPLOYEE,
        },
    )

    if not user.is_enabled:
        messages.error(request, "This account is disabled.")
        return redirect("accounts:login")

    login(request, user)
    return redirect("accounts:home")


@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the current user out and return to the login page."""
    logout(request)
    return redirect("accounts:login")


@login_required
def home_view(request: HttpRequest) -> HttpResponse:
    """Serve the React SPA entry point (single-page app root)."""
    return render(request, "index.html")

@login_required
@require_http_methods(["GET"])
def faq_view(request: HttpRequest) -> HttpResponse:
    """
    Rule-based FAQ screen. The user picks a question (no free text); the
    answer is rendered on the same page. Two questions in Phase 1:

    1. Access rights - dynamic: lists the screens this user can reach,
       resolved from accessible_screens (context processor) against the
       Screen catalogue (code -> Russian name).
    2. Platform purpose - static explanatory text.
    """
    from django.shortcuts import render

    from authorization.models import Screen

    # 1) Kullanicinin erisebildigi ekranlar (context processor ile ayni kaynak)
    from authorization.context_processors import accessible_screens as _acc
    codes = _acc(request).get("accessible_screens", set())

    # Kod -> Rusca isim eslemesi (Screen katalogu), sadece erisebildikleri
    name_by_code = dict(Screen.objects.values_list("code", "name"))
    my_screens = [name_by_code.get(code, code) for code in codes if code in name_by_code]
    my_screens = sorted(set(my_screens))

    context = {
        "my_screens": my_screens,
        "user_display": request.user.get_full_name() or request.user.username,
    }
    return render(request, "accounts/faq.html", context)

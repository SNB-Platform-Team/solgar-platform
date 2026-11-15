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


def _country_from_employees(email: str) -> str:
    """SSO mailinden ulkeyi dondur (solgar_org.employees.country).

    Eslesme: LOWER(TRIM(EMPLOYEE_EMAIL)) = email, sadece EMPLOYEE_ACTIVE=
    'ACTIVE'. Employees'teki country yazimi prm_countries ile birebir ayni
    (Russia, Kazakhistan, Ukraine ...), bu yuzden country-lock ve Страна
    dropdown ile dogrudan eslesir. Bulunamazsa '' (kisit yok; admin elle
    girer). solgar_org'a solgar_app'in SELECT yetkisi olmayabilir, bu yuzden
    solgar_prm gibi refdb baglantisindan okunur. Sadece ILK SSO olusturmada
    (get_or_create defaults) cagrilir; sonradan admin elle degistirirse ezilmez.
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return ""
    from django.db import connections
    sql = (
        "SELECT country FROM solgar_org.employees "
        "WHERE LOWER(TRIM(EMPLOYEE_EMAIL)) = %s "
        "AND UPPER(TRIM(EMPLOYEE_ACTIVE)) = 'ACTIVE' "
        "AND country IS NOT NULL AND country <> '' "
        "ORDER BY id LIMIT 1"
    )
    try:
        with connections["refdb"].cursor() as cur:
            cur.execute(sql, [email])
            row = cur.fetchone()
        return str(row[0]).strip() if row and row[0] else ""
    except Exception:
        return ""


def verify_recaptcha(token: str, remote_ip: str | None = None) -> bool:
    """
    Verify a reCAPTCHA v3 token with Google's siteverify endpoint.

    GUVENLIK (fail-closed): Onceden secret bos oldugunda True donuyordu, bu da
    prod'da anahtar set edilmezse CAPTCHA'yi tamamen devre disi birakiyordu
    (pentest: bos token'la giris). Artik davranis settings.RECAPTCHA_ENFORCE'a
    baglidir:
      - ENFORCE acik (prod varsayilani): secret yoksa VEYA token bos/gecersizse
        False (giris reddedilir). CAPTCHA atlanamaz.
      - ENFORCE kapali (local dev varsayilani): secret yoksa True (gelistirme
        bloke olmaz). Bu YALNIZCA DEBUG ortaminda otomatik devrededir.

    Args:
        token: Client-side reCAPTCHA token.
        remote_ip: Optional client IP address.

    Returns:
        True if verification passes, False otherwise.
    """
    enforce: bool = getattr(settings, "RECAPTCHA_ENFORCE", not settings.DEBUG)
    secret: str = settings.RECAPTCHA["SECRET_KEY"]

    # Anahtar yoksa: enforce'ta REDDET (fail-closed), degilse local dev -> gec.
    if not secret:
        return not enforce

    # Enforce'ta bos/eksik token dogrudan reddedilir (Google'a gitmeye gerek
    # yok; zaten basarisiz olur ama acikca kesmek daha net ve hizli).
    if enforce and not (token or "").strip():
        return False

    payload: dict[str, str] = {"secret": secret, "response": token or ""}
    if remote_ip:
        payload["remoteip"] = remote_ip

    data = urllib.parse.urlencode(payload).encode()
    try:
        with urllib.request.urlopen(
            "https://www.google.com/recaptcha/api/siteverify", data=data, timeout=5
        ) as response:
            result: dict[str, Any] = json.loads(response.read().decode())
    except Exception:
        # Google'a ulasilamadi. Enforce'ta fail-closed (giris reddedilir);
        # degilse gecise izin ver (dev). Prod'da gecici Google kesintisi
        # girisleri durdurabilir — bu bilincli bir guvenlik tercihidir.
        return not enforce

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
        from . import ratelimit

        username: str = form.cleaned_data["username"]

        # 1) Brute-force kilidi: IP ya da kullanici sayaci esigi astiysa,
        #    sifre dogru olsa bile giris penceresi boyunca reddet. Boylece
        #    sinirsiz deneme yapilamaz (pentest: "bir brute baslatirim").
        if ratelimit.is_locked(request, username):
            messages.error(
                request,
                "Слишком много попыток входа. Попробуйте позже.",  # Too many attempts
            )
            return render(request, "accounts/login.html", context, status=429)

        # 2) CAPTCHA (fail-closed; verify_recaptcha enforce'a gore davranir).
        token: str = form.cleaned_data["recaptcha_token"]
        if not verify_recaptcha(token, ratelimit.client_ip(request)):
            # Basarisiz CAPTCHA da bir deneme olarak sayilir (token olmadan
            # brute-force denemesi sayaci yesin).
            ratelimit.register_failure(request, username)
            messages.error(request, "reCAPTCHA verification failed. Please try again.")
            return render(request, "accounts/login.html", context)

        user = authenticate(
            request,
            username=username,
            password=form.cleaned_data["password"],
        )

        if user is None:
            ratelimit.register_failure(request, username)
            messages.error(request, "Invalid username or password.")
            return render(request, "accounts/login.html", context)

        if not user.is_enabled:
            # Devre disi hesap: sayaci artirmiyoruz (kimlik bilgisi dogru),
            # ama girise de izin yok.
            messages.error(request, "This account is disabled.")
            return render(request, "accounts/login.html", context)

        # Basarili: bu kullanici+IP sayaclarini temizle.
        ratelimit.reset(request, username)
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
    from django.urls import reverse

    state = secrets.token_urlsafe(24)
    request.session["azure_auth_state"] = state
    # Kullanicinin geldigi domaine gore callback URL'si (fortemira.ru/.org/
    # .online). build_absolute_uri istek host'unu kullanir -> .ru'dan giren
    # .ru'ya doner. Callback'te AYNI redirect_uri lazim, session'da saklanir.
    redirect_uri = request.build_absolute_uri(reverse("accounts:azure_callback"))
    request.session["azure_redirect_uri"] = redirect_uri
    return redirect(azure_auth.build_auth_url(state, redirect_uri=redirect_uri))


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

    # build_auth_url'de kullanilan redirect_uri ile AYNISINI kullan (Microsoft
    # kurali). Login adiminda session'a yazildi; yoksa istek host'undan uret.
    from django.urls import reverse
    redirect_uri = request.session.pop("azure_redirect_uri", None) \
        or request.build_absolute_uri(reverse("accounts:azure_callback"))
    claims = azure_auth.acquire_user_claims(code, redirect_uri=redirect_uri)
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
            # Ulke: solgar_org.employees.country'den (SADECE ilk olusturmada).
            # Employees'teki yazim prm_countries ile birebir ayni oldugu icin
            # country-lock ve Страna dropdown ile dogrudan eslesir. Eslesme
            # yoksa '' (kisit yok). defaults'ta oldugu icin yalnizca create
            # aninda uygulanir; sonradan admin elle degistirirse ezilmez.
            "country": _country_from_employees(email),
        },
    )

    if created and user.access_level is None:
        # Ilk giriste: menu_user_relation'daki kendi satirina gore AccessLevel
        # (email -> employees -> employee_name -> menu satiri -> imza -> level).
        # SADECE create aninda; sonradan admin elle degistirirse ezilmez.
        # Menu'de bulunamazsa eski davranis: en dusuk rank (fallback).
        from authorization.menu_access import level_for_email
        from authorization.models import AccessLevel

        level = level_for_email(email)
        if level is None:
            level = AccessLevel.objects.filter(rank=1).order_by("rank").first()
        if level:
            user.access_level = level
            user.save(update_fields=["access_level"])

    if not user.is_enabled:
        messages.error(request, "This account is disabled.")
        return redirect("accounts:login")

    login(request, user)
    return redirect("accounts:home")


@require_http_methods(["GET", "POST"])
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

"""
Login brute-force korumasi: IP + kullanici adi bazli deneme sayaci ve
gecici kilitleme. Django cache (prod'da Redis) uzerinde calisir; backend'den
bagimsizdir.

Pentest bulgusu: login'de hic hiz siniri / kilitleme yoktu -> sinirsiz
brute-force mumkundu (ozellikle CAPTCHA bypass ile birlikte). Bu modul iki
ayri boyutta sayar:
  - IP bazli:   bir IP'nin toplam basarisiz denemesi (dagitik kullanici
                adi denemelerini de yakalar).
  - Kullanici:  bir kullanici adina yapilan basarisiz denemeler (tek hesaba
                yonelik saldiri; IP degistirse bile hesabi korur).
Herhangi biri esigi asarsa giris penceresi boyunca kilitlenir.

Sayaclar YALNIZCA basarisiz denemede artar; basarili giriste ilgili
kullanici+IP sayaclari sifirlanir. Boylece normal kullanicinin arada bir
yanlis sifresi onu kilitlemez.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache

# --- Esikler (settings'ten override edilebilir) ---
# Pencere icinde izin verilen maksimum basarisiz deneme ve kilit suresi (sn).
_MAX_IP = int(getattr(settings, "LOGIN_RATELIMIT_IP_MAX", 30))
_MAX_USER = int(getattr(settings, "LOGIN_RATELIMIT_USER_MAX", 10))
_WINDOW = int(getattr(settings, "LOGIN_RATELIMIT_WINDOW", 15 * 60))  # 15 dk

_PREFIX = "loginfail"


def _norm_user(username: str) -> str:
    return (username or "").strip().lower()[:150]


def _ip_key(ip: str) -> str:
    return f"{_PREFIX}:ip:{ip or 'unknown'}"


def _user_key(username: str) -> str:
    return f"{_PREFIX}:user:{_norm_user(username)}"


def client_ip(request) -> str:
    """Istemci IP'si. Azure/proxy arkasinda X-Forwarded-For'un ILK IP'si.

    NOT: X-Forwarded-For istemci tarafindan sahte gonderilebilir; ancak
    guvenilir bir proxy (Azure) onunde en soldaki IP gercek istemciyi
    yansitir. IP bazli sayac tek basina degil, kullanici bazli sayacla
    BIRLIKTE kullanildigi icin sahte XFF tek hesabi yine de koruyamaz.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""


def is_locked(request, username: str) -> bool:
    """IP ya da kullanici sayaci esigi astiysa True (giris reddedilmeli)."""
    ip = client_ip(request)
    ip_n = cache.get(_ip_key(ip), 0) or 0
    user_n = cache.get(_user_key(username), 0) or 0
    return ip_n >= _MAX_IP or user_n >= _MAX_USER


def register_failure(request, username: str) -> None:
    """Basarisiz giris: IP ve kullanici sayaclarini artir (TTL'li)."""
    ip = client_ip(request)
    for key in (_ip_key(ip), _user_key(username)):
        try:
            # add + incr: yoksa 0 ile olustur (TTL ver), sonra artir. incr
            # mevcut TTL'i korur, boylece pencere sifirlanmaz (kayan degil,
            # sabit pencere). add zaten varsa dokunmaz.
            cache.add(key, 0, _WINDOW)
            cache.incr(key)
        except ValueError:
            # incr, add ile arada anahtar dusmusse ValueError verebilir;
            # yeniden kur.
            cache.set(key, 1, _WINDOW)


def reset(request, username: str) -> None:
    """Basarili giris: bu kullanici ve IP sayaclarini temizle."""
    ip = client_ip(request)
    cache.delete(_ip_key(ip))
    cache.delete(_user_key(username))

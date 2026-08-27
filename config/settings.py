"""
Solgar Internal Platform — Django settings.

Secrets are never hardcoded; they are read from the .env file via get_secret().
Database access goes through the Django ORM only — no raw SQL anywhere.
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BASE_DIR: Path = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

_SENTINEL = object()

def get_secret(key: str, default: Any = _SENTINEL) -> str:
    """
    Read a configuration value from the environment.

    Args:
        key: Environment variable name.
        default: Fallback value; if omitted, a missing key raises.

    Returns:
        The value as a string.

    Raises:
        KeyError: If the key is missing and no default was given.
    """
    value = os.environ.get(key)
    if value is not None:
        return value
    if default is _SENTINEL:
        raise KeyError(f"Missing required environment variable: {key}")
    return default

#  Core
SECRET_KEY: str = get_secret("DJANGO_SECRET_KEY")
DEBUG: bool = get_secret("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS: list[str] = [
    h.strip() for h in get_secret("ALLOWED_HOSTS", "").split(",") if h.strip()
]

#  Applications
INSTALLED_APPS: list[str] = [
  #  "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "employees",
    "authorization",
    "approvals",
    "sales",
    "rest_framework",
    "corsheaders"
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

MIDDLEWARE: list[str] = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.ActivityLogMiddleware",

]

ROOT_URLCONF: str = "config.urls"

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "authorization.context_processors.accessible_screens",
                "authorization.context_processors.accessible_screens",
                "approvals.context_processors.pending_approvals_count",
            ],
        },
    },
]

WSGI_APPLICATION: str = "config.wsgi.application"

# --- Connection pooling ---
# Cok-kullanicili ortamda (hedef: ~500 kullanici) her HTTP isteginde yeni DB
# baglantisi acmak pahalidir. CONN_MAX_AGE ile baglanti belirli sure canli
# tutulup yeniden kullanilir. 60 sn guvenli: Azure Entra token suresinden
# (saatler) cok kisa, dis sunucunun bosta-timeout'undan buyuk ihtimalle kisa.
DB_CONN_MAX_AGE: int = int(get_secret("DB_CONN_MAX_AGE", "60"))

# --- Database ---
# USE_AZURE_MYSQL=True  → Azure MySQL with Entra ID token auth (production)
# otherwise             → local Docker MySQL with a static password
USE_AZURE_MYSQL: bool = get_secret("USE_AZURE_MYSQL", "False") == "True"

# External reference database (solgar_tst on Olga's server) — read-only,
# feeds the product-category and geographic report filters.
# Azure App Service, bu degiskenleri EXTERNAL_DB_* isimleriyle sagliyor;
# lokal .env ise REFDB_* kullanabilir. Once EXTERNAL_DB_*, yoksa REFDB_* okunur.
def _ref_secret(ext_key: str, ref_key: str, default: str = "") -> str:
    """Prefer the Azure EXTERNAL_DB_* name, fall back to the local REFDB_* name."""
    val = os.environ.get(ext_key)
    if val is not None and val != "":
        return val
    return get_secret(ref_key, default)

REFERENCE_DB = {
    "ENGINE": "django.db.backends.mysql",
    "HOST": _ref_secret("EXTERNAL_DB_HOST", "REFDB_HOST", ""),
    "PORT": _ref_secret("EXTERNAL_DB_PORT", "REFDB_PORT", "3306"),
    "NAME": _ref_secret("EXTERNAL_DB_NAME", "REFDB_NAME", ""),
    "USER": _ref_secret("EXTERNAL_DB_USER", "REFDB_USER", ""),
    "PASSWORD": _ref_secret("EXTERNAL_DB_PASSWORD", "REFDB_PASSWORD", ""),
    "OPTIONS": {"charset": "utf8mb4"},
    "CONN_MAX_AGE": DB_CONN_MAX_AGE,
}

if USE_AZURE_MYSQL:
    DATABASES: dict[str, dict[str, Any]] = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": get_secret("DB_NAME"),
            "USER": get_secret("DB_USER"),
            "PASSWORD": "",  # injected as an Entra ID token by config.db_token
            "HOST": get_secret("DB_HOST"),
            "PORT": get_secret("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4", "ssl": {"ssl-mode": "REQUIRED"}},
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        },
        "refdb": REFERENCE_DB,
    }
else:
    DATABASES: dict[str, dict[str, Any]] = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": get_secret("DB_NAME"),
            "USER": get_secret("DB_USER"),
            "PASSWORD": get_secret("DB_PASSWORD"),
            "HOST": get_secret("DB_HOST", "127.0.0.1"),
            "PORT": get_secret("DB_PORT", "3307"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        },
        "refdb": REFERENCE_DB,
    }

DATABASE_ROUTERS = ["config.routers.ReferenceRouter"]

#  Custom user model
AUTH_USER_MODEL: str = "accounts.User"

#  Password validation
AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

#  Auth redirects
LOGIN_URL: str = "accounts:login"
LOGIN_REDIRECT_URL: str = "accounts:home"
LOGOUT_REDIRECT_URL: str = "accounts:login"

#  reCAPTCHA v3 (disabled locally while keys are empty)
RECAPTCHA: dict[str, str] = {
    "SITE_KEY": get_secret("RECAPTCHA_SITE_KEY", ""),
    "SECRET_KEY": get_secret("RECAPTCHA_SECRET_KEY", ""),
    "MIN_SCORE": get_secret("RECAPTCHA_MIN_SCORE", "0.5"),
}

#  Azure AD (filled in when SSO is wired up)
AZURE_AD: dict[str, str] = {
    "CLIENT_ID": get_secret("AZURE_AD_CLIENT_ID", ""),
    "TENANT_ID": get_secret("AZURE_AD_TENANT_ID", ""),
    "CLIENT_SECRET": get_secret("AZURE_AD_CLIENT_SECRET", ""),
    "REDIRECT_URI": get_secret("AZURE_AD_REDIRECT_URI", ""),
}

#  Internationalization
LANGUAGE_CODE: str = "en-us"
TIME_ZONE: str = "Europe/Istanbul"
USE_I18N: bool = True
USE_TZ: bool = True

#  Static files
STATIC_URL: str = "/static/"
STATICFILES_DIRS: list[Path] = [BASE_DIR / "static"]
STATIC_ROOT: Path = BASE_DIR / "staticfiles"

STORAGES: dict[str, dict[str, str]] = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

# --- Production security (enabled only when DEBUG is off) ---
if not DEBUG:
    SECURE_SSL_REDIRECT: bool = True
    SESSION_COOKIE_SECURE: bool = True
    CSRF_COOKIE_SECURE: bool = True
    SECURE_HSTS_SECONDS: int = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_HSTS_PRELOAD: bool = True
    SECURE_PROXY_SSL_HEADER: tuple[str, str] = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF: bool = True
    X_FRAME_OPTIONS: str = "DENY"
    CSRF_TRUSTED_ORIGINS: list[str] = [
        f"https://{host}" for host in ALLOWED_HOSTS if host
    ]

# Load the Azure MySQL token injector (no-op unless USE_AZURE_MYSQL=True)
if USE_AZURE_MYSQL:
    import config.db_token  # noqa: F401
# ---------------------------------------------------------------------------
# SQL Server (1C stock data) - read-only, accessed via pymssql (not the ORM).
# Populated from environment variables so credentials stay out of the code.
# ---------------------------------------------------------------------------
SQLSERVER_CONFIG = {
    "HOST": get_secret("SQLSERVER_HOST", ""),
    "PORT": get_secret("SQLSERVER_PORT", "1433"),
    "USER": get_secret("SQLSERVER_USER", ""),
    "PASSWORD": get_secret("SQLSERVER_PASSWORD", ""),
    "NAME": get_secret("SQLSERVER_NAME", ""),
}


# --- CORS (React frontend erişimi) ---
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

# --- CSRF trusted origins (React dev frontend) ---
# Dev'de React (localhost:5173) POST istekleri icin origin guveni.
# Production'da yukaridaki `if not DEBUG` blogundaki https origin'ler gecerli.
if DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

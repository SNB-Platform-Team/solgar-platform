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
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION: str = "config.wsgi.application"

# --- Database (MySQL via Docker) ---
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
    }
}

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

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"
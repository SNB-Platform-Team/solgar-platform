"""
config.settings_test — test-only settings.

Inherits everything from the normal settings, then overrides the databases
so tests DON'T need CREATE privilege on MySQL (solgar_app lacks it) and
DON'T touch the real data. The default DB becomes an in-memory SQLite that
Django can create freely; refdb/sqlserver are pointed at SQLite too so any
accidental use in a test fails loudly instead of hitting a live server.

Run with:
    python manage.py test --settings=config.settings_test
or:
    set DJANGO_SETTINGS_MODULE=config.settings_test   (Windows)
    python manage.py test

Scope: this supports tests of pure logic and auth/permission/screen rules —
things that use the User/AccessLevel/Screen tables (Django-managed). Models
that are managed=False and live in external schemas (pharmacy_data_*,
doctor_data, solgar_prm.*) are NOT created in the SQLite test DB; tests that
query them directly won't work here (use mocks or a smoke test for those).
"""

from .settings import *  # noqa: F401,F403

# --- Test databases: SQLite, no external servers, no special privileges ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    # refdb / sqlserver normally point at external MySQL / MSSQL. In tests we
    # redirect them to throwaway SQLite files so nothing reaches a live host.
    # A test that genuinely needs their data should mock the connection.
    "refdb": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# If the project defines extra connections (e.g. a SQL Server alias), add a
# harmless SQLite stand-in for each so test-DB setup never dials out.
try:
    from .settings import DATABASES as _REAL_DBS  # noqa: F401
    for _alias in _REAL_DBS:
        DATABASES.setdefault(
            _alias,
            {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        )
except Exception:
    pass

# Faster password hashing in tests (login/force_login setup is cheaper).
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Tests shouldn't depend on a running cache server; use local memory.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Keep tests quiet and deterministic.
DEBUG = False

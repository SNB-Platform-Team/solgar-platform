# Solgar Internal Platform

Internal web platform for Solgar employees. Django + MySQL, deployed on Azure.

> **Status:** Early development — authentication layer only.

---

## Overview

A server-rendered Django application intended for internal use by Solgar staff.
Authentication will run on Azure AD SSO once app registration is available; a
local username/password path exists as a fallback during development.

**Stack**

| Layer | Technology |
|---|---|
| Backend | Django 5.1 (server-side rendering) |
| Database | MySQL 8.0 (Docker locally, Azure MySQL Flexible in production) |
| Auth | Django sessions; Azure AD SSO planned |
| Bot protection | reCAPTCHA v3 ML (invisible) |
| Hosting | Azure App Service (planned) |
| Secrets | `.env` locally, Azure Key Vault in production |

---

## Architectural decisions

**ORM only — no raw SQL.** All database access goes through the Django ORM.
Raw SQL with string interpolation is the primary source of SQL injection
vulnerabilities; the ORM parameterizes queries automatically and keeps the code
portable across database backends.

**No secrets in source control.** Configuration is read from environment
variables via a `get_secret()` helper. `.env` is gitignored; `.env.example`
documents the required keys without exposing values. In production the same
variables will be supplied by Azure Key Vault references.

**Custom user model from day one.** `accounts.User` extends `AbstractUser` with
`azure_object_id`, `user_type`, `department`, `phone`, and `is_enabled`.
Swapping the user model after the first migration is disruptive, so it was
introduced before any tables were created.

**Server-side rendering.** No SPA. Pages are rendered by Django and sessions are
held in an HTTP-only cookie. When Azure AD SSO is added it will use the OAuth2
authorization code flow, keeping the client secret and tokens on the server.

**We plan to open the platform to consumers, not only staff as well in the future.

---



## Local setup

**Requirements:** Python 3.10+, Docker Desktop, Git

```bash
# 1. Clone and enter the project
git clone https://github.com/cnrcvk7/solgar-internal-platform.git
cd solgar-internal-platform

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Configuration
copy .env.example .env         # Linux/macOS: cp .env.example .env
```

Generate a secret key and paste it into `.env` as `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set `DB_PASSWORD` and `MYSQL_ROOT_PASSWORD` to values of your choosing — the
MySQL container is initialized with them on first run.

```bash
# 5. Start MySQL
docker compose up -d

# 6. Migrate and create an admin account
python manage.py migrate
python manage.py createsuperuser

# 7. Run
python manage.py runserver
```

| URL | Purpose |
|---|---|
| http://127.0.0.1:8000/login/ | Login page |
| http://127.0.0.1:8000/ | Dashboard (requires login) |
| http://127.0.0.1:8000/admin/ | Django admin |

MySQL runs on host port **3307** to avoid clashing with a locally installed
MySQL instance on 3306.

---

## Configuration reference

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django cryptographic signing key |
| `DJANGO_DEBUG` | `True` locally, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated list of permitted hostnames |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | MySQL credentials |
| `DB_HOST`, `DB_PORT` | MySQL connection target |
| `MYSQL_ROOT_PASSWORD` | Root password for the Docker container |
| `RECAPTCHA_SITE_KEY` | Public reCAPTCHA key (client-side) |
| `RECAPTCHA_SECRET_KEY` | Private reCAPTCHA key (server-side) |
| `RECAPTCHA_MIN_SCORE` | Minimum score to accept, `0.0`–`1.0` |
| `AZURE_AD_CLIENT_ID` | Azure AD application ID |
| `AZURE_AD_TENANT_ID` | Azure AD directory ID |
| `AZURE_AD_CLIENT_SECRET` | Azure AD client secret |
| `AZURE_AD_REDIRECT_URI` | OAuth2 callback URL |

reCAPTCHA verification is skipped while `RECAPTCHA_SECRET_KEY` is empty, so
local development is not blocked before keys are issued. It activates
automatically once the key is set.

---

## Current state

**Implemented**

- Custom user model with Azure AD fields
- Local username/password login with session handling
- Logout, disabled-account rejection, form validation
- reCAPTCHA v3 integration (activates when keys are configured)
- Django admin with custom user fields
- MySQL via Docker Compose

**Pending**

- Azure AD SSO (blocked on app registration)
- reCAPTCHA keys (blocked on a company Google account)
- Role-based authorization (approach not yet decided)
- Azure deployment (App Service, Key Vault, MySQL Flexible)
- Test suite

---



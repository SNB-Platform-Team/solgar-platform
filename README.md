# Solgar Internal Platform

Internal web platform for Solgar employees. Django + MySQL, deployed on Azure App Service.

> **Status:** Active development — authentication, employee directory, and audit logging live on Azure.

---

## Overview

A server-rendered Django application for internal use by Solgar staff. It runs on
Azure App Service and connects to Azure Database for MySQL. Authentication uses a
local username/password path today; Azure AD SSO is implemented in code and
activates once app registration details are supplied.

**Stack**

| Layer | Technology |
|---|---|
| Backend | Django 5.1 (server-side rendering) |
| Database | MySQL 8.0 (Docker locally, Azure Database for MySQL in production) |
| Auth | Django sessions; Azure AD SSO (code ready, pending registration) |
| Bot protection | reCAPTCHA v3 (invisible, activates when keys are set) |
| Hosting | Azure App Service (Linux, Python 3.10) |
| Deployment | GitHub Actions (automatic on push to `main`) |
| Secrets | `.env` locally, App Service application settings in production |

---

## Architectural decisions

**ORM only — no raw SQL.** All database access goes through the Django ORM,
organized behind a repository/service layer. Raw SQL with string interpolation is
the primary source of SQL injection vulnerabilities; the ORM parameterizes
queries automatically and keeps the code portable across database backends.

**No secrets in source control.** Configuration is read from environment
variables via a `get_secret()` helper. `.env` is gitignored; `.env.example`
documents the required keys without exposing values. In production the same
variables are supplied through App Service application settings.

**Custom user model from day one.** `accounts.User` extends `AbstractUser` with
`azure_object_id`, `user_type`, `department`, `phone`, and `is_enabled`.
Swapping the user model after the first migration is disruptive, so it was
introduced before any tables were created.

**Server-side rendering.** No SPA. Pages are rendered by Django and sessions are
held in an HTTP-only cookie. Azure AD SSO uses the OAuth2 authorization code
flow, keeping the client secret and tokens on the server.

**Azure MySQL via Entra ID token auth.** The production database runs in
Entra-ID-only mode (no static password). The application authenticates with a
short-lived token obtained through the App Service's Managed Identity; the token
is injected into each new database connection and refreshed automatically.

**Repository/service layering.** Feature apps (e.g. `employees`) separate data
access (repository), business logic (service), and presentation (views), keeping
the ORM calls in one place and the views thin.

**Screen-based authorization.** Access is controlled by named screens and access levels, kept separate from the organizational hierarchy. Each screen has a code; each access level grants a set of screens; each user has one access level. The sidebar shows only permitted screens, and views are guarded by a require_screen decorator so direct URL access is also blocked. Superusers bypass the checks.

**Approval workflow with hierarchy routing.** Equipment requests move through a state machine (pending → approved / rejected / cancelled). When an employee submits a request, the system automatically routes it to their manager (a self-referential manager field on the user model) for a decision. Business rules live in a service layer: only the assigned approver may decide, only pending requests can be acted on, and only the original requester may cancel.

**Legacy desktop migration (Solgar Intern).** Screens from the legacy Java desktop application are being rebuilt as web modules rather than translated line by line. The first migrated screen is the chain sales upload: an Excel file (.xls or .xlsx) is parsed, each product line is classified as Solgar or Bounty by its name, brand totals are computed, and the data is previewed before saving. A companion report screen filters saved sales server-side and aggregates totals.

**Parametric parsing (chains and brands in the database).** Rather than a separate parser per chain, a single parser reads chain "definitions" stored in the database: each defines its column mapping, country, and layout orientation. Adding a chain is a data change (a new row), not new code. Brand classification works the same way — each brand's identifying keywords live in a database table, with one brand marked as the default. Deactivating a brand ("pulling it out") is a single flag change, not a code edit.

**Parametric parsing** chains and brands as data. A single ChainParser reads chain "definitions" from the database (ChainDefinition): each holds a column mapping, country, source type (pharmacy/distributor), and layout orientation. Adding a chain is a new row, not new code. Brand classification is likewise data-driven (BrandDefinition): each brand's keywords live in a table with one default brand, so deactivating a brand is a single flag change.

Reference-data filters. Product-category and geographic filters on the sales report resolve against reference tables (ProductGroup, AddressGroup) loaded from solgar_tst. Sales rows match by lowercased product name and by city (settlement suffixes like " г" stripped before matching).

Schema prefixes. Tables are grouped by prefix: intern_sls_ (definitions), solgar_stk_ (distributor data), solgar_tst_ (reference data).

We plan to open the platform to consumers in the future, not only staff.

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
MySQL container is initialized with them on first run. Keep `USE_AZURE_MYSQL=False`
locally so the app uses the Docker database.

```bash
# 5. Start MySQL
docker compose up -d

# 6. Migrate and create an admin account
python manage.py migrate
python manage.py createsuperuser

# 7. Import employees (optional, if you have the source file)
python manage.py import_employees data/List_AccsessesHHHH.xlsx

# 8. Run
python manage.py runserver
```

| URL | Purpose |
|---|---|
| http://127.0.0.1:8000/login/ | Login page |
| http://127.0.0.1:8000/ | Dashboard (requires login) |
| http://127.0.0.1:8000/employees/ | Employee directory |
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
| `USE_AZURE_MYSQL` | `False` locally (Docker), `True` in production (token auth) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | MySQL credentials (no password in Azure mode) |
| `DB_HOST`, `DB_PORT` | MySQL connection target |
| `MYSQL_ROOT_PASSWORD` | Root password for the Docker container |
| `RECAPTCHA_SITE_KEY` | Public reCAPTCHA key (client-side) |
| `RECAPTCHA_SECRET_KEY` | Private reCAPTCHA key (server-side) |
| `RECAPTCHA_MIN_SCORE` | Minimum score to accept, `0.0`–`1.0` |
| `AZURE_AD_CLIENT_ID` | Azure AD application ID |
| `AZURE_AD_TENANT_ID` | Azure AD directory ID |
| `AZURE_AD_CLIENT_SECRET` | Azure AD client secret |
| `AZURE_AD_REDIRECT_URI` | OAuth2 callback URL |

reCAPTCHA verification is skipped while `RECAPTCHA_SECRET_KEY` is empty, so local
development is not blocked before keys are issued. It activates automatically once
the key is set. The same pattern applies to Azure AD SSO: the Microsoft sign-in
button shows a "coming soon" message until `AZURE_AD_CLIENT_ID` is set.

---

## Deployment (Azure App Service)

The app deploys automatically via GitHub Actions on every push to `main`.

**Key configuration:**

- **Startup command:** `gunicorn config.wsgi:application`
- **Application settings:** same variables as `.env`, with `USE_AZURE_MYSQL=True`
  and no `DB_PASSWORD` (token auth is used instead)
- **Managed Identity:** must be enabled so the app can obtain database tokens
- **Migrations:** run once from the App Service SSH console after the first deploy:
```bash
  python manage.py migrate
```

The production database uses Entra ID token authentication, so the app's Managed
Identity must be granted access to the target database, and outbound network
access to the MySQL host must be permitted.

---

## Current state

**Implemented**

- Custom user model with Azure AD fields
- Local username/password login with session handling
- Logout, disabled-account rejection, form validation
- reCAPTCHA v3 integration (activates when keys are configured)
- Azure AD SSO via OAuth2 authorization code flow (activates when registered)
- Login/logout audit logging (viewable in Django admin)
- Employee directory: list, live search, department filter, detail pages
- Repository/service architecture (ORM only)
- Django admin with custom user fields
- MySQL via Docker Compose (local) and Azure MySQL with token auth (production)
- Deployed on Azure App Service with automatic GitHub Actions deployment
- Screen-based access levels (menu filtering + URL-level protection)
- Dashboard approval statistics and pending-count badge in the sidebar
- Sales module: chain Excel upload (MFO format), Solgar/Bounty classification, preview-then-save
- Sales report screen with server-side filtering and brand totals
- .xls and .xlsx support for old versions (before 2003)
- "Solgar Intern" grouped navigation menu
- Parametric chain parser driven by database definitions (ChainDefinition)
- Parametric brand classification driven by database definitions (BrandDefinition)
- Two chains configured as definitions: MFO (pharmacy) and APTEKA_RU
- Excel export of filtered sales
- Parametric chain parser (ChainDefinition) — MFO (pharmacy) and APTEKA_RU (distributor)
- Parametric brand classification (BrandDefinition) — Solgar default, Nature's Bounty
- Distributor sales/stock upload and report screens (operation type: sale/stock)
- Sales report menu complete: Excel upload, pharmacy chain report, distributor upload, stock/sales view
- Product-category filters (main/sub group) and geographic filters (region/district) via reference data
- load_reference_data management command for loading product/address CSVs

**Pending**

- Azure AD SSO activation (blocked on app registration details)
- reCAPTCHA keys (blocked on a company Google account)
- Legacy migration: additional chain formats beyond MFO
- Legacy migration: remaining screens (marketing expenses, evaluation, etc.)
- 1C integration (if required by migrated screens)
- Employee data import to production
- Multi-language support 
- Power BI report embedding 
- Test suite
- Distributor sales/stock upload screen (operation type: sale/stock)
- Migration of sales storage to the intern_sls schema / sales_orders
- Parametric countries (currently a fixed list)
- Connect reference data to live solgar_tst (currently loaded from CSV) — pending decision
- Additional chains from the Java Companies class (as definitions, no code)
- Horizontal-layout parsing (structure ready via orientation, vertical implemented)
- Pharmacy database CRUD screen (PharmacyEntryUpdate equivalent)
- Parametric countries (currently a fixed list)

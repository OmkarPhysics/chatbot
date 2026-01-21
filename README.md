# Django DRF Email-Only Auth (User Lifecycle)

This repo is a **Django 4.x + Django REST Framework** project that implements the full user lifecycle using **email-only credentials**:

- Register → **Email OTP verification** → Login (JWT) → Logout (refresh token blacklisted)
- Forgot password / Reset password emails via **SMTP**
- Profile CRUD with correct permissions
- Minimal HTML pages to exercise the API from a browser

## Features

- **Custom User model** (`apps.accounts.models.User`) keyed by `email`
  - `email` is stored **lowercased** and has a DB-level unique constraint
  - duplicate emails are rejected in serializers + at the database level
- **Email verification by OTP** (`apps.accounts.models.EmailOTP`)
- **JWT auth** via `djangorestframework-simplejwt`
  - **Access tokens: 60 minutes**
  - **Refresh tokens: 7 days**
  - **Logout = refresh token blacklisted** (`rest_framework_simplejwt.token_blacklist`)
- **Profiles** (`apps.profiles.models.UserProfile`)
  - currently: `name`, `email` (mirrors user email), `avatar`
  - structured to be extended later without migration pain
- **No Django forms/ModelForms**: all validation is in DRF serializers

## Project layout

- `config/` – Django settings + root URLs
- `apps/accounts/` – custom user model, OTP verification, JWT endpoints, password reset endpoints
- `apps/profiles/` – `UserProfile` + `/me` endpoints + admin CRUD API
- `apps/web/` + `templates/web/` – minimal HTML pages that call the API
- `tests/` – basic unit tests for auth + password reset

## Setup

### 1) Create and activate a virtualenv

Note: **Django 4.2.x supports Python up to 3.12**. If your system Python is 3.13, use Python 3.12 (e.g. via `pyenv`) to create the venv.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

Because `.env.example` is blocked in this environment, use `env.example` as the template.

```bash
cp env.example .env
set -a; source .env; set +a
```

At minimum, set:

- `DJANGO_SECRET_KEY`
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

If you want to test without SMTP, you can temporarily set:

```bash
export DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 4) Migrate and run

Important: the project uses a **custom user model**, so do migrations before creating users.

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open the browser pages at:

- `http://127.0.0.1:8000/` (links to all exercisers)

## API endpoints

Base: `/api/`

### Auth

- `POST /api/auth/register/` – register + send OTP email
- `POST /api/auth/verify-email/` – verify OTP
- `POST /api/auth/login/` – JWT login (`access`, `refresh`)
- `POST /api/auth/token/refresh/` – refresh access token
- `POST /api/auth/logout/` – blacklist refresh token
- `POST /api/auth/forgot-password/` – send reset link email (always returns 200)
- `POST /api/auth/reset-password/` – confirm reset (`uidb64`, `token`, `new_password`)

### Profile (regular users)

- `GET /api/profile/me/`
- `PATCH /api/profile/me/`
- `DELETE /api/profile/me/` (deletes the user + cascades profile)

### Admin profile CRUD

Requires staff/superuser:

- `GET /api/profile/admin/profiles/`
- `POST /api/profile/admin/profiles/` (requires `user_id`)
- `GET/PATCH/DELETE /api/profile/admin/profiles/{id}/`

## cURL examples

### Register

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"SuperSecurePass123!","name":"Alice"}'
```

### Verify email (OTP)

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","otp":"123456"}'
```

### Login (JWT)

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"SuperSecurePass123!"}'
```

### Refresh token

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh>"}'
```

### Logout (blacklist refresh)

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh>"}'
```

### Get profile (me)

```bash
curl -s http://127.0.0.1:8000/api/profile/me/ \
  -H "Authorization: Bearer <access>"
```

### Update profile name

```bash
curl -s -X PATCH http://127.0.0.1:8000/api/profile/me/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated"}'
```

### Upload avatar

```bash
curl -s -X PATCH http://127.0.0.1:8000/api/profile/me/ \
  -H "Authorization: Bearer <access>" \
  -F "avatar=@/path/to/avatar.png"
```

## Browser exercisers (templates)

These pages call the exact same JSON API and store tokens in `localStorage`:

- `/register/`
- `/verify-email/`
- `/login/`
- `/profile/`
- `/forgot-password/`
- `/reset-password/`

## Running tests

```bash
python manage.py test
```

## Notes on extending `UserProfile`

`UserProfile` is intentionally small and stable. You can safely add fields later (address, phone, preferences, etc.) without breaking existing migrations.\n
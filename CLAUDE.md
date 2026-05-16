# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VendasKibubble is a sales management system for a Japanese food and Bubble Tea restaurant, used at events. Built with Django 6 + Django REST Framework, with a Bootstrap 5 frontend.

## Development Setup

Activate the virtual environment before running any commands:

```bash
# Windows
venv\Scripts\activate

# Unix
source venv/bin/activate
```

The project lives inside the `sistemadevenda/` subdirectory. Run all Django commands from there:

```bash
cd sistemadevenda
python manage.py runserver
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser
python manage.py test                        # run all tests
python manage.py test vendas                 # run tests for the vendas app
```

## Database

PostgreSQL is required (not SQLite — the `db.sqlite3` file in the repo is unused):

- **DB name:** `kibubble`
- **User:** `postgres`
- **Password:** `1234`
- **Host:** `localhost:5432`

## Architecture

```
sistemadevenda/
  manage.py
  mysite/          # Django project config (settings, root URLs, wsgi/asgi)
  vendas/          # Single Django app containing all business logic
    models.py      # Data models
    views.py       # View functions (template-based)
    urls.py        # App URL routes (mounted at /vendas/)
    templates/     # HTML templates using Django template language
    admin.py       # Django admin registrations (currently empty)
    migrations/    # Database migrations
```

### URL structure

| Path | Description |
|------|-------------|
| `/vendas/` | Home (index) |
| `/vendas/login/` | Login — issues JWT tokens on success |
| `/vendas/register/` | Register new user — requires `is_staff` |
| `/admin/` | Django admin |
| `/api/token/` | JWT token obtain (DRF SimpleJWT) |
| `/api/token/refresh/` | JWT token refresh |

### Data models (`vendas/models.py`)

- **Cliente** — customer with name and optional WhatsApp number
- **Produto** — product with unit price and stock quantity
- **Venda** — a sale, linked to a `User` (funcionario) and optionally a `Cliente`; stores `total_venda`
- **ItemVenda** — line item in a sale, linked to `Venda` and `Produto`; stores `preco_na_hora` (price at time of sale) and quantity

### Authentication

The app uses a hybrid approach: Django session auth for the template views, and JWT (SimpleJWT) for the REST API. After login, both a session and JWT access/refresh tokens are created. The `/register/` view is protected by `@login_required` + `@user_passes_test(is_admin)` (requires `is_staff=True`).

### Frontend

Templates use Bootstrap 5 (loaded from CDN). `base.html` is the layout template with the navbar; other templates extend it via `{% block content %}`.

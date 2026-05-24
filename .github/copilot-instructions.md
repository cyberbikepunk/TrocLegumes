# TrocLégumes — Copilot Instructions

## Project Overview

TrocLégumes is a Django web app for market gardeners to exchange and sell produce directly.
See `docs/brainstorm.md` for the full spec and `docs/roadmap.md` for the development plan.

## Architecture

- **Apps** live in `apps/` — `accounts` (done), `farms`, `market`, `billing` (Phase 1+)
- **Config** lives in `config/` — split settings: `base.py` / `dev.py` / `prod.py`
- **Templates** live in `templates/<app>/` — all extend `templates/base.html`
- **Static files** — Bootstrap, HTMX and Bootstrap Icons loaded via CDN. No build step.
- All management commands run inside Docker: `docker compose exec web python manage.py ...`

## Language

- **Code** (Python, HTML attributes, URL slugs, git commits, comments, docstrings) → English
- **User-facing text** (template content, form labels, model `verbose_name`, choice display values) → French
- Django i18n (`{% trans %}`, `.po` files) is not used — the app is French-only; hardcode French directly

## Constants

- Never scatter magic values across the codebase — define them once and import them
- **Model field choices** → use `TextChoices` / `IntegerChoices` as inner classes on the model (e.g. `Listing.Status`, `Order.Status`)
- **Business logic thresholds** (expiry delays, limits, amounts) → `apps/<app>/constants.py`
- **Environment-dependent config** (feature flags, third-party settings) → `config/settings/base.py`

## Python & Django Conventions

**Models**
- Never import `User` directly — always use `get_user_model()` or `settings.AUTH_USER_MODEL`
- New apps go in `apps/` and must be added to `LOCAL_APPS` in `config/settings/base.py` using the dotted path (e.g. `apps.farms`)
- Every `AppConfig` must set an explicit `label` to avoid conflicts (e.g. `label = "farms"`)
- Use `class Meta: ordering = [...]` instead of ordering in querysets where it's always needed
- Prefer `select_related` / `prefetch_related` — avoid N+1 queries

**Migrations**
- Always target the app explicitly: `makemigrations accounts` — never bare `makemigrations`
- Never edit a migration file by hand unless fixing a merge conflict
- Squash migrations only after a phase is fully stable

**Views**
- Use Class-Based Views (CBVs) — `LoginRequiredMixin` for protected views
- Return full pages normally; return HTML fragments for HTMX requests (detect with `request.htmx`)
- No raw SQL — ORM only. Use `annotate()` and `aggregate()` for computed values.

**URLs**
- Every app's `urls.py` must declare `app_name` for namespacing
- Use `{% url 'app:name' %}` in templates, never hardcoded paths
- URL slugs are in English (e.g. `login/`, `register/`, `farms/`)

**Forms**
- Add `class="form-control"` (or appropriate Bootstrap class) to all field widgets
- Use `novalidate` on `<form>` tags and rely on Django validation, not browser validation

**Security**
- Every POST form must include `{% csrf_token %}`
- Never use `mark_safe()` on user-supplied content
- No secrets in code — all config via `.env` / `django-environ`

## Frontend Conventions

**HTMX**
- HTMX requests return partial HTML fragments — check `request.htmx` in views
- Use `hx-target` and `hx-swap` explicitly — don't rely on defaults
- Confirm destructive actions with `hx-confirm`

**Bootstrap 5**
- Use Bootstrap utility classes — avoid writing custom CSS for layout or spacing
- Use Bootstrap Icons (`bi bi-*`) for all icons
- Messages → Bootstrap alert classes (already mapped in `base.py` via `MESSAGE_TAGS`)

**Templates**
- All templates must extend `base.html` (or a sub-layout that does)
- Use `{% block content %}` for page content, `{% block title %}` for the page title
- Keep template logic minimal — move business logic to views or model methods

## Testing

**Philosophy**: write tests after the code, not before. Each feature is complete when it works and has tests.

**Stack**: `pytest` + `pytest-django` + `factory_boy`. Run with `make test` (inside Docker).

**What to test:**
- **Models** — custom properties, methods, and any non-trivial constraint
- **Views** — HTTP status codes, login redirects, correct template used, basic form submission
- **Business logic** — billing calculations, balance computation, expiry rules

**What NOT to test:** Django internals, migrations, admin auto-registration, template markup.

**Structure:**
```
apps/<app>/tests/
    __init__.py
    factories.py     # factory_boy factories for this app's models
    test_models.py
    test_views.py
```

**Rules:**
- Every model gets a factory in `factories.py`
- Every view gets at least a smoke test (GET returns 200, unauthenticated redirects to login)
- Complex business logic (tab, balance) gets its own focused test
- Tests must pass before committing (`make test`)

**CI:** GitHub Actions runs `make test` on every push to master — a failing test blocks deployment.

> **Current status:** dev-only, no deployment yet. CI will be wired up before production.

## Logging

- Every module that needs logging declares: `logger = logging.getLogger(__name__)`
- Use the appropriate level: `DEBUG` for traces, `INFO` for business events, `WARNING` for unexpected states, `ERROR`/`exception` for failures
- Log meaningful business events: order created, listing expired, payment failed
- Never use `print()` for diagnostic output — use the logger
- In dev, logs appear in `docker compose logs web`; in prod they will go to Sentry

**Standard log format:** `TIMESTAMP LEVEL    logger funcName():line — message`
```
2026-05-24 01:12:34 INFO     apps.market.views create_order():87 — Order #42 created by user 7
```
- Fields: timestamp (`%Y-%m-%d %H:%M:%S`), level (padded to 8 chars), logger (`__name__`), function, line, message
- Dev output is color-coded by level via `colorlog` (cyan/green/yellow/red)
- Prod uses the same fields without color (plain `standard` formatter)

## Code Review

At the end of each phase, do a full review before moving on. The goal is to catch issues early, not after they compound.

**What to check — in order:**

1. **Models** — field types, `on_delete` choices, `null`/`blank` consistency, `__str__`, `Meta.ordering`, missing `verbose_name` on important fields
2. **Migrations** — one migration per app, no hand-edits, no stale/unapplied migrations (`showmigrations`)
3. **Admin** — every model registered, `list_display` / `search_fields` / `list_filter` set, inlines for related objects where useful, `autocomplete_fields` for FK fields (no raw icon buttons)
4. **Views & URLs** — `app_name` declared, all views covered by a URL, login protection on every non-public view, no hardcoded paths in templates
5. **Templates** — all extend `base.html`, use `{% url %}`, no inline styles, no business logic in templates
6. **Tests** — every model has a factory, every `__str__` and custom method is tested, all views have a smoke test, 0 failures
7. **Lint** — `ruff check .` passes with 0 errors
8. **Security** — `{% csrf_token %}` on every POST form, no `mark_safe()` on user content, no secrets in code
9. **Docker** — `python manage.py check` reports 0 issues, container starts cleanly

**After the review:**
- Fix everything found before starting the next phase
- Run `make test` + `ruff check .` one final time
- Commit as `Phase N: review fixes`

## Git Workflow

- Work directly on `master` — no feature branches
- Commit after every working increment: `git add . && git commit -m "..." && git push`
- Commit messages: `Phase 1: add Farm model and admin`

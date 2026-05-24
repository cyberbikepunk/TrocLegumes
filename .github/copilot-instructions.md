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

- Tests go in `apps/<app>/tests/` — use `pytest` and `factory_boy`
- Run with `make test` (runs inside Docker)
- Every model needs a basic factory; every view needs a smoke test

## Git Workflow

- Branch per feature: `git checkout -b phase-1/farms-model`
- Commit messages: `Phase 1: add Farm model and admin`
- Push after every working increment: `git push`

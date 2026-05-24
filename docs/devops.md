# TrocLégumes — DevOps Flow

Deliberately minimal: no Kubernetes, no staging environment, no container registry needed at this scale.

---

## Local Development

```
docker-compose.yml (dev)
  ├── db         — PostgreSQL
  ├── redis      — for Celery
  └── web        — Django dev server (runserver, hot reload)
```

- Secrets in a `.env` file (never committed)
- `manage.py migrate` and `manage.py seed` run inside the container
- A single `docker compose up` starts everything

---

## Version Control

- Git + GitHub (or GitLab)
- Feature branches → PR → merge to `main`
- `main` is always deployable

---

## CI — GitHub Actions (on every push / PR)

1. Run test suite (`pytest`)
2. Lint + format check (`ruff`)
3. Check for missing migrations (`manage.py migrate --check`)
4. (Optional) build the Docker image to catch dependency errors early

---

## Production Stack

```
docker-compose.yml (prod)
  ├── db         — PostgreSQL (named volume for persistence)
  ├── redis      — Celery broker
  ├── web        — Gunicorn (Django)
  ├── worker     — Celery worker
  ├── beat       — Celery beat (cron jobs)
  └── nginx      — Reverse proxy + serves static/media files
```

SSL via **Certbot + Let's Encrypt**, renewed automatically by a cron on the VPS.

---

## Deploy Script

Run manually or triggered from CI on merge to `main`:

```bash
git pull
docker compose build web
docker compose run --rm web manage.py migrate
docker compose run --rm web manage.py collectstatic --no-input
docker compose up -d
```

---

## Secrets

A single `.env` file on the VPS (outside the repo), injected via `env_file` in `docker-compose.yml`:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `False` in production |
| `DATABASE_URL` | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Domain name(s) |
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials |
| `SENTRY_DSN` | Error tracking (optional) |

---

## Backups

- Daily `pg_dump` cron on the VPS
- Rotated locally (keep last 7 days)
- Optional: sync to object storage (Hetzner Object Storage, Backblaze B2)

---

## Monitoring & Logging

- Django logs → stdout → captured by Docker (`docker compose logs -f web`)
- **Sentry** (free tier) for runtime error tracking — `pip install sentry-sdk` + `SENTRY_DSN` in `.env`

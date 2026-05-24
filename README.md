# TrocLégumes

A web app for market gardeners to exchange and sell produce directly with each other — no middlemen, no invoices, just a shared tab settled at the end of each season.

## Stack

- **Backend** — Django 6 / Python 3.12 / PostgreSQL 16
- **Frontend** — HTMX 2 + Bootstrap 5.3 (no build step)
- **Async** — Celery + Redis (Phase 7)
- **Infrastructure** — Docker Compose (dev), Gunicorn + Nginx (prod)

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose

### Run locally

```bash
# Clone the repo
git clone https://github.com/cyberbikepunk/TrocLegumes.git
cd TrocLegumes

# Copy the environment file and fill in your values
cp .env.example .env

# Start the stack
docker compose up -d

# Apply migrations
docker compose exec web python manage.py migrate

# Create an admin account
docker compose exec web python manage.py createsuperuser
```

Then open http://localhost:8000.

### Useful commands

```bash
make up              # Start containers
make down            # Stop containers
make shell           # Shell inside the web container
make migrate         # Apply pending migrations
make makemigrations  # Generate migrations after editing models
make test            # Run tests (pytest)
make lint            # Run linter (ruff)
```

## Project Structure

See [docs/structure.md](docs/structure.md) for a full breakdown of the codebase.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the 8-phase development plan.

## License

Private project — all rights reserved.

.PHONY: up down build shell migrate makemigrations superuser test lint

up:
	docker compose up

down:
	docker compose down

build:
	docker compose build

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

superuser:
	docker compose exec web python manage.py createsuperuser

test:
	docker compose exec web pytest

lint:
	docker compose exec web ruff check .

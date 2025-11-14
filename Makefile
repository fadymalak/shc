.PHONY: help setup up down migrate createsuperuser shell backend-shell frontend-shell logs

help:
	@echo "Available commands:"
	@echo "  make setup          - Initial setup (copy .env, install dependencies)"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make migrate        - Run database migrations"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make shell          - Open Django shell"
	@echo "  make backend-shell  - Open backend container shell"
	@echo "  make frontend-shell - Open frontend container shell"
	@echo "  make logs           - View logs"

setup:
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "Created backend/.env"; fi
	@echo "Setup complete. Please edit backend/.env with your configuration."

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	docker-compose exec backend python manage.py migrate

createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

shell:
	docker-compose exec backend python manage.py shell

backend-shell:
	docker-compose exec backend bash

frontend-shell:
	docker-compose exec frontend sh

logs:
	docker-compose logs -f

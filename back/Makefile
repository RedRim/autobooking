.PHONY: help up down logs migrate migrations restart

up:
	docker-compose up -d

down:
	docker-compose down

migrations:
	docker-compose exec app alembic revision --autogenerate -m "$(name)"

migrate:
	docker-compose exec app alembic upgrade head

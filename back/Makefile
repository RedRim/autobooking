.PHONY: up build down migrations migrate seed download-dump upload-dump

include .env

DOCKER_COMP  = docker compose
DB_CONT      = $(DOCKER_COMP) exec db
APP_CONT     = $(DOCKER_COMP) exec app

up:
	$(DOCKER_COMP) up -d

build:
	$(DOCKER_COMP) build --pull --no-cache

down:
	$(DOCKER_COMP) down

migrations:
	$(APP_CONT) alembic revision --autogenerate -m "$(name)"

migrate:
	$(APP_CONT) alembic upgrade head

seed:
	$(APP_CONT) python -m scripts.seed

# Выгрузка дампа БД в .sql файл.
# Использование: make download-dump name=dump.sql
download-dump:
	@echo "Dumping database '$(POSTGRES_DB)' to $(name)..."
	@$(DB_CONT) pg_dump -U $(POSTGRES_USER) -d $(POSTGRES_DB) > $(name)
	@echo "Done: $(name)"

# Загрузка дампа из .sql файла в БД.
# Файл должен находиться в текущей директории.
# Использование: make upload-dump name=dump.sql
upload-dump:
	@echo "Recreating database '$(POSTGRES_DB)'..."
	@$(DB_CONT) psql -U $(POSTGRES_USER) -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(POSTGRES_DB)' AND pid <> pg_backend_pid();"
	@$(DB_CONT) psql -U $(POSTGRES_USER) -c "DROP DATABASE IF EXISTS $(POSTGRES_DB);"
	@$(DB_CONT) psql -U $(POSTGRES_USER) -c "CREATE DATABASE $(POSTGRES_DB);"
	@echo "Applying dump from $(name)..."
	@$(DOCKER_COMP) cp $(name) db:/tmp/$(name)
	@$(DB_CONT) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -f /tmp/$(name)
	@echo "Done."

.PHONY: up build down migrations migrate seed seed-docker download-dump upload-dump

include .env

DOCKER_COMP  = docker-compose
APP_CONT     = $(DOCKER_COMP) exec app

# Локальный запуск Python (venv в back/, иначе python3)
export PYTHONPATH := $(CURDIR)
PY := $(if $(wildcard $(CURDIR)/.venv/bin/python),$(CURDIR)/.venv/bin/python,python3)

up:
	@mkdir -p data
	$(DOCKER_COMP) up -d

build:
	$(DOCKER_COMP) build --pull --no-cache

down:
	$(DOCKER_COMP) down

migrations:
	$(APP_CONT) alembic revision --autogenerate -m "$(name)"

migrate:
	$(APP_CONT) alembic upgrade head

# Загрузка демо-данных из dump (см. scripts/seed.py). Нужны миграции и зависимости (pip / venv).
seed:
	$(PY) -m scripts.seed

# То же внутри контейнера app (после make up).
seed-docker:
	$(APP_CONT) python -m scripts.seed

# Выгрузка дампа БД в .sql (формат SQLite .dump).
# Использование: make download-dump name=dump.sql
download-dump:
	@echo "Dumping SQLite '$(SQLITE_PATH)' to $(name)..."
	@$(APP_CONT) sqlite3 $(SQLITE_PATH) .dump > $(name)
	@echo "Done: $(name)"

# Загрузка дампа из .sql в БД (полная перезапись файла).
# Файл должен быть в каталоге back/; имя передать без пути или с путём с хоста.
# Использование: make upload-dump name=dump.sql
upload-dump:
	@echo "Recreating SQLite database from $(name)..."
	@$(DOCKER_COMP) cp $(name) app:/tmp/import_dump.sql
	@$(APP_CONT) sh -c "rm -f $(SQLITE_PATH) && sqlite3 $(SQLITE_PATH) < /tmp/import_dump.sql"
	@echo "Done."

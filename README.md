# Сервис онлайн записи на любые услуги

Чтобы запустить сервис, нужно запустить backend и frontend

## Запуск бэкенда:
1) Перейти в терминале в папку `/back`
2) создать файл `.env` и перенести туда данные из `.env.example`
3) создать каталог для базы: `mkdir -p data`
4) ввести команду `make up`. (Если команды нет, надо установить Docker Compose)

5) применить миграции: `make migrate`

6) (по желанию) загрузить демо-данные из `back/dump`: из каталога `back/` выполнить `make seed` (используется `.venv/bin/python`, если есть). Если всё делаете только через Docker: `make seed-docker` при запущенном `app`. Другой файл дампа: `SEED_DUMP_PATH=/путь/к/дампу make seed`.

Приложение будет доступно на http://localhost:8000. Свагер - http://localhost:8000/docs

База данных — SQLite, файл задаётся переменной `SQLITE_PATH` (по умолчанию `data/autobooking.db`). Откройте файл любым клиентом SQLite (DB Browser for SQLite, `sqlite3` в терминале и т.д.).

### Работа с дампом БД

- Чтобы выгрузить дамп в `.sql`: `make download-dump name=dump.sql`
- Чтобы загрузить дамп из `.sql` (файл в каталоге `back/`): `make upload-dump name=dump.sql`
- креды юзера - `admin@mail.ru`, `admin`
- Креды компаний:
    * `sweet@mail.ru`, `admin` - Уход
    * `barbers@mail.ru`, `admin` - Барбершо
    * `manic@mail.ru`, `admin` - Маникюр

## Запуск фронтенда:
1) Перейти в терминале в папку `/front`
2) Установить зависимости командой `npm install`
3) Чтобы запустить проект `npm run dev`

Приложение будет доступно на http://localhost:5173.

## Прод-развертывание (Docker + Nginx)
1) Проверьте `back/.env` (минимум: `SQLITE_PATH`, `API_KEY`, `PORT`).
2) Из корня проекта запустите:
`docker compose -f docker-compose.prod.yml up -d --build`
3) Примените миграции:
`docker compose -f docker-compose.prod.yml exec back alembic upgrade head`
4) (Опционально) загрузите демо-данные:
`docker compose -f docker-compose.prod.yml exec back python -m scripts.seed`

После запуска:
- фронт и API доступны через один домен/хост;
- запросы фронта к `/api/*` проксируются в FastAPI;
- SPA-маршруты (`/company/...`, `/bookings/...`) работают через fallback на `index.html`.

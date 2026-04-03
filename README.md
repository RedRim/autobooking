# Сервис онлайн записи на любые услуги

Чтобы запустить сервис, нужно запустить backend и frontend

## Запуск бэкенда:
1) Перейти в терминале в папку `/back`
2) создать файл `.env` и перенести туда данные из `.env.example`
3) ввести команду `make up`. (Если команды нет, надо установить)

Приложение будет доступно на http://localhost:8000. Свагер - http://localhost:8000/docs

### Работа с дампом БД

- Чтобы загрузить дамп БД, нужно положить его в папку `/back` (сейчас он там уже лежит) и ввести команду `make upload-dump name={имя_файла}`. Расширение тоже указать, если оно есть
- Чтобы выгрузить дамп, нужно ввести команду `make download-dump name={имя_файла}`
- креды юзера - `admin@mail.ru`, `admin`
- Креды компаний:
    * `sweet@mail.ru`, `admin` - Уход
    * `barbers@mail.ru`, `admin` - Барбершо
    * `manic@mail.ru`, `admin` - Маникюр
- Остальные данные можно посмотреть в pgAdmin например, если зарегать сервер (Servers -> Register -> server):
    * General.Name - любое
    * Connection.host name - `localhost`
    * port - `5432`
    * maintanance - `autobooking`
    * остальное - `postgres`
    * либо смотрите в .env файл

## Запуск фронтенда:
1) Перейти в терминале в папку `/front`
2) Устанвоить зависимости командой `npm install`
3) Чтобы запустить проект `npm run dev`



## Запуск тестов:
тестовая база данных создана
Для начала тестирования введите в консоли следующие команды:

В папке back актиивируем тесты:  python3 -m pytest tests/test_api.py -v


При неудаче: 
    Создание окружения venv: python3 -m venv venv
    Вход в окружение: source venv/bin/activate
    Установка необходимых расширений: 
        pip install -r requirements.txt
    Запyск тестирования из папки back:  python3 -m pytest tests/test_api.py -v



Если не будет работать, то вручную установить следующие библиотеки и повторить заново:
pytest==8.0.0
pytest-asyncio==0.23.5
httpx==0.27.0
, а именно:
pip install -r requirements.txt

Приложение будет доступно на http://localhost:5173.

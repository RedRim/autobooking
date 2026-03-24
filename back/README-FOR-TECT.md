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
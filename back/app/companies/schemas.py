from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel


class WorkingHoursCreate(BaseModel):
    """
    Тело запроса для создания или обновления рабочих часов одного дня.

    Используется в PUT /owner/company/{id}/schedule.

    Поля:
        day_of_week — день недели (0 = Пн, 1 = Вт, …, 6 = Вс).
        start_time  — время начала работы в формате HH:MM:SS, например «09:00:00».
        end_time    — время окончания работы в формате HH:MM:SS, например «18:00:00».
        is_working  — если False, день считается выходным и слоты не выдаются.

    Пример тела запроса:
        {
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "is_working": true
        }
    """

    day_of_week: int  # 0=Пн, 6=Вс
    start_time: time
    end_time: time
    is_working: bool = True


class WorkingHoursResponse(WorkingHoursCreate):
    """
    Ответ API с данными рабочих часов одного дня.

    Расширяет WorkingHoursCreate полями id и company_id из базы данных.
    """

    id: int
    company_id: int

    model_config = {"from_attributes": True}


class ServiceCreate(BaseModel):
    """
    Тело запроса для создания новой услуги.

    Используется в POST /owner/company/{id}/services.

    Поля:
        name                — название услуги, например «Мужская стрижка».
        description         — описание услуги для клиента.
        price               — стоимость в рублях; если None — цена не указана.
        duration_minutes    — длительность сеанса в минутах, определяет размер
                              временно́го слота при генерации расписания.
        is_active           — False скрывает услугу из публичного списка.

    Пример тела запроса:
        {
            "name": "Мужская стрижка",
            "description": "Стрижка машинкой или ножницами",
            "price": 1200.00,
            "duration_minutes": 45,
            "is_active": true
        }
    """

    name: str
    description: str | None = None
    price: Decimal | None = None
    duration_minutes: int
    is_active: bool = True


class ServiceUpdate(BaseModel):
    """
    Тело запроса для частичного обновления услуги (PATCH-семантика).

    Используется в PUT /owner/services/{id}.
    Все поля необязательны — передаётся только то, что нужно изменить.

    Пример — изменить только цену:
        {
            "price": 1500.00
        }
    """

    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    duration_minutes: int | None = None
    is_active: bool | None = None


class ServiceResponse(BaseModel):
    """
    Ответ API с полными данными об услуге.

    Возвращается при создании, обновлении и в списке услуг компании.
    """

    id: int
    company_id: int
    name: str
    description: str | None
    price: Decimal | None
    duration_minutes: int
    is_active: bool

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    """
    Тело запроса для регистрации новой компании.

    Используется в POST /owner/company.
    Доступно только пользователям с ролью 'company'.

    Поля:
        name        — публичное название компании.
        description — описание деятельности.
        category    — тип бизнеса, используется для фильтрации в поиске.
        city        — город; используется для фильтрации в поиске.
        address     — точный адрес.
        phone       — телефон для связи.

    Пример тела запроса:
        {
            "name": "Барбершоп Топор",
            "description": "Мужские стрижки и уход за бородой",
            "category": "Барбершоп",
            "city": "Москва",
            "address": "ул. Арбат, 10",
            "phone": "+7 999 123-45-67"
        }
    """

    name: str
    description: str | None = None
    category: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None


class CompanyUpdate(BaseModel):
    """
    Тело запроса для обновления данных компании (PATCH-семантика).

    Используется в PUT /owner/company/{id}.
    Все поля необязательны — передаётся только то, что нужно изменить.

    Пример — деактивировать компанию:
        {
            "is_active": false
        }
    """

    name: str | None = None
    description: str | None = None
    category: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class CompanyShortResponse(BaseModel):
    """
    Краткая карточка компании для списка (результаты поиска).

    Используется в GET /companies. Не включает услуги и расписание
    во избежание лишних JOIN при отображении большого числа карточек.
    """

    id: int
    name: str
    category: str | None
    city: str | None
    address: str | None
    phone: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class CompanyResponse(BaseModel):
    """
    Полная карточка компании с услугами и расписанием.

    Используется в GET /companies/{id} и при создании/обновлении компании.
    Включает вложенные списки services и working_hours.
    """

    id: int
    owner_id: int
    name: str
    description: str | None
    category: str | None
    city: str | None
    address: str | None
    phone: str | None
    is_active: bool
    created_at: datetime
    services: list[ServiceResponse] = []
    working_hours: list[WorkingHoursResponse] = []

    model_config = {"from_attributes": True}

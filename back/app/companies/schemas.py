from datetime import datetime, time
from decimal import Decimal
import re
from typing import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator
from pydantic_core import PydanticCustomError

from app.companies.models import CompanyRequestStatus


def _parse_ru_phone(value: str) -> str:
    cleaned = re.sub(r"\D", "", str(value))
    if cleaned.startswith("8"):
        cleaned = "7" + cleaned[1:]
    if len(cleaned) != 11 or not cleaned.startswith("7"):
        raise PydanticCustomError(
            "ru_phone",
            "Неверный формат телефона. Верный формат: +7/8 и 10 цифр",
        )
    return f"+7{cleaned[1:]}"


RuPhone = Annotated[str, BeforeValidator(_parse_ru_phone)]


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
    Тело запроса для создания заявки на новую компанию.

    Используется в POST /owner/company-request.
    Доступно только пользователям с ролью 'company'.

    Поля:
        name        — публичное название компании.
        category    — текст категории от пользователя (может быть новой категорией).
        city        — город; используется для фильтрации в поиске.

    Пример тела запроса:
        {
            "name": "Барбершоп Топор",
            "category": "Барбершоп",
            "city": "Москва"
        }
    """

    name: str
    category: str
    city: str
    phone: RuPhone


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


class CategoryResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CityResponse(BaseModel):
    name: str


class CompanyRequestUpdate(BaseModel):
    city: str | None = None
    category: str | None = None
    phone: RuPhone | None = None


class CompanyRequestResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    requested_category: str
    city: str
    phone: str | None
    status: CompanyRequestStatus
    approved_by_id: int | None
    approved_at: datetime | None
    company_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

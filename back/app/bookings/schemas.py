from datetime import date, datetime

from pydantic import BaseModel

from app.bookings.models import BookingStatus

WEEKDAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


class BookingCreate(BaseModel):
    """
    Тело запроса для создания записи на услугу.

    Используется в POST /bookings.
    end_at вычисляется автоматически: start_at + duration_minutes услуги.
    Перед сохранением система проверяет, что слот не занят другой активной записью.

    Поля:
        service_id  — ID услуги, на которую записывается пользователь.
        start_at    — желаемое UTC-время начала сеанса.
                      Должно совпадать с одним из слотов из GET /services/{id}/slots.
        notes       — необязательная заметка для мастера, например «левша» или «аллергия».

    Пример тела запроса:
        {
            "service_id": 3,
            "start_at": "2026-03-10T10:00:00Z",
            "notes": "Хочу покороче на висках"
        }
    """

    service_id: int
    start_at: datetime
    notes: str | None = None


class BookingResponse(BaseModel):
    """
    Ответ API с полными данными о записи.

    Возвращается при создании, отмене и подтверждении записи,
    а также в списках GET /bookings/my и GET /owner/company/{id}/bookings.

    Поля:
        id          — уникальный ID записи.
    user_id     — ID клиента.
    user_full_name — ФИО клиента для отображения в интерфейсе компании.
        service_id  — ID услуги.
        company_id  — ID компании (для быстрой фильтрации).
        start_at    — UTC-время начала сеанса.
        end_at      — UTC-время окончания сеанса (start_at + duration_minutes).
        status      — текущий статус: pending / confirmed / cancelled.
        notes       — заметка клиента.
        created_at  — UTC-время создания записи.
    """

    id: int
    user_id: int
    user_full_name: str | None = None
    service_id: int
    company_id: int
    start_at: datetime
    end_at: datetime
    status: BookingStatus
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TimeSlot(BaseModel):
    """
    Один свободный временно́й слот для записи на услугу.

    Возвращается в списке из GET /services/{id}/slots?date=YYYY-MM-DD.
    Клиент выбирает подходящий слот и передаёт start_at в POST /bookings.

    Поля:
        start_at — UTC-время начала слота.
        end_at   — UTC-время окончания слота (start_at + duration_minutes услуги).

    Пример одного слота в ответе:
        {
            "start_at": "2026-03-10T09:00:00+00:00",
            "end_at":   "2026-03-10T10:00:00+00:00"
        }
    """

    start_at: datetime
    end_at: datetime


# ── Календарная сетка на 2 недели ─────────────────────────────────────────────

class CalendarSlot(BaseModel):
    """
    Один слот в двухнедельном календаре услуги.

    Поля:
        start_at        — UTC-время начала слота.
        end_at          — UTC-время окончания слота.
        is_available    — True, если слот свободен и находится в будущем.
    """

    start_at: datetime
    end_at: datetime
    is_available: bool


class CalendarDay(BaseModel):
    """
    Один день в двухнедельном календаре услуги.

    Поля:
        date        — дата дня.
        weekday     — номер дня недели (0 = Пн, …, 6 = Вс).
        weekday_name — название дня на русском, например «Понедельник».
        is_working  — False, если компания не работает в этот день.
        slots       — список всех слотов дня (свободных и занятых).
                      Пустой список, если is_working = False.
    """

    date: date
    weekday: int
    weekday_name: str
    is_working: bool
    slots: list[CalendarSlot] = []


class ServiceCalendarResponse(BaseModel):
    """
    Двухнедельный календарь для конкретной услуги.

    Используется для отрисовки UI-календаря на клиентской стороне.
    Период всегда начинается с понедельника текущей недели
    и охватывает 14 дней (2 полные недели).

    Поля:
        service_id          — ID услуги.
        service_name        — название услуги.
        duration_minutes    — длительность одного сеанса в минутах.
        period_start        — дата начала периода (Пн текущей недели).
        period_end          — дата конца периода (Вс следующей недели включительно).
        days                — список из 14 объектов CalendarDay.

    Пример ответа (сокращённо):
        {
            "service_id": 3,
            "service_name": "Мужская стрижка",
            "duration_minutes": 45,
            "period_start": "2026-03-09",
            "period_end": "2026-03-22",
            "days": [
                {
                    "date": "2026-03-09",
                    "weekday": 0,
                    "weekday_name": "Понедельник",
                    "is_working": true,
                    "slots": [
                        {"start_at": "...", "end_at": "...", "is_available": true},
                        {"start_at": "...", "end_at": "...", "is_available": false}
                    ]
                },
                ...
            ]
        }
    """

    service_id: int
    service_name: str
    duration_minutes: int
    period_start: date
    period_end: date
    days: list[CalendarDay]

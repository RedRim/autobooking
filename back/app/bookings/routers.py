from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.services import get_current_user
from app.bookings import services as svc
from app.bookings.schemas import BookingCreate, BookingResponse, ServiceCalendarResponse, TimeSlot
from app.database import get_session

router = APIRouter(tags=["bookings"])


# ── Слоты и календарь (публично) ─────────────────────────────────────────────

@router.get("/services/{service_id}/calendar", response_model=ServiceCalendarResponse)
async def get_service_calendar(
    service_id: int,
    session: AsyncSession = Depends(get_session),
) -> ServiceCalendarResponse:
    """
    Двухнедельный календарь слотов для конкретной услуги.

    Возвращает сетку на 14 дней, начиная с понедельника текущей недели.
    Каждый слот помечен как доступный или занятый (is_available).
    Прошедшие слоты всегда недоступны.

    Авторизация не требуется. Используется для отрисовки UI-календаря.

    Пример:
        GET /services/3/calendar

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
                        {"start_at": "2026-03-09T09:00:00Z", "end_at": "2026-03-09T09:45:00Z", "is_available": false},
                        {"start_at": "2026-03-09T09:45:00Z", "end_at": "2026-03-09T10:30:00Z", "is_available": true}
                    ]
                },
                {
                    "date": "2026-03-15",
                    "weekday": 6,
                    "weekday_name": "Воскресенье",
                    "is_working": false,
                    "slots": []
                }
            ]
        }
    """
    return await svc.get_service_calendar(service_id, session)


@router.get("/services/{service_id}/slots", response_model=list[TimeSlot])
async def get_available_slots(
    service_id: int,
    date: date = Query(..., description="Дата в формате YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
) -> list[TimeSlot]:
    """
    Возвращает список свободных временны́х слотов для услуги на указанную дату.

    Авторизация не требуется. Используется для отображения календаря на клиентской стороне.

    Алгоритм:
    1. Берёт рабочие часы компании для дня недели указанной даты.
    2. Нарезает рабочий день на слоты по duration_minutes услуги.
    3. Исключает слоты, на которые уже есть активные записи.

    Пример:
        GET /services/3/slots?date=2026-03-10

    Пример ответа (услуга 60 мин, компания работает с 9:00 до 12:00,
    слот 09:00–10:00 уже занят):
        [
            {"start_at": "2026-03-10T10:00:00+00:00", "end_at": "2026-03-10T11:00:00+00:00"},
            {"start_at": "2026-03-10T11:00:00+00:00", "end_at": "2026-03-10T12:00:00+00:00"}
        ]
    """
    return await svc.get_available_slots(service_id, date, session)


# ── Записи (для пользователя) ────────────────────────────────────────────────

@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> BookingResponse:
    """
    Создаёт запись пользователя на услугу в выбранное время.

    Требует авторизацию. start_at должен совпадать с одним из свободных слотов
    из GET /services/{id}/slots. Система повторно проверяет занятость слота
    в момент записи (защита от гонки).

    Созданная запись получает статус 'pending'.

    Пример тела запроса:
        {
            "service_id": 3,
            "start_at": "2026-03-10T10:00:00Z",
            "notes": "Хочу покороче на висках"
        }
    """
    return await svc.create_booking(data, user, session)


@router.get("/bookings/my", response_model=list[BookingResponse])
async def my_bookings(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[BookingResponse]:
    """
    Возвращает все записи текущего пользователя, отсортированные по дате (новые первые).

    Требует авторизацию. Включает записи во всех статусах.
    Используется для отображения истории и предстоящих визитов.

    Пример:
        GET /bookings/my
        Authorization: Bearer <token>
    """
    return await svc.get_user_bookings(user, session)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> BookingResponse:
    """
    Отменяет запись пользователя (переводит статус в 'cancelled').

    Требует авторизацию. Отменить можно только свою запись.
    После отмены слот освобождается и становится доступным для других.

    Пример:
        POST /bookings/42/cancel
        Authorization: Bearer <token>
    """
    return await svc.cancel_booking(booking_id, user, session)


# ── Записи (для владельца компании) ─────────────────────────────────────────

@router.get("/owner/company/{company_id}/bookings", response_model=list[BookingResponse])
async def company_bookings(
    company_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[BookingResponse]:
    """
    Возвращает все записи к компании, отсортированные по дате (новые первые).

    Требует авторизацию; пользователь должен быть владельцем компании.
    Используется в панели управления для просмотра всех входящих заявок.

    Пример:
        GET /owner/company/5/bookings
        Authorization: Bearer <token>
    """
    return await svc.get_company_bookings(company_id, user, session)


@router.post("/owner/bookings/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> BookingResponse:
    """
    Подтверждает запись клиента (переводит статус с 'pending' в 'confirmed').

    Требует авторизацию; пользователь должен быть владельцем компании,
    к которой относится запись. Подтвердить можно только запись в статусе 'pending'.

    Пример:
        POST /owner/bookings/42/confirm
        Authorization: Bearer <token>
    """
    return await svc.confirm_booking(booking_id, user, session)


@router.post("/owner/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking_by_owner(
    booking_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> BookingResponse:
    """
    Отменяет запись клиента владельцем компании (переводит статус в 'cancelled').

    Требует авторизацию; пользователь должен быть владельцем компании,
    к которой относится запись.
    """
    return await svc.cancel_booking_by_owner(booking_id, user, session)

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.bookings.models import Booking, BookingStatus
from app.bookings.schemas import (
    BookingCreate,
    CalendarDay,
    CalendarSlot,
    ServiceCalendarResponse,
    TimeSlot,
    WEEKDAY_NAMES,
)
from app.companies.models import Service, WorkingHours


TZ_IRKUTSK = ZoneInfo("Asia/Irkutsk")


async def get_available_slots(
    service_id: int, target_date: date, session: AsyncSession
) -> list[TimeSlot]:
    """
    Возвращает список свободных временны́х слотов для услуги на указанную дату.

    Алгоритм:
    1. Получить услугу и её duration_minutes.
    2. Найти рабочие часы компании для дня недели указанной даты.
    3. Нарезать рабочий день на слоты размером duration_minutes.
    4. Вычесть из них уже занятые слоты (активные записи на эту услугу).
    5. Вернуть оставшиеся свободные слоты.

    Все временны́е метки возвращаются в часовом поясе Иркутска (Asia/Irkutsk, +08:00).

    Args:
        service_id:  ID услуги.
        target_date: дата, для которой запрашиваются слоты.
        session:     сессия БД.

    Returns:
        Список объектов TimeSlot (start_at, end_at).
        Пустой список, если день выходной или расписание не настроено.

    Raises:
        HTTPException 404: если услуга не найдена или деактивирована.

    Пример запроса:
        GET /services/3/slots?date=2026-03-10

    Пример ответа (услуга 45 мин, компания работает с 9:00 до 11:30):
        [
            {"start_at": "2026-03-10T09:00:00Z", "end_at": "2026-03-10T09:45:00Z"},
            {"start_at": "2026-03-10T09:45:00Z", "end_at": "2026-03-10T10:30:00Z"},
            {"start_at": "2026-03-10T10:30:00Z", "end_at": "2026-03-10T11:15:00Z"}
        ]
    """
    service = await session.get(Service, service_id)
    if not service or not service.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")

    day_of_week = target_date.weekday()  # 0=Пн, 6=Вс
    wh = await session.scalar(
        select(WorkingHours).where(
            WorkingHours.company_id == service.company_id,
            WorkingHours.day_of_week == day_of_week,
            WorkingHours.is_working.is_(True),
        )
    )
    if not wh:
        return []

    slot_duration = timedelta(minutes=service.duration_minutes)
    tz = TZ_IRKUTSK
    day_start = datetime.combine(target_date, wh.start_time, tzinfo=tz)
    day_end = datetime.combine(target_date, wh.end_time, tzinfo=tz)

    existing = await session.scalars(
        select(Booking).where(
            and_(
                Booking.service_id == service_id,
                Booking.start_at >= day_start,
                Booking.end_at <= day_end,
                Booking.status != BookingStatus.cancelled,
            )
        )
    )
    booked = [(b.start_at, b.end_at) for b in existing.all()]

    slots: list[TimeSlot] = []
    current = day_start
    while current + slot_duration <= day_end:
        slot_end = current + slot_duration
        overlaps = any(s < slot_end and e > current for s, e in booked)
        if not overlaps:
            slots.append(TimeSlot(start_at=current, end_at=slot_end))
        current += slot_duration

    return slots


async def create_booking(data: BookingCreate, user: User, session: AsyncSession) -> Booking:
    """
    Создаёт запись пользователя на услугу в указанное время.

    Перед сохранением:
    - Проверяет существование и активность услуги.
    - Вычисляет end_at = start_at + duration_minutes.
    - Проверяет отсутствие конфликтующих активных записей на этот слот.

    Args:
        data:    тело запроса: service_id, start_at, notes.
        user:    текущий аутентифицированный пользователь (клиент).
        session: сессия БД.

    Returns:
        Созданный объект Booking со статусом 'pending'.

    Raises:
        HTTPException 404: если услуга не найдена или деактивирована.
        HTTPException 409: если выбранный слот уже занят другой активной записью.

    Пример тела запроса:
        {
            "service_id": 3,
            "start_at": "2026-03-10T10:00:00Z",
            "notes": "Хочу покороче на висках"
        }
    """
    service = await session.get(Service, data.service_id)
    if not service or not service.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")

    end_at = data.start_at + timedelta(minutes=service.duration_minutes)

    conflict = await session.scalar(
        select(Booking).where(
            and_(
                Booking.service_id == data.service_id,
                Booking.status != BookingStatus.cancelled,
                Booking.start_at < end_at,
                Booking.end_at > data.start_at,
            )
        )
    )
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Выбранное время уже занято")

    booking = Booking(
        user_id=user.id,
        service_id=data.service_id,
        company_id=service.company_id,
        start_at=data.start_at,
        end_at=end_at,
        notes=data.notes,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


async def get_user_bookings(user: User, session: AsyncSession) -> list[Booking]:
    """
    Возвращает все записи текущего пользователя, отсортированные по дате (новые первые).

    Включает записи во всех статусах: pending, confirmed, cancelled.

    Args:
        user:    текущий аутентифицированный пользователь.
        session: сессия БД.

    Returns:
        Список объектов Booking.
    """
    result = await session.scalars(
        select(Booking).where(Booking.user_id == user.id).order_by(Booking.start_at.desc())
    )
    return list(result.all())


async def cancel_booking(booking_id: int, user: User, session: AsyncSession) -> Booking:
    """
    Отменяет запись пользователя (переводит статус в 'cancelled').

    Отменить можно только свою запись и только если она ещё не отменена.

    Args:
        booking_id: ID записи для отмены.
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Returns:
        Обновлённый объект Booking со статусом 'cancelled'.

    Raises:
        HTTPException 404: если запись не найдена.
        HTTPException 403: если запись принадлежит другому пользователю.
        HTTPException 400: если запись уже отменена.
    """
    booking = await session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    if booking.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    if booking.status == BookingStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Запись уже отменена")
    booking.status = BookingStatus.cancelled
    await session.commit()
    await session.refresh(booking)
    return booking


async def confirm_booking(booking_id: int, user: User, session: AsyncSession) -> Booking:
    """
    Подтверждает запись клиента (переводит статус с 'pending' в 'confirmed').

    Доступно только владельцу компании, к которой относится запись.
    Подтвердить можно только запись в статусе 'pending'.

    Args:
        booking_id: ID записи для подтверждения.
        user:       текущий аутентифицированный пользователь (владелец компании).
        session:    сессия БД.

    Returns:
        Обновлённый объект Booking со статусом 'confirmed'.

    Raises:
        HTTPException 404: если запись не найдена.
        HTTPException 403: если пользователь не является владельцем компании.
        HTTPException 400: если запись не в статусе 'pending'.
    """
    from app.companies.models import Company

    booking = await session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    company = await session.get(Company, booking.company_id)
    if not company or company.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя подтвердить запись со статусом '{booking.status}'",
        )
    booking.status = BookingStatus.confirmed
    await session.commit()
    await session.refresh(booking)
    return booking


async def get_service_calendar(
    service_id: int, session: AsyncSession
) -> ServiceCalendarResponse:
    """
    Возвращает двухнедельный календарь слотов для конкретной услуги.

    Период: 14 дней, начиная с понедельника текущей недели (Asia/Irkutsk, +08:00).
    Для каждого дня генерируются все слоты (занятые и свободные).

    Алгоритм:
    1. Вычислить понедельник текущей недели как начало периода.
    2. Загрузить расписание компании (WorkingHours) за один запрос.
    3. Загрузить все активные бронирования услуги на весь период за один запрос.
    4. Для каждого из 14 дней:
       a. Найти WorkingHours по day_of_week.
       b. Если выходной или расписание не настроено → is_working=False, slots=[].
       c. Нарезать рабочий день на слоты по duration_minutes.
       d. Пометить каждый слот: занят ли он или уже прошёл (is_available=False).

    Args:
        service_id: ID услуги.
        session:    сессия БД.

    Returns:
        ServiceCalendarResponse с 14 объектами CalendarDay.

    Raises:
        HTTPException 404: если услуга не найдена или деактивирована.

    Пример запроса:
        GET /services/3/calendar
    """
    service = await session.get(Service, service_id)
    if not service or not service.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")

    now = datetime.now(TZ_IRKUTSK)
    today = now.date()
    # Понедельник текущей недели
    period_start = today - timedelta(days=today.weekday())
    period_end = period_start + timedelta(days=13)  # включительно

    tz = TZ_IRKUTSK
    range_start = datetime.combine(period_start, time.min, tzinfo=tz)
    range_end = datetime.combine(period_end, time.max, tzinfo=tz)

    # Расписание компании — один запрос, индексируем по day_of_week
    wh_rows = await session.scalars(
        select(WorkingHours).where(WorkingHours.company_id == service.company_id)
    )
    schedule: dict[int, WorkingHours] = {wh.day_of_week: wh for wh in wh_rows.all()}

    # Все активные бронирования услуги на период — один запрос
    booking_rows = await session.scalars(
        select(Booking).where(
            and_(
                Booking.service_id == service_id,
                Booking.start_at >= range_start,
                Booking.start_at <= range_end,
                Booking.status != BookingStatus.cancelled,
            )
        )
    )
    booked_intervals = [(b.start_at, b.end_at) for b in booking_rows.all()]

    slot_duration = timedelta(minutes=service.duration_minutes)
    days: list[CalendarDay] = []

    for offset in range(14):
        current_date = period_start + timedelta(days=offset)
        weekday = current_date.weekday()
        wh = schedule.get(weekday)

        if not wh or not wh.is_working:
            days.append(CalendarDay(
                date=current_date,
                weekday=weekday,
                weekday_name=WEEKDAY_NAMES[weekday],
                is_working=False,
            ))
            continue

        day_start = datetime.combine(current_date, wh.start_time, tzinfo=tz)
        day_end = datetime.combine(current_date, wh.end_time, tzinfo=tz)

        slots: list[CalendarSlot] = []
        cursor = day_start
        while cursor + slot_duration <= day_end:
            slot_end = cursor + slot_duration
            is_past = slot_end <= now
            is_booked = any(s < slot_end and e > cursor for s, e in booked_intervals)
            slots.append(CalendarSlot(
                start_at=cursor,
                end_at=slot_end,
                is_available=not is_past and not is_booked,
            ))
            cursor += slot_duration

        days.append(CalendarDay(
            date=current_date,
            weekday=weekday,
            weekday_name=WEEKDAY_NAMES[weekday],
            is_working=True,
            slots=slots,
        ))

    return ServiceCalendarResponse(
        service_id=service.id,
        service_name=service.name,
        duration_minutes=service.duration_minutes,
        period_start=period_start,
        period_end=period_end,
        days=days,
    )


async def get_company_bookings(company_id: int, user: User, session: AsyncSession) -> list[Booking]:
    """
    Возвращает все записи к компании, отсортированные по дате (новые первые).

    Доступно только владельцу компании.
    Включает записи во всех статусах: pending, confirmed, cancelled.

    Args:
        company_id: ID компании.
        user:       текущий аутентифицированный пользователь (владелец компании).
        session:    сессия БД.

    Returns:
        Список объектов Booking.

    Raises:
        HTTPException 404: если компания не найдена.
        HTTPException 403: если пользователь не является владельцем компании.
    """
    from app.companies.models import Company

    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    if company.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    result = await session.scalars(
        select(Booking).where(Booking.company_id == company_id).order_by(Booking.start_at.desc())
    )
    return list(result.all())

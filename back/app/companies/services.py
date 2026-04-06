from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.companies.models import Company, Service, WorkingHours
from app.companies.schemas import CompanyCreate, CompanyUpdate, ServiceCreate, ServiceUpdate, WorkingHoursCreate


def require_company_role(user: User) -> None:
    """
    Проверяет, что пользователь имеет роль 'company'.

    Используется как guard перед любым действием, доступным только владельцам компаний.
    Вызывает HTTP 403, если роль не совпадает.

    Args:
        user: текущий аутентифицированный пользователь.

    Raises:
        HTTPException 403: если user.role != UserRole.company.
    """
    if user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только для владельцев компаний",
        )


async def get_company_or_404(company_id: int, session: AsyncSession) -> Company:
    """
    Возвращает компанию по ID или вызывает HTTP 404.

    Используется как базовый хелпер во всех эндпоинтах, работающих с конкретной компанией.

    Args:
        company_id: первичный ключ компании.
        session:    сессия БД.

    Returns:
        Объект Company (с вложенными services и working_hours, т.к. lazy='selectin').

    Raises:
        HTTPException 404: если компания с таким ID не существует.
    """
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return company


async def require_company_owner(company_id: int, user: User, session: AsyncSession) -> Company:
    """
    Возвращает компанию и проверяет, что текущий пользователь является её владельцем.

    Комбинирует get_company_or_404 с проверкой owner_id.
    Используется перед любым изменением данных компании/услуг/расписания.

    Args:
        company_id: первичный ключ компании.
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Returns:
        Объект Company, если пользователь — владелец.

    Raises:
        HTTPException 404: если компания не найдена.
        HTTPException 403: если user.id != company.owner_id.
    """
    company = await get_company_or_404(company_id, session)
    if company.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой компании")
    return company


async def list_companies(
    session: AsyncSession,
    search: str | None,
    category: str | None,
    city: str | None,
) -> list[Company]:
    """
    Возвращает список активных компаний с опциональной фильтрацией.

    Все три параметра можно комбинировать.
    Поиск по названию и городу регистронезависимый (ILIKE).

    Args:
        session:  сессия БД.
        search:   подстрока для поиска в названии компании, например «барбер».
        category: точное совпадение категории, например «Барбершоп».
        city:     подстрока для поиска в поле city, например «моск».

    Returns:
        Список объектов Company, удовлетворяющих фильтрам, с is_active=True.

    Пример запроса:
        GET /companies?search=барбер&city=Москва
    """
    q = select(Company).where(Company.is_active.is_(True))
    if search:
        q = q.where(Company.name.ilike(f"%{search}%"))
    if category:
        q = q.where(Company.name.ilike(f"%{category}%"))
    if city:
        q = q.where(Company.city.ilike(f"%{city}%"))
    result = await session.scalars(q)
    return list(result.all())


async def create_company(data: CompanyCreate, user: User, session: AsyncSession) -> Company:
    """
    Создаёт новую компанию, привязанную к текущему пользователю.

    Требует роль 'company'. Компания создаётся активной по умолчанию.

    Args:
        data:    данные из тела запроса (CompanyCreate).
        user:    текущий аутентифицированный пользователь-владелец.
        session: сессия БД.

    Returns:
        Созданный объект Company.

    Raises:
        HTTPException 403: если пользователь не имеет роль 'company'.
    """
    require_company_role(user)
    company = Company(owner_id=user.id, **data.model_dump())
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def update_company(
    company_id: int, data: CompanyUpdate, user: User, session: AsyncSession
) -> Company:
    """
    Обновляет поля компании. Изменяются только переданные поля (exclude_none).

    Args:
        company_id: ID компании для обновления.
        data:       поля для изменения (все необязательны).
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Returns:
        Обновлённый объект Company.

    Raises:
        HTTPException 404: если компания не найдена.
        HTTPException 403: если пользователь не владелец.
    """
    company = await require_company_owner(company_id, user, session)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    await session.commit()
    await session.refresh(company)
    return company


async def get_my_company(user: User, session: AsyncSession) -> Company:
    """
    Возвращает компанию, зарегистрированную текущим владельцем.

    Требует роль 'company'. Используется на странице управления компанией.

    Args:
        user:    текущий аутентифицированный пользователь.
        session: сессия БД.

    Returns:
        Объект Company владельца.

    Raises:
        HTTPException 403: если пользователь не имеет роль 'company'.
        HTTPException 404: если пользователь ещё не зарегистрировал компанию.
    """
    require_company_role(user)
    company = await session.scalar(select(Company).where(Company.owner_id == user.id))
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return company


async def create_service(
    company_id: int, data: ServiceCreate, user: User, session: AsyncSession
) -> Service:
    """
    Добавляет новую услугу в каталог компании.

    Проверяет, что пользователь является владельцем компании.

    Args:
        company_id: ID компании, к которой добавляется услуга.
        data:       данные новой услуги (название, цена, длительность и т.д.).
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Returns:
        Созданный объект Service.

    Raises:
        HTTPException 404: если компания не найдена.
        HTTPException 403: если пользователь не владелец компании.

    Пример:
        POST /owner/company/5/services
        Body: {"name": "Стрижка", "price": 1200, "duration_minutes": 45}
    """
    await require_company_owner(company_id, user, session)
    service = Service(company_id=company_id, **data.model_dump())
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def update_service(
    service_id: int, data: ServiceUpdate, user: User, session: AsyncSession
) -> Service:
    """
    Обновляет поля услуги. Изменяются только переданные поля (exclude_none).

    Перед изменением проверяет, что пользователь владеет компанией,
    которой принадлежит услуга.

    Args:
        service_id: ID услуги для обновления.
        data:       поля для изменения.
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Returns:
        Обновлённый объект Service.

    Raises:
        HTTPException 404: если услуга не найдена.
        HTTPException 403: если пользователь не владелец компании.
    """
    service = await session.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
    await require_company_owner(service.company_id, user, session)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(service, field, value)
    await session.commit()
    await session.refresh(service)
    return service


async def delete_service(service_id: int, user: User, session: AsyncSession) -> None:
    """
    Удаляет услугу из каталога компании.

    Полное удаление из БД. Все связанные записи (bookings) будут удалены каскадно.
    Альтернативно можно деактивировать услугу через update_service(is_active=False).

    Args:
        service_id: ID услуги для удаления.
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Raises:
        HTTPException 404: если услуга не найдена.
        HTTPException 403: если пользователь не владелец компании.
    """
    service = await session.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
    await require_company_owner(service.company_id, user, session)
    await session.delete(service)
    await session.commit()


async def upsert_working_hours(
    company_id: int, data: WorkingHoursCreate, user: User, session: AsyncSession
) -> WorkingHours:
    """
    Создаёт или обновляет рабочие часы для конкретного дня недели (upsert).

    Если запись для данного company_id + day_of_week уже существует — обновляет её.
    Если нет — создаёт новую. Уникальность гарантируется constraint'ом в БД.

    Args:
        company_id: ID компании.
        data:       день недели, начало и конец рабочего дня, флаг is_working.
        user:       текущий аутентифицированный пользователь.
        session:    сессия БД.

    Returns:
        Созданный или обновлённый объект WorkingHours.

    Raises:
        HTTPException 404: если компания не найдена.
        HTTPException 403: если пользователь не владелец компании.

    Пример — установить понедельник с 9 до 18:
        PUT /owner/company/5/schedule
        Body: {"day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00"}

    Пример — отметить воскресенье как выходной:
        PUT /owner/company/5/schedule
        Body: {"day_of_week": 6, "start_time": "00:00:00", "end_time": "00:00:00", "is_working": false}
    """
    await require_company_owner(company_id, user, session)
    existing = await session.scalar(
        select(WorkingHours).where(
            WorkingHours.company_id == company_id,
            WorkingHours.day_of_week == data.day_of_week,
        )
    )
    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        await session.commit()
        await session.refresh(existing)
        return existing
    wh = WorkingHours(company_id=company_id, **data.model_dump())
    session.add(wh)
    await session.commit()
    await session.refresh(wh)
    return wh


async def delete_working_hours(
    company_id: int, day_of_week: int, user: User, session: AsyncSession
) -> None:
    """
    Удаляет настройку рабочих часов для конкретного дня недели.

    После удаления день считается «не настроенным»: слоты для него не генерируются.
    Чтобы просто закрыть день, удобнее использовать upsert с is_working=False.

    Args:
        company_id:  ID компании.
        day_of_week: день недели для удаления (0–6).
        user:        текущий аутентифицированный пользователь.
        session:     сессия БД.

    Raises:
        HTTPException 404: если компания не найдена, или настройка для этого дня отсутствует.
        HTTPException 403: если пользователь не владелец компании.
    """
    await require_company_owner(company_id, user, session)
    wh = await session.scalar(
        select(WorkingHours).where(
            WorkingHours.company_id == company_id,
            WorkingHours.day_of_week == day_of_week,
        )
    )
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Расписание для этого дня не найдено")
    await session.delete(wh)
    await session.commit()

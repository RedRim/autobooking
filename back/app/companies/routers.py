from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.services import get_current_user
from app.companies import services as svc
from app.companies.schemas import (
    CategoryResponse,
    CompanyCreate,
    CompanyRequestResponse,
    CompanyRequestUpdate,
    CompanyResponse,
    CompanyShortResponse,
    CompanyUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
    WorkingHoursCreate,
    WorkingHoursResponse,
)
from app.database import get_session

router = APIRouter(tags=["companies"])


# ── Компании (публичные) ─────────────────────────────────────────────────────

@router.get("/companies", response_model=list[CompanyShortResponse])
async def list_companies(
    search: str | None = Query(None, description="Поиск по названию"),
    category: str | None = Query(None, description="Фильтр по категории"),
    city: str | None = Query(None, description="Фильтр по городу"),
    session: AsyncSession = Depends(get_session),
) -> list[CompanyShortResponse]:
    """
    Поиск и фильтрация активных компаний.

    Все параметры необязательны и комбинируются между собой.
    Возвращает краткие карточки без вложенных услуг и расписания.

    Примеры запросов:
        GET /companies                              — все компании
        GET /companies?search=барбер               — по названию
        GET /companies?category=Барбершоп          — по категории
        GET /companies?city=Москва                 — по городу
        GET /companies?search=топор&city=Москва    — комбинация фильтров
    """
    return await svc.list_companies(session, search, category, city)


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    session: AsyncSession = Depends(get_session),
) -> CompanyResponse:
    """
    Детальный просмотр компании: название, описание, услуги, расписание.

    Возвращает полную карточку с вложенными списками services и working_hours.
    Доступно без авторизации.

    Пример:
        GET /companies/5
    """
    return await svc.get_company_or_404(company_id, session)


@router.get("/companies/{company_id}/services", response_model=list[ServiceResponse])
async def get_company_services(
    company_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[ServiceResponse]:
    """
    Список активных услуг выбранной компании.

    Возвращает только услуги с is_active=True.
    Используется клиентом после выбора компании для выбора конкретной услуги.

    Пример:
        GET /companies/5/services
    """
    company = await svc.get_company_or_404(company_id, session)
    return [s for s in company.services if s.is_active]


@router.get("/categories", response_model=list[CategoryResponse])
async def search_categories(
    search: str | None = Query(None, description="Поиск категории по префиксу"),
    session: AsyncSession = Depends(get_session),
) -> list[CategoryResponse]:
    return await svc.list_categories(session, search)


# ── Компании (для владельца) ─────────────────────────────────────────────────

@router.get("/owner/company", response_model=CompanyResponse)
async def get_my_company(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyResponse:
    """
    Возвращает компанию текущего авторизованного владельца.

    Требует авторизацию (Bearer токен) и роль 'company'.
    Используется на главной странице панели управления владельца.

    Пример:
        GET /owner/company
        Authorization: Bearer <token>
    """
    return await svc.get_my_company(user, session)


@router.get("/owner/company-request", response_model=CompanyRequestResponse)
async def get_my_company_request(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyRequestResponse:
    return await svc.get_my_company_request(user, session)


@router.post("/owner/company-request", response_model=CompanyRequestResponse, status_code=201)
async def create_company_request(
    data: CompanyCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyRequestResponse:
    """
    Регистрирует новую компанию для текущего владельца.

    Требует авторизацию и роль 'company' (выдаётся при регистрации с company_name).
    После создания компании нужно добавить услуги и настроить расписание.

    Пример тела запроса:
        {
            "name": "Барбершоп Топор",
            "category": "Барбершоп",
            "city": "Москва",
            "address": "ул. Арбат, 10",
            "phone": "+7 999 123-45-67"
        }
    """
    return await svc.create_company_request(data, user, session)


@router.put("/owner/company/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    data: CompanyUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyResponse:
    """
    Обновляет данные компании. Изменяются только переданные поля.

    Требует авторизацию; пользователь должен быть владельцем компании.

    Пример — изменить адрес и телефон:
        PUT /owner/company/5
        Body: {"address": "ул. Тверская, 1", "phone": "+7 999 000-00-00"}

    Пример — временно скрыть компанию из поиска:
        PUT /owner/company/5
        Body: {"is_active": false}
    """
    return await svc.update_company(company_id, data, user, session)


@router.get("/manager/company-requests", response_model=list[CompanyRequestResponse])
async def list_company_requests(
    request_status: str | None = Query(
        None, alias="status", description="Статус заявки: pending|approved|rejected"
    ),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CompanyRequestResponse]:
    status_filter = None
    if request_status:
        try:
            status_filter = svc.CompanyRequestStatus(request_status)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Некорректный статус заявки",
            ) from exc
    return await svc.list_company_requests(user, session, status_filter)


@router.get("/manager/company-requests/{request_id}", response_model=CompanyRequestResponse)
async def get_company_request(
    request_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyRequestResponse:
    svc.require_manager_role(user)
    return await svc.get_company_request_or_404(request_id, session)


@router.put("/manager/company-requests/{request_id}", response_model=CompanyRequestResponse)
async def update_company_request(
    request_id: int,
    data: CompanyRequestUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyRequestResponse:
    return await svc.update_company_request(request_id, data, user, session)


@router.post("/manager/company-requests/{request_id}/approve", response_model=CompanyRequestResponse)
async def approve_company_request(
    request_id: int,
    data: CompanyRequestUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompanyRequestResponse:
    return await svc.approve_company_request(request_id, data, user, session)


# ── Услуги (для владельца) ───────────────────────────────────────────────────

@router.post("/owner/company/{company_id}/services", response_model=ServiceResponse, status_code=201)
async def create_service(
    company_id: int,
    data: ServiceCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ServiceResponse:
    """
    Добавляет новую услугу в каталог компании.

    Требует авторизацию; пользователь должен быть владельцем компании.

    Пример тела запроса:
        {
            "name": "Мужская стрижка",
            "description": "Стрижка машинкой или ножницами с укладкой",
            "price": 1200.00,
            "duration_minutes": 45
        }
    """
    return await svc.create_service(company_id, data, user, session)


@router.put("/owner/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    data: ServiceUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ServiceResponse:
    """
    Обновляет данные услуги. Изменяются только переданные поля.

    Пример — повысить цену:
        PUT /owner/services/12
        Body: {"price": 1500.00}

    Пример — скрыть услугу без удаления (сохраняет историю записей):
        PUT /owner/services/12
        Body: {"is_active": false}
    """
    return await svc.update_service(service_id, data, user, session)


@router.delete("/owner/services/{service_id}", status_code=204)
async def delete_service(
    service_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Удаляет услугу и все связанные с ней записи (каскадно).

    Внимание: операция необратима. Для сохранения истории записей
    рекомендуется деактивировать услугу через PUT с is_active=false.

    Пример:
        DELETE /owner/services/12
    """
    await svc.delete_service(service_id, user, session)


# ── Расписание (для владельца) ───────────────────────────────────────────────

@router.put("/owner/company/{company_id}/schedule", response_model=WorkingHoursResponse)
async def upsert_schedule(
    company_id: int,
    data: WorkingHoursCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WorkingHoursResponse:
    """
    Создаёт или обновляет рабочие часы для одного дня недели (upsert).

    Каждый вызов задаёт расписание для одного дня.
    Чтобы настроить всю неделю, нужно сделать 7 запросов (по одному на день).

    Пример — понедельник с 9:00 до 18:00:
        PUT /owner/company/5/schedule
        Body: {"day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00"}

    Пример — воскресенье — выходной:
        PUT /owner/company/5/schedule
        Body: {"day_of_week": 6, "start_time": "00:00:00", "end_time": "00:00:00", "is_working": false}
    """
    return await svc.upsert_working_hours(company_id, data, user, session)


@router.delete("/owner/company/{company_id}/schedule/{day_of_week}", status_code=204)
async def delete_schedule_day(
    company_id: int,
    day_of_week: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Полностью удаляет настройку расписания для указанного дня недели.

    После удаления этот день считается «не настроенным»: при запросе слотов
    для него будет возвращён пустой список.

    Пример — удалить настройку понедельника:
        DELETE /owner/company/5/schedule/0
    """
    await svc.delete_working_hours(company_id, day_of_week, user, session)

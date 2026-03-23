# tests/test_api.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta, date, time
from app.main import app
from app.database import get_session, engine, Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.auth.models import User, UserRole
from app.companies.models import Company, Service, WorkingHours
from app.bookings.models import Booking, BookingStatus
import asyncio

# ─────────────────────────────────────────────────────────────────────────────
# Конфигурация тестовой БД
# ─────────────────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/autobooking-test"

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Создаёт тестовый движок БД"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    """Создаёт тестовую сессию БД"""
    async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(test_session, test_engine):
    """Создаёт тестовый HTTP-клиент"""
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

# ─────────────────────────────────────────────────────────────────────────────
# Хелперы
# ─────────────────────────────────────────────────────────────────────────────

async def register_user(
    client: AsyncClient, 
    email: str, 
    password: str, 
    is_company: bool = False  # ← Переименовали для ясности
):
    """Регистрирует пользователя и возвращает токен"""
    payload = {"email": email, "password": password}
    

    endpoint = "/auth/register/company" if is_company else "/auth/register"
    
    response = await client.post(endpoint, json=payload)
    assert response.status_code == 201, f"Registration failed: {response.text}"
    return response.json()["access_token"]

async def login_user(client: AsyncClient, email: str, password: str):
    """Входит в систему и возвращает токен"""
    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

def auth_headers(token: str):
    """Возвращает заголовки авторизации"""
    return {"Authorization": f"Bearer {token}"}

# ─────────────────────────────────────────────────────────────────────────────
# Тесты: Auth
# ─────────────────────────────────────────────────────────────────────────────

class TestAuth:
    async def test_register_user(self, client: AsyncClient):
        """Регистрация обычного пользователя"""
        response = await client.post("/auth/register", json={
            "email": "test_user@example.com",
            "password": "password123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_company(self, client: AsyncClient):
        """Регистрация владельца компании"""
        response = await client.post("/auth/register/company", json={
            "email": "test_owner@example.com",
            "password": "password123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Регистрация с занятым email"""
        await client.post("/auth/register", json={
            "email": "duplicate@example.com",
            "password": "password123"
        })
        response = await client.post("/auth/register", json={
            "email": "duplicate@example.com",
            "password": "password123"
        })
        assert response.status_code == 409

    async def test_login_success(self, client: AsyncClient):
        """Успешный вход"""
        await client.post("/auth/register", json={
            "email": "login_test@example.com",
            "password": "password123"
        })
        response = await client.post("/auth/login", json={
            "email": "login_test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        """Вход с неверным паролем"""
        await client.post("/auth/register", json={
            "email": "wrong_pass@example.com",
            "password": "password123"
        })
        response = await client.post("/auth/login", json={
            "email": "wrong_pass@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    async def test_get_me(self, client: AsyncClient):
        """Получение данных текущего пользователя"""
        token = await register_user(client, "me_test@example.com", "password123", is_company=False)
        response = await client.get("/auth/me", headers=auth_headers(token))
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me_test@example.com"
        assert data["role"] == "user"

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Запрос /me без токена"""
        response = await client.get("/auth/me")
        assert response.status_code == 403

        
# ─────────────────────────────────────────────────────────────────────────────
# Тесты: Companies
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanies:
    async def test_list_companies_empty(self, client: AsyncClient):
        """Список компаний пуст"""
        response = await client.get("/companies")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_companies_with_data(self, client: AsyncClient):
        """Список компаний с данными"""
        token = await register_user(client, "owner1@example.com", "password123", is_company=True)
        await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Компания 1",
            "category": "Барбершоп",
            "city": "Москва"
        })
        
        token2 = await register_user(client, "owner2@example.com", "password123", is_company=True)
        await client.post("/owner/company", headers=auth_headers(token2), json={
            "name": "Компания 2",
            "category": "Салон красоты",
            "city": "Санкт-Петербург"
        })
        
        response = await client.get("/companies")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_filter_companies_by_city(self, client: AsyncClient):
        """Фильтр компаний по городу"""
        token = await register_user(client, "owner_filter@example.com", "password123",is_company=True)
        await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Московская Компания",
            "city": "Москва"
        })
        
        token2 = await register_user(client, "owner_filter2@example.com", "password123", is_company=True)
        await client.post("/owner/company", headers=auth_headers(token2), json={
            "name": "Питерская Компания",
            "city": "Санкт-Петербург"
        })
        
        response = await client.get("/companies?city=Москва")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["city"] == "Москва"

    async def test_get_company_details(self, client: AsyncClient):
        """Детали компании"""
        token = await register_user(client, "owner_detail@example.com", "password123", is_company=True)
        create_resp = await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Детали Компания",
            "description": "Описание",
            "category": "Барбершоп",
            "city": "Москва",
            "address": "ул. Тестовая, 1",
            "phone": "+7 999 000-00-00"
        })
        company_id = create_resp.json()["id"]
        
        response = await client.get(f"/companies/{company_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Детали Компания"
        assert "services" in data
        assert "working_hours" in data

    async def test_create_company(self, client: AsyncClient):
        """Создание компании владельцем"""
        token = await register_user(client, "create_owner@example.com", "password123", is_company=True)
        response = await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Новая Компания",
            "category": "Салон красоты",
            "city": "Казань",
            "address": "ул. Новая, 10",
            "phone": "+7 999 111-22-33"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новая Компания"
        assert data["is_active"] == True

    async def test_create_company_user_role(self, client: AsyncClient):
        """Попытка создания компании обычным пользователем"""
        token = await register_user(client, "regular_user@example.com", "password123", is_company=False)
        response = await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Нельзя Создать",
            "city": "Москва"
        })
        assert response.status_code == 403

    async def test_get_my_company(self, client: AsyncClient):
        """Получение своей компании"""
        token = await register_user(client, "my_company_owner@example.com", "password123", is_company=True)
        await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Моя Компания",
            "city": "Москва"
        })
        
        response = await client.get("/owner/company", headers=auth_headers(token))
        assert response.status_code == 200
        assert response.json()["name"] == "Моя Компания"

    async def test_update_company(self, client: AsyncClient):
        """Обновление компании"""
        token = await register_user(client, "update_owner@example.com", "password123", is_company=True)
        create_resp = await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Старое Название",
            "city": "Москва"
        })
        company_id = create_resp.json()["id"]
        
        response = await client.put(
            f"/owner/company/{company_id}",
            headers=auth_headers(token),
            json={"name": "Новое Название", "phone": "+7 999 000-00-00"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Новое Название"

# ─────────────────────────────────────────────────────────────────────────────
# Тесты: Services
# ─────────────────────────────────────────────────────────────────────────────

class TestServices:
    @pytest_asyncio.fixture
    async def company_with_owner(self, client: AsyncClient):
        """Создаёт владельца и компанию"""
        token = await register_user(client, "service_owner@example.com", "password123", is_company=True)
        create_resp = await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Сервис Компания",
            "city": "Москва"
        })
        return token, create_resp.json()["id"]

    async def test_create_service(self, client: AsyncClient, company_with_owner):
        """Создание услуги"""
        token, company_id = company_with_owner
        response = await client.post(
            f"/owner/company/{company_id}/services",
            headers=auth_headers(token),
            json={
                "name": "Стрижка",
                "description": "Мужская стрижка",
                "price": 1200.00,
                "duration_minutes": 45
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Стрижка"
        assert data["duration_minutes"] == 45

    async def test_get_company_services(self, client: AsyncClient, company_with_owner):
        """Получение услуг компании"""
        token, company_id = company_with_owner
        await client.post(
            f"/owner/company/{company_id}/services",
            headers=auth_headers(token),
            json={"name": "Услуга 1", "duration_minutes": 30}
        )
        await client.post(
            f"/owner/company/{company_id}/services",
            headers=auth_headers(token),
            json={"name": "Услуга 2", "duration_minutes": 60}
        )
        
        response = await client.get(f"/companies/{company_id}/services")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_update_service(self, client: AsyncClient, company_with_owner):
        """Обновление услуги"""
        token, company_id = company_with_owner
        create_resp = await client.post(
            f"/owner/company/{company_id}/services",
            headers=auth_headers(token),
            json={"name": "Старая Цена", "price": 1000.00, "duration_minutes": 30}
        )
        service_id = create_resp.json()["id"]
        
        response = await client.put(
            f"/owner/services/{service_id}",
            headers=auth_headers(token),
            json={"price": 1500.00}
        )
        assert response.status_code == 200
        assert response.json()["price"] == "1500.00"

    async def test_delete_service(self, client: AsyncClient, company_with_owner):
        """Удаление услуги"""
        token, company_id = company_with_owner
        create_resp = await client.post(
            f"/owner/company/{company_id}/services",
            headers=auth_headers(token),
            json={"name": "На Удаление", "duration_minutes": 30}
        )
        service_id = create_resp.json()["id"]
        
        response = await client.delete(
            f"/owner/services/{service_id}",
            headers=auth_headers(token)
        )
        assert response.status_code == 204

# ─────────────────────────────────────────────────────────────────────────────
# Тесты: Working Hours
# ─────────────────────────────────────────────────────────────────────────────

class TestWorkingHours:
    @pytest_asyncio.fixture
    async def company_with_owner(self, client: AsyncClient):
        """Создаёт владельца и компанию"""
        token = await register_user(client, "schedule_owner@example.com", "password123", is_company=True)
        create_resp = await client.post("/owner/company", headers=auth_headers(token), json={
            "name": "Расписание Компания",
            "city": "Москва"
        })
        return token, create_resp.json()["id"]

    async def test_upsert_schedule(self, client: AsyncClient, company_with_owner):
        """Создание расписания"""
        token, company_id = company_with_owner
        response = await client.put(
            f"/owner/company/{company_id}/schedule",
            headers=auth_headers(token),
            json={
                "day_of_week": 0,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "is_working": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["day_of_week"] == 0
        assert data["start_time"] == "09:00:00"

    async def test_upsert_schedule_update(self, client: AsyncClient, company_with_owner):
        """Обновление расписания"""
        token, company_id = company_with_owner
        await client.put(
            f"/owner/company/{company_id}/schedule",
            headers=auth_headers(token),
            json={"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00"}
        )
        
        response = await client.put(
            f"/owner/company/{company_id}/schedule",
            headers=auth_headers(token),
            json={"day_of_week": 1, "start_time": "10:00:00", "end_time": "19:00:00"}
        )
        assert response.status_code == 200
        assert response.json()["start_time"] == "10:00:00"

    async def test_set_weekend(self, client: AsyncClient, company_with_owner):
        """Установка выходного дня"""
        token, company_id = company_with_owner
        response = await client.put(
            f"/owner/company/{company_id}/schedule",
            headers=auth_headers(token),
            json={
                "day_of_week": 6,
                "start_time": "00:00:00",
                "end_time": "00:00:00",
                "is_working": False
            }
        )
        assert response.status_code == 200
        assert response.json()["is_working"] == False

    async def test_delete_schedule_day(self, client: AsyncClient, company_with_owner):
        """Удаление расписания дня"""
        token, company_id = company_with_owner
        await client.put(
            f"/owner/company/{company_id}/schedule",
            headers=auth_headers(token),
            json={"day_of_week": 2, "start_time": "09:00:00", "end_time": "18:00:00"}
        )
        
        response = await client.delete(
            f"/owner/company/{company_id}/schedule/2",
            headers=auth_headers(token)
        )
        assert response.status_code == 204

# ─────────────────────────────────────────────────────────────────────────────
# Тесты: Bookings
# ─────────────────────────────────────────────────────────────────────────────

class TestBookings:
    @pytest_asyncio.fixture
    async def full_setup(self, client: AsyncClient):
        """Полная настройка: владелец, компания, услуга, расписание, клиент"""
        # Владелец
        owner_token = await register_user(client, "booking_owner@example.com", "password123", is_company=True)
        company_resp = await client.post("/owner/company", headers=auth_headers(owner_token), json={
            "name": "Booking Компания",
            "city": "Москва"
        })
        company_id = company_resp.json()["id"]
        
        # Услуга
        service_resp = await client.post(
            f"/owner/company/{company_id}/services",
            headers=auth_headers(owner_token),
            json={"name": "Тест Услуга", "duration_minutes": 60, "price": 1000.00}
        )
        service_id = service_resp.json()["id"]
        
        # Расписание (завтра)
        tomorrow = (datetime.now().date() + timedelta(days=1)).weekday()
        await client.put(
            f"/owner/company/{company_id}/schedule",
            headers=auth_headers(owner_token),
            json={"day_of_week": tomorrow, "start_time": "09:00:00", "end_time": "18:00:00"}
        )
        
        # Клиент
        client_token = await register_user(client, "booking_client@example.com", "password123", is_company=False)
        
        return {
            "owner_token": owner_token,
            "client_token": client_token,
            "company_id": company_id,
            "service_id": service_id,
            "tomorrow": tomorrow
        }

    async def test_get_available_slots(self, client: AsyncClient, full_setup):
        """Получение доступных слотов"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        response = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) > 0
        assert "start_at" in slots[0]
        assert "end_at" in slots[0]

    async def test_get_service_calendar(self, client: AsyncClient, full_setup):
        """Получение календаря услуги"""
        setup = full_setup
        response = await client.get(f"/services/{setup['service_id']}/calendar")
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == setup["service_id"]
        assert len(data["days"]) == 14
        assert "period_start" in data
        assert "period_end" in data

    async def test_create_booking(self, client: AsyncClient, full_setup):
        """Создание записи"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        # Получаем свободный слот
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        # Создаём запись
        response = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={
                "service_id": setup["service_id"],
                "start_at": slot["start_at"],
                "notes": "Тестовая запись"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["notes"] == "Тестовая запись"
        return data["id"]

    async def test_create_booking_conflict(self, client: AsyncClient, full_setup):
        """Конфликт при создании записи (слот занят)"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        # Первая запись
        await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        
        # Вторая запись на тот же слот
        response = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        assert response.status_code == 409

    async def test_get_my_bookings(self, client: AsyncClient, full_setup):
        """Получение своих записей"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        
        response = await client.get("/bookings/my", headers=auth_headers(setup["client_token"]))
        assert response.status_code == 200
        assert len(response.json()) >= 1

    async def test_cancel_booking(self, client: AsyncClient, full_setup):
        """Отмена записи"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        create_resp = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        booking_id = create_resp.json()["id"]
        
        response = await client.post(
            f"/bookings/{booking_id}/cancel",
            headers=auth_headers(setup["client_token"])
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    async def test_cancel_already_cancelled(self, client: AsyncClient, full_setup):
        """Повторная отмена уже отменённой записи"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        create_resp = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        booking_id = create_resp.json()["id"]
        
        await client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers(setup["client_token"]))
        
        response = await client.post(
            f"/bookings/{booking_id}/cancel",
            headers=auth_headers(setup["client_token"])
        )
        assert response.status_code == 400

    async def test_owner_get_company_bookings(self, client: AsyncClient, full_setup):
        """Владелец получает записи компании"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        
        response = await client.get(
            f"/owner/company/{setup['company_id']}/bookings",
            headers=auth_headers(setup["owner_token"])
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    async def test_owner_confirm_booking(self, client: AsyncClient, full_setup):
        """Владелец подтверждает запись"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        create_resp = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        booking_id = create_resp.json()["id"]
        
        response = await client.post(
            f"/owner/bookings/{booking_id}/confirm",
            headers=auth_headers(setup["owner_token"])
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    async def test_owner_confirm_already_confirmed(self, client: AsyncClient, full_setup):
        """Повторное подтверждение уже подтверждённой записи"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        create_resp = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        booking_id = create_resp.json()["id"]
        
        await client.post(f"/owner/bookings/{booking_id}/confirm", headers=auth_headers(setup["owner_token"]))
        
        response = await client.post(
            f"/owner/bookings/{booking_id}/confirm",
            headers=auth_headers(setup["owner_token"])
        )
        assert response.status_code == 400

    async def test_cancel_other_user_booking(self, client: AsyncClient, full_setup):
        """Попытка отменить чужую запись"""
        setup = full_setup
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        slots_resp = await client.get(
            f"/services/{setup['service_id']}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        create_resp = await client.post(
            "/bookings",
            headers=auth_headers(setup["client_token"]),
            json={"service_id": setup["service_id"], "start_at": slot["start_at"]}
        )
        booking_id = create_resp.json()["id"]
        
        # Другой клиент пытается отменить
        other_token = await register_user(client, "other_client@example.com", "password123", is_company=False)
        response = await client.post(
            f"/bookings/{booking_id}/cancel",
            headers=auth_headers(other_token)
        )
        assert response.status_code == 403

# ─────────────────────────────────────────────────────────────────────────────
# Тесты: Permissions
# ─────────────────────────────────────────────────────────────────────────────

class TestPermissions:
    @pytest_asyncio.fixture
    async def two_companies(self, client: AsyncClient):
        """Создаёт двух владельцев с компаниями"""
        token1 = await register_user(client, "perm_owner1@example.com", "password123", is_company=True)
        company1 = await client.post("/owner/company", headers=auth_headers(token1), json={
            "name": "Компания 1",
            "city": "Москва"
        })
        
        token2 = await register_user(client, "perm_owner2@example.com", "password123", is_company=True)
        company2 = await client.post("/owner/company", headers=auth_headers(token2), json={
            "name": "Компания 2",
            "city": "Санкт-Петербург"
        })
        
        return {
            "token1": token1,
            "token2": token2,
            "company1_id": company1.json()["id"],
            "company2_id": company2.json()["id"]
        }

    async def test_cannot_access_other_company(self, client: AsyncClient, two_companies):
        """Владелец не может получить чужую компанию через /owner/company"""
        setup = two_companies
        # Владелец 1 пытается получить свою компанию (должно работать)
        response1 = await client.get("/owner/company", headers=auth_headers(setup["token1"]))
        assert response1.status_code == 200
        
        # Владелец 2 пытается получить свою компанию (должно работать)
        response2 = await client.get("/owner/company", headers=auth_headers(setup["token2"]))
        assert response2.status_code == 200
        assert response2.json()["id"] == setup["company2_id"]

    async def test_cannot_update_other_company(self, client: AsyncClient, two_companies):
        """Владелец не может обновить чужую компанию"""
        setup = two_companies
        response = await client.put(
            f"/owner/company/{setup['company2_id']}",
            headers=auth_headers(setup["token1"]),
            json={"name": "Взломанное Название"}
        )
        assert response.status_code == 403

    async def test_cannot_create_service_for_other_company(self, client: AsyncClient, two_companies):
        """Владелец не может создать услугу в чужой компании"""
        setup = two_companies
        response = await client.post(
            f"/owner/company/{setup['company2_id']}/services",
            headers=auth_headers(setup["token1"]),
            json={"name": "Чужая Услуга", "duration_minutes": 30}
        )
        assert response.status_code == 403

    async def test_cannot_confirm_other_company_booking(self, client: AsyncClient, two_companies):
        """Владелец не может подтвердить запись в чужой компании"""
        setup = two_companies
        
        # Создаём услугу в компании 2
        service_resp = await client.post(
            f"/owner/company/{setup['company2_id']}/services",
            headers=auth_headers(setup["token2"]),
            json={"name": "Услуга", "duration_minutes": 30}
        )
        service_id = service_resp.json()["id"]
        
        # Клиент создаёт запись
        client_token = await register_user(client, "perm_client@example.com", "password123", is_company=False)
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        # Настраиваем расписание
        tomorrow = tomorrow_date.weekday()
        await client.put(
            f"/owner/company/{setup['company2_id']}/schedule",
            headers=auth_headers(setup["token2"]),
            json={"day_of_week": tomorrow, "start_time": "09:00:00", "end_time": "18:00:00"}
        )
        
        slots_resp = await client.get(
            f"/services/{service_id}/slots",
            params={"date": tomorrow_date.isoformat()}
        )
        slot = slots_resp.json()[0]
        
        booking_resp = await client.post(
            "/bookings",
            headers=auth_headers(client_token),
            json={"service_id": service_id, "start_at": slot["start_at"]}
        )
        booking_id = booking_resp.json()["id"]
        
        # Владелец 1 пытается подтвердить (должно быть запрещено)
        response = await client.post(
            f"/owner/bookings/{booking_id}/confirm",
            headers=auth_headers(setup["token1"])
        )
        assert response.status_code == 403

# ─────────────────────────────────────────────────────────────────────────────
# Запуск тестов
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
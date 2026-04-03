"""
Заполнение БД данными из дампа PostgreSQL (`COPY ... FROM stdin`).

Использование (из каталога ``back/``)::

    PYTHONPATH=. python -m scripts.seed

Путь к файлу дампа по умолчанию: ``back/dump``. Переопределение::

    SEED_DUMP_PATH=/path/to/dump PYTHONPATH=. python -m scripts.seed

Перед запуском примените миграции (``alembic upgrade head``). Скрипт очищает
таблицы и вставляет строки из дампа с сохранением исходных ``id`` и связей.
"""
from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.bookings.models import Booking, BookingStatus
from app.companies.models import Company, Service, WorkingHours
from app.auth.models import User, UserRole
from app.database import async_session_maker


def _default_dump_path() -> Path:
    return Path(__file__).resolve().parent.parent / "dump"


def _parse_pg_timestamp(s: str) -> datetime:
    """Преобразует метку времени из pg_dump в aware-datetime."""
    s = s.strip()
    if s.endswith("+00"):
        s = s[:-3] + "+00:00"
    return datetime.fromisoformat(s)


def _parse_time(s: str) -> time:
    return datetime.strptime(s.strip(), "%H:%M:%S").time()


def _parse_bool(raw: str) -> bool:
    return raw.strip() == "t"


def _parse_nullable(raw: str) -> str | None:
    if raw == "\\N" or raw == "":
        return None
    return raw


def parse_copy_sections(dump_path: Path) -> dict[str, tuple[list[str], list[list[str]]]]:
    """
    Извлекает из pg_dump блоки ``COPY public.<table> (...) FROM stdin``.

    Returns:
        Имя таблицы -> (список колонок, строки как списки полей).
    """
    content = dump_path.read_text(encoding="utf-8")
    tables: dict[str, tuple[list[str], list[list[str]]]] = {}
    lines = content.splitlines()
    i = 0
    copy_re = re.compile(r"^COPY public\.(\w+) \(([^)]+)\) FROM stdin;$")
    while i < len(lines):
        m = copy_re.match(lines[i])
        if m:
            table = m.group(1)
            cols = [c.strip() for c in m.group(2).split(",")]
            i += 1
            rows: list[list[str]] = []
            while i < len(lines) and lines[i] != r"\.":
                rows.append(lines[i].split("\t"))
                i += 1
            tables[table] = (cols, rows)
        i += 1
    return tables


def _build_users(rows: list[list[str]]) -> list[User]:
    out: list[User] = []
    for r in rows:
        email, hashed_password, role_s, created_at_s, id_s = r
        out.append(
            User(
                id=int(id_s),
                email=email,
                hashed_password=hashed_password,
                role=UserRole(role_s),
                created_at=_parse_pg_timestamp(created_at_s),
            )
        )
    return out


def _build_companies(rows: list[list[str]]) -> list[Company]:
    out: list[Company] = []
    for r in rows:
        (
            owner_id,
            name,
            description,
            category,
            city,
            address,
            phone,
            is_active,
            created_at_s,
            id_s,
        ) = r
        out.append(
            Company(
                id=int(id_s),
                owner_id=int(owner_id),
                name=name,
                description=_parse_nullable(description),
                category=_parse_nullable(category),
                city=_parse_nullable(city),
                address=_parse_nullable(address),
                phone=_parse_nullable(phone),
                is_active=_parse_bool(is_active),
                created_at=_parse_pg_timestamp(created_at_s),
            )
        )
    return out


def _build_services(rows: list[list[str]]) -> list[Service]:
    out: list[Service] = []
    for r in rows:
        company_id, name, description, price_s, duration_s, is_active, id_s = r
        price: Decimal | None
        if price_s == "\\N":
            price = None
        else:
            price = Decimal(price_s)
        out.append(
            Service(
                id=int(id_s),
                company_id=int(company_id),
                name=name,
                description=_parse_nullable(description),
                price=price,
                duration_minutes=int(duration_s),
                is_active=_parse_bool(is_active),
            )
        )
    return out


def _build_working_hours(rows: list[list[str]]) -> list[WorkingHours]:
    out: list[WorkingHours] = []
    for r in rows:
        company_id, dow, st, et, is_working, id_s = r
        out.append(
            WorkingHours(
                id=int(id_s),
                company_id=int(company_id),
                day_of_week=int(dow),
                start_time=_parse_time(st),
                end_time=_parse_time(et),
                is_working=_parse_bool(is_working),
            )
        )
    return out


def _build_bookings(rows: list[list[str]]) -> list[Booking]:
    out: list[Booking] = []
    for r in rows:
        user_id, service_id, company_id, start_s, end_s, status_s, notes, created_s, id_s = r
        out.append(
            Booking(
                id=int(id_s),
                user_id=int(user_id),
                service_id=int(service_id),
                company_id=int(company_id),
                start_at=_parse_pg_timestamp(start_s),
                end_at=_parse_pg_timestamp(end_s),
                status=BookingStatus(status_s),
                notes=_parse_nullable(notes),
                created_at=_parse_pg_timestamp(created_s),
            )
        )
    return out


async def _clear_tables(session: AsyncSession) -> None:
    await session.execute(delete(Booking))
    await session.execute(delete(WorkingHours))
    await session.execute(delete(Service))
    await session.execute(delete(Company))
    await session.execute(delete(User))
    await session.execute(text("DELETE FROM alembic_version"))


async def seed_from_dump(dump_path: Path) -> None:
    data = parse_copy_sections(dump_path)
    required = ("users", "companies", "services", "working_hours", "bookings", "alembic_version")
    for t in required:
        if t not in data:
            raise FileNotFoundError(
                f"В дампе нет таблицы «{t}». Проверьте файл: {dump_path}"
            )

    users = _build_users(data["users"][1])
    companies = _build_companies(data["companies"][1])
    services = _build_services(data["services"][1])
    working_hours = _build_working_hours(data["working_hours"][1])
    bookings = _build_bookings(data["bookings"][1])
    alembic_rows = data["alembic_version"][1]
    if not alembic_rows or len(alembic_rows[0]) != 1:
        raise ValueError("Некорректные данные alembic_version в дампе")
    version_num = alembic_rows[0][0].strip()

    async with async_session_maker() as session:
        await _clear_tables(session)
        session.add_all(users)
        session.add_all(companies)
        session.add_all(services)
        session.add_all(working_hours)
        session.add_all(bookings)
        await session.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
            {"v": version_num},
        )
        await session.commit()


async def main() -> None:
    dump_path = Path(os.environ.get("SEED_DUMP_PATH", _default_dump_path())).resolve()
    if not dump_path.is_file():
        raise SystemExit(f"Файл дампа не найден: {dump_path}")
    await seed_from_dump(dump_path)
    print(f"OK: данные загружены из {dump_path}")


if __name__ == "__main__":
    asyncio.run(main())

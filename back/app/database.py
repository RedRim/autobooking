"""
настройка подключения к базе данных
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer

from app.config import get_config

_cfg = get_config()
_cfg.db.ensure_sqlite_parent_exists()
DATABASE_URL = _cfg.db.dsn

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """
    базовый класс для всех моделей
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


async def get_session():
    """
    генератор сессий для dependency injection
    """
    async with async_session_maker() as session:
        yield session

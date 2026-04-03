"""
конфигурация приложения
"""
from pathlib import Path

from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """
    конфигурация подключения к базе данных (SQLite).

    Путь задаётся относительно текущей рабочей директории процесса
    (при запуске из каталога `back/` — например `data/autobooking.db`).
    """

    sqlite_path: str = "data/autobooking.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def _resolved_path(self) -> str:
        return str(Path(self.sqlite_path).expanduser().resolve())

    def ensure_sqlite_parent_exists(self) -> None:
        """Создаёт каталог для файла БД (например data/), если его ещё нет."""
        Path(self._resolved_path()).parent.mkdir(parents=True, exist_ok=True)

    @property
    def dsn(self) -> str:
        """
        асинхронный DSN для SQLite (aiosqlite)
        """
        p = self._resolved_path()
        # абсолютный путь: четыре слэша после sqlite+aiosqlite:
        return f"sqlite+aiosqlite:///{p}"

    @property
    def sync_dsn(self) -> str:
        """
        синхронный DSN для Alembic
        """
        p = self._resolved_path()
        return f"sqlite:///{p}"


class Settings(BaseSettings):
    """
    Общие настройки приложения
    """
    api_key: str

    class Config:
        env_file = ".env"
        extra = "ignore"


class JWTConfig(BaseSettings):
    """
    конфигурация JWT токенов
    """
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 дней

    class Config:
        env_file = ".env"
        extra = "ignore"


class Config:
    """
    главная конфигурация проекта
    """
    db: DatabaseConfig = DatabaseConfig()
    settings: Settings = Settings()
    jwt: JWTConfig = JWTConfig()


_config = None


def get_config() -> Config:
    """
    получить глобальный инстанс конфигурации
    """
    global _config
    if _config is None:
        _config = Config()
    return _config

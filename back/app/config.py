"""
конфигурация приложения
"""
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """
    конфигурация подключения к базе данных
    """
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str
    db_port: int

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def dsn(self) -> str:
        """
        асинхронный DSN для подключения к PostgreSQL
        """
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.db_host}:{self.db_port}/{self.postgres_db}"

    @property
    def sync_dsn(self) -> str:
        """
        синхронный DSN для подключения (для Alembic)
        """
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.db_host}:{self.db_port}/{self.postgres_db}"


class Settings(BaseSettings):
    """
    Общие настройки приложения
    """

    api_key: str
    # Список origin фронта через запятую (для CORS). Пример: http://localhost:8080,http://127.0.0.1:8080
    cors_origins: str = (
        "http://localhost,http://127.0.0.1,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:80,http://127.0.0.1:80"
    )

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

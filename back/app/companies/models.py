import enum
from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CompanyRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Category(Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)


class CompanyCreationRequest(Base):
    __tablename__ = "company_creation_requests"

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[CompanyRequestStatus] = mapped_column(
        Enum(CompanyRequestStatus, name="companyrequeststatus", native_enum=True),
        nullable=False,
        default=CompanyRequestStatus.pending,
    )
    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Company(Base):
    """
    Компания, зарегистрированная в системе.

    Владелец (owner_id) — пользователь с ролью 'company'.
    К компании привязаны услуги (services) и рабочее расписание (working_hours).

    Атрибуты:
        owner_id        — ID владельца (FK → users.id).
        name            — название компании, например «Барбершоп Топор».
        description     — произвольное описание деятельности.
        category_id     — ссылка на категорию (FK → categories.id).
        city            — город присутствия, например «Москва».
        address         — улица и номер дома.
        phone           — контактный телефон.
        is_active       — флаг видимости в поиске; False скрывает компанию из выдачи.
        created_at      — UTC-время регистрации, проставляется БД автоматически.
        services        — список услуг (загружается сразу вместе с компанией).
        working_hours   — список рабочих часов по дням недели (сортировка по дню).
    """

    __tablename__ = "companies"

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    services: Mapped[list["Service"]] = relationship(
        "Service", back_populates="company", lazy="selectin"
    )
    working_hours: Mapped[list["WorkingHours"]] = relationship(
        "WorkingHours", back_populates="company", lazy="selectin", order_by="WorkingHours.day_of_week"
    )
    category_rel: Mapped["Category | None"] = relationship("Category", lazy="joined")

    @property
    def category(self) -> str | None:
        if self.category_rel is None:
            return None
        return self.category_rel.name


class Service(Base):
    """
    Услуга, предоставляемая компанией.

    Определяет название, стоимость и продолжительность одного сеанса.
    На основе duration_minutes система нарезает свободные временны́е слоты
    при запросе доступного расписания.

    Атрибуты:
        company_id          — ID компании-владельца (FK → companies.id).
        name                — название услуги, например «Мужская стрижка».
        description         — подробное описание услуги.
        price               — стоимость в рублях (Decimal 10,2); None — цена не указана.
        duration_minutes    — длительность сеанса в минутах, например 60.
        is_active           — False исключает услугу из публичного списка и поиска слотов.
    """

    __tablename__ = "services"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="services")


class WorkingHours(Base):
    """
    Рабочие часы компании для конкретного дня недели.

    Одна запись = один день. Уникальное ограничение (company_id, day_of_week)
    гарантирует, что для каждого дня не может быть двух записей.

    Атрибуты:
        company_id  — ID компании (FK → companies.id).
        day_of_week — день недели: 0 = Понедельник, …, 6 = Воскресенье.
        start_time  — время начала работы, например 09:00.
        end_time    — время окончания работы, например 18:00.
        is_working  — False означает выходной день (слоты не генерируются).

    Пример: company_id=5, day_of_week=0, start_time=09:00, end_time=18:00, is_working=True
            → в понедельник компания работает с 9 до 18.
    """

    __tablename__ = "working_hours"

    __table_args__ = (UniqueConstraint("company_id", "day_of_week", name="uq_company_day"),)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Пн, 6=Вс
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="working_hours")

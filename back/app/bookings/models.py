import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BookingStatus(str, enum.Enum):
    """
    Жизненный цикл записи на услугу.

    Значения:
        pending   — запись создана, ожидает подтверждения владельцем.
        confirmed — владелец подтвердил запись.
        cancelled — запись отменена пользователем или владельцем.

    Переходы:
        pending → confirmed  (владелец подтверждает через POST /owner/bookings/{id}/confirm)
        pending → cancelled  (пользователь отменяет через POST /bookings/{id}/cancel)
    """

    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Booking(Base):
    """
    Запись пользователя на конкретную услугу в конкретное время.

    end_at вычисляется автоматически при создании:
        end_at = start_at + timedelta(minutes=service.duration_minutes)

    Атрибуты:
        user_id     — ID пользователя, сделавшего запись (FK → users.id).
        service_id  — ID услуги (FK → services.id).
        company_id  — ID компании (FK → companies.id); дублируется для быстрой фильтрации
                      всех записей компании без JOIN на services.
        start_at    — UTC-дата и время начала сеанса.
        end_at      — UTC-дата и время окончания сеанса.
        status      — текущий статус (см. BookingStatus).
        notes       — произвольная заметка от клиента, например «аллергия на краску».
        created_at  — UTC-время создания записи, проставляется БД автоматически.

    Пример:
        service.duration_minutes = 60
        start_at = 2026-03-10 10:00 UTC
        end_at   = 2026-03-10 11:00 UTC
    """

    __tablename__ = "bookings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="bookingstatus", native_enum=False),
        default=BookingStatus.pending,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

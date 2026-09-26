"""Unified employment period table.

ЕДИНАЯ таблица периодов занятости: общие данные о начале/окончании +
дискриминатор типа (period_type). Данные, специфичные для конкретного вида,
хранятся в собственной таблице деталей модуля (FK 1:1 по period_id).

Изменения фиксируются через update_reason / version / active / updated_by.
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.employee import Employee
    from src.models.financial import FinancialRecord


class PeriodType(str, enum.Enum):
    """Виды занятости. Каждый вид — унифицированный модуль (см. src/models/occupancy)."""

    shift = "shift"            # вахта
    vacation = "vacation"      # отпуск
    sick_leave = "sick_leave"  # больничный
    flight = "flight"          # перелёт
    hotel = "hotel"            # гостиница
    train = "train"            # поездка на поезде
    taxi = "taxi"              # поездка на такси
    other = "other"            # другое


class EmploymentPeriod(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employment_periods"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id"), index=True
    )
    period_type: Mapped[PeriodType] = mapped_column(
        SAEnum(PeriodType, name="period_type"), index=True, nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    update_reason: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employee: Mapped["Employee"] = relationship()
    financial_records: Mapped[list["FinancialRecord"]] = relationship(
        back_populates="period",
        cascade="all, delete-orphan",
    )

    @validates("period_type")
    def _coerce_period_type(self, key: str, value: Any) -> PeriodType:
        """Нормализует строковые значения в enum (для любого пути создания)."""
        if isinstance(value, str):
            return PeriodType(value)
        return value
"""Financial records (income/expenses) of employment periods + attachments.

Унифицированные свойства видов занятости: расходы и доходы
(сумма float, описание text), подтверждаемые файлами (S3).
"""
import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.employment_period import EmploymentPeriod


class FinancialKind(str, enum.Enum):
    income = "income"
    expense = "expense"


class FinancialRecord(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "financial_records"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[FinancialKind] = mapped_column(
        SAEnum(FinancialKind, name="financial_kind"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    period: Mapped["EmploymentPeriod"] = relationship(back_populates="financial_records")
    attachments: Mapped[list["FinancialAttachment"]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )

    @validates("kind")
    def _coerce_kind(self, key: str, value: Any) -> FinancialKind:
        if isinstance(value, str):
            return FinancialKind(value)
        return value


class FinancialAttachment(UUIDMixin, TimestampMixin, Base):
    """Метаданные файла-подтверждения; сам файл хранится в S3."""

    __tablename__ = "financial_attachments"

    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_records.id", ondelete="CASCADE"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(200))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    s3_key: Mapped[str] = mapped_column(String(1000))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    record: Mapped[FinancialRecord] = relationship(back_populates="attachments")
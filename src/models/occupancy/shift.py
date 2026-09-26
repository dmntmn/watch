"""Модуль «Вахта». Вахты ведутся на месторождениях (fields)."""
import uuid

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class ShiftDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "shift_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id"), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class ShiftCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_id: uuid.UUID
    notes: str | None = None


class ShiftUpdate(BaseModel):
    field_id: uuid.UUID | None = None
    notes: str | None = None


@register_occupancy_type
class ShiftModule(OccupancyModule):
    type_name = "shift"
    label = "Вахта"
    detail_model = ShiftDetail
    create_schema = ShiftCreate
    update_schema = ShiftUpdate
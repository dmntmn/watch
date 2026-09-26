"""Модуль «Отпуск»."""
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class VacationDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "vacation_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class VacationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notes: str | None = None


class VacationUpdate(BaseModel):
    notes: str | None = None


@register_occupancy_type
class VacationModule(OccupancyModule):
    type_name = "vacation"
    label = "Отпуск"
    detail_model = VacationDetail
    create_schema = VacationCreate
    update_schema = VacationUpdate
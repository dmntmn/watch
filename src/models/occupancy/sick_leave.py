"""Модуль «Больничный»."""
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class SickLeaveDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sick_leave_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class SickLeaveCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notes: str | None = None


class SickLeaveUpdate(BaseModel):
    notes: str | None = None


@register_occupancy_type
class SickLeaveModule(OccupancyModule):
    type_name = "sick_leave"
    label = "Больничный"
    detail_model = SickLeaveDetail
    create_schema = SickLeaveCreate
    update_schema = SickLeaveUpdate
"""Модуль «Другое» — универсальный вид занятости."""
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class OtherDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "other_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class OtherCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notes: str | None = None


class OtherUpdate(BaseModel):
    notes: str | None = None


@register_occupancy_type
class OtherModule(OccupancyModule):
    type_name = "other"
    label = "Другое"
    detail_model = OtherDetail
    create_schema = OtherCreate
    update_schema = OtherUpdate
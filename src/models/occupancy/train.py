"""Модуль «Поездка на поезде»."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class TrainDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "train_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    route: Mapped[str | None] = mapped_column(String(300))
    train_number: Mapped[str | None] = mapped_column(String(50))
    carriage: Mapped[str | None] = mapped_column(String(50))
    seat_number: Mapped[str | None] = mapped_column(String(50))
    departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TrainCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    route: str | None = None
    train_number: str | None = None
    carriage: str | None = None
    seat_number: str | None = None
    departure_at: datetime | None = None
    arrival_at: datetime | None = None


class TrainUpdate(BaseModel):
    route: str | None = None
    train_number: str | None = None
    carriage: str | None = None
    seat_number: str | None = None
    departure_at: datetime | None = None
    arrival_at: datetime | None = None


@register_occupancy_type
class TrainModule(OccupancyModule):
    type_name = "train"
    label = "Поездка на поезде"
    detail_model = TrainDetail
    create_schema = TrainCreate
    update_schema = TrainUpdate
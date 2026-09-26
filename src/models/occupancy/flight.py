"""Модуль «Перелёт»."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class FlightDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "flight_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    airline: Mapped[str | None] = mapped_column(String(200))
    flight_number: Mapped[str | None] = mapped_column(String(50))
    departure_airport: Mapped[str | None] = mapped_column(String(200))
    arrival_airport: Mapped[str | None] = mapped_column(String(200))
    departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FlightCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    airline: str | None = None
    flight_number: str | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
    departure_at: datetime | None = None
    arrival_at: datetime | None = None


class FlightUpdate(BaseModel):
    airline: str | None = None
    flight_number: str | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
    departure_at: datetime | None = None
    arrival_at: datetime | None = None


@register_occupancy_type
class FlightModule(OccupancyModule):
    type_name = "flight"
    label = "Перелёт"
    detail_model = FlightDetail
    create_schema = FlightCreate
    update_schema = FlightUpdate
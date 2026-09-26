"""Модуль «Поездка на такси»."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class TaxiDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "taxi_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    pickup_address: Mapped[str | None] = mapped_column(String(500))
    dropoff_address: Mapped[str | None] = mapped_column(String(500))
    ride_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaxiCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pickup_address: str | None = None
    dropoff_address: str | None = None
    ride_at: datetime | None = None


class TaxiUpdate(BaseModel):
    pickup_address: str | None = None
    dropoff_address: str | None = None
    ride_at: datetime | None = None


@register_occupancy_type
class TaxiModule(OccupancyModule):
    type_name = "taxi"
    label = "Поездка на такси"
    detail_model = TaxiDetail
    create_schema = TaxiCreate
    update_schema = TaxiUpdate
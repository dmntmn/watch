"""Модуль «Гостиница»."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.occupancy.base import OccupancyModule, register_occupancy_type


class HotelDetail(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "hotel_details"

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_periods.id", ondelete="CASCADE"), unique=True
    )
    hotel_name: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(500))
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class HotelCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hotel_name: str | None = None
    city: str | None = None
    address: str | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None


class HotelUpdate(BaseModel):
    hotel_name: str | None = None
    city: str | None = None
    address: str | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None


@register_occupancy_type
class HotelModule(OccupancyModule):
    type_name = "hotel"
    label = "Гостиница"
    detail_model = HotelDetail
    create_schema = HotelCreate
    update_schema = HotelUpdate
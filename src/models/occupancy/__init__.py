"""Реестр модулей видов занятости.

Импорт этого пакета регистрирует все модули в OCCUPANCY_REGISTRY.
"""
from src.models.occupancy.base import (  # noqa: F401
    OCCUPANCY_REGISTRY,
    OccupancyModule,
    get_module,
    register_occupancy_type,
)
from src.models.occupancy.flight import FlightModule  # noqa: F401
from src.models.occupancy.hotel import HotelModule  # noqa: F401
from src.models.occupancy.other import OtherModule  # noqa: F401
from src.models.occupancy.shift import ShiftModule  # noqa: F401
from src.models.occupancy.sick_leave import SickLeaveModule  # noqa: F401
from src.models.occupancy.taxi import TaxiModule  # noqa: F401
from src.models.occupancy.train import TrainModule  # noqa: F401
from src.models.occupancy.vacation import VacationModule  # noqa: F401

__all__ = [
    "OCCUPANCY_REGISTRY",
    "OccupancyModule",
    "get_module",
    "register_occupancy_type",
    "FlightModule",
    "HotelModule",
    "OtherModule",
    "ShiftModule",
    "SickLeaveModule",
    "TaxiModule",
    "TrainModule",
    "VacationModule",
]
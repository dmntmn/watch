"""Unified occupancy module interface and registry.

Каждый вид занятости — унифицированный модуль: собственная таблица деталей
(1:1 с employment_periods), собственные Pydantic-схемы и правила валидации.
Новый вид добавляется файлом-модулем + декоратором @register_occupancy_type.
"""
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

from src.models.base import Base

TModel = TypeVar("TModel", bound=Base)


class OccupancyModule:
    """Базовый класс модуля вида занятости."""

    type_name: str = ""
    label: str = ""
    detail_model: type[TModel] | None = None
    create_schema: type[BaseModel] | None = None
    update_schema: type[BaseModel] | None = None

    def validate(self, payload: BaseModel, period: Any) -> None:
        """Доменные проверки специфичные для вида (переопределяется в модуле)."""

    def to_view(self, period: Any, detail: TModel | None) -> dict[str, Any]:
        """Сериализация периода + деталей для REST/Socket.IO (переопределяется)."""
        return {"period_id": str(period.id), "period_type": self.type_name}


OCCUPANCY_REGISTRY: dict[str, OccupancyModule] = {}


def register_occupancy_type(cls: type[OccupancyModule]) -> type[OccupancyModule]:
    """Класс-декоратор: регистрирует модуль в реестре."""
    if not cls.type_name or not cls.detail_model:
        raise ValueError(f"Occupancy module {cls.__name__} must define type_name and detail_model")
    OCCUPANCY_REGISTRY[cls.type_name] = cls()
    return cls


def get_module(type_name: str) -> OccupancyModule:
    try:
        return OCCUPANCY_REGISTRY[type_name]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown occupancy type: {type_name}")
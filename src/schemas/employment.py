"""Схемы периодов занятости."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.models.employment_period import PeriodType
from src.schemas.common import ORMModel


class EmploymentPeriodCreate(BaseModel):
    employee_id: uuid.UUID
    period_type: PeriodType
    started_at: datetime
    ended_at: datetime | None = None
    # Детали конкретного вида (поля зависят от модуля, см. update_schema модуля)
    details: dict[str, Any] = Field(default_factory=dict)


class EmploymentPeriodUpdate(BaseModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None
    update_reason: str = "обновлен"
    details: dict[str, Any] | None = None


class EmploymentPeriodDelete(BaseModel):
    update_reason: str = "удален"


class EmploymentPeriodOut(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    period_type: str
    started_at: datetime
    ended_at: datetime | None
    version: int
    active: bool
    update_reason: str | None
    updated_by: uuid.UUID | None
    detail: dict[str, Any] | None = None
    financial_records: list[dict[str, Any]] = []
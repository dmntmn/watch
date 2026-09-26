"""Общие Pydantic-схемы."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EmployeeRef(ORMModel):
    id: uuid.UUID
    email: str
    first_name: str
    surname: str


class PeriodRef(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    period_type: str
    started_at: datetime
    ended_at: datetime | None


class ViewWindow(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime


class MessageResponse(BaseModel):
    message: str
"""Схемы проектов, месторождений и назначений сотрудников."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class FieldCreate(BaseModel):
    name: str = Field(min_length=1)


class FieldUpdate(BaseModel):
    name: str | None = None


class FieldOut(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str


class ProjectEmployeeAssign(BaseModel):
    employee_id: uuid.UUID


class ProjectEmployeeOut(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID
    employee_id: uuid.UUID
    assigned_by: uuid.UUID | None
    created_at: datetime
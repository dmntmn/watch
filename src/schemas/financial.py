"""Схемы финансовых записей и вложений."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.models.financial import FinancialKind
from src.schemas.common import ORMModel


class FinancialRecordCreate(BaseModel):
    kind: FinancialKind
    amount: float = Field(gt=0)
    description: str | None = None


class FinancialRecordUpdate(BaseModel):
    kind: FinancialKind | None = None
    amount: float | None = Field(default=None, gt=0)
    description: str | None = None


class FinancialRecordOut(ORMModel):
    id: uuid.UUID
    period_id: uuid.UUID
    kind: str
    amount: float
    description: str | None
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
    created_at: datetime


class AttachmentOut(ORMModel):
    id: uuid.UUID
    record_id: uuid.UUID
    file_name: str
    content_type: str | None
    size_bytes: int
    uploaded_by: uuid.UUID | None
    created_at: datetime
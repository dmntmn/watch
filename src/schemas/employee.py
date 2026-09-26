"""Схемы сотрудников и их суб-записей."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.common import ORMModel


class EmployeeBase(BaseModel):
    email: EmailStr
    phone: str | None = None
    first_name: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    patronymic: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    first_name: str | None = None
    surname: str | None = None
    patronymic: str | None = None


class EmployeeOut(EmployeeBase, ORMModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# --- Суб-записи ---

class EmployeeEducationCreate(BaseModel):
    title: str
    institution: str | None = None
    graduated_at: int | None = None


class EmployeeEducationUpdate(BaseModel):
    title: str | None = None
    institution: str | None = None
    graduated_at: int | None = None


class EmployeeEducationOut(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    title: str
    institution: str | None
    graduated_at: int | None


class EmployeeCertificationCreate(BaseModel):
    title: str
    issued_at: date | None = None
    expires_at: date | None = None


class EmployeeCertificationUpdate(BaseModel):
    title: str | None = None
    issued_at: date | None = None
    expires_at: date | None = None


class EmployeeCertificationOut(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    title: str
    issued_at: date | None
    expires_at: date | None


class EmployeeMedicalExamCreate(BaseModel):
    exam_date: date
    expires_at: date | None = None
    conclusion: str | None = None


class EmployeeMedicalExamUpdate(BaseModel):
    exam_date: date | None = None
    expires_at: date | None = None
    conclusion: str | None = None


class EmployeeMedicalExamOut(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    exam_date: date
    expires_at: date | None
    conclusion: str | None


class EmployeePPECreate(BaseModel):
    item_name: str
    issued_at: date
    expires_at: date | None = None


class EmployeePPEUpdate(BaseModel):
    item_name: str | None = None
    issued_at: date | None = None
    expires_at: date | None = None


class EmployeePPEOut(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    item_name: str
    issued_at: date
    expires_at: date | None
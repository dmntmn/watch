"""Employees (workers) master data.

Workers have NO access to the system itself; they only receive email
notifications. Sub-records carry optional expiry dates (срок давности):
certifications, medical exams, PPE / workwear issuance.
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.project import Project


class Employee(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employees"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str] = mapped_column(String(255))
    surname: Mapped[str] = mapped_column(String(255))
    patronymic: Mapped[str | None] = mapped_column(String(255))

    projects: Mapped[list["Project"]] = relationship(
        secondary="project_employees",
        back_populates="employees",
    )
    educations: Mapped[list["EmployeeEducation"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["EmployeeCertification"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    medical_exams: Mapped[list["EmployeeMedicalExam"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    ppe_records: Mapped[list["EmployeePPERecord"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )


class EmployeeEducation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employee_educations"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    institution: Mapped[str | None] = mapped_column(String(500))
    graduated_at: Mapped[int | None]  # год окончания

    employee: Mapped[Employee] = relationship(back_populates="educations")


class EmployeeCertification(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employee_certifications"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    issued_at: Mapped[date | None] = mapped_column(Date)
    expires_at: Mapped[date | None] = mapped_column(Date)  # срок давности

    employee: Mapped[Employee] = relationship(back_populates="certifications")


class EmployeeMedicalExam(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employee_medical_exams"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    exam_date: Mapped[date] = mapped_column(Date)
    expires_at: Mapped[date | None] = mapped_column(Date)  # срок давности
    conclusion: Mapped[str | None] = mapped_column(Text)

    employee: Mapped[Employee] = relationship(back_populates="medical_exams")


class EmployeePPERecord(UUIDMixin, TimestampMixin, Base):
    """Выдача средств индивидуальной защиты и спецодежды."""

    __tablename__ = "employee_ppe_records"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    item_name: Mapped[str] = mapped_column(String(500))
    issued_at: Mapped[date] = mapped_column(Date)
    expires_at: Mapped[date | None] = mapped_column(Date)  # срок давности

    employee: Mapped[Employee] = relationship(back_populates="ppe_records")
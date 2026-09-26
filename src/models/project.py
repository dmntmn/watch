"""Projects, fields (месторождения) and employee-to-project assignments."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.employee import Employee


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)

    fields: Mapped[list["Field"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    employees: Mapped[list["Employee"]] = relationship(
        secondary="project_employees",
        back_populates="projects",
    )


class Field(UUIDMixin, TimestampMixin, Base):
    """Месторождение — часть проекта. Вахты ведутся на месторождениях."""

    __tablename__ = "fields"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(500))

    project: Mapped[Project] = relationship(back_populates="fields")


class ProjectEmployee(UUIDMixin, TimestampMixin, Base):
    """Назначение работника на проект (доступ к проекту для работника)."""

    __tablename__ = "project_employees"
    __table_args__ = (UniqueConstraint("project_id", "employee_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
"""Audit log — every insert/update/delete is recorded with the author."""
import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDMixin


class AuditAction(str, enum.Enum):
    insert = "insert"
    update = "update"
    delete = "delete"


class AuditLog(UUIDMixin, Base):
    __tablename__ = "audit_logs"

    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action"), nullable=False
    )
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
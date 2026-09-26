"""System users — synced from Keycloak on every authenticated request."""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    keycloak_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))

    # Группы Keycloak (claim "groups"), например ["/personnel-managers", ...]
    groups: Mapped[list[Any]] = mapped_column(JSONB, default=list)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User sub={self.keycloak_sub} email={self.email}>"


# Foreign keys to users.id used across the schema
UserID = uuid.UUID
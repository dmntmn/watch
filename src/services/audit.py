"""Audit logging via SQLAlchemy event listeners.

Любые изменения данных (insert/update/delete) любой таблицы автоматически
фиксируются в audit_logs вместе с автором. Автор берётся из contextvar,
который заполняется auth-dependency (set_actor) на время запроса.
"""
import contextvars
import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any

import sqlalchemy as sa
from sqlalchemy import event, inspect

from src.models.audit import AuditAction, AuditLog
from src.models.base import Base

# Текущий автор изменения (UUID пользователя или None — системная операция)
current_actor: contextvars.ContextVar[uuid.UUID | None] = contextvars.ContextVar(
    "current_actor", default=None
)


def set_actor(actor_id: uuid.UUID | None) -> None:
    current_actor.set(actor_id)


def get_actor() -> uuid.UUID | None:
    return current_actor.get()


def _serialize(value: Any) -> Any:
    if isinstance(value, (datetime, date, uuid.UUID)):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(v) for v in value]
    return value


def _to_dict(instance: Any) -> dict[str, Any]:
    return {
        c.key: _serialize(getattr(instance, c.key))
        for c in instance.__table__.columns
    }


def _write_audit(
    connection: sa.Connection,
    target: Any,
    action: AuditAction,
    old_values: dict[str, Any] | None,
    new_values: dict[str, Any] | None,
) -> None:
    connection.execute(
        sa.insert(AuditLog).values(
            entity_type=target.__tablename__,
            entity_id=str(getattr(target, "id", "")),
            action=action,
            old_values=old_values,
            new_values=new_values,
            actor_id=get_actor(),
            created_at=datetime.now(timezone.utc),
        )
    )


@event.listens_for(Base, "after_insert", propagate=True)
def _after_insert(mapper: Any, connection: sa.Connection, target: Any) -> None:
    if isinstance(target, AuditLog):
        return
    _write_audit(connection, target, AuditAction.insert, None, _to_dict(target))


@event.listens_for(Base, "after_update", propagate=True)
def _after_update(mapper: Any, connection: sa.Connection, target: Any) -> None:
    if isinstance(target, AuditLog):
        return
    state = inspect(target)
    changed = {}
    for attr_name in state.attrs.keys():
        history = state.attrs[attr_name].history
        if history.has_changes() and history.deleted:
            changed[attr_name] = _serialize(history.deleted[0])
    if not changed:
        return
    new_values = {
        c.key: _serialize(getattr(target, c.key)) for c in target.__table__.columns
    }
    _write_audit(connection, target, AuditAction.update, changed, new_values)


@event.listens_for(Base, "after_delete", propagate=True)
def _after_delete(mapper: Any, connection: sa.Connection, target: Any) -> None:
    if isinstance(target, AuditLog):
        return
    _write_audit(connection, target, AuditAction.delete, _to_dict(target), None)
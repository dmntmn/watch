"""REST: /audit-logs — история изменений данных (автор, old/new значения)."""
import uuid
from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, DBSession
from src.models.audit import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[dict[str, Any]])
async def list_audit_logs(
    db: DBSession,
    user: CurrentUser,
    entity: str | None = Query(default=None, description="Имя таблицы, например employment_periods"),
    entity_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if entity:
        query = query.where(AuditLog.entity_type == entity)
    if entity_id:
        query = query.where(AuditLog.entity_id == str(entity_id))
    if action:
        query = query.where(AuditLog.action == action)

    rows = (await db.execute(query)).scalars().all()
    return [
        {
            "id": str(row.id),
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "action": row.action.value,
            "old_values": row.old_values,
            "new_values": row.new_values,
            "actor_id": str(row.actor_id) if row.actor_id else None,
            "created_at": str(row.created_at),
        }
        for row in rows
    ]
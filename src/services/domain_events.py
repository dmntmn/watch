"""Публикация доменных событий в Redis pub/sub (после успешного commit)."""
from typing import Any

from src.sockets.events_bus import event_bus


async def publish(
    entity: str,
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    period_start: Any = None,
    period_end: Any = None,
    project_ids: list[Any] | None = None,
) -> None:
    event: dict[str, Any] = {
        "entity": entity,
        "action": action,
        "payload": payload,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "project_ids": [str(p) for p in (project_ids or [])],
    }
    await event_bus.publish(event)
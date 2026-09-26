"""In-memory subscription manager for Socket.IO live views.

Хранит подписки слушателей (sid) с фильтрами окна просмотра.
При приходе доменного события (из Redis pub/sub) определяет, какие sid
должны получить data:changed.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class ViewSubscription:
    sid: str
    user_id: uuid.UUID
    from_dt: datetime
    to_dt: datetime
    project_ids: list[uuid.UUID] | None = None
    filters: dict[str, Any] = field(default_factory=dict)

    def overlaps(self, event: dict[str, Any]) -> bool:
        """Пересекается ли событие с окном просмотра подписчика."""
        # Скоуп по проектам: если подписчик ограничен проектами, событие
        # должно попадать хотя бы в один из них. Пустой список проектов у
        # события трактуем как общесистемное событие.
        if self.project_ids:
            event_projects = [uuid.UUID(p) for p in (event.get("project_ids") or [])]
            if event_projects and not set(event_projects) & set(self.project_ids):
                return False

        period_start = _parse_dt(event.get("period_start"))
        period_end = _parse_dt(event.get("period_end"))

        if period_start is None:
            return True  # не-периодическая сущность (employee/project и т.п.)

        # Пересечение [period_start, period_end] с [from_dt, to_dt]:
        # NOT (period_end < from) AND NOT (period_start > to)
        if period_end is not None and period_end < self.from_dt:
            return False
        if period_start > self.to_dt:
            return False
        return True


class SubscriptionManager:
    def __init__(self) -> None:
        self._subscriptions: dict[str, ViewSubscription] = {}
        self._users: dict[str, uuid.UUID] = {}

    def set_user(self, sid: str, user_id: uuid.UUID) -> None:
        self._users[sid] = user_id

    def get_user(self, sid: str) -> uuid.UUID | None:
        return self._users.get(sid)

    def subscribe(self, sid: str, subscription: ViewSubscription) -> None:
        self._subscriptions[sid] = subscription

    def unsubscribe(self, sid: str) -> None:
        self._subscriptions.pop(sid, None)
        self._users.pop(sid, None)

    def matching_sids(self, event: dict[str, Any]) -> list[str]:
        return [sid for sid, sub in self._subscriptions.items() if sub.overlaps(event)]

    def clear(self) -> None:
        self._subscriptions.clear()
        self._users.clear()


subscription_manager = SubscriptionManager()
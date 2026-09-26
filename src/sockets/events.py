"""Socket.IO сервер: аутентификация по токену, подписка на просмотр,
live-доставка изменений через Redis pub/sub (data:changed).
"""
import logging
import uuid
from typing import Any

import socketio

from src.config import get_settings
from src.database import async_session_factory
from src.models.user import User
from src.services import audit
from src.services.auth import TokenValidationError, decode_token, sync_user
from src.services.view_service import build_snapshot, month_window, parse_dt
from src.sockets.events_bus import event_bus
from src.sockets.manager import ViewSubscription, subscription_manager

logger = logging.getLogger(__name__)

settings = get_settings()

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins,
)


async def _authenticate(auth: dict[str, Any] | None) -> User:
    """Проверяет токен и синхронизирует пользователя в БД."""
    token = (auth or {}).get("token")
    if not token:
        raise ConnectionRefusedError("Missing token")
    try:
        claims = decode_token(token)
    except TokenValidationError as exc:
        raise ConnectionRefusedError(f"Invalid token: {exc}") from exc

    async with async_session_factory() as db:
        user = await sync_user(db, claims)
        await db.commit()
        return user


@sio.event
async def connect(sid: str, environ: dict, auth: dict[str, Any] | None = None) -> bool:
    user = await _authenticate(auth)
    subscription_manager.set_user(sid, user.id)
    audit.set_actor(user.id)
    logger.info("Socket connected: sid=%s user=%s", sid, user.id)
    await sio.emit("connected", {"user_id": str(user.id)}, room=sid)
    return True


@sio.event
async def disconnect(sid: str) -> None:
    subscription_manager.unsubscribe(sid)
    logger.info("Socket disconnected: sid=%s", sid)


@sio.on("view:init")
async def on_view_init(sid: str, data: dict[str, Any]) -> None:
    """Инициализация просмотра: окно [from, to] + первичный snapshot."""
    try:
        default_from, default_to = month_window()
        from_dt = parse_dt(data["from"]) if data.get("from") else default_from
        to_dt = parse_dt(data["to"]) if data.get("to") else default_to
        project_ids = data.get("project_ids")

        async with async_session_factory() as db:
            snapshot = await build_snapshot(db, from_dt, to_dt, project_ids)

        user_id = subscription_manager.get_user(sid)
        subscription_manager.subscribe(
            sid,
            ViewSubscription(
                sid=sid,
                user_id=user_id or uuid.UUID(int=0),
                from_dt=from_dt,
                to_dt=to_dt,
                project_ids=project_ids,
                filters=data,
            ),
        )
        await sio.emit("view:snapshot", snapshot, room=sid)
    except Exception as exc:  # noqa: BLE001
        logger.exception("view:init failed")
        await sio.emit("view:error", {"message": str(exc)}, room=sid)


@sio.on("view:close")
async def on_view_close(sid: str, data: dict[str, Any] | None = None) -> None:
    subscription_manager.unsubscribe(sid)
    await sio.emit("view:closed", {"ok": True}, room=sid)


async def _on_domain_event(event: dict[str, Any]) -> None:
    """Подписчик Redis pub/sub: рассылка data:changed слушателям с
    пересекающимися фильтрами (каждый инстанс — своим клиентам)."""
    matching = subscription_manager.matching_sids(event)
    for sid in matching:
        await sio.emit("data:changed", event, room=sid)
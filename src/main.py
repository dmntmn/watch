"""Точка входа: FastAPI (REST /api/v1) + Socket.IO (live-обновления).

Схема работы:
- REST: каждый запрос валидирует Keycloak JWT (JWKS), синхронизирует
  пользователя в users и фиксирует автора для аудита.
- Изменения после commit публикуются в Redis-канал (EventBus).
- Каждый инстанс подписан на канал и рассылает data:changed своим
  Socket.IO клиентам (см. src/sockets/events.py).
"""
import asyncio
import logging
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.config import get_settings
from src.services import audit  # noqa: F401  — регистрация event listeners аудита
from src.services.storage import storage
from src.sockets.events import _on_domain_event, sio
from src.sockets.events_bus import event_bus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redis pub/sub шина событий
    await event_bus.connect()
    await event_bus.start_listener(_on_domain_event)
    # S3-бакет для вложений (не блокируем старт, если S3 недоступен)
    try:
        await asyncio.wait_for(storage.ensure_bucket(), timeout=5)
    except Exception:  # noqa: BLE001
        logger.warning("S3 bucket check failed or timed out (startup continues)", exc_info=True)
    yield
    await event_bus.close()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


# Совмещённый ASGI: HTTP (FastAPI) + WebSocket (Socket.IO)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

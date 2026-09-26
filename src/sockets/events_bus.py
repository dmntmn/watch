"""Redis pub/sub domain event bus.

Сервисы после успешного commit публикуют доменное событие в Redis-канал;
каждый инстанс приложения подписан на канал и пересылает событие своим
подключённым Socket.IO клиентам (см. src/sockets/events.py).
"""
import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import redis.asyncio as aioredis

from src.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self, redis_url: str, channel: str) -> None:
        self._redis_url = redis_url
        self._channel = channel
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._task: asyncio.Task | None = None
        self._handler: EventHandler | None = None

    async def connect(self) -> None:
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)

    async def ensure_channel(self) -> None:
        pass  # pub/sub каналы создаются автоматически при подписке

    async def start_listener(self, handler: EventHandler) -> None:
        """Запускает фоновую подписку на канал (по одному слушателю на инстанс)."""
        assert self._redis is not None, "EventBus.connect() must be called first"
        self._handler = handler
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self._channel)
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("EventBus: subscribed to %s", self._channel)

    async def _listen_loop(self) -> None:
        assert self._pubsub is not None
        try:
            async for message in self._pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    if self._handler is not None:
                        await self._handler(data)
                except Exception:  # noqa: BLE001 — не роняем подписчика
                    logger.exception("EventBus: failed to handle event")
        except asyncio.CancelledError:
            pass

    async def publish(self, event: dict[str, Any]) -> None:
        """Публикует событие в канал (JSON-сериализация с default=str для UUID/datetime)."""
        if self._redis is None:
            return
        try:
            await self._redis.publish(self._channel, json.dumps(event, default=str))
        except Exception:  # noqa: BLE001
            logger.exception("EventBus: publish failed")

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._pubsub is not None:
            await self._pubsub.unsubscribe(self._channel)
            await self._pubsub.aclose()
        if self._redis is not None:
            await self._redis.aclose()


# Singleton шины (запуск/остановка — в src/main.py)
event_bus = EventBus(settings.redis_url, settings.events_channel)
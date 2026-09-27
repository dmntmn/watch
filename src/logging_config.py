"""Централизованная конфигурация логирования для всего приложения.

Единая точка настройки: уровень, формат (text/JSON), подавление шума
сторонних библиотек. Используйте хелпер ``get_logger`` в любом модуле —
конфигурация применится автоматически, даже если ``setup_logging`` ещё
не вызывался (скрипты, тесты, отдельные сервисы).

Пример:
    from src.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("period created", extra={"period_id": str(period.id)})
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.config import get_settings

_configured = False

# Поля, которые не попадают в JSON-вывод (стандартные атрибуты LogRecord).
_RESERVED_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
}

# Сторонние логгеры, которые шумят на INFO — приглушаем до WARNING.
_QUIET_LOGGERS = {
    "sqlalchemy.engine": logging.WARNING,
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "aiobotocore": logging.WARNING,
    "botocore": logging.WARNING,
    "socketio": logging.WARNING,
    "engineio": logging.WARNING,
}


class TextFormatter(logging.Formatter):
    """Компактный человекочитаемый формат: время | уровень | логгер | сообщение."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone()
        return dt.isoformat(timespec="milliseconds")

    def format(self, record: logging.LogRecord) -> str:
        base = f"{self.formatTime(record)} | {record.levelname:<8} | {record.name} | {record.getMessage()}"
        # Дополнительные поля из extra={...}
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_ATTRS and not key.startswith("_")
        }
        if extras:
            base += f" | {extras}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


class JsonFormatter(logging.Formatter):
    """Структурированный JSON-вывод для агрегаторов логов (ELK, Loki и т.п.).

    Все значения из ``extra={...}`` попадают в объект верхнего уровня.
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone()
        return dt.isoformat(timespec="milliseconds")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    resolved = logging.getLevelName(str(level).upper())
    return resolved if isinstance(resolved, int) else logging.INFO


def setup_logging(
    *,
    level: str | int | None = None,
    log_format: str | None = None,
    force: bool = False,
) -> None:
    """Применяет единую конфигурацию логирования (идемпотентно).

    Параметры берутся из настроек приложения (``LOG_LEVEL`` / ``LOG_FORMAT``),
    но могут быть переопределены аргументами. ``force=True`` позволяет
    перенастроить логирование повторно (например, в тестах).
    """
    global _configured
    if _configured and not force:
        return

    settings = get_settings()
    resolved_level = _resolve_level(level if level is not None else settings.log_level)
    fmt = (log_format or settings.log_format or "text").lower()

    root = logging.getLogger()
    root.setLevel(resolved_level)

    # Убираем ранее установленные нами обработчики (чтобы не дублировать вывод)
    for handler in list(root.handlers):
        if getattr(handler, "_watch_managed", False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if fmt == "json" else TextFormatter())
    handler.setLevel(logging.NOTSET)
    handler._watch_managed = True  # type: ignore[attr-defined]
    root.addHandler(handler)

    # Приглушаем шумные сторонние логгеры
    for name, quiet_level in _QUIET_LOGGERS.items():
        logging.getLogger(name).setLevel(quiet_level)

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Возвращает логгер с гарантированно применённой центральной конфигурацией.

    ``name`` обычно передавайте как ``__name__`` модуля — тогда в логах будет
    видна иерархия (например, ``src.services.notifications``).
    """
    setup_logging()
    return logging.getLogger(name or "watch")
"""Email notifications to workers (employees have no system access).

Триггеры: создание/изменение/мягкое удаление периода занятости,
добавление финансовых записей. Письма отправляются через SMTP
(текстовые шаблоны).
"""
import logging
from datetime import datetime
from typing import Any

import aiosmtplib

from src.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class EmailNotifier:
    def __init__(self) -> None:
        self._settings = settings

    async def send(self, to_email: str, subject: str, body: str) -> None:
        """Отправляет текстовое письмо; ошибки не роняют основной поток."""
        try:
            await aiosmtplib.send(
                message=(
                    f"From: {self._settings.smtp_from}\r\n"
                    f"To: {to_email}\r\n"
                    f"Subject: {subject}\r\n"
                    "MIME-Version: 1.0\r\n"
                    "Content-Type: text/plain; charset=utf-8\r\n"
                    "\r\n"
                    f"{body}"
                ),
                hostname=self._settings.smtp_host,
                port=self._settings.smtp_port,
                username=self._settings.smtp_user or None,
                password=self._settings.smtp_password or None,
                use_tls=self._settings.smtp_tls,
                start_tls=self._settings.smtp_starttls,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
        except Exception:  # noqa: BLE001
            logger.exception("Email to %s failed: %s", to_email, subject)


notifier = EmailNotifier()


# --- Текстовые шаблоны ---

def _fmt_dt(value: datetime | None) -> str:
    return value.strftime("%d.%m.%Y %H:%M") if value else "—"


def period_created_email(employee: Any, period: Any) -> tuple[str, str]:
    subject = "Новый период занятости"
    body = (
        f"Здравствуйте, {employee.first_name} {employee.surname}!\n\n"
        f"Для вас зарегистрирован новый период занятости:\n"
        f"  Вид: {period.period_type.value}\n"
        f"  Начало: {_fmt_dt(period.started_at)}\n"
        f"  Окончание: {_fmt_dt(period.ended_at)}\n"
    )
    return subject, body


def period_updated_email(employee: Any, period: Any, reason: str) -> tuple[str, str]:
    subject = "Период занятости изменён"
    body = (
        f"Здравствуйте, {employee.first_name} {employee.surname}!\n\n"
        f"Ваш период занятости изменён ({reason}):\n"
        f"  Вид: {period.period_type.value}\n"
        f"  Начало: {_fmt_dt(period.started_at)}\n"
        f"  Окончание: {_fmt_dt(period.ended_at)}\n"
    )
    return subject, body


def financial_added_email(employee: Any, record: Any) -> tuple[str, str]:
    subject = "Добавлена финансовая запись"
    kind = "доход" if record.kind.value == "income" else "расход"
    body = (
        f"Здравствуйте, {employee.first_name} {employee.surname}!\n\n"
        f"По вашему периоду занятости добавлена запись:\n"
        f"  Тип: {kind}\n"
        f"  Сумма: {record.amount:.2f}\n"
        f"  Описание: {record.description or '—'}\n"
    )
    return subject, body
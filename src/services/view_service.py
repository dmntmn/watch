"""View snapshot service.

При инициализации просмотра пользователь указывает дату/время начала (from)
и опционально окончание (to); по умолчанию окно — текущий месяц.
Возвращаются все периоды занятости, пересекающиеся с окном
(включая начатые ранее и продолжающиеся в окне), вместе со связанными
данными: сотрудники, проекты, месторождения, финансы.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.employee import Employee
from src.models.employment_period import EmploymentPeriod
from src.models.financial import FinancialRecord
from src.models.occupancy import get_module
from src.models.project import Field, Project

MODEL_VIEW_FIELDS = {
    "employees": ("id", "email", "phone", "first_name", "surname", "patronymic"),
    "projects": ("id", "name", "description"),
    "fields": ("id", "project_id", "name"),
}


def _to_str(value: Any) -> Any:
    if isinstance(value, (datetime, uuid.UUID)):
        return str(value)
    return value


def _row_view(model: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {name: _to_str(getattr(model, name)) for name in fields}


def ensure_tz(dt: datetime) -> datetime:
    """Нормализует naive datetime к UTC (все сравнения — timezone-aware)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_dt(value: str) -> datetime:
    return ensure_tz(datetime.fromisoformat(value))


def month_window() -> tuple[datetime, datetime]:
    """Окно просмотра по умолчанию: весь текущий месяц (UTC)."""
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def serialize_period(
    period: EmploymentPeriod,
    detail: Any | None = None,
    financial_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Единая сериализация периода занятости (REST + Socket.IO + snapshot)."""
    base = {
        "id": str(period.id),
        "employee_id": str(period.employee_id),
        "period_type": period.period_type.value,
        "started_at": str(period.started_at),
        "ended_at": str(period.ended_at) if period.ended_at else None,
        "version": period.version,
        "active": period.active,
        "update_reason": period.update_reason,
        "updated_by": str(period.updated_by) if period.updated_by else None,
    }
    return {
        **base,
        "detail": _detail_to_dict(detail) if detail is not None else None,
        "financial_records": financial_records or [],
    }


def _detail_to_dict(detail: Any) -> dict[str, Any] | None:
    data: dict[str, Any] = {}
    for c in detail.__table__.columns:
        if c.key in ("id", "created_at", "updated_at", "period_id"):
            continue
        data[c.key] = _to_str(getattr(detail, c.key))
    return data


def _financial_view(records: list[FinancialRecord]) -> dict[uuid.UUID, list[dict[str, Any]]]:
    grouped: dict[uuid.UUID, list[dict[str, Any]]] = {}
    for rec in records:
        grouped.setdefault(rec.period_id, []).append(
            {
                "id": str(rec.id),
                "kind": rec.kind.value,
                "amount": rec.amount,
                "description": rec.description,
                "created_by": str(rec.created_by) if rec.created_by else None,
                "updated_by": str(rec.updated_by) if rec.updated_by else None,
            }
        )
    return grouped


async def build_snapshot(
    db: AsyncSession,
    from_dt: datetime,
    to_dt: datetime,
    project_ids: list[uuid.UUID] | None = None,
) -> dict[str, Any]:
    """Собирает полный snapshot данных за окно просмотра."""

    # --- Проекты и месторождения (скоуп по проектам) ---
    projects_q = select(Project)
    fields_q = select(Field)
    if project_ids:
        projects_q = projects_q.where(Project.id.in_(project_ids))
        fields_q = fields_q.where(Field.project_id.in_(project_ids))
    projects = (await db.execute(projects_q.order_by(Project.name))).scalars().all()
    fields = (await db.execute(fields_q.order_by(Field.name))).scalars().all()

    # --- Периоды занятости, пересекающиеся с окном ---
    overlap = or_(
        EmploymentPeriod.ended_at.is_(None),
        EmploymentPeriod.ended_at >= from_dt,
    ) & (EmploymentPeriod.started_at <= to_dt)
    periods_q = select(EmploymentPeriod).where(
        EmploymentPeriod.active.is_(True), overlap
    )
    periods = (await db.execute(periods_q)).scalars().all()

    # --- Детали типов через реестр модулей ---
    details_by_period: dict[uuid.UUID, Any] = {}
    types_present: dict[str, list[uuid.UUID]] = {}
    for p in periods:
        types_present.setdefault(p.period_type.value, []).append(p.id)

    for type_name, period_ids in types_present.items():
        module = get_module(type_name)
        model = module.detail_model
        rows = (
            await db.execute(select(model).where(model.period_id.in_(period_ids)))
        ).scalars().all()
        for row in rows:
            details_by_period[row.period_id] = row

    # --- Финансовые записи периодов ---
    financial: dict[uuid.UUID, list[dict[str, Any]]] = {}
    if periods:
        records = (
            await db.execute(
                select(FinancialRecord).where(
                    FinancialRecord.period_id.in_([p.id for p in periods])
                )
            )
        ).scalars().all()
        financial = _financial_view(records)

    # --- Сотрудники (только те, у кого есть периоды в окне) ---
    employee_ids = {p.employee_id for p in periods}
    employees: list[Employee] = []
    if employee_ids:
        employees_q = select(Employee).where(Employee.id.in_(employee_ids))
        employees = (await db.execute(employees_q)).scalars().all()

    periods_view = [
        serialize_period(p, details_by_period.get(p.id), financial.get(p.id, []))
        for p in periods
    ]

    return {
        "window": {"from": str(from_dt), "to": str(to_dt)},
        "projects": [_row_view(p, MODEL_VIEW_FIELDS["projects"]) for p in projects],
        "fields": [_row_view(f, MODEL_VIEW_FIELDS["fields"]) for f in fields],
        "employees": [_row_view(e, MODEL_VIEW_FIELDS["employees"]) for e in employees],
        "periods": periods_view,
    }
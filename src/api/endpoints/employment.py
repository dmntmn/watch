"""REST: /employment-periods — CRUD периодов занятости (группа распределения занятости).

Период хранится в единой таблице employment_periods; данные конкретного вида —
в таблице деталей соответствующего модуля (реестр OCCUPANCY_REGISTRY).
Изменения: version++ , update_reason, updated_by, активность (active).
"""
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, DBSession, RequireOccupancyManage
from src.models.employee import Employee
from src.models.employment_period import EmploymentPeriod
from src.models.financial import FinancialRecord
from src.models.occupancy import get_module
from src.models.project import Field
from src.schemas.common import PeriodRef
from src.schemas.employment import (
    EmploymentPeriodCreate,
    EmploymentPeriodDelete,
    EmploymentPeriodUpdate,
)
from src.services.domain_events import publish
from src.services.notifications import (
    notifier,
    period_created_email,
    period_updated_email,
)
from src.services.view_service import _financial_view, parse_dt, serialize_period

router = APIRouter(prefix="/employment-periods", tags=["employment-periods"])


async def _get_period_or_404(db: AsyncSession, period_id: uuid.UUID) -> EmploymentPeriod:
    period = await db.get(EmploymentPeriod, period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Employment period not found")
    return period


async def _load_detail(db: AsyncSession, period: EmploymentPeriod) -> Any | None:
    module = get_module(period.period_type.value)
    model = module.detail_model
    result = await db.execute(select(model).where(model.period_id == period.id))
    return result.scalar_one_or_none()


async def _resolve_project_ids(db: AsyncSession, period: EmploymentPeriod) -> list[uuid.UUID]:
    """Проект периода: для вахты — проект месторождения (shift_details.field.project)."""
    if period.period_type.value != "shift":
        return []
    detail = await _load_detail(db, period)
    if detail is None or getattr(detail, "field_id", None) is None:
        return []
    field = await db.get(Field, detail.field_id)
    return [field.project_id] if field else []


def _email_task_factory(employee: Employee, period: EmploymentPeriod, template: str, reason: str = ""):
    async def task() -> None:
        if template == "created":
            subject, body = period_created_email(employee, period)
        else:
            subject, body = period_updated_email(employee, period, reason)
        await notifier.send(employee.email, subject, body)

    return task


# --- Создание ---

@router.post("", response_model=PeriodRef, status_code=status.HTTP_201_CREATED)
async def create_period(
    payload: EmploymentPeriodCreate,
    background: BackgroundTasks,
    db: DBSession,
    user: RequireOccupancyManage,
) -> dict[str, Any]:
    module = get_module(payload.period_type.value)

    period = EmploymentPeriod(
        employee_id=payload.employee_id,
        period_type=payload.period_type,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        update_reason="создан",
        version=1,
        active=True,
        updated_by=user.id,
    )
    db.add(period)
    await db.flush()

    # Детали вида через схему модуля
    detail_data = None
    if payload.details:
        create_schema = module.create_schema
        if create_schema is None:
            raise HTTPException(status_code=400, detail=f"Type {module.type_name} has no detail schema")
        detail_payload = create_schema(**payload.details)
        module.validate(detail_payload, period)
        detail_data = module.detail_model(period_id=period.id, **detail_payload.model_dump())
        db.add(detail_data)

    await db.commit()
    await db.refresh(period)

    employee = await db.get(Employee, period.employee_id)
    if employee is not None:
        background.add_task(_email_task_factory(employee, period, "created"))

    project_ids = await _resolve_project_ids(db, period)
    await publish(
        "employment_period", "created",
        {"period": serialize_period(period, detail_data)},
        period_start=period.started_at,
        period_end=period.ended_at,
        project_ids=project_ids,
    )
    return PeriodRef.model_validate(period).model_dump(mode="json")


# --- Чтение ---

@router.get("", response_model=list[dict[str, Any]])
async def list_periods(
    db: DBSession,
    user: CurrentUser,
    from_: str | None = None,
    to: str | None = None,
) -> list[dict[str, Any]]:
    query = select(EmploymentPeriod).where(EmploymentPeriod.active.is_(True))
    if from_:
        from_dt = parse_dt(from_)
        query = query.where(
            or_(EmploymentPeriod.ended_at.is_(None), EmploymentPeriod.ended_at >= from_dt)
        )
    if to:
        to_dt = parse_dt(to)
        query = query.where(EmploymentPeriod.started_at <= to_dt)

    periods = (await db.execute(query.order_by(EmploymentPeriod.started_at))).scalars().all()
    result: list[dict[str, Any]] = []
    for p in periods:
        detail = await _load_detail(db, p)
        records = (
            await db.execute(
                select(FinancialRecord).where(FinancialRecord.period_id == p.id)
            )
        ).scalars().all()
        result.append(serialize_period(p, detail, _financial_view(records).get(p.id, [])))
    return result


@router.get("/{period_id}", response_model=dict[str, Any])
async def get_period(period_id: uuid.UUID, db: DBSession, user: CurrentUser) -> dict[str, Any]:
    period = await _get_period_or_404(db, period_id)
    detail = await _load_detail(db, period)
    records = (
        await db.execute(select(FinancialRecord).where(FinancialRecord.period_id == period.id))
    ).scalars().all()
    return serialize_period(period, detail, _financial_view(records).get(period.id, []))


# --- Обновление ---

@router.put("/{period_id}", response_model=dict[str, Any])
async def update_period(
    period_id: uuid.UUID,
    payload: EmploymentPeriodUpdate,
    background: BackgroundTasks,
    db: DBSession,
    user: RequireOccupancyManage,
) -> dict[str, Any]:
    period = await _get_period_or_404(db, period_id)
    module = get_module(period.period_type.value)

    for field in ("started_at", "ended_at"):
        value = getattr(payload, field)
        if value is not None:
            setattr(period, field, value)

    period.update_reason = payload.update_reason or "обновлен"
    period.updated_by = user.id
    period.version += 1
    await db.flush()

    # Обновление деталей вида (частично, по переданным полям)
    detail_data = await _load_detail(db, period)
    if payload.details:
        update_schema = module.update_schema
        if update_schema is None:
            raise HTTPException(status_code=400, detail=f"Type {module.type_name} has no detail schema")
        update_payload = update_schema(**payload.details)
        module.validate(update_payload, period)
        if detail_data is None:
            detail_data = module.detail_model(period_id=period.id)
            db.add(detail_data)
        for field, value in update_payload.model_dump(exclude_unset=True).items():
            setattr(detail_data, field, value)

    await db.commit()
    await db.refresh(period)

    employee = await db.get(Employee, period.employee_id)
    if employee is not None:
        background.add_task(
            _email_task_factory(employee, period, "updated", period.update_reason or "обновлен")
        )

    project_ids = await _resolve_project_ids(db, period)
    await publish(
        "employment_period", "updated",
        {"period": serialize_period(period, detail_data)},
        period_start=period.started_at,
        period_end=period.ended_at,
        project_ids=project_ids,
    )
    return serialize_period(period, detail_data)


# --- Мягкое удаление ---

@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_period(
    period_id: uuid.UUID,
    background: BackgroundTasks,
    db: DBSession,
    user: RequireOccupancyManage,
    payload: EmploymentPeriodDelete | None = None,
) -> None:
    period = await _get_period_or_404(db, period_id)
    period.active = False
    period.update_reason = (payload.update_reason if payload else None) or "удален"
    period.updated_by = user.id
    period.version += 1
    await db.commit()

    employee = await db.get(Employee, period.employee_id)
    if employee is not None:
        background.add_task(_email_task_factory(employee, period, "updated", "удален"))

    project_ids = await _resolve_project_ids(db, period)
    await publish(
        "employment_period", "deleted",
        {"period_id": str(period_id)},
        period_start=period.started_at,
        period_end=period.ended_at,
        project_ids=project_ids,
    )


# --- Детали типа напрямую (через реестр модулей) ---

@router.get("/{period_id}/{period_type}", response_model=dict[str, Any])
async def get_period_detail(
    period_id: uuid.UUID, period_type: str, db: DBSession, user: CurrentUser
) -> dict[str, Any]:
    period = await _get_period_or_404(db, period_id)
    if period.period_type.value != period_type:
        raise HTTPException(status_code=409, detail="Period type mismatch")
    module = get_module(period_type)
    detail = await _load_detail(db, period)
    if detail is None:
        raise HTTPException(status_code=404, detail="Detail not found")
    return {
        "period_id": str(period.id),
        "period_type": period_type,
        "detail": {
            c.key: getattr(detail, c.key)
            for c in detail.__table__.columns
            if c.key not in ("id", "created_at", "updated_at", "period_id")
        },
    }


@router.put("/{period_id}/{period_type}", response_model=dict[str, Any])
async def upsert_period_detail(
    period_id: uuid.UUID,
    period_type: str,
    payload: dict[str, Any],
    db: DBSession,
    user: RequireOccupancyManage,
) -> dict[str, Any]:
    period = await _get_period_or_404(db, period_id)
    if period.period_type.value != period_type:
        raise HTTPException(status_code=409, detail="Period type mismatch")
    module = get_module(period_type)
    update_schema = module.update_schema
    if update_schema is None:
        raise HTTPException(status_code=400, detail=f"Type {period_type} has no detail schema")
    update_payload = update_schema(**payload)
    module.validate(update_payload, period)

    detail = await _load_detail(db, period)
    if detail is None:
        detail = module.detail_model(period_id=period.id)
        db.add(detail)
    for field, value in update_payload.model_dump(exclude_unset=True).items():
        setattr(detail, field, value)

    period.version += 1
    period.update_reason = "обновлен"
    period.updated_by = user.id

    await db.commit()
    await db.refresh(period)

    project_ids = await _resolve_project_ids(db, period)
    await publish(
        "employment_period", "updated",
        {"period": serialize_period(period, detail)},
        period_start=period.started_at,
        period_end=period.ended_at,
        project_ids=project_ids,
    )
    return serialize_period(period, detail)


@router.delete("/{period_id}/{period_type}", status_code=204)
async def delete_period_detail(
    period_id: uuid.UUID,
    period_type: str,
    db: DBSession,
    user: RequireOccupancyManage,
) -> None:
    period = await _get_period_or_404(db, period_id)
    if period.period_type.value != period_type:
        raise HTTPException(status_code=409, detail="Period type mismatch")
    module = get_module(period_type)
    detail = await _load_detail(db, period)
    if detail is None:
        raise HTTPException(status_code=404, detail="Detail not found")
    await db.delete(detail)
    await db.commit()
    await publish("employment_period", "updated", {"period_id": str(period_id)})
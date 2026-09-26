"""REST: /view/init — snapshot данных за окно просмотра (для live-обновлений)."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import CurrentUser, DBSession, get_claims
from src.services.permissions import project_scope
from src.services.view_service import build_snapshot, month_window, parse_dt

router = APIRouter(prefix="/view", tags=["view"])


@router.get("/init")
async def view_init(
    db: DBSession,
    user: CurrentUser,
    claims: dict | None = Depends(get_claims),
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """Snapshot: периоды занятости за интервал [from, to] (+ сотрудники,
    проекты, месторождения, финансы). По умолчанию окно — текущий месяц."""
    default_from, default_to = month_window()
    try:
        from_dt = parse_dt(from_) if from_ else default_from
        to_dt = parse_dt(to) if to else default_to
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {exc}") from exc

    if from_dt > to_dt:
        raise HTTPException(status_code=400, detail="from must be <= to")

    # ABAC-lite: скоуп по проектам из токена
    scoped = project_scope(claims or {})
    return await build_snapshot(db, from_dt, to_dt, scoped)
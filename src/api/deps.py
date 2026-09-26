"""FastAPI dependencies: current user, permission checks."""
import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.services import audit
from src.services.auth import TokenValidationError, decode_token, sync_user
from src.services.permissions import Permission, permissions_for_groups

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Валидация токена Keycloak + синхронизация пользователя + фиксация автора."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        claims = decode_token(credentials.credentials)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    user = await sync_user(db, claims)
    audit.set_actor(user.id)
    # Сохраняем claims для ABAC-lite скоупа (доступно в endpoint'ах)
    db.info["claims"] = claims
    return user


def require_permission(permission: Permission) -> Callable:
    """Фабрика dependency: требует конкретное разрешение у пользователя."""

    async def checker(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        perms = permissions_for_groups(user.groups)
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}",
            )
        return user

    return checker


def get_claims(db: Annotated[AsyncSession, Depends(get_db)]) -> dict | None:
    """Claims токена текущего запроса (для ABAC-lite скоупа)."""
    return db.info.get("claims")


CurrentUser = Annotated[User, Depends(get_current_user)]
RequireEmployeesManage = Annotated[User, Depends(require_permission(Permission.EMPLOYEES_MANAGE))]
RequireProjectsManage = Annotated[User, Depends(require_permission(Permission.PROJECTS_MANAGE))]
RequireOccupancyManage = Annotated[User, Depends(require_permission(Permission.OCCUPANCY_MANAGE))]

# Сессия БД как Annotated-алиас (используется в аннотациях эндпоинтов)
DBSession = Annotated[AsyncSession, Depends(get_db)]
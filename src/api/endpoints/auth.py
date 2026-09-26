"""REST: /me — текущий пользователь из Keycloak-токена."""
from fastapi import APIRouter

from src.api.deps import CurrentUser
from src.models.user import User

router = APIRouter(prefix="/me", tags=["auth"])


@router.get("")
async def get_me(user: CurrentUser) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "groups": user.groups,
        "last_login_at": str(user.last_login_at) if user.last_login_at else None,
    }
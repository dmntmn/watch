"""Keycloak JWT validation and user synchronization.

Каждый запрос: токен проверяется на валидность (подпись RS256 через JWKS,
issuer, audience, exp), после чего информация о пользователе обновляется
в таблице users сервиса.
"""
from datetime import datetime, timezone
from typing import Any

import jwt as pyjwt
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.user import User

settings = get_settings()

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.keycloak_jwks_uri, cache_keys=True)
    return _jwks_client


class TokenValidationError(Exception):
    pass


def decode_token(token: str) -> dict[str, Any]:
    """Проверяет подпись (JWKS), срок действия, issuer и audience."""
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        claims = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.keycloak_aud,
            issuer=settings.keycloak_issuer_url,
            options={"verify_exp": True, "verify_aud": True, "verify_iss": True},
        )
    except pyjwt.PyJWTError as exc:
        raise TokenValidationError(str(exc)) from exc
    return claims


def extract_user_info(claims: dict[str, Any]) -> dict[str, Any]:
    """Извлекает профиль и группы из claims токена."""
    groups = claims.get("groups") or []
    if isinstance(groups, str):
        groups = [groups]
    return {
        "keycloak_sub": str(claims["sub"]),
        "email": claims.get("email") or "",
        "first_name": claims.get("given_name"),
        "last_name": claims.get("family_name"),
        "groups": list(groups),
    }


async def sync_user(db: AsyncSession, claims: dict[str, Any]) -> User:
    """Upsert пользователя из Keycloak в БД сервиса."""
    info = extract_user_info(claims)
    now = datetime.now(timezone.utc)

    result = await db.execute(select(User).where(User.keycloak_sub == info["keycloak_sub"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(**info, last_login_at=now)
        db.add(user)
    else:
        user.email = info["email"]
        user.first_name = info["first_name"]
        user.last_name = info["last_name"]
        user.groups = info["groups"]
        user.last_login_at = now

    await db.flush()
    return user
"""Permission model: Keycloak groups -> permissions + project scope (ABAC-lite).

Группы Keycloak передаются в токене (claim "groups") в виде путей,
например "/personnel-managers". Разрешения назначаются группам;
скоуп по проектам берётся из опционального claim "projects".
"""
import enum
import uuid
from typing import Any


class Permission(str, enum.Enum):
    EMPLOYEES_MANAGE = "employees:manage"
    PROJECTS_MANAGE = "projects:manage"
    OCCUPANCY_MANAGE = "occupancy:manage"
    READ = "read"


# Группы Keycloak -> набор разрешений
GROUP_PERMISSIONS: dict[str, set[Permission]] = {
    "personnel-managers": {Permission.EMPLOYEES_MANAGE, Permission.READ},
    "project-managers": {Permission.PROJECTS_MANAGE, Permission.READ},
    "occupancy-managers": {Permission.OCCUPANCY_MANAGE, Permission.READ},
}


def normalize_group(group: str) -> str:
    """'/personnel-managers/sub' -> 'sub'; '/occupancy-managers' -> 'occupancy-managers'."""
    return group.strip("/").rsplit("/", 1)[-1]


def permissions_for_groups(groups: list[str]) -> set[Permission]:
    """Все аутентифицированные получают READ; остальное — по группам."""
    perms: set[Permission] = {Permission.READ}
    for group in groups or []:
        perms |= GROUP_PERMISSIONS.get(normalize_group(group), set())
    return perms


def project_scope(claims: dict[str, Any]) -> list[uuid.UUID] | None:
    """Скоуп видимости: claim 'projects'. None = вся база."""
    raw = claims.get("projects")
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = [raw]
    try:
        return [uuid.UUID(str(item)) for item in raw]
    except (ValueError, TypeError):
        return None
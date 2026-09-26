"""Сборка API-роутеров (префикс /api/v1)."""
from fastapi import APIRouter

from src.api.endpoints import (
    audit,
    auth,
    employees,
    employment,
    financial,
    projects,
    view,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(projects.router)
api_router.include_router(employment.router)
api_router.include_router(financial.router)
api_router.include_router(view.router)
api_router.include_router(audit.router)
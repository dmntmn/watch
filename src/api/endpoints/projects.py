"""REST: /projects — проекты, месторождения, назначение сотрудников (менеджер проектов)."""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import (
    CurrentUser,
    DBSession,
    RequireProjectsManage,
)
from src.models.employee import Employee
from src.models.project import Field, Project, ProjectEmployee
from src.schemas.project import (
    FieldCreate,
    FieldOut,
    FieldUpdate,
    ProjectCreate,
    ProjectEmployeeAssign,
    ProjectEmployeeOut,
    ProjectOut,
    ProjectUpdate,
)
from src.services.domain_events import publish

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project_or_404(db: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_field_or_404(db: AsyncSession, field_id: uuid.UUID) -> Field:
    field = await db.get(Field, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


# --- Проекты ---

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: DBSession,
    user: RequireProjectsManage,
) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    await publish("project", "created", {"id": str(project.id)})
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: DBSession, user: CurrentUser) -> list[Project]:
    result = await db.execute(select(Project).order_by(Project.name))
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: uuid.UUID, db: DBSession, user: CurrentUser) -> Project:
    return await _get_project_or_404(db, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: DBSession,
    user: RequireProjectsManage,
) -> Project:
    project = await _get_project_or_404(db, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    await publish("project", "updated", {"id": str(project.id)})
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID, db: DBSession, user: RequireProjectsManage
) -> None:
    project = await _get_project_or_404(db, project_id)
    await db.delete(project)
    await db.commit()
    await publish("project", "deleted", {"id": str(project_id)})


# --- Месторождения ---

@router.post("/{project_id}/fields", response_model=FieldOut, status_code=201)
async def create_field(
    project_id: uuid.UUID,
    payload: FieldCreate,
    db: DBSession,
    user: RequireProjectsManage,
) -> Field:
    project = await _get_project_or_404(db, project_id)
    field = Field(project_id=project.id, **payload.model_dump())
    db.add(field)
    await db.commit()
    await db.refresh(field)
    await publish("field", "created", {"id": str(field.id), "project_id": str(project.id)})
    return field


@router.get("/{project_id}/fields", response_model=list[FieldOut])
async def list_fields(
    project_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[Field]:
    project = await _get_project_or_404(db, project_id)
    result = await db.execute(select(Field).where(Field.project_id == project.id))
    return list(result.scalars().all())


@router.put("/fields/{field_id}", response_model=FieldOut)
async def update_field(
    field_id: uuid.UUID,
    payload: FieldUpdate,
    db: DBSession,
    user: RequireProjectsManage,
) -> Field:
    field = await _get_field_or_404(db, field_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(field, key, value)
    await db.commit()
    await db.refresh(field)
    await publish("field", "updated", {"id": str(field.id)})
    return field


@router.delete("/fields/{field_id}", status_code=204)
async def delete_field(
    field_id: uuid.UUID, db: DBSession, user: RequireProjectsManage
) -> None:
    field = await _get_field_or_404(db, field_id)
    project_id = field.project_id
    await db.delete(field)
    await db.commit()
    await publish("field", "deleted", {"id": str(field_id), "project_id": str(project_id)})


# --- Назначение сотрудников на проекты ---

@router.get("/{project_id}/employees", response_model=list[ProjectEmployeeOut])
async def list_project_employees(
    project_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[ProjectEmployee]:
    project = await _get_project_or_404(db, project_id)
    result = await db.execute(
        select(ProjectEmployee).where(ProjectEmployee.project_id == project.id)
    )
    return list(result.scalars().all())


@router.post("/{project_id}/employees", response_model=ProjectEmployeeOut, status_code=201)
async def assign_employee(
    project_id: uuid.UUID,
    payload: ProjectEmployeeAssign,
    db: DBSession,
    user: RequireProjectsManage,
) -> ProjectEmployee:
    project = await _get_project_or_404(db, project_id)
    employee = await db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing = await db.execute(
        select(ProjectEmployee).where(
            ProjectEmployee.project_id == project.id,
            ProjectEmployee.employee_id == employee.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Employee already assigned to project")

    assignment = ProjectEmployee(
        project_id=project.id, employee_id=employee.id, assigned_by=user.id
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    await publish(
        "project_employee", "assigned",
        {"project_id": str(project.id), "employee_id": str(employee.id)},
    )
    return assignment


@router.delete("/{project_id}/employees/{employee_id}", status_code=204)
async def unassign_employee(
    project_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: DBSession,
    user: RequireProjectsManage,
) -> None:
    result = await db.execute(
        select(ProjectEmployee).where(
            ProjectEmployee.project_id == project_id,
            ProjectEmployee.employee_id == employee_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await db.delete(assignment)
    await db.commit()
    await publish(
        "project_employee", "unassigned",
        {"project_id": str(project_id), "employee_id": str(employee_id)},
    )
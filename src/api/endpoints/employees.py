"""REST: /employees — CRUD сотрудников и их суб-записей (менеджер персонала)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import (
    CurrentUser,
    DBSession,
    RequireEmployeesManage,
)
from src.models.employee import (
    Employee,
    EmployeeCertification,
    EmployeeEducation,
    EmployeeMedicalExam,
    EmployeePPERecord,
)
from src.schemas.employee import (
    EmployeeCertificationCreate,
    EmployeeCertificationOut,
    EmployeeCertificationUpdate,
    EmployeeCreate,
    EmployeeEducationCreate,
    EmployeeEducationOut,
    EmployeeEducationUpdate,
    EmployeeMedicalExamCreate,
    EmployeeMedicalExamOut,
    EmployeeMedicalExamUpdate,
    EmployeeOut,
    EmployeePPECreate,
    EmployeePPEOut,
    EmployeePPEUpdate,
    EmployeeUpdate,
)
from src.services.domain_events import publish

router = APIRouter(prefix="/employees", tags=["employees"])


async def _get_employee_or_404(db: AsyncSession, employee_id: uuid.UUID) -> Employee:
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


# --- CRUD сотрудников ---

@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> Employee:
    employee = Employee(**payload.model_dump())
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    await publish("employee", "created", {"id": str(employee.id)})
    return employee


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    db: DBSession,
    user: CurrentUser,
) -> list[Employee]:
    result = await db.execute(select(Employee).order_by(Employee.surname, Employee.first_name))
    return list(result.scalars().all())


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: uuid.UUID, db: DBSession, user: CurrentUser) -> Employee:
    return await _get_employee_or_404(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> Employee:
    employee = await _get_employee_or_404(db, employee_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    await db.commit()
    await db.refresh(employee)
    await publish("employee", "updated", {"id": str(employee.id)})
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: uuid.UUID,
    db: DBSession,
    user: RequireEmployeesManage,
) -> None:
    employee = await _get_employee_or_404(db, employee_id)
    await db.delete(employee)
    await db.commit()
    await publish("employee", "deleted", {"id": str(employee_id)})


# --- Суб-записи: образование ---

@router.post("/{employee_id}/educations", response_model=EmployeeEducationOut, status_code=201)
async def add_education(
    employee_id: uuid.UUID,
    payload: EmployeeEducationCreate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeeEducation:
    employee = await _get_employee_or_404(db, employee_id)
    record = EmployeeEducation(employee_id=employee.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{employee_id}/educations", response_model=list[EmployeeEducationOut])
async def list_educations(
    employee_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[EmployeeEducation]:
    employee = await _get_employee_or_404(db, employee_id)
    result = await db.execute(
        select(EmployeeEducation).where(EmployeeEducation.employee_id == employee.id)
    )
    return list(result.scalars().all())


@router.put("/{employee_id}/educations/{record_id}", response_model=EmployeeEducationOut)
async def update_education(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: EmployeeEducationUpdate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeeEducation:
    record = await db.get(EmployeeEducation, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="Education record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{employee_id}/educations/{record_id}", status_code=204)
async def delete_education(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    db: DBSession,
    user: RequireEmployeesManage,
) -> None:
    record = await db.get(EmployeeEducation, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="Education record not found")
    await db.delete(record)
    await db.commit()


# --- Суб-записи: сертификаты ---

@router.post("/{employee_id}/certifications", response_model=EmployeeCertificationOut, status_code=201)
async def add_certification(
    employee_id: uuid.UUID,
    payload: EmployeeCertificationCreate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeeCertification:
    employee = await _get_employee_or_404(db, employee_id)
    record = EmployeeCertification(employee_id=employee.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{employee_id}/certifications", response_model=list[EmployeeCertificationOut])
async def list_certifications(
    employee_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[EmployeeCertification]:
    employee = await _get_employee_or_404(db, employee_id)
    result = await db.execute(
        select(EmployeeCertification).where(
            EmployeeCertification.employee_id == employee.id
        )
    )
    return list(result.scalars().all())


@router.put("/{employee_id}/certifications/{record_id}", response_model=EmployeeCertificationOut)
async def update_certification(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: EmployeeCertificationUpdate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeeCertification:
    record = await db.get(EmployeeCertification, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="Certification record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{employee_id}/certifications/{record_id}", status_code=204)
async def delete_certification(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    db: DBSession,
    user: RequireEmployeesManage,
) -> None:
    record = await db.get(EmployeeCertification, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="Certification record not found")
    await db.delete(record)
    await db.commit()


# --- Суб-записи: медосмотры ---

@router.post("/{employee_id}/medical-exams", response_model=EmployeeMedicalExamOut, status_code=201)
async def add_medical_exam(
    employee_id: uuid.UUID,
    payload: EmployeeMedicalExamCreate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeeMedicalExam:
    employee = await _get_employee_or_404(db, employee_id)
    record = EmployeeMedicalExam(employee_id=employee.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{employee_id}/medical-exams", response_model=list[EmployeeMedicalExamOut])
async def list_medical_exams(
    employee_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[EmployeeMedicalExam]:
    employee = await _get_employee_or_404(db, employee_id)
    result = await db.execute(
        select(EmployeeMedicalExam).where(EmployeeMedicalExam.employee_id == employee.id)
    )
    return list(result.scalars().all())


@router.put("/{employee_id}/medical-exams/{record_id}", response_model=EmployeeMedicalExamOut)
async def update_medical_exam(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: EmployeeMedicalExamUpdate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeeMedicalExam:
    record = await db.get(EmployeeMedicalExam, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="Medical exam not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{employee_id}/medical-exams/{record_id}", status_code=204)
async def delete_medical_exam(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    db: DBSession,
    user: RequireEmployeesManage,
) -> None:
    record = await db.get(EmployeeMedicalExam, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="Medical exam not found")
    await db.delete(record)
    await db.commit()


# --- Суб-записи: СИЗ и спецодежда ---

@router.post("/{employee_id}/ppe-records", response_model=EmployeePPEOut, status_code=201)
async def add_ppe_record(
    employee_id: uuid.UUID,
    payload: EmployeePPECreate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeePPERecord:
    employee = await _get_employee_or_404(db, employee_id)
    record = EmployeePPERecord(employee_id=employee.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{employee_id}/ppe-records", response_model=list[EmployeePPEOut])
async def list_ppe_records(
    employee_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[EmployeePPERecord]:
    employee = await _get_employee_or_404(db, employee_id)
    result = await db.execute(
        select(EmployeePPERecord).where(EmployeePPERecord.employee_id == employee.id)
    )
    return list(result.scalars().all())


@router.put("/{employee_id}/ppe-records/{record_id}", response_model=EmployeePPEOut)
async def update_ppe_record(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: EmployeePPEUpdate,
    db: DBSession,
    user: RequireEmployeesManage,
) -> EmployeePPERecord:
    record = await db.get(EmployeePPERecord, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="PPE record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{employee_id}/ppe-records/{record_id}", status_code=204)
async def delete_ppe_record(
    employee_id: uuid.UUID,
    record_id: uuid.UUID,
    db: DBSession,
    user: RequireEmployeesManage,
) -> None:
    record = await db.get(EmployeePPERecord, record_id)
    if record is None or record.employee_id != employee_id:
        raise HTTPException(status_code=404, detail="PPE record not found")
    await db.delete(record)
    await db.commit()
"""REST: финансовые записи периодов и файлы-подтверждения (S3)."""
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, DBSession, RequireOccupancyManage
from src.models.employee import Employee
from src.models.employment_period import EmploymentPeriod
from src.models.financial import FinancialAttachment, FinancialRecord
from src.schemas.financial import (
    AttachmentOut,
    FinancialRecordCreate,
    FinancialRecordOut,
    FinancialRecordUpdate,
)
from src.services.domain_events import publish
from src.services.notifications import financial_added_email, notifier
from src.services.storage import storage

router = APIRouter(tags=["financial"])


async def _get_record_or_404(db: AsyncSession, record_id: uuid.UUID) -> FinancialRecord:
    record = await db.get(FinancialRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Financial record not found")
    return record


async def _get_period_or_404(db: AsyncSession, period_id: uuid.UUID) -> EmploymentPeriod:
    period = await db.get(EmploymentPeriod, period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Employment period not found")
    return period


def _email_task_factory(employee: Employee, record: FinancialRecord):
    async def task() -> None:
        subject, body = financial_added_email(employee, record)
        await notifier.send(employee.email, subject, body)

    return task


# --- Финансовые записи ---

@router.post(
    "/employment-periods/{period_id}/financial-records",
    response_model=FinancialRecordOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_financial_record(
    period_id: uuid.UUID,
    payload: FinancialRecordCreate,
    background: BackgroundTasks,
    db: DBSession,
    user: RequireOccupancyManage,
) -> FinancialRecord:
    period = await _get_period_or_404(db, period_id)
    record = FinancialRecord(
        period_id=period.id,
        kind=payload.kind,
        amount=payload.amount,
        description=payload.description,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    employee = await db.get(Employee, period.employee_id)
    if employee is not None:
        background.add_task(_email_task_factory(employee, record))

    await publish(
        "financial_record", "created",
        {"period_id": str(period.id), "record_id": str(record.id)},
        period_start=period.started_at,
        period_end=period.ended_at,
    )
    return record


@router.get(
    "/employment-periods/{period_id}/financial-records",
    response_model=list[FinancialRecordOut],
)
async def list_financial_records(
    period_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[FinancialRecord]:
    await _get_period_or_404(db, period_id)
    result = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.period_id == period_id)
        .order_by(FinancialRecord.created_at)
    )
    return list(result.scalars().all())


@router.put("/financial-records/{record_id}", response_model=FinancialRecordOut)
async def update_financial_record(
    record_id: uuid.UUID,
    payload: FinancialRecordUpdate,
    db: DBSession,
    user: RequireOccupancyManage,
) -> FinancialRecord:
    record = await _get_record_or_404(db, record_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_by = user.id
    await db.commit()
    await db.refresh(record)

    period = await db.get(EmploymentPeriod, record.period_id)
    await publish(
        "financial_record", "updated",
        {"period_id": str(record.period_id), "record_id": str(record.id)},
        period_start=period.started_at if period else None,
        period_end=period.ended_at if period else None,
    )
    return record


@router.delete("/financial-records/{record_id}", status_code=204)
async def delete_financial_record(
    record_id: uuid.UUID, db: DBSession, user: RequireOccupancyManage
) -> None:
    record = await _get_record_or_404(db, record_id)
    await db.delete(record)
    await db.commit()
    await publish(
        "financial_record", "deleted",
        {"period_id": str(record.period_id), "record_id": str(record_id)},
    )


# --- Вложения (файлы-подтверждения) ---

@router.post(
    "/financial-records/{record_id}/attachments",
    response_model=AttachmentOut,
    status_code=201,
)
async def upload_attachment(
    record_id: uuid.UUID,
    file: UploadFile,
    db: DBSession,
    user: RequireOccupancyManage,
) -> FinancialAttachment:
    record = await _get_record_or_404(db, record_id)

    content = await file.read()
    s3_key = f"{record_id}/{uuid.uuid4()}/{file.filename or 'attachment'}"

    await storage.upload(s3_key, content, file.content_type)

    attachment = FinancialAttachment(
        record_id=record.id,
        file_name=file.filename or "attachment",
        content_type=file.content_type,
        size_bytes=len(content),
        s3_key=s3_key,
        uploaded_by=user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    period = await db.get(EmploymentPeriod, record.period_id)
    await publish(
        "attachment", "created",
        {"record_id": str(record.id), "attachment_id": str(attachment.id)},
        period_start=period.started_at if period else None,
        period_end=period.ended_at if period else None,
    )
    return attachment


@router.get(
    "/financial-records/{record_id}/attachments",
    response_model=list[AttachmentOut],
)
async def list_attachments(
    record_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> list[FinancialAttachment]:
    await _get_record_or_404(db, record_id)
    result = await db.execute(
        select(FinancialAttachment).where(FinancialAttachment.record_id == record_id)
    )
    return list(result.scalars().all())


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> Response:
    attachment = await db.get(FinancialAttachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    body = await storage.download(attachment.s3_key)
    return Response(
        content=body.read(),
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment.file_name}"'},
    )


@router.delete("/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: uuid.UUID, db: DBSession, user: RequireOccupancyManage
) -> None:
    attachment = await db.get(FinancialAttachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    await storage.delete(attachment.s3_key)
    await db.delete(attachment)
    await db.commit()
    await publish(
        "attachment", "deleted", {"attachment_id": str(attachment_id)}
    )
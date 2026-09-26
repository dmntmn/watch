"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    # --- ENUM типы ---
    period_type = postgresql.ENUM(
        "shift", "vacation", "sick_leave", "flight", "hotel", "train", "taxi", "other",
        name="period_type", create_type=False,
    )
    financial_kind = postgresql.ENUM(
        "income", "expense", name="financial_kind", create_type=False,
    )
    audit_action = postgresql.ENUM(
        "insert", "update", "delete", name="audit_action", create_type=False,
    )
    period_type.create(op.get_bind(), checkfirst=True)
    financial_kind.create(op.get_bind(), checkfirst=True)
    audit_action.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("keycloak_sub", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("first_name", sa.String(255)),
        sa.Column("last_name", sa.String(255)),
        sa.Column("groups", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_users_keycloak_sub", "users", ["keycloak_sub"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])

    # --- employees ---
    op.create_table(
        "employees",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(64)),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("surname", sa.String(255), nullable=False),
        sa.Column("patronymic", sa.String(255)),
        *_timestamps(),
    )
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)

    # --- employee sub-records ---
    op.create_table(
        "employee_educations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("employee_id", _uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("institution", sa.String(500)),
        sa.Column("graduated_at", sa.Integer()),
        *_timestamps(),
    )
    op.create_index("ix_employee_educations_employee_id", "employee_educations", ["employee_id"])

    op.create_table(
        "employee_certifications",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("employee_id", _uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("issued_at", sa.Date()),
        sa.Column("expires_at", sa.Date()),
        *_timestamps(),
    )
    op.create_index("ix_employee_certifications_employee_id", "employee_certifications", ["employee_id"])

    op.create_table(
        "employee_medical_exams",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("employee_id", _uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("expires_at", sa.Date()),
        sa.Column("conclusion", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_employee_medical_exams_employee_id", "employee_medical_exams", ["employee_id"])

    op.create_table(
        "employee_ppe_records",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("employee_id", _uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_name", sa.String(500), nullable=False),
        sa.Column("issued_at", sa.Date(), nullable=False),
        sa.Column("expires_at", sa.Date()),
        *_timestamps(),
    )
    op.create_index("ix_employee_ppe_records_employee_id", "employee_ppe_records", ["employee_id"])

    # --- projects / fields ---
    op.create_table(
        "projects",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        *_timestamps(),
    )

    op.create_table(
        "fields",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("project_id", _uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_fields_project_id", "fields", ["project_id"])

    op.create_table(
        "project_employees",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("project_id", _uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", _uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by", _uuid(), sa.ForeignKey("users.id")),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "employee_id"),
    )
    op.create_index("ix_project_employees_project_id", "project_employees", ["project_id"])
    op.create_index("ix_project_employees_employee_id", "project_employees", ["employee_id"])

    # --- employment_periods (единая таблица) ---
    op.create_table(
        "employment_periods",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("employee_id", _uuid(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("period_type", period_type, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", _uuid(), sa.ForeignKey("users.id")),
        sa.Column("update_reason", sa.String(100)),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_employment_periods_employee_id", "employment_periods", ["employee_id"])
    op.create_index("ix_employment_periods_period_type", "employment_periods", ["period_type"])
    op.create_index("ix_employment_periods_started_at", "employment_periods", ["started_at"])

    # --- detail tables (1:1 c employment_periods) ---
    op.create_table(
        "shift_details",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("field_id", _uuid(), sa.ForeignKey("fields.id"), nullable=False),
        sa.Column("notes", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_shift_details_field_id", "shift_details", ["field_id"])

    for name in ("vacation_details", "sick_leave_details", "other_details"):
        op.create_table(
            name,
            sa.Column("id", _uuid(), primary_key=True),
            sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("notes", sa.Text()),
            *_timestamps(),
        )

    op.create_table(
        "flight_details",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("airline", sa.String(200)),
        sa.Column("flight_number", sa.String(50)),
        sa.Column("departure_airport", sa.String(200)),
        sa.Column("arrival_airport", sa.String(200)),
        sa.Column("departure_at", sa.DateTime(timezone=True)),
        sa.Column("arrival_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )

    op.create_table(
        "hotel_details",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("hotel_name", sa.String(300)),
        sa.Column("city", sa.String(200)),
        sa.Column("address", sa.String(500)),
        sa.Column("check_in_at", sa.DateTime(timezone=True)),
        sa.Column("check_out_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )

    op.create_table(
        "train_details",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("route", sa.String(300)),
        sa.Column("train_number", sa.String(50)),
        sa.Column("carriage", sa.String(50)),
        sa.Column("seat_number", sa.String(50)),
        sa.Column("departure_at", sa.DateTime(timezone=True)),
        sa.Column("arrival_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )

    op.create_table(
        "taxi_details",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("pickup_address", sa.String(500)),
        sa.Column("dropoff_address", sa.String(500)),
        sa.Column("ride_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )

    # --- financial_records / financial_attachments ---
    op.create_table(
        "financial_records",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("period_id", _uuid(), sa.ForeignKey("employment_periods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", financial_kind, nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_by", _uuid(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", _uuid(), sa.ForeignKey("users.id")),
        *_timestamps(),
    )
    op.create_index("ix_financial_records_period_id", "financial_records", ["period_id"])

    op.create_table(
        "financial_attachments",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("record_id", _uuid(), sa.ForeignKey("financial_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(200)),
        sa.Column("size_bytes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("uploaded_by", _uuid(), sa.ForeignKey("users.id")),
        *_timestamps(),
    )
    op.create_index("ix_financial_attachments_record_id", "financial_attachments", ["record_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("old_values", postgresql.JSONB()),
        sa.Column("new_values", postgresql.JSONB()),
        sa.Column("actor_id", _uuid(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("financial_attachments")
    op.drop_table("financial_records")
    op.drop_table("taxi_details")
    op.drop_table("train_details")
    op.drop_table("hotel_details")
    op.drop_table("flight_details")
    op.drop_table("other_details")
    op.drop_table("sick_leave_details")
    op.drop_table("vacation_details")
    op.drop_table("shift_details")
    op.drop_table("employment_periods")
    op.drop_table("project_employees")
    op.drop_table("fields")
    op.drop_table("projects")
    op.drop_table("employee_ppe_records")
    op.drop_table("employee_medical_exams")
    op.drop_table("employee_certifications")
    op.drop_table("employee_educations")
    op.drop_table("employees")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS audit_action")
    op.execute("DROP TYPE IF EXISTS financial_kind")
    op.execute("DROP TYPE IF EXISTS period_type")
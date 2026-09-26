"""SQLAlchemy models. Импорт пакета регистрирует все модели и модули занятости."""
from src.models.audit import AuditAction, AuditLog  # noqa: F401
from src.models.base import Base  # noqa: F401
from src.models.employee import (  # noqa: F401
    Employee,
    EmployeeCertification,
    EmployeeEducation,
    EmployeeMedicalExam,
    EmployeePPERecord,
)
from src.models.employment_period import EmploymentPeriod, PeriodType  # noqa: F401
from src.models.financial import (  # noqa: F401
    FinancialAttachment,
    FinancialKind,
    FinancialRecord,
)
from src.models.occupancy import OCCUPANCY_REGISTRY, get_module  # noqa: F401
from src.models.project import Field, Project, ProjectEmployee  # noqa: F401
from src.models.user import User  # noqa: F401

__all__ = [
    "AuditAction",
    "AuditLog",
    "Base",
    "Employee",
    "EmployeeCertification",
    "EmployeeEducation",
    "EmployeeMedicalExam",
    "EmployeePPERecord",
    "EmploymentPeriod",
    "Field",
    "FinancialAttachment",
    "FinancialKind",
    "FinancialRecord",
    "OCCUPANCY_REGISTRY",
    "PeriodType",
    "Project",
    "ProjectEmployee",
    "User",
    "get_module",
]
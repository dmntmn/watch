/** Типы DTO, повторяющие схемы backend (FastAPI /api/v1). */

export type UUID = string;

export interface Me {
  id: UUID;
  email: string;
  first_name: string | null;
  last_name: string | null;
  groups: string[];
  last_login_at: string | null;
}

// --- Сотрудники ---

export interface Employee {
  id: UUID;
  email: string;
  phone: string | null;
  first_name: string;
  surname: string;
  patronymic: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeCreate {
  email: string;
  phone?: string | null;
  first_name: string;
  surname: string;
  patronymic?: string | null;
}

export interface EmployeeUpdate {
  email?: string;
  phone?: string | null;
  first_name?: string;
  surname?: string;
  patronymic?: string | null;
}

export interface EmployeeEducation {
  id: UUID;
  employee_id: UUID;
  title: string;
  institution: string | null;
  graduated_at: number | null;
}

export interface EmployeeCertification {
  id: UUID;
  employee_id: UUID;
  title: string;
  issued_at: string | null;
  expires_at: string | null;
}

export interface EmployeeMedicalExam {
  id: UUID;
  employee_id: UUID;
  exam_date: string;
  expires_at: string | null;
  conclusion: string | null;
}

export interface EmployeePPERecord {
  id: UUID;
  employee_id: UUID;
  item_name: string;
  issued_at: string;
  expires_at: string | null;
}

// --- Проекты / месторождения / назначения ---

export interface Project {
  id: UUID;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Field {
  id: UUID;
  project_id: UUID;
  name: string;
}

export interface ProjectEmployee {
  id: UUID;
  project_id: UUID;
  employee_id: UUID;
  assigned_by: UUID | null;
  created_at: string;
}

// --- Периоды занятости ---

export type PeriodType =
  | 'shift'
  | 'vacation'
  | 'sick_leave'
  | 'flight'
  | 'hotel'
  | 'train'
  | 'taxi'
  | 'other';

export interface FinancialRecordView {
  id: UUID;
  kind: 'income' | 'expense';
  amount: number;
  description: string | null;
  created_by: UUID | null;
  updated_by: UUID | null;
}

export interface EmploymentPeriod {
  id: UUID;
  employee_id: UUID;
  period_type: PeriodType;
  started_at: string;
  ended_at: string | null;
  version: number;
  active: boolean;
  update_reason: string | null;
  updated_by: UUID | null;
  detail: Record<string, unknown> | null;
  financial_records: FinancialRecordView[];
}

export interface EmploymentPeriodCreate {
  employee_id: UUID;
  period_type: PeriodType;
  started_at: string;
  ended_at?: string | null;
  details?: Record<string, unknown>;
}

export interface EmploymentPeriodUpdate {
  started_at?: string;
  ended_at?: string | null;
  update_reason: string;
  details?: Record<string, unknown>;
}

export interface FinancialRecord {
  id: UUID;
  period_id: UUID;
  kind: 'income' | 'expense';
  amount: number;
  description: string | null;
  created_by: UUID | null;
  updated_by: UUID | null;
  created_at: string;
}

export interface FinancialRecordCreate {
  kind: 'income' | 'expense';
  amount: number;
  description?: string | null;
}

export interface Attachment {
  id: UUID;
  record_id: UUID;
  file_name: string;
  content_type: string | null;
  size_bytes: number;
  uploaded_by: UUID | null;
  created_at: string;
}

// --- Snapshot просмотра (GET /view/init) ---

export interface ViewSnapshot {
  window: { from: string; to: string };
  projects: Array<{ id: UUID; name: string; description: string | null }>;
  fields: Array<{ id: UUID; project_id: UUID; name: string }>;
  employees: Array<{
    id: UUID;
    email: string;
    phone: string | null;
    first_name: string;
    surname: string;
    patronymic: string | null;
  }>;
  periods: EmploymentPeriod[];
}

// --- Аудит ---

export type AuditAction = 'insert' | 'update' | 'delete';

export interface AuditLogRow {
  id: UUID;
  entity_type: string;
  entity_id: string;
  action: AuditAction;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  actor_id: UUID | null;
  created_at: string;
}
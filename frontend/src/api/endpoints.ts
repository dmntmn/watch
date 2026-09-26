import api from './client';
import type {
  Attachment,
  AuditLogRow,
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
  EmploymentPeriod,
  EmploymentPeriodCreate,
  EmploymentPeriodUpdate,
  Field,
  FinancialRecord,
  FinancialRecordCreate,
  Me,
  Project,
  ProjectEmployee,
  ViewSnapshot,
} from './types';

// --- Пользователь ---

export const getMe = () => api.get<Me>('/me').then((r) => r.data);

// --- Сотрудники ---

export const listEmployees = () => api.get<Employee[]>('/employees').then((r) => r.data);
export const createEmployee = (data: EmployeeCreate) =>
  api.post<Employee>('/employees', data).then((r) => r.data);
export const updateEmployee = (id: string, data: EmployeeUpdate) =>
  api.put<Employee>(`/employees/${id}`, data).then((r) => r.data);
export const deleteEmployee = (id: string) => api.delete(`/employees/${id}`);

// Суб-записи сотрудников (универсальные CRUD через массив ресурсов)

export type SubResource =
  | 'educations'
  | 'certifications'
  | 'medical-exams'
  | 'ppe-records';

export const listSubRecords = <T>(employeeId: string, resource: SubResource) =>
  api.get<T[]>(`/employees/${employeeId}/${resource}`).then((r) => r.data);
export const createSubRecord = <T>(employeeId: string, resource: SubResource, data: unknown) =>
  api.post<T>(`/employees/${employeeId}/${resource}`, data).then((r) => r.data);
export const updateSubRecord = <T>(
  employeeId: string,
  resource: SubResource,
  recordId: string,
  data: unknown,
) => api.put<T>(`/employees/${employeeId}/${resource}/${recordId}`, data).then((r) => r.data);
export const deleteSubRecord = (employeeId: string, resource: SubResource, recordId: string) =>
  api.delete(`/employees/${employeeId}/${resource}/${recordId}`);

// --- Проекты / месторождения / назначения ---

export const listProjects = () => api.get<Project[]>('/projects').then((r) => r.data);
export const createProject = (data: { name: string; description?: string | null }) =>
  api.post<Project>('/projects', data).then((r) => r.data);
export const updateProject = (
  id: string,
  data: { name?: string; description?: string | null },
) => api.put<Project>(`/projects/${id}`, data).then((r) => r.data);
export const deleteProject = (id: string) => api.delete(`/projects/${id}`);

export const listFields = (projectId: string) =>
  api.get<Field[]>(`/projects/${projectId}/fields`).then((r) => r.data);
export const createField = (projectId: string, data: { name: string }) =>
  api.post<Field>(`/projects/${projectId}/fields`, data).then((r) => r.data);
export const updateField = (fieldId: string, data: { name?: string }) =>
  api.put<Field>(`/projects/fields/${fieldId}`, data).then((r) => r.data);
export const deleteField = (fieldId: string) => api.delete(`/projects/fields/${fieldId}`);

export const listProjectEmployees = (projectId: string) =>
  api.get<ProjectEmployee[]>(`/projects/${projectId}/employees`).then((r) => r.data);
export const assignEmployee = (projectId: string, employeeId: string) =>
  api.post<ProjectEmployee>(`/projects/${projectId}/employees`, { employee_id: employeeId }).then((r) => r.data);
export const unassignEmployee = (projectId: string, employeeId: string) =>
  api.delete(`/projects/${projectId}/employees/${employeeId}`);

// --- Периоды занятости ---

export const listPeriods = (params?: { from?: string; to?: string }) =>
  api.get<EmploymentPeriod[]>('/employment-periods', { params }).then((r) => r.data);
export const createPeriod = (data: EmploymentPeriodCreate) =>
  api.post<EmploymentPeriod>('/employment-periods', data).then((r) => r.data);
export const updatePeriod = (id: string, data: EmploymentPeriodUpdate) =>
  api.put<EmploymentPeriod>(`/employment-periods/${id}`, data).then((r) => r.data);
export const deletePeriod = (id: string) => api.delete(`/employment-periods/${id}`);

// --- Финансы ---

export const listFinancialRecords = (periodId: string) =>
  api.get<FinancialRecord[]>(`/employment-periods/${periodId}/financial-records`).then((r) => r.data);
export const createFinancialRecord = (periodId: string, data: FinancialRecordCreate) =>
  api.post<FinancialRecord>(`/employment-periods/${periodId}/financial-records`, data).then((r) => r.data);
export const updateFinancialRecord = (recordId: string, data: Partial<FinancialRecordCreate>) =>
  api.put<FinancialRecord>(`/financial-records/${recordId}`, data).then((r) => r.data);
export const deleteFinancialRecord = (recordId: string) => api.delete(`/financial-records/${recordId}`);

export const listAttachments = (recordId: string) =>
  api.get<Attachment[]>(`/financial-records/${recordId}/attachments`).then((r) => r.data);
export const uploadAttachment = (recordId: string, file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api
    .post<Attachment>(`/financial-records/${recordId}/attachments`, form)
    .then((r) => r.data);
};
export const downloadAttachment = async (attachmentId: string) => {
  const res = await api.get<Blob>(`/attachments/${attachmentId}`, { responseType: 'blob' });
  return res.data;
};
export const deleteAttachment = (attachmentId: string) => api.delete(`/attachments/${attachmentId}`);

// --- Snapshot просмотра ---

export const fetchViewSnapshot = (params: { from?: string; to?: string }) =>
  api.get<ViewSnapshot>('/view/init', { params }).then((r) => r.data);

// --- Аудит ---

export const listAuditLogs = (params?: {
  entity?: string;
  entity_id?: string;
  action?: string;
  limit?: number;
}) => api.get<AuditLogRow[]>('/audit-logs', { params }).then((r) => r.data);
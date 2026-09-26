import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
} from '@tanstack/react-query';
import * as api from '@/api/endpoints';
import type {
  Attachment,
  Employee,
  EmployeeCertification,
  EmployeeEducation,
  EmployeeMedicalExam,
  EmployeePPERecord,
  EmploymentPeriod,
  FinancialRecord,
  FinancialRecordCreate,
  Project,
  ViewSnapshot,
} from '@/api/types';

export const qk = {
  me: ['me'] as QueryKey,
  employees: ['employees'] as QueryKey,
  employee: (id: string) => ['employees', id] as QueryKey,
  employeeSub: (id: string, resource: string) => ['employees', id, resource] as QueryKey,
  projects: ['projects'] as QueryKey,
  projectFields: (id: string) => ['projects', id, 'fields'] as QueryKey,
  projectEmployees: (id: string) => ['projects', id, 'employees'] as QueryKey,
  view: (from?: string, to?: string) => ['view', from ?? '', to ?? ''] as QueryKey,
  periods: ['employment-periods'] as QueryKey,
  financial: (periodId: string) => ['financial', periodId] as QueryKey,
  attachments: (recordId: string) => ['attachments', recordId] as QueryKey,
  audit: ['audit'] as QueryKey,
};

/** Префиксный ключ для инвалидации всех snapshot-ов просмотра. */
export const VIEW_KEY: QueryKey = ['view'];

// --- Запросы ---

export function useMe() {
  return useQuery({ queryKey: qk.me, queryFn: api.getMe, staleTime: 60_000 });
}

export function useEmployees() {
  return useQuery({ queryKey: qk.employees, queryFn: api.listEmployees });
}

export function useSubRecords<T>(employeeId: string, resource: string) {
  return useQuery({
    queryKey: qk.employeeSub(employeeId, resource),
    queryFn: () => api.listSubRecords<T>(employeeId, resource as never),
  });
}

export function useProjects() {
  return useQuery({ queryKey: qk.projects, queryFn: api.listProjects });
}

export function useProjectFields(projectId: string) {
  return useQuery({
    queryKey: qk.projectFields(projectId),
    queryFn: () => api.listFields(projectId),
    enabled: Boolean(projectId),
  });
}

export function useProjectEmployees(projectId: string) {
  return useQuery({
    queryKey: qk.projectEmployees(projectId),
    queryFn: () => api.listProjectEmployees(projectId),
    enabled: Boolean(projectId),
  });
}

export function useViewSnapshot(from: string, to: string) {
  return useQuery({
    queryKey: qk.view(from, to),
    queryFn: () => api.fetchViewSnapshot({ from, to }),
    staleTime: 15_000,
  });
}

export function useFinancialRecords(periodId: string) {
  return useQuery({
    queryKey: qk.financial(periodId),
    queryFn: () => api.listFinancialRecords(periodId),
    enabled: Boolean(periodId),
  });
}

export function useAttachments(recordId: string) {
  return useQuery({
    queryKey: qk.attachments(recordId),
    queryFn: () => api.listAttachments(recordId),
    enabled: Boolean(recordId),
  });
}

export function useAuditLogs(params?: { entity?: string; action?: string }) {
  return useQuery({
    queryKey: [...qk.audit, params?.entity ?? '', params?.action ?? ''],
    queryFn: () => api.listAuditLogs(params),
  });
}

// --- Мутации ---

function useInvalidatingMutation<TData, TVariables>(
  mutationFn: (v: TVariables) => Promise<TData>,
  keys: QueryKey[],
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: async () => {
      await Promise.all(keys.map((k) => qc.invalidateQueries({ queryKey: k })));
    },
  });
}

export function useCreateEmployee() {
  return useInvalidatingMutation(api.createEmployee, [qk.employees]);
}
export function useUpdateEmployee() {
  return useInvalidatingMutation(
    ({ id, data }: { id: string; data: Parameters<typeof api.updateEmployee>[1] }) =>
      api.updateEmployee(id, data),
    [qk.employees],
  );
}
export function useDeleteEmployee() {
  return useInvalidatingMutation(api.deleteEmployee, [qk.employees, qk.projects]);
}

export function useCreateSubRecord<T>(employeeId: string, resource: string) {
  return useInvalidatingMutation<T, { data: unknown }>(
    ({ data }) => api.createSubRecord<T>(employeeId, resource as never, data),
    [qk.employeeSub(employeeId, resource)],
  );
}
export function useUpdateSubRecord<T>(employeeId: string, resource: string) {
  return useInvalidatingMutation<T, { recordId: string; data: unknown }>(
    ({ recordId, data }) => api.updateSubRecord<T>(employeeId, resource as never, recordId, data),
    [qk.employeeSub(employeeId, resource)],
  );
}
export function useDeleteSubRecord(employeeId: string, resource: string) {
  return useInvalidatingMutation(
    (recordId: string) => api.deleteSubRecord(employeeId, resource as never, recordId),
    [qk.employeeSub(employeeId, resource)],
  );
}

export function useCreateProject() {
  return useInvalidatingMutation(api.createProject, [qk.projects, VIEW_KEY]);
}
export function useUpdateProject() {
  return useInvalidatingMutation(
    ({ id, data }: { id: string; data: Parameters<typeof api.updateProject>[1] }) =>
      api.updateProject(id, data),
    [qk.projects],
  );
}
export function useDeleteProject() {
  return useInvalidatingMutation(api.deleteProject, [qk.projects, VIEW_KEY]);
}

export function useCreateField(projectId: string) {
  return useInvalidatingMutation((data: { name: string }) => api.createField(projectId, data), [
    qk.projectFields(projectId),
    VIEW_KEY,
  ]);
}
export function useUpdateField() {
  return useInvalidatingMutation(
    ({ id, data }: { id: string; data: { name?: string } }) => api.updateField(id, data),
    [qk.projects, VIEW_KEY],
  );
}
export function useDeleteField(projectId: string) {
  return useInvalidatingMutation(api.deleteField, [qk.projectFields(projectId), VIEW_KEY]);
}

export function useAssignEmployee(projectId: string) {
  return useInvalidatingMutation((employeeId: string) => api.assignEmployee(projectId, employeeId), [
    qk.projectEmployees(projectId),
    VIEW_KEY,
  ]);
}
export function useUnassignEmployee(projectId: string) {
  return useInvalidatingMutation(
    (employeeId: string) => api.unassignEmployee(projectId, employeeId),
    [qk.projectEmployees(projectId), VIEW_KEY],
  );
}

export function useCreatePeriod() {
  return useInvalidatingMutation(api.createPeriod, [qk.periods, VIEW_KEY]);
}
export function useUpdatePeriod() {
  return useInvalidatingMutation(
    ({ id, data }: { id: string; data: Parameters<typeof api.updatePeriod>[1] }) =>
      api.updatePeriod(id, data),
    [qk.periods, VIEW_KEY],
  );
}
export function useDeletePeriod() {
  return useInvalidatingMutation(api.deletePeriod, [qk.periods, VIEW_KEY]);
}

export function useCreateFinancialRecord(periodId: string) {
  return useInvalidatingMutation(
    (data: FinancialRecordCreate) => api.createFinancialRecord(periodId, data),
    [qk.financial(periodId), VIEW_KEY],
  );
}
export function useUpdateFinancialRecord(periodId: string) {
  return useInvalidatingMutation(
    ({ id, data }: { id: string; data: Parameters<typeof api.updateFinancialRecord>[1] }) =>
      api.updateFinancialRecord(id, data),
    [qk.financial(periodId), VIEW_KEY],
  );
}
export function useDeleteFinancialRecord(periodId: string) {
  return useInvalidatingMutation(api.deleteFinancialRecord, [qk.financial(periodId), VIEW_KEY]);
}

export function useUploadAttachment(recordId: string) {
  return useInvalidatingMutation((file: File) => api.uploadAttachment(recordId, file), [
    qk.attachments(recordId),
  ]);
}
export function useDeleteAttachment(recordId: string) {
  return useInvalidatingMutation(api.deleteAttachment, [qk.attachments(recordId)]);
}

export type { Employee, Project, ViewSnapshot, FinancialRecord, Attachment, EmploymentPeriod };
export type {
  EmployeeEducation,
  EmployeeCertification,
  EmployeeMedicalExam,
  EmployeePPERecord,
};
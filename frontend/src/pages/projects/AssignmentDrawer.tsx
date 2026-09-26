import { App, Button, Drawer, Select, Space, Table, Typography } from 'antd';
import { useState } from 'react';
import { apiErrorMessage } from '@/api/client';
import { ConfirmDeleteButton } from '@/components/ConfirmDeleteButton';
import { EmptyState, LoadingState } from '@/components/States';
import {
  useAssignEmployee,
  useEmployees,
  useProjectEmployees,
  useUnassignEmployee,
} from '@/hooks/queries';
import { usePermission } from '@/permissions';

interface Props {
  projectId: string;
  projectName: string;
  open: boolean;
  onClose: () => void;
}

/** Назначение сотрудников на проект (менеджер проектов). */
export function AssignmentDrawer({ projectId, projectName, open, onClose }: Props) {
  const { can } = usePermission();
  const { message } = App.useApp();
  const { data: assigned, isLoading, refetch } = useProjectEmployees(projectId);
  const { data: allEmployees } = useEmployees();
  const assignMutation = useAssignEmployee(projectId);
  const unassignMutation = useUnassignEmployee(projectId);
  const [selected, setSelected] = useState<string | undefined>();

  const assignedIds = new Set((assigned ?? []).map((a) => a.employee_id));
  const available = (allEmployees ?? []).filter((e) => !assignedIds.has(e.id));

  const handleAssign = async (employeeId?: string) => {
    if (!employeeId) return;
    try {
      await assignMutation.mutateAsync(employeeId);
      message.success('Сотрудник назначен на проект');
      setSelected(undefined);
    } catch (error) {
      message.error(apiErrorMessage(error));
    }
  };

  return (
    <Drawer
      title={`Сотрудники проекта: ${projectName}`}
      open={open}
      onClose={onClose}
      width={560}
      extra={
        <Button onClick={() => void refetch()} type="link">
          Обновить
        </Button>
      }
    >
      {isLoading ? (
        <LoadingState rows={3} />
      ) : (
        <>
          <Typography.Paragraph type="secondary">
            Назначенные сотрудники имеют доступ к проекту (могут получать занятость на его
            месторождениях).
          </Typography.Paragraph>
          {can('projects:manage') && (
            <Space style={{ marginBottom: 16 }}>
              <Select
                showSearch
                allowClear
                placeholder="Добавить сотрудника…"
                value={selected}
                onChange={setSelected}
                optionFilterProp="label"
                style={{ minWidth: 280 }}
                options={available.map((e) => ({
                  value: e.id,
                  label: `${e.surname} ${e.first_name}${e.patronymic ? ` ${e.patronymic}` : ''} — ${e.email}`,
                }))}
              />
              <Button type="primary" disabled={!selected} onClick={() => void handleAssign(selected)}>
                Назначить
              </Button>
            </Space>
          )}
          {!assigned?.length ? (
            <EmptyState description="На проект никто не назначен" />
          ) : (
            <Table
              rowKey="id"
              size="small"
              pagination={false}
              dataSource={assigned}
              columns={[
                {
                  title: 'Сотрудник',
                  key: 'employee',
                  render: (_, row: { employee_id: string }) => {
                    const emp = allEmployees?.find((e) => e.id === row.employee_id);
                    return emp
                      ? `${emp.surname} ${emp.first_name}${emp.patronymic ? ` ${emp.patronymic}` : ''}`
                      : row.employee_id;
                  },
                },
                ...(can('projects:manage')
                  ? [
                      {
                        title: '',
                        key: 'actions',
                        render: (_: unknown, row: { employee_id: string }) => (
                          <ConfirmDeleteButton
                            size="small"
                            title="Снять сотрудника с проекта?"
                            onConfirm={async () => {
                              await unassignMutation.mutateAsync(row.employee_id);
                              message.success('Сотрудник снят с проекта');
                            }}
                          />
                        ),
                      },
                    ]
                  : []),
              ]}
            />
          )}
        </>
      )}
    </Drawer>
  );
}
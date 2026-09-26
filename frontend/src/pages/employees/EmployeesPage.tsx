import { App, Button, Input, Space, Table, Tag } from 'antd';
import { PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { useMemo, useState } from 'react';
import type { Employee } from '@/api/types';
import { ConfirmDeleteButton } from '@/components/ConfirmDeleteButton';
import { PageHeader } from '@/components/PageHeader';
import { PermissionGate } from '@/components/PermissionGate';
import { EmptyState, ErrorState, LoadingState } from '@/components/States';
import { useDeleteEmployee, useEmployees } from '@/hooks/queries';
import { usePermission } from '@/permissions';
import { EmployeeFormModal } from './EmployeeFormModal';
import { EmployeeSubRecords } from './EmployeeSubRecords';

function fullName(e: Employee): string {
  return [e.surname, e.first_name, e.patronymic].filter(Boolean).join(' ');
}

export default function EmployeesPage() {
  const { can } = usePermission();
  const { message } = App.useApp();
  const { data, isLoading, isError, refetch } = useEmployees();
  const deleteMutation = useDeleteEmployee();
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    if (!q) return data;
    return data.filter(
      (e) =>
        fullName(e).toLowerCase().includes(q) || e.email.toLowerCase().includes(q),
    );
  }, [data, search]);

  if (isLoading) return <LoadingState />;
  if (isError)
    return (
      <ErrorState
        error="Не удалось загрузить сотрудников"
        onRetry={() => void refetch()}
      />
    );

  return (
    <>
      <PageHeader
        title="Сотрудники"
        extra={
          <Space>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="Поиск по ФИО или email"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 260 }}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void refetch()} />
            <PermissionGate action="employees:manage">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setEditing(null);
                  setModalOpen(true);
                }}
              >
                Добавить
              </Button>
            </PermissionGate>
          </Space>
        }
      />
      {!filtered.length ? (
        <EmptyState description="Сотрудники не найдены" />
      ) : (
        <Table<Employee>
          rowKey="id"
          dataSource={filtered}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (t) => `Всего: ${t}`,
          }}
          columns={[
            {
              title: 'ФИО',
              key: 'name',
              sorter: (a, b) => fullName(a).localeCompare(fullName(b)),
              render: (_, e) => <strong>{fullName(e)}</strong>,
            },
            {
              title: 'Email',
              dataIndex: 'email',
              sorter: (a, b) => a.email.localeCompare(b.email),
            },
            {
              title: 'Телефон',
              dataIndex: 'phone',
              render: (v: string | null) => v ?? '—',
            },
            {
              title: 'Статус записей',
              key: 'records',
              render: () => <Tag color="blue">медосмотр/СИЗ</Tag>,
            },
            ...(can('employees:manage')
              ? [
                  {
                    title: '',
                    key: 'actions',
                    render: (_: unknown, e: Employee) => (
                      <Space size={4}>
                        <Button
                          type="link"
                          size="small"
                          onClick={() => {
                            setEditing(e);
                            setModalOpen(true);
                          }}
                        >
                          Изменить
                        </Button>
                        <ConfirmDeleteButton
                          size="small"
                          onConfirm={async () => {
                            await deleteMutation.mutateAsync(e.id);
                            message.success('Сотрудник удалён');
                          }}
                        />
                      </Space>
                    ),
                  },
                ]
              : []),
          ]}
          expandable={{
            expandedRowRender: (e) => <EmployeeSubRecords employee={e} />,
          }}
        />
      )}
      <EmployeeFormModal
        open={modalOpen}
        employee={editing}
        onClose={() => setModalOpen(false)}
      />
    </>
  );
}
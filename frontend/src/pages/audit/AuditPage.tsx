import { Button, Select, Space, Table, Tag, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useState } from 'react';
import type { AuditAction, AuditLogRow } from '@/api/types';
import { PageHeader } from '@/components/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '@/components/States';
import { useAuditLogs } from '@/hooks/queries';

const ACTION_COLORS: Record<AuditAction, string> = {
  insert: 'green',
  update: 'orange',
  delete: 'red',
};

const ACTION_LABELS: Record<AuditAction, string> = {
  insert: 'Создание',
  update: 'Изменение',
  delete: 'Удаление',
};

const ENTITIES = [
  'users',
  'employees',
  'employee_educations',
  'employee_certifications',
  'employee_medical_exams',
  'employee_ppe_records',
  'projects',
  'fields',
  'project_employees',
  'employment_periods',
  'shift_details',
  'vacation_details',
  'sick_leave_details',
  'flight_details',
  'hotel_details',
  'train_details',
  'taxi_details',
  'other_details',
  'financial_records',
  'financial_attachments',
];

export default function AuditPage() {
  const [entity, setEntity] = useState<string | undefined>();
  const [action, setAction] = useState<AuditAction | undefined>();

  const { data, isLoading, isError, refetch } = useAuditLogs({ entity, action });

  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState error="Не удалось загрузить аудит-лог" onRetry={() => void refetch()} />;

  return (
    <>
      <PageHeader
        title="Аудит изменений"
        extra={
          <Space>
            <Select
              allowClear
              placeholder="Сущность"
              value={entity}
              onChange={setEntity}
              style={{ minWidth: 220 }}
              options={ENTITIES.map((e) => ({ value: e, label: e }))}
            />
            <Select
              allowClear
              placeholder="Действие"
              value={action}
              onChange={setAction}
              style={{ minWidth: 140 }}
              options={(Object.keys(ACTION_LABELS) as AuditAction[]).map((a) => ({
                value: a,
                label: ACTION_LABELS[a],
              }))}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void refetch()} />
          </Space>
        }
      />
      {!data?.length ? (
        <EmptyState description="Записей аудита нет" />
      ) : (
        <Table<AuditLogRow>
          rowKey="id"
          dataSource={data}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (t) => `Всего: ${t}`,
          }}
          columns={[
            {
              title: 'Дата',
              dataIndex: 'created_at',
              sorter: (a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf(),
              defaultSortOrder: 'descend',
              render: (v: string) => dayjs(v).format('DD.MM.YYYY HH:mm:ss'),
            },
            {
              title: 'Сущность',
              dataIndex: 'entity_type',
              sorter: (a, b) => a.entity_type.localeCompare(b.entity_type),
            },
            { title: 'ID записи', dataIndex: 'entity_id' },
            {
              title: 'Действие',
              dataIndex: 'action',
              render: (a: AuditAction) => (
                <Tag color={ACTION_COLORS[a]}>{ACTION_LABELS[a]}</Tag>
              ),
            },
            {
              title: 'Автор',
              dataIndex: 'actor_id',
              render: (v: string | null) => v ?? 'система',
            },
          ]}
          expandable={{
            expandedRowRender: (row) => (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Typography.Text strong>Было:</Typography.Text>
                <pre style={{ margin: 0 }}>{JSON.stringify(row.old_values ?? {}, null, 2)}</pre>
                <Typography.Text strong>Стало:</Typography.Text>
                <pre style={{ margin: 0 }}>{JSON.stringify(row.new_values ?? {}, null, 2)}</pre>
              </Space>
            ),
          }}
        />
      )}
    </>
  );
}
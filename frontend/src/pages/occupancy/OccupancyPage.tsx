import { App, Button, DatePicker, Select, Space, Table, Tag } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import type { EmploymentPeriod, PeriodType } from '@/api/types';
import { ConfirmDeleteButton } from '@/components/ConfirmDeleteButton';
import { PageHeader } from '@/components/PageHeader';
import { PermissionGate } from '@/components/PermissionGate';
import { EmptyState, ErrorState, LoadingState } from '@/components/States';
import { useDeletePeriod, useViewSnapshot } from '@/hooks/queries';
import { usePermission } from '@/permissions';
import { closeView, subscribeView } from '@/realtime/socket';
import { periodTypeLabel } from './detailRenderers';
import { FinanceDrawer } from './FinanceDrawer';
import { PeriodFormModal } from './PeriodFormModal';

const DT_FORMAT = 'DD.MM.YYYY HH:mm';

export default function OccupancyPage() {
  const { can } = usePermission();
  const { message } = App.useApp();
  const [windowRange, setWindowRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month'),
  ]);
  const [employeeFilter, setEmployeeFilter] = useState<string | undefined>();
  const [modal, setModal] = useState<{ period: EmploymentPeriod | null } | null>(null);
  const [finance, setFinance] = useState<EmploymentPeriod | null>(null);

  const from = windowRange[0].toISOString();
  const to = windowRange[1].toISOString();

  const { data: snapshot, isLoading, isError, refetch } = useViewSnapshot(from, to);
  const deleteMutation = useDeletePeriod();

  // Live-подписка: окно просмотра передаётся на сервер (Socket.IO view:init)
  useEffect(() => {
    subscribeView(from, to);
    return () => closeView();
  }, [from, to]);

  const employeesOptions = useMemo(
    () =>
      (snapshot?.employees ?? []).map((e) => ({
        value: e.id,
        label: `${e.surname} ${e.first_name}${e.patronymic ? ` ${e.patronymic}` : ''}`,
      })),
    [snapshot],
  );

  const fieldOptions = useMemo(() => {
    if (!snapshot) return [];
    const projectName = new Map(snapshot.projects.map((p) => [p.id, p.name]));
    return (snapshot.fields ?? []).map((f) => ({
      value: f.id,
      label: `${projectName.get(f.project_id) ?? '—'} / ${f.name}`,
    }));
  }, [snapshot]);

  const employeeName = useMemo(() => {
    const map = new Map(employeesOptions.map((o) => [o.value, o.label]));
    return (id: string) => map.get(id) ?? id;
  }, [employeesOptions]);

  const periods = useMemo(() => {
    const list = snapshot?.periods ?? [];
    if (!employeeFilter) return list;
    return list.filter((p) => p.employee_id === employeeFilter);
  }, [snapshot, employeeFilter]);

  if (isLoading) return <LoadingState />;
  if (isError)
    return (
      <ErrorState error="Не удалось загрузить данные за выбранный период" onRetry={() => void refetch()} />
    );

  return (
    <>
      <PageHeader
        title="Занятость"
        extra={
          <Space>
            <DatePicker.RangePicker
              allowClear={false}
              value={windowRange}
              onChange={(range) => {
                if (range?.[0] && range[1]) {
                  setWindowRange([range[0], range[1]]);
                }
              }}
            />
            <Select
              allowClear
              placeholder="Все сотрудники"
              value={employeeFilter}
              onChange={setEmployeeFilter}
              showSearch
              optionFilterProp="label"
              style={{ minWidth: 220 }}
              options={employeesOptions}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void refetch()} />
            <PermissionGate action="occupancy:manage">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setModal({ period: null })}
              >
                Добавить период
              </Button>
            </PermissionGate>
          </Space>
        }
      />

      {!periods.length ? (
        <EmptyState description="За выбранный период периодов занятости нет" />
      ) : (
        <Table<EmploymentPeriod>
          rowKey="id"
          dataSource={periods}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (t) => `Всего: ${t}`,
          }}
          columns={[
            {
              title: 'Сотрудник',
              key: 'employee',
              sorter: (a, b) =>
                employeeName(a.employee_id).localeCompare(employeeName(b.employee_id)),
              render: (_, p) => <strong>{employeeName(p.employee_id)}</strong>,
            },
            {
              title: 'Вид',
              dataIndex: 'period_type',
              sorter: (a, b) => a.period_type.localeCompare(b.period_type),
              render: (t: PeriodType) => <Tag color="blue">{periodTypeLabel(t)}</Tag>,
            },
            {
              title: 'Начало',
              dataIndex: 'started_at',
              sorter: (a, b) => dayjs(a.started_at).valueOf() - dayjs(b.started_at).valueOf(),
              render: (v: string) => dayjs(v).format(DT_FORMAT),
            },
            {
              title: 'Окончание',
              dataIndex: 'ended_at',
              render: (v: string | null) => (v ? dayjs(v).format(DT_FORMAT) : '—'),
            },
            {
              title: 'Версия',
              dataIndex: 'version',
              width: 80,
              render: (v: number) => <Tag>{`v${v}`}</Tag>,
            },
            {
              title: '',
              key: 'actions',
              width: 240,
              render: (_, p) => (
                <Space size={4}>
                  <Button type="link" size="small" onClick={() => setFinance(p)}>
                    Финансы
                  </Button>
                  {can('occupancy:manage') && (
                    <>
                      <Button type="link" size="small" onClick={() => setModal({ period: p })}>
                        Изменить
                      </Button>
                      <ConfirmDeleteButton
                        size="small"
                        title="Удалить период?"
                        description="Запись будет помечена неактивной (мягкое удаление) и попадет в аудит."
                        onConfirm={async () => {
                          await deleteMutation.mutateAsync(p.id);
                          message.success('Период удалён');
                        }}
                      />
                    </>
                  )}
                </Space>
              ),
            },
          ]}
        />
      )}

      {modal ? (
        <PeriodFormModal
          open
          period={modal.period}
          employeesOptions={employeesOptions}
          fieldOptions={fieldOptions}
          onClose={() => setModal(null)}
        />
      ) : null}

      <FinanceDrawer
        periodId={finance?.id ?? ''}
        periodTitle={finance ? `${employeeName(finance.employee_id)} — ${periodTypeLabel(finance.period_type)}` : ''}
        open={Boolean(finance)}
        onClose={() => setFinance(null)}
      />
    </>
  );
}
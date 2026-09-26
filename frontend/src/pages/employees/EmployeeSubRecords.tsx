import {
  App,
  Button,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Space,
  Table,
  Tabs,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useMemo, useState, type ReactNode } from 'react';
import type { Employee } from '@/api/types';
import { apiErrorMessage } from '@/api/client';
import { ConfirmDeleteButton } from '@/components/ConfirmDeleteButton';
import { EmptyState, LoadingState } from '@/components/States';
import {
  useCreateSubRecord,
  useDeleteSubRecord,
  useSubRecords,
  useUpdateSubRecord,
} from '@/hooks/queries';

type Resource = 'educations' | 'certifications' | 'medical-exams' | 'ppe-records';

interface ColumnDef {
  key: string;
  title: string;
  render: (record: Record<string, unknown>) => ReactNode;
}

interface ResourceConfig {
  label: string;
  columns: ColumnDef[];
  formFields: ReactNode;
  toPayload: (values: Record<string, unknown>) => Record<string, unknown>;
}

const DATE = 'YYYY-MM-DD';

function dateCol(key: string, title: string): ColumnDef {
  return {
    key,
    title,
    render: (r) => (r[key] ? dayjs(String(r[key])).format(DATE) : '—'),
  };
}

const CONFIGS: Record<Resource, ResourceConfig> = {
  educations: {
    label: 'Образование',
    columns: [
      { key: 'title', title: 'Название', render: (r) => String(r.title ?? '') },
      { key: 'institution', title: 'Учреждение', render: (r) => String(r.institution ?? '—') },
      { key: 'graduated_at', title: 'Год окончания', render: (r) => String(r.graduated_at ?? '—') },
    ],
    formFields: (
      <>
        <Form.Item name="title" label="Название" rules={[{ required: true, message: 'Обязательно' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="institution" label="Учреждение">
          <Input />
        </Form.Item>
        <Form.Item name="graduated_at" label="Год окончания">
          <InputNumber min={1950} max={2100} style={{ width: '100%' }} />
        </Form.Item>
      </>
    ),
    toPayload: (v) => v,
  },
  certifications: {
    label: 'Сертификаты',
    columns: [
      { key: 'title', title: 'Название', render: (r) => String(r.title ?? '') },
      dateCol('issued_at', 'Выдан'),
      dateCol('expires_at', 'Действителен до'),
    ],
    formFields: (
      <>
        <Form.Item name="title" label="Название" rules={[{ required: true, message: 'Обязательно' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="issued_at" label="Дата выдачи">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="expires_at" label="Действителен до (срок давности)">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
      </>
    ),
    toPayload: (v) => ({
      ...v,
      issued_at: v.issued_at ? dayjs(v.issued_at as string).format(DATE) : null,
      expires_at: v.expires_at ? dayjs(v.expires_at as string).format(DATE) : null,
    }),
  },
  'medical-exams': {
    label: 'Медосмотры',
    columns: [
      dateCol('exam_date', 'Дата осмотра'),
      dateCol('expires_at', 'Действителен до'),
      { key: 'conclusion', title: 'Заключение', render: (r) => String(r.conclusion ?? '—') },
    ],
    formFields: (
      <>
        <Form.Item
          name="exam_date"
          label="Дата осмотра"
          rules={[{ required: true, message: 'Обязательно' }]}
        >
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="expires_at" label="Действителен до (срок давности)">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="conclusion" label="Заключение">
          <Input.TextArea rows={2} />
        </Form.Item>
      </>
    ),
    toPayload: (v) => ({
      ...v,
      exam_date: dayjs(v.exam_date as string).format(DATE),
      expires_at: v.expires_at ? dayjs(v.expires_at as string).format(DATE) : null,
    }),
  },
  'ppe-records': {
    label: 'СИЗ и одежда',
    columns: [
      { key: 'item_name', title: 'Наименование', render: (r) => String(r.item_name ?? '') },
      dateCol('issued_at', 'Выдано'),
      dateCol('expires_at', 'Действителен до'),
    ],
    formFields: (
      <>
        <Form.Item
          name="item_name"
          label="Наименование"
          rules={[{ required: true, message: 'Обязательно' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="issued_at"
          label="Дата выдачи"
          rules={[{ required: true, message: 'Обязательно' }]}
        >
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="expires_at" label="Действителен до (срок давности)">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
      </>
    ),
    toPayload: (v) => ({
      ...v,
      issued_at: dayjs(v.issued_at as string).format(DATE),
      expires_at: v.expires_at ? dayjs(v.expires_at as string).format(DATE) : null,
    }),
  },
};

interface SubRecordModalProps {
  resource: Resource;
  record: Record<string, unknown> | null;
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
}

function SubRecordModal({ resource, record, onClose, onSubmit }: SubRecordModalProps) {
  const [form] = Form.useForm();
  const config = CONFIGS[resource];
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const initial = useMemo(() => ({ ...(record ?? {}) }), [record]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await onSubmit(config.toPayload(values));
      message.success('Запись сохранена');
      onClose();
    } catch (error) {
      if (error instanceof Error || typeof error === 'object') {
        message.error(apiErrorMessage(error));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open
      title={record ? `Редактировать: ${config.label}` : `Добавить: ${config.label}`}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Form form={form} layout="vertical" initialValues={initial}>
        {config.formFields}
      </Form>
    </Modal>
  );
}

interface Props {
  employee: Employee;
}

/** Вкладки суб-записей сотрудника: образование, сертификаты, медосмотры, СИЗ. */
export function EmployeeSubRecords({ employee }: Props) {
  const [active, setActive] = useState<Resource>('educations');
  const [modal, setModal] = useState<{
    resource: Resource;
    record: Record<string, unknown> | null;
  } | null>(null);

  const { data, isLoading, isError, refetch } = useSubRecords<Record<string, unknown>>(
    employee.id,
    active,
  );
  const createMutation = useCreateSubRecord(employee.id, active);
  const updateMutation = useUpdateSubRecord(employee.id, active);
  const deleteMutation = useDeleteSubRecord(employee.id, active);
  const config = CONFIGS[active];

  const items = (Object.keys(CONFIGS) as Resource[]).map((resource) => ({
    key: resource,
    label: CONFIGS[resource].label,
  }));

  return (
    <>
      <Tabs activeKey={active} onChange={(k) => setActive(k as Resource)} items={items} />
      {isLoading ? (
        <LoadingState rows={2} />
      ) : isError ? (
        <Space>
          <span>Ошибка загрузки</span>
          <Button onClick={() => void refetch()}>Повторить</Button>
        </Space>
      ) : !data?.length ? (
        <EmptyState description={`Записей «${config.label}» нет`} />
      ) : (
        <Table<Record<string, unknown>>
          rowKey="id"
          size="small"
          dataSource={data}
          pagination={false}
          columns={[
            ...config.columns.map((c) => ({
              title: c.title,
              dataIndex: c.key,
              render: c.render,
            })),
            {
              title: '',
              key: 'actions',
              render: (_, record) => (
                <Space size={4}>
                  <Button
                    size="small"
                    type="link"
                    onClick={() => setModal({ resource: active, record })}
                  >
                    Изменить
                  </Button>
                  <ConfirmDeleteButton
                    size="small"
                    onConfirm={async () => {
                      await deleteMutation.mutateAsync(String(record.id));
                    }}
                  />
                </Space>
              ),
            },
          ]}
        />
      )}
      <Space style={{ marginTop: 12 }}>
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={() => setModal({ resource: active, record: null })}
        >
          Добавить запись
        </Button>
      </Space>
      {modal ? (
        <SubRecordModal
          resource={modal.resource}
          record={modal.record}
          onClose={() => setModal(null)}
          onSubmit={async (payload) => {
            if (modal.record?.id) {
              await updateMutation.mutateAsync({
                recordId: String(modal.record.id),
                data: payload,
              });
            } else {
              await createMutation.mutateAsync({ data: payload });
            }
          }}
        />
      ) : null}
    </>
  );
}
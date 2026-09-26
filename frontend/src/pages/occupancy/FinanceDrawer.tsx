import {
  App,
  Button,
  Descriptions,
  Divider,
  Drawer,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Upload,
} from 'antd';
import { DownloadOutlined, PlusOutlined, UploadOutlined } from '@ant-design/icons';
import { useMemo, useState } from 'react';
import type { Attachment, FinancialRecord, FinancialRecordCreate } from '@/api/types';
import { downloadAttachment } from '@/api/endpoints';
import { apiErrorMessage } from '@/api/client';
import { ConfirmDeleteButton } from '@/components/ConfirmDeleteButton';
import { EmptyState, LoadingState } from '@/components/States';
import {
  useAttachments,
  useCreateFinancialRecord,
  useDeleteAttachment,
  useDeleteFinancialRecord,
  useFinancialRecords,
  useUpdateFinancialRecord,
  useUploadAttachment,
} from '@/hooks/queries';

interface Props {
  periodId: string;
  periodTitle: string;
  open: boolean;
  onClose: () => void;
}

function FinancialFormModal({
  record,
  onClose,
  onSubmit,
}: {
  record: FinancialRecord | null;
  onClose: () => void;
  onSubmit: (data: FinancialRecordCreate) => Promise<void>;
}) {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await onSubmit(values);
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
      title={record ? 'Редактирование записи' : 'Новая запись'}
      onOk={() => void handleOk()}
      onCancel={onClose}
      confirmLoading={loading}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={
          record
            ? { kind: record.kind, amount: record.amount, description: record.description }
            : { kind: 'expense' }
        }
      >
        <Form.Item name="kind" label="Тип" rules={[{ required: true, message: 'Обязательно' }]}>
          <Select
            options={[
              { value: 'income', label: 'Доход' },
              { value: 'expense', label: 'Расход' },
            ]}
          />
        </Form.Item>
        <Form.Item
          name="amount"
          label="Сумма"
          rules={[{ required: true, message: 'Укажите сумму' }]}
        >
          <InputNumber min={0.01} precision={2} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="description" label="Описание">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

function AttachmentsBlock({ record }: { record: FinancialRecord }) {
  const { message } = App.useApp();
  const { data, isLoading } = useAttachments(record.id);
  const uploadMutation = useUploadAttachment(record.id);
  const deleteAttachmentMutation = useDeleteAttachment(record.id);

  const handleDownload = async (attachment: Attachment) => {
    try {
      const blob = await downloadAttachment(attachment.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = attachment.file_name;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      message.error(apiErrorMessage(error));
    }
  };

  if (isLoading) return <LoadingState rows={1} />;

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Upload
        showUploadList={false}
        beforeUpload={(file) => {
          void uploadMutation
            .mutateAsync(file)
            .then(() => message.success('Файл загружен'))
            .catch((error) => message.error(apiErrorMessage(error)));
          return false;
        }}
      >
        <Button icon={<UploadOutlined />}>Загрузить подтверждение</Button>
      </Upload>
      {!data?.length ? (
        <EmptyState description="Подтверждений нет" />
      ) : (
        <Table<Attachment>
          rowKey="id"
          size="small"
          pagination={false}
          dataSource={data}
          columns={[
            { title: 'Файл', dataIndex: 'file_name' },
            {
              title: 'Размер',
              dataIndex: 'size_bytes',
              render: (v: number) => `${(v / 1024).toFixed(1)} КБ`,
            },
            {
              title: '',
              key: 'actions',
              render: (_, a) => (
                <Space size={4}>
                  <Button
                    size="small"
                    type="link"
                    icon={<DownloadOutlined />}
                    onClick={() => void handleDownload(a)}
                  >
                    Скачать
                  </Button>
                  <ConfirmDeleteButton
                    size="small"
                    onConfirm={async () => {
                      await deleteAttachmentMutation.mutateAsync(a.id);
                      message.success('Файл удалён');
                    }}
                  />
                </Space>
              ),
            },
          ]}
        />
      )}
    </Space>
  );
}

/** Финансы периода: доходы/расходы + файлы-подтверждения. */
export function FinanceDrawer({ periodId, periodTitle, open, onClose }: Props) {
  const { message } = App.useApp();
  const { data, isLoading, isError, refetch } = useFinancialRecords(periodId);
  const createMutation = useCreateFinancialRecord(periodId);
  const updateMutation = useUpdateFinancialRecord(periodId);
  const deleteMutation = useDeleteFinancialRecord(periodId);
  const [modal, setModal] = useState<{ record: FinancialRecord | null } | null>(null);

  const totals = useMemo(() => {
    let income = 0;
    let expense = 0;
    for (const r of data ?? []) {
      if (r.kind === 'income') income += r.amount;
      else expense += r.amount;
    }
    return { income, expense, balance: income - expense };
  }, [data]);

  return (
    <Drawer
      title={`Финансы: ${periodTitle}`}
      open={open}
      onClose={onClose}
      width={720}
      extra={
        <Button onClick={() => void refetch()} type="link">
          Обновить
        </Button>
      }
    >
      <Descriptions size="small" column={3} style={{ marginBottom: 12 }}>
        <Descriptions.Item label="Доходы">{totals.income.toFixed(2)}</Descriptions.Item>
        <Descriptions.Item label="Расходы">{totals.expense.toFixed(2)}</Descriptions.Item>
        <Descriptions.Item label="Баланс">{totals.balance.toFixed(2)}</Descriptions.Item>
      </Descriptions>
      <Divider style={{ margin: '0 0 16px' }} />

      {isLoading ? (
        <LoadingState rows={3} />
      ) : isError ? (
        <EmptyState description="Не удалось загрузить финансовые записи" />
      ) : !data?.length ? (
        <EmptyState description="Финансовых записей нет" />
      ) : (
        <Table<FinancialRecord>
          rowKey="id"
          dataSource={data}
          pagination={false}
          columns={[
            {
              title: 'Тип',
              dataIndex: 'kind',
              render: (k: FinancialRecord['kind']) =>
                k === 'income' ? <Tag color="green">Доход</Tag> : <Tag color="red">Расход</Tag>,
            },
            {
              title: 'Сумма',
              dataIndex: 'amount',
              sorter: (a, b) => a.amount - b.amount,
              render: (v: number) => v.toFixed(2),
            },
            { title: 'Описание', dataIndex: 'description', render: (v: string | null) => v ?? '—' },
            {
              title: '',
              key: 'actions',
              render: (_, r) => (
                <Space size={4}>
                  <Button type="link" size="small" onClick={() => setModal({ record: r })}>
                    Изменить
                  </Button>
                  <ConfirmDeleteButton
                    size="small"
                    title="Удалить финансовую запись?"
                    onConfirm={async () => {
                      await deleteMutation.mutateAsync(r.id);
                      message.success('Запись удалена');
                    }}
                  />
                </Space>
              ),
            },
          ]}
          expandable={{
            expandedRowRender: (r) => <AttachmentsBlock record={r} />,
          }}
        />
      )}

      <Space style={{ marginTop: 16 }}>
        <Button type="dashed" icon={<PlusOutlined />} onClick={() => setModal({ record: null })}>
          Добавить запись
        </Button>
      </Space>

      {modal ? (
        <FinancialFormModal
          record={modal.record}
          onClose={() => setModal(null)}
          onSubmit={async (values) => {
            if (modal.record) {
              await updateMutation.mutateAsync({ id: modal.record.id, data: values });
            } else {
              await createMutation.mutateAsync(values);
            }
          }}
        />
      ) : null}
    </Drawer>
  );
}
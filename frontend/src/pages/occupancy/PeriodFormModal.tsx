import { App, DatePicker, Form, Modal, Select, Space, Typography } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo } from 'react';
import type { EmploymentPeriod, PeriodType } from '@/api/types';
import { apiErrorMessage } from '@/api/client';
import { useCreatePeriod, useUpdatePeriod } from '@/hooks/queries';
import {
  detailFieldsFor,
  detailFromRecord,
  detailToPayload,
  PERIOD_TYPE_OPTIONS,
  renderDetailField,
} from './detailRenderers';

interface Props {
  open: boolean;
  period: EmploymentPeriod | null;
  employeesOptions: Array<{ value: string; label: string }>;
  fieldOptions: Array<{ value: string; label: string }>;
  onClose: () => void;
}

export function PeriodFormModal({
  open,
  period,
  employeesOptions,
  fieldOptions,
  onClose,
}: Props) {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const createMutation = useCreatePeriod();
  const updateMutation = useUpdatePeriod();

  const periodType = Form.useWatch('period_type', form) as PeriodType | undefined;
  const detailDefs = useMemo(
    () => detailFieldsFor(periodType ?? 'other', fieldOptions),
    [periodType, fieldOptions],
  );

  useEffect(() => {
    if (!open) return;
    if (period) {
      form.setFieldsValue({
        employee_id: period.employee_id,
        period_type: period.period_type,
        started_at: dayjs(period.started_at),
        ended_at: period.ended_at ? dayjs(period.ended_at) : null,
        details: detailFromRecord(period.detail, period.period_type),
      });
    } else {
      form.resetFields();
    }
  }, [open, period, form]);

  const handleTypeChange = () => {
    form.setFieldsValue({ details: {} });
  };

  const handleOk = async () => {
    try {
      const v = await form.validateFields();
      const common = {
        employee_id: v.employee_id as string,
        period_type: v.period_type as PeriodType,
        started_at: dayjs(v.started_at as string).toISOString(),
        ended_at: v.ended_at ? dayjs(v.ended_at as string).toISOString() : null,
      };
      if (period) {
        await updateMutation.mutateAsync({
          id: period.id,
          data: {
            ...common,
            update_reason: 'обновлен',
            details: detailToPayload(v.details ?? {}, v.period_type as PeriodType),
          },
        });
        message.success('Период обновлён');
      } else {
        await createMutation.mutateAsync({
          ...common,
          details: detailToPayload(v.details ?? {}, v.period_type as PeriodType),
        });
        message.success('Период создан');
      }
      onClose();
    } catch (error) {
      if (error instanceof Error || typeof error === 'object') {
        message.error(apiErrorMessage(error));
      }
    }
  };

  return (
    <Modal
      open={open}
      title={period ? 'Редактирование периода' : 'Новый период занятости'}
      onOk={() => void handleOk()}
      onCancel={onClose}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      okText="Сохранить"
      cancelText="Отмена"
      width={560}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="employee_id"
          label="Сотрудник"
          rules={[{ required: true, message: 'Выберите сотрудника' }]}
        >
          <Select showSearch optionFilterProp="label" options={employeesOptions} />
        </Form.Item>
        <Form.Item
          name="period_type"
          label="Вид занятости"
          rules={[{ required: true, message: 'Выберите вид' }]}
        >
          <Select options={PERIOD_TYPE_OPTIONS} onChange={handleTypeChange} />
        </Form.Item>
        <Space size={16} style={{ display: 'flex', alignItems: 'flex-start' }}>
          <Form.Item
            name="started_at"
            label="Начало"
            rules={[{ required: true, message: 'Укажите начало' }]}
            style={{ flex: 1 }}
          >
            <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="ended_at" label="Окончание" style={{ flex: 1 }}>
            <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: '100%' }} />
          </Form.Item>
        </Space>

        {detailDefs.length > 0 && (
          <>
            <Typography.Text type="secondary">Данные вида</Typography.Text>
            {detailDefs.map((def) => (
              <Form.Item
                key={def.name}
                name={['details', def.name]}
                label={def.label}
                rules={def.required ? [{ required: true, message: 'Обязательно' }] : undefined}
              >
                {renderDetailField(def)}
              </Form.Item>
            ))}
          </>
        )}
      </Form>
    </Modal>
  );
}
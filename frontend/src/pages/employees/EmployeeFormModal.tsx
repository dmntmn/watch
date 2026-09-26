import { App, Form, Input, Modal } from 'antd';
import { useEffect } from 'react';
import type { Employee } from '@/api/types';
import { apiErrorMessage } from '@/api/client';
import {
  useCreateEmployee,
  useEmployees,
  useUpdateEmployee,
} from '@/hooks/queries';

interface Props {
  open: boolean;
  employee: Employee | null;
  onClose: () => void;
}

export function EmployeeFormModal({ open, employee, onClose }: Props) {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const { refetch } = useEmployees();
  const createMutation = useCreateEmployee();
  const updateMutation = useUpdateEmployee();

  useEffect(() => {
    if (!open) return;
    if (employee) {
      form.setFieldsValue({
        email: employee.email,
        phone: employee.phone,
        first_name: employee.first_name,
        surname: employee.surname,
        patronymic: employee.patronymic,
      });
    } else {
      form.resetFields();
    }
  }, [open, employee, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (employee) {
        await updateMutation.mutateAsync({ id: employee.id, data: values });
        message.success('Сотрудник обновлён');
      } else {
        await createMutation.mutateAsync(values);
        message.success('Сотрудник создан');
      }
      void refetch();
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
      title={employee ? 'Редактирование сотрудника' : 'Новый сотрудник'}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="surname"
          label="Фамилия"
          rules={[{ required: true, message: 'Укажите фамилию' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="first_name"
          label="Имя"
          rules={[{ required: true, message: 'Укажите имя' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item name="patronymic" label="Отчество">
          <Input />
        </Form.Item>
        <Form.Item
          name="email"
          label="Email"
          rules={[
            { required: true, message: 'Укажите email' },
            { type: 'email', message: 'Некорректный email' },
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item name="phone" label="Телефон">
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
}
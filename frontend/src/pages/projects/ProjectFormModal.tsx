import { App, Form, Input, Modal } from 'antd';
import { useEffect } from 'react';
import type { Project } from '@/api/types';
import { apiErrorMessage } from '@/api/client';
import { useCreateProject, useUpdateProject } from '@/hooks/queries';

interface Props {
  open: boolean;
  project: Project | null;
  onClose: () => void;
}

export function ProjectFormModal({ open, project, onClose }: Props) {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const createMutation = useCreateProject();
  const updateMutation = useUpdateProject();

  useEffect(() => {
    if (!open) return;
    if (project) {
      form.setFieldsValue({ name: project.name, description: project.description });
    } else {
      form.resetFields();
    }
  }, [open, project, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (project) {
        await updateMutation.mutateAsync({ id: project.id, data: values });
        message.success('Проект обновлён');
      } else {
        await createMutation.mutateAsync(values);
        message.success('Проект создан');
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
      title={project ? 'Редактирование проекта' : 'Новый проект'}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="Название" rules={[{ required: true, message: 'Укажите название' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="description" label="Описание">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
import { App, Button, type ButtonProps } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { apiErrorMessage } from '@/api/client';

interface Props extends Omit<ButtonProps, 'onClick'> {
  title?: string;
  description?: string;
  onConfirm: () => Promise<unknown> | void;
}

/** Кнопка удаления с подтверждением (Modal.confirm) и сообщениями об успехе/ошибке. */
export function ConfirmDeleteButton({
  title = 'Удалить запись?',
  description = 'Действие будет записано в аудит.',
  onConfirm,
  children,
  ...rest
}: Props) {
  const { modal, message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const handleClick = () => {
    modal.confirm({
      title,
      content: description,
      okText: 'Удалить',
      okButtonProps: { danger: true },
      cancelText: 'Отмена',
      onOk: async () => {
        setLoading(true);
        try {
          await onConfirm();
          message.success('Запись удалена');
        } catch (error) {
          message.error(apiErrorMessage(error));
        } finally {
          setLoading(false);
        }
      },
    });
  };

  return (
    <Button danger type="text" icon={<DeleteOutlined />} loading={loading} onClick={handleClick} {...rest}>
      {children}
    </Button>
  );
}
import { Space, Typography } from 'antd';
import type { ReactNode } from 'react';

/** Заголовок страницы с блоком действий справа (flex без inline-стилей). */
export function PageHeader({ title, extra }: { title: ReactNode; extra?: ReactNode }) {
  return (
    <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        {title}
      </Typography.Title>
      {extra ? <Space>{extra}</Space> : null}
    </Space>
  );
}
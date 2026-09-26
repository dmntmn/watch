import { Empty, Result, Skeleton, Spin } from 'antd';

/** Состояние загрузки таблицы/контента. */
export function LoadingState({ rows = 4 }: { rows?: number }) {
  return <Skeleton active paragraph={{ rows }} title={false} />;
}

/** Полноэкранный спиннер страницы. */
export function PageSpinner() {
  return (
    <div style={{ display: 'grid', placeItems: 'center', minHeight: 240 }}>
      <Spin size="large" />
    </div>
  );
}

/** Ошибка запроса с кнопкой повтора. */
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <Result
      status="error"
      title="Не удалось загрузить данные"
      subTitle={error instanceof Error ? error.message : String(error)}
      extra={
        onRetry ? (
          <button type="button" onClick={onRetry}>
            Повторить
          </button>
        ) : undefined
      }
    />
  );
}

/** Пустое состояние списка. */
export function EmptyState({ description = 'Данных пока нет' }: { description?: string }) {
  return <Empty description={description} />;
}
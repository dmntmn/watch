import type { ReactNode } from 'react';
import { usePermission, type Action } from '@/permissions';

/** Скрывает содержимое, если у пользователя нет требуемого действия. */
export function PermissionGate({ action, children }: { action: Action; children: ReactNode }) {
  const { can } = usePermission();
  return can(action) ? <>{children}</> : null;
}
import { useAuth } from '@/auth/useAuth';

/** Действия системы (совпадают с разрешениями backend). */
export type Action =
  | 'read'
  | 'employees:manage'
  | 'projects:manage'
  | 'occupancy:manage'
  | 'audit:read';

/** Группы Keycloak -> действия. */
const GROUP_PERMISSIONS: Record<string, Action[]> = {
  'personnel-managers': ['employees:manage'],
  'project-managers': ['projects:manage'],
  'occupancy-managers': ['occupancy:manage'],
  admin: ['employees:manage', 'projects:manage', 'occupancy:manage', 'audit:read'],
};

function permissionsForGroups(groups: string[]): Set<Action> {
  const perms = new Set<Action>(['read']);
  for (const group of groups) {
    for (const action of GROUP_PERMISSIONS[group] ?? []) {
      perms.add(action);
    }
  }
  return perms;
}

export interface PermissionApi {
  can: (action: Action) => boolean;
  groups: string[];
}

/** Хук прав: скрывает кнопки/меню/маршруты по группам Keycloak. */
export function usePermission(): PermissionApi {
  const { user } = useAuth();
  const groups = user?.groups ?? [];
  const perms = permissionsForGroups(groups);
  return {
    can: (action: Action) => perms.has(action),
    groups,
  };
}
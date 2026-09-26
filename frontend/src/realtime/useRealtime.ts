import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useAuth } from '@/auth/useAuth';
import { connectRealtime, disconnectRealtime, getSocket } from './socket';

interface DataChangedEvent {
  entity: string;
  action: string;
  payload?: Record<string, unknown>;
}

/**
 * Подключает Socket.IO при входе, слушает data:changed и инвалидирует
 * затронутые query-кэши — экраны обновляются без перезагрузки.
 */
export function useRealtime() {
  const { status } = useAuth();
  const qc = useQueryClient();

  useEffect(() => {
    if (status !== 'authenticated') return;
    const socket = connectRealtime();

    const onChange = (event: DataChangedEvent) => {
      const viewKeys = ['view'];
      const entity = event.entity;
      if (entity === 'employee') {
        void qc.invalidateQueries({ queryKey: ['employees'] });
        void qc.invalidateQueries({ queryKey: viewKeys });
      } else if (entity === 'project' || entity === 'field' || entity === 'project_employee') {
        void qc.invalidateQueries({ queryKey: ['projects'] });
        void qc.invalidateQueries({ queryKey: viewKeys });
      } else if (
        entity === 'employment_period' ||
        entity === 'financial_record' ||
        entity === 'attachment'
      ) {
        void qc.invalidateQueries({ queryKey: ['employment-periods'] });
        void qc.invalidateQueries({ queryKey: ['financial'] });
        void qc.invalidateQueries({ queryKey: ['attachments'] });
        void qc.invalidateQueries({ queryKey: viewKeys });
      }
    };

    socket.on('data:changed', onChange);
    return () => {
      socket.off('data:changed', onChange);
      disconnectRealtime();
    };
  }, [status, qc]);

  return { socket: getSocket };
}
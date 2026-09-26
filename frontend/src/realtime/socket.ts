import { io, type Socket } from 'socket.io-client';
import { config } from '@/config';
import { getAccessToken } from '@/auth/keycloak';

let socket: Socket | null = null;

/** Подключение к Socket.IO с токеном в auth (live-обновления). */
export function connectRealtime(): Socket {
  if (!socket) {
    socket = io(config.apiUrl, {
      auth: { token: getAccessToken() },
      transports: ['websocket'],
      reconnectionAttempts: 5,
    });
  }
  return socket;
}

export function getSocket(): Socket | null {
  return socket;
}

export function disconnectRealtime(): void {
  socket?.close();
  socket = null;
}

export function subscribeView(from: string, to: string): void {
  socket?.emit('view:init', { from, to });
}

export function closeView(): void {
  socket?.emit('view:close');
}
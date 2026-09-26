import axios, { AxiosError, type AxiosRequestConfig } from 'axios';
import { config } from '@/config';
import { ensureFreshToken, getAccessToken, keycloak } from '@/auth/keycloak';

const api = axios.create({
  baseURL: `${config.apiUrl}/api/v1`,
  timeout: 30_000,
});

/** Автоматическая подстановка Authorization: Bearer <token> во все запросы. */
api.interceptors.request.use(async (cfg) => {
  await ensureFreshToken();
  const token = getAccessToken();
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`;
  }
  return cfg;
});

/** При 401 — обновляем токен и повторяем запрос один раз; иначе logout. */
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retried?: boolean };
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      try {
        await keycloak.updateToken(0);
        const token = getAccessToken();
        if (token) {
          original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${token}` };
          return api.request(original);
        }
      } catch {
        // токен не удалось обновить
      }
      keycloak.logout({ redirectUri: window.location.origin });
    }
    return Promise.reject(error);
  },
);

/** Человекочитаемое сообщение об ошибке API для message/notification. */
export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (error.message) return error.message;
  }
  return 'Неизвестная ошибка';
}

export default api;
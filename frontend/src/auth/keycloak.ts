import Keycloak from 'keycloak-js';
import { config } from '@/config';

/** Единственный экземпляр Keycloak (OIDC Authorization Code + PKCE). */
export const keycloak = new Keycloak({
  url: config.keycloakUrl,
  realm: config.keycloakRealm,
  clientId: config.keycloakClientId,
});

let initPromise: Promise<boolean> | null = null;

/**
 * Инициализация Keycloak выполняется только один раз за сессию
 * (защита от повторного init при StrictMode-перемонтировании).
 */
export function initKeycloak(): Promise<boolean> {
  if (!initPromise) {
    initPromise = keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256' });
  }
  return initPromise;
}

/** Обновляет токен, если он истекает в ближайшие minValidity секунд. */
export async function ensureFreshToken(minValidity = 30): Promise<void> {
  if (!keycloak.authenticated) return;
  try {
    await keycloak.updateToken(minValidity);
  } catch {
    // Обработкой займётся 401-перехватчик
  }
}

export function getAccessToken(): string | undefined {
  return keycloak.token;
}

/** Группы пользователя из payload access-токена. */
export function getGroups(): string[] {
  const groups = keycloak.tokenParsed?.groups;
  if (Array.isArray(groups)) return groups.map(String);
  if (typeof groups === 'string') return [groups];
  return [];
}
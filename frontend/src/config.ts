/** Конфигурация приложения из переменных окружения (VITE_*). */
export const config = {
  apiUrl: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  keycloakUrl: import.meta.env.VITE_KEYCLOAK_URL ?? 'http://localhost:8080',
  keycloakRealm: import.meta.env.VITE_KEYCLOAK_REALM ?? 'watch',
  keycloakClientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? 'watch-frontend',
} as const;
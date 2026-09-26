import { Button, Result } from 'antd';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/auth/useAuth';

/** Страница-заглушка: обычно Keycloak сразу перенаправляет на логин. */
export default function LoginPage() {
  const { status, login } = useAuth();

  if (status === 'authenticated') return <Navigate to="/occupancy" replace />;

  return (
    <Result
      status="info"
      title="Вход через Keycloak"
      subTitle="Авторизация выполняется через внешний провайдер (OIDC Authorization Code + PKCE)."
      extra={
        <Button type="primary" onClick={login}>
          Войти
        </Button>
      }
    />
  );
}
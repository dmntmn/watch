import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { initKeycloak, keycloak } from './keycloak';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

export interface AuthUser {
  sub?: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  groups: string[];
}

interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  login: () => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function parseUser(): AuthUser {
  const parsed = keycloak.tokenParsed;
  return {
    sub: parsed?.sub,
    email: parsed?.email,
    firstName: parsed?.given_name,
    lastName: parsed?.family_name,
    groups: Array.isArray(parsed?.groups) ? parsed.groups.map(String) : [],
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let active = true;
    initKeycloak()
      .then((authenticated) => {
        if (!active) return;
        if (authenticated) {
          setUser(parseUser());
          setStatus('authenticated');
        } else {
          setStatus('unauthenticated');
        }
      })
      .catch(() => {
        if (active) setStatus('unauthenticated');
      });
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(() => {
    keycloak.login();
  }, []);

  const logout = useCallback(() => {
    keycloak.logout({ redirectUri: window.location.origin });
  }, []);

  const value = useMemo(
    () => ({ status, user, login, logout }),
    [status, user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
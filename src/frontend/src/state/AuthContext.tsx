import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi } from "../api/endpoints";
import { setAuthToken, getAuthToken, SESSION_EXPIRED_EVENT } from "../api/client";
import type { UserResponse } from "../api/types";

interface AuthContextValue {
  user: UserResponse | null;
  loading: boolean;
  sessionExpired: boolean;
  dismissSessionExpired: () => void;
  login: (email: string, password: string) => Promise<UserResponse>;
  signup: (email: string, password: string, role: "candidate" | "recruiter") => Promise<UserResponse>;
  logout: () => void;
  withdraw: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    // 새로고침 시 sessionStorage에 토큰이 남아있으면 /me로 세션 복원
    if (getAuthToken()) {
      authApi
        .me()
        .then(setUser)
        .catch(() => setAuthToken(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // 세션 도중 토큰이 만료/무효화되면(api/client.ts) 로그인 화면으로
    // 자연스럽게 돌아가도록 user를 비운다 — ProtectedRoute가 리다이렉트한다.
    function handleSessionExpired() {
      setUser(null);
      setSessionExpired(true);
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await authApi.login(email, password);
    setAuthToken(access_token);
    const me = await authApi.me();
    setUser(me);
    setSessionExpired(false);
    return me;
  }

  async function signup(email: string, password: string, role: "candidate" | "recruiter") {
    await authApi.signup(email, password, role);
    return login(email, password);
  }

  function logout() {
    setAuthToken(null);
    setUser(null);
  }

  async function withdraw() {
    await authApi.withdraw();
    logout();
  }

  function dismissSessionExpired() {
    setSessionExpired(false);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, sessionExpired, dismissSessionExpired, login, signup, logout, withdraw }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

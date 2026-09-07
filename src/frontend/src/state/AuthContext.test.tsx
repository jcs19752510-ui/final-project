import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "./AuthContext";
import { SESSION_EXPIRED_EVENT, getAuthToken, setAuthToken } from "../api/client";
import { authApi } from "../api/endpoints";

vi.mock("../api/endpoints", () => ({
  authApi: {
    login: vi.fn(),
    signup: vi.fn(),
    me: vi.fn(),
    withdraw: vi.fn(),
  },
}));

const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>;

describe("AuthContext", () => {
  beforeEach(() => {
    sessionStorage.clear();
    setAuthToken(null); // client.ts의 인메모리 토큰은 sessionStorage.clear()로 안 지워짐
    vi.clearAllMocks();
  });

  afterEach(() => {
    sessionStorage.clear();
    setAuthToken(null);
  });

  it("로그인 성공 시 user를 채우고 토큰을 저장한다", async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: "tok-1", token_type: "bearer" });
    vi.mocked(authApi.me).mockResolvedValue({ id: "u1", email: "a@example.com", role: "candidate" });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login("a@example.com", "pw12345678");
    });

    expect(result.current.user).toEqual({ id: "u1", email: "a@example.com", role: "candidate" });
    expect(getAuthToken()).toBe("tok-1");
  });

  it("로그인 실패 시 user는 그대로 null이고 에러가 전파된다", async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error("invalid credentials"));

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await expect(
      act(async () => {
        await result.current.login("a@example.com", "wrong");
      })
    ).rejects.toThrow("invalid credentials");

    expect(result.current.user).toBeNull();
  });

  it("logout()은 user와 토큰을 모두 비운다", async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: "tok-2", token_type: "bearer" });
    vi.mocked(authApi.me).mockResolvedValue({ id: "u2", email: "b@example.com", role: "recruiter" });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      await result.current.login("b@example.com", "pw12345678");
    });
    expect(result.current.user).not.toBeNull();

    act(() => result.current.logout());

    expect(result.current.user).toBeNull();
    expect(getAuthToken()).toBeNull();
  });

  it("세션만료 이벤트가 오면 user를 비우고 sessionExpired를 true로 만든다", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
    });

    expect(result.current.sessionExpired).toBe(true);

    act(() => result.current.dismissSessionExpired());
    expect(result.current.sessionExpired).toBe(false);
  });

  it("signup()은 가입 후 자동으로 로그인까지 수행한다", async () => {
    vi.mocked(authApi.signup).mockResolvedValue({ id: "u3", email: "c@example.com", role: "candidate" });
    vi.mocked(authApi.login).mockResolvedValue({ access_token: "tok-3", token_type: "bearer" });
    vi.mocked(authApi.me).mockResolvedValue({ id: "u3", email: "c@example.com", role: "candidate" });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.signup("c@example.com", "pw12345678", "candidate");
    });

    expect(authApi.signup).toHaveBeenCalledWith("c@example.com", "pw12345678", "candidate");
    expect(authApi.login).toHaveBeenCalledWith("c@example.com", "pw12345678");
    expect(result.current.user?.email).toBe("c@example.com");
  });
});

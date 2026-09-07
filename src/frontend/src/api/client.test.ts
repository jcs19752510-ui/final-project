import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest, getAuthToken, setAuthToken, SESSION_EXPIRED_EVENT } from "./client";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiRequest / ApiError 파싱", () => {
  beforeEach(() => {
    setAuthToken(null);
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("정상 응답(JSON)을 그대로 반환한다", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { id: "1" }));
    const result = await apiRequest<{ id: string }>("/api/v1/whatever");
    expect(result).toEqual({ id: "1" });
  });

  it("204 응답은 undefined를 반환한다", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }));
    const result = await apiRequest("/api/v1/whatever", { method: "POST" });
    expect(result).toBeUndefined();
  });

  it("{error:{code,message}} 바디를 ApiError로 정확히 변환한다", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(409, { error: { code: "CONFLICT", message: "완료된 면접만 리포트를 생성할 수 있습니다." } })
    );
    await expect(apiRequest("/api/v1/x")).rejects.toMatchObject({
      status: 409,
      code: "CONFLICT",
      message: "완료된 면접만 리포트를 생성할 수 있습니다.",
    });
  });

  it("JSON이 아닌 에러 바디는 기본 메시지로 폴백한다", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("<html>500</html>", { status: 500 }));
    await expect(apiRequest("/api/v1/x")).rejects.toMatchObject({
      status: 500,
      code: "UNKNOWN_ERROR",
    });
  });

  it("토큰이 있으면 Authorization 헤더를 붙이고, auth:false면 안 붙인다", async () => {
    setAuthToken("tok123");
    vi.mocked(fetch).mockImplementation(async () => jsonResponse(200, {}));

    await apiRequest("/api/v1/protected");
    const authedHeaders = vi.mocked(fetch).mock.calls[0][1]?.headers as Record<string, string>;
    expect(authedHeaders["Authorization"]).toBe("Bearer tok123");

    await apiRequest("/api/v1/public", { auth: false });
    const publicHeaders = vi.mocked(fetch).mock.calls[1][1]?.headers as Record<string, string>;
    expect(publicHeaders["Authorization"]).toBeUndefined();
  });

  it("인증된 요청이 401을 받으면 토큰을 지우고 세션만료 이벤트를 쏜다", async () => {
    setAuthToken("expired-token");
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, { error: { code: "NOT_AUTHENTICATED", message: "토큰이 만료되었습니다." } })
    );

    const handler = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, handler);
    await expect(apiRequest("/api/v1/protected")).rejects.toBeInstanceOf(ApiError);
    window.removeEventListener(SESSION_EXPIRED_EVENT, handler);

    expect(handler).toHaveBeenCalledOnce();
    expect(getAuthToken()).toBeNull();
  });

  it("토큰 없이 보낸 요청이 401을 받아도 세션만료 이벤트는 쏘지 않는다(원래 비로그인 상태)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, { error: { code: "NOT_AUTHENTICATED", message: "토큰 없음" } })
    );

    const handler = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, handler);
    await expect(apiRequest("/api/v1/auth/me")).rejects.toBeInstanceOf(ApiError);
    window.removeEventListener(SESSION_EXPIRED_EVENT, handler);

    expect(handler).not.toHaveBeenCalled();
  });
});

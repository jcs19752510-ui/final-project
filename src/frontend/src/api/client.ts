import type { ApiErrorBody } from "./types";

// 2026-09-18(Next.js 전환): Vite의 VITE_ 접두사 대신 Next.js의
// NEXT_PUBLIC_ 접두사를 사용해야 클라이언트 번들에 값이 실린다.
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// Next.js는 클라이언트 컴포넌트도 최초 HTML을 서버에서 한 번 렌더링한다
// (SSR pass) — 그 시점엔 `sessionStorage`가 없는 Node 환경이라, 모듈 최상단
// 평가 시 바로 호출하면 서버에서 죽는다. `typeof window` 가드로 방어.
let authToken: string | null =
  typeof window !== "undefined" ? sessionStorage.getItem("aimock_token") : null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    sessionStorage.setItem("aimock_token", token);
  } else {
    sessionStorage.removeItem("aimock_token");
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

// 인증된 요청이 401로 거부되면(토큰 만료 등) 전역 이벤트로 알림.
// AuthContext가 이를 구독해 user를 비우고, ProtectedRoute가 자연히 /login으로
// 보낸다(TRD §0-1 "인증 가드"의 연장선 — 세션 만료 시 방치되지 않도록).
export const SESSION_EXPIRED_EVENT = "aimock:session-expired";

async function parseError(res: Response): Promise<never> {
  let code = "UNKNOWN_ERROR";
  let message = `요청이 실패했습니다 (HTTP ${res.status})`;
  try {
    const body = (await res.json()) as Partial<ApiErrorBody>;
    if (body.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
    }
  } catch {
    // 응답 본문이 JSON이 아닌 경우 기본 메시지 사용
  }
  throw new ApiError(res.status, code, message);
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  formData?: FormData;
  auth?: boolean;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, auth = true } = options;
  const isAuthenticatedRequest = auth && !!authToken;
  const headers: Record<string, string> = {};
  if (isAuthenticatedRequest) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  let requestBody: BodyInit | undefined;
  if (formData) {
    requestBody = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    requestBody = JSON.stringify(body);
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: requestBody,
  });

  if (!res.ok) {
    if (res.status === 401 && isAuthenticatedRequest) {
      setAuthToken(null);
      window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
    }
    await parseError(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

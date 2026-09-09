import { apiRequest } from "./client";
import type {
  CodeSubmissionResponse,
  InterviewSummary,
  MediaAssetResponse,
  ReportResponse,
  StartInterviewResponse,
  StatsResponse,
  TokenResponse,
  TurnResponse,
  UserResponse,
  WhiteboardSnapshotResponse,
} from "./types";

export const authApi = {
  signup: (email: string, password: string, role: "candidate" | "recruiter") =>
    apiRequest<UserResponse>("/api/v1/auth/signup", {
      method: "POST",
      body: { email, password, role },
      auth: false,
    }),
  login: (email: string, password: string) =>
    apiRequest<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),
  me: () => apiRequest<UserResponse>("/api/v1/auth/me"),
  withdraw: () => apiRequest<void>("/api/v1/auth/withdraw", { method: "POST" }),
};

export const interviewApi = {
  start: (jobRole: string) =>
    apiRequest<StartInterviewResponse>("/api/v1/interviews", {
      method: "POST",
      body: { job_role: jobRole },
    }),
  submitTurn: (interviewId: string, turnIndex: number, audio: Blob) => {
    const form = new FormData();
    form.append("turn_index", String(turnIndex));
    form.append("audio", audio, "turn.webm");
    return apiRequest<TurnResponse>(`/api/v1/interviews/${interviewId}/turns`, {
      method: "POST",
      formData: form,
    });
  },
  end: (interviewId: string) =>
    apiRequest<void>(`/api/v1/interviews/${interviewId}/end`, { method: "POST" }),
};

export const codingApi = {
  submit: (interviewId: string, language: "python" | "javascript", code: string) =>
    apiRequest<CodeSubmissionResponse>(`/api/v1/interviews/${interviewId}/coding-submissions`, {
      method: "POST",
      body: { language, code },
    }),
};

export const reportApi = {
  generate: (interviewId: string) =>
    apiRequest<ReportResponse>(`/api/v1/interviews/${interviewId}/report`, { method: "POST" }),
  get: (interviewId: string) =>
    apiRequest<ReportResponse>(`/api/v1/interviews/${interviewId}/report`),
};

export const mediaApi = {
  list: (interviewId: string) =>
    apiRequest<MediaAssetResponse[]>(`/api/v1/interviews/${interviewId}/media`),
  delete: (mediaId: string) => apiRequest<void>(`/api/v1/media/${mediaId}`, { method: "DELETE" }),
  uploadFrame: (interviewId: string, turnIndex: number, frame: Blob) => {
    const form = new FormData();
    form.append("kind", "video_frame");
    form.append("turn_index", String(turnIndex));
    form.append("file", frame, "frame.jpg");
    return apiRequest<MediaAssetResponse>(`/api/v1/interviews/${interviewId}/media`, {
      method: "POST",
      formData: form,
    });
  },
};

export const whiteboardApi = {
  submit: (interviewId: string, image: Blob) => {
    const form = new FormData();
    form.append("file", image, "whiteboard.png");
    return apiRequest<WhiteboardSnapshotResponse>(
      `/api/v1/interviews/${interviewId}/whiteboard-snapshots`,
      { method: "POST", formData: form }
    );
  },
  list: (interviewId: string) =>
    apiRequest<WhiteboardSnapshotResponse[]>(`/api/v1/interviews/${interviewId}/whiteboard-snapshots`),
};

export const recruiterApi = {
  listInterviews: () => apiRequest<InterviewSummary[]>("/api/v1/recruiter/interviews"),
  getReport: (interviewId: string) =>
    apiRequest<ReportResponse>(`/api/v1/recruiter/interviews/${interviewId}/report`),
  stats: () => apiRequest<StatsResponse>("/api/v1/recruiter/stats"),
};

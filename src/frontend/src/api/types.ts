// 백엔드 Pydantic 스키마와 1:1 대응 (src/backend/app/schemas/*.py 기준, 원본 우선 원칙)

export type Role = "candidate" | "recruiter";

export interface UserResponse {
  id: string;
  email: string;
  role: Role;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ApiErrorBody {
  error: { code: string; message: string };
}

export interface StartInterviewResponse {
  interview_id: string;
  question_text: string;
}

export interface TurnResponse {
  question_text: string;
  ended: boolean;
}

export interface CodeSubmissionResponse {
  submission_id: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  timed_out: boolean;
}

export interface ReportResponse {
  interview_id: string;
  technical_score: number | null;
  communication_score: number | null;
  cultural_fit_score: number | null;
  summary_text: string | null;
  details_json: Record<string, unknown>;
}

export interface InterviewSummary {
  interview_id: string;
  candidate_email: string;
  job_role: string;
  status: string;
  pass_recommendation: boolean | null;
}

export interface MediaAssetResponse {
  id: string;
  kind: string;
  turn_index: number;
  created_at: string;
}

export interface StatsResponse {
  total_interviews: number;
  completed_interviews: number;
  avg_technical_score: number | null;
  avg_communication_score: number | null;
  avg_cultural_fit_score: number | null;
}

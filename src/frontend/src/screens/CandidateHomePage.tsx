"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../state/AuthContext";
import { interviewApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import { FIRST_QUESTION_STORAGE_PREFIX } from "./InterviewPage";

export function CandidateHomePage() {
  const { user, withdraw } = useAuth();
  const router = useRouter();
  const [jobRole, setJobRole] = useState("백엔드 개발자");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [confirmingWithdraw, setConfirmingWithdraw] = useState(false);

  async function handleStart(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setStarting(true);
    try {
      const res = await interviewApi.start(jobRole);
      // 2026-09-18(Next.js 전환): react-router의 navigate(path, {state})는
      // Next.js 라우터에 대응하는 기능이 없어, 다음 페이지가 그 즉시(모달
      // 없이) 읽어갈 수 있게 sessionStorage로 1회성 전달한다(InterviewPage가
      // 마운트 시 읽고 곧바로 지움).
      sessionStorage.setItem(FIRST_QUESTION_STORAGE_PREFIX + res.interview_id, res.question_text);
      router.push(`/interview/${res.interview_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "면접을 시작하지 못했습니다.");
    } finally {
      setStarting(false);
    }
  }

  async function handleWithdraw() {
    await withdraw();
    router.push("/login");
  }

  return (
    <div className="page">
      <h1>안녕하세요, {user?.email}님</h1>

      <section className="card">
        <h2>새 모의면접 시작</h2>
        <form onSubmit={handleStart}>
          <label htmlFor="job-role">지원 직무</label>
          <input id="job-role" value={jobRole} onChange={(e) => setJobRole(e.target.value)} required />
          <p className="hint">
            입력하신 직무에 맞춰 AI 면접관이 질문을 생성합니다. 원하는 직무로
            자유롭게 바꿔서 시작할 수 있습니다.
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={starting}>
            {starting ? "시작하는 중..." : "면접 시작"}
          </button>
        </form>
      </section>

      <section className="card danger-zone">
        <h2>계정 탈퇴</h2>
        {!confirmingWithdraw ? (
          <button className="danger" onClick={() => setConfirmingWithdraw(true)}>
            회원 탈퇴
          </button>
        ) : (
          <div role="alertdialog" aria-label="탈퇴 확인">
            <p>정말 탈퇴하시겠습니까? 30일 내 재로그인하면 계정이 복구됩니다.</p>
            <button className="danger" onClick={handleWithdraw}>
              확인, 탈퇴합니다
            </button>
            <button onClick={() => setConfirmingWithdraw(false)}>취소</button>
          </div>
        )}
      </section>
    </div>
  );
}

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { interviewApi } from "../api/endpoints";
import { ApiError } from "../api/client";

export function CandidateHomePage() {
  const { user, withdraw } = useAuth();
  const navigate = useNavigate();
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
      navigate(`/interview/${res.interview_id}`, { state: { firstQuestion: res.question_text } });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "면접을 시작하지 못했습니다.");
    } finally {
      setStarting(false);
    }
  }

  async function handleWithdraw() {
    await withdraw();
    navigate("/login");
  }

  return (
    <div className="page">
      <h1>안녕하세요, {user?.email}님</h1>

      <section className="card">
        <h2>새 모의면접 시작</h2>
        <form onSubmit={handleStart}>
          <label htmlFor="job-role">지원 직무</label>
          <input id="job-role" value={jobRole} onChange={(e) => setJobRole(e.target.value)} required />
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

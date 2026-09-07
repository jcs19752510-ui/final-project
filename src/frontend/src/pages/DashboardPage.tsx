import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { recruiterApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { InterviewSummary, StatsResponse } from "../api/types";

export function DashboardPage() {
  const [interviews, setInterviews] = useState<InterviewSummary[] | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([recruiterApi.listInterviews(), recruiterApi.stats()])
      .then(([list, s]) => {
        setInterviews(list);
        setStats(s);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "대시보드를 불러오지 못했습니다.");
      });
  }, []);

  return (
    <div className="page">
      <h1>채용담당자 대시보드</h1>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {stats && (
        <div className="card score-row">
          <ScoreBadge label="전체 면접" value={stats.total_interviews} />
          <ScoreBadge label="완료" value={stats.completed_interviews} />
          <ScoreBadge label="평균 기술점수" value={stats.avg_technical_score} />
          <ScoreBadge label="평균 커뮤니케이션" value={stats.avg_communication_score} />
          <ScoreBadge label="평균 조직적합성" value={stats.avg_cultural_fit_score} />
        </div>
      )}

      <div className="card">
        <h2>지원자 목록</h2>
        {interviews === null && <p>불러오는 중...</p>}
        {interviews?.length === 0 && <p>아직 지원자 면접 기록이 없습니다.</p>}
        <table className="candidate-table">
          <thead>
            <tr>
              <th>지원자</th>
              <th>직무</th>
              <th>상태</th>
              <th>추천 여부</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {interviews?.map((i) => (
              <tr key={i.interview_id}>
                <td>{i.candidate_email}</td>
                <td>{i.job_role}</td>
                <td>{i.status}</td>
                <td>{i.pass_recommendation === null ? "-" : i.pass_recommendation ? "추천" : "비추천"}</td>
                <td>
                  <Link to={`/dashboard/report/${i.interview_id}`}>리포트 보기</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScoreBadge({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="score-badge">
      <span className="score-label">{label}</span>
      <span className="score-value">{value ?? "-"}</span>
    </div>
  );
}

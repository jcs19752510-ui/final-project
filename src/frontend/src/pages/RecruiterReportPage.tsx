import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { recruiterApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import { ReportDetails } from "../components/ReportDetails";
import type { ReportResponse } from "../api/types";

export function RecruiterReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    recruiterApi
      .getReport(id)
      .then(setReport)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "리포트를 불러오지 못했습니다.");
      });
  }, [id]);

  return (
    <div className="page">
      <Link to="/dashboard">← 대시보드로</Link>
      <h1>지원자 리포트</h1>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {report && (
        <div className="card">
          <div className="score-row">
            <ScoreBadge label="기술" value={report.technical_score} />
            <ScoreBadge label="커뮤니케이션" value={report.communication_score} />
            <ScoreBadge label="조직 적합성" value={report.cultural_fit_score} />
          </div>
          <h3>요약</h3>
          <p>{report.summary_text ?? "요약 정보가 없습니다."}</p>
          <ReportDetails details={report.details_json} />
        </div>
      )}
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

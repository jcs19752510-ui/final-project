import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { recruiterApi } from "../api/endpoints";
import { ApiError } from "../api/client";
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
            <span>기술: {report.technical_score ?? "-"}</span>
            <span>커뮤니케이션: {report.communication_score ?? "-"}</span>
            <span>조직 적합성: {report.cultural_fit_score ?? "-"}</span>
          </div>
          <h3>요약</h3>
          <p>{report.summary_text ?? "요약 정보가 없습니다."}</p>
          <h3>상세</h3>
          <pre className="output-block">{JSON.stringify(report.details_json, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { mediaApi, reportApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { MediaAssetResponse, ReportResponse } from "../api/types";

type ViewState =
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "conflict"; message: string }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string }
  | { kind: "ready"; report: ReportResponse };

export function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [state, setState] = useState<ViewState>({ kind: "loading" });
  const [generating, setGenerating] = useState(false);

  async function load() {
    if (!id) return;
    setState({ kind: "loading" });
    try {
      const report = await reportApi.get(id);
      setState({ kind: "ready", report });
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setState({ kind: "not-found" });
      } else if (err instanceof ApiError && err.status === 503) {
        setState({ kind: "unavailable", message: err.message });
      } else if (err instanceof ApiError) {
        setState({ kind: "error", message: err.message });
      } else {
        setState({ kind: "error", message: "리포트를 불러오지 못했습니다." });
      }
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleGenerate() {
    if (!id) return;
    setGenerating(true);
    try {
      const report = await reportApi.generate(id);
      setState({ kind: "ready", report });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // 409는 "리포트가 이미 생성 중"이 아니라 서버가 그때그때 알려주는
        // 충돌 사유(예: "완료된 면접만 리포트를 생성할 수 있습니다")를 의미
        // (원본 코드 우선 원칙 — src/backend/app/services/report_service.py
        // generate_report()의 ConflictError 실제 발생 조건을 재확인 후 수정).
        setState({ kind: "conflict", message: err.message });
      } else if (err instanceof ApiError && err.status === 503) {
        setState({ kind: "unavailable", message: err.message });
      } else if (err instanceof ApiError) {
        setState({ kind: "error", message: err.message });
      }
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="page">
      <h1>피드백 리포트</h1>
      {state.kind === "loading" && <p>불러오는 중...</p>}
      {state.kind === "not-found" && (
        <div className="card">
          <p>아직 생성된 리포트가 없습니다.</p>
          <button onClick={handleGenerate} disabled={generating}>
            {generating ? "생성 중..." : "리포트 생성하기"}
          </button>
        </div>
      )}
      {state.kind === "conflict" && (
        <p className="form-error" role="alert">
          {state.message}
        </p>
      )}
      {state.kind === "unavailable" && (
        <p className="form-error" role="alert">
          {state.message}
        </p>
      )}
      {state.kind === "error" && (
        <p className="form-error" role="alert">
          {state.message}
        </p>
      )}
      {state.kind === "ready" && (
        <div className="card">
          <div className="score-row">
            <ScoreBadge label="기술" value={state.report.technical_score} />
            <ScoreBadge label="커뮤니케이션" value={state.report.communication_score} />
            <ScoreBadge label="조직 적합성" value={state.report.cultural_fit_score} />
          </div>
          <h3>요약</h3>
          <p>{state.report.summary_text ?? "요약 정보가 없습니다."}</p>
          <h3>상세</h3>
          <pre className="output-block">{JSON.stringify(state.report.details_json, null, 2)}</pre>
          <p className="hint">표정/음성 비언어 지표(U3-b)는 아직 준비 중입니다.</p>
        </div>
      )}
      {id && <MediaManager interviewId={id} />}
    </div>
  );
}

function MediaManager({ interviewId }: { interviewId: string }) {
  const [items, setItems] = useState<MediaAssetResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function load() {
    try {
      const list = await mediaApi.list(interviewId);
      setItems(list);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "원본 미디어 목록을 불러오지 못했습니다.");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interviewId]);

  async function handleDelete(mediaId: string) {
    setDeletingId(mediaId);
    setError(null);
    try {
      await mediaApi.delete(mediaId);
      setItems((prev) => (prev ? prev.filter((m) => m.id !== mediaId) : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "삭제에 실패했습니다.");
    } finally {
      setDeletingId(null);
    }
  }

  if (items === null) return null;

  return (
    <div className="card">
      <h3>원본 답변 오디오 관리</h3>
      <p className="hint">
        면접 중 제출한 원본 오디오는 삭제를 요청하기 전까지 암호화되어 보관됩니다(ADR-004).
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {items.length === 0 ? (
        <p className="hint">저장된 원본 오디오가 없습니다.</p>
      ) : (
        <ul className="media-list">
          {items.map((m) => (
            <li key={m.id}>
              <span>
                턴 {m.turn_index + 1} · {m.kind} · {new Date(m.created_at).toLocaleString()}
              </span>
              <button
                className="danger"
                onClick={() => handleDelete(m.id)}
                disabled={deletingId === m.id}
              >
                {deletingId === m.id ? "삭제 중..." : "삭제"}
              </button>
            </li>
          ))}
        </ul>
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

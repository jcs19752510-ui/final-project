import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { codingApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { CodeSubmissionResponse } from "../api/types";

const DEFAULT_CODE = "def solve():\n    # 여기에 코드를 작성하세요\n    return 42\n\nprint(solve())\n";

export function CodingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [code, setCode] = useState(DEFAULT_CODE);
  const [result, setResult] = useState<CodeSubmissionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!id) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const res = await codingApi.submit(id, code);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "코드 실행에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>라이브 코딩 (Python)</h1>
      <p className="hint">실행 시간이 5초를 넘으면 자동으로 타임아웃됩니다.</p>
      <div className="editor-wrap">
        <Editor
          height="360px"
          defaultLanguage="python"
          value={code}
          onChange={(v) => setCode(v ?? "")}
          options={{ minimap: { enabled: false }, fontSize: 14 }}
        />
      </div>
      <button onClick={handleSubmit} disabled={submitting}>
        {submitting ? "실행 중..." : "코드 실행 및 제출"}
      </button>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {result && (
        <div className="card result-card">
          <h3>실행 결과 {result.timed_out && <span className="badge-warn">타임아웃</span>}</h3>
          <p>종료 코드: {result.exit_code ?? "N/A"}</p>
          <pre className="output-block">{result.stdout || "(표준출력 없음)"}</pre>
          {result.stderr && (
            <>
              <p>에러 출력:</p>
              <pre className="output-block error">{result.stderr}</pre>
            </>
          )}
        </div>
      )}
      <button className="secondary" onClick={() => navigate(`/report/${id}`)}>
        리포트 화면으로 이동
      </button>
    </div>
  );
}

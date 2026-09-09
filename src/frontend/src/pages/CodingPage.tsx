import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { codingApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { CodeSubmissionResponse } from "../api/types";

type Language = "python" | "javascript";

// 2026-09-09(REQ-F-004 갭 해소): Python만 지원하던 것을 JavaScript까지
// 확장. 언어 전환 시 에디터 내용을 그 언어의 기본 템플릿으로 바꿔준다
// (Python 코드를 JS로 그대로 두면 문법 에러만 나서 혼란스러움).
const DEFAULT_CODE: Record<Language, string> = {
  python: "def solve():\n    # 여기에 코드를 작성하세요\n    return 42\n\nprint(solve())\n",
  javascript: "function solve() {\n  // 여기에 코드를 작성하세요\n  return 42;\n}\n\nconsole.log(solve());\n",
};

export function CodingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [language, setLanguage] = useState<Language>("python");
  const [code, setCode] = useState(DEFAULT_CODE.python);
  const [result, setResult] = useState<CodeSubmissionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handleLanguageChange(next: Language) {
    setLanguage(next);
    // 사용자가 이미 뭔가 작성했다면 그 내용을 지우지 않는다 — 기본
    // 템플릿 그대로일 때만(변경 안 했을 때만) 바꿔준다.
    setCode((prev) => (Object.values(DEFAULT_CODE).includes(prev) ? DEFAULT_CODE[next] : prev));
  }

  async function handleSubmit() {
    if (!id) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const res = await codingApi.submit(id, language, code);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "코드 실행에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>라이브 코딩</h1>
      <p className="hint">
        실행 시간이 5초를 넘으면 자동으로 타임아웃됩니다. JavaScript는 Python과 달리 네트워크
        접근이 완전히 차단되지 않습니다 — 상세는 관리자에게 문의하세요.
      </p>
      <div className="language-select">
        <label htmlFor="coding-language">언어</label>
        <select
          id="coding-language"
          value={language}
          onChange={(e) => handleLanguageChange(e.target.value as Language)}
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
        </select>
      </div>
      <div className="editor-wrap">
        <Editor
          height="360px"
          language={language}
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
      <button className="secondary" onClick={() => navigate(`/interview/${id}/whiteboard`)}>
        화이트보드로 이동
      </button>
    </div>
  );
}

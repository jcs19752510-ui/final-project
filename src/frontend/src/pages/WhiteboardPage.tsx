import { useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { whiteboardApi } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { WhiteboardSnapshotResponse } from "../api/types";

const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 480;

// 원안 F-005: 시스템 설계 화이트보드. 마우스/터치로 자유롭게 그린 다음
// PNG로 캡처해 업로드하면 Gemini Vision이 설계를 평가해준다(사람 승인,
// AskUserQuestion 2026-09-09 — "Gemini 재활성화").
export function WhiteboardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawingRef = useRef(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);

  const [hasDrawing, setHasDrawing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<WhiteboardSnapshotResponse | null>(null);

  function getContext(): CanvasRenderingContext2D | null {
    return canvasRef.current?.getContext("2d") ?? null;
  }

  function pointFromEvent(e: React.PointerEvent<HTMLCanvasElement>): { x: number; y: number } {
    const rect = canvasRef.current!.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function handlePointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    drawingRef.current = true;
    lastPointRef.current = pointFromEvent(e);
    setHasDrawing(true);
  }

  function handlePointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current) return;
    const ctx = getContext();
    const from = lastPointRef.current;
    const to = pointFromEvent(e);
    if (!ctx || !from) return;
    ctx.strokeStyle = "#1a1a1a";
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
    lastPointRef.current = to;
  }

  function handlePointerUp() {
    drawingRef.current = false;
    lastPointRef.current = null;
  }

  function handleClear() {
    const canvas = canvasRef.current;
    const ctx = getContext();
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawing(false);
    setSnapshot(null);
  }

  async function handleSubmit() {
    const canvas = canvasRef.current;
    if (!id || !canvas) return;
    setSubmitting(true);
    setError(null);
    try {
      const blob: Blob | null = await new Promise((resolve) =>
        canvas.toBlob((b) => resolve(b), "image/png")
      );
      if (!blob) throw new Error("이미지 캡처에 실패했습니다.");
      const res = await whiteboardApi.submit(id, blob);
      setSnapshot(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "화이트보드 평가 요청에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>시스템 설계 화이트보드 (선택)</h1>
      <p className="hint">
        마우스나 터치로 시스템 설계를 자유롭게 그려보세요. AI가 구성요소·데이터 흐름·확장성
        관점에서 피드백을 드립니다. 이 단계는 건너뛰어도 괜찮습니다.
      </p>

      <div className="whiteboard-canvas-wrap">
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          className="whiteboard-canvas"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        />
      </div>

      <div className="whiteboard-actions">
        <button className="secondary" onClick={handleClear} disabled={submitting}>
          지우기
        </button>
        <button onClick={handleSubmit} disabled={submitting || !hasDrawing}>
          {submitting ? "평가 중..." : "AI 평가 요청"}
        </button>
      </div>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {snapshot && (
        <div className="card result-card">
          <h3>AI 피드백</h3>
          <p>{snapshot.ai_feedback_text}</p>
        </div>
      )}

      <button className="secondary" onClick={() => navigate(`/report/${id}`)}>
        리포트 화면으로 이동
      </button>
    </div>
  );
}

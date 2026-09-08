import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { interviewApi, mediaApi } from "../api/endpoints";
import { ApiError } from "../api/client";

export function InterviewPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation() as { state?: { firstQuestion?: string } };
  const navigate = useNavigate();

  const [question, setQuestion] = useState(location.state?.firstQuestion ?? "질문을 불러오는 중...");
  const [turnIndex, setTurnIndex] = useState(0);
  const [recording, setRecording] = useState(false);
  const [ended, setEnded] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const videoStreamRef = useRef<MediaStream | null>(null);

  // U3-b(표정 분석) — 면접 화면 진입 시 카메라를 한 번만 켜서 작은
  // 미리보기로 계속 띄워두고(지원자가 촬영 중임을 눈으로 확인할 수 있게),
  // 답변을 제출할 때마다 그 순간의 프레임 한 장을 자동으로 캡처해 같이
  // 업로드한다. 사용자가 별도로 사진을 찍는 조작을 하지 않아도 된다.
  useEffect(() => {
    let cancelled = false;
    navigator.mediaDevices
      .getUserMedia({ video: { width: 320, height: 240 } })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        videoStreamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraReady(true);
      })
      .catch(() => {
        setCameraError("카메라 접근에 실패했습니다. 표정 분석 없이 음성 답변만 진행됩니다.");
      });

    return () => {
      cancelled = true;
      videoStreamRef.current?.getTracks().forEach((t) => t.stop());
      videoStreamRef.current = null;
    };
  }, []);

  function captureFrameBlob(): Promise<Blob | null> {
    return new Promise((resolve) => {
      const video = videoRef.current;
      // 2026-09-08 버그 수정: 예전엔 화면에서 숨긴(hidden, display:none)
      // <canvas> DOM 엘리먼트를 재사용했는데, 실제 사용자 테스트에서 캡처된
      // 프레임 14장이 전부 완전히 새까맣게 찍히는 것을 발견했다(표정분석이
      // 계속 "unknown"으로 나온 진짜 원인 — DeepFace 문제가 아니었음).
      // display:none 캔버스에 비디오 프레임을 그리면 일부 브라우저(특히
      // GPU 가속 비디오 디코드 환경)에서 빈 화면이 찍히는 알려진 문제와
      // 일치 — DOM에 아예 붙이지 않는 인메모리 캔버스로 교체해 회피.
      // video.videoWidth가 아직 0이면(카메라는 열렸지만 첫 프레임이 아직
      // 디코딩되기 전) 캡처를 건너뛴다 — 빈 화면을 억지로 찍는 대신
      // 이번 턴은 표정 데이터 없이 넘어가고 다음 턴에 다시 시도.
      if (!video || !cameraReady || video.videoWidth === 0 || video.videoHeight === 0) {
        resolve(null);
        return;
      }
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        resolve(null);
        return;
      }
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.8);
    });
  }

  async function uploadFrameForTurn(turn: number) {
    if (!id) return;
    try {
      const frame = await captureFrameBlob();
      if (frame) await mediaApi.uploadFrame(id, turn, frame);
    } catch {
      // 표정 캡처/업로드 실패는 면접 진행 자체를 막지 않는다(부가 기능).
    }
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        void submitTurn(blob);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setError("마이크 접근에 실패했습니다. 아래 '오디오 파일로 답변 제출'을 이용해 주세요.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void submitTurn(file);
    e.target.value = "";
  }

  async function submitTurn(audio: Blob) {
    if (!id) return;
    setSubmitting(true);
    setError(null);
    const thisTurn = turnIndex;
    void uploadFrameForTurn(thisTurn); // 답변 제출과 동시에, 실패해도 서로 영향 없음
    try {
      const res = await interviewApi.submitTurn(id, thisTurn, audio);
      setQuestion(res.question_text);
      setTurnIndex((i) => i + 1);
      if (res.ended) setEnded(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "답변 제출에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinish() {
    if (!id) return;
    setSubmitting(true);
    try {
      await interviewApi.end(id);
      navigate(`/interview/${id}/coding`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "면접 종료 처리에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>면접장 (턴 {turnIndex + 1})</h1>

      <div className="camera-preview">
        <video ref={videoRef} autoPlay muted playsInline />
        {cameraReady && <span className="camera-live-badge">촬영 중</span>}
        {cameraError && <p className="hint">{cameraError}</p>}
      </div>

      <div className="card">
        <p className="question-text">{question}</p>

        {!ended ? (
          <>
            {!recording ? (
              <button onClick={startRecording} disabled={submitting}>
                녹음 시작
              </button>
            ) : (
              <button onClick={stopRecording}>녹음 종료 및 제출</button>
            )}
            <div className="fallback-upload">
              <label htmlFor="audio-file">또는 오디오 파일로 답변 제출</label>
              <input id="audio-file" type="file" accept="audio/*" onChange={handleFileUpload} disabled={submitting} />
            </div>
            {submitting && <p>답변을 제출하는 중...</p>}
          </>
        ) : (
          <button onClick={handleFinish} disabled={submitting}>
            면접 종료하고 코딩 테스트로 이동
          </button>
        )}

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}

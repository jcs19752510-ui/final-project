// 리포트 "상세" 영역을 사람이 읽기 좋게 보여주는 공용 컴포넌트.
// 2026-09-08 재설계 — 원래는 `details_json`을 그대로
// `JSON.stringify(..., null, 2)`로 화면에 찍어내고 있었음(개발자 디버그
// 화면 수준, 마스터 TRD F-006이 요구하는 "리포트"에 못 미침). 후보자용
// ReportPage.tsx와 채용담당자용 RecruiterReportPage.tsx가 동일한
// details_json 구조를 쓰므로 공용 컴포넌트로 분리.
interface VoiceProsodyEntry {
  turn_index: number;
  pitch_mean_hz: number;
  energy_mean: number;
}

interface EmotionEntry {
  turn_index: number;
  dominant_emotion: string;
  confidence: number;
}

interface ReportDetailsData {
  keywords?: string[];
  star_analysis?: string;
  pass_recommendation?: boolean;
  voice_prosody?: VoiceProsodyEntry[];
  emotion_timeline?: EmotionEntry[];
}

const EMOTION_LABELS: Record<string, string> = {
  neutral: "무표정",
  happy: "긍정적",
  sad: "슬픔",
  angry: "화남",
  surprise: "놀람",
  fear: "불안",
  disgust: "불쾌",
  unknown: "인식 안 됨",
};

export function ReportDetails({ details }: { details: Record<string, unknown> }) {
  const data = details as ReportDetailsData;
  const keywords = data.keywords ?? [];
  const prosody = data.voice_prosody ?? [];
  const emotions = data.emotion_timeline ?? [];
  const emotionsDetected = emotions.filter((e) => e.dominant_emotion !== "unknown");

  return (
    <div className="report-details">
      {data.pass_recommendation !== undefined && (
        <span className={`pass-badge ${data.pass_recommendation ? "pass" : "fail"}`}>
          {data.pass_recommendation ? "합격 추천" : "합격 보류"}
        </span>
      )}

      {data.star_analysis && (
        <section>
          <h3>STAR 분석</h3>
          <p>{data.star_analysis}</p>
        </section>
      )}

      {keywords.length > 0 && (
        <section>
          <h3>핵심 키워드</h3>
          <div className="keyword-tags">
            {keywords.map((k, i) => (
              <span className="keyword-tag" key={`${k}-${i}`}>
                {k}
              </span>
            ))}
          </div>
        </section>
      )}

      {emotions.length > 0 && (
        <section>
          <h3>표정 타임라인</h3>
          {emotionsDetected.length === 0 && (
            <p className="hint">
              캡처된 프레임 {emotions.length}장에서 표정을 인식하지 못했습니다(카메라 화질/각도
              문제일 수 있습니다).
            </p>
          )}
          <table className="report-table">
            <thead>
              <tr>
                <th>턴</th>
                <th>표정</th>
                <th>신뢰도</th>
              </tr>
            </thead>
            <tbody>
              {emotions.map((e) => (
                <tr key={e.turn_index}>
                  <td>{e.turn_index + 1}</td>
                  <td>{EMOTION_LABELS[e.dominant_emotion] ?? e.dominant_emotion}</td>
                  <td>{e.dominant_emotion === "unknown" ? "-" : `${Math.round(e.confidence * 100)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {prosody.length > 0 && (
        <section>
          <h3>음성 운율</h3>
          <table className="report-table">
            <thead>
              <tr>
                <th>턴</th>
                <th>평균 피치(Hz)</th>
                <th>발화 에너지</th>
              </tr>
            </thead>
            <tbody>
              {prosody.map((p) => (
                <tr key={p.turn_index}>
                  <td>{p.turn_index + 1}</td>
                  <td>{p.pitch_mean_hz > 0 ? p.pitch_mean_hz.toFixed(1) : "-"}</td>
                  <td>{p.energy_mean > 0 ? p.energy_mean.toFixed(4) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

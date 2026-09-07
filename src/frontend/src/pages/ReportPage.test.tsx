import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReportPage } from "./ReportPage";
import { reportApi, mediaApi } from "../api/endpoints";
import { ApiError } from "../api/client";

vi.mock("../api/endpoints", () => ({
  reportApi: {
    get: vi.fn(),
    generate: vi.fn(),
  },
  mediaApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}));

function renderAt(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/report/${id}`]}>
      <Routes>
        <Route path="/report/:id" element={<ReportPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ReportPage — 409 처리 회귀 테스트", () => {
  beforeEach(() => {
    vi.mocked(mediaApi.list).mockResolvedValue([]);
  });

  // 2026-09-07 발견된 버그: 409를 "리포트를 이미 생성 중"이라고 하드코딩된
  // 문구로 잘못 안내했음. 실제로는 report_service.generate_report()의 유일한
  // 409 조건이 "면접이 아직 completed 상태가 아님"이라, 서버가 주는 실제
  // 메시지를 그대로 보여줘야 한다(원본 우선 원칙). 재발 방지용 테스트.
  it("리포트 생성 409 응답은 서버의 실제 메시지를 그대로 보여준다 ('생성 중'이 아니다)", async () => {
    vi.mocked(reportApi.get).mockRejectedValue(new ApiError(404, "NOT_FOUND", "아직 생성된 리포트가 없습니다."));
    vi.mocked(reportApi.generate).mockRejectedValue(
      new ApiError(409, "CONFLICT", "완료된 면접만 리포트를 생성할 수 있습니다.")
    );

    renderAt("interview-1");

    const generateButton = await screen.findByRole("button", { name: "리포트 생성하기" });
    generateButton.click();

    await waitFor(() => {
      expect(screen.getByText("완료된 면접만 리포트를 생성할 수 있습니다.")).toBeInTheDocument();
    });
    expect(screen.queryByText(/이미 생성하는 중/)).not.toBeInTheDocument();
  });

  it("503(SERVICE_UNAVAILABLE)은 unavailable 메시지를 그대로 보여준다", async () => {
    vi.mocked(reportApi.get).mockRejectedValue(
      new ApiError(503, "SERVICE_UNAVAILABLE", "리포트 생성 AI가 아직 준비되지 않았습니다(GEMINI_API_KEY 미설정).")
    );

    renderAt("interview-2");

    await waitFor(() => {
      expect(
        screen.getByText("리포트 생성 AI가 아직 준비되지 않았습니다(GEMINI_API_KEY 미설정).")
      ).toBeInTheDocument();
    });
  });

  it("정상 리포트는 점수와 요약을 렌더링한다", async () => {
    vi.mocked(reportApi.get).mockResolvedValue({
      interview_id: "interview-3",
      technical_score: 4,
      communication_score: 3,
      cultural_fit_score: 5,
      summary_text: "테스트 요약입니다.",
      details_json: { keywords: ["테스트"] },
    });

    renderAt("interview-3");

    await waitFor(() => {
      expect(screen.getByText("테스트 요약입니다.")).toBeInTheDocument();
    });
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  // AC-M6: 지원자가 리포트 화면에서 원본 오디오 삭제를 요청할 수 있어야 한다.
  it("원본 오디오 목록을 보여주고, 삭제 버튼을 누르면 목록에서 사라진다", async () => {
    vi.mocked(reportApi.get).mockRejectedValue(new ApiError(404, "NOT_FOUND", "아직 생성된 리포트가 없습니다."));
    vi.mocked(mediaApi.list).mockResolvedValue([
      { id: "media-1", kind: "audio", turn_index: 0, created_at: "2026-09-08T00:00:00Z" },
    ]);
    vi.mocked(mediaApi.delete).mockResolvedValue(undefined);

    renderAt("interview-4");

    await screen.findByText(/턴 1/);
    const deleteButton = screen.getByRole("button", { name: "삭제" });
    deleteButton.click();

    await waitFor(() => {
      expect(mediaApi.delete).toHaveBeenCalledWith("media-1");
      expect(screen.getByText("저장된 원본 오디오가 없습니다.")).toBeInTheDocument();
    });
  });
});

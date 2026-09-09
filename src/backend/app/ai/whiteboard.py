"""화이트보드(시스템 설계) 이미지를 Vision LLM으로 평가.

docs/trd/aimock_u2c_trd.md §2/§3 (2026-09-09 신규, 원안 F-005 착수).

2026-09-09 결정(사용자 AskUserQuestion 응답, "Gemini 재활성화"): 이 앱의
텍스트 대화 LLM은 Gemini 무료 티어 일일 한도 소진으로 Groq로 전환했지만
(app/ai/llm.py 상단 이력 참조), 화이트보드는 처음부터 별도 기능이라 텍스트
파이프라인과 무관하게 공급자를 독립적으로 고를 수 있다. Groq도 비전 모델을
제공하지만, 사용자가 명시적으로 Gemini를 선택했으므로 여기서는 Groq 대안
구현을 만들지 않는다(어댑터 패턴은 유지 — 나중에 필요하면 GroqVisionEvaluator
를 추가하기만 하면 됨).
"""

import logging
from abc import ABC, abstractmethod

from app.ai.gemini_errors import describe_gemini_error
from app.config import settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger("aimock.whiteboard")

WHITEBOARD_SYSTEM_PROMPT = (
    "당신은 시스템 설계 면접관입니다. 지원자가 화이트보드에 그린 시스템 설계 "
    "다이어그램 이미지를 보고, 직무 맥락에 맞춰 다음을 한국어로 간결하게 "
    "평가하십시오: (1) 표현된 구성요소와 데이터 흐름이 타당한지, (2) 확장성/"
    "장애 대응 등 놓친 고려사항, (3) 개선 제안. 인구통계적 특징은 절대 "
    "평가에 반영하지 마십시오(공정성 원칙). 3~6문장의 자연어 피드백만 "
    "출력하고, JSON이나 마크다운 헤더 같은 형식을 쓰지 마십시오."
)

FALLBACK_FEEDBACK = "화이트보드 평가 생성에 실패했습니다 — 채용 담당자의 수동 검토가 필요합니다."


class WhiteboardEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, image_bytes: bytes, mime_type: str, job_role: str) -> str: ...


class GeminiWhiteboardEvaluator(WhiteboardEvaluator):
    """모델명은 app/ai/llm.py GeminiProvider와 동일 판단 근거로 `-latest` 별칭 사용."""

    def __init__(self, model: str = "gemini-flash-lite-latest"):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.gemini_api_key:
                raise ServiceUnavailableError(
                    "화이트보드 평가 AI가 아직 준비되지 않았습니다(GEMINI_API_KEY 미설정). "
                    "https://aistudio.google.com 에서 무료 키를 발급받아 .env에 넣으세요."
                )
            import google.genai as genai

            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    async def evaluate(self, image_bytes: bytes, mime_type: str, job_role: str) -> str:
        from google.genai import errors, types

        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    f"직무: {job_role}\n\n이 화이트보드 이미지를 평가해주세요.",
                ],
                config=types.GenerateContentConfig(system_instruction=WHITEBOARD_SYSTEM_PROMPT),
            )
        except errors.APIError as exc:
            logger.warning("Gemini Vision 화이트보드 평가 실패: %s", exc)
            raise ServiceUnavailableError(describe_gemini_error(exc)) from exc
        return (response.text or "").strip() or FALLBACK_FEEDBACK

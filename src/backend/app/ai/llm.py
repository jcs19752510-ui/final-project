"""ADR-002: LLM은 Google Gemini 무료 티어. docs/trd/aimock_u3a_trd.md §2/§3.

원본 기획서 §5.1.2의 "구조화된 출력" 원칙: LLM 응답은 항상 JSON으로 강제하고
Pydantic으로 검증한다. 스키마를 어긴 응답은 안전한 폴백으로 흡수한다(AC-4).
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.config import settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger("aimock.llm")

FALLBACK_REPLY = "죄송합니다, 다음 질문으로 이어가겠습니다. 이전 프로젝트에서 가장 어려웠던 기술적 문제는 무엇이었나요?"

SYSTEM_PROMPT = (
    "당신은 15년 차 시니어 개발자 면접관입니다. 지원자의 답변이 모호할 경우 "
    "즉시 정답을 알려주지 말고 힌트를 주어 유도하십시오. 기술 용어 사용의 "
    "정확성을 평가하되, 인종·성별·억양 등 인구통계적 특징은 절대 언급하거나 "
    "평가에 반영하지 마십시오(공정성 원칙). 반드시 지정된 JSON 스키마로만 "
    "응답하십시오."
)


@dataclass
class ConversationContext:
    job_role: str
    history: list[dict[str, str]] = field(default_factory=list)  # [{speaker, text}]
    candidate_questions: list[str] = field(default_factory=list)


class LLMTurnResult(BaseModel):
    reply_text: str
    action: Literal["ask_question", "end_interview"]
    evaluation: dict | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate_next_turn(self, context: ConversationContext) -> LLMTurnResult: ...


class GeminiProvider(LLMProvider):
    """실제 구현. GEMINI_API_KEY가 없으면 호출 시점에만 예외 발생(지연 초기화)."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.gemini_api_key:
                raise ServiceUnavailableError(
                    "AI 면접관이 아직 준비되지 않았습니다(GEMINI_API_KEY 미설정). "
                    "https://aistudio.google.com 에서 무료 키를 발급받아 .env에 "
                    "넣으세요 (ADR-002 참조)."
                )
            import google.genai as genai

            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def _build_contents(self, context: ConversationContext) -> str:
        history_text = "\n".join(f"{turn['speaker']}: {turn['text']}" for turn in context.history)
        hints = "\n".join(f"- {q}" for q in context.candidate_questions)
        return (
            f"직무: {context.job_role}\n\n"
            f"[대화 이력]\n{history_text}\n\n"
            f"[참고 가능한 질문 후보]\n{hints}\n\n"
            '다음 JSON 스키마로만 응답하세요: '
            '{"reply_text": "면접관 발화(질문 또는 종료 인사)", '
            '"action": "ask_question 또는 end_interview", '
            '"evaluation": {"technical_accuracy": 1-5, "key_observations": ["..."]} (선택)}'
        )

    async def generate_next_turn(self, context: ConversationContext) -> LLMTurnResult:
        from google.genai import types

        client = self._get_client()
        response = await client.aio.models.generate_content(
            model=self._model,
            contents=self._build_contents(context),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        return _parse_or_fallback(response.text)


def _parse_or_fallback(raw_text: str | None) -> LLMTurnResult:
    """AC-4: 스키마 불일치 시 서버가 죽지 않고 안전한 폴백으로 진행."""
    try:
        data = json.loads(raw_text or "")
        return LLMTurnResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("LLM 응답 스키마 불일치, 폴백 사용: %s", exc)
        return LLMTurnResult(reply_text=FALLBACK_REPLY, action="ask_question", evaluation=None)

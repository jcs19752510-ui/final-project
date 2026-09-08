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

from app.ai.gemini_errors import describe_gemini_error
from app.ai.groq_errors import describe_groq_error
from app.config import settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger("aimock.llm")

FALLBACK_REPLY = "죄송합니다, 다음 질문으로 이어가겠습니다. 이전 프로젝트에서 가장 어려웠던 기술적 문제는 무엇이었나요?"

SYSTEM_PROMPT = (
    "당신은 15년 차 시니어 개발자 면접관입니다. 지원자의 답변이 모호할 경우 "
    "즉시 정답을 알려주지 말고 힌트를 주어 유도하십시오. 기술 용어 사용의 "
    "정확성을 평가하되, 인종·성별·억양 등 인구통계적 특징은 절대 언급하거나 "
    "평가에 반영하지 마십시오(공정성 원칙). "
    "[참고 가능한 질문 후보]는 아이디어를 위한 참고 자료일 뿐입니다 — "
    "그대로 베끼지 말고, 반드시 [대화 이력]에서 지원자가 방금 한 답변의 "
    "구체적인 내용(언급한 기술/프로젝트/경험)을 이어받아 새로운 후속 질문을 "
    "만드십시오. 이미 [대화 이력]에 나온 것과 같거나 거의 같은 질문을 "
    "다시 하지 마십시오(2026-09-08 추가 — 실사용 중 동일 질문 반복 문제 "
    "발견). 반드시 지정된 JSON 스키마로만 응답하십시오."
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


def _build_user_message(context: ConversationContext) -> str:
    """Gemini/Groq 공용 — 대화 이력 + 질문 후보를 하나의 사용자 메시지로."""
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


class GeminiProvider(LLMProvider):
    """실제 구현. GEMINI_API_KEY가 없으면 호출 시점에만 예외 발생(지연 초기화).

    모델명 이력(2026-09-08, 실제 키로 검증하며 3회 변경):
    1. `gemini-2.0-flash` → 서비스 종료(404) 발견, `-latest` 별칭으로 교체.
    2. `gemini-flash-latest` → 그 시점에 구글 쪽 일시적 과부하(503,
       "high demand")로 실패 확인 → 안정 버전인 `gemini-2.5-flash-lite`로
       고정.
    3. `gemini-2.5-flash-lite` → **무료 티어 일일 한도(모델당 하루 20건,
       `GenerateRequestsPerDayPerProjectPerModel-FreeTier`)를 실제 사용
       중(개발 테스트 + 사용자 실사용) 소진해 429 RESOURCE_EXHAUSTED
       발생을 실제 면접 화면에서 재현·확인**. 특정 모델 버전을 고정하면
       (a) 언제 단종될지 모르고 (b) 그 모델의 개별 일일 쿼터가 소진되면
       똑같이 막힌다는 두 문제를 동시에 겪음 → **다시 `-latest` 별칭
       (`gemini-flash-lite-latest`)으로 전환**. 별칭은 구글이 내부적으로
       현재 권장 모델로 매핑하고, 쿼터도 그 시점의 실제 모델 기준으로
       추적되어 특정 구버전 쿼터 고갈의 영향을 덜 받는다.
    ⚠️ 무료 티어 자체가 "모델당 하루 20건"으로 매우 작다 — 면접 1회
    (턴마다 1건 + 리포트 생성 1건)만 해도 금방 소진될 수 있음. 실사용이
    잦아지면 유료 티어 전환 검토 필요(사람 결정 사항).
    """

    def __init__(self, model: str = "gemini-flash-lite-latest"):
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

    async def generate_next_turn(self, context: ConversationContext) -> LLMTurnResult:
        from google.genai import errors, types

        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=_build_user_message(context),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                ),
            )
        except errors.APIError as exc:
            # Gemini 쪽 오류(모델 단종/쿼터 초과/일시 장애 등)를 원본 500으로
            # 새지 않게 표준 에러 포맷(503)으로 변환(2026-09-08 추가 — 실제
            # 키로 테스트하다 모델 단종 시 raw 500이 나가는 것을 발견,
            # 이후 429 쿼터 소진도 실사용 중 재현해 메시지 분기 추가).
            logger.warning("Gemini API 호출 실패: %s", exc)
            raise ServiceUnavailableError(describe_gemini_error(exc)) from exc
        return _parse_or_fallback(response.text)


class GroqProvider(LLMProvider):
    """2026-09-08 신규 — ADR-002에 원래 계획돼 있던 Gemini→Groq 전환.

    사유: Gemini 무료 티어가 모델당 하루 20건으로 실사용(면접 1회에도
    쉽게 소진)에 너무 작다는 것을 실제로 겪음(위 GeminiProvider 이력
    참조). Groq 무료 티어는 실측 기준(2026-09-08, `openai/gpt-oss-120b`)
    분당 1000요청/8000토큰 수준으로 훨씬 넉넉함을 실제 응답 헤더로 확인
    후 채택. `LLMProvider` 인터페이스를 그대로 구현해 교체 — 다른 코드는
    한 줄도 안 바뀜(어댑터 패턴의 이점, ADR-002 설계 의도대로).
    """

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.groq_api_key:
                raise ServiceUnavailableError(
                    "AI 면접관이 아직 준비되지 않았습니다(GROQ_API_KEY 미설정). "
                    "https://console.groq.com 에서 무료 키를 발급받아 .env에 넣으세요."
                )
            from groq import AsyncGroq

            self._client = AsyncGroq(api_key=settings.groq_api_key)
        return self._client

    async def generate_next_turn(self, context: ConversationContext) -> LLMTurnResult:
        import groq

        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_message(context)},
                ],
                response_format={"type": "json_object"},
            )
        except groq.APIStatusError as exc:
            logger.warning("Groq API 호출 실패: %s", exc)
            raise ServiceUnavailableError(describe_groq_error(exc)) from exc
        return _parse_or_fallback(response.choices[0].message.content)


def _parse_or_fallback(raw_text: str | None) -> LLMTurnResult:
    """AC-4: 스키마 불일치 시 서버가 죽지 않고 안전한 폴백으로 진행."""
    try:
        data = json.loads(raw_text or "")
        return LLMTurnResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("LLM 응답 스키마 불일치, 폴백 사용: %s", exc)
        return LLMTurnResult(reply_text=FALLBACK_REPLY, action="ask_question", evaluation=None)

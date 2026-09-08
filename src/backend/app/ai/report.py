"""docs/trd/aimock_u4_trd.md §2/§3. U3-a의 LLM 어댑터 패턴을 재사용."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

from app.ai.gemini_errors import describe_gemini_error
from app.ai.groq_errors import describe_groq_error
from app.config import settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger("aimock.report")

FALLBACK_SUMMARY = "평가 생성에 실패했습니다 — 채용 담당자의 수동 검토가 필요합니다."

REPORT_SYSTEM_PROMPT = (
    "당신은 채용 평가관입니다. 아래 면접 대화와 코드 제출 이력을 바탕으로 "
    "STAR 기법(Situation/Task/Action/Result) 관점의 답변 구조 분석, 기술/"
    "커뮤니케이션/조직적합성 점수(1~5), 합격 추천 여부를 JSON으로만 "
    "응답하십시오. 인구통계적 특징은 절대 평가에 반영하지 마십시오."
)


@dataclass
class ReportContext:
    job_role: str
    transcript_lines: list[str] = field(default_factory=list)
    code_submissions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


class ReportResult(BaseModel):
    technical_score: int
    communication_score: int
    cultural_fit_score: int
    summary_text: str
    star_analysis: str
    pass_recommendation: bool


class ReportGenerator(ABC):
    @abstractmethod
    async def generate(self, context: ReportContext) -> ReportResult: ...


def _build_report_prompt(context: ReportContext) -> str:
    """Gemini/Groq 공용 프롬프트 본문."""
    transcript_text = "\n".join(context.transcript_lines)
    code_text = "\n---\n".join(context.code_submissions) or "(코드 제출 없음)"
    return (
        f"직무: {context.job_role}\n\n[대화 전문]\n{transcript_text}\n\n"
        f"[제출 코드]\n{code_text}\n\n[추출된 키워드]\n{', '.join(context.keywords)}\n\n"
        '다음 JSON 스키마로만 응답하세요: {"technical_score": 1-5, '
        '"communication_score": 1-5, "cultural_fit_score": 1-5, '
        '"summary_text": "종합 요약", "star_analysis": "STAR 구조 분석", '
        '"pass_recommendation": true/false}'
    )


class GeminiReportGenerator(ReportGenerator):
    """모델명은 `-latest` 별칭 사용(2026-09-08, `app/ai/llm.py`
    GeminiProvider와 동일 판단 근거 — 모델 단종/일시과부하/일일쿼터고갈
    이력 3종 참조)."""

    def __init__(self, model: str = "gemini-flash-lite-latest"):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.gemini_api_key:
                raise ServiceUnavailableError(
                    "리포트 생성 AI가 아직 준비되지 않았습니다(GEMINI_API_KEY 미설정)."
                )
            import google.genai as genai

            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    async def generate(self, context: ReportContext) -> ReportResult:
        from google.genai import errors, types

        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=_build_report_prompt(context),
                config=types.GenerateContentConfig(
                    system_instruction=REPORT_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                ),
            )
        except errors.APIError as exc:
            logger.warning("Gemini 리포트 생성 API 호출 실패: %s", exc)
            raise ServiceUnavailableError(describe_gemini_error(exc)) from exc
        return _parse_or_fallback(response.text)


class GroqReportGenerator(ReportGenerator):
    """2026-09-08 신규 — `GroqProvider`(app/ai/llm.py)와 동일 판단 근거로
    Gemini에서 전환."""

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.groq_api_key:
                raise ServiceUnavailableError(
                    "리포트 생성 AI가 아직 준비되지 않았습니다(GROQ_API_KEY 미설정)."
                )
            from groq import AsyncGroq

            self._client = AsyncGroq(api_key=settings.groq_api_key)
        return self._client

    async def generate(self, context: ReportContext) -> ReportResult:
        import groq

        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_report_prompt(context)},
                ],
                response_format={"type": "json_object"},
            )
        except groq.APIStatusError as exc:
            logger.warning("Groq 리포트 생성 API 호출 실패: %s", exc)
            raise ServiceUnavailableError(describe_groq_error(exc)) from exc
        return _parse_or_fallback(response.choices[0].message.content)


def _parse_or_fallback(raw_text: str | None) -> ReportResult:
    try:
        data = json.loads(raw_text or "")
        return ReportResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("리포트 LLM 응답 스키마 불일치, 폴백 사용: %s", exc)
        return ReportResult(
            technical_score=3,
            communication_score=3,
            cultural_fit_score=3,
            summary_text=FALLBACK_SUMMARY,
            star_analysis="",
            pass_recommendation=False,
        )

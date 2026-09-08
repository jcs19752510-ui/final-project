"""Groq API 에러를 사용자 메시지로 변환하는 공통 로직.

`app/ai/gemini_errors.py`와 동일한 취지(2026-09-08) — 429(레이트리밋)와
그 외 일시 장애를 구분해서 안내한다. Groq는 무료 티어 한도가 모델별로
분당/일당 단위라 Gemini의 "하루 20건" 같은 초저용량 문제는 훨씬 덜하지만,
동일한 패턴을 유지해 나중에 소진되더라도 사용자가 오해하지 않게 한다.
"""

import groq

QUOTA_EXCEEDED_MESSAGE = (
    "AI 서비스의 무료 사용량 한도(분당/일당 요청 수 제한)를 초과했습니다. "
    "잠시 후 다시 시도해 주세요."
)
GENERIC_UNAVAILABLE_MESSAGE = "AI 호출에 실패했습니다. 잠시 후 다시 시도해 주세요."


def describe_groq_error(exc: "groq.APIStatusError") -> str:
    if getattr(exc, "status_code", None) == 429:
        return QUOTA_EXCEEDED_MESSAGE
    return GENERIC_UNAVAILABLE_MESSAGE

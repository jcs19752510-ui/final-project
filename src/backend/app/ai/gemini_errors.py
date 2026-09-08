"""Gemini API 에러를 사용자 메시지로 변환하는 공통 로직.

2026-09-08: 실제 사용 중 429(RESOURCE_EXHAUSTED, 무료 티어 하루 20건
한도 소진)를 겪었는데, 기존엔 일시 장애(503)와 같은 문구("잠시 후 다시
시도")로 안내해서 사용자가 "몇 초 후 재시도하면 될 것"으로 오해하기
쉬웠다(실제로는 하루 단위 쿼터라 재시도해도 그날 안에는 안 풀림).
`app/ai/llm.py`/`app/ai/report.py`에서 공통으로 사용.
"""

from google.genai import errors

QUOTA_EXCEEDED_MESSAGE = (
    "AI 서비스의 무료 사용량 한도를 초과했습니다(모델당 하루 요청 수 제한). "
    "잠시 후가 아니라 시간이 좀 지나야(보통 자정 기준 리셋) 다시 가능합니다."
)
GENERIC_UNAVAILABLE_MESSAGE = "AI 호출에 실패했습니다. 잠시 후 다시 시도해 주세요."


def describe_gemini_error(exc: "errors.APIError") -> str:
    if getattr(exc, "code", None) == 429:
        return QUOTA_EXCEEDED_MESSAGE
    return GENERIC_UNAVAILABLE_MESSAGE

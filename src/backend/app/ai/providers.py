"""프로세스 전역 싱글턴. 테스트에서는 FastAPI `dependency_overrides`로 교체."""

from app.ai.llm import GeminiProvider, LLMProvider
from app.ai.stt import FasterWhisperProvider, STTProvider
from app.config import settings

_llm_provider: LLMProvider = GeminiProvider()
_stt_provider: STTProvider = FasterWhisperProvider(settings.stt_model_size)


def get_llm_provider() -> LLMProvider:
    return _llm_provider


def get_stt_provider() -> STTProvider:
    return _stt_provider

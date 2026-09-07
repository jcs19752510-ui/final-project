"""프로세스 전역 싱글턴. 테스트에서는 FastAPI `dependency_overrides`로 교체."""

from app.ai.emotion import DeepFaceEmotionAnalyzer, EmotionAnalyzer
from app.ai.llm import GeminiProvider, LLMProvider
from app.ai.prosody import LibrosaProsodyAnalyzer, ProsodyAnalyzer
from app.ai.report import GeminiReportGenerator, ReportGenerator
from app.ai.stt import FasterWhisperProvider, STTProvider
from app.config import settings

_llm_provider: LLMProvider = GeminiProvider()
_stt_provider: STTProvider = FasterWhisperProvider(settings.stt_model_size)
_report_generator: ReportGenerator = GeminiReportGenerator()
_emotion_analyzer: EmotionAnalyzer = DeepFaceEmotionAnalyzer()
_prosody_analyzer: ProsodyAnalyzer = LibrosaProsodyAnalyzer()


def get_llm_provider() -> LLMProvider:
    return _llm_provider


def get_stt_provider() -> STTProvider:
    return _stt_provider


def get_report_generator() -> ReportGenerator:
    return _report_generator


def get_emotion_analyzer() -> EmotionAnalyzer:
    return _emotion_analyzer


def get_prosody_analyzer() -> ProsodyAnalyzer:
    return _prosody_analyzer

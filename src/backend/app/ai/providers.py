"""프로세스 전역 싱글턴. 테스트에서는 FastAPI `dependency_overrides`로 교체."""

from app.ai.emotion import DeepFaceEmotionAnalyzer, EmotionAnalyzer
from app.ai.llm import GroqProvider, LLMProvider
from app.ai.prosody import LibrosaProsodyAnalyzer, ProsodyAnalyzer
from app.ai.report import GroqReportGenerator, ReportGenerator
from app.ai.stt import FasterWhisperProvider, STTProvider
from app.config import settings

# 2026-09-08: Gemini → Groq 전환(ADR-002에 원래 계획돼 있던 방향).
# Gemini 무료 티어(모델당 하루 20건)를 실사용 중 소진해 면접이 막히는 걸
# 실제로 겪음 — Groq 무료 티어가 훨씬 넉넉함을 실측 확인 후 교체.
# Gemini 구현(GeminiProvider/GeminiReportGenerator)은 삭제하지 않고
# app/ai/llm.py, app/ai/report.py에 그대로 남겨둠 — 필요 시 여기 두 줄만
# 되돌리면 재전환 가능(어댑터 패턴의 이점).
_llm_provider: LLMProvider = GroqProvider()
_stt_provider: STTProvider = FasterWhisperProvider(settings.stt_model_size)
_report_generator: ReportGenerator = GroqReportGenerator()
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

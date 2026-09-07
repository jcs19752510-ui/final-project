"""테스트 전용 Fake Provider — docs/trd/aimock_u3a_trd.md AC-1 (어댑터 패턴 검증)."""

from app.ai.emotion import EmotionAnalyzer, EmotionResult
from app.ai.llm import ConversationContext, LLMProvider, LLMTurnResult
from app.ai.prosody import ProsodyAnalyzer, ProsodyResult
from app.ai.report import ReportContext, ReportGenerator, ReportResult
from app.ai.stt import STTProvider


class FakeSTTProvider(STTProvider):
    """오디오 바이트를 그대로 UTF-8 텍스트로 취급 — 테스트에서 전사 결과를 직접 제어."""

    async def transcribe(self, audio_bytes: bytes) -> str:
        return audio_bytes.decode("utf-8")


class FakeLLMProvider(LLMProvider):
    def __init__(self, action: str = "ask_question", reply_text: str = "다음 질문입니다."):
        self.action = action
        self.reply_text = reply_text
        self.call_count = 0

    async def generate_next_turn(self, context: ConversationContext) -> LLMTurnResult:
        self.call_count += 1
        return LLMTurnResult(reply_text=self.reply_text, action=self.action, evaluation=None)


class FakeReportGenerator(ReportGenerator):
    def __init__(self):
        self.call_count = 0

    async def generate(self, context: ReportContext) -> ReportResult:
        self.call_count += 1
        return ReportResult(
            technical_score=4,
            communication_score=4,
            cultural_fit_score=3,
            summary_text="전반적으로 양호한 답변입니다.",
            star_analysis="STAR 구조를 대체로 따랐습니다.",
            pass_recommendation=True,
        )


class FakeEmotionAnalyzer(EmotionAnalyzer):
    """docs/trd/aimock_u3b_trd.md — 실제 DeepFace 모델 다운로드 없이 고정값 반환."""

    def __init__(self, fixed_result: EmotionResult | None = None):
        self.fixed_result = fixed_result or EmotionResult("neutral", 0.9)
        self.call_count = 0

    async def analyze_frame(self, image_bytes: bytes) -> EmotionResult:
        self.call_count += 1
        return self.fixed_result


class FakeProsodyAnalyzer(ProsodyAnalyzer):
    """docs/trd/aimock_u3b_trd.md — 실제 librosa 연산 없이 고정값 반환."""

    def __init__(self, fixed_result: ProsodyResult | None = None):
        self.fixed_result = fixed_result or ProsodyResult(180.0, 0.03)
        self.call_count = 0

    async def analyze(self, audio_bytes: bytes) -> ProsodyResult:
        self.call_count += 1
        return self.fixed_result

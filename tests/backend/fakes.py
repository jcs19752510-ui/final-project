"""테스트 전용 Fake Provider — docs/trd/aimock_u3a_trd.md AC-1 (어댑터 패턴 검증)."""

from app.ai.llm import ConversationContext, LLMProvider, LLMTurnResult
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

"""ADR-002: STT는 원래 faster-whisper 로컬 실행이었으나, ADR-008(2026-09-08)로
GroqWhisperProvider(호스팅 API)로 전환. docs/trd/aimock_u3a_trd.md §2."""

import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from app.ai.groq_errors import describe_groq_error
from app.config import settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger("aimock.stt")


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str: ...


class GroqWhisperProvider(STTProvider):
    """ADR-008(2026-09-08) 신규 — 현재 실사용 구현.

    사유: Render 배포 후 실측 결과 턴 제출 응답이 10초 이상 걸리는 것을
    발견(N-001 목표 8초 초과). 원인은 로컬 `faster-whisper` 추론이 Render
    저사양 인스턴스(0.5 vCPU)에서 CPU 바운드로 느린 것 — 로컬 개발 PC에서는
    안 보이던 문제. STT 연산 자체를 Groq 호스팅 API로 위임하면 Render
    인스턴스 사양과 무관하게 빨라진다(2026-09-08 실측: 동일 샘플 오디오
    기준 로컬 대비 압도적으로 빠른 응답, 내부테스트결과서 참조).
    `LLMProvider`와 동일한 GROQ_API_KEY를 재사용하므로 추가 키 발급 불필요.
    """

    def __init__(self, model: str = "whisper-large-v3-turbo"):
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.groq_api_key:
                raise ServiceUnavailableError(
                    "STT 서비스가 아직 준비되지 않았습니다(GROQ_API_KEY 미설정). "
                    "https://console.groq.com 에서 무료 키를 발급받아 .env에 넣으세요."
                )
            from groq import AsyncGroq

            self._client = AsyncGroq(api_key=settings.groq_api_key)
        return self._client

    async def transcribe(self, audio_bytes: bytes) -> str:
        import groq

        client = self._get_client()
        try:
            response = await client.audio.transcriptions.create(
                model=self._model,
                file=("audio.webm", audio_bytes),
                language="ko",
            )
        except groq.APIStatusError as exc:
            logger.warning("Groq STT 호출 실패: %s", exc)
            raise ServiceUnavailableError(describe_groq_error(exc)) from exc
        return response.text.strip()


class FasterWhisperProvider(STTProvider):
    """ADR-002 원안 구현. ADR-008로 기본 사용 provider에서는 빠졌지만,
    되돌릴 수 있도록(어댑터 패턴) 코드는 그대로 남겨둔다 —
    `app/ai/providers.py`의 한 줄만 바꾸면 재전환 가능.
    모델은 최초 호출 시 1회만 로드(지연 초기화, ~5초)."""

    def __init__(self, model_size: str = "tiny"):
        self._model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        return self._model

    async def transcribe(self, audio_bytes: bytes) -> str:
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes)

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        model = self._get_model()
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            path = Path(f.name)
        try:
            segments, _info = model.transcribe(str(path), language="ko")
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            path.unlink(missing_ok=True)

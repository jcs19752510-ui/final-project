"""ADR-002: STT는 faster-whisper 로컬 실행. docs/trd/aimock_u3a_trd.md §2."""

import asyncio
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str: ...


class FasterWhisperProvider(STTProvider):
    """실제 구현. 모델은 최초 호출 시 1회만 로드(지연 초기화, ~5초)."""

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

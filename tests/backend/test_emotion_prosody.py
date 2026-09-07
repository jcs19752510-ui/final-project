"""docs/trd/aimock_u3b_trd.md §5/§6.

AC-1/AC-2(실제 사용자 제공 얼굴 영상/음성 샘플로 검증)는 개인 생체정보라
저장소에 커밋하지 않고 로컬 1회성 스크립트로 수동 검증했다(내부테스트
결과서 참조). 여기서는 합성 데이터로 실제 라이브러리의 예외 안전성
(AC-3)을 자동화한다 — 실제 DeepFace/librosa를 그대로 실행(mock 없음).
"""

import numpy as np

from app.ai.emotion import DeepFaceEmotionAnalyzer, UNKNOWN_EMOTION
from app.ai.prosody import LibrosaProsodyAnalyzer


def _blank_jpeg_bytes() -> bytes:
    import cv2

    # 얼굴이 없는 단색 이미지 — DeepFace가 얼굴을 못 찾는 경로를 재현
    img = np.full((200, 200, 3), 127, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def _silent_wav_bytes() -> bytes:
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000)  # 1초 무음
    return buf.getvalue()


async def test_ac3_no_face_detected_returns_unknown_not_exception():
    analyzer = DeepFaceEmotionAnalyzer()
    result = await analyzer.analyze_frame(_blank_jpeg_bytes())
    assert result.dominant_emotion == UNKNOWN_EMOTION
    assert result.confidence == 0.0


async def test_prosody_silence_returns_safe_values_not_exception():
    analyzer = LibrosaProsodyAnalyzer()
    result = await analyzer.analyze(_silent_wav_bytes())
    # 무음이므로 유효 피치가 없어 0.0으로 폴백되는 것이 정상(예외 없이 끝나는 것이 핵심)
    assert result.pitch_mean_hz == 0.0
    assert result.energy_mean >= 0.0

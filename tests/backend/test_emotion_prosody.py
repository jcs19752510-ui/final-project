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


def _toned_wav_bytes(seconds: float = 5.0, sr: int = 22050, freq_hz: float = 180.0) -> bytes:
    """무음이 아니라 실제 음성과 비슷하게 pyin이 "유성음"으로 판단할 만한
    사인파 톤 — 2026-09-08 리포트 생성 속도 회귀 테스트(아래)용. 무음
    샘플만으로는 pyin의 실제 연산 비용(유성 구간 탐색)을 재현하지 못한다."""
    import io
    import wave

    import numpy as np

    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    tone = (np.sin(2 * np.pi * freq_hz * t) * 0.5 * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(tone.tobytes())
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


async def test_prosody_analysis_completes_quickly_and_finds_reasonable_pitch():
    """2026-09-08 회귀 방지 테스트 — 운영 환경에서 리포트 생성이 1분 이상
    걸리던 문제의 실측 원인이 `librosa.pyin()`(확률적 Viterbi 디코딩이라
    원래 무거움)이었다(내부테스트결과서 참조: 8.75초 오디오 기준 3.16초).
    다운샘플(8kHz) + 탐색범위 축소(C2~C6)로 0.69초까지 줄였는데, 이 최적화가
    나중에 실수로 되돌아가면(예: 다시 원본 샘플레이트 그대로 분석) 이
    테스트가 실패해서 알아챌 수 있어야 한다. 5초 톤 기준 여유 있게 3초
    한도(로컬/CI 성능 편차 감안 — 최적화 전이었다면 최소 그 이상 걸림)."""
    import time

    analyzer = LibrosaProsodyAnalyzer()
    audio = _toned_wav_bytes(seconds=5.0, freq_hz=180.0)

    started = time.monotonic()
    result = await analyzer.analyze(audio)
    elapsed = time.monotonic() - started

    assert elapsed < 3.0, f"프로소디 분석이 너무 느림({elapsed:.2f}초) — pyin 최적화가 되돌아갔을 수 있음"
    # 180Hz 톤을 넣었으니 피치 탐지 결과도 그 근처여야 함(완전히 엉뚱한 값이면
    # 다운샘플/탐색범위 축소가 정확도를 망가뜨린 회귀).
    assert 150.0 < result.pitch_mean_hz < 210.0

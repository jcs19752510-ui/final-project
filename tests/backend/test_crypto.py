"""2026-09-09 보안 강화 — F-4(저장 암호화 AES-128→AES-256)
`app/core/crypto.py`(AES-256-GCM) 단위 테스트. 실제 pyca/cryptography
AESGCM을 그대로 실행한다(mock 없음)."""

import base64
import secrets

import pytest


async def test_encrypt_decrypt_round_trip_returns_original_bytes():
    from app.core.crypto import decrypt_bytes, encrypt_bytes

    original = b"this is a fake audio/video payload \x00\x01\x02"
    encrypted = encrypt_bytes(original)
    assert encrypted != original  # 실제로 암호화됐는지(평문 그대로 아님)
    assert decrypt_bytes(encrypted) == original


async def test_encrypt_produces_different_ciphertext_each_call():
    """같은 평문이라도 매번 다른 nonce를 쓰므로 암호문이 달라야 한다 —
    nonce가 고정돼 있거나 재사용되면 AES-GCM의 안전성이 깨진다."""
    from app.core.crypto import encrypt_bytes

    original = b"same plaintext"
    encrypted_1 = encrypt_bytes(original)
    encrypted_2 = encrypt_bytes(original)
    assert encrypted_1 != encrypted_2


async def test_tampered_ciphertext_fails_to_decrypt():
    """무결성 검증(GCM 인증 태그) — 암호문이 1바이트라도 변조되면 복호화가
    반드시 실패해야 한다. 원본 미디어 데이터라 "적당히 넘어가는" 폴백은
    없어야 하며, 예외가 그대로 전파되는 게 맞는 설계다."""
    from cryptography.exceptions import InvalidTag

    from app.core.crypto import encrypt_bytes, decrypt_bytes

    encrypted = bytearray(encrypt_bytes(b"sensitive interview audio"))
    encrypted[-1] ^= 0xFF  # 마지막 바이트(태그의 일부) 변조
    with pytest.raises(InvalidTag):
        decrypt_bytes(bytes(encrypted))


async def test_decrypt_with_wrong_key_fails(monkeypatch):
    from cryptography.exceptions import InvalidTag

    from app.config import settings
    from app.core.crypto import decrypt_bytes, encrypt_bytes

    encrypted = encrypt_bytes(b"secret payload")

    other_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    monkeypatch.setattr(settings, "media_encryption_key", other_key)
    with pytest.raises(InvalidTag):
        decrypt_bytes(encrypted)


async def test_decrypt_truncated_payload_raises_value_error():
    from app.core.crypto import decrypt_bytes

    with pytest.raises(ValueError):
        decrypt_bytes(b"short")  # nonce 크기(12바이트)보다 짧음


async def test_missing_key_raises_clear_runtime_error(monkeypatch):
    from app.config import settings
    from app.core.crypto import encrypt_bytes

    monkeypatch.setattr(settings, "media_encryption_key", None)
    with pytest.raises(RuntimeError, match="MEDIA_ENCRYPTION_KEY가 설정되지"):
        encrypt_bytes(b"x")


async def test_wrong_length_key_raises_clear_runtime_error(monkeypatch):
    """32바이트가 아닌 값(예: 예전 방식으로 짧게 만든 키)을 넣으면 애매하게
    실패하지 않고, 왜 안 되는지 알 수 있는 메시지로 즉시 실패해야 한다."""
    from app.config import settings
    from app.core.crypto import encrypt_bytes

    short_key = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode()  # AES-128 크기
    monkeypatch.setattr(settings, "media_encryption_key", short_key)
    with pytest.raises(RuntimeError, match="정확히 32바이트"):
        encrypt_bytes(b"x")

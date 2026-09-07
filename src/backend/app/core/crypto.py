from cryptography.fernet import Fernet

from app.config import settings


def _fernet() -> Fernet:
    if not settings.media_encryption_key:
        raise RuntimeError(
            "MEDIA_ENCRYPTION_KEY가 설정되지 않았습니다. "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "로 생성 후 .env에 넣으세요 (docs/adr/adr-004-media-capture-scope.md 참조)."
        )
    return Fernet(settings.media_encryption_key.encode())


def encrypt_bytes(raw: bytes) -> bytes:
    return _fernet().encrypt(raw)


def decrypt_bytes(token: bytes) -> bytes:
    return _fernet().decrypt(token)

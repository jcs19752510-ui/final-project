import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

# 2026-09-09(보안 강화, F-4 — 99.모의면접_전수검사/전수검사결과_20260909101218.md,
# docs/adr/adr-004-media-capture-scope.md "암호화 알고리즘 변경" 참조):
# 기존 Fernet(AES-128-CBC+HMAC-SHA256)에서 AES-256-GCM으로 전환. 실질적인
# 보안 강도 차이(128비트도 브루트포스 불가능)보다는, 사양(AES-256)을
# 맞추고 GCM(단일 프리미티브로 기밀성+무결성을 함께 제공하는 표준 AEAD
# 방식)으로 옮기는 게 더 현대적인 선택이라는 판단. 기존 저장 데이터는
# 전부 테스트 데이터라 사용자 승인 하에 삭제하고 무중단 전환(구버전
# Fernet 페이로드에 대한 하위 호환 디코딩은 넣지 않음 — 남아있는 데이터가
# 없으므로 그 복잡도를 감수할 이유가 없음).
_NONCE_SIZE_BYTES = 12  # AES-GCM 표준 권장 nonce 크기(96비트)
_KEY_SIZE_BYTES = 32  # AES-256


def _aesgcm() -> AESGCM:
    if not settings.media_encryption_key:
        raise RuntimeError(
            "MEDIA_ENCRYPTION_KEY가 설정되지 않았습니다. "
            "python -c \"import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())\" "
            "로 생성 후 .env에 넣으세요 (docs/adr/adr-004-media-capture-scope.md 참조)."
        )
    try:
        key = base64.urlsafe_b64decode(settings.media_encryption_key.encode())
    except Exception as exc:
        raise RuntimeError(
            "MEDIA_ENCRYPTION_KEY가 올바른 base64 형식이 아닙니다. "
            "python -c \"import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())\" "
            "로 새로 생성하세요."
        ) from exc
    if len(key) != _KEY_SIZE_BYTES:
        raise RuntimeError(
            f"MEDIA_ENCRYPTION_KEY는 디코딩했을 때 정확히 {_KEY_SIZE_BYTES}바이트(AES-256)여야 "
            f"하는데 {len(key)}바이트입니다. "
            "python -c \"import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())\" "
            "로 새로 생성하세요(기존 Fernet 키를 재사용하지 마세요)."
        )
    return AESGCM(key)


def encrypt_bytes(raw: bytes) -> bytes:
    """매 호출마다 새 랜덤 nonce를 생성해 암호문 앞에 붙여 반환한다 —
    AES-GCM은 같은 키로 nonce를 재사용하면 기밀성/무결성이 깨지므로,
    저장 시 nonce를 별도 컬럼이 아니라 페이로드에 포함시켜(Fernet과
    동일한 관례) 호출부(media_service)가 신경 쓸 필요 없게 한다."""
    nonce = os.urandom(_NONCE_SIZE_BYTES)
    ciphertext = _aesgcm().encrypt(nonce, raw, None)
    return nonce + ciphertext


def decrypt_bytes(token: bytes) -> bytes:
    """`token`이 `_NONCE_SIZE_BYTES`보다 짧으면(손상된 파일 등) 명확한
    에러로 실패하고, 태그 검증에 실패하면(변조/잘못된 키) `InvalidTag`를
    그대로 전파한다 — 호출부가 무결성 실패를 조용히 삼키면 안 되므로
    폴백하지 않는다(원본 오디오/영상이라는 데이터 특성상, 위변조된
    데이터를 정상인 것처럼 반환하는 것이 훨씬 더 위험함)."""
    if len(token) < _NONCE_SIZE_BYTES:
        raise ValueError("손상된 암호화 데이터입니다(길이가 nonce 크기보다 짧음).")
    nonce, ciphertext = token[:_NONCE_SIZE_BYTES], token[_NONCE_SIZE_BYTES:]
    return _aesgcm().decrypt(nonce, ciphertext, None)

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aimock"
    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    # 실제 값은 .env(MEDIA_ENCRYPTION_KEY)로 주입 — 여기 하드코딩하지 않음.
    # 로컬 최초 셋업: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    media_encryption_key: str | None = None
    media_storage_dir: str = "uploads"
    account_deletion_grace_days: int = 30
    gemini_api_key: str | None = None  # ADR-002 — https://aistudio.google.com 무료 키
    groq_api_key: str | None = None  # ADR-002 — https://console.groq.com 무료 키(2026-09-08, Gemini 무료 티어 일일 한도 소진 대응으로 전환)
    stt_model_size: str = "tiny"
    turn_max_answer_chars: int = 800  # aimock_u2a_trd.md §3 (F-003 대체)


settings = Settings()

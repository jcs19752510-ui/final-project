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


settings = Settings()

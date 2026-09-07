class AppError(Exception):
    """docs/tech_conventions.md 에러 응답 포맷({error:{code,message}})에 매핑되는 베이스 예외."""

    status_code: int = 400
    code: str = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DuplicateEmailError(AppError):
    status_code = 409
    code = "DUPLICATE_EMAIL"


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"


class NotAuthenticatedError(AppError):
    status_code = 401
    code = "NOT_AUTHENTICATED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class ServiceUnavailableError(AppError):
    """외부 AI 서비스(LLM/STT 등)가 설정 미비 등으로 쓸 수 없을 때."""

    status_code = 503
    code = "SERVICE_UNAVAILABLE"


class RateLimitedError(AppError):
    """로그인 브루트포스 완화(app/core/rate_limit.py) — 반복 실패 시 잠금."""

    status_code = 429
    code = "RATE_LIMITED"

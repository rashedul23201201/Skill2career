import logging
import sys
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SKILL2CAREER"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database Configuration (MySQL)
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/skill2career"

    # JWT & Authentication
    JWT_SECRET_KEY: str = "change_this_in_production_super_secret_key_minimum_32_characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_REMEMBER_DAYS: int = 30
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # CORS & Frontend Origins
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Payment Gateways (SKL-20)
    SSLCOMMERZ_STORE_ID: str = "skill2career_sandbox"
    SSLCOMMERZ_STORE_PASSWORD: str = "skill2career_sandbox@ssl"
    SSLCOMMERZ_IS_SANDBOX: bool = True
    SSLCOMMERZ_SESSION_API: str = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
    SSLCOMMERZ_VALIDATION_API: str = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"

    STRIPE_SECRET_KEY: str = "sk_test_mock_stripe_secret_key_skill2career"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_mock_stripe_publishable_key_skill2career"
    STRIPE_WEBHOOK_SECRET: str = "whsec_mock_stripe_webhook_secret_skill2career"
    GLOBAL_GATEWAY_PROVIDER: str = "STRIPE"
    PAYMENT_BACKEND_BASE_URL: str = "http://localhost:8000/api/v1"

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated allowed origins into a cleaned list."""
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL.strip())
        return origins

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()


def setup_logging() -> None:
    """Set up structured application logging without leaking sensitive information."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Silence verbose 3rd-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if not settings.DEBUG else logging.INFO)

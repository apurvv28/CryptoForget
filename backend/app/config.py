"""
Application configuration loaded from environment variables.

Uses Pydantic Settings for type-safe configuration with .env support.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings — loaded from environment / .env file."""

    # Database (SQLite with async aiosqlite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/cryptoforget.db"
    DATABASE_ECHO: bool = False

    # AWS S3 (Artifact storage & Queueing)
    AWS_PROFILE: str = "cryptoforget"
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = "cryptoforget-artifacts-313696198691"
    S3_ENDPOINT_URL: str | None = None  # Optional custom endpoint

    # Auth
    SECRET_KEY: str = "change-this-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # ML
    MODEL_PATH: str = "./models/distilgpt2"
    MODEL_REVISION: str = "main"
    MAX_SEQ_LENGTH: int = 128
    PYTORCH_NUM_THREADS: int = 3
    PYTORCH_INTEROP_THREADS: int = 1

    # Resource Guardrails
    MAX_RSS_GB: float = 6.0
    MIN_AVAILABLE_GB: float = 1.5
    MAX_WALL_TIME_MINUTES: int = 60

    # Certificate Signing
    SIGNING_KEY_PATH: str = "./signing_keys/private.pem"
    PUBLIC_KEY_PATH: str = "./signing_keys/public.pem"
    SIGNING_KEY_ID: str = "key-001"

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

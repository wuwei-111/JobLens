"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    """Runtime settings.

    Every field can be overridden with a ``JOBLENS_`` prefixed environment
    variable, or via ``backend/.env``. ``JOBLENS_CORS_ORIGINS`` must be a JSON
    array, e.g. ``["http://localhost:5173"]``.
    """

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="JOBLENS_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "JobLens API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = f"sqlite:///{(DATA_DIR / 'joblens.db').as_posix()}"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    max_upload_bytes: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

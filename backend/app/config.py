"""Application configuration, loaded from environment variables / .env.

Kept as a single settings object (rather than scattered os.environ calls) so
tests can override values (e.g. DATABASE_URL, GEMINI_API_KEY) by constructing
a Settings() with kwargs or monkeypatching env vars before import.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg2://swim:swim@localhost:5432/swim_search"

    # Gemini / multimodal LLM
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    llm_max_retries: int = 4
    llm_retry_min_wait_sec: float = 2.0
    llm_retry_max_wait_sec: float = 16.0

    # Video download / storage
    download_dir: Path = Path("./downloads")
    # Videos longer than this are rejected outright (processing time + LLM cost
    # grow roughly linearly with duration). The frontend also warns the user
    # before submission so this should rarely be hit in practice.
    max_video_duration_sec: int = 3600

    # Frame extraction (used by the Phase 2 embedding pipeline interface).
    frame_sample_fps: float = 1.0

    # Search
    default_search_top_k: int = 5

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Polling
    status_poll_interval_ms: int = 2000


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.download_dir.mkdir(parents=True, exist_ok=True)
    return settings

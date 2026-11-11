"""Application settings, loaded from environment variables and `backend/.env`.

All configuration lives here so nothing (especially the Groq API key or model name)
is hard-coded anywhere else in the code base.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The backend folder (one level above `app/`). Relative paths such as INDEX_DIR and
# KB_DIR are resolved against it, so the app works no matter where it is started from.
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Placeholder value shipped in .env.example. Treated the same as "no key".
PLACEHOLDER_API_KEY = "your_groq_api_key_here"


class Settings(BaseSettings):
    """Typed settings. Field names match the variable names in `.env.example`."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Required ---
    GROQ_API_KEY: str = ""

    # --- LLM ---
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.2
    GROQ_MAX_TOKENS: int = 2048
    GROQ_TIMEOUT_SECONDS: float = 30
    GROQ_MAX_RETRIES: int = 2
    GROQ_USE_JSON_SCHEMA: bool = False

    # --- RAG ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    INDEX_DIR: str = "data/index"
    KB_DIR: str = "knowledge_base"
    RAG_TOP_K: int = 5
    RAG_MIN_SCORE: float = 0.35
    CHUNK_SIZE_TOKENS: int = 350
    CHUNK_OVERLAP_TOKENS: int = 50

    # --- Upload limits ---
    MAX_UPLOAD_MB: int = 10
    MAX_PDF_PAGES: int = 20
    MAX_REPORT_CHARS: int = 24000
    MIN_EXTRACTED_CHARS: int = 80

    # --- App ---
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 20

    # ---- Derived helpers -------------------------------------------------
    @property
    def cors_origin_list(self) -> list[str]:
        """CORS_ORIGINS is comma-separated in the env file; return it as a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def index_path(self) -> Path:
        return _resolve(self.INDEX_DIR)

    @property
    def kb_path(self) -> Path:
        return _resolve(self.KB_DIR)

    @property
    def has_api_key(self) -> bool:
        key = self.GROQ_API_KEY.strip()
        return bool(key) and key != PLACEHOLDER_API_KEY


def _resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else BACKEND_DIR / path


@lru_cache
def get_settings() -> Settings:
    """Return one shared Settings object (read from the environment once)."""
    return Settings()

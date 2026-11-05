"""CYRUS Configuration Management.

Loads application configuration from environment variables and .env file.
Provides structured, type-safe settings with zero mandatory external dependencies,
while gracefully supporting Pydantic Settings when installed.
"""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def _load_env_file():
    """Parses a simple .env file without external dependencies."""
    if not ENV_FILE.exists():
        return
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


_load_env_file()


@dataclass
class Settings:
    """Central configuration class for CYRUS."""

    # --- Application Settings ---
    CYRUS_ENV: str = os.getenv("CYRUS_ENV", "development")
    CYRUS_DEBUG: bool = os.getenv("CYRUS_DEBUG", "true").lower() in ("true", "1", "yes")
    CYRUS_APP_NAME: str = os.getenv("CYRUS_APP_NAME", "CYRUS (Cybernetic Yet Responsive Unified System)")
    CYRUS_VERSION: str = os.getenv("CYRUS_VERSION", "0.1.0")
    CYRUS_BACKEND_PORT: int = int(os.getenv("CYRUS_BACKEND_PORT", "8000"))
    CYRUS_BACKEND_HOST: str = os.getenv("CYRUS_BACKEND_HOST", "127.0.0.1")
    CYRUS_FRONTEND_PORT: int = int(os.getenv("CYRUS_FRONTEND_PORT", "5173"))

    # --- Security & CORS ---
    CYRUS_SECRET_KEY: str = os.getenv("CYRUS_SECRET_KEY", "cyrus-local-dev-key-m5-saksham-2026")
    CYRUS_CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    CYRUS_SANDBOX_PATH: str = os.getenv("CYRUS_SANDBOX_PATH", str(PROJECT_ROOT))

    # --- Database Settings ---
    CYRUS_DATABASE_PATH: str = os.getenv("CYRUS_DATABASE_PATH", "data/cyrus.db")
    CYRUS_DB_WAL_MODE: bool = os.getenv("CYRUS_DB_WAL_MODE", "true").lower() in ("true", "1", "yes")

    # --- Local AI Runtime (Ollama) ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b-instruct")
    OLLAMA_FALLBACK_MODEL: str = os.getenv("OLLAMA_FALLBACK_MODEL", "qwen2.5:3b-instruct")
    OLLAMA_TIMEOUT_SECONDS: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))

    # --- Mandatory Language Governance ---
    DEFAULT_RESPONSE_LANGUAGE: str = os.getenv("DEFAULT_RESPONSE_LANGUAGE", "English")
    INPUT_LANGUAGE_DETECTION: str = os.getenv("INPUT_LANGUAGE_DETECTION", "Automatic")
    SUPPORTED_INPUT_LANGUAGES: List[str] = field(default_factory=lambda: ["English", "Hindi", "Hinglish"])
    ALLOW_HINDI_RESPONSES: bool = os.getenv("ALLOW_HINDI_RESPONSES", "false").lower() in ("true", "1", "yes")

    # --- Lifecycle & Process Management ---
    ENABLE_AUTO_START: bool = os.getenv("ENABLE_AUTO_START", "false").lower() in ("true", "1", "yes")
    PROCESS_CHECK_INTERVAL_SECONDS: int = int(os.getenv("PROCESS_CHECK_INTERVAL_SECONDS", "5"))
    SHUTDOWN_GRACE_PERIOD_SECONDS: int = int(os.getenv("SHUTDOWN_GRACE_PERIOD_SECONDS", "3"))

    # --- External Monitoring (Phase 9+) ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    @property
    def absolute_db_path(self) -> Path:
        """Returns the absolute path to the SQLite database file."""
        db_path = Path(self.CYRUS_DATABASE_PATH)
        if db_path.is_absolute():
            return db_path
        return PROJECT_ROOT / db_path


settings = Settings()

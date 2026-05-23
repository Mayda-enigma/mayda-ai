"""
Application configuration using pydantic-settings.
Loads from environment variables and .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Service identity ──
    PROJECT_NAME: str = "Recommendation Service"
    VERSION: str = "1.0.0"
    PORT: int = 8101

    # ── External backend API ──
    BACKEND_API_URL: str = "http://host.docker.internal:8000"
    BACKEND_API_TIMEOUT: int = 30

    # ── LLM configuration ──
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.0-flash"
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1000

    # ── Security ──
    SERVICE_TOKEN: str = ""
    GATEWAY_ORIGIN: str = "http://localhost:3000"

    # ── ChromaDB configuration ──
    CHROMA_DB_DIR: str = "chroma_db"
    CHROMA_COLLECTION_NAME: str = "dishes"

    # ── Inventory configuration ──
    INVENTORY_DATABASE_URL: str = "sqlite:///./data/inventory.db"
    INVENTORY_MODEL_PATH: str = "data/models.joblib"

    # ── Voice configuration ──
    WHISPER_MODEL: str = "tiny"

    # ── Logging ──
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

"""
Configuration settings for simplified containerized recommendation service
"""
import os
from typing import Optional

class Settings:
    # Service Configuration
    PROJECT_NAME: str = "Simplified Recommendation Service"
    API_V1_STR: str = "/api/v1"
    
    # External Backend API Configuration (running on host)
    BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://host.docker.internal:8000")
    BACKEND_API_TIMEOUT: int = int(os.getenv("BACKEND_API_TIMEOUT", "30"))
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Service Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Remove database configuration since we're not using a local database
    # We only use the external backend API now

settings = Settings()
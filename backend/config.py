"""
Centralized configuration for the CampusHire.AI backend.
Uses pydantic BaseSettings to load values from environment variables and .env file.
"""

import os
import tempfile
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- API Keys ---
    GEMINI_API_KEY: str = ""

    # --- Gemini Model ---
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["*"]

    # --- File Upload ---
    MAX_UPLOAD_SIZE_MB: int = 10  # Maximum file size in MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    UPLOAD_DIR: str = os.path.join(tempfile.gettempdir(), "campushire_uploads")

    # --- Server ---
    APP_TITLE: str = "CampusHire.AI API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-powered campus hiring platform — resume parsing, ATS scoring, "
        "interview question generation, feedback, and voice services."
    )
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()

# Validate required settings on import
def validate_settings():
    """Validate that required settings are configured."""
    errors = []
    
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append(
            "GEMINI_API_KEY is not set. Please set it in your .env file.\n"
            "Get your API key from: https://makersuite.google.com/app/apikey"
        )
    
    if errors:
        error_msg = "\n".join(f"❌ {error}" for error in errors)
        raise ValueError(
            f"\n{'='*60}\n"
            f"Configuration Error:\n"
            f"{error_msg}\n"
            f"{'='*60}\n"
            f"Please create a .env file in the project root with:\n"
            f"GEMINI_API_KEY=your_actual_api_key_here\n"
            f"DEBUG=True\n"
        )
    
    return True

# Validate on import (can be disabled for testing)
try:
    validate_settings()
except ValueError as e:
    # Only raise in non-debug mode or if explicitly required
    if not settings.DEBUG:
        import warnings
        warnings.warn(str(e), UserWarning)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

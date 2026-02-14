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

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

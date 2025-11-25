# backend/config.py
"""
Configuration module for Langchain + OpenAI integration
Allows flexible model switching without code changes
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-mini")
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2048
    
    # Langchain Configuration (Optional - for monitoring)
    langchain_tracing_v2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    langchain_endpoint: Optional[str] = os.getenv("LANGCHAIN_ENDPOINT", None)
    langchain_api_key: Optional[str] = os.getenv("LANGCHAIN_API_KEY", None)
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "legal-doc-assistant")
    
    # Server Configuration
    port: int = int(os.getenv("PORT", 8000))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Document Configuration
    max_file_size_mb: int = 50
    allowed_file_types: list = [".docx"]
    session_timeout_minutes: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize global settings
settings = Settings()

# Configure Langchain tracing if enabled
if settings.langchain_tracing_v2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.langchain_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    if settings.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

"""
Centralized configuration management for the Insurance Compliance System.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, Field, validator
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Info
    APP_NAME: str = "Insurance Compliance System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    
    # API Configuration
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_RELOAD: bool = Field(True, env="API_RELOAD")
    API_PREFIX: str = Field("/api/v1", env="API_PREFIX")
    
    # Database Configuration
    DATABASE_URL: str = Field("sqlite:///./compliance_system.db", env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(False, env="DATABASE_ECHO")  # For SQLAlchemy logging
    
    # Security Configuration
    SECRET_KEY: str = Field("your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:3000"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File Upload Configuration
    UPLOAD_DIR: Path = Field(Path("./data/uploads"), env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(52428800, env="MAX_FILE_SIZE")  # 50MB
    ALLOWED_EXTENSIONS: List[str] = Field([".pdf", ".txt", ".docx"], env="ALLOWED_EXTENSIONS")
    
    # ML Model Configuration
    LEGAL_BERT_MODEL: str = Field("nlpaueb/legal-bert-base-uncased", env="LEGAL_BERT_MODEL")
    MODEL_DIR: Path = Field(Path("./models"), env="MODEL_DIR")
    MAX_SEQUENCE_LENGTH: int = Field(512, env="MAX_SEQUENCE_LENGTH")
    BATCH_SIZE: int = Field(8, env="BATCH_SIZE")
    LEARNING_RATE: float = Field(2e-5, env="LEARNING_RATE")
    NUM_EPOCHS: int = Field(3, env="NUM_EPOCHS")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field("llama3.1", env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT: int = Field(120, env="OLLAMA_TIMEOUT")  # seconds
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Classification Labels
    COMPLIANCE_LABELS: Dict[int, str] = {
        0: "COMPLIANT",
        1: "NON_COMPLIANT",
        2: "REQUIRES_REVIEW"
    }
    
    # Processing Configuration
    MAX_CONCURRENT_TASKS: int = Field(10, env="MAX_CONCURRENT_TASKS")
    TASK_TIMEOUT: int = Field(300, env="TASK_TIMEOUT")  # 5 minutes
    
    # Cache Configuration  
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    CACHE_TTL: int = Field(3600, env="CACHE_TTL")  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_ECHO: bool = True


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    API_RELOAD: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_ECHO: bool = False


class TestingSettings(Settings):
    """Testing environment settings."""
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test_compliance_system.db"
    LOG_LEVEL: str = "DEBUG"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings based on environment.
    Uses LRU cache to avoid re-reading environment variables.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        return DevelopmentSettings()
    elif environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return Settings()


# Global settings instance
settings = get_settings()
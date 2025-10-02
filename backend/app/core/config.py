"""
Centralized configuration management for the Insurance Compliance System.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
from pathlib import Path


# Resolve backend root regardless of working directory
BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = BACKEND_ROOT / "data"
MODELS_ROOT = BACKEND_ROOT / "models"
UPLOADS_ROOT = DATA_ROOT / "uploads"


class Settings(BaseModel):
    """Application settings with environment variable support."""
    
    # Application Info
    APP_NAME: str = "Insurance Compliance System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_PREFIX: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./compliance_system.db"
    DATABASE_ECHO: bool = False  # For SQLAlchemy logging
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:3000"
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File Upload Configuration
    UPLOAD_DIR: Path = UPLOADS_ROOT
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx"]
    
    # ML Model Configuration
    LEGAL_BERT_MODEL: str = "nlpaueb/legal-bert-base-uncased"
    MODEL_DIR: Path = MODELS_ROOT
    MODELS_DIR: Path = MODELS_ROOT  # Alias for compatibility
    MAX_SEQUENCE_LENGTH: int = 512
    BATCH_SIZE: int = 8
    LEARNING_RATE: float = 2e-5
    NUM_EPOCHS: int = 3
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT: int = 120  # seconds
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Classification Labels
    COMPLIANCE_LABELS: Dict[int, str] = {
        0: "COMPLIANT",
        1: "NON_COMPLIANT",
        2: "REQUIRES_REVIEW"
    }
    
    # Processing Configuration
    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT: int = 300  # 5 minutes
    
    # Cache Configuration  
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Ensure important directories exist at runtime
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
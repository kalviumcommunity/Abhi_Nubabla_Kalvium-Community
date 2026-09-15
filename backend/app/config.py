import os
import json
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class AppConfig:
    """Centralized configuration manager for Contract RAG Backend."""

    # ==============================
    # Groq - LLM Answer Generation
    # ==============================
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    # ==============================
    # OpenRouter - Vector Embeddings
    # ==============================
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "2048"))

    # Context & Token Limits
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "1500"))
    MAX_ANSWER_TOKENS: int = int(os.getenv("MAX_ANSWER_TOKENS", "500"))
    ANSWER_TEMPERATURE: float = float(os.getenv("ANSWER_TEMPERATURE", "0.2"))
    MAX_HISTORY_TOKENS: int = int(os.getenv("MAX_HISTORY_TOKENS", "1000"))
    HISTORY_TRIM_THRESHOLD: float = float(os.getenv("HISTORY_TRIM_THRESHOLD", "0.80"))

    # Supabase Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Backend JWT Authentication Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-backend-jwt-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Pinecone Credentials
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "contract-rag-index")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

    # Storage Paths
    CONTRACT_STORAGE_DIR: Path = BASE_DIR / os.getenv("CONTRACT_STORAGE_DIR", "data/contracts")
    LOCAL_VECTOR_STORE_PATH: Path = BASE_DIR / os.getenv("LOCAL_VECTOR_STORE_PATH", "data/contracts/vector_store.json")

    # Server Settings
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    API_WORKERS: int = int(os.getenv("API_WORKERS", "1"))

    # CORS Origins
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]')
        try:
            origins = json.loads(raw)
            if isinstance(origins, list):
                return origins
        except Exception:
            pass
        return [item.strip() for item in raw.split(",") if item.strip()]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Ensure required data directories exist
AppConfig.CONTRACT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str = "contract_rag") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, AppConfig.LOG_LEVEL, logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger("app_config")

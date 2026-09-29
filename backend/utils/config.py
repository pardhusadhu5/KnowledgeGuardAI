import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_documents"
SQLITE_DB_PATH = DATA_DIR / "knowledgeguard.db"

# Ensure directories exist
for directory in [DATA_DIR, UPLOAD_DIR, CHROMA_DIR, SAMPLE_DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "KnowledgeGuard AI"
    PROJECT_SUBTITLE: str = "An Agentic RAG System for Detecting Outdated and Conflicting Knowledge in AI Systems"
    ENV: str = "development"
    
    # LLM Settings
    LLM_PROVIDER: str = "openai"  # openai, groq, gemini, or mock
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = ""
    
    # Chroma & Embedding Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIR: str = str(CHROMA_DIR)
    
    # Database
    DATABASE_URL: str = f"sqlite:///{SQLITE_DB_PATH}"
    
    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

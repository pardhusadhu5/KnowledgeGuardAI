import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DEFAULT_CHROMA_DIR = DATA_DIR / "chromadb"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_documents"
SQLITE_DB_PATH = DATA_DIR / "knowledgeguard.db"

# Ensure core directories exist
for directory in [DATA_DIR, UPLOAD_DIR, DEFAULT_CHROMA_DIR, SAMPLE_DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "KnowledgeGuard AI"
    PROJECT_SUBTITLE: str = "An Agentic RAG System for Detecting Outdated and Conflicting Knowledge in AI Systems"
    ENV: str = "development"
    
    # LLM Provider Configuration
    # Options: gemini | openai | groq
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_API_KEY: str = ""  # general fallback key
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_BASE_URL: str = ""
    
    # Chroma & Vector Storage Settings
    CHROMA_PERSIST_DIR: str = str(DEFAULT_CHROMA_DIR)
    COLLECTION_NAME: str = "knowledgeguard_documents"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Relational Database
    DATABASE_URL: str = f"sqlite:///{SQLITE_DB_PATH}"

    def get_effective_api_key(self) -> str:
        prov = self.LLM_PROVIDER.lower()
        if prov == "gemini":
            return self.GEMINI_API_KEY or self.LLM_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        elif prov == "groq":
            return self.GROQ_API_KEY or self.LLM_API_KEY or os.environ.get("GROQ_API_KEY", "")
        elif prov == "openai":
            return self.OPENAI_API_KEY or self.LLM_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        return self.LLM_API_KEY
    
    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure configured chroma persist dir exists
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

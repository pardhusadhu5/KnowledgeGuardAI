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
    # Options: groq | gemini | openai
    LLM_PROVIDER: str = "groq"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_API_KEY: str = ""  # general fallback key
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_BASE_URL: str = ""
    
    # Chroma & Vector Storage Settings
    CHROMA_PERSIST_DIR: str = str(DEFAULT_CHROMA_DIR)
    COLLECTION_NAME: str = "knowledgeguard_documents"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    # Optional Chroma HttpClient / Cloud settings for production
    CHROMA_SERVER_HOST: str = ""
    CHROMA_SERVER_PORT: int = 8000
    CHROMA_SERVER_SSL: bool = False
    CHROMA_AUTH_TOKEN: str = ""
    
    # Relational Database
    DATABASE_URL: str = f"sqlite:///{SQLITE_DB_PATH}"

    # Server & Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    FRONTEND_URL: str = "https://knowledgeguardai-1.onrender.com"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://knowledgeguardai-1.onrender.com,https://knowledgeguardai.onrender.com,https://knowledgeguard-frontend.onrender.com"


    def get_effective_api_key(self) -> str:
        # Check active provider first
        prov = (self.LLM_PROVIDER or "groq").lower()
        if prov == "groq":
            key = self.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "") or self.LLM_API_KEY
            if key and not key.startswith("your_"):
                return key.strip()
        elif prov == "gemini":
            key = self.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "") or self.LLM_API_KEY
            if key and not key.startswith("your_"):
                return key.strip()
        elif prov == "openai":
            key = self.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "") or self.LLM_API_KEY
            if key and not key.startswith("your_"):
                return key.strip()

        # Automatic cross-provider fallback
        for candidate_key in [
            self.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", ""),
            self.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", ""),
            self.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", ""),
            self.LLM_API_KEY or os.environ.get("LLM_API_KEY", "")
        ]:
            if candidate_key and len(candidate_key.strip()) > 5 and not candidate_key.strip().startswith("your_"):
                return candidate_key.strip()
        return ""
    
    class Config:
        env_file = (str(BASE_DIR / ".env"), str(BACKEND_DIR / ".env"))
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure configured chroma persist dir exists
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

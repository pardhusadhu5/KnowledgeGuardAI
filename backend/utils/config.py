import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# Detect persistent storage root
_env_persistent_dir = os.environ.get("PERSISTENT_DATA_DIR", "").strip()
DATA_DIR = Path(_env_persistent_dir) if _env_persistent_dir else (BASE_DIR / "data")

_env_upload_dir = os.environ.get("UPLOAD_DIR", "").strip()
UPLOAD_DIR = Path(_env_upload_dir) if _env_upload_dir else (DATA_DIR / "uploads")

_env_chroma_dir = os.environ.get("CHROMA_PERSIST_DIR", "").strip()
DEFAULT_CHROMA_DIR = Path(_env_chroma_dir) if _env_chroma_dir else (DATA_DIR / "chromadb")

SAMPLE_DOCS_DIR = BASE_DIR / "data" / "sample_documents"
SQLITE_DB_PATH = DATA_DIR / "knowledgeguard.db"

# Ensure core local directories exist safely
for directory in [DATA_DIR, UPLOAD_DIR, DEFAULT_CHROMA_DIR, SAMPLE_DOCS_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


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
    
    # Storage Paths & Directories
    PERSISTENT_DATA_DIR: str = str(DATA_DIR)
    UPLOAD_DIR: str = str(UPLOAD_DIR)

    # Chroma & Vector Storage Settings
    CHROMA_PERSIST_DIR: str = str(DEFAULT_CHROMA_DIR)
    CHROMA_COLLECTION_NAME: str = "knowledgeguard_documents"
    COLLECTION_NAME: str = "knowledgeguard_documents"  # backwards compatibility alias
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Optional Chroma HttpClient / Cloud settings for production
    CHROMA_SERVER_HOST: str = ""
    CHROMA_SERVER_PORT: int = 8000
    CHROMA_SERVER_SSL: bool = False
    CHROMA_AUTH_TOKEN: str = ""
    
    # Relational Database Configuration
    # When empty or unset: defaults cleanly to local SQLite (data/knowledgeguard.db)
    # When postgresql:// or postgres://: seamlessly connects to production PostgreSQL
    DATABASE_URL: str = ""

    # Server & Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    FRONTEND_URL: str = "https://knowledgeguardai-1.onrender.com"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://knowledgeguardai-1.onrender.com,https://knowledgeguardai.onrender.com,https://knowledgeguard-frontend.onrender.com"

    @property
    def effective_collection_name(self) -> str:
        return self.CHROMA_COLLECTION_NAME or self.COLLECTION_NAME or "knowledgeguard_documents"

    @property
    def effective_database_url(self) -> str:
        raw = (self.DATABASE_URL or "").strip()
        if not raw:
            return f"sqlite:///{SQLITE_DB_PATH}"
        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql://", 1)
        return raw

    @property
    def is_postgres(self) -> bool:
        url = self.effective_database_url.lower()
        return url.startswith("postgresql://") or url.startswith("postgres://")

    @property
    def database_type(self) -> str:
        return "postgresql" if self.is_postgres else "sqlite"

    @property
    def is_remote_chroma(self) -> bool:
        return bool(self.CHROMA_SERVER_HOST and len(self.CHROMA_SERVER_HOST.strip()) > 0)

    @property
    def vector_store_type(self) -> str:
        return "remote_chroma" if self.is_remote_chroma else "local_chroma"

    def get_safe_storage_summary(self) -> dict:
        if self.is_postgres:
            raw = self.effective_database_url
            host_part = raw.split("@")[-1] if "@" in raw else "remote"
            db_desc = f"PostgreSQL (host={host_part.split('/')[0]})"
        else:
            db_desc = f"SQLite ({SQLITE_DB_PATH})"

        if self.is_remote_chroma:
            vec_desc = f"Remote ChromaDB ({self.CHROMA_SERVER_HOST}:{self.CHROMA_SERVER_PORT}, ssl={self.CHROMA_SERVER_SSL})"
        else:
            vec_desc = f"Local ChromaDB ({self.CHROMA_PERSIST_DIR})"

        return {
            "database_type": self.database_type,
            "database_description": db_desc,
            "vector_store_type": self.vector_store_type,
            "vector_store_description": vec_desc,
            "collection_name": self.effective_collection_name,
            "upload_storage": str(self.UPLOAD_DIR),
            "persistent_data_dir": str(self.PERSISTENT_DATA_DIR),
        }

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

# Ensure configured chroma persist dir and upload dir exist if local
if not settings.is_remote_chroma:
    try:
        Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

try:
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
except Exception:
    pass

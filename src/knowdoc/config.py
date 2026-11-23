from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://knowdoc:knowdoc@127.0.0.1:54329/knowdoc"
    migration_database_url: str | None = None
    storage_dir: Path = Path("data/uploads")
    ollama_url: str = "http://127.0.0.1:11434"
    embedding_backend: str = "ollama"
    embedding_model: str = "nomic-embed-text:latest"
    embedding_dim: int = 768
    embedding_digest: str = ""
    generation_model: str = "gemma:2b"
    allow_remote_provider: bool = False
    cookie_secure: bool = False
    web_origin: str = "http://127.0.0.1:5173"
    max_upload_bytes: int = 20 * 1024 * 1024
    job_lease_seconds: int = 300
    max_attempts: int = 3
    session_hours: int = 24
    ocr_enabled: bool = False

    @model_validator(mode="after")
    def local_provider(self):
        host = urlparse(self.ollama_url).hostname
        if not self.allow_remote_provider and host not in {
            "localhost", "127.0.0.1", "::1", "host.docker.internal"
        }:
            raise ValueError("Remote provider disabled; explicit data authorization is required")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()

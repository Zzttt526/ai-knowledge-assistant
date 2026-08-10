from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Knowledge Assistant"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    llm_api_key: str | None = None
    llm_mode: str = "mock"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_allow_mock_fallback: bool = True
    model_name: str = "BAAI/bge-small-zh"
    embedding_allow_fallback: bool = True
    vector_db_path: str = "./data/vector"
    upload_dir: str = "./data/uploads"
    vector_collection: str = "knowledge_base"
    max_upload_size_mb: int = 20
    chunk_size: int = 500
    chunk_overlap: int = 80
    app_database_path: str = "./data/app.db"
    jwt_secret_key: str = "change-this-in-production"
    jwt_expire_minutes: int = 1440

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

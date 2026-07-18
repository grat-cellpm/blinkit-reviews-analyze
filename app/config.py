from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    database_url: str = "sqlite:///./data/blinkit.db"
    chroma_path: str = "./data/chroma"
    blinkit_app_id: str = "com.grofers.customerapp"
    blinkit_app_lang: str = "en"
    blinkit_app_country: str = "in"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_top_k: int = 8
    review_fetch_count: int = 1000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()

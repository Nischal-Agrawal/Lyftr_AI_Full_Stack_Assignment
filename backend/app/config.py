import os
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeyConfig(BaseModel):
    key_id: str
    api_key: str
    model: str


class Settings(BaseSettings):
    LLM_API_KEYS: str = "mock-key-alpha-12345,mock-key-beta-67890"
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LLM_MODELS: str = ""
    DATABASE_URL: str = "sqlite:////data/app.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ENABLE_FAILURE_SIMULATION: bool = True
    DEFAULT_SYSTEM_PROMPT: str = "You are a helpful, concise AI assistant."
    LITELLM_CACHE_TYPE: str = "local"
    LLM_TIMEOUT_SECONDS: int = 25

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def key_pool(self) -> List[KeyConfig]:
        raw_keys = [k.strip() for k in self.LLM_API_KEYS.split(",") if k.strip()]
        raw_models = [m.strip() for m in self.LLM_MODELS.split(",") if m.strip()]

        pool: List[KeyConfig] = []
        for i, key in enumerate(raw_keys):
            key_id = f"key_{i + 1}"
            model = raw_models[i] if i < len(raw_models) and raw_models[i] else self.LLM_MODEL
            pool.append(KeyConfig(key_id=key_id, api_key=key, model=model))
        return pool

    @property
    def sqlite_db_path(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("sqlite:////"):
            return "/" + url[11:]
        elif url.startswith("sqlite:///"):
            return url[10:]
        return url


settings = Settings()

"""Backend-only configuration; OS environment overrides the root .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parent.parent / ".env", Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: SecretStr = SecretStr("")
    mongodb_db: str = Field(default="execflow", min_length=1)
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = Field(default="llama-3.3-70b-versatile", min_length=1)
    executive_user_name: str = "Arjun Malhotra"
    executive_user_role: str = "VP Sales"


@lru_cache
def get_settings() -> Settings:
    return Settings()

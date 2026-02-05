from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./agent_scrum.db"

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"

    # Simulation mode - when True, agents use mock responses instead of Gemini API
    simulate_mode: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()

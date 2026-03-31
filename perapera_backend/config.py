from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database (PostgreSQL via Docker)
    database_url: str = "postgresql+asyncpg://appuser:devpassword@db:5432/english_app"

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # OpenAI (developer key — used for free sessions, proxied via backend)
    openai_dev_api_key: str = ""

    # Free session limits (set at registration based on age group)
    free_sessions_adult: int = 5
    free_sessions_student: int = 10

    # App
    debug: bool = False

    #model_config = {"env_file": ".env"}
    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
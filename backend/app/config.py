from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vestora.db"  # swap for PostgreSQL in prod

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    # LLM (Groq or OpenAI-compatible)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "llama3-8b-8192"

    # Cache TTL (seconds)
    MARKET_DATA_TTL: int = 60 * 60 * 24        # 24hr — daily NSE data
    ANALYTICS_CACHE_TTL: int = 60 * 60          # 1hr
    API_RESPONSE_TTL: int = 60 * 15            # 15min

    # NSE scraper
    NSE_DATA_URL: str = "https://afx.kwayisi.org/nse/"
    USE_DATA_URL: str = "https://afx.kwayisi.org/use/"

    class Config:
        env_file = ".env"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI-Powered HRMS Virtual Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    DATABASE_URL: str

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_core import MultiHostUrl
from pydantic import computed_field, PostgresDsn
from typing import Literal


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "Lyrebird Mini Tech API"
    ENV: Literal["local", "docker"] = "local"
    DEBUG: bool = True

    ## Postgres
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return str(
            MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    # JWT Settings
    JWT_SECRET: str  # Change in production
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 30  # minutes

    # OpenAI
    OPENAI_API_KEY: str

    # default model
    DEFAULT_LLM_TEXT_MODEL: str = "gpt-4o"
    FORMAT_PROMPT: str = "format-transcript"
    EXTRACT_RULES_PROMPT: str = "create-memory"

    # LangSmith
    LANGSMITH_TRACING: bool
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_API_KEY: str | None = None
    LLM_BASE_URL: str
    LLM_MODEL: str
    PROJECT_NAME: str = "LLM Gateway API"

    class Config:
        env_file = ".env"

settings = Settings()

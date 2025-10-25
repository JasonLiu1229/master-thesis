from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_API_KEY: str | None = None
    LLM_BASE_URL: str
    LLM_MODEL: str

    class Config:
        env_file = ".env"

settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_API_KEY: str | None = None
    LLM_BASE_URL: str
    LLM_MODEL: str


settings = Settings()

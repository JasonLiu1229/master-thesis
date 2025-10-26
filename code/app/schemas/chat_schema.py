from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_message: str
    api_key: str | None = None


class ChatResponse(BaseModel):
    reply: str

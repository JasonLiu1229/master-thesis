from typing import List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str


class ChatChoice(BaseModel):
    message: ChatMessage


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class ChatResponse(BaseModel):
    choices: List[ChatChoice]
    usage: Optional[Usage] = None  

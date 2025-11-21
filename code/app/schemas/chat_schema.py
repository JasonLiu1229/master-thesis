from pydantic import BaseModel
from types import List

class ChatRequest(BaseModel):
    user_message: str
    api_key: str | None = None
    
class ChatMessage(BaseModel):
    content: str

class ChatChoice(BaseModel):
    message: ChatMessage
    
class ChatResponse(BaseModel):
    choices: List[ChatChoice]

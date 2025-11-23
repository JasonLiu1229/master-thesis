from pydantic import BaseModel
from types import List

class ChatMessage(BaseModel):
    role:str
    content: str
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str

class ChatChoice(BaseModel):
    message: ChatMessage
    
class ChatResponse(BaseModel):
    choices: List[ChatChoice]

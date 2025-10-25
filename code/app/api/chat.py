from fastapi import APIRouter, HTTPException, status
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.llm import ask_llm

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    """
    Middleman endpoint:
    - take user message
    - ask the LLM
    - return model reply
    """
    try:
        reply_text = await ask_llm(body.user_message)
        return ChatResponse(reply=reply_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream LLM error"
        ) from e

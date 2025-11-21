from fastapi import APIRouter, HTTPException, status
from schemas.chat_schema import ChatRequest, ChatResponse, ChatMessage, ChatChoice
from services.llm import ask_llm
from services.security import verify_api_key

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest) -> ChatResponse:
    """
    Middleman endpoint:
    - take user message
    - ask the LLM
    - return model reply
    """
    if body.api_key:
        import json

        with open(
            "json_db.json", "r"
        ) as f:  # JSON is just a toy db for API keys (not included in the git repo)
            db = json.load(f)

        verify = any(
            verify_api_key(body.api_key, stored_hash)
            for stored_hash in db.get("api_keys", [])
        )

        if not verify:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
            )
    try:
        reply_text = await ask_llm(body.user_message)
        return ChatResponse(choices=[ChatChoice(message=ChatMessage(content=reply_text))])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream LLM error"
        ) from e

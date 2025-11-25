import logging

from fastapi import APIRouter, Header, HTTPException, status

from logger import setup_logging
from schemas.chat_schema import ChatChoice, ChatMessage, ChatRequest, ChatResponse
from services.llm import ask_llm
from services.security import verify_api_key

setup_logging("api")
logger = logging.getLogger("api")

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest, authorization: str = Header(None)
) -> ChatResponse:
    if authorization:
        scheme, _, key = authorization.partition(" ")
        if scheme.lower() == "bearer":
            import json

            with open("json_db.json", "r") as f:
                db = json.load(f)

            verify = any(
                verify_api_key(key, stored_hash)
                for stored_hash in db.get("api_keys", [])
            )

            if not verify:
                raise HTTPException(status_code=401, detail="Invalid API key")

    user_message = ""

    for message in body.messages:
        if message.role == "user":
            user_message = message.content
            break

    try:
        reply_text = await ask_llm(user_message)

        return ChatResponse(
            choices=[
                ChatChoice(
                    message=ChatMessage(
                        role="assistant",
                        content=reply_text,
                    )
                )
            ]
        )
    except Exception as e:
        logger.error(f"Upstream LLM error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Upstream LLM error: {e}"
        ) from e

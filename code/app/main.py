from fastapi import FastAPI
from app.core.config import settings
from app.api.chat import router as chat_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0"
)

app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.get("/health")
async def health():
    return {"status": "ok"}

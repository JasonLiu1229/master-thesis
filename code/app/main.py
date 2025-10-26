from fastapi import FastAPI
from app.api.chat import router as chat_router
from app.api.keygen import router as keygen_router

app = FastAPI(
    title="LLM Chat API (Local tool)",
    version="1.0.0"
)

app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(keygen_router, prefix="/api", tags=["keygen"])

@app.get("/health")
async def health():
    return {"status": "ok"}

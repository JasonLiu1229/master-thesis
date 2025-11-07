import anyio
from model import get_model

model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"


async def ask_llm(user_message: str) -> str:
    llm = get_model(model_id)
    return await anyio.to_thread.run_sync(llm.generate, user_message)

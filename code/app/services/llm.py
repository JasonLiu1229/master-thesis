import anyio
from model import get_model

model_id = "codellama/CodeLlama-7b-Instruct-hf"


async def ask_llm(user_message: str) -> str:
    llm = get_model(model_id)
    return await anyio.to_thread.run_sync(llm.generate, user_message)

from model import get_model

model_id = "codellama/CodeLlama-13b-Instruct-hf"


async def ask_llm(user_message: str) -> str:
    llm = get_model(model_id)
    response = llm.generate(user_message)
    return response

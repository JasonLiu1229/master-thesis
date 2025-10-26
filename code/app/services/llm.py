from model import LLM_Model

# Load the LLM model once at startup
model_id = "codellama/CodeLlama-13b-Instruct-hf"

llm_model = LLM_Model()
llm_model.load_model(model_id)


async def ask_llm(user_message: str) -> str:
    response = llm_model.generate(user_message)

    return response

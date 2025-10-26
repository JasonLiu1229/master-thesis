from model import LLM_Model

model_id = "codellama/CodeLlama-13b-Instruct-hf"

_llm_model = None  # singleton

def get_model() -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        m = LLM_Model()
        m.load_model(model_id)
        _llm_model = m
    return _llm_model

async def ask_llm(user_message: str) -> str:
    llm = get_model()
    response = llm.generate(user_message)
    return response

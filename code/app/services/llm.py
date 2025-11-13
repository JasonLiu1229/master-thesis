import anyio
from model import get_model, get_local_model
import yaml

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


async def ask_llm(user_message: str) -> str:
    if config["USE_LOCAL_LLM"]:
        llm = get_local_model(config["LOCAL_MODEL_PATH"])
    else:
        llm = get_model(config["MODEL_ID"])
    return await anyio.to_thread.run_sync(llm.generate, user_message)

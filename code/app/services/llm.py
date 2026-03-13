import anyio
from model import get_model, get_local_model, LocalUsage
import yaml

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

async def ask_llm(user_message: str, sys_instruction: str) -> tuple[str, LocalUsage]:
    if config["USE_LOCAL_LLM"]:
        llm = get_local_model(config["MODEL_ID"], config["ADAPTER_FILE"])
    else:
        llm = get_model(config["MODEL_ID"])

    return await anyio.to_thread.run_sync(
        lambda: llm.generate_with_usage(
            user_message,
            sys_instruction=sys_instruction,
            do_sample=True
        )
    )

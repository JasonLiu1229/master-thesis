import anyio
from model import get_model, get_local_model, convert_checkpoint
import yaml
import os

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

def is_hf_model_folder(path: str) -> bool:
    if not os.path.isfile(os.path.join(path, "config.json")):
        return False
    
    # Must contain at least ONE valid weight file
    weight_files = [
        "pytorch_model.bin",
        "model.safetensors",
        "tf_model.h5",
        "model.ckpt.index",
        "flax_model.msgpack",
    ]
    
    return any(os.path.isfile(os.path.join(path, f)) for f in weight_files)

async def ask_llm(user_message: str, sys_instruction: str) -> str:
    if config["USE_LOCAL_LLM"]:
        if config["LOAD_FROM_CKPT"]:
            if not is_hf_model_folder(config["LOCAL_MODEL_PATH"]):
                convert_checkpoint(config["CKPT_PATH"], config["MODEL_ID"], config["LOCAL_MODEL_PATH"])
            llm = get_local_model(config["LOCAL_MODEL_PATH"])
        else:
            llm = get_local_model(config["LOCAL_MODEL_PATH"])
    else:
        llm = get_model(config["MODEL_ID"])

    return await anyio.to_thread.run_sync(
        lambda: llm.generate(
            user_message,
            sys_instruction=sys_instruction,
            do_sample=True
        )
    )

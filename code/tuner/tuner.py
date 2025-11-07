import os

import torch
import yaml
from datasets import DatasetDict

from peft import get_peft_model, LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


def define_base():
    """
    This function will set the base function for the tune function. Where we set what model we use and how the Lora config is set.

    Return:
        - Model
        - AutoTokenizer
    """
    tokenizer = AutoTokenizer.from_pretrained(config["MODEL_NAME"], use_fast=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    if config["USE_QLORA"]:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_type=torch.float16,
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            config["MODEL_NAME"],
            quantization_config=bnb_config,
            devide_map='auto',
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        ).to(device)
    else:
        base_model = AutoModelForCausalLM.from_pretrained(
            config["MODEL_NAME"],
            device_map='auto',
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        ).to(device)
    
    lora_config = LoraConfig(
        r=config["RANK"],
        lora_alpha=config["LORA_ALPHA"],
        lora_dropout=config["LORA_DROPOUT"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
    )
    
    model = get_peft_model(base_model, lora_config)
    return model, tokenizer  


def tune():
    pass

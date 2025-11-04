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


def tune():
    pass

import os

import torch
import yaml
from datasets import DatasetDict

from model import get_model, LLM_Model
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
    pass


def tune():
    pass

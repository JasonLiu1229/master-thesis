import logging
import os

import torch
import yaml
from datasets import DatasetDict

from model import LLM_Model

from peft import get_peft_model, LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

logger = logging.getLogger('tuner')

logging.basicConfig(filename='out/logs/tuner.log', encoding='utf-8', level=logging.DEBUG)

_llm_model = None

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


def load_ds(path: str) -> DatasetDict:
    assert os.path.exists(path), f"Dataset path {path} does not exist."
    try:
        return DatasetDict.load_from_disk(path)
    except Exception as e:
        logger.error(f"Failed to load dataset from {path}: {e}")
        raise RuntimeError(f"Failed to load dataset from {path}: {e}")


def set_llm_model(model, model_name, tokenizer) -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        _llm_model = LLM_Model()
    _llm_model.set_model(
        model,
        model_name,
        tokenizer,
    )
    return _llm_model


def define_base():
    """
    This function will set the base function for the tune function. Where we set what model we use and how the Lora config is set.

    Return:
        - Model
        - AutoTokenizer
    """
    global _llm_model
    if _llm_model is not None:
        return _llm_model

    tokenizer = AutoTokenizer.from_pretrained(config["MODEL_NAME"], use_fast=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if config["USE_QLORA"]:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_type=torch.bfloat16,
        )

        base_model = AutoModelForCausalLM.from_pretrained(
            config["MODEL_ID"],
            quantization_config=bnb_config,
            devide_map="auto",
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        )
    else:
        base_model = AutoModelForCausalLM.from_pretrained(
            config["MODEL_ID"],
            device_map="auto",
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        )

    lora_config = LoraConfig(
        r=config["RANK"],
        lora_alpha=config["LORA_ALPHA"],
        lora_dropout=config["LORA_DROPOUT"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    model = get_peft_model(base_model, lora_config)

    _llm_model = set_llm_model(model, config["MODEL_NAME"], tokenizer)

    return model, tokenizer


def get_llm_model() -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        define_base()
    return _llm_model


def tune():
    output_dir = config["OUTPUT_DIR"]
    train_data_path = output_dir + config["TRAIN_DIR"]
    val_data_path = output_dir + config["VAL_DIR"]

    train_ds = load_ds(train_data_path)
    val_ds = load_ds(val_data_path)

    model, tokenizer = define_base()

    collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    args = TrainingArguments(
        output_dir=config["SAVE_MODEL_PATH"],
        num_train_epochs=config["NUM_EPOCHS"],
        per_device_train_batch_size=config["BATCH_SIZE_PER_DEVICE"],
        per_device_eval_batch_size=config["BATCH_SIZE_PER_DEVICE"],
        gradient_accumulation_steps=config["GRAD_ACCUM_STEPS"],
        learning_rate=config["LEARNING_RATE"],
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        weight_decay=0.0,
        logging_steps=config["LOGGING_STEPS"],
        evaluation_strategy="steps" if val_ds is not None else "no",
        eval_steps=config["EVAL_STEPS"],
        save_steps=config["EVAL_STEPS"],
        save_total_limit=config["MAX_SAVE_TOTAL"],
        bf16=torch.cuda.is_available(),  # use bf16 if available
        gradient_checkpointing=True,
        report_to=["tensorboard"],
    )

    trainer = Trainer(
        model=model,
        args=args,
        data_collator=collator,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    logger.info("Starting training...")
    trainer.train()

    adapter_dir = os.path.join("out/", "adapter")
    os.makedirs(adapter_dir, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

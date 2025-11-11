import inspect
import logging
import os

import torch
import yaml
from datasets import Dataset
from logger import setup_logging

from model import LLM_Model

from peft import get_peft_model, LoraConfig, prepare_model_for_kbit_training

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

setup_logging("tuner")
logger = logging.getLogger("tuner")

_llm_model: LLM_Model = None

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)


def load_ds(path: str) -> Dataset:
    if not os.path.exists(path):
        logger.warning(f"Dataset path {path} does not exist. Returning None.")
        raise FileNotFoundError(f"Dataset path {path} does not exist.")
    try:
        return Dataset.load_from_disk(path)
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
        return _llm_model.get_model(), _llm_model.get_tokenizer()

    tokenizer = AutoTokenizer.from_pretrained(config["MODEL_ID"], use_fast=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    tokenizer.padding_side = "right"

    if config["USE_QLORA"]:
        if not torch.cuda.is_available():
            logger.warning(
                "QLoRA is enabled but CUDA is not available. Falling back to non-quantized model."
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                config["MODEL_ID"],
                device_map="auto",
                torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
            )
        else:
            logger.info("Loading model with QLoRA quantization...")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_type=torch.bfloat16,
            )

            base_model = AutoModelForCausalLM.from_pretrained(
                config["MODEL_ID"],
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
            )

            base_model = prepare_model_for_kbit_training(base_model)
    else:
        logging.info("Loading model without quantization...")
        base_model = AutoModelForCausalLM.from_pretrained(
            config["MODEL_ID"],
            device_map="auto",
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        )

    try:
        base_model.gradient_checkpointing_enable()
        base_model.enable_input_require_grads()
    except Exception:
        pass

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

    try:
        model.config.use_cache = False
    except Exception:
        pass
    
    _llm_model = set_llm_model(model, config["MODEL_ID"], tokenizer)

    return model, tokenizer


def get_llm_model() -> LLM_Model:
    global _llm_model
    if _llm_model is None:
        logger.info("Defining base LLM model...")
        define_base()
        logger.info("LLM model defined and loaded.")
    return _llm_model


def make_args(val_ds: Dataset | None) -> TrainingArguments:
    sig = inspect.signature(TrainingArguments)

    logging.info("Creating TrainingArguments...")

    kw = {
        "output_dir": config["SAVE_MODEL_PATH"],
        "num_train_epochs": config["NUM_EPOCHS"],
        "per_device_train_batch_size": config["BATCH_SIZE_PER_DEVICE"],
        "per_device_eval_batch_size": config["BATCH_SIZE_PER_DEVICE"],
        "gradient_accumulation_steps": config["GRAD_ACCUM_STEPS"],
        "learning_rate": config["LEARNING_RATE"],
        "warmup_ratio": 0.03,  # starts with a lower LR and then slowly increases to the set LR based on this ratio
        "lr_scheduler_type": "cosine",  # slow decay in the beginning, fast decay at the end
        "weight_decay": 0.0,
        "logging_steps": config["LOGGING_STEPS"],
        "eval_steps": config["EVAL_STEPS"],
        "save_steps": config["EVAL_STEPS"],
        "save_total_limit": config["MAX_SAVE_TOTAL"],
        "bf16": False,
        "gradient_checkpointing": True,
        "report_to": ["tensorboard"],
        "load_best_model_at_end": True if val_ds is not None else False,
    }

    try:
        kw["bf16"] = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    except Exception:
        kw["bf16"] = False

    if "evaluation_strategy" in sig.parameters:
        kw["evaluation_strategy"] = "steps" if val_ds is not None else "no"
    else:
        kw["eval_strategy"] = "steps" if val_ds is not None else "no"

    if "save_strategy" in sig.parameters:
        kw["save_strategy"] = "steps"

    return TrainingArguments(**kw)


def tune():
    output_dir = config["OUTPUT_DIR"]
    train_data_path = os.path.join(output_dir, config["TRAIN_DIR"])
    val_data_path = os.path.join(output_dir, config["VAL_DIR"])

    train_ds = load_ds(train_data_path)
    val_ds = load_ds(val_data_path)

    model, tokenizer = define_base()

    collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=8,  # for better performance on GPUs
    )

    args = make_args(val_ds)

    trainer = Trainer(
        model=model,
        args=args,
        data_collator=collator,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    logger.info("Starting training...")
    trainer.train()

    adapter_dir = config["ADAPTER_SAVE_PATH"]
    os.makedirs(adapter_dir, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    logger.info(f"Adapter model saved to {adapter_dir}")

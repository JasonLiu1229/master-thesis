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
    TrainerCallback,
    TrainingArguments,
)

from transformers.trainer_utils import get_last_checkpoint

setup_logging("tuner")
logger = logging.getLogger("tuner")

_llm_model: LLM_Model = None

config = {}
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

# VSC overide the files with env vars
config["ARROW_DIR"] = os.environ.get("ARROW_DIR", config["ARROW_DIR"])
config["SAVE_MODEL_PATH"] = os.environ.get("SAVE_MODEL_PATH", config["SAVE_MODEL_PATH"])
config["ADAPTER_SAVE_PATH"] = os.environ.get(
    "ADAPTER_SAVE_PATH", config["ADAPTER_SAVE_PATH"]
)
config["LOG_DIR"] = os.environ.get("LOG_DIR", config["LOG_DIR"])


def load_ds(path: str) -> Dataset:
    if not os.path.exists(path):
        logger.error(f"Dataset path {path} does not exist. Returning None.")
        raise FileNotFoundError(f"Dataset path {path} does not exist.")
    try:
        return Dataset.load_from_disk(path)
    except Exception as e:
        logger.error(f"Failed to load dataset from {path}: {e}")
        raise RuntimeError(f"Failed to load dataset from {path}: {e}")


def pick_attn_implementation() -> str | None:  # gpt generated
    """
    Choose the best attention backend available on this machine.

    Returns:
        "flash_attention_2" if it should work,
        "sdpa" as a safe GPU/CPU fallback when available,
        None to let Transformers choose its default.
    """
    if not torch.cuda.is_available():
        logger.info("CUDA not available -> not using flash attention.")
        return "sdpa"  # works on CPU too (falls back internally)

    try:
        major, minor = torch.cuda.get_device_capability()
        if major < 8:
            logger.warning(
                f"GPU compute capability is {major}.{minor} (< 8.0). "
                "FlashAttention-2 not supported -> falling back to sdpa."
            )
            return "sdpa"
    except Exception as e:
        logger.warning(
            f"Could not read CUDA device capability: {e}. Falling back to sdpa."
        )
        return "sdpa"

    try:
        logger.info("flash_attn import OK -> using flash_attention_2.")
        return "flash_attention_2"
    except Exception as e:
        logger.warning(f"flash_attn not available ({e!r}) -> falling back to sdpa.")
        return "sdpa"


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

    attn_impl = pick_attn_implementation()

    def base_model_load():
        kwargs = dict(
            device_map="auto",
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        )
        if attn_impl is not None:
            kwargs["attn_implementation"] = attn_impl

        return AutoModelForCausalLM.from_pretrained(config["MODEL_ID"], **kwargs)

    if config["USE_QLORA"]:
        if not torch.cuda.is_available():
            logger.warning(
                "QLoRA is enabled but CUDA is not available. Falling back to non-quantized model."
            )
            base_model = base_model_load()
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
                **({"attn_implementation": attn_impl} if attn_impl is not None else {}),
            )

            base_model = prepare_model_for_kbit_training(base_model)
    else:
        logger.info("Loading model without quantization...")
        base_model = base_model_load()

    try:
        if config["GRADIENT_CHECKPOINTING"]:
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

    logger.info("Creating TrainingArguments...")

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
        "gradient_checkpointing": config["GRADIENT_CHECKPOINTING"],
        "report_to": ["tensorboard"],
        "load_best_model_at_end": True if val_ds is not None else False,
        "disable_tqdm": False,
        "group_by_length": True,
        "dataloader_num_workers": 8,
        "optim": "paged_adamw_8bit",
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


class AdapterSnapshotCallback(TrainerCallback):
    def __init__(self, model, tokenizer, adapter_root, percentages=(0.25, 0.5, 1.0)):
        self.model = model
        self.tokenizer = tokenizer
        self.adapter_root = adapter_root
        self.percentages = percentages
        self.saved = set()

    def on_step_end(self, args, state, control, **kwargs):
        if not state.max_steps:
            return

        progress = state.global_step / state.max_steps

        for p in self.percentages:
            if progress >= p and p not in self.saved:
                out_dir = os.path.join(self.adapter_root, f"adapter_{int(p*100)}pct")
                os.makedirs(out_dir, exist_ok=True)

                self.model.save_pretrained(out_dir)
                self.tokenizer.save_pretrained(out_dir)

                logger.info(f"Saved adapter snapshot at {int(p*100)}% -> {out_dir}")
                self.saved.add(p)


def tune(input_arrow_dir: str | None = None):
    arrow_dir = input_arrow_dir or config["ARROW_DIR"]
    train_data_path = os.path.join(arrow_dir, config["TRAIN_DIR"])
    val_data_path = os.path.join(arrow_dir, config["VAL_DIR"])

    train_ds = load_ds(train_data_path)
    val_ds = load_ds(val_data_path)
    
    # for ds_name, ds in [("train", train_ds), ("val", val_ds)]:
    #     if ds is not None and "labels" in ds.column_names:
    #         logger.warning(f"Removing 'labels' column from {ds_name} dataset (was ragged).")
    #         if ds_name == "train":
    #             train_ds = train_ds.remove_columns(["labels"])
    #         else:
    #             val_ds = val_ds.remove_columns(["labels"])

    model, tokenizer = define_base()

    collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=8,  # for better performance on GPUs
    )

    args = make_args(val_ds)

    last_ckpt = None
    if os.path.isdir(args.output_dir):
        last_ckpt = get_last_checkpoint(args.output_dir)

    if config.get("USE_SMALLER_DATASET", False):
        fraction = config.get("SMALLER_FRACTION", 0.1)
        train_size = int(len(train_ds) * fraction)
        val_size = int(len(val_ds) * fraction) if val_ds is not None else 0
        train_ds = train_ds.shuffle(seed=42).select(range(train_size))
        if val_ds is not None:
            val_ds = val_ds.shuffle(seed=42).select(range(val_size))
        logger.info(
            f"Using smaller dataset fraction: {fraction}. Train size: {train_size}, Val size: {val_size}"
        )

    trainer = Trainer(
        model=model,
        args=args,
        data_collator=collator,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        callbacks=[
            AdapterSnapshotCallback(
                model=model,
                tokenizer=tokenizer,
                adapter_root=config["ADAPTER_SAVE_PATH"],
                percentages=(0.25, 0.5, 1.0),
            ),
        ],
    )

    logger.info("Starting training...")

    if config.get("RESUME_FROM_LAST_CP", False) and last_ckpt is not None:
        logger.info(f"Resuming training from checkpoint: {last_ckpt}")
        trainer.train(resume_from_checkpoint=last_ckpt)
    else:
        trainer.train()

    # adapter_dir = config["ADAPTER_SAVE_PATH"]
    # os.makedirs(adapter_dir, exist_ok=True)
    # model.save_pretrained(adapter_dir)
    # tokenizer.save_pretrained(adapter_dir)
    # logger.info(f"Adapter model saved to {adapter_dir}")

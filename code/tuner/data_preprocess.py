import json
import logging
import os
import random
import shutil
from typing import List

import yaml
from datasets import Dataset, Features, Sequence, Value
from logger import setup_logging
from transformers import AutoTokenizer

SYSTEM_INSTRUCTION = (
    "You are a code refactoring assistant for Java unit tests.\n"
    "You will be given:\n"
    "- A Java test method (wrapped in a dummy class), and\n"
    "- A list of identifier names (method + local variables + parameters).\n\n"
    "Your job is to propose more meaningful names for these identifiers.\n"
    "Make use of this template to additionally guide the naming:\n"
    "- A test case should have an assertion between expected and actual values. "
    "So for identifiers that are used in the assertions itself, try to make use "
    "of expected and actual.\n\n"
    "You MUST ONLY respond with a JSON object mapping originalName -> newName.\n"
    "You MUST NOT output code or comments or markdown.\n"
)

USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated Java test method wrapped in a dummy class:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Here are the identifiers that may be renamed:\n"
    "{identifiers}\n\n"
    "Propose more meaningful names for each of THESE identifiers only.\n"
    "Return a single JSON object mapping originalName -> newName.\n"
    "Example:\n"
    '{{ "func_1": "testYearEnd" }}\n\n'
    "Important:\n"
    "- Use ONLY the listed identifiers as keys.\n"
    "- Do NOT introduce new identifiers.\n"
    "- Do NOT include any keys that were not listed.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text)."
)


setup_logging("tuner")
logger = logging.getLogger("tuner")

config: dict = {}
try:
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError(f"config.yml parsed to {type(config)}, expected dict")
except Exception as e:
    logger.exception(f"Failed to read/parse config.yml: {e}")
    raise


def _format_identifier_list(identifiers: List[str]) -> str:
    return "\n".join(f"- {name}" for name in identifiers)


def build_prompt(obf_code: str, identifiers: List[str], tokenizer) -> str:
    """Build the full prompt string in chat-template format."""
    user_content = USER_PROMPT_TEMPLATE.format(
        test_case=obf_code,
        identifiers=_format_identifier_list(identifiers),
    )
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_content},
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def preprocess_single(
    obf_code: str,
    mapping: dict,
    identifiers: List[str],
    max_length: int,
    tokenizer: AutoTokenizer,
):
    """
    Build one (input_ids, attention_mask, labels) triple.

    The model is trained to produce the JSON mapping as its completion.
    Only completion tokens carry real labels; prompt tokens get -100.
    """
    eos = tokenizer.eos_token or "</s>"

    prompt = build_prompt(obf_code, identifiers, tokenizer)

    completion = (
        json.dumps(
            {k: mapping[k] for k in identifiers if k in mapping}, ensure_ascii=False
        )
        + eos
    )

    full_text = prompt + completion
    prompt_len_chars = len(prompt)

    encoder = tokenizer(
        full_text,
        return_offsets_mapping=True,
        max_length=max_length,
        truncation=True,
        padding="max_length",
    )

    input_ids: List[int] = encoder["input_ids"]
    attn_mask: List[int] = encoder["attention_mask"]
    offsets: List[tuple] = encoder["offset_mapping"]

    labels: List[int] = []
    for (start, end), idx, mask in zip(offsets, input_ids, attn_mask):
        if mask == 0:
            labels.append(-100)
        elif end <= prompt_len_chars:
            labels.append(-100)
        else:
            labels.append(idx)

    assert len(labels) == len(input_ids) == max_length
    return {
        "input_ids": input_ids,
        "attention_mask": attn_mask,
        "labels": labels,
    }


def preprocess(
    input_dir: str,
    output_dir: str,
    shuffle: bool = True,
    seed: int = 42,
) -> Dataset:
    """
    Reads .jsonl files from *input_dir*.  Each line must be a JSON object with:
        - "obf_code"    : str  – the obfuscated wrapped Java test
        - "mapping"     : dict – {obfuscated_name: original_name}
        - "identifiers" : list – ordered list of obfuscated identifier names

    Writes an Arrow dataset to *output_dir*.
    """
    assert os.path.exists(input_dir), f"Input directory {input_dir} does not exist."

    # Clean / create output dir
    if os.path.exists(output_dir) and os.listdir(output_dir):
        logger.warning(
            f"Output directory {output_dir} already exists and is not empty. "
            "Overwriting contents."
        )
        for name in os.listdir(output_dir):
            fp = os.path.join(output_dir, name)
            shutil.rmtree(fp) if os.path.isdir(fp) else os.remove(fp)
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.endswith(".jsonl")]
    assert files, f"No .jsonl files found in {input_dir}."

    if shuffle:
        random.Random(seed).shuffle(files)

    tokenizer = AutoTokenizer.from_pretrained(config["MODEL_ID"], use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    max_len = int(config["MAX_LENGTH"])

    features = Features(
        {
            "input_ids": Sequence(Value("int32"), length=max_len),
            "attention_mask": Sequence(Value("int8"), length=max_len),
            "labels": Sequence(Value("int32"), length=max_len),
        }
    )

    logger.info(
        f"Preprocessing files in {input_dir} "
        f"(streaming, max_len={max_len}, format=json-mapping) …"
    )

    def gen():
        kept = skipped_json = skipped_feat = 0

        for file_idx, filename in enumerate(files, 1):
            if file_idx % 1000 == 0 or file_idx == 1:
                logger.info(f"Processing file {file_idx}/{len(files)}: {filename}")

            input_path = os.path.join(input_dir, filename)
            try:
                with open(input_path, "r", encoding="utf-8") as fh:
                    for line_idx, line in enumerate(fh, 1):
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            record = json.loads(line)
                        except Exception as e:
                            skipped_json += 1
                            logger.exception(
                                f"Bad JSON in {input_path}:{line_idx} "
                                f"({type(e).__name__}: {e})"
                            )
                            continue

                        obf_code = record.get("obf_code")
                        mapping = record.get("mapping")  
                        identifiers = record.get("identifiers")  

                        if not obf_code or not mapping or not identifiers:
                            skipped_json += 1
                            logger.warning(
                                f"Skipping incomplete record at {input_path}:{line_idx} "
                                f"(missing obf_code / mapping / identifiers)"
                            )
                            continue

                        if not isinstance(mapping, dict) or not isinstance(
                            identifiers, list
                        ):
                            skipped_json += 1
                            logger.warning(
                                f"Skipping malformed record at {input_path}:{line_idx}"
                            )
                            continue

                        try:
                            feat = preprocess_single(
                                obf_code, mapping, identifiers, max_len, tokenizer
                            )
                        except Exception as e:
                            skipped_feat += 1
                            logger.exception(
                                f"preprocess_single failed at {input_path}:{line_idx} "
                                f"({type(e).__name__}: {e})"
                            )
                            continue

                        if any(
                            len(feat[k]) != max_len
                            for k in ("input_ids", "attention_mask", "labels")
                        ):
                            skipped_feat += 1
                            logger.warning(
                                f"Length mismatch at {input_path}:{line_idx} – skipping."
                            )
                            continue

                        if all(lbl == -100 for lbl in feat["labels"]):
                            skipped_feat += 1
                            logger.warning(
                                f"No supervised tokens (completion truncated?) "
                                f"at {input_path}:{line_idx} – skipping."
                            )
                            continue

                        kept += 1
                        if kept % 50_000 == 0:
                            logger.info(
                                f"Generated {kept} examples so far "
                                f"(skipped_json={skipped_json}, "
                                f"skipped_feat={skipped_feat})"
                            )

                        yield feat

            except Exception as e:
                logger.exception(
                    f"Failed to read file {input_path} "
                    f"({type(e).__name__}: {e}) – skipping file."
                )

        logger.info(
            f"Done. kept={kept}, "
            f"skipped_json={skipped_json}, skipped_feat={skipped_feat}"
        )

    ds = Dataset.from_generator(gen, features=features)

    if len(ds) == 0:
        raise RuntimeError("No valid examples found after preprocessing.")

    ds.save_to_disk(output_dir)
    logger.info(f"Saved dataset to {output_dir} (num_rows={len(ds)})")
    return ds

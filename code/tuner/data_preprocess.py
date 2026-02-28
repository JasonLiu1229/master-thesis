import difflib
import json
import logging
import os
import random
from typing import List, Tuple

import yaml
from datasets import Dataset, DatasetDict, Features, Sequence, Value
from logger import setup_logging

from transformers import AutoTokenizer

# Uses a different prompting, fine in general because the tasks remains the same but overall is now simpler
USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated test:\n\n"
    "```java\n"
    "{obf}\n"
    "```\n\n"
    "Return ONLY the improved code block, nothing else."
)

SYSTEM_INSTRUCTION = (
    "You are a code refactoring assistant.\n"
    "Rename identifiers in the following Java unit test so that names are meaningful and self-explanatory.\n"
    "Do **NOT** change logic, literals, comments, formatting, assertions, try and catch methodology, or method call structure.\n"
    "ONLY change identifier names (methods, variables)."
)

setup_logging("tuner")

logger = logging.getLogger("tuner")

config = {}

try:
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError(f"config.yml parsed to {type(config)}, expected dict")
except Exception as e:
    logger.exception(f"Failed to read/parse config.yml: {e}")
    raise


def diff_spans(obf: str, gt: str) -> List[Tuple[int, int]]:
    """checks the difference between obfuscated code and ground truth code and a list of tuples of where to where it is located

    Args:
        obf (str): obfuscated code
        gt (str): ground truth

    Returns:
        List[Tuple[int, int]]: list of indexes from where to where it is located (start, end)
    """
    sm = difflib.SequenceMatcher(a=obf, b=gt, autojunk=False)
    spans = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag in ("replace", "insert", "delete"):
            spans.append((b0, b1))
    return spans


def spans_overlap(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    """check for overlap between two spans
    Args:
        span1 (Tuple[int, int]): first span
        span2 (Tuple[int, int]): second span
    Returns:
        bool: whether they overlap
    """
    return not (span1[1] <= span2[0] or span2[1] <= span1[0])


def build_prompt_qwen(obf_code: str, tokenizer) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(obf=obf_code)},
    ]
    prompt_text: str = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    return prompt_text


# Note this part of the code is partially made with the help of GPT-4, this is because i did not understand the logic behind the tokenization and label creation fully.
def preprocess_single(
    obf_code: str, gt_code: str, max_length: int, tokenizer: AutoTokenizer
):
    eos = tokenizer.eos_token or "</s>"

    prompt = build_prompt_qwen(obf_code, tokenizer)
    response_prefix = "```java\n"
    response_suffix = "\n```" + eos

    full_text = prompt + response_prefix + gt_code + response_suffix

    gt_code_start = len(prompt + response_prefix)
    gt_code_end = gt_code_start + len(gt_code)

    changed_spans_local = diff_spans(obf_code, gt_code)

    encoder = tokenizer(
        full_text,
        return_offsets_mapping=True,
        max_length=max_length,
        truncation=True,
        padding="max_length",
    )

    input_ids = encoder["input_ids"]
    attn_mask = encoder["attention_mask"]
    offsets = encoder["offset_mapping"]

    labels = []
    for (start, end), idx, m in zip(offsets, input_ids, attn_mask):
        if m == 0:
            labels.append(-100)
            continue

        label_id = -100

        if start >= gt_code_start and end <= gt_code_end:
            local_start = start - gt_code_start
            local_end = end - gt_code_start

            for c_start, c_end in changed_spans_local:
                if spans_overlap((local_start, local_end), (c_start, c_end)):
                    label_id = idx
                    break

        labels.append(label_id)

    assert len(labels) == len(input_ids) == max_length

    return {
        "input_ids": input_ids,
        "attention_mask": attn_mask,
        "labels": labels,
    }


def preprocess( # fixed using GPT-5.2
    input_dir: str,
    output_dir: str,
    shuffle: bool = True,
    seed: int = 42,
) -> Dataset | DatasetDict:
    if not os.path.exists(input_dir):
        logging.error(f"Input directory {input_dir} does not exist.")
    assert os.path.exists(input_dir), f"Input directory {input_dir} does not exist."

    if os.path.exists(output_dir) and os.listdir(output_dir):
        logger.warning(
            f"Output directory {output_dir} already exists and is not empty. Overwriting contents."
        )
        for f in os.listdir(output_dir):
            file_path = os.path.join(output_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                import shutil

                shutil.rmtree(file_path)
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

    logger.info(f"Preprocessing files in {input_dir} (streaming, max_len={max_len})...")

    def gen():
        kept = 0
        skipped_json = 0
        skipped_feat = 0

        for file_idx, file in enumerate(files, 1):
            if file_idx % 1000 == 0 or file_idx == 1:
                logger.info(f"Processing file {file_idx}/{len(files)}: {file}")

            input_path = os.path.join(input_dir, file)
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    for line_idx, line in enumerate(f, 1):
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line)
                        except Exception as e:
                            skipped_json += 1
                            logger.exception(
                                f"Skipping bad JSON in {input_path}:{line_idx} "
                                f"({type(e).__name__}: {e})"
                            )
                            continue

                        obf_code = entry.get("prompt")
                        gt_code = entry.get("response")
                        if not obf_code or not gt_code:
                            continue

                        try:
                            feat = preprocess_single(
                                obf_code, gt_code, max_len, tokenizer
                            )
                        except Exception as e:
                            skipped_feat += 1
                            logger.exception(
                                f"Skipping example (preprocess_single failed) at {input_path}:{line_idx} "
                                f"({type(e).__name__}: {e})"
                            )
                            continue

                        if (
                            len(feat["input_ids"]) != max_len
                            or len(feat["attention_mask"]) != max_len
                            or len(feat["labels"]) != max_len
                        ):
                            skipped_feat += 1
                            logger.warning(
                                f"Skipping example with wrong lengths at {input_path}:{line_idx} "
                                f"(got input_ids={len(feat['input_ids'])}, labels={len(feat['labels'])})"
                            )
                            continue

                        kept += 1
                        if kept % 50000 == 0:
                            logger.info(
                                f"Generated {kept} examples so far "
                                f"(skipped_json={skipped_json}, skipped_feat={skipped_feat})"
                            )

                        yield {
                            "input_ids": feat["input_ids"],
                            "attention_mask": feat["attention_mask"],
                            "labels": feat["labels"],
                        }
            except Exception as e:
                logger.exception(
                    f"Failed to read file {input_path} ({type(e).__name__}: {e}) - skipping file"
                )
                continue

        logger.info(
            f"Done generating examples. kept={kept}, skipped_json={skipped_json}, skipped_feat={skipped_feat}"
        )

    ds = Dataset.from_generator(gen, features=features)

    if len(ds) == 0:
        raise RuntimeError("No valid examples found after preprocessing.")

    ds.save_to_disk(output_dir)
    logger.info(f"Saved preprocessed dataset to {output_dir} (num_rows={len(ds)})")

    return ds
